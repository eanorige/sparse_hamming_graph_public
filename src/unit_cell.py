from technology import Technology
from protocol import Protocol

class UnitCell():
	def __init__(self, tech_name, prot_name, bw, f):
		tech = Technology(tech_name)
		prot = Protocol(prot_name)
		self.width_in_mm = tech.mm_per_vertical_wire * prot.wires_per_connection(bw)
		self.height_in_mm = tech.mm_per_horizontal_wire * prot.wires_per_connection(bw)
		self.area_in_mm2 = self.width_in_mm * self.height_in_mm
		self.delay_h_in_cycles = tech.s_per_mm * self.width_in_mm * f
		self.delay_v_in_cycles = tech.s_per_mm * self.height_in_mm * f
		self.logic_power_in_w = tech.w_per_mm2_logic * self.area_in_mm2
		self.wire_power_in_w = tech.w_per_mm2_wire * self.area_in_mm2
