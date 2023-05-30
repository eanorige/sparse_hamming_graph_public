# Libraries
from sympy.combinatorics import GrayCode
import sys
import math
import copy

# Custom files
from place_and_route import place_and_route
from create_tile import create_tile
from error import error, warning

# Map for gray-code like ordering of rows and columns
row_map = None
col_map = None

# Auxiliary function to transform bit-lists (tile-ids) to row and column of said tile
def bin_to_rc(binary, rows, cols):
	global row_map
	global col_map
	bin_row = binary[:int(math.log2(rows))]
	bin_col = binary[int(math.log2(rows)):]
	row = row_map[int(bin_row, 2)]
	col = col_map[int(bin_col, 2)]
	return (row, col)
	
# Generate a Hypercube topology
def generate(module_name, area, n_endpoints, tech, prot, bw, freq, rows, cols, config):
	global row_map
	global col_map
	print("Generating Hypercube Topology...")

	# VALIDATION: Hypercube specific input validation
	if math.log2(rows) % 1 != 0 or math.log2(cols) % 1 != 0:
		msg = "rows and columns must both be powers of 2"
		error(__file__, msg)

	# Compute size of bit-vectors that represent tile IDs.
	row_dimensions = int(math.log2(rows))
	col_dimensions = int(math.log2(cols))
	dimensions = row_dimensions + col_dimensions 
	
	# Compute gray code for rows and columns
	row_gc = list(GrayCode(row_dimensions).generate_gray())
	col_gc = list(GrayCode(col_dimensions).generate_gray())

	# Maps to arrange rows and columns in gray code style
	# This ensures that mesh-like links are always part of the Hypercube topology
	row_map = {int(row_gc[i],2) : i for i in range(rows)}
	col_map = {int(col_gc[i],2) : i for i in range(cols)}

	# Create Tile...
	tile_name = module_name
	# ...Add ports for mesh-like connections
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
	# ...Add ports for remaining column-links
	col_hop_start_id = 4
	nports = max(row_dimensions-2,0)
	for i in range(nports):
		mports.append({"face" : "north", "align" : -1})
		sports.append({"face" : "north", "align" : 1})
	# ...Add ports for remaining row-links
	row_hop_start_id = 4 + nports
	nports = max(col_dimensions-2,0)
	for i in range(nports):
		mports.append({"face" : "east", "align" : -1})
		sports.append({"face" : "east", "align" : 1})
	# ...Create tile
	create_tile(tile_name, area, n_endpoints, mports, sports)
	
	# Compose a list of edges that are part of the hypercube topology
	edges = []
	for i in range(2**dimensions):
		start = list(bin(i)[2:]) 
		start = ["0" for j in range(dimensions - len(start))] + start
		for j in range(dimensions):	
			end = copy.deepcopy(start)
			end[j] = "1" if end[j] == "0" else "0"
			edges.append((start, end))

	# Maps a tile to its lowest available port-id for column and row links
	m_col_hop_id = {(row,col) : col_hop_start_id for row in range(rows) for col in range(cols)}
	s_col_hop_id = {(row,col) : col_hop_start_id for row in range(rows) for col in range(cols)}
	m_row_hop_id = {(row,col) : row_hop_start_id for row in range(rows) for col in range(cols)}
	s_row_hop_id = {(row,col) : row_hop_start_id for row in range(rows) for col in range(cols)}

	# Add connections...
	connections = []
	for edge in edges:
		# ...Extract start and end tile ids
		(start, end) = edge
		start = "".join(start)
		end = "".join(end)
		# ...Translate tile ids to tile locations
		(srow,scol) = bin_to_rc(start, rows, cols)
		(erow,ecol) = bin_to_rc(end, rows, cols)
		# ...Set ports for mesh-like connections
		if scol == ecol and (srow + 1) % rows == erow:
			sport = 0
			eport = 2
		elif scol == ecol and (srow - 1) % rows == erow:
			sport = 2
			eport = 0
		elif srow == erow and (scol + 1) % cols == ecol:
			sport = 1
			eport = 3
		elif srow == erow and (scol - 1) % cols == ecol:
			sport = 3
			eport = 1
		# ...Set ports for remaining column-connections
		elif scol == ecol:
			sport = m_col_hop_id[(srow,scol)]
			m_col_hop_id[(srow,scol)] += 1
			eport = s_col_hop_id[(erow,ecol)]
			s_col_hop_id[(erow,ecol)] += 1
		# ...Set ports for remaining row-connections
		elif srow == erow:
			sport = m_row_hop_id[(srow,scol)]
			m_row_hop_id[(srow,scol)] += 1
			eport = s_row_hop_id[(erow,ecol)]
			s_row_hop_id[(erow,ecol)] += 1
		else:
			msg = "Invalid connection direction"
			error(__file__, msg)
		connections.append(((srow,scol,sport),(erow,ecol,eport)))

	# Place and Router
	place_and_route(module_name, tile_name, tech, prot, bw, freq, rows, cols, connections)

### Main ###
if __name__ == "__main__":
	args = sys.argv
	if len(args) < 10:
		print("Usage: python generate_hypercube.py <module-name> <tile-area> <#endpoints>"+\
			  " <tech-name> <prot-name> <bw> <freq> <rows> <cols>")
		sys.exit()

	generate(args[1], int(args[2]), int(args[3]), args[4], args[5], int(args[6]), 
			int(float(args[7])), int(args[8]), int(args[9]), [])

