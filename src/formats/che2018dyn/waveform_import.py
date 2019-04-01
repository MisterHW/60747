import numpy as np
import sys
import os
same_path_as_script = lambda filename: os.path.join(os.path.dirname(__file__), filename)
sys.path.append(same_path_as_script('../../'))
import wfa

# compatible input file version: unspecified format of Cheleiha V2 as of 20181112. 
# Header format can change. Header length depends on LabView input.
#
# Hint: Best estimator for header end symbol (currently not implemented, fixed length header_rows used instead): 
#	last occurrence of '\n\n\n' followed by the pattern of the last lines. 
#	Analyzing the end of file using file.seek(), see 
#	https://stackoverflow.com/questions/3346430/what-is-the-most-efficient-way-to-get-first-and-last-line-of-a-text-file 


# all header keywords
keys = [
'Modul', 'Schalter', 'RG',
'Durchlauf Nr.', 'V HMP 2', 'I HMP 2', 'V HMP 3', 'I HMP 3', 'V ps 1', 'I ps 1', 'Temp.', 
'delay [mS]', 'pre-charge [mS]', 'pause [mS]', 'puls [mS]', 'periode [mS]', 
'dt Cha.1 [Sek]', 'dt Cha.2 [Sek]', 'dt Cha.3 [Sek]', 'dt Cha.4 [Sek]', 
]

# header keywords to resolve timebase information
timebase_keys = [
'dt Cha.1 [Sek]', 'dt Cha.2 [Sek]', 'dt Cha.3 [Sek]', 'dt Cha.4 [Sek]'
]


def extract_header_information(filename, header_rows, skip = 0):
	tsv_list = []
	### read a subset of header lines, split them at '\t'
	f = open(filename, 'r')
	for n in range(0, header_rows):
		line = f.readline()
		if line is None: # EOF
			break 
		if n < skip: # skip line, read more
			continue
		line = line.strip() # remove leading/trailing whitespaces
		if line != '': # reject empty lines
			# indiscriminately split lines by tab characters
			raw_values = line.split('\t')
			# batch remove leading/trailing whitespaces on all items in a list
			cleaned_values = list(map(lambda s:s.strip(), raw_values)) 
			# append output
			tsv_list.append(cleaned_values)	
	f.close()
	
	### extract meta data from pairs of lines turned into lists 
	### where one list has key strings and the following list contains float values
	### note only these list pairs have matching lengths 
	
	dict = {}
	
	for col in range(0,len(tsv_list)-1):
		if len(tsv_list[col]) != len(tsv_list[col+1]):
			continue # length mismatch detected, not a valid pair of key and value lists.
		for row in range(0,len(tsv_list[col])):
			key   = tsv_list[col  ][row]
			value = tsv_list[col+1][row]
			if key in keys:
				dict[key] = value
	
	return dict


# parameters:
#	str filename: input file 
#	analysisData analysis_data: instance for parameters, receiving data
# 	read_file_header_and_data return value: success (boolean)
def read_file_header_and_data(filename, analysis_data):
	
	fn_root, fn_extension = os.path.splitext(filename)
	if fn_extension != analysis_data.par['file_ext']:
		print("\t file extension mismatch -> skipped")
		return False
	analysis_data.par['file_root'] = fn_root
	analysis_data.par['file_base'] = os.path.basename(filename)
	
	### read extended file information
	print("reading header:")
	analysis_data.hdr = extract_header_information(filename, analysis_data.par['header_rows'], analysis_data.par['skipped_header_rows'])
	
	for key in sorted(analysis_data.hdr.keys()):
		print("\t%s = %s" % (key, analysis_data.hdr[key]))
	
	### read Cheleiha V2 saved waveform file as ndarray, rejecting header rows.
	print("reading data:")
	#[comma separated floats] strtofloatconv = lambda x:float(x.replace(',','.'))
	#[comma separated floats] per_column_converters = {n:strtofloatconv for n in range(1,par['ndatacols']+1)}
	data = np.loadtxt(
		fname = filename, 
		dtype = 'float', 
		delimiter = '\t', 
		skiprows = analysis_data.par['header_rows'], 
		#[comma separated floats] converters = per_column_converters,
		unpack = True,		
		)
	print("\tinput array size = " + repr(data.shape))
	analysis_data.par['n_samples'] = data.shape[1]
	
	### process waveforms
	# create one WaveformAnazyer instance for each channel
	# assume trigger position (t=0) is at the center of the waveform 
	
	timebases = [ float(analysis_data.hdr[timebase_keys[n]]) for n in range(0,len(timebase_keys)) ]
	analysis_data.CH = [ 
		wfa.WaveformAnalyzer(
			samples_data     = data[n], 
			timebase         = timebases[n], 
			t0_samplepos     = int(len(data[n])/2),
			timebase_unitstr = 's',
			id_str           = 'Channel %d' % (n+1)
		) for n in range(0,analysis_data.par['ndatacols']) ]
		
	return True
	
	
	