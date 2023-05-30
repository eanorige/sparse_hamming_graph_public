# Custom Files
from create_tile import create_tile 
from embed_tile_in_grid import embed_tile_in_grid 
from place_and_route_general import place_and_route

# Configuration
tile_area = 908000
n_endpoints = 4
tech = "gf22"
prot = "tcdm"
bw = 32
freq = int(5e8)

def build_mempool():
	# Create Mempool Tile 
	# ----------------------------------------------------------------------------------------
	name_mpt = "mpt"
	mports = []
	sports = []
	# Local
	mports.append({"location" : (42,90)})
	sports.append({"location" : (43,90)})
	# North
	mports.append({"location" : (38,90)})
	sports.append({"location" : (39,90)})
	# North-East
	mports.append({"location" : (34,90)})
	sports.append({"location" : (35,90)})
	# East
	mports.append({"location" : (44,88)})
	sports.append({"location" : (44,89)})
	# create and embed tile
	create_tile(name_mpt, tile_area, n_endpoints, mports, sports, port_placement = "manual")
	name_mpt_emb = embed_tile_in_grid(name_mpt, tech, prot, bw, int(freq))

	# Create horizontal crossbar Tile (local)
	# ----------------------------------------------------------------------------------------
	name_xbarHL = "xbarHL"
	mports = []
	sports = []
	# First 8 ports: Bottom
	for i in range(8):
		mports.append({"location" : (0,1 + 8*i)})
		sports.append({"location" : (0,1 + 8*i+1)})
	# Last 8 ports: Top
	for i in range(8):
		mports.append({"location" : (1,2 + 8*i)})
		sports.append({"location" : (1,2 + 8*i+1)})

	# create and embed tile
	create_tile(name_xbarHL, 0, 0, mports, sports, aspect_ratio = 0.08, port_placement = "manual")
	name_xbarHL_emb = embed_tile_in_grid(name_xbarHL, tech, prot, bw, int(freq))

	# Create horizontal crossbar Tile (global)
	# ----------------------------------------------------------------------------------------
	name_xbarHG = "xbarHG"
	mports = []
	sports = []
	# First 16 ports: Bottom
	for i in range(16):
		mports.append({"location" : (0,0 + 4*i)})
	# Last 16 ports: top
	for i in range(16):
		sports.append({"location" : (1,0 + 4*i)})
	# create and embed tile
	create_tile(name_xbarHG, 0, 0, mports, sports, aspect_ratio = 0.08, port_placement = "manual")
	name_xbarHG_emb = embed_tile_in_grid(name_xbarHG, tech, prot, bw, int(freq))

	# Create vertical crossbar Tile (global)
	# ----------------------------------------------------------------------------------------
	name_xbarVG = "xbarVG"
	mports = []
	sports = []
	# First 16 ports: Left 
	for i in range(16):
		mports.append({"location" : (4 + 2*i,0)})
	# Last 8 ports: Right 
	for i in range(16):
		sports.append({"location" : (4 + 2*i,3)})
	# create and embed tile
	create_tile(name_xbarVG, 0, 0, mports, sports, aspect_ratio = 20, port_placement = "manual")
	name_xbarVG_emb = embed_tile_in_grid(name_xbarVG, tech, prot, bw, int(freq))

	# Create Quadrant Module
	# ----------------------------------------------------------------------------------------
	components = []
	connections = []
	# crossbar (local)
	components.append({"name" : name_xbarHL_emb, "location" : (116,186)})
	row_starts = [0,55,135,190]
	col_starts = [0,115,232,355]
	tid = 1
	# Add 4 rows and 4 columns of tiles
	for row in range(4):
		for col in range(4):
			loc = (row_starts[row], col_starts[col])
			components.append({"name" : name_mpt_emb, "location" : loc})
			connections.append(((tid,0,"mp"),(0,tid-1,"sp")))
			connections.append(((0,tid-1,"mp"),(tid,0,"sp")))
			tid += 1
	# Place and route module
	place_and_route(components, connections,235, 450, "mp_quadrant")

	# Create MemPool Module
	# ----------------------------------------------------------------------------------------
	components = []
	connections = []
	# Specify spacing of rows and columns
	mid_row = 273
	top_row = 325
	mid_col = 485
	right_col = 515
	# Add crossbar tiles (global) 
	# North: Left: Up - id = 0
	components.append({"name" : name_xbarHG_emb, "location" : (mid_row,50), "xmirror" : True})
	# North: Left: Down - id = 1
	components.append({"name" : name_xbarHG_emb, "location" : (mid_row,150)})
	# North: Right: Up - id = 2
	components.append({"name" : name_xbarHG_emb, "location" : (mid_row,750), "xmirror" : True})
	# North: Right: Down - id = 3
	components.append({"name" : name_xbarHG_emb, "location" : (mid_row,850)})
	# North-East: Left: Up - id = 4
	components.append({"name" : name_xbarHG_emb, "location" : (mid_row,250), "xmirror" : True})
	# North-East: Left: Down - id = 5
	components.append({"name" : name_xbarHG_emb, "location" : (mid_row,350)})
	# North-East: Right: Up - id = 6
	components.append({"name" : name_xbarHG_emb, "location" : (mid_row,right_col + 50), "xmirror" : True})
	# North-East: Right: Down - id = 7
	components.append({"name" : name_xbarHG_emb, "location" : (mid_row,right_col + 150)})
	# East: Bottom: Up - id = 8
	components.append({"name" : name_xbarVG_emb, "location" : (50,mid_col), "ymirror" : True})
	# East: Bottom: Down - id = 9
	components.append({"name" : name_xbarVG_emb, "location" : (150,mid_col)})
	# East: Top: Up - id = 10
	components.append({"name" : name_xbarVG_emb, "location" : (top_row + 50,mid_col), "ymirror" : True})
	# East: Top: Down - id = 11
	components.append({"name" : name_xbarVG_emb, "location" : (top_row + 150,mid_col)})
	# Add quadrant modules 
	# Bottom-Left - id = 12
	components.append({"name" : "mp_quadrant", "type" : "module", "location" : (0,0)})
	# Top-Left - id = 13
	components.append({"name" : "mp_quadrant", "type" : "module", "location" : (top_row,0), "xmirror" : True})
	# Bottom-Right - id = 14
	components.append({"name" : "mp_quadrant", "type" : "module", "location" : (0,right_col), "ymirror" : True})
	# Top-Right - id = 15
	components.append({"name" : "mp_quadrant", "type" : "module", "location" : (top_row,right_col), "xmirror" : True, "ymirror" : True})
	# Auxiliary function to add connections
	def connect(xid, qid1, qid2, tid, pid):
		connections.append(((qid1, tid, pid,"mp"),(xid,tid,"sp")))
		connections.append(((xid, tid,"mp"),(qid2,tid,pid,"sp")))
	# Add connections between tiles and global crossbars
	for tid in range(16):
		# North: Left
		connect(xid = 0, qid1 = 12, qid2 = 13, tid = tid, pid = 1)
		connect(xid = 1, qid1 = 13, qid2 = 12, tid = tid, pid = 1)
		# North: Right
		connect(xid = 2, qid1 = 14, qid2 = 15, tid = tid, pid = 1)
		connect(xid = 3, qid1 = 15, qid2 = 14, tid = tid, pid = 1)
		# North-East: Right
		connect(xid = 4, qid1 = 12, qid2 = 15, tid = tid, pid = 2)
		connect(xid = 5, qid1 = 15, qid2 = 12, tid = tid, pid = 2)
		# North-East: Left
		connect(xid = 6, qid1 = 12, qid2 = 13, tid = tid, pid = 2)
		connect(xid = 7, qid1 = 13, qid2 = 12, tid = tid, pid = 2)
		# East: Bottom
		connect(xid = 8, qid1 = 12, qid2 = 14, tid = tid, pid = 3)
		connect(xid = 9, qid1 = 14, qid2 = 12, tid = tid, pid = 3)
		# East: Top
		connect(xid = 10, qid1 = 13, qid2 = 15, tid = tid, pid = 3)
		connect(xid = 11, qid1 = 15, qid2 = 13, tid = tid, pid = 3)
	# Place and route the MemPool Module
	place_and_route(components, connections,560, 965, "mempool")
	
### Main ###
if __name__ == "__main__":
	build_mempool()
