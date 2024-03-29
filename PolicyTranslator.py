from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.controller.dpset import DPSet
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import ether_types
from LegacyRouteModulator import legacyRouteMod
from DBConnection import DBConnection
from Allocator import allocator
from Allocator import ip2int
from Allocator import int2ip
import signal
import os, sys, inspect
from event import *

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

def net2str (net):
    return (str(net[0]) + "/" + str(net[1]))

def str2net (netStr):
    return netStr.split("/")

def getMaskWildcard(subnet_size):
    dest_wildcard = int2ip ( (1<<(32-int(subnet_size))) - 1 )
    netmask = int2ip(((1<<32 )- 1) - ip2int(dest_wildcard))
    return [netmask, dest_wildcard]

class policyTranslator(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _EVENTS =  [EventMessage]

    # src = ""                                      # Source subnet of the policy
    # dst = ""                                      # Destination subnet of the policy
    # route = []                                    # Route of the policy
    # matches = datapath.ofproto_parser.OFPMatch()  # Match conditions of the policy
    # actions = []                                  # Actions to be taken
    # mapRange = []                                 # Range of IP addresses to map the policy to
    A = None                                        # Instance of the allocator object of network
    dbCon = None
    datapath_store = {}
    curr = 0
    mac_to_port = {}


    # Constructor
    def __init__(self, *args, **kwargs):
        super(policyTranslator, self).__init__(*args, **kwargs)
        self.A = allocator()
        self.dbCon = DBConnection()
        self.mac_to_port = {}
        self.datapath_store = {}
        self.curr = 0

    # Event to trigger the Policy updation, sent through another controller
    @set_ev_cls(EventMessage)
    def event_Test(self, ev):
        self.curr = self.curr + 1
        if (self.curr > 1):
            print "Installing ..."
            self.setPolicy({'nw_proto' : 6, 'dl_type' : 0x0800}, "10.0.1.10/24", "10.0.2.10/24", [1, 13, 14, 2])
            self.setPolicy({'nw_proto' : 6, 'dl_type' : 0x0800}, "10.0.2.10/24", "10.0.1.10/24", [2, 14, 13, 1])


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapath_store[datapath.id] = datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        add_flow(datapath, 0, match, actions)


    # PACKET - IN method handler
    # would require to handle the Internet IP Clash problem
    # @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    # def _packet_in_handler(self, ev):
    #     self.curr = self.curr + 1


    #     if (self.curr > 5):
    #         self.setPolicy({'nw_proto' : 1, 'dl_type' : 0x0800}, "10.0.1.0/24", "10.0.2.10/32", [1, 13, 14, 2])
    #         self.curr = -10000000

    #     msg = ev.msg
    #     datapath = msg.datapath
    #     ofproto = datapath.ofproto

    #     pkt = packet.Packet(msg.data)

    #     pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)

    #     if pkt_ipv4 == None:
    #         self._simple_packet_in_handler(ev)
    #         return

    #     src = pkt_ipv4.src
    #     dst = pkt_ipv4.dst

    #     if self.A.checkIfAllocated(dst):
    #         self.A.getNext(32)
    #     else:
    #         self._simple_packet_in_handler(ev)

    def _simple_packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)

            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)


    # Function to get the range of allocated IPs for the policy
    # by calling the getNext function of the allocator object
    def getAllocation (self, dest):
        dst = str2net (dest)
        # Get subnet information from the destination information
        sub = dst [1]

        # Call the allocator to get a range to map to
        return self.A.getNext(sub)

    # would be called by the Network Administrator
    # src   = 192.168.1.0/24
    # dst   = 192.168.2.0/24
    # match = ['tcp_port' : '23']
    # path  = [s1_dev_id, r1_dev_id, .... other Rs .... s2_dev_id]
    def setPolicy (self, m, src, dst, path):
        # get Range to Map the Policy path to
        mapRange = self.getAllocation (dst)

        pathPrime = path[:]

        # Call the legacy route modulator to install routes in legacy devices
        LRM = legacyRouteMod(self.dbCon, mapRange, pathPrime)
        LRM.addRoutes()

        # Call the twin flow pusher to add flows
        # into the source(first in route) and destination(last in route) SDN switches
        twinFlowPusher.push(self.datapath_store[path[0]], self.datapath_store[path[-1]],
            self.dbCon, mapRange, m, src, dst, path[0], path[1], path[-2], path[-1]
        )

class twinFlowPusher:
    "Push the flow entries in two end SDN switches"

    @staticmethod
    def push(dp1, dp2, dbCon, mapRange, matchConditions, src, dst, sdn1_id, r1_dev_id, rN_dev_id, sdnN_id):
        already_added = {int(sdnN_id) : False}

        dest_netmask, dest_wildcard = getMaskWildcard(str2net(dst)[1])
        src_netmask, src_wildcard = getMaskWildcard(str2net(src)[1])

        inPort = dbCon.getInterfaceConnectedTo(sdnN_id, rN_dev_id)

        # FIRST CHECK if Reverse Mapping entries already added in Dest SDN
        # Need to remeber if added or not
        if already_added[int(sdnN_id)] == False:

            i = 0
            # iterate over mapRange IPs with 'i'
            for i in range(ip2int(mapRange[0]), ip2int(mapRange[1])+1):

                matches = dp2.ofproto_parser.OFPMatch(
                    in_port=int(inPort[5]),
                    ip_proto=matchConditions['nw_proto'],
                    ipv4_dst=(int2ip(ip2int(dest_wildcard) & i), dest_wildcard),
                    eth_type  = matchConditions['dl_type']
                )

                rev_mapped_dest_ip = (i & ip2int(dest_wildcard)) | ip2int((str2net(dst))[0])

                # from the interface table in database
                host = dbCon.getMacFromIP(int2ip(rev_mapped_dest_ip)) 

                if host is None:
                    continue

                host_mac = str(host[0]).encode('utf-8')
                result =  dbCon.getInterfaceConnectedTo(sdnN_id, host[1])

                if result is None:
                    continue
                out_port = int(result[5])

                # need to use OpenFlow 1.2+ here
                actions = [
                    dp2.ofproto_parser.OFPActionSetField(ipv4_dst=int2ip(rev_mapped_dest_ip)),
                    dp2.ofproto_parser.OFPActionSetField(eth_dst=host_mac),
                    dp2.ofproto_parser.OFPActionOutput(out_port)
                ]

                # call the add flow method
                add_flow(dp2, priority=60000, match=matches, actions=actions)


        # NOW, add the Mapping entries in Source SDN

        # required for setting the Output ACTION in Flow entry to-be-added
        result = dbCon.getInterfaceConnectedTo(sdn1_id, r1_dev_id)

        if result is None:
            return

        out_port = int(result[5])

        # required for setting the Set field(Dest MAC address) action
        result = dbCon.getInterfaceConnectedTo(r1_dev_id, sdn1_id)
        router_rec_port_mac = result[3]

        # add Mapping entries in source SDN switch
        i = 0

        # iterate over mapRange IPs with 'i'
        for i in range(ip2int(mapRange[0]), ip2int(mapRange[1])+1):
            matches = dp1.ofproto_parser.OFPMatch(
                ip_proto = matchConditions['nw_proto'],
                ipv4_src   = (str2net(src)[0], src_netmask),
                ipv4_dst   = int2ip((i & ip2int(dest_wildcard)) | ip2int((str2net(dst))[0])),
                eth_type  = matchConditions['dl_type']
            )

            # need to use OpenFlow 1.2+ here
            host = dbCon.getMacFromIP(int2ip((i & ip2int(dest_wildcard)) | ip2int((str2net(dst))[0]))) 

            # Add mapping entries only if Host with ip exists
            if host is None:
                continue

            actions = [
                dp1.ofproto_parser.OFPActionSetField(ipv4_dst=int2ip(i)),
                dp1.ofproto_parser.OFPActionSetField(eth_dst=router_rec_port_mac),
                dp1.ofproto_parser.OFPActionOutput(out_port)
            ]

            # call the add flow method
            add_flow(dp1, priority=60001, match=matches, actions=actions)


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


# test class, invoke only when testing
class TwinFlowPusherTester:
    def __init__(self):
        "Tester initialized"
        self.dbCon = DBConnection()

    def testPush():
        twinFlowPusher.push(self.dbCon, ['1.0.0.1'], {'nw_proto' : 'ip', 'src_ip' : '10.0.1.0/24', 'nw_dst' : '10.0.2.1'})

# tester = TwinFlowPusherTester()
# tester.testPush()
