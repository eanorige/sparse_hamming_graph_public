# Libraries
import sys

# Custom files
from place_and_route import place_and_route
from create_tile import create_tile
from error import error, warning

# Generate Torus Topology
def generate(module_name, area, n_endpoints, tech, prot, bw, freq, rows, cols, config):
	print("Generating Torus Topology...")

	# VALIDATION: Config format
	if len(config) < 1:
		msg = "Config format: [<bidirectional>]"
		error(__file__, msg)

	bidir = config[0]

	# Create tile
	tile_name = module_name
	mports = []
	sports = []
	mports.append({"face" : "north", "align" : -1})
	sports.append({"face" : "north", "align" : 1})
	mports.append({"face" : "east", "align" : -1})
	sports.append({"face" : "east", "align" : 1})
	mports.append({"face" : "south", "align" : 1})
	sports.append({"face" : "south", "align" : -1})
	mports.append({"face" : "west", "align" : 1})
	sports.append({"face" : "west", "align" : -1})
	create_tile(tile_name, area, n_endpoints, mports, sports)

	# Add connections...
	connections = []
	for row in range(rows):
		for col in range(cols):
			# ...Forward
			connections.append(((row,col,0),((row+1) % rows,col,2)))
			connections.append(((row,col,1),(row,(col+1) % cols,3)))
			# ...Backward
			if bidir:
				connections.append(((row,col,2),((row-1) % rows,col,0)))
				connections.append(((row,col,3),(row,(col-1) % cols,1)))

	# Place and route
	place_and_route(module_name, tile_name, tech, prot, bw, freq, rows, cols, connections)

# Main
if __name__ == "__main__":
	args = sys.argv
	if len(args) < 11:
		print("Usage: python generate_torus.py <module-name> <tile-area> <#endpoints>"+\
			  " <tech-name> <prot-name> <bw> <freq> <rows> <cols> <bidirectional>")
		sys.exit()
	generate(args[1], int(args[2]), int(args[3]), args[4], args[5], int(args[6]), 
			int(float(args[7])), int(args[8]), int(args[9]), [args[10] == "True"])
		
