#!python3

import os
import sys 
import numpy as np
import re

same_path_as_script = lambda filename: os.path.join(os.path.dirname(__file__), filename)
sys.path.append(same_path_as_script('../../'))
import wfa

import importlib
# import later: waveform_import
# import later: preprocess_data
	

class analysisData:
	def __init__(self):
		self.args = None
		self.CH = []
		# higher-level analysis description paramters and results in dictionary form
		self.hdr = {} # header data (dict)
		self.par = {} # analysis parameters (dict)
		self.res = {} # results (dict)
		self.err = {} # errors / quantities that failed to evaluate (contains defaults or NaN)

	def clean_up(self):
		for c in self.CH:
			del c
		self.CH  = []
		self.hdr = {} 
		self.par = {} 
		self.res = {}
		self.err = {}	
		

class analysisProcessor:
	
	def __init__(self, args):
		self.data = analysisData()
		self.data.args = args
		self.output_table_line_template = \
			'{success};{Modul};{Schalter};{R_shunt};"{file_base}";' + \
			'{V_CE_turnoff};{V_DC};{Ipk_turnoff};{Temp.};{RG};{V_GE_high};{V_GE_low};' + \
			'{turn_off_t1};{turn_off_t2};{turn_off_t3};{turn_off_t4};{turn_on_t1};{turn_on_t2};{turn_on_t3};{turn_on_t4};' + \
			'{E_turnoff_J};{E_turnon_J};{turn_off_t3};{turn_off_t4};' + \
			'{I_droop_during_pause};'	
		self.plotfile_template = same_path_as_script('../../setups/%s/gnuplot_template.plt' % args.setup)
		
	
	def extract_voltage_and_current_values(self):
		d = self.data 
		
		print("\tvoltage and current levels")
		# extract basic waveform voltages and currents 
	
		d.res['V_GE_low']  = d.CH[d.par['CH_VGE']].average(d.par['tAOI_V_GE_low'])[0]
		d.res['V_GE_high'] = d.CH[d.par['CH_VGE']].percentile_value(d.par['tAOI_V_GE_high'], 0.99)
		d.res['V_DC'] = d.CH[d.par['CH_VDC']].percentile_value(d.par['tAOI_V_DC'], 0.5) # median
		d.res['Ipk_turnoff'] = d.CH[d.par['CH_IE']].percentile_value(d.par['tAOI_Ipk_1st_fall'], 0.99)
		d.res['Ipk_turnon']  = d.CH[d.par['CH_IE']].percentile_value(d.par['tAOI_Ipk_2nd_rise'], 0.995)
		
		d.res['I_1st_fit_a_bx'] = d.CH[d.par['CH_IE']].lin_fit(d.par['tAOI_I_1st_fit'])
		d.res['I_1st_fit_a'] = d.res['I_1st_fit_a_bx'][0]
		d.res['I_1st_fit_b'] = d.res['I_1st_fit_a_bx'][1]
		I1 = lambda t, a=d.res['I_1st_fit_a_bx'][0], b=d.res['I_1st_fit_a_bx'][1] : [t, a + b*t]
		d.res['I_1st_fall_estimate'] = I1(d.par['t_1st_fall_nom'])
		
		d.res['I_2nd_fit_a_bx']  = d.CH[d.par['CH_IE']].lin_fit(d.par['tAOI_I_2nd_fit'])
		d.res['I_2nd_fit_a'] = d.res['I_2nd_fit_a_bx'][0]
		d.res['I_2nd_fit_b'] = d.res['I_2nd_fit_a_bx'][1]
		I2 = lambda t, a=d.res['I_2nd_fit_a_bx'][0], b=d.res['I_2nd_fit_a_bx'][1] : [t, a + b*t]		
		d.res['I_2nd_rise_estimate'] = I2(d.par['t_2nd_rise_nom'])
		
		d.res['I_droop_during_pause'] = d.res['I_1st_fall_estimate'][1] - d.res['I_2nd_rise_estimate'][1]
		
		# current-compensated V_CE at turn-off
		#shunt_dropout_correction =  lambda vals, R=d.par['R_shunt'] : vals[0] - R * vals[1]
		#V_CE_corrected = wfa.arithmetic_operation(
		#	WFA_list = [CH[par['CH_VCE']], CH[par['CH_IE']]], 
		#	tAOI = d.par['tAOI_V_CE'], 
		#	func = shunt_dropout_correction )
		#res['V_CE_turnoff'] = np.average(V_CE_corrected[1])
			
		# new implementation employing CH_VCE_corr
		d.res['V_CE_turnoff'] = d.CH[d.par['CH_VCE_corr']].average(d.par['tAOI_V_CE'])[0]
		
		
	def extract_turnoff_timing_markers(self):
		d = self.data 
	
		### extract waveform timing according to IEC60747-9 definitions
		
		# turn-off marker 1: V_GE = 0.9 * V_GE_high falling
		t_off_t1 = d.CH[d.par['CH_VGE']].find_level_crossing(
			tAOI  = d.par['tAOI_turn_off_bounds'],
			level = 0.9 * d.res['V_GE_high'],
			edge  = 'falling',
			t_edge= 20E-9 )	
		if t_off_t1[0] == None: 
			print('Error: failed to evaluate turn_off_t1 marker in range %s' % repr(d.par['tAOI_turn_off_bounds']))
			d.err['turn_off_t1'] = np.nan
			d.err['turn_off_t1_slope'] = np.nan
		else:
			d.res['turn_off_t1'] = t_off_t1[0]
			d.res['turn_off_t1_slope'] = t_off_t1[1]
			
		# turn-off marker 2: I_C  = 0.9 * Ipk_turnoff falling
		t_off_t2 = d.CH[d.par['CH_IE']].find_level_crossing(
			tAOI  = d.par['tAOI_turn_off_bounds'],
			level = 0.9 * d.res['Ipk_turnoff'],
			edge  = 'falling',
			t_edge= 10E-9 )	
		if t_off_t2[0] == None: 
			print('Error: failed to evaluate turn_off_t2 marker in range %s' % repr(d.par['tAOI_turn_off_bounds']))
			d.err['turn_off_t2'] = np.nan
			d.err['turn_off_t2_slope'] = np.nan
		else:
			d.res['turn_off_t2'] = t_off_t2[0]
			d.res['turn_off_t2_slope'] = t_off_t2[1]
			
		# turn-off marker 3: I_C  = 0.1 * Ipk_turnoff falling
		t_off_t3 = d.CH[d.par['CH_IE']].find_level_crossing(
			tAOI  = d.par['tAOI_turn_off_bounds'],
			level = 0.1 * d.res['Ipk_turnoff'],
			edge  = 'falling',
			t_edge= 20E-9 )	
		if t_off_t3[0] == None: 
			print('Error: failed to evaluate turn_off_t3 marker in range %s' % repr(d.par['tAOI_turn_off_bounds']))
			d.err['turn_off_t3'] = np.nan
			d.err['turn_off_t3_slope'] = np.nan
		else:
			d.res['turn_off_t3'] = t_off_t3[0]
			d.res['turn_off_t3_slope'] = t_off_t3[1]
			
		# turn-off marker 4: I_C  = 0.02 * Ipk_turnoff falling
		t_off_t4 = d.CH[d.par['CH_IE']].find_level_crossing(
			tAOI  = d.par['tAOI_turn_off_bounds'],
			level = 0.02 * d.res['Ipk_turnoff'],
			edge  = 'falling',
			t_edge= 200E-9 )
		if t_off_t4[0] == None: 
			print('Error: failed to evaluate turn_off_t4 marker in range %s' % repr(d.par['tAOI_turn_off_bounds']))
			d.err['turn_off_t4'] = np.nan
			d.err['turn_off_t4_slope'] = np.nan
		else:

			d.res['turn_off_t4'] = t_off_t4[0]
			d.res['turn_off_t4_slope'] = t_off_t4[1]
			
		# if successful, specify integration interval
		if 'turn_off_t1' in d.res and 'turn_off_t4' in d.res:
			d.res['tAOI_1st_losses'] = [d.res['turn_off_t1'], d.res['turn_off_t4']] 
		else:
			d.err['tAOI_1st_losses'] = [np.nan, np.nan]
		
			
	def extract_turnon_timing_markers(self):		
		d = self.data 
	
		# turn-on marker 1: V_GE = 0.1 * V_GE_high rising
		t_on_t1 = d.CH[d.par['CH_VGE']].find_level_crossing(
			tAOI  = d.par['tAOI_turn_on_bounds'],
			level = 0.1 * d.res['V_GE_high'],
			edge  = 'rising',
			t_edge= 6E-9 )	
		if t_on_t1[0] == None: 
			print('Error: failed to evaluate turn_on_t1 marker in range %s' % repr(d.par['tAOI_turn_on_bounds']))
			d.err['turn_on_t1'] = np.nan
			d.err['turn_on_t1_slope'] = np.nan
		else:
			d.res['turn_on_t1'] = t_on_t1[0]
			d.res['turn_on_t1_slope'] = t_on_t1[1]
			
		# turn-on marker 2: I_C  = 0.1 * Ipk_turnoff rising
		t_on_t2 = d.CH[d.par['CH_IE']].find_level_crossing(
			tAOI  = d.par['tAOI_turn_on_bounds'],
			level = 0.1 * d.res['Ipk_turnoff'],
			edge  = 'rising',
			t_edge= 6E-9 )	
		if t_on_t2[0] == None: 
			print('Error: failed to evaluate turn_on_t2 marker in range %s' % repr(d.par['tAOI_turn_on_bounds']))
			d.err['turn_on_t2'] = np.nan
			d.err['turn_on_t2_slope'] = np.nan
		else:
			d.res['turn_on_t2'] = t_on_t2[0]
			d.res['turn_on_t2_slope'] = t_on_t2[1]
			
		# turn-on marker 3: I_C  = 0.9 * Ipk_turnoff rising
		t_on_t3 = d.CH[d.par['CH_IE']].find_level_crossing(
			tAOI  = d.par['tAOI_turn_on_bounds'],
			level = 0.9 * d.res['Ipk_turnoff'],
			edge  = 'rising',
			t_edge= 6E-9 )	
		if t_on_t3[0] == None: 
			print('Error: failed to evaluate turn_on_t3 marker in range %s' % repr(d.par['tAOI_turn_on_bounds']))
			d.err['turn_on_t3'] = np.nan
			d.err['turn_on_t3_slope'] = np.nan
		else:
			d.res['turn_on_t3'] = t_on_t3[0]
			d.res['turn_on_t3_slope'] = t_on_t3[1]
			
		# turn-on marker 4: V_CE_corr = 0.02 * V_DC
		t_on_t4 = d.CH[d.par['CH_VCE_corr']].find_level_crossing(
			tAOI  = d.par['tAOI_turn_on_bounds'],
			level = 0.02 * d.res['V_DC'],
			edge  = 'falling',
			t_edge= 6E-9 )	
		if t_on_t4[0] == None: 
			print('Error: failed to evaluate turn_on_t4 marker in range %s' % repr(d.par['tAOI_turn_on_bounds']))
			d.err['turn_on_t4'] = np.nan
			d.err['turn_on_t4_slope'] = np.nan	
		else:
			d.res['turn_on_t4'] = t_on_t4[0]
			d.res['turn_on_t4_slope'] = t_on_t4[1]	
		
		# if successful, specify integration interval	
		if 'turn_on_t1' in d.res and 'turn_on_t4' in d.res:		
			d.res['tAOI_2nd_losses'] = [d.res['turn_on_t1'] , d.res['turn_on_t4']] 
		else:
			d.err['tAOI_2nd_losses'] = [np.nan, np.nan]

		
	def calculate_turnoff_characteristics(self):
		d = self.data 
		
		### determine switching times, energies according to IEC60747-9 definitions
		print("\tturn-off switching characteristics")
		
		multiply = lambda vals : vals[0] * vals[1]
		if ('tAOI_1st_losses' in d.res):
			assert d.res['tAOI_1st_losses'][0] < d.res['tAOI_1st_losses'][1], "tAOI_1st_losses: violation of requirement turn_off_t1 < turn_off_t4."
			# turn-off energy
			turnoff_prod = wfa.arithmetic_operation(
				WFA_list = [d.CH[d.par['CH_VCE']], d.CH[d.par['CH_IE']]], 
				tAOI = d.res['tAOI_1st_losses'], 
				func = multiply,
				generate_time_coords = True )
			d.res['E_turnoff_J'] = np.trapz(turnoff_prod[1], turnoff_prod[0]) 
		else:
			d.err['E_turnoff_J'] = np.nan
			
			
	def calculate_turnon_characteristics(self):
		d = self.data 
		
		print("\tturn-on switching characteristics")
		
		multiply = lambda vals : vals[0] * vals[1]
		if ('tAOI_2nd_losses' in d.res):
			assert d.res['tAOI_2nd_losses'][0] < d.res['tAOI_2nd_losses'][1], "tAOI_2nd_losses: violation of requirement turn_on_t1 < turn_on_t4."
			# turn-on energy 
			turnon_prod = wfa.arithmetic_operation(
				WFA_list = [d.CH[d.par['CH_VCE']], d.CH[d.par['CH_IE']]], 
				tAOI = d.res['tAOI_2nd_losses'], 
				func = multiply,
				generate_time_coords = True )
			d.res['E_turnon_J'] = np.trapz(turnon_prod[1], turnon_prod[0])
		else:
			d.err['E_turnon_J'] = np.nan
			
			
	def print_assertion_error(self, error, full_info = False):
		print('\n\nAssertionError: ', error)
		if full_info:
			print('=============================================')
			visualize_output(purge_unresolved_placeholders = True)
			print('=============================================\n\n')	

			
		
	def store_header(self, fn):
		line = self.output_table_line_template.replace('"{','"').replace('}"','"').replace('{','"').replace('}','"') + '\n'
		if fn == None:
			print(line)
		else:
			f = open(fn, 'w')
			f.write(line)
			f.close()
		return


	def store_results(self, fn):
		line = self.resolve_placeholders(self.output_table_line_template) + '\n'
		if fn == None:
			print(line)
		else:
			f = open(fn, 'a')
			f.write(line)
			f.close()
		return
		
		
	def resolve_placeholders(self, s, purge_unresolved = False):
		d = self.data 
		
		for key in d.hdr.keys():
			s = s.replace('{%s}'%key, str(d.hdr[key]))
		for key in d.par.keys():
			s = s.replace('{%s}'%key, str(d.par[key]))
		for key in d.res.keys():
			s = s.replace('{%s}'%key, str(d.res[key]))
		for key in d.err.keys():
			s = s.replace('{%s}'%key, str(d.err[key]))	
		if purge_unresolved:
			placeholder_pattern = r'\{[^\}\/\\]*\}' # match "{text}" pattern except when text contains \ (gnuplot multiline) or / (gnuplot {/:bold ....} )
			s = re.sub(placeholder_pattern, '(nan)',s)
		return s
			
		
	def print_params_and_results(self):
		d = self.data 
	
		print("parameters:")
		for key in sorted(d.par.keys()):
			print("\t%s = %s" % (key, repr(d.par[key])))	
			
		print("results:")
		for key in sorted(d.res.keys()):
			print("\t%s = %s" % (key, repr(d.res[key])))
			
		if len(d.err) > 0:
			print("failed to evaluate:")
			for key in sorted(d.err.keys()):
				print("\t%s = %s" % (key, repr(d.err[key])))
			
		

	def visualize_output(self, purge_unresolved_placeholders = False):
		d = self.data 
	
		### generate output and gnuplot file for documentation
		
		self.print_params_and_results()
			
		d.par['insertion_before_plot'] = ''
		d.par['insertion_after_plot']  = ''
		
		if len(d.err) > 0:
			d.par['insertion_before_plot'] += 'set label 10000 "{/:Bold FAILED: %s}" font "Verdana,16" tc rgb "red" at graph 0.5, graph 0.5 center front\n' % (", ".join(d.err.keys()).replace('_', '\\\_'))
		
		# generate gnuplot script for visualization and validation
		f = open(self.plotfile_template, 'r', encoding='cp1252')
		plt = f.readlines()
		f.close()
		plt_output_filename = d.par['file_root'] + '.plt'
		f = open(plt_output_filename, 'w+')
		for line in plt: # replace all placeholders in the template file (same names as the dictionary keys) 
			f.write(self.resolve_placeholders(line, purge_unresolved_placeholders))
		f.close()
	
		
	def __process_file(self, filename):
	
		result = False
		
		if waveform_import.read_file_header_and_data(filename, self.data):
			try: 
				preprocess_data.assign_advanced_analysis_parameters(self.data)
				preprocess_data.prepare_data(self.data)
				print("analysis:")
				self.extract_voltage_and_current_values()
			except AssertionError as e:
				self.print_assertion_error(e)
				return result

			result = True
			
			try: 
				self.extract_turnoff_timing_markers()
				self.calculate_turnoff_characteristics()	
			except AssertionError as e:
				result = False
				self.print_assertion_error(e)
				
			try: 				
				self.extract_turnon_timing_markers()
				self.calculate_turnon_characteristics()	
			except AssertionError as e:
				result = False
				self.print_assertion_error(e)
				
			self.data.res['success'] = int(len(self.data.err) == 0) # 1: success, 0: errors occured.
			self.visualize_output(purge_unresolved_placeholders = True)
			
		print("")
		return result
		
		
	def process_file(self, filename):
		global waveform_import, preprocess_data
		waveform_import   = importlib.import_module('formats.%s.waveform_import' % self.data.args.inputformat)
		preprocess_data   = importlib.import_module('setups.%s.preprocess_data'  % self.data.args.setup)
		
		print("processing:\n\t'%s'" % filename)
		
		preprocess_data.assign_basic_analysis_parameters(self.data)
		
		headerlines = 22
		self.data.par['header_rows'] = headerlines

		result = self.__process_file(filename)
			
		print("")
		return result
		
		
	def clean_up(self):
		self.data.clean_up()

		
