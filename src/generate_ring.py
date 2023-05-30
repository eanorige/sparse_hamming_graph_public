# Libraries
import sys

# Custom files
from place_and_route import place_and_route
from create_tile import create_tile
from error import error, warning

# Generate ring topology
def generate(module_name, area, n_endpoints, tech, prot, bw, freq, rows, cols, config):
	print("Generating Ring Topology...")

	# VALIDATION: Format of config
	if len(config) < 1:
		msg = "Config format: [<bidirectional>]" 
		error(__file__, msg)
	bidir = config[0]

	# Create Tile
	tile_name = module_name
	mports = []
	sports = []
	mports.append({"face" : "east", "align" : -1})
	sports.append({"face" : "east", "align" : 1})
	mports.append({"face" : "west", "align" : 1})
	sports.append({"face" : "west", "align" : -1})
	create_tile(tile_name, area, n_endpoints, mports, sports)

	# Add connections...
	connections = []
	for row in range(rows):
		# ...Horizontal part	
		for col in range(1,cols-1):
			if row % 2 == 0 or bidir:
				connections.append(((row,col,0),(row,col+1,1)))
			if row % 2 == 1 or bidir:
				connections.append(((row,col+1,1),(row,col,0)))
		# ...Vertical part at right-most column
		if row % 2 == 0:
			connections.append(((row,cols-1,0),(row+1,cols-1,0)))
			if bidir:
				connections.append(((row+1,cols-1,0),(row,cols-1,0)))
		# ...Vertical part at second-to-left most column
		if row % 2 == 1 and row < rows-1:
			connections.append(((row,1,1),(row+1,1,1)))
			if bidir:
				connections.append(((row+1,1,1),(row,1,1)))
		# ...Vertical part at left most column
		if row < rows-1:
			port = 1 if row % 2 == 0 else 0
			connections.append(((row+1,0,port),(row,0,port)))
			if bidir:
				connections.append(((row,0,port),(row+1,0,port)))
	# ...Attaching top-left and bottom-left corners
	connections.append(((0,0,0),(0,1,1)))
	connections.append(((rows-1,1,1),(rows-1,0,0)))
	if bidir:
		connections.append(((0,1,1),(0,0,0)))
		connections.append(((rows-1,0,0),(rows-1,1,1)))
	# ...Place and Router
	place_and_route(module_name, tile_name, tech, prot, bw, freq, rows, cols, connections)

### Main ###
if __name__ == "__main__":
	args = sys.argv
	if len(args) < 11:
		print("Usage: python generate_ring.py <module-name> <tile-area> <#endpoints>"+\
			  " <tech-name> <prot-name> <bw> <freq> <rows> <cols> <bidirectional>")
		sys.exit()
	generate(args[1], int(args[2]), int(args[3]), args[4], args[5], int(args[6]),
			int(float(args[7])), int(args[8]), int(args[9]), [args[10] == "True"])


