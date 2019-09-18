#!python3

import argparse
import os.path
import importlib 
# import later: evaluate_waveform

args = None


def extant_file(x):
	# https://stackoverflow.com/questions/11540854/file-as-command-line-argument-for-argparse-error-message-if-argument-is-not-va
    if not os.path.exists(x):
        # Argparse uses the ArgumentTypeError to give a rejection message
        raise argparse.ArgumentTypeError("{0} does not exist".format(x))
    return x
	
	
def extant_dir(x):
	x = os.path.abspath(x)
	if not os.path.isdir(x):
		raise argparse.ArgumentTypeError("'{0}' is not a valid directory.".format(x))
	return x


def init_argparse():
	global args	
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--directory", type=extant_dir, help="starting path for processing.", required=True)
	parser.add_argument("-r", "--recursive", action='store_true', default=False, help='recursively process subdirectories.')
	parser.add_argument("-f", "--inputformat", type=str, help="Input format identifier. (folder name of a template in formats/)", required=True)
	parser.add_argument("-s", "--setup", type=str, help="Setup identifier for pre-processing (folder name of a template in setups/)", required=True)	
	parser.add_argument("-m", "--method", type=str, help="Analysis method identifier (folder name of a template in methods/).", required=True)
	parser.add_argument("-o", "--outputfilename", default='analysis_result.csv', help='output filename for a .csv with results. Absolute path or relative to -d.')
	parser.add_argument("-D", "--debug", action='store_true', default=False, help='turns on debugging output and exception reporting.')
	parser.add_argument("-p", "--plotfile", required=False, help="specify a plot file associated with the setup that is not gnuplot_template.plt but contained the setup folder.")
	parser.add_argument("--noplot", required=False, help="Do not create plots.")
	
	args = parser.parse_args()
	
	
def process_files(start_dir):
	analysis = evaluate_waveform.analysisProcessor(args)
	
	# prepare output file: create absolute path, initialize file with header row.
	# Joining in path.join() continues from the last absolute path argument,
	# so if args.output is relative, it gets resolved w.r.t. args.directory .
	outp = os.path.join(os.path.abspath(args.directory), args.outputfilename)
	if os.path.exists(outp):
		os.remove(outp) 
		print('deleted %s' % outp)
		
	analysis.store_header(outp)
	
	# iterate over all suitable files in start_dir. 
	# Recursively process subdirectories if required.
	for f in sorted(os.listdir(start_dir)):
		f = os.path.join(start_dir, f)
		if os.path.exists(f):
			if analysis.process_file(f):
				analysis.store_results(outp)
			analysis.clean_up()
		if os.path.isdir(f) and args.recursive:
			process_files(f)
	
	
if __name__ == "__main__":
	init_argparse()
	# load evaluate_waveform from subdirectory: methods/<args.method>/evaluate_waveform.py
	evaluate_waveform = importlib.import_module('methods.%s.evaluate_waveform' % args.method)
	process_files(args.directory)
	