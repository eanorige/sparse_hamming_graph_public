# Libraries
import subprocess
import sys
import config as cfg

# Run BookSim with varying loads
def run_booksim(topo, traffic, routing, loads, is_coarse = True):
	# Files for results and logs
	res_file_name = cfg.bs_results + "results-%s-%s-%s.csv" % (topo, traffic, routing)
	log_file_name = cfg.bs_logs + "log-%s-%s-%s.log" % (topo, traffic, routing)
	# Simulation results
	results = {}
	print("=== %s - %s - %s ===" % (topo, traffic, routing))
	# Add header to logfile
	with open(log_file_name, "w") as log_file:
		log_file.write("Creating log for %s - %s - %s" % (topo, traffic, routing))
	# Iterate through loads
	lval = None
	for load in loads:
		print("-> " + str(load) + " => ", end = '')
		# Read and update configuration
		with open("../booksim2/src/anynet.conf", "r") as cfg_file:
			lines = cfg_file.readlines()
		lines[0] = "network_file = " + cfg.bs_topologies + topo + ".anynet;\n"
		lines[1] = "injection_rate = " + str(load) + ";\n"
		lines[2] = "traffic = " + traffic + ";\n"
		lines[3] = "routing_function = " + routing + ";\n"
		with open("../booksim2/src/anynet.conf", "w") as cfg_file:
			cfg_file.writelines(lines)
		# Start simulation and capture output
		proc = subprocess.Popen(['../booksim2/src/booksim', "../booksim2/src/anynet.conf"], stdout=subprocess.PIPE)
		out = proc.stdout.read()
		# Write lowest 50 lines of output to logfile
		out_list = str(out)[1:-1].split("\\n")[-50:]
		out_str = ""
		for line in out_list:
			out_str += line + "\n"	
		with open(log_file_name, "a") as log_file:
			log_file.write("\n\n*** %s - %s - %s - %f ***\n\n" % (topo, traffic, routing, load))	
			log_file.write(out_str)
		val = -1
		if "unstable" in out_str:
			val = 1000
		else:
			try:
				tmp = out_list[-29].split(" ")	
				for j in range(len(tmp)-1):
					if tmp[j] == "=":
						val = float(tmp[j+1])
						break
			except:
				val = -1
		# Store and print result
		results[load] = val
		print(val)
		# Run fine grained simulations
		if (val < 0 or (lval != None and (lval * 1.5 < val))) and is_coarse and load >= 0.1:
			fine_loads = [round(load - 0.1 + x / 100,2) for x in range(1,10)]
			fine_results = run_booksim(topo, traffic, routing, fine_loads, False)
			for fine_load in fine_results:
				results[fine_load] = fine_results[fine_load]
		lval = val
		# Stop simulations 
		if val < 0 or val >= 1000:	
			break
	if is_coarse:
		with open(res_file_name, "w") as res_file:
			for load in sorted(results):
				res_file.write("%f, %f\n" % (load, results[load]))
	else:
		return results

### Main ###
if __name__ == "__main__":
	loads = [0.01,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,0.99]
	if len(sys.argv) < 4:
		print("Usage: run_simulation.py <topology> <traffic> <routing> [load]")
		sys.exit()
	topo = sys.argv[1]
	traffic = sys.argv[2]
	routing = sys.argv[3]
	one_load = sys.argv[4] if len(sys.argv) > 4 else None
	loads = loads if one_load == None else [float(one_load)]
	run_booksim(topo, traffic, routing, loads)

