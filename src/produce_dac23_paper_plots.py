# Custom files
from run_experiment import run_experiment
from plot import create_comparison_plot_v2, create_legend_only

# Custom topology generation scripts 
import generate_ring as gr
import generate_mesh as gm
import generate_torus as gt
import generate_folded_torus as gft
import generate_hypercube as ghc
import generate_flattened_butterfly as gfb
import generate_slimnoc as gs
import generate_custom as gc

def produce():
	# General Settings
	tech = "gf22"
	prot = "axi"
	freq = 1.2e9
	traffic = "uniform"
	routing = "min"
	bw = 512

	# Architectural Parameters
	arch_params = [
		# name, logic_area, rows, cols, endpoints 
		("64tiles_1endpoint_35MGE", 35e6, 8, 8, 1),
		("128tiles_1endpoint_35MGE", 35e6, 8, 16, 1),
		("64tiles_2endpoint_70MGE", 70e6, 8, 8, 2),
		("128tiles_2endpoint_70MGE", 70e6, 8, 16, 2),
	]

	# Topologies
	topos = [
		# name, generator, configuration
		("ring", gr, [True]),
		("mesh", gm, []),
		("torus", gt, [True]),
		("folded_torus", gft, [True]),
		("hypercube", ghc, []),
		("slimnoc", gs, None),
		("flattened_butterfly", gfb, []),
		("custom", gc, None),
	]

	# Get slimnoc config for specific #rows and #cols
	def get_slimnoc_config(rows, cols):
		if (rows, cols) == (4,8):
			return [4,4,8]
		elif (rows, cols) == (8,16):
			return [8,8,16]
		else:
			return None 


	# Get custom config for specific set of architectural parameters
	def get_custom_config(param_name):
		if param_name == "64tiles_1endpoint_35MGE":
			Sr = [4]
			Sc = [2,5]
		elif param_name == "128tiles_1endpoint_35MGE":
			Sr = [3]
			Sc = [2,5]
		elif param_name == "64tiles_2endpoint_70MGE":
			Sr = [2,4]
			Sc = [2,4]
		elif param_name == "128tiles_2endpoint_70MGE":
			Sr = [2,4]
			Sc = [2,4]
		else:
			Sr = []
			Sc = []
		return [Sr, Sc]

	# Compile configurations for experiments
	experiments = []
	for (param_name, tile_area, rows, cols, endpoints) in arch_params:
		for (topo_name, generator, config) in topos:
			# Generate config for special topologies
			if topo_name == "slimnoc":
				config = get_slimnoc_config(rows, cols)
				if config == None:
					continue	
			if topo_name == "custom":
				config = get_custom_config(param_name)
			# Compile experiment parameters
			exp_name = param_name + "_" + topo_name		
			exp = {}
			exp["exp_name"] = exp_name
			exp["chip_name"] = exp_name
			exp["param_name"] = param_name
			exp["topology"] = topo_name
			exp["topology_generator"] = generator 
			exp["topology_config"] = config
			exp["tiles"] = rows * cols
			exp["tile_area"] = int(tile_area)
			exp["rows"] = rows
			exp["cols"] = cols
			exp["endpoints"] = endpoints
			exp["technology"] = tech
			exp["protocol"] = prot
			exp["bandwidth"] = bw
			exp["frequency"] = int(freq)
			exp["traffic"] = traffic
			exp["routing"] = routing
			experiments.append(exp)

	# Evaluate all experiments
	name = "comparison_for_dac23_paper"
	run_experiment(experiments, name)

	# Create plots
	for (param_name, tile_area, rows, cols, endpoints) in arch_params:
		plot_name = name + "_" + param_name
		topos_for_plots = [topo[0] for topo in topos]
		create_comparison_plot_v2(name, plot_name, topos_for_plots, param_name) 

	# Create legend for plots
	topologies = []
	for exp in experiments:
		if exp["tiles"] == 128:
			if exp["topology"] not in topologies:
				topologies.append(exp["topology"])
	create_legend_only(topologies, "legend_for_dac23_paper")

### Main ###
if __name__ == "__main__":
	produce()


