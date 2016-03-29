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


def net2str (net):
    return (str(net[0]) + "/" + str(net[1]))

def str2net (netStr):
    return netStr.split("/")

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
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
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
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        pkt = packet.Packet(msg.data)
        
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        
        if pkt_ipv4 == None:
            self._simple_packet_in_handler(ev)
            return

        src = pkt_ipv4.src
        dst = pkt_ipv4.dst
        print src, dst

        if self.A.checkIfAllocated(dst):
            self.A.getNext(32)
        else:
            self._simple_packet_in_handler(ev)

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

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

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
    def getAllocation (dest):
        dst = str2net (dest)
        # Get subnet information from the destination information
        sub = dst [1]

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
        twinFlowPusher.push(self.dbCon, mapRange, m, src, dst, route[0], route[1], route[-1])


class twinFlowPusher:
    "Push the flow entries in two end SDN switches"

    @staticmethod
    def push(dbCon, mapRange, matchConditions, src, dst, sdn1_id, r1_dev_id, sdnN_id):

        # FIRST CHECK if Reverse Mapping entries already added in Dest SDN
        # Need to remeber if added or not
        if already_added[sdnN_id] == False:
            i = 0
            # iterate over mapRange IPs with 'i'
            for i in range(mapRange[0], mapRange[1]+1):
                # get Datapath from dpid
                datapath = DPset.get(sdn1_id)

                # dest_wildcard = matchConditions['mapRange'] + "" # append appropriate wildcard here
                dest_wildcard = int2ip ( 1<<mapRange[2] - 1 )
                host_mac = dbCon.getMacFromIp(i) # from the interface table in database

                # need to make this dynamic
                matches = datapath.ofproto_parser.OFPMatch(
                    nw_proto = matchConditions['nw_proto'],
                    nw_src   = matchConditions['src_ip'][i],
                    nw_dst   = dest_wildcard,
                    dl_type  = matchConditions['dl_type'],
                    tcp_dst  = matchConditions['tcp_dst_port']
                )

                # need to write this
                # rev_mapped_dest_ip = getRevMappedDestinationIP(i)
                rev_mapped_dest_ip = (i and dest_wildcard) or (str2net(dst))[0]

                # need to use OpenFlow 1.2+ here
                actions = [
                    datapath.ofproto_parser.OFPActionSetField(nw_dst=rev_mapped_dest_ip),
                    datapath.ofproto_parser.OFPActionSetField(dl_dst=host_mac),
                    datapath.ofproto_parser.OFPActionOutput(out_port)
                ]

                # call the add flow method
                add_flow(datapath, priority=60000, match=self.matches, actions=actions)


        # NOW, add the Mapping entries in Source SDN

        # required for setting the Output ACTION in Flow entry to-be-added
        out_port = dbCon.getInterfaceConnectedTo(sdn1_id, r1_dev_id)

        # required for setting the Set field(Dest MAC address) action
        router_rec_port = dbCon.getInterfaceConnectedTo(r1_dev_id, sdn1_id)

        # add Mapping entries in source SDN switch
        i = 0
        # iterate over mapRange IPs with 'i'
        for i in range(mapRange[0], mapRange[1]+1):
            # get Datapath from dpid
            datapath = DPset.get(sdn1_id)

            # need to make this dynamic
            matches = datapath.ofproto_parser.OFPMatch(
                nw_proto = matchConditions['nw_proto'],
                nw_src   = src,
                nw_dst   = (i and dest_wildcard) or (str2net(dst))[0],
                dl_type  = matchConditions['dl_type'],
                tcp_dst  = matchConditions['tcp_dst_port']
            )

            # need to use OpenFlow 1.2+ here
            actions = [
                datapath.ofproto_parser.OFPActionSetField(nw_dst=i),
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
