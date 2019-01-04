#!python3

# double-pulse test waveform evaluation according to IEC 60747-9:2007.
# compatible input file version: unspecified format of Cheleiha V2 as of 20181112. 
# Header format can change. Header length depends on LabView input.
#
# Hint: Best estimator for header end symbol (currently not implemented, fixed length header_rows used instead): 
#	last occurrence of '\n\n\n' followed by the pattern of the last lines. 
#	Analyzing the end of file using file.seek(), see 
#	https://stackoverflow.com/questions/3346430/what-is-the-most-efficient-way-to-get-first-and-last-line-of-a-text-file 


import os.path
import sys 
import numpy as np
import wfa


##################################################
#	Analysis Configuration
##################################################

# all header keywords
keys = [
'Durchlauf Nr.', 'V HMP 2', 'I HMP 2', 'V HMP 3', 'I HMP 3', 'V ps 1', 'I ps 1', 'Temp.', 
'delay [mS]', 'pre-charge [mS]', 'pause [mS]', 'puls [mS]', 'periode [mS]', 
'dt Cha.1 [Sek]', 'dt Cha.2 [Sek]', 'dt Cha.3 [Sek]', 'dt Cha.4 [Sek]', 
]

# header keywords to resolve timebase information
timebase_keys = [
'dt Cha.1 [Sek]', 'dt Cha.2 [Sek]', 'dt Cha.3 [Sek]', 'dt Cha.4 [Sek]'
]


CH = []
same_path_as_script = lambda filename: os.path.join(os.path.dirname(__file__), filename)
# higher-level analysis description paramters and results in dictionary form
hdr = {} # header data (dict)
par = {} # analysis parameters (dict)
res = {} # results (dict)
err = {} # errors / quantities that failed to evaluate (contains defaults or NaN)
plotfile_template = same_path_as_script('gnuplot_template.plt')




def assign_basic_analysis_parameters():
	global par 
	### basic file information
	par['file_ext'] = '.txt'
	par['ndatacols'] = 4
	par['skipped_header_rows'] = 4
	par['R_shunt'] = 0.00984

	
def assign_advanced_analysis_parameters():
	print("parameters:")		
	global hdr, par
	# scope channel mapping
	par['CH_VGE'] = 0 # Channel 1 : gate-emitter voltage
	par['TS_VGE'] = float(hdr['dt Cha.1 [Sek]']) # sampling time step 
	par['CH_VDC'] = 1 # Channel 2 : DC link voltage 
	par['TS_VDC'] = float(hdr['dt Cha.2 [Sek]'])
	par['CH_VCE'] = 2 # Channel 3 : collector-shunt voltage (collector-emitter voltage + shunt and contact resistance dropout)
	par['TS_VCE'] = float(hdr['dt Cha.3 [Sek]'])
	par['CH_IE']  = 3 # Channel 4 : sensed current (shunt voltage * 100 A/V)
	par['TS_IE']  = float(hdr['dt Cha.4 [Sek]'])
	# nominal gate driver timing
	par['t_1st_duration'] =  float(hdr['pre-charge [mS]'])*1E-3
	par['t_inter_pulse_duration']   = float(hdr['pause [mS]'])*1E-3
	par['t_2nd_duration'] =  float(hdr['puls [mS]' ])*1E-3
	par['t_1st_rise_nom'] = -par['t_inter_pulse_duration'] -par['t_1st_duration'] 
	par['t_1st_fall_nom'] = -par['t_inter_pulse_duration']
	par['t_2nd_rise_nom'] = 0 # coincident with trigger (not accounting for propagation delay in the LWL and gate driver circuitry)
	par['t_2nd_fall_nom'] = par['t_2nd_duration']
	# switching event regions
	par['tAOI_turn_off_bounds'] = [par['t_1st_fall_nom'] - 0, par['t_1st_fall_nom'] + par['t_inter_pulse_duration'] * 0.9]
	par['tAOI_turn_off_bounds_start'] = par['tAOI_turn_off_bounds'][0]
	par['tAOI_turn_off_bounds_end']   = par['tAOI_turn_off_bounds'][1]
	par['tAOI_turn_on_bounds']  = [par['t_2nd_rise_nom'] - 0.5E-6, par['t_2nd_rise_nom'] + par['t_2nd_duration'] * 0.9]
	par['tAOI_turn_on_bounds_start'] = par['tAOI_turn_on_bounds'][0]
	par['tAOI_turn_on_bounds_end']   = par['tAOI_turn_on_bounds'][1]
	# analysis areas of interest (unit: seconds)
	par['tAOI_V_GE_low']  = [par['t_2nd_rise_nom']-22E-6, par['t_2nd_rise_nom']- 2E-6] # AOI for off-state gate voltage estimation
	par['tAOI_V_GE_high'] = [par['t_1st_fall_nom']- 2E-6, par['t_1st_fall_nom']- 0.5E-6] # AOI for on-state gate voltage estimation
	par['tAOI_V_DC'] = [par['t_1st_fall_nom'] + 5E-6, par['t_2nd_rise_nom'] - 2E-6] # AOI for DC link voltage estimation after first pulse
	par['tAOI_V_CE'] = [par['t_1st_fall_nom'] - 2E-6, par['t_1st_fall_nom'] - 0E-6] # AOI for CE saturation voltage estimation close to peak current (not compensated for drop across shunt)
	par['tAOI_Ipk_1st_fall'] = [par['t_1st_fall_nom']-0.5E-6,par['t_1st_fall_nom']+5E-6] # AOI for peak turn-off current detection
	par['tAOI_Ipk_2nd_rise'] = [par['t_2nd_rise_nom']+0,par['t_2nd_rise_nom']+2E-6] # AOI for peak turn-on current detection
	par['tAOI_I_1st_fit'] = [
		par['t_1st_fall_nom'] - max(min(10E-6, 0.8*par['t_1st_duration']), 0.5E-6),
		par['t_1st_fall_nom'] - 0] # AOI for first pulse current rise (fit near end)
	par['tAOI_I_2nd_fit'] = [
		par['t_2nd_rise_nom'] + 1.5E-6,
		par['t_2nd_rise_nom'] + max(min(10E-6, 0.8*par['t_2nd_duration']), 2.5E-6)] # AOI for second pulse current rise (fit near beginning)

##################################################
	
	

def extract_header_information(filename, header_rows, skip = 0):
	tsv_list = []
	### read a subset of header lines, split them at '\t'
	f = open(filename, 'r')
	for n in range(0,header_rows):
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

	
def read_file_header_and_data(filename):
	global CH, hdr, par
	
	fn_root, fn_extension = os.path.splitext(filename)
	if fn_extension != par['file_ext']:
		print("\t file extension mismatch -> skipped")
		return False
	par['file_root'] = fn_root
	par['file_base'] = os.path.basename(filename)
	
	### read extended file information
	print("reading header:")
	hdr = extract_header_information(filename, par['header_rows'], par['skipped_header_rows'])
	
	for key in hdr.keys():
		print("\t%s : %s" % (key, hdr[key]))
	
	### read Cheleiha V2 saved waveform file as ndarray, rejecting header rows.
	print("reading data:")
	#[comma separated floats] strtofloatconv = lambda x:float(x.replace(',','.'))
	#[comma separated floats] per_column_converters = {n:strtofloatconv for n in range(1,par['ndatacols']+1)}
	data = np.loadtxt(
		fname = filename, 
		dtype = 'float', 
		delimiter = '\t', 
		skiprows = par['header_rows'], 
		#[comma separated floats] converters = per_column_converters,
		unpack = True,		
		)
	print("\tinput array size = " + repr(data.shape))
	par['n_samples'] = data.shape[1]
	
	### process waveforms
	# create one WaveformAnazyer instance for each channel
	# assume trigger position (t=0) is at the center of the waveform 
	
	timebases = [ float(hdr[timebase_keys[n]]) for n in range(0,len(timebase_keys)) ]
	CH = [ 
		wfa.WaveformAnalyzer(
			samples_data     = data[n], 
			timebase         = timebases[n], 
			t0_samplepos     = int(len(data[n])/2),
			timebase_unitstr = 's',
			id_str           = 'Channel %d' % (n+1)
		) for n in range(0,par['ndatacols']) ]
		
	return True
		
		
def create_corrected_VCE_channel():
	global CH, par
	# create additional V_CE_corr waveform corrected for shunt dropout voltage
	
	shunt_dropout_correction =  lambda vals, R=par['R_shunt'] : vals[0] - R * vals[1]
		
	V_CE_corrected = None
	
	if ( (CH[par['CH_VCE']].timebase == CH[par['CH_IE']].timebase) and 
		(CH[par['CH_IE']].t0_samplepos == CH[par['CH_IE']].t0_samplepos) and 
		(len(CH[par['CH_VCE']].s) == len(CH[par['CH_IE']].s)) ):
		# shortcut: work directly on the waveform data 
		# assuming channels have equal and aligned number of equidistant samples
		V_CE_corrected = CH[par['CH_VCE']].s - par['R_shunt'] * CH[par['CH_IE']].s
	else:	
		# fallback: slow version with interpolation
		V_CE_corrected = wfa.arithmetic_operation(
			WFA_list = [CH[par['CH_VCE']], CH[par['CH_IE']]], 
			tAOI = CH[par['CH_VCE']].time_span(), 
			func = shunt_dropout_correction )[1]

	CH.append( wfa.WaveformAnalyzer(
		samples_data     = V_CE_corrected , 
		timebase         = CH[par['CH_VCE']].timebase, 
		t0_samplepos     = CH[par['CH_VCE']].t0_samplepos,
		timebase_unitstr = 's',
		id_str           = 'Channel %d (corr)' % (par['CH_VCE']+1) ))
		
	par['CH_VCE_corr'] = len(CH) - 1
	
	
def extract_voltage_and_current_values():
	global CH, par, res
	
	print("\tvoltage and current levels")
	# extract basic waveform voltages and currents 
	
	res['V_GE_low']  = CH[par['CH_VGE']].average(par['tAOI_V_GE_low'])[0]
	res['V_GE_high'] = CH[par['CH_VGE']].percentile_value(par['tAOI_V_GE_high'], 0.99)
	res['V_DC']	= CH[par['CH_VDC']].percentile_value(par['tAOI_V_DC'], 0.5) # median
	res['Ipk_turnoff'] = CH[par['CH_IE']].percentile_value(par['tAOI_Ipk_1st_fall'], 0.99)
	res['Ipk_turnon']  = CH[par['CH_IE']].percentile_value(par['tAOI_Ipk_2nd_rise'], 0.995)
	
	res['I_1st_fit_a_bx']  = CH[par['CH_IE']].lin_fit(par['tAOI_I_1st_fit'])
	res['I_1st_fit_a'] = res['I_1st_fit_a_bx'][0]
	res['I_1st_fit_b'] = res['I_1st_fit_a_bx'][1]
	I1 = lambda t, a=res['I_1st_fit_a_bx'][0], b=res['I_1st_fit_a_bx'][1] : [t, a + b*t]
	res['I_1st_fall_estimate'] = I1(par['t_1st_fall_nom'])
	
	res['I_2nd_fit_a_bx']  = CH[par['CH_IE']].lin_fit(par['tAOI_I_2nd_fit'])
	res['I_2nd_fit_a'] = res['I_2nd_fit_a_bx'][0]
	res['I_2nd_fit_b'] = res['I_2nd_fit_a_bx'][1]
	I2 = lambda t, a=res['I_2nd_fit_a_bx'][0], b=res['I_2nd_fit_a_bx'][1] : [t, a + b*t]		
	res['I_2nd_rise_estimate'] = I2(par['t_2nd_rise_nom'])
	
	res['I_droop_during_pause'] = res['I_1st_fall_estimate'][1] - res['I_2nd_rise_estimate'][1]
	
	# current-compensated V_CE at turn-off
	#shunt_dropout_correction =  lambda vals, R=par['R_shunt'] : vals[0] - R * vals[1]
	#V_CE_corrected = wfa.arithmetic_operation(
	#	WFA_list = [CH[par['CH_VCE']], CH[par['CH_IE']]], 
	#	tAOI = par['tAOI_V_CE'], 
	#	func = shunt_dropout_correction )
	#res['V_CE_turnoff'] = np.average(V_CE_corrected[1])
		
	# new implementation employing CH_VCE_corr
	res['V_CE_turnoff'] = CH[par['CH_VCE_corr']].average(par['tAOI_V_CE'])
		
def extract_timing_markers():
	global CH, par, res, err
	
	### extract waveform timing according to IEC60747-9 definitions
	
	# turn-off marker 1: V_GE = 0.9 * V_GE_high falling
	t_off_t1 = CH[par['CH_VGE']].find_level_crossing(
		tAOI  = par['tAOI_turn_off_bounds'],
		level = 0.9 * res['V_GE_high'],
		edge  = 'falling',
		t_edge= 0 )	
	if t_off_t1[0] == None: 
		print('Error: failed to evaluate turn_off_t1 marker in range %s' % repr(par['tAOI_turn_off_bounds']))
		err['turn_off_t1'] = np.nan
		err['turn_off_t1_slope'] = np.nan
	else:
		res['turn_off_t1'] = t_off_t1[0]
		res['turn_off_t1_slope'] = t_off_t1[1]
		
	# turn-off marker 2: I_C  = 0.9 * Ipk_turnoff falling
	t_off_t2 = CH[par['CH_IE']].find_level_crossing(
		tAOI  = par['tAOI_turn_off_bounds'],
		level = 0.9 * res['Ipk_turnoff'],
		edge  = 'falling',
		t_edge= 6E-9 )	
	if t_off_t2[0] == None: 
		print('Error: failed to evaluate turn_off_t2 marker in range %s' % repr(par['tAOI_turn_off_bounds']))
		err['turn_off_t2'] = np.nan
		err['turn_off_t2_slope'] = np.nan
	else:
		res['turn_off_t2'] = t_off_t2[0]
		res['turn_off_t2_slope'] = t_off_t2[1]
		
	# turn-off marker 3: I_C  = 0.1 * Ipk_turnoff falling
	t_off_t3 = CH[par['CH_IE']].find_level_crossing(
		tAOI  = par['tAOI_turn_off_bounds'],
		level = 0.1 * res['Ipk_turnoff'],
		edge  = 'falling',
		t_edge= 6E-9 )	
	if t_off_t3[0] == None: 
		print('Error: failed to evaluate turn_off_t3 marker in range %s' % repr(par['tAOI_turn_off_bounds']))
		err['turn_off_t3'] = np.nan
		err['turn_off_t3_slope'] = np.nan
	else:
		res['turn_off_t3'] = t_off_t3[0]
		res['turn_off_t3_slope'] = t_off_t3[1]
		
	# turn-off marker 4: I_C  = 0.02 * Ipk_turnoff falling
	t_off_t4 = CH[par['CH_IE']].find_level_crossing(
		tAOI  = par['tAOI_turn_off_bounds'],
		level = 0.02 * res['Ipk_turnoff'],
		edge  = 'falling',
		t_edge= 6E-9 )	
	if t_off_t4[0] == None: 
		print('Error: failed to evaluate turn_off_t4 marker in range %s' % repr(par['tAOI_turn_off_bounds']))
		err['turn_off_t4'] = np.nan
		err['turn_off_t4_slope'] = np.nan
	else:
		res['turn_off_t4'] = t_off_t4[0]
		res['turn_off_t4_slope'] = t_off_t4[1]
		
		
	# turn-on marker 1: V_GE = 0.1 * V_GE_high rising
	t_on_t1 = CH[par['CH_VGE']].find_level_crossing(
		tAOI  = par['tAOI_turn_on_bounds'],
		level = 0.1 * res['V_GE_high'],
		edge  = 'rising',
		t_edge= 6E-9 )	
	if t_on_t1[0] == None: 
		print('Error: failed to evaluate turn_on_t1 marker in range %s' % repr(par['tAOI_turn_on_bounds']))
		err['turn_on_t1'] = np.nan
		err['turn_on_t1_slope'] = np.nan
	else:
		res['turn_on_t1'] = t_on_t1[0]
		res['turn_on_t1_slope'] = t_on_t1[1]
		
	# turn-on marker 2: I_C  = 0.1 * Ipk_turnoff rising
	t_on_t2 = CH[par['CH_IE']].find_level_crossing(
		tAOI  = par['tAOI_turn_on_bounds'],
		level = 0.1 * res['Ipk_turnoff'],
		edge  = 'rising',
		t_edge= 6E-9 )	
	if t_on_t2[0] == None: 
		print('Error: failed to evaluate turn_on_t2 marker in range %s' % repr(par['tAOI_turn_on_bounds']))
		err['turn_on_t2'] = np.nan
		err['turn_on_t2_slope'] = np.nan
	else:
		res['turn_on_t2'] = t_on_t2[0]
		res['turn_on_t2_slope'] = t_on_t2[1]
		
	# turn-on marker 3: I_C  = 0.9 * Ipk_turnoff rising
	t_on_t3 = CH[par['CH_IE']].find_level_crossing(
		tAOI  = par['tAOI_turn_on_bounds'],
		level = 0.9 * res['Ipk_turnoff'],
		edge  = 'rising',
		t_edge= 6E-9 )	
	if t_on_t3[0] == None: 
		print('Error: failed to evaluate turn_on_t3 marker in range %s' % repr(par['tAOI_turn_on_bounds']))
		err['turn_on_t3'] = np.nan
		err['turn_on_t3_slope'] = np.nan
	else:
		res['turn_on_t3'] = t_on_t3[0]
		res['turn_on_t3_slope'] = t_on_t3[1]
		
	# turn-on marker 4: V_CE_corr = 0.02 * V_DC
	t_on_t4 = CH[par['CH_VCE_corr']].find_level_crossing(
		tAOI  = par['tAOI_turn_on_bounds'],
		level = 0.02 * res['V_DC'],
		edge  = 'falling',
		t_edge= 6E-9 )	
	if t_on_t4[0] == None: 
		print('Error: failed to evaluate turn_on_t4 marker in range %s' % repr(par['tAOI_turn_on_bounds']))
		err['turn_on_t4'] = np.nan
		err['turn_on_t4_slope'] = np.nan	
	else:
		res['turn_on_t4'] = t_on_t4[0]
		res['turn_on_t4_slope'] = t_on_t4[1]	
	
	# if successful, specify AOIs
	if 'turn_off_t1' in res and 'turn_off_t4' in res:
		res['tAOI_1st_losses'] = [res['turn_off_t1'], res['turn_off_t4']] 
	else:
		err['tAOI_1st_losses'] = [np.nan, np.nan]
		
	if 'turn_on_t1' in res and 'turn_on_t4' in res:		
		res['tAOI_2nd_losses'] = [res['turn_on_t1'] , res['turn_on_t4']] 
	else:
		err['tAOI_2nd_losses'] = [np.nan, np.nan]

	
def calculate_double_pulse_test_quantities():
	### determine switching times, energies according to IEC60747-9 definitions
		
	print("\tswitching energies")
	
	multiply = lambda vals : vals[0] * vals[1]
	
	if ('tAOI_1st_losses' in res):
		# turn-off energy
		turnoff_prod = wfa.arithmetic_operation(
			WFA_list = [CH[par['CH_VCE']], CH[par['CH_IE']]], 
			tAOI = res['tAOI_1st_losses'], 
			func = multiply,
			generate_time_coords = True )
		res['E_turnoff_J'] = np.trapz(turnoff_prod[1], turnoff_prod[0]) 
	else:
		err['E_turnoff_J'] = np.nan

	if ('tAOI_2nd_losses' in res):
		# turn-on energy 
		turnon_prod = wfa.arithmetic_operation(
			WFA_list = [CH[par['CH_VCE']], CH[par['CH_IE']]], 
			tAOI = res['tAOI_2nd_losses'], 
			func = multiply,
			generate_time_coords = True )
		res['E_turnon_J'] = np.trapz(turnon_prod[1], turnon_prod[0])
	else:
		err['E_turnon_J'] = np.nan

		
def resolve_placeholders(s):
	for key in par.keys():
		s = s.replace('{%s}'%key, str(par[key]))
	for key in res.keys():
		s = s.replace('{%s}'%key, str(res[key]))
	for key in err.keys():
		s = s.replace('{%s}'%key, str(err[key]))	
	return s
		
	
def visualize_output():
	### generate output and gnuplot file for documentation

	print("parameters:")
	for key in par.keys():
		print("\t%s = %s" % (key, repr(par[key])))	
		
	print("results:")
	for key in res.keys():
		print("\t%s = %s" % (key, repr(res[key])))
		
	if len(err) > 0:
		print("failed to evaluate:")
		for key in err.keys():
			print("\t%s = %s" % (key, repr(err[key])))
		
	par['insertion_before_plot'] = ''
	par['insertion_after_plot']  = ''
	
	if len(err) > 0:
		par['insertion_before_plot'] += 'set label 10000 "{/:Bold FAILED: %s}" font "Verdana,16" tc rgb "red" at graph 0.05, graph 0.9 front\n' % (", ".join(err.keys()).replace('_', '\\\_'))
	
	# generate gnuplot script for visualization and validation
	f = open(plotfile_template, 'r', encoding='cp1252')
	plt = f.readlines()
	f.close()
	plt_output_filename = par['file_root'] + '.plt'
	f = open(plt_output_filename, 'w+')
	for line in plt: # replace all placeholders in the template file (same names as the dictionary keys) 
		f.write(resolve_placeholders(line))
	f.close()
	

def store_results():
	# generate output to file
	return
	
	
def clean_up():
	global CH, hdr, par, res
	for c in CH:
		del c
	CH  = []
	hdr = {} 
	par = {} 
	res = {}
	err = {}
	
	
def process_file(filename, headerlines):
	global par, res
	
	print("processing:\n\t'%s'" % filename)
	assign_basic_analysis_parameters()
	par['header_rows'] = headerlines
	
	if read_file_header_and_data(filename):
		assign_advanced_analysis_parameters()
		create_corrected_VCE_channel()
		
		print("analysis:")
		extract_voltage_and_current_values()
		extract_timing_markers()
		calculate_double_pulse_test_quantities()
		res['success'] = int(len(err) == 0) # 1: success, 0: errors occured.
		visualize_output()
		store_results()
		
	print("")
	# clean_up()


	
	