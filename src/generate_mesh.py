# Libraries
import sys

# Custom files
from create_tile import create_tile
from place_and_route import place_and_route

# Generate Mesh topology
def generate(module_name, area, n_endpoints, tech, prot, bw, freq, rows, cols, config):
	print("Generating Mesh Topology...")

	# Create Tile...
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
			# Column connections
			if row < rows-1:
				connections.append(((row,col,0),(row+1,col,2)))
				connections.append(((row+1,col,2),(row,col,0)))
			# Row connections
			if col < cols-1:
				connections.append(((row,col,1),(row,col+1,3)))
				connections.append(((row,col+1,3),(row,col,1)))

	place_and_route(module_name, tile_name, tech, prot, bw, freq, rows, cols, connections)

### Main ###
if __name__ == "__main__":
	args = sys.argv
	if len(args) < 10:
		print("Usage: python generate_mesh.py <module-name> <tile-area> <#endpoints>"+\
			  " <tech-name> <prot-name> <bw> <freq> <rows> <cols>")
		sys.exit()
	generate(args[1], int(args[2]), int(args[3]), args[4], args[5], int(args[6]), 
			int(float(args[7])), int(args[8]), int(args[9]), [])

