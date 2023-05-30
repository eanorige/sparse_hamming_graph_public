# Libraries
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Custom files
import config as cfg
from error import error, warning
 
# create an (un-embedded) tile
# name:				Tile name
# area:				Tile area in GE
# n_endpoints:		Number of endpoints
# mports:			List of master ports (dictionaries with face and align 
#					(of placement = auto) or location (placement = manual))
# sports:			List of slave ports (dictionaries with face and align 
#					(of placement = auto) or location (placement = manual))
# phys:				List of PHYs (dictionaries with location and direction)
# aspect_ration:	Ratio height:width of tile
# port placement:	either "auto" (pass location) or "manual" (pass face + alignment)
def create_tile(name, area, n_endpoints, mports, sports, phys = [], aspect_ratio = 1, port_placement = "auto"):
	print("Creating Tile \"%s\"..." % name, end = '')
	# Extract master- and slave-port as well as PHY count
	n_mports = len(mports)
	n_sports = len(sports)
	n_phys = len(phys)
	# Create XML file to store tile...
	xml_root = ET.Element("tile")
	# ...Add basic info
	ET.SubElement(xml_root, "tile_area_in_ge").text = str(area)
	ET.SubElement(xml_root, "n_endpoints").text = str(n_endpoints)
	ET.SubElement(xml_root, "height_width_ratio").text = str(aspect_ratio)
	ET.SubElement(xml_root, "port_placement").text = port_placement
	xml_cons = ET.SubElement(xml_root, "connections")
	# ...Add connections for endpoints <-> central router
	for i in range(n_endpoints):
		ET.SubElement(xml_cons, "connection").text = str(((i,"ep"),("r",)))
		ET.SubElement(xml_cons, "connection").text = str((("r",),(i,"ep")))
	# ...Add master-ports...
	xml_mports = ET.SubElement(xml_root, "master-ports")
	for i in range(n_mports):
		xml_port = ET.SubElement(xml_mports, "port")
		ET.SubElement(xml_port, "id").text = str(i)
		# ...Add face and alignment if auto-placement
		if port_placement == "auto":
			ET.SubElement(xml_port, "face").text = mports[i]["face"]
			ET.SubElement(xml_port, "align").text = str(mports[i]["align"])
		# ...Add location if manual-placement
		elif port_placement == "manual":
			ET.SubElement(xml_port, "location").text = str(mports[i]["location"])
		else:
			msg = "Invalid port placement method: %s"
			msg %= port_placement
			error(__file__, msg)
		# ...Add connections for central router -> master port
		ET.SubElement(xml_cons, "connection").text = str((("r",),(i,"mp")))
	# ...Add slave-ports...
	xml_sports = ET.SubElement(xml_root, "slave-ports")
	for i in range(n_sports):
		xml_port = ET.SubElement(xml_sports, "port")
		ET.SubElement(xml_port, "id").text = str(i)
		# ...Add face and alignment if auto-placement
		if port_placement == "auto":
			ET.SubElement(xml_port, "face").text = sports[i]["face"]
			ET.SubElement(xml_port, "align").text = str(sports[i]["align"])
		# ...Add location if manual-placement
		elif port_placement == "manual":
			ET.SubElement(xml_port, "location").text = str(sports[i]["location"])
		else:
			msg = "Invalid port placement method: %s"
			msg %= port_placement
			error(__file__, msg)
		# ...Add connections for slave-port -> central router
		ET.SubElement(xml_cons, "connection").text = str(((i,"sp"),("r",)))
	# ...Add slave-ports...
	xml_phys = ET.SubElement(xml_root, "phys")
	for i in range(n_phys):
		xml_phy = ET.SubElement(xml_phys, "phy")
		# ...Add basic PHY infor
		ET.SubElement(xml_phy, "id").text = str(i)
		ET.SubElement(xml_phy, "location").text = str(phys[i]["location"])
		ET.SubElement(xml_phy, "direction").text = str(phys[i]["direction"])
		phy_dir = phys[i]["direction"]
		# Add connection central router <- or -> PHY based on PHY direction
		if phy_dir == "in":
			ET.SubElement(xml_cons, "connection").text = str(((i,"p"),("r",)))
		elif phy_dir == "out":
			ET.SubElement(xml_cons, "connection").text = str((("r",),(i,"p")))
		else:
			msg = "Invalid phy direction: %s"
			msg %= phy_dir
			error(__file__, msg)
	# Save file
	xml_string = minidom.parseString(ET.tostring(xml_root)).toprettyxml(indent="\t")
	xml_file = open(cfg.unembedded_tile_path + name + ".xml", "w")
	xml_file.write(xml_string)
	print("saved tile as \"%s%s\"" % (cfg.unembedded_tile_path, name))

