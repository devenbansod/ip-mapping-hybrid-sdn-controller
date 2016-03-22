#
# Script takes IP address/prefix, next hop and an optional interface
# as input
#

# Telnets to the router (gets details from the database's 'devices' table)
# and adds the static route entry
#
import pexpect
import time,sys
import DBConnection


# ip_prefix = ""  	# "192.168.1.4" or "192.168.1.0/24"
# next_hop = "" 	# "10.0.1.4"
# interface = ""    # eth2


class TelnetDriver:

	def __init__(self):
		print "Telnet Driver Initialized"

	def addStaticRoute(self, 
		router_id, ip_prefix, next_router=None, next_hop=None, interface=None
	):

		if next_router == None and next_hop == None:
			print "Atleast one of 'next_router' OR 'next_hop' has to be specified"
			return False

		add_static_route = "ip route add " + ip_prefix + " " + interface + " " + next_hop +  "\r"

		try:
			dbCon = DBConnection('test_db')
			details = dbCon.getDetailsForDevice(router_id)

			print "Attemting to connect to Switch"
			telconn = pexpect.spawn('telnet ' + details['ip'])
			telconn.logfile = sys.stdout

			telconn.expect(":")
			telconn.send(details['password'] + "\r")

			telconn.expect(">")
			telconn.send ("en\r")

			telconn.expect (":")
			telconn.send (details['password'] + "\r")
			time.sleep(1)

			telconn.expect ("#")
			telconn.send ("config t\r")
			time.sleep(1)

			telconn.expect ("#")
			telconn.sendline (add_static_route)
			telconn.expect("#")

			telconn.send ("end\r")
			telconn.expect("#")

			telconn.send ("disable\r")
			telconn.expect (">")
			telconn.send ("q\r")

			print "Static Route Added"
			return True
		except:
			print ""
		finally:
			return False


	def removeStaticRoute(self, 
		router_id, ip_prefix, next_router=None, next_hop=None, interface=None
	):
		if next_router == None and next_hop == None:
			print "Atleast one of 'next_router' OR 'next_hop' has to be specified"
			return False

		remove_static_route = "no ip route add " \
			+ ip_prefix + " " + interface + " " + next_hop +  "\r"

		try:
			dbCon = DBConnection('test_db')
			details = dbCon.getDetailsForDevice(router_id)

			print "Attemting to connect to Switch"
			telconn = pexpect.spawn('telnet ' + details['ip'])
			telconn.logfile = sys.stdout

			telconn.expect(":")
			telconn.send(details['password'] + "\r")

			telconn.expect(">")
			telconn.send ("en\r")

			telconn.expect (":")
			telconn.send (details['password'] + "\r")
			time.sleep(1)

			telconn.expect ("#")
			telconn.send ("config t\r")
			time.sleep(1)

			telconn.expect ("#")
			telconn.sendline (remove_static_route)
			telconn.expect("#")

			telconn.send ("end\r")
			telconn.expect("#")

			telconn.send ("disable\r")
			telconn.expect (">")
			telconn.send ("q\r")

			print "Static Route Added"
			return True
		except:
			print ""
		finally:
			return False

