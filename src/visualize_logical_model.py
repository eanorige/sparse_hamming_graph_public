# libraries
import networkx as nx
import matplotlib.pyplot as plt
import math
import sys

# Custom files
import config as cfg
from module import Module
from tile import Tile 
from stacked_chip import StackedChip
from error import error, warning

# Visualize logical model (graph)
def visualize(vertices, edges, edge_delays, cols):
	# Initialize graph
	G=nx.DiGraph()
	# Construct graph
	routers = []
	nodes = []
	node_parents = {}
	for vertex in vertices:
		if vertex[-1] == "r":
			routers.append(vertex)
		else:
			nodes.append(vertex)
	for (src, dst) in edges:
		if src[-1] == "r":
			node_parents[dst] = src
		if dst[-1] == "r":
			node_parents[src] = dst

	# Compute number of rows to be used in the visualization
	rows = math.ceil(len(routers) / cols)
	
	# Compute positions of router nodes (only for visualization)
	router_pos = {}
	for i in range(len(routers)):	
		router = routers[i]
		row = i // cols
		col = i % cols
		pos = (col + 0.3 * min(row,rows-row-1)**0.5,\
			   row + 0.3 * min(col,cols-col-1)**0.5)
		G.add_node(router, pos = pos)
		router_pos[router] = pos

	# Compute positions of endpoint nodes (only for visualization)
	nodes_per_router = {router : 0 for router in routers}
	total_nodes_per_router = {r: sum([1 for n in nodes if node_parents[n] == r]) for r in routers}
	for i in range(len(nodes)):	
		nodes_per_router[router] += 1
		node = nodes[i]
		router = node_parents[node]
		pos = router_pos[router]
		node_cnt = total_nodes_per_router[router]
		node_idx = nodes_per_router[router]
		r = 0.33
		t = ((3.141592654 / 4) + (2 * 3.141592654 / node_cnt * node_idx)) % (2 * 3.141502654)
		x = r*math.cos(t) + pos[0];
		y = r*math.sin(t) + pos[1];
		G.add_node(node, pos = (x,y))

	# Add edges
	for edge in edges:
		G.add_edge(edge[0], edge[1])

	# Color-coded vertices
	color_map = []
	for node in G:
		if "r" in node:
			color_map.append("#009900")
		elif "mp" in node:	
			color_map.append("#990000")
		elif "sp" in node:	
			color_map.append("#999900")
		elif "p" in node:	
			color_map.append("#996600")
		elif "ep" in node:	
			color_map.append("#000099")
		else:
			color_map.append("#999999")
	
	# Draw graph
	nx.draw(	G, 
				pos=nx.get_node_attributes(G,'pos'),
				node_color=color_map, 
				node_size=200, 
				node_shape="o", 
				alpha=0.5, 
				linewidths=2,
				arrowstyle="-|>",
				arrowsize=10,
			)
	plt.show()

# Read a tile/module and visualize it
def read_and_visualize(typ, name, cols):
	if typ == "tile":
		top = Tile(name)
	elif typ == "module":
		top = Module(name)
	elif typ == "schip":
		top = StackedChip(name)
	else:
		msg = "Invalid type \"%s\". Only \"tile\" and \"module\" are valid"
		msg %= typ
		error(__file__, msg)
	visualize(top.vertices, top.edges, top.edge_delays, cols)

if __name__ == "__main__":
	args = sys.argv
	if len(args) < 4:
		print("Usage: python visualize_logical_model.py <type in {tile, module, schip}> <name> <cols>")
		sys.exit()
	read_and_visualize(args[1], args[2], int(args[3]))

