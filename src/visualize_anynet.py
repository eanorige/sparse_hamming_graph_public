# libraries
import networkx as nx
import matplotlib.pyplot as plt
import math
import sys

# Custom files
import config as cfg

# Visualize graph given as a BookSim anynet input file
def visualize(anynet_file, cols):

	# Initialize graph
	G=nx.DiGraph()

	# Read anynet file 
	routers = []
	nodes = []
	node_parents = {}
	edges = []
	with open(cfg.bs_topologies + anynet_file + ".anynet", "r") as file:
		lines = file.readlines()
		n = len(lines)
		for line in lines:	
			words = line.split(" ")				
			cur = words.pop(0) + words.pop(0)	
			routers.append(cur)
			while len(words) > 0:
				nxt = words.pop(0) + words.pop(0)
				if "router" in nxt:
					words.pop(0)
				if "node" in nxt:
					nodes.append(nxt)
					node_parents[nxt] = cur
				edges.append((cur,nxt))

	# compute rows to display
	rows = math.ceil(len(routers) / cols)
	
	# Compute router positions (only to visualize, not corresponding to physical locations)
	# and add routers to graph
	router_pos = {}
	for i in range(len(routers)):	
		router = routers[i]
		row = i // cols
		col = i % cols
		pos = (col + 0.3 * min(row,rows-row-1)**0.5,\
			   row + 0.3 * min(col,cols-col-1)**0.5)
		G.add_node(router, pos = pos)
		router_pos[router] = pos

	# Compute endpoint positions: Arrange them in a circle around their router 
	# and add nodes to graph 
	nodes_per_router = {router : 0 for router in routers}
	for i in range(len(nodes)):	
		nodes_per_router[router] += 1
		node = nodes[i]
		router = node_parents[node]
		pos = router_pos[router]
		node_cnt = (len(nodes)/len(routers))
		node_idx = nodes_per_router[router]
		r = 0.33
		t = ((3.141592654 / 4) + (2 * 3.141592654 / node_cnt * node_idx)) % (2 * 3.141502654)
		x = r*math.cos(t) + pos[0];
		y = r*math.sin(t) + pos[1];
		G.add_node(node, pos = (x,y))

	# Add edges to graph
	for edge in edges:
		G.add_edge(edge[0], edge[1])

	# Color-coded vertices
	color_map = []
	for node in G:
		if "router" in node:
			color_map.append("#009900")
		else:	
			color_map.append("#000099")
	
	# Draw graph
	nx.draw(	G, 
				pos=nx.get_node_attributes(G,'pos'),
				node_color=color_map, 
				with_labels=True, 
				node_size=500, 
				node_shape="o", 
				alpha=0.5, 
				linewidths=2,
				arrowstyle="-|>",
    			arrowsize=10,
			)
	plt.show()

### Main ###
if __name__ == "__main__":
	args = sys.argv
	if len(args) < 3:
		print("Usage: python %s <filename> <cols>" % args[0])
		sys.exit()
	visualize(args[1], int(args[2]))
