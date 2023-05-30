# Libraries
import sys

# Custom files
from place_and_route import place_and_route
from create_tile import create_tile
from error import error, warning

# GF(4)
add_4 = [   [0,1,2,3],
			[1,0,3,2],
			[2,3,0,1],
			[3,2,1,0]]

mul_4 = [   [0,0,0,0],
			[0,1,2,3],
			[0,2,3,1],
			[0,3,1,2]]

# GF(8)
add_8 = [   [0, 1, 2, 3, 4, 5, 6, 7],
			[1, 0, 3, 2, 5, 4, 7, 6],
			[2, 3, 0, 1, 6, 7, 4, 5],
			[3, 2, 1, 0, 7, 6, 5, 4],
			[4, 5, 6, 7, 0, 1, 2, 3],
			[5, 4, 7, 6, 1, 0, 3, 2],
			[6, 7, 4, 5, 2, 3, 0, 1],
			[7, 6, 5, 4, 3, 2, 1, 0]]

mul_8 = [   [0, 0, 0, 0, 0, 0, 0, 0],
			[0, 1, 2, 3, 4, 5, 6, 7],
			[0, 2, 4, 6, 3, 1, 7, 5],
			[0, 3, 6, 5, 7, 4, 1, 2],
			[0, 4, 3, 7, 6, 2, 5, 1],
			[0, 5, 1, 4, 2, 7, 3, 6],
			[0, 6, 7, 1, 5, 3, 2, 4],
			[0, 7, 5, 2, 1, 6, 4, 3]]

# For GF(4) and GF(8), see SlimNoC paper 
X4 = [1,3]
X8 = [1,4,7]
Xp4 = [2,1]
Xp8 = [2,5,3]

# Store GF(4) and GF(8) info
add = {4:add_4,8:add_8}
mul = {4:mul_4,8:mul_8}
X = {4:X4,8:X8}
Xp = {4:Xp4,8:Xp8}

# Prime Powers 
prime_powers = [3,5,7,11,13,17,19,23,29]

# Auxiliary function: Get node_b given subgroup_a, subgroup_b and node_a
def get_node_b(q, subgroup_a, subgroup_b, node_a):
	# Prime powers: See SlimFly paper
	if q in prime_powers:
		return (subgroup_a * subgroup_b + node_a) % q
	# Other Galois Fields: See SlimNoC paper
	elif q in add and q in mul:
		return add[q][mul[q][subgroup_a][subgroup_b]][node_a]
	# Other numbers are not supported
	else:
		msg = "q = %d is not supported"
		msg %= q
		error(__file__, msg)

# Auxiliary function: Computes connections for given groups, subgroups and nodes.
def get_connection(group_a, subgroup_a, node_a, group_b, subgroup_b, node_b, mpmap, spmap):
	row_a = node_a
	row_b = node_b
	col_a = 2 * subgroup_a + group_a
	col_b = 2 * subgroup_b + group_b
	port_a = mpmap[(row_a,col_a)]
	mpmap[(row_a,col_a)] += 1
	port_b = spmap[(row_b,col_b)]
	spmap[(row_b,col_b)] += 1
	return((row_a,col_a,port_a),(row_b,col_b,port_b))

# Generate SlimNoC topology
def generate(module_name, area, n_endpoints, tech, prot, bw, freq, rows, cols, config):
	print("Generating SlimNoC Topology...")

	# SlimNoC uses rows and cols from the configuration.
	# It ignore the explicit row and col parameters
	if len(config) < 3:
		msg = "Config format: [<q>,<rows>,<cols>]"
		error(__file__, msg)
	(q,rows,cols) = config

	# VALIDATION: check that the passed config parameter q is valid and supported
	if q not in prime_powers and (q not in add or q not in mul):
		msg = "Currently, q = %d is not supported"
		msg %= q
		error(__file__, msg)

	# Create Tile...
	tile_name = module_name
	mports = []
	sports = []
	# ...Ports for intra-subgroup links
	n_ports = len(X[q])
	col_hop_start_id = 0
	for i in range(n_ports):
		mports.append({"face" : "east", "align" : 1})
		sports.append({"face" : "east", "align" : 1})
	# ...Ports for inter-group links
	row_hop_start_id = n_ports
	n_ports = q
	for i in range(q):
		mports.append({"face" : "north", "align" : 1})
		sports.append({"face" : "north", "align" : 1})
	# ...Create tile	
	create_tile(tile_name, area, n_endpoints, mports, sports)

	# Maps tile locations to next available master and slave port id for row (inter-group) and column (intra-subgroup) links
	m_col_hop_id = {(row,col) : col_hop_start_id for row in range(rows) for col in range(cols)}
	s_col_hop_id = {(row,col) : col_hop_start_id for row in range(rows) for col in range(cols)}
	m_row_hop_id = {(row,col) : row_hop_start_id for row in range(rows) for col in range(cols)}
	s_row_hop_id = {(row,col) : row_hop_start_id for row in range(rows) for col in range(cols)}
	
	# Add connections...
	connections = []
	# ...Build intra-subgroup connections
	for group in [0,1]:
		for subgroup in range(q):
			for node_a in range(q):
				Xset = X[q] if group == 0 else Xp[q]
				for x in Xset:
					node_b = add[q][node_a][x]
					connections.append(get_connection(group, subgroup, node_a, group, subgroup, node_b, m_col_hop_id, s_col_hop_id))
	# ...Build inter-group connections
	for subgroup_a in range(q):
		for node_a in range(q):
			for subgroup_b in range(q):
				node_b = get_node_b(q,subgroup_a,subgroup_b,node_a)
				connections.append(get_connection(0, subgroup_a, node_a, 1, subgroup_b, node_b, m_row_hop_id, s_row_hop_id))
				connections.append(get_connection(1, subgroup_b, node_b, 0, subgroup_a, node_a, m_row_hop_id, s_row_hop_id))

	# Place and Router
	place_and_route(module_name, tile_name, tech, prot, bw, freq, rows, cols, connections)

### Main ###
if __name__ == "__main__":
	args = sys.argv
	if len(args) < 11:
		print("Usage: python generate_torus.py <module-name> <tile-area> <#endpoints>"+\
			  " <tech-name> <prot-name> <bw> <freq> <rows> <cols> <q>")
		sys.exit()

	generate(args[1], int(args[2]), int(args[3]), args[4], args[5], int(args[6]),
			int(float(args[7])), int(args[8]), int(args[9]), [int(args[10]), int(args[8]), int(args[9])])







