#Libraries
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Custom files 
from tile import Tile
from module import Module 
from error import error
import config as cfg

# Settings...
# ...Activate debug output
debug = False
# ...Reduce the number of corners per connection
#    For some reason, this does not yet seem to work...
corner_penalty = 5
# ...Number of cells that connection can make detours w.r.t. optimal path
#    Larger -> Slower, more accurate, higher chance of successful routing
detour_limit_h = 50
detour_limit_v = 10

# Print grid (only used for debugging)
def print_grid(grid):
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

# Routing of connections in heterogeneous design where locations of
# components (placement) is already given as input
def place_and_route(components, connections, n_rows, n_cols, save_name):
	print("Routing Module %s..." % save_name)

	# Pre-process components:
	for comp in components:
		if "xmirror" not in comp:
			comp["xmirror"] = False
		if "ymirror" not in comp:
			comp["ymirror"] = False
		if "type" not in comp:
			comp["type"] = "tile"
			
	# Create grid of unit-cells
	grid = [[[0,0] for i in range(n_cols)] for j in range(n_rows)]

	# Place Components 
	for cid in range(len(components)):
		# Read components
		comp = components[cid]
		comp_obj = Tile(comp["name"]) if comp["type"] == "tile" else Module(comp["name"])
		comp_obj.mirror(comp["xmirror"], comp["ymirror"])
		comp["object"] = comp_obj
		# Copy component-grid into main grid
		for r in range(comp_obj.n_rows):
			for c in range(comp_obj.n_cols):
				row = comp["location"][0] + r
				col = comp["location"][1] + c
				cell_content = comp_obj.grid[r][c]
				# VALIDATION: Overlapping Tiles 
				if type(cell_content) == str:
					if grid[row][col] != [0,0]:
						msg = "Overlapping Tiles or Modules"
						error(__file__, msg)
					grid[row][col] = cell_content
				elif type(grid[row][col]) == list:
					grid[row][col][0] += cell_content[0]
					grid[row][col][1] += cell_content[1]

	# Route Connections By using Dijkstra
	cons = []
	for cid in range(len(connections)):
		(source_label, destination_label) = connections[cid]
		print("Routing connection %d of %d" % (cid+1, len(connections)))

		# A second grid used for Dijkstra
		dgrid = [[[float("inf"),float("inf"),None,None] for i in range(n_cols)] for j in range(n_rows)]

		# Source tile
		source_loc_coarse = components[source_label[0]]["location"]
		source_loc_fine = components[source_label[0]]["object"].master_port_lab_to_loc[source_label[1:]]
		source = (source_loc_coarse[0] + source_loc_fine[0], source_loc_coarse[1] + source_loc_fine[1])

		# Target tile
		destination_loc_coarse = components[destination_label[0]]["location"]
		destination_loc_fine = components[destination_label[0]]["object"].slave_port_lab_to_loc[destination_label[1:]]
		destination = (destination_loc_coarse[0] + destination_loc_fine[0], destination_loc_coarse[1] + destination_loc_fine[1])

		# Routing can only cells in abounding box:
		# This speeds up routing but reduces quality of result
		# Size of bounding box can be configured on top of the file
		bottom_bound = min(source[0], destination[0]) - detour_limit_v
		top_bound = max(source[0], destination[0]) + detour_limit_v
		left_bound = min(source[1], destination[1]) - detour_limit_h
		right_bound = max(source[1], destination[1]) + detour_limit_h

		# Perform Dijkstra
		todo = [source]
		dgrid[source[0]][source[1]] = (0,0,None,None) # collisions, distance, direction, previous
		while len(todo) > 0:	
			(cr,cc) = todo.pop(0)
			# Look at all neighboring unit-cells
			for (rd,cd) in [(0,1),(0,-1),(1,0),(-1,0)]:	
				(nr, nc) = (cr + rd, cc + cd)
				# Only continue if neighboring unit-cell is present (not out of bounds)
				if cr + rd < n_rows and cr + rd >= 0 and cc + cd < n_cols and cc + cd >= 0:
					# We only consider unit-cells available for wires and slave-ports of tiles
					if type(grid[nr][nc]) == list or (nr,nc) == destination:
						# We only consider cells that are within the bounding box for routing (see above) 
						if cr + rd <= top_bound and cr + rd >= bottom_bound and cc + cd <= right_bound and cc + cd >= left_bound:
							cols = dgrid[cr][cc][0] + (grid[nr][nc][abs(rd)] if (nr,nc) != destination else 0)
							dist = dgrid[cr][cc][1] + 1
							# If we change direction in current cell
							if abs(rd) != dgrid[cr][cc][2] and dgrid[cr][cc][2] != None:
								if type(grid[cr][cc]) == list:
									cols += grid[cr][cc][dgrid[cr][cc][2]] 	# Also check for collisions in current cell
								dist += corner_penalty						# Penalize corners (currently only in terms of length)
							# If we found a shorter path to a new unit-cell
							if cols < dgrid[nr][nc][0] or (cols < dgrid[nr][nc][0] and dist < dgrid[nr][nc][1]):
								dgrid[nr][nc][0] = cols
								dgrid[nr][nc][1] = dist
								dgrid[nr][nc][2] = abs(rd)
								dgrid[nr][nc][3] = (cr,cc)
								todo.append((nr,nc))

		# If unable to route: Continue
		if dgrid[destination[0]][destination[1]][3] == None:
			print("Unable to route connection...")
			print((source, destination))
			continue

		# Back tracking to reconstruct connection
		con = [destination]
		cur = destination
		while cur != source:
			# Current
			(cr,cc) = cur
			# Previous
			prv = dgrid[cr][cc][3]
			(pr,pc) = prv
			# Directions
			cdir = dgrid[cr][cc][2]
			pdir = dgrid[pr][pc][2]
			# Update original grid
			if cur not in [source, destination]:
				grid[cr][cc][cdir] += 1
			# Corner: Additional grid update + insert corner into connection
			if  cdir != pdir and (pr,pc) != source:
				con.insert(0, prv)
				grid[pr][pc][cdir] += 1
			# Next hop
			cur = prv
		con.insert(0, source)
		cons.append(con)

	# Compose XML file for new module
	xml_root = ET.Element("module")
	comp = components[0]["object"]
	ET.SubElement(xml_root, "technology").text = comp.technology
	ET.SubElement(xml_root, "protocol").text = comp.protocol
	ET.SubElement(xml_root, "bandwidth").text = str(comp.bandwidth)
	ET.SubElement(xml_root, "frequency").text = str(comp.frequency)
	ET.SubElement(xml_root, "n_rows").text = str(n_rows)
	ET.SubElement(xml_root, "n_cols").text = str(n_cols)
	# Add Components
	xml_comps = ET.SubElement(xml_root, "components")
	for cid in range(len(components)):
		comp = components[cid]
		xml_comp = ET.SubElement(xml_comps, "component")
		ET.SubElement(xml_comp, "id").text = str(cid)
		ET.SubElement(xml_comp, "type").text = comp["type"]
		ET.SubElement(xml_comp, "name").text = comp["name"]
		ET.SubElement(xml_comp, "location").text = str(comp["location"])
		ET.SubElement(xml_comp, "xmirror").text = str(comp["xmirror"] if "xmirror" in comp else False)
		ET.SubElement(xml_comp, "ymirror").text = str(comp["ymirror"] if "ymirror" in comp else False)
	# Add Connections
	xml_conns = ET.SubElement(xml_root, "connections")
	for con in cons:
		ET.SubElement(xml_conns, "connection").text=str(con).replace("[","(").replace("]",")")
	# Save File
	xml_string = minidom.parseString(ET.tostring(xml_root)).toprettyxml(indent="\t")
	xml_file = open(cfg.module_path + save_name + ".xml", "w")
	xml_file.write(xml_string)
	print("saved as \"%s%s\"" % (cfg.module_path, save_name))

			
