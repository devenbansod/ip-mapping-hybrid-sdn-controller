from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.controller.dpset import DPSet
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from LegacyRouteModulator import legacyRouteMod
from DBConnection import DBConnection
from Allocator import allocator

class policyTranslator(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # src = ""                                      # Source subnet of the policy
    # dst = ""                                      # Destination subnet of the policy
    # route = []                                    # Route of the policy
    # matches = datapath.ofproto_parser.OFPMatch()  # Match conditions of the policy
    # actions = []                                  # Actions to be taken
    # mapRange = []                                 # Range of IP addresses to map the policy to
    A = None                                        # Instance of the allocator object of network
    dbCon = None


    # Constructor
    def __init__(self, *args, **kwargs):
        super(policyTranslator, self).__init__(*args, **kwargs)
        self.A = allocator()
        self.dbCon = DBConnection()

    # PACKET - IN method handler
    # would require to handle the Internet IP Clash problem

    # Function to extract subnet size from network
    def getSubnet (net):
        # Parse network details to extract and return subnet
        return net

    # Function to get the range of allocated IPs for the policy
    # by calling the getNext function of the allocator object
    def getAllocation (dst):
        # Get subnet information from the destination information
        sub = self.getSubnet(dst)

        # Call the allocator to get a range to map to
        return self.A.getNext(sub)

    # would be called by the Network Administrator
    # src   = 192.168.1.0/24
    # dst   = 192.168.2.0/24
    # path  = [s1_dev_id, r1_dev_id, .... other Rs .... s2_dev_id]
    def setPolicy (self, src, dst, path):
        # get Range to Map the Policy path to
        mapRange = getAllocation (dst)

        # Call the legacy route modulator to install routes in legacy devices
        LRM = legacyRouteMod(self.dbCon, mapRange, route[1:])
        LRM.addRoutes()

        # Call the twin flow pusher to add flows
        # into the source(first in route) and destination(last in route) SDN switches
        twinFlowPusher.push(self.dbCon, mapRange, m, route[0], route[1], route[-1])


class twinFlowPusher:
    "Push the flow entries in two end SDN switches"

    @staticmethod
    def push(dbCon, mapRange, matchConditions, sdn1_id, r1_dev_id, sdnN_id):

        # FIRST CHECK if Reverse Mapping entries already added in Dest SDN
        # Need to remeber if added or not
        if already_added[sdnN_id] == False:
            i = 0
            # iterate over mapRange IPs with 'i'
            for i in range(1, len(mapRange)):
                # get Datapath from dpid
                datapath = DPset.get(sdn1_id)

                dest_wildcard = matchConditions['mapRange'] + "" # append appropriate wildcard here
                host_mac = dbCon.getMacFromIp(mapRange[i]) # from the interface table in database

                # need to make this dynamic
                matches = datapath.ofproto_parser.OFPMatch(
                    nw_proto = matchConditions['nw_proto'],
                    nw_src   = matchConditions['src_ip'][i],
                    nw_dst   = dest_wildcard,
                    dl_type  = matchConditions['dl_type'],
                    tcp_dst  = matchConditions['tcp_dst_port']
                )

                # need to write this
                rev_mapped_dest_ip = getRevMappedDestinationIP(mapRange[i])

                # need to use OpenFlow 1.2+ here
                actions = [
                    datapath.ofproto_parser.OFPActionSetField(nw_dst=rev_mapped_dest_ip),
                    datapath.ofproto_parser.OFPActionSetField(dl_dst=host_mac),
                    datapath.ofproto_parser.OFPActionOutput(out_port)
                ]

                # call the add flow method
                self.add_flow(datapath, priority=60000, match=self.matches, actions=actions)


        # NOW, add the Mapping entries in Source SDN

        # required for setting the Output ACTION in Flow entry to-be-added
        out_port = dbCon.getInterfaceConnectedTo(sdn1_id, r1_dev_id)

        # required for setting the Set field(Dest MAC address) action
        router_rec_port = dbCon.getInterfaceConnectedTo(r1_dev_id, sdn1_id)

        # add Mapping entries in source SDN switch
        i = 0
        # iterate over mapRange IPs with 'i'
        for i in range(1, len(mapRange)):
            # get Datapath from dpid
            datapath = DPset.get(sdn1_id)

            # need to make this dynamic
            matches = datapath.ofproto_parser.OFPMatch(
                nw_proto = matchConditions['nw_proto'],
                nw_src   = matchConditions['src_ip'][i],
                nw_dst   = matchConditions['nw_dst'],
                dl_type  = matchConditions['dl_type'],
                tcp_dst  = matchConditions['tcp_dst_port']
            )

            # need to use OpenFlow 1.2+ here
            actions = [
                datapath.ofproto_parser.OFPActionSetField(nw_dst=self.mapRange[i]),
                datapath.ofproto_parser.OFPActionSetField(dl_dst=router_rec_port['mac_addr']),
                datapath.ofproto_parser.OFPActionOutput(out_port)
            ]

            # call the add flow method
            add_flow(datapath, priority=60000, match=self.matches, actions=actions)


def add_flow(datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)


class TwinFlowPusherTester:
    def __init__(self):
        "Tester initialized"
        self.dbCon = DBConnection()

    def testPush():
        twinFlowPusher.push(self.dbCon, ['1.0.0.1'], {'nw_proto' : 'ip', 'src_ip' : '10.0.1.0/24', 'nw_dst' : '10.0.2.1'})

# tester = TwinFlowPusherTester()
# tester.testPush()
