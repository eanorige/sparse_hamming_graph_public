# Libraries
import sys

# Custom files
from place_and_route import place_and_route
from create_tile import create_tile
from error import error, warning

# Generate customized topology from "class of topologies" approach
def generate(module_name, area, n_endpoints, tech, prot, bw, freq, rows, cols, config):
	print("Generating Custom Topology...")

	# VALIDATION: config format
	if len(config) < 2:
		msg = "Config format: [<row-hops>,<col-hops>]"
		error(__file__, msg)
	
	# Get config
	(row_hops, col_hops) = config

	# Create tiles with ports...
	tile_name = module_name
	mports = []
	sports = []
	
	# ...Ports for mesh (base network)
	mports.append({"face" : "north", "align" : -1})
	sports.append({"face" : "north", "align" : 1})
	mports.append({"face" : "east", "align" : -1})
	sports.append({"face" : "east", "align" : 1})
	mports.append({"face" : "south", "align" : 1})
	sports.append({"face" : "south", "align" : -1})
	mports.append({"face" : "west", "align" : 1})
	sports.append({"face" : "west", "align" : -1})

	# ...Ports for column networks
	col_hop_start_id = 4
	for i in range(len(col_hops)):
		mports.append({"face" : "east", "align" : -1})
		sports.append({"face" : "east", "align" : 1})
		mports.append({"face" : "east", "align" : -1})
		sports.append({"face" : "east", "align" : 1})

	# ...Ports for row networks
	row_hop_start_id = 4 + 2 * len(col_hops)
	for i in range(len(row_hops)):
		mports.append({"face" : "north", "align" : -1})
		sports.append({"face" : "north", "align" : 1})
		mports.append({"face" : "north", "align" : -1})
		sports.append({"face" : "north", "align" : 1})

	# ...create tile
	create_tile(tile_name, area, n_endpoints, mports, sports)

	# Add connections...
	connections = []
	# ...Mesh as base network
	for row in range(rows):
		for col in range(cols-1):
			connections.append(((row, col, 1),(row, col+1, 3)))	
			connections.append(((row, col+1, 3),(row, col, 1)))	
	for col in range(cols):
		for row in range(rows-1):
			connections.append(((row, col, 0),(row+1, col, 2)))	
			connections.append(((row+1, col, 2),(row, col, 0)))	

	# ...Additional col connections
	for col in range(cols):
		for i in range(len(col_hops)):
			hop = col_hops[i]
			for j in range(rows - hop):
				connections.append(((j, col, col_hop_start_id + 2 * i),(j + hop, col, col_hop_start_id + 2 * i)))	
				connections.append(((j + hop, col, col_hop_start_id + 2 * i + 1),(j, col, col_hop_start_id + 2 * i + 1)))	

	# ...Additional row connections
	for row in range(rows):
		for i in range(len(row_hops)):
			hop = row_hops[i]
			for j in range(cols - hop):
				connections.append(((row, j, row_hop_start_id + 2 * i),(row, j + hop, row_hop_start_id + 2 * i)))	
				connections.append(((row, j + hop, row_hop_start_id + 2 * i + 1),(row, j, row_hop_start_id + 2 * i + 1)))	

	# Place and route
	place_and_route(module_name, tile_name, tech, prot, bw, freq, rows, cols, connections)

### Main ###
if __name__ == "__main__":
	args = sys.argv
	if len(args) < 12:
		print("Usage: python generate_custom.py <module-name> <tile-area> <#endpoints>"+\
			  " <tech-name> <prot-name> <bw> <freq> <rows> <cols> <row-hops> <col-hops>")
		sys.exit()
	generate(args[1], int(args[2]), int(args[3]), args[4], args[5], int(args[6]), 
			int(float(args[7])), int(args[8]), int(args[9]), [eval(args[10]),eval(args[11])])
		
