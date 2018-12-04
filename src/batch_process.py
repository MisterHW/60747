#!python3

import argparse
import os.path
import evaluate_waveform

args = None

def extant_file(x):
    """
    'Type' for argparse - checks that file exists but does not open.
	https://stackoverflow.com/questions/11540854/file-as-command-line-argument-for-argparse-error-message-if-argument-is-not-va
    """
    if not os.path.exists(x):
        # Argparse uses the ArgumentTypeError to give a rejection message like:
        # error: argument input: x does not exist
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
	args = parser.parse_args()

	
def process_files(start_dir, recursive):
	for f in os.listdir(start_dir):
		f = os.path.join(start_dir, f)
		if os.path.exists(f):
			evaluate_waveform.process_file(f)
		if os.path.isdir(f) and recursive:
			process_files(f, recursive)
	
	
if __name__ == "__main__":
	init_argparse()
	process_files(args.directory, args.recursive)
	