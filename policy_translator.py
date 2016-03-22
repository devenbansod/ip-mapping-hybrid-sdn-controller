from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

class policyTranslator:
	src = ""					# Source subnet of the policy
	dst = ""					# Destination subnet of the policy
	route = []					# Route of the policy
	matches = datapath.ofproto_parser.OFPMatch()	# Match conditions of the policy
	actions = []					# Actions to be taken
	mapRange = []					# Range of IP addresses to map the policy to
	A = allocator()					# Instance of the allocator object of network

	# Constructor
	def __init__ (self, src, dst, path, m, a, alloc):
		self.src = src
		self.dst = dst
		self.route = path
		self.matches = m
		self.actions = a
		self.A = alloc

		setPolicy()

	# PACKET - IN method handler
	# would require to handle the Internet IP Clash problem


	# Function to extract subnet size from network
	def getSubnet (net):
		# Parse network details to extract and return subnet
		return net

	# Function to get the range of allocated IPs for the policy by calling the getNext function of the allocator object
	def getAllocation (dst):
		# Get subnet information from the destination information
		sub = getSubnet (dst)

		# Call the allocator to get a range to map to
		mapRange = A.getNext(sub)

	def setPolicy ():
		getAllocation (dst)

		# Call the legacy route modulator to install routes in legacy devices
		LRM = legacyRouteMod(mapRange, route[1:])
		LRM.addRoutes()

		# Call the twin flow pusher to add flows into the source and destination SDN switches
		TFP = twinFlowPusher(mapRange, route)
		TFP.push()
