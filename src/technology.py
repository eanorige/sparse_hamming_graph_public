# Libraries
import xml.etree.ElementTree as ET

# Custom files
import config as cfg

class Technology():

	def __init__(self, tech_name):
		xml_root = ET.parse(cfg.technology_path + tech_name + ".xml").getroot()
		self.mm2_per_ge = float(xml_root.find("mm2_per_ge").text)
		self.mm_per_vertical_wire = float(xml_root.find("mm_per_vertical_wire").text)
		self.mm_per_horizontal_wire = float(xml_root.find("mm_per_horizontal_wire").text)
		self.s_per_mm = eval(xml_root.find("s_per_mm").text)
		self.w_per_mm2_logic = float(xml_root.find("w_per_mm2_logic").text)
		self.w_per_mm2_wire = float(xml_root.find("w_per_mm2_wire").text)


