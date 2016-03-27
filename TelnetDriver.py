#
# Script takes IP address/prefix, next hop and an optional interface
# as input
#

# Telnets to the router (gets details from the database's 'devices' table)
# and adds the static route entry
#
import pexpect
import time,sys
from DBConnection import DBConnection


# ip_prefix = ""    # "192.168.1.4" or "192.168.1.0/24"
# next_hop = ""     # "10.0.1.4"
# interface = ""    # eth2


class TelnetDriver:
    dbCon = None

    def __init__(self, dbCon):
        self.dbCon = dbCon
        print "Telnet Driver Initialized"

    def addStaticRoute(self,
        router_id, log_file, ip_prefix,
        next_router=None, next_hop=None, interface=None
    ):

        if next_router == None and next_hop == None:
            print "Atleast one of 'next_router' OR 'next_hop' has to be specified"
            return False
        if interface == None:
            interface = ""
        if next_hop == None:
            next_hop = ""

        add_static_route = "ip route " + ip_prefix + " " + next_hop + " " + interface +  "\r"

        details = self.dbCon.getDetailsForDevice(router_id)
        print "Attemting to connect to Router: " + router_id

        while True:
            try:
                telconn = pexpect.spawn('telnet ' + details['ip']
                    + ' ' + details['port'],
                    timeout=2
                )
                telconn.logfile = log_file

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
        router_id, log_file, ip_prefix,
        next_router=None, next_hop=None, interface=None
    ):
        if next_router == None and next_hop == None:
            print "Atleast one of 'next_router' OR 'next_hop' has to be specified"
            return False
        if interface == None:
            interface = ""
        if next_hop == None:
            next_hop = ""

        remove_static_route = "no ip route " \
            + ip_prefix + " " + interface + " " + next_hop +  "\r"

        details = self.dbCon.getDetailsForDevice(router_id)
        print "Attemting to connect to Router: " + router_id

        while True:
            try:
                telconn = pexpect.spawn('telnet ' + details['ip']
                    + ' ' + details['port'],
                    timeout=2
                )
                telconn.logfile = log_file

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

                print "Static Route Removed"
                break
            except pexpect.TIMEOUT:
                print "run again"
            except pexpect.EOF:
                print "Unable to connect to remote host: No route to host\n"
                break

    def get_routes(self, router_id, log_file):
        print "Attemting to connect to Router: " + router_id

        details = self.dbCon.getDetailsForDevice(router_id)
        while(True):
            try:
                telconn = pexpect.spawn('telnet ' + details['ip'] + ' ospfd\r', timeout = 2)
                telconn.setwinsize(500, 500)

                telconn.logfile = log_file
                telconn.expect(":")
                telconn.send("zebra" + "\r")

                telconn.expect(">")
                telconn.send("show ip ospf neighbor" + "\r")
                telconn.send("\r")

                telconn.expect(">")
                telconn.logfile = None
                telconn.send("exit\r")

                telconn.kill(1)
                print "Routes fetched"
                break
            except pexpect.TIMEOUT:
                print "run again"
            except pexpect.EOF:
                print "Unable to connect to remote host: No route to host\n"
                break


class TestTelnetDriver:

    def __init__(self):
        self.dbCon = DBConnection()
        self.td = TelnetDriver(self.dbCon)
        self.test_log = open("test_log.txt", "w")

    def testAdd(self):
        self.td.addStaticRoute(
            "1", self.test_log,
            "192.168.1.0/24", next_hop="192.168.1.1"
        )

    def testRemove(self):
        self.td.removeStaticRoute("1", self.test_log,
            "192.168.1.0/24", next_hop="192.168.1.1")

    def testGet(self):
        self.td.get_routes("1", self.test_log)
