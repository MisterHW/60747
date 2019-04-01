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
	
	
def extract_voltage_and_current_values_m2():
	global CH, par, res
	
	print("\tvoltage and current levels")
	# extract basic waveform voltages and currents

	res['I_1st_fr_peak'] = CH[par['CH_ID']].percentile_value(par['tAOI_1st_fr_event'], 0.99)	
	res['V_D_1st_fr_peak'] = CH[par['CH_VD']].percentile_value(par['tAOI_1st_fr_event'], 0.99)	
	res['V_D_1st_on_av'] = CH[par['CH_VD']].average(par['tAOI_D_FWD'])[0]
	res['V_DC_1st_on_av'] = CH[par['CH_VDC']].average(par['tAOI_D_FWD'])[0]
	res['I_rr_fwd'] = CH[par['CH_ID']].percentile_value(par['tAOI_rr_event'], 0.995)
	res['I_rr_rev_max'] = CH[par['CH_ID']].percentile_value(par['tAOI_rr_event'], 0.001)		
	
	res['I_1st_on_fit_a_bx']  = CH[par['CH_ID']].lin_fit(par['tAOI_D_FWD'])
	I1 = lambda t, a=res['I_1st_on_fit_a_bx'][0], b=res['I_1st_on_fit_a_bx'][1] : [t, a + b*t]
	res['I_1st_fr_peak_lin_estimate'] = I1(par['t_1st_fall_nom'])
	res['I_rr_fwd_lin_estimate'] = I1(par['t_2nd_rise_nom'])
 	# TODO	
	
		
def store_header(fn, method):
	line = output_table_line_templates[method].replace('"{','"').replace('}"','"').replace('{','"').replace('}','"') + '\n'
	if fn == None:
		print(line)
	else:
		f = open(fn, 'w')
		f.write(line)
		f.close()
	return


def store_results(fn, method):
	line = resolve_placeholders(output_table_line_templates[method]) + '\n'
	if fn == None:
		print(line)
	else:
		f = open(fn, 'a')
		f.write(line)
		f.close()
	return
	
	
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
		
		
def print_assertion_error(error, full_info = False):
	print('\n\nAssertionError: ', error)
	if full_info:
		print('=============================================')
		visualize_output(purge_unresolved_placeholders = True)
		print('=============================================\n\n')			

def process_file(filename, headerlines):	
	global par, res, CH 
	result = False
	
	if read_file_header_and_data(filename):
		try: 
			assign_advanced_analysis_parameters_m2()
			CH[par['CH_ID']].invert()
			print("analysis:")
			extract_voltage_and_current_values_m2()
		except AssertionError as e:
			print_assertion_error(e)
			return result

		result = True
		
		try: 
			extract_rr_timing_markers_m2()
			calculate_rr_characteristics_m2()
		except AssertionError as e:
			result = False
			print_assertion_error(e)
			
		res['success'] = int(len(err) == 0) # 1: success, 0: errors occured.
		visualize_output_m2(purge_unresolved_placeholders = True)
		
	print("")
	return result
	
	
def store_header(fn, _args):
	return
	
	
def store_results(fn, _args):
	return
	
	
def clean_up():
	global CH, hdr, par, res, err
	for c in CH:
		del c
	CH  = []
	hdr = {} 
	par = {} 
	res = {}
	err = {}