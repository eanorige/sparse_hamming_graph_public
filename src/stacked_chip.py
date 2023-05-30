# Libraries
import xml.etree.ElementTree as ET

# Custom files
import config as cfg
from tile import Tile
from module import Module
from error import error, warning

class StackedChip:
	# Read stacked chip from file
	def read_from_file(self):
		# Read XML file
		xml_root = ET.parse(cfg.stacked_chip_path + self.name + ".xml").getroot()
		# Read basic stacked chip info
		self.width_in_mm= float(xml_root.find("width_in_mm").text)
		self.height_in_mm= float(xml_root.find("height_in_mm").text)
		# Read Chiplets 
		self.chiplets = []
		cnt = 0	
		for xml_chiplet in xml_root.find("chiplets"):
			chiplet = {}
			chiplet["id"] = int(xml_chiplet.find("id").text)
			chiplet["name"] = name = xml_chiplet.find("name").text
			chiplet["location"] = eval(xml_chiplet.find("location").text)
			chiplet["rotation"] = int(xml_chiplet.find("rotation").text)
			chiplet["width"] = float(xml_chiplet.find("width").text)
			chiplet["height"] = float(xml_chiplet.find("height").text)
			chiplet["object"] = Module(chiplet["name"])
			chiplet["phys"] = []
			# Read PHYs inside chiplet
			for xml_phy in xml_chiplet.find("phys"):
				phy = {}
				phy["label"] = eval(xml_phy.find("label").text)
				phy["location"] = eval(xml_phy.find("location").text)
				phy["direction"] = xml_phy.find("direction").text
				chiplet["phys"].append(phy)
			self.chiplets.append(chiplet)
			# VALIDATION: IDs need to be given consecutively and they need to start at 0
			if chiplet["id"] != cnt:
				msg = "While reading stacked chip \"%s\": Chiplets need to be ordered"
				msg += " according to their IDs (starting at 0). Expected ID: %d Read ID: %d"
				msg %= (self.name, cnt, chiplet_id)
				error(__file__, msg)
			cnt += 1

		# Read connections
		self.connections = []
		for xml_con in xml_root.find("connections"):
			self.connections.append(eval(xml_con.text))

	# Compose the stacked chip's graph (logical model)
	def compose_graph(self):
		# Construct Graph
		self.vertices = []
		self.edges = []
		self.edge_delays = {}
		# Add components (vertices)
		for chiplet_id in range(len(self.chiplets)):
			chiplet = self.chiplets[chiplet_id]
			# Add chiplet's vertices
			for label in chiplet["object"].vertices:
				self.vertices.append((chiplet_id, ) + label)
			# Add chiplet's edges
			for (s_label, e_label) in chiplet["object"].edges:
				edge = ((chiplet_id, ) + s_label, (chiplet_id, ) + e_label)
				self.edges.append(edge)
				self.edge_delays[edge] = chiplet["object"].edge_delays[(s_label, e_label)]
		# Add own connections (edges)
		for i in range(len(self.connections)):
			(start, end, delay) = self.connections[i]
			# Validation: Start at PHY
			if start[-1] != "p":
				msg = "While reading stacked chip \"%s\": Connection %s needs to start at a PHY"
				msg %= (self.name, con)
				error(__file__, msg)
			# Validation: End at PHY
			if end[-1] != "p":
				msg = "While reading stacked chip \"%s\": Connection %s needs to end at a PHY"
				msg %= (self.name, con)
				error(__file__, msg)
			self.edges.append((start, end))
			self.edge_delays[edge] = delay

	# Initialization: Read all info about the tile from module
	def __init__(self, name):
		self.name = name
		self.read_from_file()
		self.compose_graph()

		# MODEL: Compute total area and power
		self.total_area_in_mm2 = self.height_in_mm * self.width_in_mm
		component_power = sum([cplt["object"].total_power_in_w for cplt in self.chiplets])
		# TODO: Add a power model for the interposer.
		self.total_power_in_w = component_power


