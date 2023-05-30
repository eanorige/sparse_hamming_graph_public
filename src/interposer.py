# Libraries
import xml.etree.ElementTree as ET

# Custom files 
import config as cfg

class Interposer():
	def __init__(self, interposer_name):
		xml_root = ET.parse(cfg.interposer_path + interposer_name + ".xml").getroot()
		self.spacing = float(xml_root.find("chiplet_spacing").text)
		self.padding = float(xml_root.find("schip_padding").text)
		self.f_length_in_mm_delay_in_s= eval(xml_root.find("f_length_in_mm_delay_in_s").text)
		self.max_connection_length_in_mm = float(xml_root.find("max_connection_length_in_mm").text)
		self.phy_delay_in_cycles = float(xml_root.find("phy_delay_in_cycles").text)
		self.connection_routing = xml_root.find("connection_routing").text
		self.signal_ubumps_per_mm2 = float(xml_root.find("signal_ubumps_per_mm2").text)
		self.f_bandwidth_ubumps = eval(xml_root.find("f_bandwidth_ubumps").text)

