# Libraries
import sys

# Custom files
from place_and_route import place_and_route
from create_tile import create_tile
from error import error, warning

# Generate a folded torus topology
def generate(module_name, area, n_endpoints, tech, prot, bw, freq, rows, cols, config):
	print("Generating Folded Torus Topology...")

	# VALIDATION: Format of config
	if len(config) < 1:
		msg = "Config format: [<bidirectional>]"
		error(__file__, msg)
	bidir = config[0]

	# Create Tile...
	tile_name = module_name
	mports = []
	sports = []
	# ...Ports for unidirectional network
	mports.append({"face" : "north", "align" : -1})
	sports.append({"face" : "north", "align" : 1})
	mports.append({"face" : "east", "align" : -1})
	sports.append({"face" : "east", "align" : 1})
	# ...Ports for bidirectional network
	if bidir:
		mports.append({"face" : "north", "align" : 1})
		sports.append({"face" : "north", "align" : -1})
		mports.append({"face" : "east", "align" : 1})
		sports.append({"face" : "east", "align" : -1})
	# ...Create Tile
	create_tile(tile_name, area, n_endpoints, mports, sports)

	# Add connections...
	connections = []
	# ...Row connections...
	for row in range(rows):
		for col in range(cols):
			# ...Left to right
			if col % 2 == 0 and col < cols - 2:
				connections.append(((row,col,0),(row,col+2,0)))
				if bidir:	
					connections.append(((row,col+2,2),(row,col,2)))
			# ...Right to left
			if col % 2 == 1 and col > 1:
				connections.append(((row,col,0),(row,col-2,0)))
				if bidir:	
					connections.append(((row,col-2,2),(row,col,2)))
		# ...Special connections on edge of chip
		connections.append(((row,1,0),(row,0,0)))
		connections.append(((row,cols-2,0),(row,cols-1,0)))
		if bidir:
			connections.append(((row,0,2),(row,1,2)))
			connections.append(((row,cols-1,2),(row,cols-2,2)))
	# ...Column connections...
	for col in range(cols):
		for row in range(rows):
			# ...Bottom to top 
			if row % 2 == 0 and row < rows - 2:
				connections.append(((row,col,1),(row+2,col,1)))
				if bidir:	
					connections.append(((row+2,col,3),(row,col,3)))
			# ...Top to bottom 
			if row % 2 == 1 and row > 1:
				connections.append(((row,col,1),(row-2,col,1)))
				if bidir:	
					connections.append(((row-2,col,3),(row,col,3)))
		# ...Special connections on edge of chip
		connections.append(((1,col,1),(0,col,1)))
		connections.append(((rows-2,col,1),(rows-1,col,1)))
		if bidir:
			connections.append(((0,col,3),(1,col,3)))
			connections.append(((rows-1,col,3),(rows-2,col,3)))

	# Place and Route
	place_and_route(module_name, tile_name, tech, prot, bw, freq, rows, cols, connections)

### Main ###
if __name__ == "__main__":
	args = sys.argv
	if len(args) < 11:
		print("Usage: python generate_folded_torus.py <module-name> <tile-area> <#endpoints>"+\
			  " <tech-name> <prot-name> <bw> <freq> <rows> <cols> <bidirectional>")
		sys.exit()
	generate(args[1], int(args[2]), int(args[3]), args[4], args[5], int(args[6]), 
			int(float(args[7])), int(args[8]), int(args[9]), [args[10] == "True"])
		
