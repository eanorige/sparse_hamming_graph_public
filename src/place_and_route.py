# Libraries
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Custom files 
from embed_tile_in_grid import embed_tile_in_grid
from tile import Tile
from error import error, warning
import config as cfg

# Settings
debug = False

# Print the intermediate grid (global routing)
# This function is only used for debugging
def print_intermediate_grid(grid):
	n_rows = len(grid)
	n_cols = len(grid[0])
	for row in range(n_rows-1,-1,-1):
		print(str(row) + (" " if row < 10 else "") + ": ", end = '')
		for col in range(n_cols):
			if grid[row][col] == "T":
				print(" T ",end = '')
			elif grid[row][col] == "M":
				print(" M ",end = '')
			elif grid[row][col] == "S":
				print(" S ",end = '')
			elif type(grid[row][col]) == list:
				print(" %d%d" % (tuple(grid[row][col])),end = '')
		print()
	print("    ", end = '')
	for col in range(n_cols):
		print(" " + str(col) + (" " if col < 10 else ""), end = '')
	print()

# Print the fine grid (detailed routing)
# This function is only used for debugging
def print_fine_grid(grid):
	n_rows = len(grid)
	n_cols = len(grid[0])
	for row in range(n_rows-1,-1,-1):
		print(str(row) + (" " if row < 10 else "") + ": ", end = '')
		for col in range(n_cols):
			if grid[row][col] == "T":
				print(" T ",end = '')
			elif grid[row][col] == "M":
				print(" M ",end = '')
			elif grid[row][col] == "S":
				print(" S ",end = '')
			elif grid[row][col] == [0,1]:
				print(" | ",end = '')
			elif grid[row][col] == [1,0]:
				print(" - ",end = '')
			elif grid[row][col] == [1,1]:
				print(" + ",end = '')
			elif grid[row][col] == [0,0]:
				print("   ",end = '')
			else:
				print(" X ",end = '')
		print()
	print("    ", end = '')
	for col in range(n_cols):
		print(" " + str(col) + (" " if col < 10 else ""), end = '')
	print()

# Get the tile-face on which a port sits 
def get_port_face(tile, typ, pid):
	ports = (tile.master_ports if typ == "master" else tile.slave_ports)
	if ports[pid]["location"][0] == 0:
		return "south"
	elif ports[pid]["location"][0] == tile.n_rows-1:
		return "north"
	elif ports[pid]["location"][1] == 0:
		return "west"
	elif ports[pid]["location"][1] == tile.n_cols-1:
		return "east"
	else:
		msg = "Unable to determine port face"
		error(__file__, msg)

# VALIDATION: make sure that no port is used twice
def validate_connections(cons_raw):
	masters = [x[0] for x in cons_raw]
	slaves = [x[1] for x in cons_raw]
	# master ports
	if len(masters) != len(set(masters)):
		msg = "Invalid connections are passed as argument: %d Master-Ports are used twice"
		msg %= (len(masters) - len(set(masters)))
		error(__file__, msg)
	# slave ports
	if len(slaves) != len(set(slaves)):
		msg = "Invalid connections are passed as argument: %d Slave-Ports are used twice"
		msg %= (len(slaves) - len(set(slaves)))
		error(__file__, msg)

# Perform global routing in coarse grid
def route_in_coarse_grid(cons_raw,  tile):
	# Route connections in coarse grid
	cons_in_coarse_grid = []
	for ((srr, scr, spid), (err, ecr, epid)) in cons_raw:
		# Translate tile-coordinates to coarse grid coordinates
		(src,scc,erc,ecc) = (2*srr+1,2*scr+1,2*err+1,2*ecr+1)
		# Get fine-grid coordinates
		(srf,scf,erf,ecf) = tile.master_ports[spid]["location"] + tile.slave_ports[epid]["location"]
		# Get direction in which master and slave ports are facing
		sface = get_port_face(tile, "master", spid)
		eface = get_port_face(tile, "slave", epid)
		# Start-Segment
		if sface == "north":
			start_segment = [(src,scc,srf,scf),(src+1,scc)]
		elif sface == "south":
			start_segment = [(src,scc,srf,scf),(src-1,scc)]
		elif sface == "east":
			start_segment = [(src,scc,srf,scf),(src,scc+1)]
		elif sface == "west":
			start_segment = [(src,scc,srf,scf),(src,scc-1)]
		# End-Segment
		if eface == "north":
			end_segment = [(erc+1,ecc),(erc,ecc,erf,ecf)]
		elif eface == "south":
			end_segment = [(erc-1,ecc),(erc,ecc,erf,ecf)]
		elif eface == "east":
			end_segment = [(erc,ecc+1),(erc,ecc,erf,ecf)]
		elif eface == "west":
			end_segment = [(erc,ecc-1),(erc,ecc,erf,ecf)]
		# Determine how the middle part of the connection looks like

		# Row-Row
		if sface in ["north","south"] and eface in ["north","south"]:
			# Same Row: 1 intermediate segment -> 0 intermediate corners 
			if start_segment[1][0] == end_segment[0][0]:
				middle_segments = []
			# Different Rows: 3 intermediate segments -> 2 intermediate corners
			else:
				d = 1 if ecc >= scc else -1
				middle_segments = [	(start_segment[1][0],start_segment[1][1]+d),
									(end_segment[0][0],start_segment[1][1]+d),
								  ]
		# Col-Col 
		elif sface in ["east","west"] and eface in ["east","west"]:
			# Same Col: 1 intermediate segment -> 0 intermediate corners 
			if start_segment[1][1] == end_segment[0][1]:
				middle_segments = []
			# Different Cols: 3 intermediate segments -> 2 intermediate corners
			else:
				d = 1 if erc >= src else -1
				middle_segments = [	(start_segment[1][0]+d,start_segment[1][1]),
									(start_segment[1][0]+d,end_segment[0][1]),
								  ]
		# Row-Col: 2 intermediate segments -> 1 intermediate corner
		elif sface in ["north","south"] and eface in ["east","west"]:
			middle_segments = [(start_segment[1][0],end_segment[0][1])]
		# Col-Row: 2 intermediate segments -> 1 intermediate corner
		elif sface in ["east","west"] and eface in ["north","south"]:
			middle_segments = [(end_segment[0][0],start_segment[1][1])]
		# Compose full connection
		con = start_segment + middle_segments + end_segment
		# Fix straight connections
		if len(con) == 4 and con[1] == con[2]:	
			con = [con[0],con[-1]]
		# Store connection
		cons_in_coarse_grid.append(con)
	return cons_in_coarse_grid

# Compute the final size of the fine grid
def compute_final_grid_size(cons_coarse, tile, rows_of_tiles, cols_of_tiles):
	# Determine size of intermediate grid
	n_rows = rows_of_tiles * (tile.n_rows + 1) + 1
	n_cols = cols_of_tiles * (tile.n_cols + 1) + 1

	# Map row and column (only of even index!!!) from coarse to intermediate grid
	row_map = {row : (row // 2) * (tile.n_rows + 1) + (1 if row % 2 == 1 else 0) for row in range(2 * rows_of_tiles + 2)}
	col_map = {col : (col // 2) * (tile.n_cols + 1) + (1 if col % 2 == 1 else 0) for col in range(2 * cols_of_tiles + 2)}

	# Create intermediate grid
	grid = [[[0,0] for col in range(n_cols)] for row in range(n_rows)]
	for rot in range(1,2*rows_of_tiles+1,2):
		for cot in range(1,2*cols_of_tiles+1,2):
			for r in range(tile.n_rows):
				for c in range(tile.n_cols):
					grid[row_map[rot]+r][col_map[cot]+c] = "T"

	# Count the number of horizontal / vertical wires per cell in intermediate grid
	for con in cons_coarse:		
		master_loc = (row_map[con[0][0]] + con[0][2], col_map[con[0][1]] + con[0][3])
		slave_loc = (row_map[con[-1][0]] + con[-1][2], col_map[con[-1][1]] + con[-1][3])
		last_point = None
		for i in range(len(con)-1):
			# Collect info about current segment
			seg = (con[i], con[i+1])
			if seg[0][0] == seg[1][0]:
				seg_typ = "H"
				seg_dir  = 1 if seg[0][1] < seg[1][1] else -1
			elif seg[0][1] == seg[1][1]: 	
				seg_typ = "V"
				seg_dir  = 1 if seg[0][0] < seg[1][0] else -1
			else:
				msg = "Connection (coarse) changes row and column in same hop"
				error(__file__, msg)
			# Count space requirement for current segment
			# HORIZONTAL 
			if seg_typ == "H":
				# First segment
				if i == 0:
					row = master_loc[0]
					start_col = master_loc[1] + seg_dir
				# Not First segment
				else:
					row = last_point[0]
					start_col = last_point[1]
				end_col = col_map[seg[1][1]]
				# Second to last segment
				if i == len(con) - 3:
					end_col = slave_loc[1]
				# Last segment
				if i == len(con) - 2:
					row = slave_loc[0]
					end_col = slave_loc[1] - seg_dir
				# Count space needed for this segment
				for col in range(start_col, end_col + seg_dir, seg_dir):
					grid[row][col][0] += 1
				# Store where our connection ended
				last_point = (row, end_col)
			# VERTICAL
			elif seg_typ == "V":
				# First segment
				if i == 0:
					col = master_loc[1]
					start_row = master_loc[0] + seg_dir
				# Not First segment
				else:
					col = last_point[1]
					start_row = last_point[0]
				end_row = row_map[seg[1][0]]
				# Second to last segment
				if i == len(con) - 3:
					end_row = slave_loc[0]
				# Last segment
				if i == len(con) - 2:
					col = slave_loc[1]
					end_row = slave_loc[0] - seg_dir
				# Count space needed for this segment
				for row in range(start_row, end_row + seg_dir, seg_dir):
					grid[row][col][1] += 1
				# Store where our connection ended
				last_point = (end_row, col)
			else:
				msg = "Connection (coarse) changes row and column in same hop"
				error(__file__, msg)

	print_intermediate_grid(grid) if debug else 0

	# Compute required row- and columns size	
	row_sizes = {row : (tile.n_rows if row % 2 == 1 else max([grid[row_map[row]][col][0] for col in range(0, n_cols)])) for row in range(2*rows_of_tiles+1)}
	col_sizes = {col : (tile.n_cols if col % 2 == 1 else max([grid[row][col_map[col]][1] for row in range(0, n_rows)])) for col in range(2*cols_of_tiles+1)}		

	return (row_sizes, col_sizes)

# Perform detailed routing in fine grid
def route_in_fine_grid(cons_coarse, tile, row_sizes, col_sizes):
	# Gather info on rows and columns
	n_rows = sum(row_sizes.values())
	n_cols = sum(col_sizes.values())
	row_starts = {}
	col_starts = {}

	# Compute row starts
	row = 0
	for row_idx in row_sizes:
		row_starts[row_idx] = row
		row += row_sizes[row_idx]

	# Compute col starts
	col = 0
	for col_idx in col_sizes:
		col_starts[col_idx] = col
		col += col_sizes[col_idx]

	# Construct grid 
	grid = [[[0,0] for col in range(n_cols)] for row in range(n_rows)]
	for row in row_starts:
		for col in col_starts:
			# Rows / cols with tiles
			if row % 2 == 1 and col % 2 == 1:
				for r in range(row_starts[row], row_starts[row+1], 1):
					for c in range(col_starts[col], col_starts[col+1], 1):
						grid[r][c] = "T"
				for master in tile.master_ports:	
					mport = master["location"]
					grid[row_starts[row] + mport[0]][col_starts[col] + mport[1]] = "M"
				for slave in tile.slave_ports:	
					sport = slave["location"]
					grid[row_starts[row] + sport[0]][col_starts[col] + sport[1]] = "S"

	# Route connections with minimal conflicts / length
	cons_fine = []
	for con in cons_coarse:
		print("Con-coarse: " + str(con)) if debug else 0
		# Extract master and slave port location
		master = (row_starts[con[0][0]] + con[0][2], col_starts[con[0][1]] + con[0][3])
		slave = (row_starts[con[-1][0]] + con[-1][2], col_starts[con[-1][1]] + con[-1][3])
		print("Master: %s" % str(master)) if debug else 0
		print("Slave: %s" % str(slave)) if debug else 0
		corners_meta = []
		# Insert master port
		# Corner, collisions, length, all previous corners
		corners_meta.append([(master,0,0,[])])
		# Process segments
		for i in range(len(con)-2):
			# Gather segment info
			seg = (con[i], con[i+1], con[i+2])
			seg_typ = "H" if seg[0][0] == seg[1][0] else "V"
			if seg_typ == "H":
				seg_dir = 1 if seg[0][1] < seg[1][1] else -1
				next_seg_dir = 1 if seg[1][0] < seg[2][0] else -1
				corner_start = (col_starts[seg[1][1]]) if seg_dir == 1 else (col_starts[seg[1][1]] + col_sizes[seg[1][1]] - 1)
				corner_end = (col_starts[seg[1][1]] + col_sizes[seg[1][1]]) if seg_dir == 1 else (col_starts[seg[1][1]] - 1)
			elif seg_typ == "V":
				seg_dir = 1 if seg[0][0] < seg[1][0] else -1
				next_seg_dir = 1 if seg[1][1] < seg[2][1] else -1
				corner_start = (row_starts[seg[1][0]]) if seg_dir == 1 else (row_starts[seg[1][0]] + row_sizes[seg[1][0]] - 1)
				corner_end = (row_starts[seg[1][0]] + row_sizes[seg[1][0]]) if seg_dir == 1 else (row_starts[seg[1][0]] - 1)
			print("Segment: %s, type: %s, direction: %s" % (seg[:2], seg_typ, seg_dir)) if debug else 0
			# Prepare data structure to store intermediate results
			corners_interm = {}
			# Iterate through previous corners
			for (prev_corner, c, l, p) in corners_meta[-1]:
				print("Checking from start point %s" % str(prev_corner)) if debug else 0
				# Examine path from previous corner to first valid corner location
				idx = 0 if seg_typ == "H" else 1
				fix = prev_corner[idx]
				length_tmp = 0
				collisions_tmp = 0
				# Path from previous corner to next corner
				for loc in range(prev_corner[1-idx] + seg_dir, corner_start, seg_dir):
					print("Checking Access: %s" % str((fix,loc) if seg_typ == "H" else (loc,fix))) if debug else 0
					length_tmp += 1
					collisions_tmp += (grid[fix][loc][idx] if seg_typ == "H" else grid[loc][fix][idx])
				# Examine possible fine corners in next coarse corner
				for loc in range(corner_start, corner_end, seg_dir):
					print("Checking Corner: %s" % str((fix,loc) if seg_typ == "H" else (loc,fix))) if debug else 0
					length_tmp += 1
					collisions_tmp += (grid[fix][loc][idx] if seg_typ == "H" else grid[loc][fix][idx])
					if seg_typ == "H":
						print("Adding intermediate corner %s" % str((fix,loc))) if debug else 0
						corners_interm[(fix,loc)] = (c + collisions_tmp, l + length_tmp, p + [prev_corner])
					else:
						print("Adding intermediate corner %s" % str((loc,fix))) if debug else 0
						corners_interm[(loc,fix)] = (c + collisions_tmp, l + length_tmp, p + [prev_corner])
			# Finalize: Route connections to (correct) border of next corner + quadratically reduce number of possible corners
			corners_final = {}	
			for corner in corners_interm:
				# Gather info
				(c,l,p) = corners_interm[corner]
				if seg_typ == "H":
					fix = corner[1]
					start = corner[0]
					end = row_starts[seg[1][0]] + row_sizes[seg[1][0]] if next_seg_dir == 1 else row_starts[seg[1][0]] - 1
				else:
					fix = corner[0]
					start = corner[1]
					end = col_starts[seg[1][1]] + col_sizes[seg[1][1]] if next_seg_dir == 1 else col_starts[seg[1][1]] - 1
				# Compute collisions and length until border of coarse-corner cell
				collisions_tmp = c
				length_tmp = l
				for loc in range(start, end, next_seg_dir):
					length_tmp += 1
					collisions_tmp += grid[loc][fix][1] if seg_typ == "H" else grid[fix][loc][0]
				new_corner = (loc,fix) if seg_typ == "H" else (fix,loc)
				# Store corner (if new or improvement)
				if new_corner not in corners_final:
					corners_final[new_corner] = (corner, collisions_tmp, length_tmp, p)
				else:
					(corner_, c_, l_, p_) = corners_final[new_corner]
					if collisions_tmp < c_ or (collisions_tmp == c_ and length_tmp < l_):
						corners_final[new_corner] = (corner, collisions_tmp, length_tmp, p)
			corners_meta.append(corners_final.values())
		# Only keep connections that can route to slave port
		connections_valid = []	
		last_seg_typ = "H" if con[-2][0] == con[-1][0] else "V"
		last_seg_dir = 1 if ((last_seg_typ == "H" and con[-2][1] < con[-1][1]) or (last_seg_typ == "V" and con[-2][0] < con[-1][0])) else -1
		idx = 0 if last_seg_typ == "H" else 1
		for (corner, c, l, prev) in corners_meta[-1]:
			if (last_seg_typ == "H" and corner[0] == slave[0]) or (last_seg_typ == "V" and corner[1] == slave[1]):
				fix = corner[idx]
				collisions_tmp = c
				length_tmp = l
				for loc in range (corner[idx], slave[idx], last_seg_dir):
					length_tmp += 1
					collisions_tmp += grid[fix][loc][idx] if last_seg_typ == "H" else grid[loc][fix][idx]
				connections_valid.append((prev + [corner] + [slave], collisions_tmp, length_tmp))
		# Out of remaining connections choose best one
		chosen_con = None
		chosen_collisions = float('inf')
		chosen_length = float('inf')
		for (con, c, l) in connections_valid:
			if c < chosen_collisions or (c == chosen_collisions and l < chosen_length):
				chosen_con = con
				chosen_collisions = c
				chosen_length = l
		# If now fitting connection was found (e.g. happens if it is a straight connection in coarse grid but bot in fine grid)
		if chosen_con == None:	
			chosen_con = [master]
			chosen_collisions = 0
			chosen_length = 0

			hdir = 1 if master[1] < slave[1] else -1
			vdir = 1 if master[0] < slave[0] else -1
			if con[0][0] == con[-1][0]:	
				mid_col = (master[1] + slave[1]) // 2
				# Segment 1
				row = master[0]	
				for col in range(master[1]+hdir, mid_col+hdir, hdir):
					chosen_length += 1
					chosen_collisions += grid[row][col][0]
				chosen_con += [(row,col)]
				# Segment 2
				col = mid_col
				for row in range(master[0], slave[0]+vdir, vdir):
					chosen_length += 1
					chosen_collisions += grid[row][col][1]
				chosen_con += [(row,col)]
				# Segment 3
				row = slave[0]	
				for col in range(mid_col, slave[1], vdir):
					chosen_length += 1
					chosen_collisions += grid[row][col][0]
				chosen_con += [slave]
			elif con[0][1] == con[-1][1]:	
				mid_row = (master[0] + slave[0]) // 2
				# Segment 1
				col = master[1]	
				for row in range(master[0]+vdir, mid_row+vdir, vdir):
					chosen_length += 1
					chosen_collisions += grid[row][col][1]
				chosen_con += [(row,col)]
				# Segment 2
				row = mid_row
				for col in range(master[1], slave[1]+hdir, hdir):
					chosen_length += 1
					chosen_collisions += grid[row][col][0]
				chosen_con += [(row,col)]
				# Segment 3
				col = slave[1]	
				for row in range(mid_row, slave[0], vdir):
					chosen_length += 1
					chosen_collisions += grid[row][col][1]
				chosen_con += [slave]
			else:
				msg = "Unable to route connection %s"
				msg %= str(con)
				error(__file__, msg)
		# Store chosen connection to list
		cons_fine.append(chosen_con)	
		print("Routed as %s with %d collisions and length %d" % (str(chosen_con), chosen_collisions, chosen_length)) if debug else 0
		# Add chosen connection to grid
		for i in range(len(chosen_con)-1):
			seg = (chosen_con[i], chosen_con[i+1])
			seg_typ = "H" if seg[0][0] == seg[1][0] else "V"
			seg_dir = 1 if ((seg_typ == "H" and seg[0][1] < seg[1][1]) or (seg_typ == "V" and seg[0][0] < seg[1][0])) else -1
			idx = 0 if seg_typ == "H" else 1
			fix = seg[0][0] if seg_typ == "H" else seg[0][1]
			start = seg[0][1] if seg_typ == "H" else seg[0][0]
			start = start if i > 0 else start + seg_dir
			end = seg[1][1] if seg_typ == "H" else seg[1][0]
			end = end if i < len(chosen_con) - 2 else end - seg_dir
			for loc in range(start, end + seg_dir, seg_dir):
				(grid[fix][loc] if seg_typ == "H" else grid[loc][fix])[idx] += 1
	print_fine_grid(grid) if debug else 0
	return cons_fine


# Perform place and route for a homogeneous chip with same-sized tiles arranged in rows and columns
def place_and_route(module, tile, tech, prot, bw, freq, rows_of_tiles, cols_of_tiles, cons_raw):
	print("Place and Route...")

	# Input Validation	
	validate_connections(cons_raw)

	# Embed and load tile
	emb_tile_name = embed_tile_in_grid(tile, tech, prot, bw, int(freq))
	tile = Tile(emb_tile_name)

	# Route connections in coarse grid
	cons_coarse = route_in_coarse_grid(cons_raw,  tile)

	# Determine final grid size
	(row_sizes, col_sizes) = compute_final_grid_size(cons_coarse, tile, rows_of_tiles, cols_of_tiles)
	n_rows = sum(row_sizes.values())
	n_cols = sum(col_sizes.values())

	# Route connections in fine grid
	cons_fine = route_in_fine_grid(cons_coarse, tile, row_sizes, col_sizes)

	# Compose XML file for new module
	xml_root = ET.Element("module")
	ET.SubElement(xml_root, "technology").text = tile.technology
	ET.SubElement(xml_root, "protocol").text = tile.protocol
	ET.SubElement(xml_root, "bandwidth").text = str(tile.bandwidth)
	ET.SubElement(xml_root, "frequency").text = str(tile.frequency)
	ET.SubElement(xml_root, "n_rows").text = str(n_rows)
	ET.SubElement(xml_root, "n_cols").text = str(n_cols)
	# Add Tiles
	xml_comps = ET.SubElement(xml_root, "components")
	comp_id = 0
	row_acc = 0
	for row in row_sizes:	
		col_acc = 0
		for col in col_sizes:	
			if row % 2 == 1 and col % 2 == 1:
				loc = (row_acc, col_acc)
				xml_comp = ET.SubElement(xml_comps, "component")
				ET.SubElement(xml_comp, "id").text = str(comp_id)
				ET.SubElement(xml_comp, "type").text = "tile"
				ET.SubElement(xml_comp, "name").text = emb_tile_name
				ET.SubElement(xml_comp, "location").text = str(tuple(loc))
				ET.SubElement(xml_comp, "xmirror").text = "False"
				ET.SubElement(xml_comp, "ymirror").text = "False"
				comp_id += 1
			col_acc += col_sizes[col]
		row_acc += row_sizes[row]
	# Add Connections
	xml_conns = ET.SubElement(xml_root, "connections")
	for con in cons_fine:
		ET.SubElement(xml_conns, "connection").text=str(con).replace("[","(").replace("]",")")
	# Save File
	xml_string = minidom.parseString(ET.tostring(xml_root)).toprettyxml(indent="\t")
	xml_file = open(cfg.module_path + module + ".xml", "w")
	xml_file.write(xml_string)
	print("Saved as " + module)

