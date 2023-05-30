# Libraries
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import math
import sys

# Custom files
from tile import Tile
from module import Module
from stacked_chip import StackedChip
from error import error, warning


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

def draw_rectangle(x, y, w, h, c, a = 1.0, border = False, grid_mode = True):
	if grid_mode:
		x = x * 0.5 # TODO: Replace by technology-dependent factor
		w = w * 0.5
	if border:
		rectangle = plt.Rectangle((x,y), w, h, fc = c, fill = True, alpha = a, ec = "#000000")
	else:
		rectangle = plt.Rectangle((x,y), w, h, fc = c, fill = True, alpha = a)
	plt.gca().add_patch(rectangle)

def visualize_floorplan(grid, scale):

	n_rows_orig = len(grid)
	n_cols_orig = len(grid[0])

	n_rows = math.ceil(n_rows_orig / scale)
	n_cols = math.ceil(n_cols_orig / scale)

	scale_grid = [[[0,0,0] for i in range(n_cols)] for j in range(n_rows)]	

	for row in range(n_rows_orig):
		for col in range(n_cols_orig):
			r = row // scale
			c = col // scale
			if type(grid[row][col]) == str and grid[row][col] in  ["M","S","T"]:
				scale_grid[r][c][0] += 1
			if type(grid[row][col]) == list:
				if grid[row][col][1] > 0:
					scale_grid[r][c][1] += 1
				if grid[row][col][0] >0:
					scale_grid[r][c][2] += 1

	fig, ax = plt.subplots()

	for row in range(n_rows):
		for col in range(n_cols):
			r = int(scale_grid[row][col][0] * 255 / scale**2)
			g = int(scale_grid[row][col][1] * 255 / scale**2)
			b = int(scale_grid[row][col][2] * 255 / scale**2)
			color = '#%02x%02x%02x' % (r,g,b)
			draw_rectangle(col, row, 1, 1, color)

	# Fix ticks
	ax.set_xticks([])
	ax.set_yticks([])
	ax.set_xlim(0,n_cols/2)
	ax.set_ylim(0,n_rows)

	# Make ration between height and width correct
	plt.gca().set_aspect('equal', adjustable='box')
	plt.show()


# Read a tile/module and visualize it
def read_and_visualize(typ, name, scale):
	if typ == "tile":
		grid = Tile(name).grid
	elif typ == "module":
		grid = Module(name).grid
	elif typ == "schip":
		# TODO: Add floorplan visualization for 2.5D stacked chips
		msg = "Visualizing 2.5D stacked chips is not supported"
		error(__file__, msg)
	else:
		msg = "Invalid type \"%s\". Only \"tile\" and \"module\" are valid"
		msg %= typ
		error(__file__, msg)
	visualize_floorplan(grid, scale)

if __name__ == "__main__":
    args = sys.argv
    if len(args) < 4:
        print("Usage: python physical_visualizer.py <type in {tile, module}> <name> <scale>")
        sys.exit()
    read_and_visualize(args[1], args[2], int(args[3]))

		
		
