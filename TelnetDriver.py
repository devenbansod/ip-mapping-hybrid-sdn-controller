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


# ip_prefix = ""    # "192.168.1.4" or "192.168.1.0/24"
# next_hop = ""     # "10.0.1.4"
# interface = ""    # eth2


class TelnetDriver:
    dbCon = None

    def __init__(self, dbCon):
        self.dbCon = dbCon
        print "Telnet Driver Initialized"

    def addStaticRoute(self, 
        router_id, ip_prefix, next_router=None, next_hop=None, interface=None
    ):

        if next_router == None and next_hop == None:
            print "Atleast one of 'next_router' OR 'next_hop' has to be specified"
            return False

        add_static_route = "ip route add " + ip_prefix + " " + interface + " " + next_hop +  "\r"

        details = self.dbCon.getDetailsForDevice(router_id)
        print "Attemting to connect to Switch"

        while True:
            try:
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
                break
            except pexpect.TIMEOUT:
                print "run again"
            except pexpect.EOF:
                print "Unable to connect to remote host: No route to host\n"
                break




    def removeStaticRoute(self, 
        router_id, ip_prefix, next_router=None, next_hop=None, interface=None
    ):
        if next_router == None and next_hop == None:
            print "Atleast one of 'next_router' OR 'next_hop' has to be specified"
            return False

        remove_static_route = "no ip route add " \
            + ip_prefix + " " + interface + " " + next_hop +  "\r"

        details = self.dbCon.getDetailsForDevice(router_id)
        print "Attemting to connect to Switch"

        while True:
            try:
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
                break
            except pexpect.TIMEOUT:
                print "run again"
            except pexpect.EOF:
                print "Unable to connect to remote host: No route to host\n"
                break

    def get_routes(self, router, file):
        print "Attemting to connect to Router: " + router
        # a = datetime.datetime.now()
        while(True):
            try:
                telconn = pexpect.spawn('telnet ' + router + ' ospfd\r', timeout = 2)
                # time.sleep(1)
                # print "Hello 1"
                telconn.setwinsize(500, 500)

                telconn.expect(":")
                telconn.send("zebra" + "\r")
                # time.sleep(1)
                # print "Hello 2"
                # time.sleep(1)

                telconn.expect(">")
                telconn.logfile = file
                telconn.send("show ip ospf neighbor" + "\r")
                # time.sleep(1)
                telconn.send("\r")
                # print "Hello 3"

                telconn.expect(">")
                telconn.logfile = None
                telconn.send("exit\r")
                # time.sleep(1)
                # print "Hello 4"
                telconn.kill(1)
                # print "Hello 5"
                print "Done\n"
                break
            except pexpect.TIMEOUT:
                print "run again"
            except pexpect.EOF:
                print "Unable to connect to remote host: No route to host\n"
                break