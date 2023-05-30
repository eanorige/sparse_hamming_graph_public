# Libraries
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import sys

# Custom files
from tile import Tile
from module import Module
from stacked_chip import StackedChip
from technology import Technology
from error import error, warning

# Colors used for different aspects of the model
grid_color = "#999999"
tile_color = "#9999FF"
schip_color = "#CCCCCC"
chiplet_color = "#888888"
master_color = "#FF9999"
slave_color = "#FFFF99"
phy_in_color = "#FF9933"
phy_out_color = "#CC6600"
con_color = "#333333"
collision_color = "#FF0000"

wire_ratio = 1

# Auxiliary Function: Component-wise addition of two tuples
def tadd(a,b):
	return (a[0] + b[0], a[1] + b[1])

# Draw a line
def draw_line(a,b,c, arr = False, lwd= 1, grid_mode = True):
	global wire_ratio
	if grid_mode:
		(a,b) = ((a[0]*wire_ratio, a[1]),(b[0]*wire_ratio,b[1]))
	plt.arrow(	a[0],a[1],b[0]-a[0],b[1]-a[1], 
				color = c, 
				head_width = 0.1 if arr else 0,
				length_includes_head = True,
				linewidth = lwd)

# Draw a rectangle
def draw_rectangle(x, y, w, h, c, a = 1.0, border = False, grid_mode = True):
	global wire_ratio
	if grid_mode:
		x = x * wire_ratio 
		w = w * wire_ratio
	if border:
		rectangle = plt.Rectangle((x,y), w, h, fc = c, fill = True, alpha = a, ec = "#000000")
	else:
		rectangle = plt.Rectangle((x,y), w, h, fc = c, fill = True, alpha = a)
	plt.gca().add_patch(rectangle)

# Draw a circle
def draw_circle(x,y,r,c):
	circle = plt.Circle((x,y),radius = r, color = c)
	plt.gca().add_patch(circle)

# Draw text
def draw_text(x,y,txt):
	global wire_ratio
	x = x * wire_ratio
	plt.text(x,y,txt,verticalalignment='center', horizontalalignment='center',)

# Visualize a single tile
def visualize_tile(tile):
	(rows, cols) = (tile.n_rows, tile.n_cols)
	fig, ax = plt.subplots()
	# Draw tile
	draw_rectangle(0, 0, cols, rows, tile_color)
	# Draw grid
	for row in range(rows + 1):
		draw_line((0,row),(cols,row), grid_color)
	for col in range(cols + 1):
		draw_line((col,0),(col,rows), grid_color)
	# Draw master-ports:
	for mport in tile.master_ports:
		(row,col) = mport["location"]
		draw_rectangle(col, row, 1, 1, master_color)
	# Draw slave-ports:
	for sport in tile.slave_ports:
		(row,col) = sport["location"]
		draw_rectangle(col, row, 1, 1, slave_color)
	# Draw phys:
	for phy in tile.phys:
		(row,col) = phy["location"]
		color = phy_in_color if phy["direction"] == "in" else phy_out_color
		draw_rectangle(col, row, 1, 1, color)
	# Fix ticks
	ax.set_xticks([(x + 0.5) * 0.5 for x in range(cols)])
	ax.set_xticklabels([str(x) for x in range(cols)])
	ax.set_yticks([x + 0.5 for x in range(rows)])
	ax.set_yticklabels([str(x) for x in range(rows)])
	# Make ration between height and width correct
	plt.gca().set_aspect('equal', adjustable='box')
	plt.show()

# Draw a module 
def visualize_module(module):
	(rows, cols) = (module.n_rows, module.n_cols)
	fig, ax = plt.subplots()
	# Draw tiles
	for tile in module.tiles:
		(row, col) = tile["location"]
		(height, width) = tile["dimensions"]
		draw_rectangle(col, row, width, height, tile_color)
	# Draw grid
	for row in range(rows + 1):
		draw_line((0,row),(cols,row), grid_color)
	for col in range(cols + 1):
		draw_line((col,0),(col,rows), grid_color)
	# Draw master-ports:
	for mport in module.master_ports:
		(row,col) = mport["location"]
		draw_rectangle(col, row, 1, 1, master_color)
		pid = mport["label"][-2]
		draw_text(col+0.5,row+0.25,pid)
		draw_text(col+0.5,row+0.75,pid)
	# Draw slave-ports:
	for sport in module.slave_ports:
		(row,col) = sport["location"]
		draw_rectangle(col, row, 1, 1, slave_color)
		pid = sport["label"][-2]
		draw_text(col+0.5,row+0.25,pid)
		draw_text(col+0.5,row+0.75,pid)
	# Draw phys:
	for phy in module.phys:
		(row,col) = phy["location"]
		color = phy_in_color if phy["direction"] == "in" else phy_out_color
		draw_rectangle(col, row, 1, 1, color)
		pid = phy["label"][-2]
		draw_text(col+0.5,row+0.25,pid)
		draw_text(col+0.5,row+0.75,pid)
	# Draw collisions:
	grid = module.grid
	for row in range(rows):
		for col in range(cols):
			if type(grid[row][col]) == list and (grid[row][col][0] > 1 or grid[row][col][1] > 1):
				draw_rectangle(col, row, 1, 1, collision_color)
	# Draw connections:
	for con in module.connections:
		for i in range(len(con)-1):
			a = con[i]
			b = con[i+1] 
			draw_line((a[1]+0.5,a[0]+0.5),(b[1]+0.5, b[0]+0.5), con_color, True, 1.5)
	# Draw tile-borders
	for tile in module.tiles:
		(row, col) = tile["location"]
		(height, width) = tile["dimensions"]
		draw_rectangle(col, row, width, height, "none", border = True)
	# Fix ticks
	ax.set_xticks([(x + 0.5) * 0.5 for x in range(cols)])
	ax.set_xticklabels([str(x) for x in range(cols)])
	ax.set_yticks([x + 0.5 for x in range(rows)])
	ax.set_yticklabels([str(x) for x in range(rows)])
	# Make ration between height and width correct
	plt.gca().set_aspect('equal', adjustable='box')
	plt.show()

# Draw a 2.5D stacked chip
def visualize_schip(schip):
	(width, height) = (schip.width_in_mm, schip.height_in_mm)
	fig, ax = plt.subplots()
	ax.set_xlim(0,width)
	ax.set_ylim(0,height)
	# Draw stacked chip
	draw_rectangle(0, 0, width, height, schip_color, grid_mode = False)
	# Draw chiplets
	for chiplet in schip.chiplets:
		(x,y) = chiplet["location"]
		(w,h) = (chiplet["width"], chiplet["height"])	
		draw_rectangle(x, y, w, h, chiplet_color, grid_mode = False)
		for phy in chiplet["phys"]:
			(x_phy,y_phy) = phy["location"]
			color = phy_in_color if phy["direction"] == "in" else phy_out_color
			draw_circle(x + x_phy, y + y_phy, 0.5, color)
	# Connections
	for ((c1,m1,p1,l1), (c2,m2,p2,l2), _) in schip.connections:
		phy1_loc = phy2_loc = None
		chiplet = schip.chiplets[c1]
		for phy in chiplet["phys"]:
			if phy["label"] == (m1,p1,l1):
				phy1_loc = tadd(chiplet["location"], phy["location"])
		chiplet = schip.chiplets[c2]
		for phy in chiplet["phys"]:
			if phy["label"] == (m2,p2,l2):
				phy2_loc = tadd(chiplet["location"], phy["location"])
		if None not in [phy1_loc, phy2_loc]:
			draw_line(phy1_loc, phy2_loc, con_color, arr = True, lwd= 3, grid_mode = False)
	# Make ratio between height and width correct
	plt.gca().set_aspect('equal', adjustable='box')
	plt.show()

# Read a tile/module/stacked-chip and visualize it
def read_and_visualize(typ, name):
	global wire_ratio
	# Tile
	if typ == "tile":
		tile = Tile(name)
		tech = Technology(tile.technology)
		wire_ratio = tech.mm_per_vertical_wire / tech.mm_per_horizontal_wire	
		visualize_tile(tile)
	# Module 
	elif typ == "module":
		module = Module(name)
		tech = Technology(module.technology)
		wire_ratio = tech.mm_per_vertical_wire / tech.mm_per_horizontal_wire	
		visualize_module(module)
	# 2.5D Stacked Chip
	elif typ == "schip":
		schip = StackedChip(name)
		visualize_schip(schip)
	else:
		msg = "Invalid type \"%s\". Only \"tile\" and \"module\" are valid"
		msg %= typ
		error(__file__, msg)

if __name__ == "__main__":
    args = sys.argv
    if len(args) < 3:
        print("Usage: python visualize_physical_model.py <type in {tile, module, schip}> <name>")
        sys.exit()
    read_and_visualize(args[1], args[2])

		
		
