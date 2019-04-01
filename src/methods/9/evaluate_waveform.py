#!python3

import os
import sys 
import numpy as np
import wfa
import re

# output table format
output_table_line_template = \
	'{success};{Modul};{Schalter};{R_shunt};"{file_base}";' + \
	'{V_CE_turnoff};{V_DC};{Ipk_turnoff};{Temp.};{RG};{V_GE_high};{V_GE_low};' + \
	'{turn_off_t1};{turn_off_t2};{turn_off_t3};{turn_off_t4};{turn_on_t1};{turn_on_t2};{turn_on_t3};{turn_on_t4};' + \
	'{E_turnoff_J};{E_turnon_J};{turn_off_t3};{turn_off_t4};' + \
	'{I_droop_during_pause};'
	
	
same_path_as_script = lambda filename: os.path.join(os.path.dirname(__file__), filename)
plotfile_template = same_path_as_script('gnuplot_template.plt')	

CH = []

# higher-level analysis description paramters and results in dictionary form
hdr = {} # header data (dict)
par = {} # analysis parameters (dict)
res = {} # results (dict)
err = {} # errors / quantities that failed to evaluate (contains defaults or NaN)



def extract_voltage_and_current_values_m9():
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
	res['V_CE_turnoff'] = CH[par['CH_VCE_corr']].average(par['tAOI_V_CE'])[0]


		

		
def extract_turnoff_timing_markers_m9():
	global CH, par, res, err
	
	### extract waveform timing according to IEC60747-9 definitions
	
	# turn-off marker 1: V_GE = 0.9 * V_GE_high falling
	t_off_t1 = CH[par['CH_VGE']].find_level_crossing(
		tAOI  = par['tAOI_turn_off_bounds'],
		level = 0.9 * res['V_GE_high'],
		edge  = 'falling',
		t_edge= 20E-9 )	
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
		t_edge= 10E-9 )	
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
		t_edge= 20E-9 )	
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
		t_edge= 200E-9 )
	if t_off_t4[0] == None: 
		print('Error: failed to evaluate turn_off_t4 marker in range %s' % repr(par['tAOI_turn_off_bounds']))
		err['turn_off_t4'] = np.nan
		err['turn_off_t4_slope'] = np.nan
	else:

		res['turn_off_t4'] = t_off_t4[0]
		res['turn_off_t4_slope'] = t_off_t4[1]
		
	# if successful, specify integration interval
	if 'turn_off_t1' in res and 'turn_off_t4' in res:
		res['tAOI_1st_losses'] = [res['turn_off_t1'], res['turn_off_t4']] 
	else:
		err['tAOI_1st_losses'] = [np.nan, np.nan]
		
		
def extract_turnon_timing_markers_m9():
	global CH, par, res, err		
		
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
	
	# if successful, specify integration interval	
	if 'turn_on_t1' in res and 'turn_on_t4' in res:		
		res['tAOI_2nd_losses'] = [res['turn_on_t1'] , res['turn_on_t4']] 
	else:
		err['tAOI_2nd_losses'] = [np.nan, np.nan]

	
def calculate_turnoff_characteristics_m9():
	### determine switching times, energies according to IEC60747-9 definitions
	global res, err	
	print("\tturn-off switching characteristics")
	
	multiply = lambda vals : vals[0] * vals[1]
	if ('tAOI_1st_losses' in res):
		assert res['tAOI_1st_losses'][0] < res['tAOI_1st_losses'][1], "tAOI_1st_losses: violation of requirement turn_off_t1 < turn_off_t4."
		# turn-off energy
		turnoff_prod = wfa.arithmetic_operation(
			WFA_list = [CH[par['CH_VCE']], CH[par['CH_IE']]], 
			tAOI = res['tAOI_1st_losses'], 
			func = multiply,
			generate_time_coords = True )
		res['E_turnoff_J'] = np.trapz(turnoff_prod[1], turnoff_prod[0]) 
	else:
		err['E_turnoff_J'] = np.nan
		
		
def calculate_turnon_characteristics_m9():
	global res, err
	print("\tturn-on switching characteristics")
	
	multiply = lambda vals : vals[0] * vals[1]
	if ('tAOI_2nd_losses' in res):
		assert res['tAOI_2nd_losses'][0] < res['tAOI_2nd_losses'][1], "tAOI_2nd_losses: violation of requirement turn_on_t1 < turn_on_t4."
		# turn-on energy 
		turnon_prod = wfa.arithmetic_operation(
			WFA_list = [CH[par['CH_VCE']], CH[par['CH_IE']]], 
			tAOI = res['tAOI_2nd_losses'], 
			func = multiply,
			generate_time_coords = True )
		res['E_turnon_J'] = np.trapz(turnon_prod[1], turnon_prod[0])
	else:
		err['E_turnon_J'] = np.nan
		
		
def print_assertion_error(error, full_info = False):
	print('\n\nAssertionError: ', error)
	if full_info:
		print('=============================================')
		visualize_output(purge_unresolved_placeholders = True)
		print('=============================================\n\n')	

	
def __process_file(filename, headerlines):
	global par, res
	result = False
	
	if read_file_header_and_data(filename):
		try: 
			assign_advanced_analysis_parameters_m9()
			create_corrected_VCE_channel()
			print("analysis:")
			extract_voltage_and_current_values_m9()
		except AssertionError as e:
			print_assertion_error(e)
			return result

		result = True
		
		try: 
			extract_turnoff_timing_markers_m9()
			calculate_turnoff_characteristics_m9()	
		except AssertionError as e:
			result = False
			print_assertion_error(e)
			
		try: 				
			extract_turnon_timing_markers_m9()
			calculate_turnon_characteristics_m9()	
		except AssertionError as e:
			result = False
			print_assertion_error(e)
			
		res['success'] = int(len(err) == 0) # 1: success, 0: errors occured.
		visualize_output_m9(purge_unresolved_placeholders = True)
		
	print("")
	return result
	
	
def process_file(filename, headerlines, method):
	global par, res
	
	print("processing:\n\t'%s'" % filename)
	
	assign_basic_analysis_parameters() # TODO: import module, then call
	
	par['header_rows'] = headerlines

	result = __process_file(filename, headerlines)
		
	print("")
	return result
	
	
def store_header(fn, method):
	line = output_table_line_template.replace('"{','"').replace('}"','"').replace('{','"').replace('}','"') + '\n'
	if fn == None:
		print(line)
	else:
		f = open(fn, 'w')
		f.write(line)
		f.close()
	return


def store_results(fn, method):
	line = resolve_placeholders(output_table_line_template) + '\n'
	if fn == None:
		print(line)
	else:
		f = open(fn, 'a')
		f.write(line)
		f.close()
	return
	
	
	
def resolve_placeholders(s, purge_unresolved = False):
	for key in hdr.keys():
		s = s.replace('{%s}'%key, str(hdr[key]))
	for key in par.keys():
		s = s.replace('{%s}'%key, str(par[key]))
	for key in res.keys():
		s = s.replace('{%s}'%key, str(res[key]))
	for key in err.keys():
		s = s.replace('{%s}'%key, str(err[key]))	
	if purge_unresolved:
		placeholder_pattern = r'\{[^\}\/\\]*\}' # match "{text}" pattern except when text contains \ (gnuplot multiline) or / (gnuplot {/:bold ....} )
		s = re.sub(placeholder_pattern, '(nan)',s)
	return s
		
	
def print_params_and_results():
	print("parameters:")
	for key in sorted(par.keys()):
		print("\t%s = %s" % (key, repr(par[key])))	
		
	print("results:")
	for key in sorted(res.keys()):
		print("\t%s = %s" % (key, repr(res[key])))
		
	if len(err) > 0:
		print("failed to evaluate:")
		for key in sorted(err.keys()):
			print("\t%s = %s" % (key, repr(err[key])))
			
	
def __visualize_output(plotfile_template, purge_unresolved_placeholders = False):
	### generate output and gnuplot file for documentation

	print_params_and_results()
		
	par['insertion_before_plot'] = ''
	par['insertion_after_plot']  = ''
	
	if len(err) > 0:
		par['insertion_before_plot'] += 'set label 10000 "{/:Bold FAILED: %s}" font "Verdana,16" tc rgb "red" at graph 0.5, graph 0.5 center front\n' % (", ".join(err.keys()).replace('_', '\\\_'))
	
	# generate gnuplot script for visualization and validation
	f = open(plotfile_template, 'r', encoding='cp1252')
	plt = f.readlines()
	f.close()
	plt_output_filename = par['file_root'] + '.plt'
	f = open(plt_output_filename, 'w+')
	for line in plt: # replace all placeholders in the template file (same names as the dictionary keys) 
		f.write(resolve_placeholders(line, purge_unresolved_placeholders))
	f.close()
	
	
def visualize_output( purge_unresolved_placeholders = False):
	__visualize_output(plotfile_template, purge_unresolved_placeholders)
	

	
def clean_up():
	global CH, hdr, par, res, err
	for c in CH:
		del c
	CH  = []
	hdr = {} 
	par = {} 
	res = {}
	err = {}