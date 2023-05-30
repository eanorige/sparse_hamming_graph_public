# Libraries
import xml.etree.ElementTree as ET

# Custom files
import config as cfg

class Protocol():

	def __init__(self, prot_name):
		xml_root = ET.parse(cfg.protocol_path + prot_name + ".xml").getroot()
		self.wires_per_connection = eval(xml_root.find("wires_per_connection").text)
		self.mux_area_in_ge = eval(xml_root.find("mux_area_in_ge").text)
		self.demux_area_in_ge = eval(xml_root.find("demux_area_in_ge").text)
		self.router_area_in_ge = eval(xml_root.find("router_area_in_ge").text)
		self.phy_area_in_ge = eval(xml_root.find("phy_area_in_ge").text)


