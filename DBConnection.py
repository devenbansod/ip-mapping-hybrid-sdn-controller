import sqlite3
import json
import os
import sys

class DBConnection:
	"Wrapper to fetch and insert data into database"
	conn = None
	db = "test_db"

	tbl_master = "sqlite_master"
	tbl_devices = "devices"
	tbl_interfaces = "interfaces"
	tbl_links = "links"
	db_structure_file = "db_structure.sql"

	next_global_int_id = 1
	next_link_id = 1

	def __init__(self, db_file = None):
		if db_file == None:
			db_file = db

		os.system("rm " + self.db)
		print "\n*** Initialising and connecting to database"
		self.conn = sqlite3.connect(db_file)
		self.db = db_file
		print "\n*** Setting up tables in the database"
		self.setupTables()

	def setupTables(self):
		db_structure = open(self.db_structure_file, "r")
		self.conn.executescript(db_structure.read())

	# Returns the table in the database
	def showTablesInDB(self):
		return self.conn.execute("Select name from " + self.tbl_master + " \
			where type = 'table';")

	# Returns all the devices
	def getDevices(self):
		return self.conn.execute("Select * from " + self.tbl_devices + ";")

	# Returns all the interfaces
	def getInterfaces(self):
		return self.conn.execute("Select * from " + self.tbl_interfaces + ";")		

	# Returns the interfaces for a particular device
	def getInterfacesForDevice(self, device_id):
		return self.conn.execute("Select int_id, mac_addr, ip_addr \
			FROM " + self.tbl_interfaces + " where device_id = '" + str(device_id) + "';")

	# Returns the links from/to a particular device
	def getLinksFromToDevice(self, device_id):
		return self.conn.execute("Select * FROM " + self.tbl_links + " WHERE "
			+ "int1 in ("
			+ "Select global_int_id FROM " + self.tbl_interfaces + " WHERE device_id = '"
			+ str(device_id) + "')"
			+ " OR int2 in ("
			+ "Select global_int_id FROM " + self.tbl_interfaces + " WHERE device_id = '"
			+ str(device_id) + "');"
		)

	# Returns the interface connected from src_device to dest_device
	def getInterfaceConnectedTo(self, src_device, dest_device):
		links_src = self.getLinksFromToDevice(src_device);
		links_dest = self.getLinksFromToDevice(dest_device);
		linksA = []
		i = 0
		for link in links_src:
			linksA.insert(i, link[0])
			i = i + 1
		linksB = []
		i = 0
		for link in links_dest:
			linksB.insert(i, link[0])
			i = i + 1

		connected_links = list(set(linksA) & set(linksB))
		for link in connected_links:
			result = self.conn.execute("SELECT * FROM " + self.tbl_links 
				+ " WHERE link_id = "
				+ str(link)
			)
			for r in result:
				interface = self.conn.execute("SELECT * FROM " + self.tbl_interfaces
					+ " WHERE (global_int_id = " + str(r[1]) + " OR "
					+ " global_int_id = " + str(r[2]) + ") AND "
					+ " device_id = " + str(src_device)
				)

				return interface.fetchone()

	# returns the 'details' column as a JSON - associative array
	def getDetailsForDevice(self, router_id):
		result = self.conn.execute("SELECT details FROM "
			+ self.tbl_devices + " WHERE device_id = " + str(router_id)
		)
		return json.load(result.fetchone()[0])

	# returns the MAC address from IP
	def getMacFromIP(self, ip_addr):
		return self.conn.execute("SELECT mac_addr FROM "
			+ self.tbl_interfaces + " WHERE ip_addr = " + str(ip_addr)
		)
		return result.fetchone()[0]

	def addDevice(self, device_id, name, details):
		self.conn.execute("INSERT INTO " + self.tbl_devices
			+ " VALUES (?, ?, ?)", (device_id, name, details)
		)
		return device_id

	def addInterface(
		self, int_id, device_id,
		ip_addr=None, mac_addr=None, name=None
	):
		if ip_addr == None:
			ip_addr = ""
		if mac_addr == None:
			mac_addr = ""
		if name == "":
			name = ""

		self.conn.execute("INSERT INTO " + self.tbl_interfaces
			+ "(global_int_id, int_id, ip_addr, mac_addr, device_id, name)"
			+ " VALUES (?, ?, ?, ?, ?, ?)",
			(self.next_global_int_id, int_id, ip_addr, mac_addr, device_id, name)
		)

		self.next_global_int_id = self.next_global_int_id + 1
		return self.next_global_int_id - 1


	def addLink(self, int1_str, int2_str):
		int1_id = self.conn.execute("SELECT global_int_id FROM "
			+ self.tbl_interfaces + " WHERE int_id = '"
			+ int1_str + "'"
		).fetchone()[0]
		int2_id = self.conn.execute("SELECT global_int_id FROM "
			+ self.tbl_interfaces + " WHERE int_id = '"
			+ int2_str + "'"
		).fetchone()[0]

		self.conn.execute("INSERT INTO " + self.tbl_links
			+ "(link_id, int1, int2)"
			+ " VALUES (?, ?, ?)", (self.next_link_id, int1_id, int2_id)
		)
		self.next_link_id = self.next_link_id + 1
		return self.next_link_id - 1

# helper function
def printResult(rows):
	for row in rows:
		for element in row:
			sys.stdout.write(str(element).encode('utf-8') + "|\t")
		print ""

class test_DBConnection:

	# Test cases
	def __init__():
		print "\n*** Initialising Database"
		conn = DBConnection('test_db')

	def testAll():
		print "\n*** Showing tables in the Database"
		rows = conn.showTablesInDB()
		printResult(rows)

		print "\n*** Showing all devices"
		conn.addDevice(10, "Test_device", "")
		conn.addDevice(20, "Test_device2", "")
		rows = conn.getDevices()
		printResult(rows)

		print "\n*** Showing all interfaces"
		conn.addInterface("r1-eth1", "10", "50.1", "00:50", "abc")
		conn.addInterface("r2-eth1", "20", "60.1", "00:60", "abc")
		rows = conn.getInterfaces()
		printResult(rows)

		print "\n*** Showing tables in the Database"
		rows = conn.showTablesInDB()
		printResult(rows)


		conn.addLink("r1-eth1", "r2-eth1")
		devices = conn.getDevices()
		for device in devices:
			print "\n*** Links for Device " + str(device[0]) + " (" + device[1] + ")"
			print "Link_id| Interface1| Interface2"
			rows = conn.getLinksFromToDevice(device[0])
			printResult(rows)

		print "\n*** Interface connected from device 1 to device 2"
		rows = conn.getInterfaceConnectedTo(1, 2)
		print rows

		print "\n*** Interface connected from device 4 to 2"
		rows = conn.getInterfaceConnectedTo(4, 2)
		print rows

		print "\n*** Interface connected from device 1 to 3"
		rows = conn.getInterfaceConnectedTo(1, 3)
		print rows

		print "\n*** Interface connected from device 3 to 1"
		rows = conn.getInterfaceConnectedTo(3, 1)
		print rows

		print "\n*** Interface connected from device 1 to 4"
		rows = conn.getInterfaceConnectedTo(1, 4)
		print rows