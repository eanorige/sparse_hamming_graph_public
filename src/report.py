# Libraries
import sys

# Custom files
from tile import Tile
from module import Module
from stacked_chip import StackedChip
from error import error

# Read a component (tile, module, or 2.5D stacked chip) and report area and power
def read_and_report(typ, name):
	entity = None
	additional_info = {}
	# Tile
	if typ == "tile":
		entity = Tile(name)
	# Module 
	elif typ == "module":
		entity = Module(name)
		additional_info["Logic Area"] = str(round(entity.logic_area_in_mm2,4)) + " mm2"
		additional_info["Wire Area"] = str(round(entity.wire_area_in_mm2,4)) + " mm2"
		additional_info["Empty Area"] = str(round(entity.empty_area_in_mm2,4)) + " mm2"
		additional_info["Logic Power"] = str(round(entity.logic_power_in_w,4)) + " w"
		additional_info["Wire Power"] = str(round(entity.wire_power_in_w,4)) + " w"

	# 2.5D stacked chip 
	elif typ == "schip":
		entity = StackedChip(name)
	# Error for invalid argument
	else:
		msg = "Invalid type \"%s\". Only \"tile\", \"module\" and \"schip\" are valid"
		msg %= typ
		error(__file__, msg)

	# Report Metrics
	print("Name:\t\t" + entity.name)
	print("Area:\t\t" + str(round(entity.total_area_in_mm2,4)) + " mm2")
	print("Power:\t\t" + str(round(entity.total_power_in_w,4)) + " W")
	# Additional metrics
	for info in additional_info:
		print(info + ":\t" + str(additional_info[info]))

if __name__ == "__main__":
    args = sys.argv
    if len(args) < 3:
        print("Usage: python report.py <type in {tile, module, schip}> <name>")
        sys.exit()
    read_and_report(args[1], args[2])

		
		
