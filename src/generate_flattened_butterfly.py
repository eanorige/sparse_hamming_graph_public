# Libraries
import sys

# Custom files
from place_and_route import place_and_route
from create_tile import create_tile

# Generate Flattened Butterfly Topology
def generate(module_name, area, n_endpoints, tech, prot, bw, freq, rows, cols, config):
	print("Generating Flattened Butterfly Topology...")

	# Crate tiles...
	tile_name = module_name
	# ...Ports for mesh-like links
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
	# ...Ports for column links
	col_hop_start_id = 4
	for i in range(rows - 3):
		mports.append({"face" : "east", "align" : -1})
		sports.append({"face" : "east", "align" : 1})
	# ...Ports for row links
	row_hop_start_id = 4 + (rows - 3)
	for i in range(cols - 3):
		mports.append({"face" : "north", "align" : -1})
		sports.append({"face" : "north", "align" : 1})
	# ...Create Tile
	create_tile(tile_name, area, n_endpoints, mports, sports)
	
	# Add connections
	connections = []
	# Maps to specify the next available master and slave port per tile
	m_col_hop_id = {(row,col) : col_hop_start_id for row in range(rows) for col in range(cols)}
	s_col_hop_id = {(row,col) : col_hop_start_id for row in range(rows) for col in range(cols)}
	# Column Connections 
	for col in range(cols):
		for row in range(rows):
			# Torus like connections
			connections.append(((row, col, 0),((row+1) % rows, col, 2)))
			connections.append(((row, col, 2),((row-1) % rows, col, 0)))
			# Remaining connections
			for orow in [x for x in range(rows) if x != row and x != (row -1) % rows and x != (row + 1) % rows]:
				mport = m_col_hop_id[(row,col)]
				sport = s_col_hop_id[(orow,col)]
				m_col_hop_id[(row,col)] += 1
				s_col_hop_id[(orow,col)] += 1
				connections.append(((row, col, mport),(orow, col, sport)))
	# Maps to specify the next available master and slave port per tile
	m_row_hop_id = {(row,col) : row_hop_start_id for row in range(rows) for col in range(cols)}
	s_row_hop_id = {(row,col) : row_hop_start_id for row in range(rows) for col in range(cols)}
	# Row Network
	for row in range(rows):
		for col in range(cols):
			# Torus like connections
			connections.append(((row, col, 1),(row, (col+1) % cols, 3)))
			connections.append(((row, col, 3),(row, (col-1) % cols, 1)))
			# Remaining connections
			for ocol in [x for x in range(cols) if x != col and x != (col -1) % cols and x != (col + 1) % cols]:
				mport = m_row_hop_id[(row,col)]
				sport = s_row_hop_id[(row,ocol)]
				m_row_hop_id[(row,col)] += 1
				s_row_hop_id[(row,ocol)] += 1
				connections.append(((row, col, mport),(row, ocol, sport)))

	# Place and route 
	place_and_route(module_name, tile_name, tech, prot, bw, freq, rows, cols, connections)

### Main ###
if __name__ == "__main__":
	args = sys.argv
	if len(args) < 10:
		print("Usage: python generate_flattened_butterfly.py <module-name> <tile-area> <#endpoints>"+\
			  " <tech-name> <prot-name> <bw> <freq> <rows> <cols>")
		sys.exit()
	generate(args[1], int(args[2]), int(args[3]), args[4], args[5], int(args[6]), 
			int(float(args[7])), int(args[8]), int(args[9]), [])

		
