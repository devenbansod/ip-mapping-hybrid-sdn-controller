import DBConnection
import TelnetDriver

class legacyRouteMod:
    ipRange = []
    route = []

    def __init__ (self, map, path):
        self.ipRange = map
        self.route = reversed(path)

    def getOutputInterface(src, dst):
        # return the interface in src which connects to dst
        # query database for this
        conn = DBConnection('test_db')
        interface = conn.getInterfaceConnectedTo(src, dst)

        # the interface 'name' is interface[5]
        return interface[5]


    def addRoutes():
        for i in range(1, len(route)):
            # get output interface information
            intf = getOutputInterface(self.route[i], self.route[i-1])

            # Call expect script to add route to the router
            # set network (ipRange[3]) output to intf
            tD = TelnetDriver()
            success = td.addStaticRoute(
                self.route[i], self.ipRange[3], next_router=self.route[i-1], interface=intf
            )

            if (success == False):
                # remove previously added routes

                # call 'tD.removeStaticRoute()' in a loop over all previous routers
                for j in range(1, i + 1):
                    # get output interface information
                    intf = getOutputInterface(self.route[j], self.route[j-1])
                    td.removeStaticRoute(
                        self.route[j], self.ipRange[3], next_router=self.route[j-1], interface=intf
                    )

                # and break
                break;
