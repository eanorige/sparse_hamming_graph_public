# Libraries
import xml.etree.ElementTree as ET
from xml.dom import minidom
import math
import sys

# Custom files
import config as cfg
from error import error, warning
from unit_cell import UnitCell
from technology import Technology
from protocol import Protocol

# Embeds a given tile in the grid
# tile_name:		"Name of tile (both un-embedded and embedded)
# tech_name:		Name of technology node file
# prot_name:		Name of on-chip transport protocol file
# bw:				Bandwidth in bits/cycle
# freq:				Frequency in GHz
def embed_tile_in_grid(tile_name, tech_name, prot_name, bw, freq):
	print("Embedding tile \"%s\"..." % tile_name, end = '')
	# Read XML file containing un-embedded tile info...
	xml_root = ET.parse(cfg.unembedded_tile_path + tile_name + ".xml").getroot()
	# ...Read general tile info
	logic_area_in_ge = int(xml_root.find("tile_area_in_ge").text)
	n_endpoints = int(xml_root.find("n_endpoints").text)
	height_width_ratio = float(xml_root.find("height_width_ratio").text)
	port_placement = xml_root.find("port_placement").text
	# ...Read and validate master ports...
	cnt = 0
	master_ports = []
	for xml_port in xml_root.find("master-ports"):
		new_port = {}
		# ...Read master port
		new_port["id"] = int(xml_port.find("id").text)
		if port_placement == "auto":
			new_port["face"] = xml_port.find("face").text
			new_port["align"] = int(xml_port.find("align").text)
		elif port_placement == "manual":
			new_port["location"] = eval(xml_port.find("location").text)
		else:
			msg = "Invalid port placement method: %s"
			msg %= port_placement
			error(__file__, msg)
		# ...VALIDATION: Port IDs must be consecutive
		if new_port["id"] != cnt:
			msg = "While reading tile \"%s\": Master-Ports need to be ordered"
			msg += " according to their IDs (starting at 0). Expected ID: %d Read ID: %d"
			msg %= (tile_name, cnt, new_port["id"])
			error(__file__, msg)
		cnt += 1
		# ...Store master port
		master_ports.append(new_port)
	# ...Read and validate slave ports...
	cnt = 0
	slave_ports = []
	for xml_port in xml_root.find("slave-ports"):
		new_port = {}
		# ...Read slave port
		new_port["id"] = int(xml_port.find("id").text)
		if port_placement == "auto":
			new_port["face"] = xml_port.find("face").text
			new_port["align"] = int(xml_port.find("align").text)
		elif port_placement == "manual":
			new_port["location"] = eval(xml_port.find("location").text)
		else:
			msg = "Invalid port placement method: %s"
			msg %= port_placement
			error(__file__, msg)
		# ...VALIDATION: Port IDs must be consecutive
		if new_port["id"] != cnt:
			msg = "While reading tile \"%s\": Slave-Ports need to be ordered"
			msg += " according to their IDs (starting at 0). Expected ID: %d Read ID: %d"
			msg %= (tile_name, cnt, new_port["id"])
			error(__file__, msg)
		cnt += 1
		# ...Store slave port
		slave_ports.append(new_port)
	# ...Read and validate PHYs...
	cnt = 0
	phys = []
	for xml_phy in xml_root.find("phys"):
		new_phy = {}
		# ...Read PHY
		new_phy["id"] = int(xml_phy.find("id").text)
		new_phy["location"] = eval(xml_phy.find("location").text)
		new_phy["direction"] = xml_phy.find("direction").text
		# VALIDATION: PHY IDs must be consecutive
		if new_phy["id"] != cnt:
			msg = "While reading tile \"%s\": PHYs need to be ordered"
			msg += " according to their IDs (starting at 0). Expected ID: %d Read ID: %d"
			msg %= (tile_name, cnt, new_phy["id"])
			error(__file__, msg)
		cnt += 1
		# Save PHY
		phys.append(new_phy)
	# ...Read connections
	connections = []
	for xml_con in xml_root.find("connections"):
		connections.append(eval(xml_con.text))

	# Read XML file containing technology info
	tech = Technology(tech_name)

	# Read XML file containing protocol info
	prot = Protocol(prot_name)	

	# Compute unit cell properties
	ucell = UnitCell(tech_name, prot_name, bw, freq)
	
	# Number of master and slave ports of central router
	s = n_endpoints + len(slave_ports)
	m = n_endpoints + len(master_ports)

	# MODEL: Area of embedded tile
	router_area_in_ge = prot.router_area_in_ge(prot.mux_area_in_ge, prot.demux_area_in_ge, s, m, bw)
	phy_area_in_ge = len(phys) * prot.phy_area_in_ge(bw)
	tile_area_in_ge = logic_area_in_ge + router_area_in_ge + phy_area_in_ge
	tile_area_in_mm2 = tile_area_in_ge * tech.mm2_per_ge
	tile_height_in_mm = math.sqrt(height_width_ratio * tile_area_in_mm2)
	tile_width_in_mm = math.sqrt(tile_area_in_mm2 / height_width_ratio)
	tile_width_in_cells = int(round(tile_width_in_mm / ucell.width_in_mm))
	tile_height_in_cells = int(round(tile_height_in_mm / ucell.height_in_mm))


	# Compute port locations for auto-placement
	if port_placement == "auto":
		# ...Count ports per face	
		faces = ["north","east","south","west"]
		port_cnt = {f : 0 for f in faces}
		for port in master_ports + slave_ports:
			port_cnt[port["face"]] += 1	
		# ...VALIDATION: ports must fit on given face
		port_limit = {	"north" : tile_width_in_cells-1,
						"east" : tile_height_in_cells-1,
						"south" : tile_width_in_cells-1,
						"west" : tile_height_in_cells-1	}
		for face in faces:
			if port_cnt[face] > port_limit[face]:
				msg = "Not able to fit all ports on %s-faces of tile"
				msg %= face
				error(__file__, msg)
		# ...Compute port locations
		face_start= {	"north" : 1, 
						"east" : 1, 
						"south" : 1, 
						"west" : 1}
		face_end = {	"north" : tile_width_in_cells - 2, 
						"east" : tile_height_in_cells - 2, 
						"south" : tile_width_in_cells -2, 
						"west" : tile_height_in_cells -2 }
		fixed_dim = {	"north" : tile_height_in_cells - 1, 
						"east" : tile_width_in_cells - 1, 
						"south" : 0, 
						"west" : 0}
		moving_dim = {-1 : face_start, 1 : face_end}
		nports = sum([1 for x in master_ports + slave_ports if x["face"] == "north"])
		sports = sum([1 for x in master_ports + slave_ports if x["face"] == "south"])
		eports = sum([1 for x in master_ports + slave_ports if x["face"] == "east"])
		wports = sum([1 for x in master_ports + slave_ports if x["face"] == "west"])
		h_spacing = max(1, math.floor(tile_width_in_cells / max(nports, sports, 1)))
		v_spacing = max(1, math.floor(tile_height_in_cells / max(eports, wports, 1)))
		for port in master_ports + slave_ports:
			face = port["face"]
			align = port["align"]
			if face in ["north","south"]:
				row = fixed_dim[face]
				col = moving_dim[align][face]
				moving_dim[align][face] -= align * h_spacing
				port["location"] = (row,col)
			if face in ["east","west"]:
				col = fixed_dim[face]
				row = moving_dim[align][face]
				moving_dim[align][face] -= align * v_spacing
				port["location"] = (row,col)
	# VALIDATION: Port must be on border of tile
	elif port_placement == "manual":
		for port in master_ports + slave_ports:
			loc = port["location"]
			if not (loc[0] in [0,tile_height_in_cells-1] or loc[1] in [0,tile_width_in_cells-1]):
				msg = "Port with id %d and location %s is not on the border of tile %s"
				msg %= (port["id"], str(loc), tile_name) 
				error(__file__, msg)

	# VALIDATION: Ports and / or PHYs can not overlap 
	taken_locations = []
	for item in master_ports + slave_ports + phys:
		loc = item["location"]
		if loc in taken_locations:
			msg = "Port or PHY location %s is placed on a unit-cell that is already occupied"
			msg %= str(loc)
			error(__file__, msg)
		else:
			taken_locations.append(loc)

	# Compose XML file for embedded tile...
	xml_root = ET.Element("tile")	
	# ...Add basic info
	ET.SubElement(xml_root, "technology").text = tech_name
	ET.SubElement(xml_root, "protocol").text = prot_name
	ET.SubElement(xml_root, "bandwidth").text = str(bw)
	ET.SubElement(xml_root, "frequency").text = str(freq)
	ET.SubElement(xml_root, "n_rows").text = str(tile_height_in_cells)
	ET.SubElement(xml_root, "n_cols").text = str(tile_width_in_cells)
	ET.SubElement(xml_root, "n_endpoints").text = str(n_endpoints)
	# ...Add master ports
	xml_mports = ET.SubElement(xml_root, "master-ports")
	for port_id in range(len(master_ports)):
		port = master_ports[port_id]
		xml_port = ET.SubElement(xml_mports, "port")
		ET.SubElement(xml_port, "id").text = str(port["id"])
		ET.SubElement(xml_port, "location").text = str(port["location"])
	# ...Add slave ports
	xml_mports = ET.SubElement(xml_root, "slave-ports")
	for port_id in range(len(slave_ports)):
		port = slave_ports[port_id]
		xml_port = ET.SubElement(xml_mports, "port")
		ET.SubElement(xml_port, "id").text = str(port["id"])
		ET.SubElement(xml_port, "location").text = str(port["location"])
	# ...Add PHYs
	xml_phys = ET.SubElement(xml_root, "phys")
	for phy_id in range(len(phys)):
		phy = phys[phy_id]
		xml_phy = ET.SubElement(xml_phys, "phy")
		ET.SubElement(xml_phy, "id").text = str(phy["id"])
		ET.SubElement(xml_phy, "location").text = str(phy["location"])
		ET.SubElement(xml_phy, "direction").text = str(phy["direction"])
	# ...Add connections
	xml_connections = ET.SubElement(xml_root, "connections")
	for connection in connections:
		ET.SubElement(xml_connections, "connection").text = str(connection)
	# Save file
	xml_string = minidom.parseString(ET.tostring(xml_root)).toprettyxml(indent="\t")
	xml_file = open(cfg.tile_path + tile_name+ ".xml", "w")
	xml_file.write(xml_string)
	print("saved tile as \"%s%s\"" % (cfg.tile_path, tile_name))
	return tile_name 

### Main ###
if __name__ == "__main__":
	args = sys.argv
	if len(args) < 6:
		  print("Usage: python embed_tile_in_grid.py <tile-name> <tech-name> <prot-name> <bw> <freq>")
		  sys.exit()
	embed_tile_in_grid(args[1], args[2], args[3], int(args[4]), int(float(args[5])))
