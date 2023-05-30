# Libraries
import sys
import os

# Display error message
def error(file, message, do_terminate = True):
	file = os.path.basename(file)
	print("ERROR in %s: %s" % (file, message))
	if do_terminate:
		sys.exit()

# Display warning message
def warning(file, message, do_terminate = False):
	file = os.path.basename(file)
	print("WARNING in %s: %s" % (file, message))
	if do_terminate:
		sys.exit()
