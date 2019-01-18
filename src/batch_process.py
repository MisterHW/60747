#!python3

import argparse
import os.path
import evaluate_waveform

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
	parser.add_argument("-m", "--method", type=int, help="Analysis method (2: diode reverse recovery, 9: IGBT switching characteristics.", required=True)
	parser.add_argument("-r", "--recursive", action='store_true', default=False, help='recursively process subdirectories.')
	parser.add_argument("-o", "--output", default='analysis_result.csv', help='output filename for a .csv with results. Absolute path or relative to -d.')
	parser.add_argument("-l", "--headerlines", type=int, help='number of header lines to be processed separately (and skipped to jump to the data).', required=True)
	args = parser.parse_args()
	
	
def process_files(start_dir, recursive):
	# prepare output file: create absolute path, initialize file with header row.
	# Joining in path.join() continues from from the last absolute path argument,
	# so if args.output is relative, it gets resolved w.r.t. args.directory .
	outp = os.path.join(os.path.abspath(args.directory), args.output)
	if os.path.exists(outp):
		os.remove(outp) 
		print('deleted %s' % outp)
	evaluate_waveform.store_header(outp)
	
	# iterate over all suitable files in directory. 
	# Recursively process subdirectories if required.
	for f in sorted(os.listdir(start_dir)):
		f = os.path.join(start_dir, f)
		if os.path.exists(f):
			if evaluate_waveform.process_file(f, args.headerlines, args.method):
				evaluate_waveform.store_results(outp)
			evaluate_waveform.clean_up()
		if os.path.isdir(f) and recursive:
			process_files(f, recursive)
	
	
if __name__ == "__main__":
	init_argparse()
	process_files(args.directory, args.recursive)
	