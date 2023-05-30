# Libraries
import xml.etree.ElementTree as ET

# Custom files
from unit_cell import UnitCell
from error import error
import config as cfg

class Tile:
	# Initialization Read all info about the tile from file
	def __init__(self, name):
		# Store name
		self.name = name
		# Read XML file
		xml_root = ET.parse(cfg.tile_path + name + ".xml").getroot()
		# Read basic tile-info
		self.technology = xml_root.find("technology").text
		self.protocol = xml_root.find("protocol").text
		self.bandwidth = int(xml_root.find("bandwidth").text)
		self.frequency = int(xml_root.find("frequency").text)
		self.n_rows = int(xml_root.find("n_rows").text)
		self.n_cols = int(xml_root.find("n_cols").text)
		self.n_endpoints = int(xml_root.find("n_endpoints").text)

		# Compute unit cell properties
		ucell = UnitCell(self.technology, self.protocol, self.bandwidth, self.frequency)
		
		# At itself to tiles (needed for compatibility with modules as components)
		self.tiles = [{"location" : (0,0), "dimensions" : (self.n_rows, self.n_cols)}]
		self.connections = []

		# Read master-ports
		self.master_ports = []
		cnt = 0	
		for xml_port in xml_root.find("master-ports"):
			port_id = int(xml_port.find("id").text)
			# VALIDATION: IDs need to be given consecutively and they need to start at 0
			if port_id != cnt:
				msg = "Reading tile \"%s\": Master-Ports need to be ordered"
				msg += " according to their IDs (starting at 0). Expected ID: %d Read ID: %d"
				msg %= (name, cnt, port_id)
				error(__file__, msg)
			self.master_ports.append({"label" : (port_id, "mp"), "location" : eval(xml_port.find("location").text)})
			cnt += 1
		# Read slave-ports
		self.slave_ports = []
		cnt = 0	
		for xml_port in xml_root.find("slave-ports"):
			port_id = int(xml_port.find("id").text)
			# VALIDATION: IDs need to be given consecutively and they need to start at 0
			if port_id != cnt:
				msg = "Reading tile \"%s\": Slave-Ports need to be ordered"
				msg += " according to their IDs (starting at 0). Expected ID: %d Read ID: %d"
				msg %= (name, cnt, port_id)
				error(__file__, msg)
			self.slave_ports.append({"label" : (port_id, "sp"), "location" : eval(xml_port.find("location").text)})
			cnt += 1
		# Read PHYs
		self.phys = []
		cnt = 0	
		for xml_phy in xml_root.find("phys"):
			phy_id = int(xml_phy.find("id").text)
			phy_direction = xml_phy.find("direction").text 
			# VALIDATION: IDs need to be given consecutively and they need to start at 0
			if phy_id != cnt:
				msg = "Reading tile \"%s\": PHYs need to be ordered"
				msg += " according to their IDs (starting at 0). Expected ID: %d Read ID: %d" 
				msg %= (name, cnt, phy_id)
				error(__file__, msg)
			self.phys.append({"label" : (phy_id, "p"), "location" : eval(xml_phy.find("location").text), "direction" : phy_direction})
			cnt += 1
		# Read connections
		self.internal_connections = []
		for xml_con in xml_root.find("connections"):
			con = eval(xml_con.text)
			# VALIDATION: Start- and Endpoint need to be valid
			for point in [con[0],con[-1]]:
				if point[-1] == "ep" and point[0] >= self.n_endpoints:
					msg = "Reading tile \"%s\": Connection \"%s\" references invalid endpoint"
					msg += " with ID %d. Highest endpoint id present in this tile is %d"
					msg %= (name, str(con), point[0], self.n_endpoints-1)
					error(__file__, msg)
				if point[-1] == "mp" and point[0] >= len(self.master_ports):
					msg = "Reading tile \"%s\": Connection \"%s\" references invalid master-"
					msg += "port with ID %d. Highest master-port id present in this tile is %d"
					msg %= (name, str(con), point[0], len(self.master_ports)-1)
					error(__file__, msg)
				if point[-1] == "sp" and point[0] >= len(self.slave_ports):
					msg = "Reading tile \"%s\": Connection \"%s\" references invalid slave-"
					msg += "port with ID %d. Highest slave-port id present in this tile is %d"
					msg %= (name, str(con), point[0], len(self.slave_ports)-1)
					error(__file__, msg)
				if point[-1] == "p" and point[0] >= len(self.phys):
					msg = "Reading tile \"%s\": Connection \"%s\" references invalid PHY with"
					msg += " ID %d. Highest PHY id present in this tile is %d"
					msg %= (name, str(con), point[0], len(self.phys)-1)
					error(__file__, msg)
			# Save connection
			self.internal_connections.append(con)
		# Compose grid
		self.grid = [["T" for i in range(self.n_cols)] for j in range(self.n_rows)]
		# Map locations to labels
		self.master_port_loc_to_lab = {}
		self.slave_port_loc_to_lab = {}
		self.phy_loc_to_lab = {}
		# Map labels to locations
		self.master_port_lab_to_loc = {}
		self.slave_port_lab_to_loc = {}
		self.phy_lab_to_loc = {}
		# Add master-ports
		for port_id in range(len(self.master_ports)):
			(row,col) = self.master_ports[port_id]["location"]
			self.grid[row][col] = "M"
			self.master_port_loc_to_lab[(row,col)] = (port_id, "mp")
			self.master_port_lab_to_loc[(port_id, "mp")] = (row,col)
		# Add master-ports
		for port_id in range(len(self.slave_ports)):
			(row,col) = self.slave_ports[port_id]["location"]
			self.grid[row][col] = "S"
			self.slave_port_loc_to_lab[(row,col)] = (port_id, "sp")
			self.slave_port_lab_to_loc[(port_id, "sp")] = (row,col)
		# Add phys
		for phy_id in range(len(self.phys)):
			(row,col) = self.phys[phy_id]["location"]
			self.grid[row][col] = "P"
			self.phy_loc_to_lab[(row,col)] = (phy_id, "p")
			self.phy_lab_to_loc[(phy_id, "p")] = (row,col)
		# Compose graph
		self.vertices = [("r",)]	
		self.vertices += [(i,"ep") for i in range(self.n_endpoints)]
		self.vertices += [(i,"mp") for i in range(len(self.master_ports))]
		self.vertices += [(i,"sp") for i in range(len(self.slave_ports))]
		self.vertices += [(i,"p") for i in range(len(self.phys))]
		self.edges = [con for con in self.internal_connections]	
		delay = self.n_rows * ucell.delay_v_in_cycles / 2 + self.n_cols * ucell.delay_h_in_cycles / 2 
		self.edge_delays = {edge : delay for edge in self.edges}

		# MODEL
		self.total_area_in_mm2 = self.n_rows * self.n_cols * ucell.area_in_mm2
		self.total_power_in_w = self.n_rows * self.n_cols * ucell.logic_power_in_w

	# Function to mirror a tile
	def mirror(self, xmirror, ymirror):
		# Mirror grid
		new_grid = [[None for i in range(self.n_cols)] for j in range(self.n_rows)]
		for row in range(self.n_rows):
			for col in range(self.n_cols):
				srow = (self.n_rows - 1 - row) if xmirror else row
				scol = (self.n_cols - 1 - col) if ymirror else col
				cell = self.grid[srow][scol]
				new_grid[row][col] = cell
		self.grid = new_grid

		# Adapt master ports
		new_mports = []
		new_master_port_loc_to_lab = {}
		new_master_port_lab_to_loc = {}
		for mport in self.master_ports:
			(orow, ocol) = mport["location"]
			label = mport["label"]
			row = (self.n_rows - 1 - orow) if xmirror else orow
			col = (self.n_cols - 1 - ocol) if ymirror else ocol
			new_loc = (row,col)
			new_mports.append({"label" : label, "location" : new_loc})
			new_master_port_loc_to_lab[new_loc] = label
			new_master_port_lab_to_loc[label] = new_loc
		self.master_ports = new_mports
		self.master_port_loc_to_lab = new_master_port_loc_to_lab
		self.master_port_lab_to_loc = new_master_port_lab_to_loc
		# Adapt slave ports
		new_sports = []
		new_slave_port_loc_to_lab = {}
		new_slave_port_lab_to_loc = {}
		for sport in self.slave_ports:
			(orow, ocol) = sport["location"]
			label = sport["label"]
			row = (self.n_rows - 1 - orow) if xmirror else orow
			col = (self.n_cols - 1 - ocol) if ymirror else ocol
			new_loc = (row,col)
			new_sports.append({"label" : label, "location" : new_loc})
			new_slave_port_loc_to_lab[new_loc] = label
			new_slave_port_lab_to_loc[label] = new_loc
		self.slave_ports = new_sports
		self.slave_port_loc_to_lab = new_slave_port_loc_to_lab
		self.slave_port_lab_to_loc = new_slave_port_lab_to_loc
		# Adapt phys 
		new_phys = []
		new_phy_loc_to_lab = {}
		new_phy_lab_to_loc = {}
		for phy in self.phys:
			(orow, ocol) = phy["location"]
			label = phy["label"]
			row = (self.n_rows - 1 - orow) if xmirror else orow
			col = (self.n_cols - 1 - ocol) if ymirror else ocol
			new_loc = (row,col)
			new_phys.append({"label" : label, "location" : new_loc, "direction" : phy["direction"]})
			new_phy_loc_to_lab[new_loc] = label
			new_phy_lab_to_loc[label] = new_loc
		self.phys = new_phys
		self.phy_loc_to_lab = new_phy_loc_to_lab
		self.phy_lab_to_loc = new_phy_lab_to_loc



