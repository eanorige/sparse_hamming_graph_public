# Libraries
import sys

# Custom files
import config as cfg
from module import Module
from stacked_chip import StackedChip
from error import error, warning

# Translate a logical model to an anynet BookSim input
def translate_lm_to_bs(output_file_name, vertices, edges, edge_delays):

	print("Translating Logical Model to BookSim anynet file...", end = '')
	# Step 1: Construct auxiliary data structures
	adj_list = {}
	router_list = []
	endpoint_list = []
	for v in vertices:
		adj_list[v] = []
		if v[-1] == "r":
			router_list.append(v)
		if v[-1] in ["ep"]:
			endpoint_list.append(v)
	for (s,e) in edges:
		adj_list[s].append(e)
	# Step 2: Only keep routers and endpoints
	f = open(cfg.bs_topologies + output_file_name + ".anynet", "w")
	for router in router_list:
		succ_routers = []
		succ_nodes = []
		# Run Dijkstra from each router but abort as soon as next router is found
		dist = {router : 0}
		todo = [router]
		while len(todo) > 0:
			cur = todo.pop(0)
			for nei in adj_list[cur]:
				dist[nei] = dist[cur] + edge_delays[(cur,nei)]
				if nei[-1] in ["r"]:
					succ_routers.append(nei)
				elif nei[-1] in ["ep"]:
					succ_nodes.append(nei)
				else:
					todo.append(nei)
		# Step 3: Write anynet topology 
		f.write("router " + str(router_list.index(router)))
		for succ in succ_routers + succ_nodes:
			if succ[-1] == "r":
				f.write(" router " + str(router_list.index(succ)) + " " + str(max(1,int(round(dist[succ])))))	
			elif succ[-1] in ["ep"]: 
				f.write(" node " + str(endpoint_list.index(succ)))	
		f.write("\n")
	f.close()
	print("saved anynet file as \"%s%s\"" % (cfg.bs_topologies, output_file_name))

# Read a module and translate it
def read_and_translate(typ, out_file, name):
	if typ == "module":
		top = Module(name)
	elif typ == "schip":
		top = StackedChip(name)
	else:
		msg = "Invalid type \"%s\", valid types are \"module\" and \"schip\""
		msg %= typ
		error(__file__, msg)
	translate_lm_to_bs(out_file, top.vertices, top.edges, top.edge_delays)

### Main ###
if __name__ == "__main__":
	 args = sys.argv
	 if len(args) < 4:
		  print("Usage: python translate_lm_to_bs.py <type in {module, schip}> <out-file-name> <module- or schip-name>")
		  sys.exit()
	 read_and_translate(args[1], args[2], args[3])
	
		
		
