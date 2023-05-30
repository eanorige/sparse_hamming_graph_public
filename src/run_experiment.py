# Libraries
import csv
from xml.dom import minidom

# Custom files
from technology import Technology
from translate_lm_to_bs import translate_lm_to_bs
from run_booksim import run_booksim
from module import Module
import config as cfg

# Load steps used for BookSim
global_loads = [0.01,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,0.95,0.99]

# Experiment parameters
parameters = [	
	"exp_name",
	"chip_name",
	"param_name",
	"topology", 
	"topology_config", 
	"tiles",
	"tile_area", 
	"rows", 
	"cols", 
	"endpoints", 
	"technology", 
	"protocol", 
	"bandwidth", 
	"frequency", 
	"traffic", 
	"routing",
]

# Experiment outputs 
outputs = [
	"no_noc_area",
	"total_area",
	"logic_area",
	"wire_area",
	"empty_area",
	"area_overhead",

	"no_noc_power",
	"total_power",
	"logic_power",
	"wire_power",
	"noc_power",

	"latency",
	"throughput",
	"load_lat_pairs",	
]

# Function to run a list of experiments 
def run_experiment(experiments, output_filename):
	# Write header to results file
	with open(cfg.eval_results + output_filename + ".csv", "w") as out_file: 
		out_file.write(str(parameters)[1:-1].replace("'","").replace(" ","") + ",")
		out_file.write(str(outputs)[1:-1].replace("'","").replace(" ","") + "\n")
	# Iterate through experiments
	for exp in experiments:		
		# Generate topology under test
		exp["topology_generator"].generate(	exp["chip_name"], exp["tile_area"], \
											exp["endpoints"],
											exp["technology"], exp["protocol"],
											exp["bandwidth"], exp["frequency"],
											exp["rows"], exp["cols"], exp["topology_config"])
		# Load chip under test
		top = Module(exp["chip_name"])
		# Export topology to BookSim
		translate_lm_to_bs(exp["chip_name"], top.vertices, top.edges, top.edge_delays)
		# Run BookSim experiments
		run_booksim(exp["chip_name"], exp["traffic"], exp["routing"], global_loads)

		# Load technology info
		tech = Technology(exp["technology"])

		# Gather results...
		results = {}
		# ...Extract area
		results["no_noc_area"] = tech.mm2_per_ge * exp["tiles"] * exp["tile_area"]
		results["total_area"] = top.total_area_in_mm2
		results["logic_area"] = top.logic_area_in_mm2
		results["wire_area"] = top.wire_area_in_mm2
		results["empty_area"] = top.empty_area_in_mm2
		results["area_overhead"] = (results["total_area"] - results["no_noc_area"]) / results["total_area"]
		# ...Extract power 
		results["no_noc_power"] = tech.w_per_mm2_logic * results["no_noc_area"]
		results["total_power"] = top.total_power_in_w
		results["logic_power"] = top.logic_power_in_w
		results["wire_power"] = top.wire_power_in_w
		results["noc_power"] = max(results["total_power"] - results["no_noc_power"],0)

		# ...Read BookSim results
		bs_filename = cfg.bs_results + "results-%s-%s-%s.csv" % (exp["chip_name"], exp["traffic"], exp["routing"])
		with open(bs_filename, newline = '') as csvfile:
			latencies = {}
			reader = csv.reader(csvfile, delimiter=',', quotechar = '"')
			for row in reader:
				if len(row) > 1:
					load = float(row[0])
					latency = float(row[1])
					latencies[load] = latency
		results["load_lat_pairs"] = "\"" + str(list(zip(latencies.keys(), latencies.values()))) + "\""
		results["latency"] = min(latencies.values())
		results["throughput"] = min([x for x in  latencies.keys() if latencies[x] > 2 * results["latency"]] + [max(latencies.keys())])

		# Write results to csv file
		exp["topology_config"] = "\"" + str(exp["topology_config"]) + "\""
		with open(cfg.eval_results + output_filename + ".csv", "a") as out_file: 
			# Write parameters
			for param in parameters:
				out_file.write(str(exp[param]) + ",")
			# Write results 
			for res in outputs:
				out_file.write(str(results[res]) + ("," if outputs.index(res) < len(outputs) - 1 else "\n"))

