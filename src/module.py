# Libraries
import xml.etree.ElementTree as ET

# Custom Files 
import config as cfg
from error import error, warning
from unit_cell import UnitCell
from tile import Tile

class Module:
	# Read (embedded) module from file
	def read_from_file(self):
		# Read XML file
		xml_root = ET.parse(cfg.module_path + self.name + ".xml").getroot()
		# Read basic tile-info
		self.technology = xml_root.find("technology").text
		self.protocol = xml_root.find("protocol").text
		self.bandwidth = int(xml_root.find("bandwidth").text)
		self.frequency = int(xml_root.find("frequency").text)
		self.n_rows = int(xml_root.find("n_rows").text)
		self.n_cols = int(xml_root.find("n_cols").text)
		# Read Components...
		self.components = []
		cnt = 0	
		for xml_comp in xml_root.find("components"):
			comp = {}
			# ...Read basic info
			comp_id = int(xml_comp.find("id").text)
			comp_type = xml_comp.find("type").text
			comp_name = xml_comp.find("name").text
			comp["location"] = eval(xml_comp.find("location").text)
			comp["xmirror"] = xml_comp.find("xmirror").text == "True"
			comp["ymirror"] = xml_comp.find("ymirror").text == "True"
			# ...VALIDATION: IDs need to be given consecutively and they need to start at 0
			if comp_id != cnt:
				msg = " While reading module \"%s\": Components need to be ordered"
				msg += " according to their IDs (starting at 0). Expected ID: %d Read ID: %d"
				msg %= (self.name, cnt, comp_id)
				error(__file__, msg)
			# ...Read tile or module
			if comp_type == "tile":
				comp["object"] = Tile(comp_name)
			elif comp_type == "module":
				comp["object"] = Module(comp_name)
			else:
				msg = " While reading module \"%s\": Invalid component type \"%d\""
				msg += " for component with ID %d. Only \"tile\" and \"module\" are valid."
				msg %= (self.name, comp_id)
				error(__file__, msg)
			# ...Apply component mirroring
			comp["object"].mirror(comp["xmirror"], comp["ymirror"])
			# ... Store component
			self.components.append(comp)
			cnt += 1
		# Read connections
		self.connections = []
		for xml_con in xml_root.find("connections"):
			self.connections.append(eval(xml_con.text))

	# Compose the module's grid (physical model)
	def compose_grid(self):
		# Compose grid
		self.grid = [[[0,0] for i in range(self.n_cols)] for j in range(self.n_rows)]
		self.tiles = []
		self.master_ports = []
		self.slave_ports = []
		self.phys = []
		# Map locations to labels
		self.master_port_loc_to_lab = {}
		self.slave_port_loc_to_lab = {}
		self.phy_loc_to_lab = {}
		# Map labels to locations
		self.master_port_lab_to_loc = {}
		self.slave_port_lab_to_loc = {}
		self.phy_lab_to_loc = {}
		# Add Components
		for cid in range(len(self.components)):
			# Basic
			comp = self.components[cid]
			comp_obj = comp["object"]
			(r,c) = comp["location"] 
			# Add component to own grid
			comp_grid = comp_obj.grid
			comp_n_rows = len(comp_grid)
			comp_n_cols = len(comp_grid[0])
			for row in range(comp_n_rows):
				for col in range(comp_n_cols):
					cell_content = comp_grid[row][col]
					if type(cell_content) == str:
						if self.grid[r + row][c + col] == [0,0]:
							self.grid[r + row][c + col] = cell_content
						else:
							msg = "Collision between components"
							error(__file__, msg)
			# Add component's tiles
			for tile in comp_obj.tiles:
				dimensions = tile["dimensions"]	
				(row,col) = tile["location"] 
				self.tiles.append({"location" : (r + row, c + col), "dimensions" : dimensions})

			# Add component's connections
			for con in comp_obj.connections:
				new_con = []
				for (row,col) in con:
					new_con.append((r + row, c + col))
				self.connections.append(new_con)

			# Add component's master-ports
			for mport in comp_obj.master_ports:
				label = mport["label"]
				(row,col) = mport["location"]
				new_lab = (cid, ) + label
				new_loc = (r + row, c + col)
				new_mport = {"label" : new_lab, "location" : new_loc}
				self.master_ports.append(new_mport)
				self.master_port_loc_to_lab[new_loc] = new_lab
				self.master_port_lab_to_loc[new_lab] = new_loc
			# Add component's slave-ports
			for sport in comp_obj.slave_ports:
				label = sport["label"]
				(row,col) = sport["location"]
				new_lab = (cid, ) + label
				new_loc = (r + row, c + col)
				new_sport = {"label" : new_lab, "location" : new_loc}
				self.slave_ports.append(new_sport)
				self.slave_port_loc_to_lab[new_loc] = new_lab
				self.slave_port_lab_to_loc[new_lab] = new_loc
			# Add component's phys
			for phy in comp_obj.phys:
				label = phy["label"]
				(row,col) = phy["location"]
				new_lab = (cid, ) + label
				new_loc = (r + row, c + col)
				new_phy = {"label" : new_lab, "location" : new_loc, "direction" : phy["direction"]}
				self.phys.append(new_phy)
				self.phy_loc_to_lab[new_loc] = new_lab
				self.phy_lab_to_loc[new_lab] = new_loc

		# Add Connections
		collision_count = 0
		for con in self.connections:
			# Build full connection: Series of adjacent cells
			full_con = []
			for i in range(len(con)-1):
				if con[i][0] == con[i+1][0]:
					direction = (1 if con[i][1] < con[i+1][1] else -1)
					for col in range(con[i][1], con[i+1][1], direction):
						full_con.append((con[i][0], col))
				elif con[i][1] == con[i+1][1]:
					direction = (1 if con[i][0] < con[i+1][0] else -1)
					for row in range(con[i][0], con[i+1][0], direction):
						full_con.append((row, con[i][1]))
				else:
					msg = " While reading module \"%s\": Connection %s changes row and "
					msg += " column in same hop which is illegal"
					msg %= (self.name, str(con))
					error(__file__, msg)
			full_con.append(con[-1])
			# Add full connection to grid
			for i in range(1, len(full_con)-1):	
				prv = full_con[i-1]
				(r,c) = cur = full_con[i]
				nxt = full_con[i+1]
				in_dir = "H" if prv[0] == cur[0] else "V"
				out_dir = "H" if cur[0] == nxt[0] else "V"
				if type(self.grid[r][c]) == list:
					if in_dir == "H" or out_dir == "H":
						if self.grid[r][c][0] > 0:
							collision_count += 1
						self.grid[r][c][0] += 1
					if in_dir == "V" or out_dir == "V":
						if self.grid[r][c][1] > 0:
							collision_count += 1
						self.grid[r][c][1] += 1
				else:
					msg = " While reading module \"%s\": Connection %s tries to use"
					msg += " a cell that is already occupied by a tile: %s"
					msg %= (self.name, str(con), str(cur))



	# Compose the module's graph (logical model)
	def compose_graph(self, ucell):
		# Construct Graph
		self.vertices = []
		self.edges = []
		self.edge_delays = {}
		# Add components
		for comp_id in range(len(self.components)):
			comp = self.components[comp_id]
			# Add component's vertices
			for label in comp["object"].vertices:
				self.vertices.append((comp_id, ) + label)
			# Add component's edges
			for (s_label, e_label) in comp["object"].edges:
				edge = ((comp_id, ) + s_label, (comp_id, ) + e_label)
				self.edges.append(edge)
				self.edge_delays[edge] = comp["object"].edge_delays[(s_label, e_label)]
		# Add own connections
		for con in self.connections:
			s_label = self.master_port_loc_to_lab[(con[0][0],con[0][1])]
			e_label = self.slave_port_loc_to_lab[(con[-1][0],con[-1][1])]
			edge = (s_label, e_label)
			self.edges.append(edge)
			delay = sum([abs(con[i][0] - con[i+1][0]) * ucell.delay_h_in_cycles + \
						 abs(con[i][1] - con[i+1][1]) * ucell.delay_v_in_cycles \
						 for i in range(len(con) -1)])
			self.edge_delays[edge] = delay

	# Mirror this module
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
		# Adapt tiles
		for tile in self.tiles:	
			(orow, ocol) = tile["location"]
			(height, width) = tile["dimensions"]
			row = (self.n_rows - orow - height) if xmirror else orow
			col = (self.n_cols - ocol - width) if ymirror else ocol
			tile["location"] = (row,col)
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
		# Adapt connections
		new_cons = []
		for con in self.connections:
			new_con = []
			for (orow,ocol) in con:
				row = (self.n_rows - 1 - orow) if xmirror else orow
				col = (self.n_cols - 1 - ocol) if ymirror else ocol
				new_con.append((row,col))
			new_cons.append(new_con)
		self.connections = new_cons

	# Initialization Read all info about the tile from module
	def __init__(self, name):
		self.name = name

		# Read module from file
		self.read_from_file()

		# Compute unit cell properties
		ucell = UnitCell(self.technology, self.protocol, self.bandwidth, self.frequency)

		# Compose grid (physical model) and graph (logical model)
		self.compose_grid()
		self.compose_graph(ucell)

		# MODEL: Compute area, power...

		# ...Count number of unit cells occupied by logic, wires, nothing
		n_logic_cells = 0
		n_wire_cells = 0
		n_h_wire_cells = 0
		n_v_wire_cells = 0
		n_empty_cells = 0
		for row in range(self.n_rows):
			for col in range(self.n_cols):
				if type(self.grid[row][col]) == str and self.grid[row][col] in ["T","S","M","P"]:
					n_logic_cells += 1
				elif (type(self.grid[row][col]) == list) and (max(self.grid[row][col]) > 0):
					n_wire_cells += 1
					n_h_wire_cells += self.grid[row][col][0]
					n_v_wire_cells += self.grid[row][col][1]
				else:
					n_empty_cells += 1

		# Area computation
		# The no-noc area needs to be computed in the evaluation file
		self.total_area_in_mm2 = self.n_rows * self.n_cols * ucell.area_in_mm2
		self.logic_area_in_mm2 = n_logic_cells * ucell.area_in_mm2
		self.wire_area_in_mm2 = n_wire_cells * ucell.area_in_mm2
		self.empty_area_in_mm2 = n_empty_cells * ucell.area_in_mm2

		# Power computation
		# The no-noc power needs to be computed in the evaluation file
		self.logic_power_in_w = n_logic_cells * ucell.logic_power_in_w
		self.wire_power_in_w = (1/2) * (n_h_wire_cells+n_v_wire_cells) * ucell.wire_power_in_w
		self.total_power_in_w = self.logic_power_in_w + self.wire_power_in_w
