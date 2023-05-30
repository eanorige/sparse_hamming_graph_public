# Libraries
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Custom files
import config as cfg
from module import Module
from error import error, warning
from interposer import Interposer
from unit_cell import UnitCell

# Auxiliary function: Component-wise addition of 2-tuples
def tadd(a,b):
	return (a[0] + b[0], a[1] + b[1])

# Auxiliary function: Get a specific corner of a rectangle
def get_corners(rectangle):
	((x,y),(w,h)) = rectangle
	corners = {	"bottom-left" : {"x" : x, "y" : y},
				"bottom-right" : {"x" : x + w, "y" : y},
				"top-left" : {"x" : x, "y" : y + h},
				"top-right" : {"x" : x + w, "y" : y + h}}
	return corners

# Auxiliary function: Check if one rectangle is completely within another rectangle
def is_within(outer, inner, padding):
	out = get_corners(outer)
	inn = get_corners(inner)
	within = True	
	within &= out["bottom-left"]["x"] + padding < inn["bottom-left"]["x"]
	within &= out["bottom-left"]["y"] + padding < inn["bottom-left"]["y"]
	within &= out["top-left"]["x"] + padding < inn["top-left"]["x"]
	within &= out["top-left"]["y"] > inn["top-left"]["y"] + padding
	within &= out["bottom-right"]["x"] > inn["bottom-right"]["x"] + padding
	within &= out["bottom-right"]["y"] + padding < inn["bottom-right"]["y"]
	within &= out["top-right"]["x"] > inn["top-right"]["x"] + padding
	within &= out["top-right"]["y"] > inn["top-right"]["y"] + padding

	return within

# Auxiliary function: Check if one rectangle intersects with another rectangle
def do_intersect(first, second, spacing):
	fst = get_corners(first)
	snd = get_corners(second)
	no_collision = False
	for dim in ["x","y"]:
		no_collision |= (fst["top-right"][dim] + spacing) < snd["bottom-left"][dim]	
		no_collision |= fst["bottom-left"][dim] > (snd["top-right"][dim] + spacing)
	return not no_collision
 
# Function to create stacked chips
# name: 			Name of the stacked chip
# interposer_name:	Name of the interposer-input-file to be used
# schip_width		Width of the stacked chip in mm
# schip_height		Height of the stacked chip in mm
# chiplets:			List of chiplets (dictionaries with name, location, [rotation]) 
# connections:		List of connections
def create_stacked_chip(name, interposer_name, schip_width, schip_height, chiplets, connections, bw, freq):
	print("Creating 2.5D Stacked Chip \"%s\"..." % name, end = '')

	# Get number of chiplets
	n_chiplets = len(chiplets)
	# Read interposer info
	interp = Interposer(interposer_name)

	# Complete chiplet info...
	for chiplet in chiplets:
		# ...load chiplet
		obj = Module(chiplet["name"])
		chiplet["object"] = obj
		ucell = UnitCell(obj.technology, obj.protocol, obj.bandwidth, obj.frequency)
		chiplet["ucell"] = ucell
		# ...set rotation to 0 if not specified
		if "rotation" not in chiplet:
			chiplet["rotation"] = 0
		# ...Compute chiplet width and height w.r.t. rotation
		width = obj.n_cols * ucell.width_in_mm
		height = obj.n_rows * ucell.height_in_mm
		chiplet["width"] = width if chiplet["rotation"] % 2 == 0 else height
		chiplet["height"] = height if chiplet["rotation"] % 2 == 0 else width 
		# ...Compute location of PHYs w.r.t. rotation
		for phy in obj.phys:
			(w,h) = (width,height)
			(oldy, oldx) = phy["location"]
			newx = oldx / obj.n_cols * w
			newy = oldy / obj.n_rows * h
			for i in range(chiplet["rotation"]):
				(newx, newy) = (newy, w - newx)
				(w,h) = (h,w)
			phy["location"] = (newx, newy)

	# VALIDATION: Check that all u-bumps fit on chiplet
	for chiplet in chiplets:
		obj = chiplet["object"]
		ucell = chiplet["ucell"]
		ubumps_needed = len(obj.phys) * interp.f_bandwidth_ubumps(bw)
		chiplet_area = chiplet["object"].n_rows * chiplet["object"].n_cols * ucell.area_in_mm2
		ubumps_available = interp.signal_ubumps_per_mm2 * chiplet_area 
		if ubumps_needed > ubumps_available:
			msg = "Chiplet \"%s\" has %d u-bumps but only %d fit on it's area"
			msg %= (chiplet["object"].name, ubumps_needed, int(ubumps_available))
			error(__file__, msg)

	# VALIDATION: Check that chiplets are within interposer and that they do not overlap
	border = ((0,0),(schip_width, schip_height))
	for first in chiplets:
		fst = (first["location"],(first["width"],first["height"]))
		# Check for chiplets that exceed interposer border
		if not is_within(border, fst, interp.padding):
			msg = "Chiplet is out of bounds or padding is violated"
			error(__file__, msg)
		# Check for overlapping chiplets
		for second in chiplets:
			if second != first:
				snd = (second["location"],(second["width"],second["height"]))
				if do_intersect(fst, snd, interp.spacing):
					msg = "Two chiplets are intersecting or spacing is violated"
					error(__file__, msg)

	# Compute connection lengths and delays...
	connections_with_data = []
	for con  in connections:
		# ...Get connection details
		((c1,m1,p1,l1), (c2,m2,p2,l2)) = con
		# ...Get location of start PHY
		phy1_loc = None
		chiplet = chiplets[c1]
		for phy in chiplet["object"].phys:
			if phy["label"] == (m1,p1,l1):
				phy1_loc = tadd(chiplet["location"], phy["location"])
		# ...Get location of end PHY
		phy2_loc = None
		chiplet = chiplets[c2]
		for phy in chiplet["object"].phys:
			if phy["label"] == (m2,p2,l2):
				phy2_loc = tadd(chiplet["location"], phy["location"])
		# ...Compute connection length based on on-interposer connection routing
		if interp.connection_routing == "manhattan":
			con_len_in_mm = abs(phy1_loc[0] - phy2_loc[0]) + abs(phy1_loc[1] - phy2_loc[1])
		else:
			msg = "Unsupported connection routing: \"%s\""
			msg %= interp.connection_routing
			error(__file__, msg)
		# ... Compute connection latency
		con_delay_in_s = interp.f_length_in_mm_delay_in_s(con_len_in_mm)
		con_delay_in_cycles = con_delay_in_s * freq + 2 * interp.phy_delay_in_cycles
		connections_with_data.append(con + (con_len_in_mm, con_delay_in_cycles))

	# VALIDATION: Check that no on-interposer connections exceeds the maximum length
	for (start, end, length, latency) in connections_with_data:
		if length > interp.max_connection_length_in_mm:
			msg = "A connection with length %f mm exceeds the maximum connection length of %f mm"
			msg %= (length, interp.max_connection_length_in_mm)
			error(__file__, msg)

	# Create XML file for the stacked chip...
	xml_root = ET.Element("stacked_chip")
	# ...Height and width of stacked chip
	ET.SubElement(xml_root, "width_in_mm").text = str(schip_width)
	ET.SubElement(xml_root, "height_in_mm").text = str(schip_height)
	# ...Add Chiplets...
	xml_chiplets = ET.SubElement(xml_root, "chiplets")
	for i in range(n_chiplets):
		xml_chiplet = ET.SubElement(xml_chiplets, "chiplet")
		ET.SubElement(xml_chiplet, "id").text = str(i)
		ET.SubElement(xml_chiplet, "name").text = chiplets[i]["name"] 
		ET.SubElement(xml_chiplet, "location").text = str(chiplets[i]["location"])
		ET.SubElement(xml_chiplet, "rotation").text = str(chiplets[i]["rotation"])
		ET.SubElement(xml_chiplet, "width").text = str(chiplets[i]["width"])
		ET.SubElement(xml_chiplet, "height").text = str(chiplets[i]["height"])
		# ...Add PHSs within chiplet
		xml_phys = ET.SubElement(xml_chiplet, "phys")
		for j in range(len(chiplets[i]["object"].phys)):
			phy = chiplets[i]["object"].phys[j]
			xml_phy = ET.SubElement(xml_phys, "phy")
			ET.SubElement(xml_phy, "label").text = str(phy["label"])
			ET.SubElement(xml_phy, "location").text = str(phy["location"])
			ET.SubElement(xml_phy, "direction").text = str(phy["direction"])
	# ... Add Connections
	xml_connections = ET.SubElement(xml_root, "connections")
	for (start, end, length, latency) in connections_with_data:
		ET.SubElement(xml_connections, "connection").text = str((start,end,latency))
	# Save file
	xml_string = minidom.parseString(ET.tostring(xml_root)).toprettyxml(indent="\t")
	xml_file = open(cfg.stacked_chip_path + name + ".xml", "w")
	xml_file.write(xml_string)
	print("saved 2.5D stacked chip as \"%s%s\"" % (cfg.stacked_chip_path, name))
	

