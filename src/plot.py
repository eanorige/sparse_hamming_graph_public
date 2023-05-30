# Libraries
import matplotlib.pyplot as plt
import pandas as pd

# Custom files
import config as cfg

# configure label, color, marker and abbreviation for topologies
def get_lab_col_mar_abv(name):
	col = "#666666"
	mar = "o"
	lab = "name"

	if "ring" in name:
		col = "#990000"
		mar = "h"
		lab = "Ring"
		abv = "R"
	if "mesh" in name:
		col = "#009900"
		mar = "P"
		lab = "2D Mesh"
		abv = "M"
	if "torus" in name:
		col = "#000099"
		mar = "D"
		lab = "2D Torus"
		abv = "2DT"
	if "folded_torus" in name:
		col = "#009999"
		mar = "d"
		lab = "Folded 2D Torus"
		abv = "F2DT"
	if "slimnoc" in name:
		col = "#999900"
		mar = "p"
		lab = "SlimNoC"
		abv = "SN"
	if "flattened_butterfly" in name:
		col = "#990099"
		mar = "v"
		lab = "Flattened Butterfly"
		abv = "FB"
	if "custom" in name:
		col = "#000000"
		mar = "*"
		lab = "Sparse Hamming Graph (This Work)"
		abv = "TW"
	if "custom-additional" in name:
		col = "#666666"
		mar = "o"
		lab = "Sparse Hamming Graph (Other Configurations)"
		abv = "SHG"
	if "hypercube" in name:
		col = "#996600"
		mar = "s"
		lab = "Hypercube"
		abv = "HC"
	if "bidir" in name:
		col = col.replace("DD","88").replace("66","11")
	return (lab, col, mar, abv)

# Create comparison plot with latency-vs-load plot, area-bars and power-bars
def create_comparison_plot_v1(filename, plotname, topologies, param_name):

	# Read data
	df = pd.read_csv(cfg.eval_results + filename + ".csv");
	df = df[(df["param_name"] == param_name) & (df["topology"].isin(topologies))]

	# Set up figure
	fig, ax = plt.subplots(1,3, figsize = (5,2), gridspec_kw={'width_ratios': [2, 1, 1]})
	plt.subplots_adjust(left=0.08, right = 0.99, top = 0.9, bottom = 0.2, wspace = 0.33)

	# Grid
	ax[0].grid()
	ax[1].grid(axis = "y")
	ax[2].grid(axis = "y")

	# Labels
	ax[0].set_xlabel("Offered Load [%]")
	ax[0].set_ylabel("Latency [cycles]", labelpad = 2)
	ax[1].set_ylabel("Area Overhead [%]", labelpad = 0)
	ax[2].set_ylabel("Power [$W$]", labelpad = 0)

	# Pre-process data 
	areas = []
	powers = []
	colors = []	
	abbreviations = []
	for topology in topologies:	
		(lab, col, mar, abv) = get_lab_col_mar_abv(topology)
		data = df[(df["topology"] == topology)]
		if len(data.index) > 0:
			# create latency-vs-load plot
			load_lat_pairs = eval(data["load_lat_pairs"].iat[0])
			loads = [x[0] for x in load_lat_pairs]
			lats = [x[1] for x in load_lat_pairs]
			ax[0].plot(loads, lats, label = lab, marker = mar, color = col, markersize = 3,\
					fillstyle="none", linewidth = 1)
			# Prepare bar plot (area)
			areas.append(data["area_overhead"].iat[0])
			powers.append(data["noc_power"].iat[0])
			colors.append(col)	
			abbreviations.append(abv)
	# Fix ticks
	ax[0].set_xticks([0,0.2,0.4,0.6,0.8,1.0], ["0","20","40","60","80","100"], fontsize = 9)
	ax[0].set_yticklabels([int(x) for x in ax[0].get_yticks()], rotation = 90, va = "center", fontsize = 9)
	xlocs = list(range(len(areas)))

	# Area plot
	ax[1].bar(xlocs, areas, color = colors, label = abbreviations, zorder = 2)
	ax[1].set_xticks(xlocs, abbreviations, rotation = 90, fontsize = 8)
	ax[1].set_ylim(0,1)
	ax[1].set_yticklabels([int(100 * x) for x in ax[1].get_yticks()], rotation = 90, va = "center", fontsize = 9)

	# Power plot
	xlocs = list(range(len(powers)))
	ax[2].bar(xlocs, powers, color = colors, label = abbreviations, zorder = 2)
	ax[2].set_xticks(xlocs, abbreviations, rotation = 90, fontsize = 8)
	ax[2].set_yticklabels([int(x) for x in ax[2].get_yticks()], rotation = 90, va = "center", fontsize = 9)
	
	# Axis
	ax[0].set_xlim(0,1.0)
	ax[0].set_ylim(0,310)

	# Store plot
	plt.savefig(cfg.plots + plotname + ".pdf")

# Create comparison plots with one latency-vs-throughput and one power-vs-area plot
def create_comparison_plot_v2(filename, plotname, topologies, param_name):

	# Read data
	df = pd.read_csv(cfg.eval_results + filename + ".csv");
	df = df[(df["param_name"] == param_name) & (df["topology"].isin(topologies))]

	# Set up figure
	fig, ax = plt.subplots(1,2, figsize = (5,2.5))
	plt.subplots_adjust(left=0.12, right = 0.97, top = 0.9, bottom = 0.2, wspace = 0.4)


	# Titles 
	ax[0].set_title("Cost")
	ax[1].set_title("Performance")

	# Axis labels
	ax[0].set_xlabel("NoC Power Consumption [W]")
	ax[1].set_xlabel("Zero-Load Latency [cycles]")
	ax[0].set_ylabel("NoC Area Overhead [%]")
	ax[1].set_ylabel("Saturation Throughput [%]")

	# Find maximum x values
	mxpower = 32 if "64" in plotname else 210 
	mxlatency = 200 if "64" in plotname else 400 
	mxarea = 102 
	

	# Axis limits
	ax[0].set_xlim(-mxpower/50, mxpower)
	ax[0].set_ylim(-2,mxarea)
	ax[1].set_xlim(-mxlatency/50, mxlatency)
	ax[1].set_ylim(-2,102)

	# Grid and Arrow pointing towards "better" direction
	for i in range(2):
		# Grid	
		ax[i].grid(zorder = 0)
		# Arrow
		xlim = mxpower if i == 0 else mxlatency
		ylim = mxarea if i == 0 else 100 
		tweak = (-1 if i == 0 else 1)
		length = (-xlim / 5, tweak * ylim / 5)
		start = (xlim/2 - length[0]/2, ylim/2 - length[1]/2)
		end = (start[0] + length[0], start[1] + length[1])
		rot = 0 if i == 0 else 90
		prop = dict(arrowstyle="-|>,head_width=0.2,head_length=0.8", facecolor='black')
		ax[i].annotate("", xy=end, xytext=start, arrowprops=prop, )	
		# Text
		ax[i].text(start[0] + length[0]/2 + tweak * xlim / 30, start[1] + length[1]/2 + 5, "Better", rotation = 45 - rot, ha = "center", va = "center", fontsize = 9)

	# Plot data 
	additional_cnt = 1
	for topology in topologies:	
		(lab, col, mar, abv) = get_lab_col_mar_abv(topology)
		data = df[(df["topology"] == topology)]
		# Skip if no data found
		if len(data) == 0:
			continue
		for i in range(len(data["topology"])):
			# Extract metrics of interest
			area = data["area_overhead"].iat[i] * 100
			power = data["noc_power"].iat[i]
			latency = data["latency"].iat[i]
			throughput = data["throughput"].iat[i] * 100
			# Create plots	
			ax[0].plot(power, area, label = lab, marker = mar, color = col, markersize = 6)
			ax[1].plot(latency, throughput, label = lab, marker = mar, color = col, markersize = 6)
			if data["topology"].iat[i] == "custom-additional":
				num = str(additional_cnt)
				additional_cnt += 1
				ax[0].text(power, area-0.5, num, ha = "center", va = "center", fontsize = 6, fontweight = "bold")
				ax[1].text(latency, throughput-0.5, num, ha = "center", va = "center", fontsize = 6, fontweight = "bold")
	# Save plot
	plt.savefig(cfg.plots + plotname + ".pdf")

# Only create the legend, needed for DAC paper
def create_legend_only(topologies, plotname):
	plt.close("all")
	plt.axis('off')
	f = lambda m,c: plt.plot([],[],marker=m, color=c, ls="none")[0]
	handles = []
	labels = []
	for topology in topologies:
		(lab, col, mar, abv) = get_lab_col_mar_abv(topology)
		handles.append(f(mar, col))
		labels.append(lab)
	legend = plt.legend(handles, labels, loc=0, frameon=True, ncol = 9, columnspacing = 0.5, handletextpad = 0.2)
	fig  = legend.figure
	fig.canvas.draw()
	bbox = legend.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
	fig.savefig(cfg.plots + plotname + ".pdf", dpi="figure", bbox_inches=bbox)

	

# Create comparison plots with one latency-vs-throughput and one power-vs-area plot
def create_additional_plot_for_slides(filename, plotname, topologies, param_name):

	radix_map = {
		"ring" : 2,
		"mesh" : 4,
		"torus" : 4,
		"folded_torus" : 4,
		"hypercube" : 7,
		"slimnoc" : 12,
		"flattened_butterfly" : 22,
	}

	diam_map = {
		"ring" : 64,
		"mesh" : 22,
		"torus" : 12,
		"folded_torus" : 12,
		"hypercube" : 7,
		"slimnoc" : 2,
		"flattened_butterfly" : 2,
	}


	# Read data
	df = pd.read_csv(cfg.eval_results + filename + ".csv");
	df = df[(df["param_name"] == param_name) & (df["topology"].isin(topologies))]

	############### Figure 1: Area vs. Router Radix ##################
	# Set up figure
	fig, ax = plt.subplots(1,1, figsize = (3,3))
	plt.subplots_adjust(left=0.2, right = 0.95, top = 0.95, bottom = 0.15)
	ax.grid()
	ax.set_ylim(0,100)
	ax.set_xlim(0,25)
	ax.set_xlabel("Router Radix")
	ax.set_ylabel("NoC Area [%]")
	# Plot data 
	for topology in topologies:	
		(lab, col, mar, abv) = get_lab_col_mar_abv(topology)
		data = df[(df["topology"] == topology)]
		# Skip if no data found
		if len(data) == 0:
			continue
		for i in range(len(data["topology"])):
			# Extract metrics of interest
			radix = radix_map[data["topology"].iat[i]]
			area = data["area_overhead"].iat[i] * 100
			# Create plots	
			ax.plot(radix, area, label = lab, marker = mar, color = col, markersize = 6)
	# Save plot
	plt.savefig(cfg.plots + plotname + "_area_vs_radix.pdf")

	############### Figure 2: throughput vs. Network Diameter ##################
	# Set up figure
	fig, ax = plt.subplots(1,1, figsize = (3,3))
	plt.subplots_adjust(left=0.2, right = 0.95, top = 0.95, bottom = 0.15)
	ax.grid()
	ax.set_ylim(0,100)
	ax.set_xlim(0,65)
	ax.set_xlabel("Network Diameter")
	ax.set_ylabel("Saturation Throughput [%]")
	ax.set_xticks([10*x for x in range(8)])
	# Plot data 
	for topology in topologies:	
		(lab, col, mar, abv) = get_lab_col_mar_abv(topology)
		data = df[(df["topology"] == topology)]
		# Skip if no data found
		if len(data) == 0:
			continue
		for i in range(len(data["topology"])):
			# Extract metrics of interest
			diam = diam_map[data["topology"].iat[i]]
			tp = data["throughput"].iat[i] * 100
			# Create plots	
			ax.plot(diam, tp, label = lab, marker = mar, color = col, markersize = 6)
	# Save plot
	plt.savefig(cfg.plots + plotname + "_tp_vs_diam.pdf")


