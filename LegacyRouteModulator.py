from DBConnection import DBConnection
from TelnetDriver import TelnetDriver

class legacyRouteMod:
    ipRange = []
    route = []
    dbCon = None

    def __init__ (self, dbCon, map, path):
        self.ipRange = map
        path.reverse()
        self.route = path
        self.dbCon = dbCon

    def getOutputInterface(self, src, dst):
        # return the interface in src which connects to dst
        # query database for this
        interface = self.dbCon.getInterfaceConnectedTo(src, dst)
        # the interface 'name' is interface[5]
        return interface[5]


    def addRoutes(self):
        for i in range(1, len(self.route) - 1):
            # get output interface information
            # intf = self.getOutputInterface(self.route[i], self.route[i-1])
            interface = self.dbCon.getInterfaceConnectedTo(self.route[i-1], self.route[i])

            # Call expect script to add route to the router
            # set network (ipRange[3]) output to intf
            print "int ", interface[4]
            td = TelnetDriver(self.dbCon)
            success = td.addStaticRoute(
                self.route[i], self.ipRange[3], next_router=self.route[i-1],
                next_hop=interface[4] #interface=intf
            )

            if (success == False):
                # remove previously added routes

                # call 'tD.removeStaticRoute()' in a loop over all previous routers
                for j in range(1, i + 1):
                    # get output interface information
                    intf = getOutputInterface(self.route[j], self.route[j-1])
                    td.removeStaticRoute(
                        self.dbCon, self.route[j], self.ipRange[3], next_router=self.route[j-1], interface=intf
                    )

                # and break
                break;
