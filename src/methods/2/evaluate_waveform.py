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
			'{Temp.};{V_DC_1st_on_av};{I_rr_fwd_max};{I_rr_rev_max};{V_D_1st_on_av};' + \
			'{t_rr};{Q_rr};{E_rr_J};{dI_rr_dt_falling_edge};{RRSF_tbta};{RRSF_dIdt};'
		if self.data.args.plotfile is not None:
			plotfile = self.data.args.plotfile
		self.plotfile_template = same_path_as_script('../../setups/%s/%s' % (self.data.args.setup, plotfile))

	
	def extract_voltage_and_current_values(self):
		d = self.data
		
		print("\tvoltage and current levels")
		
		# extract basic waveform voltages and currents
		
		# treat first forward recovery as optional: tAOI_1st_fr_event may lie outside waveform bounds
		if d.CH[d.par['CH_ID']].overlaps(d.par['tAOI_1st_fr_event']): 
			d.res['I_1st_fr_peak'] = d.CH[d.par['CH_ID']].percentile_value(d.par['tAOI_1st_fr_event'], 0.99)
		if d.CH[d.par['CH_VD']].overlaps(d.par['tAOI_1st_fr_event']):
			d.res['V_D_1st_fr_peak'] = d.CH[d.par['CH_VD']].percentile_value(d.par['tAOI_1st_fr_event'], 0.99)	
		
		# treat reverse recover as mandatory
		d.res['V_D_1st_on_av'] = d.CH[d.par['CH_VD']].average(d.par['tAOI_D_FWD'])[0]
		d.res['V_DC_1st_on_av'] = d.CH[d.par['CH_VDC']].average(d.par['tAOI_D_FWD'])[0]
		d.res['I_rr_fwd_max'] = d.CH[d.par['CH_ID']].percentile_value(d.par['tAOI_rr_event'], 0.98)
		d.res['I_rr_rev_max'] = d.CH[d.par['CH_ID']].percentile_value(d.par['tAOI_rr_event'], 0.001)	
		
		d.res['I_1st_on_fit_a_bx']  = d.CH[d.par['CH_ID']].lin_fit(d.par['tAOI_D_FWD'])
		I1 = lambda t, a=d.res['I_1st_on_fit_a_bx'][0], b=d.res['I_1st_on_fit_a_bx'][1] : [t, a + b*t]
		d.res['I_1st_fr_peak_lin_estimate'] = I1(d.par['t_1st_fall_nom'])[1]
		d.res['I_rr_fwd_lin_estimate'] = I1(d.par['t_2nd_rise_nom'])[1]
				
			
	def extract_rr_timing_markers(self):
		d = self.data
		
		d.res['t_rr_50pc_FM_falling'] = d.CH[d.par['CH_ID']].find_level_crossing(
			tAOI  = d.par['tAOI_rr_event'],
			level = 0.5 * d.res['I_rr_fwd_max'],
			edge  = 'falling',
			t_edge = 5E-9
			)[0]
		d.res['t_rr_0'] = d.CH[d.par['CH_ID']].find_level_crossing(
			tAOI  = d.par['tAOI_rr_event'],
			level = 0,
			edge  = 'falling',
			t_edge = 5E-9
			)[0]
		d.res['t_rr_50pc_RM_falling'] = d.CH[d.par['CH_ID']].find_level_crossing(
			tAOI  = d.par['tAOI_rr_event'],
			level = 0.5 * d.res['I_rr_rev_max'],
			edge  = 'falling',
			t_edge = 5E-9
			)[0]
		
		reverse_max_y_range = [1.0 * d.res['I_rr_rev_max'], 0.9 * d.res['I_rr_rev_max']]
		points_around_rm = d.CH[d.par['CH_ID']].sorted_samples_in_rect(d.par['tAOI_rr_event'], reverse_max_y_range)
		d.res['t_rr_RM'] = np.average(points_around_rm[:,0])

		
		d.res['t_rr_90pc_RM_rising'] = d.CH[d.par['CH_ID']].find_level_crossing(
			tAOI  = [d.res['t_rr_RM'], d.par['tAOI_rr_event'][1]],
			level = 0.9 * d.res['I_rr_rev_max'],
			edge  = 'rising',
			)[0]
			
		d.res['t_rr_50pc_RM_rising'] = d.CH[d.par['CH_ID']].find_level_crossing(
			tAOI  = [d.res['t_rr_RM'], d.par['tAOI_rr_event'][1]],
			level = 0.5 * d.res['I_rr_rev_max'],
			edge  = 'rising',
			)[0]
			
		d.res['t_rr_25pc_RM_rising'] = d.CH[d.par['CH_ID']].find_level_crossing(
			tAOI  = [d.res['t_rr_RM'], d.par['tAOI_rr_event'][1]],
			level = 0.25 * d.res['I_rr_rev_max'],
			edge  = 'rising',
			)[0]
			
		assert d.res['t_rr_90pc_RM_rising'] < d.res['t_rr_25pc_RM_rising'], "Error: t_rr_90pc_RM_rising >= t_rr_25pc_RM_rising."
		dirrf_dt = (0.9-0.25)*d.res['I_rr_rev_max'] / (d.res['t_rr_90pc_RM_rising'] - d.res['t_rr_25pc_RM_rising'])
		d.res['rr_rising_edge_nom_90_25'] = [
			0.9 * d.res['I_rr_rev_max'] - d.res['t_rr_90pc_RM_rising'] * dirrf_dt, 
			dirrf_dt]
		inv_rr_rising_edge_nom_90_25 = \
			lambda I, \
			a = d.res['rr_rising_edge_nom_90_25'][0], \
			b = d.res['rr_rising_edge_nom_90_25'][1] \
			: [(I - a) / b, I]
			
		d.res['t_rr_1_90_25'] = inv_rr_rising_edge_nom_90_25(0.0)[0]
				
		
	def calculate_rr_characteristics(self):
		d = self.data
		fwddecl = {key:np.nan for key in [
			'rr_falling_edge', 
			'rr_rising_edge_90_25',
			'rr_rising_edge_90_50',
			'rr_rising_edge_50_25',
			'rr_rising_edge_ratio_1',
			'RRSF',
			't_rr_0_lin',
			't_rr_1_lin_90_25',
			't_rr_1_lin_90_50',
			't_rr_1_lin_50_25',
			't_rr_int_end',
			'Q_rr',
			]}
		
		# falling-edge transition fit from 50% I_FM to 50% I_RM points
		# the value t_rr_0_lin is the intersection with I = 0 and should be compatible with t_rr_0
		# which will be tested
		rr_falling_edge = d.CH[d.par['CH_ID']].lin_fit(
			[d.res['t_rr_50pc_FM_falling'], d.res['t_rr_50pc_RM_falling']] )
		rr_falling_edge_neg = d.CH[d.par['CH_ID']].lin_fit(
			[d.res['t_rr_0'], d.res['t_rr_50pc_RM_falling']] )
		reconstruct_t_rr_50pc_FM_falling = False
		if rr_falling_edge[0] == None:
			print("Error: rr_falling_edge fit failed.")
			d.err.update(fwddecl)
			return
		else:
			d.res['rr_falling_edge'] = rr_falling_edge
			fwddecl.pop('rr_falling_edge')
			
			if rr_falling_edge_neg[0] == None:
				print("\tWarning: rr_falling_edge_neg edge fit failed - cannot verify rr_falling_edge against rr_falling_edge_neg.")
			else:
				if not 0.9 < (rr_falling_edge[1]/rr_falling_edge_neg[1]) < 1.1:
					print("\tWarning: rr_falling_edge instability - reverting from [t(0.5I_FM);t(0.5I_RM)] to [t0;t(0.5I_RM)].")
					reconstruct_t_rr_50pc_FM_falling = True
					d.res['rr_falling_edge']  = rr_falling_edge_neg
			
		d.res['dI_rr_dt_falling_edge'] = d.res['rr_falling_edge'][1]
		I_rr_falling_edge   = lambda t, a=d.res['rr_falling_edge'][0], b=d.res['rr_falling_edge'][1] : [t, a + b*t]
		inv_rr_falling_edge = lambda I, a=d.res['rr_falling_edge'][0], b=d.res['rr_falling_edge'][1] : [(I - a) / b, I]
		t_rr_0_lin = inv_rr_falling_edge(0.0)[0]
		if reconstruct_t_rr_50pc_FM_falling:
			t_rr_50pc_FM_falling_new = inv_rr_falling_edge(0.5 * d.res['I_rr_fwd_max'])[0]
			print("\tInfo: changing t_rr_50pc_FM_falling from %g to %g." % (d.res['t_rr_50pc_FM_falling'], t_rr_50pc_FM_falling_new))
			d.res['t_rr_50pc_FM_falling'] = t_rr_50pc_FM_falling_new
		
		if not (d.par['tAOI_rr_event'][0] < t_rr_0_lin < d.res['t_rr_RM']):
			print("Error: t_rr_0_lin did not evaluate to a value within [tAOI_rr_event;t_rr_RM]")
			d.err.update(fwddecl)
			return
		else:
			d.res['t_rr_0_lin'] = t_rr_0_lin
			fwddecl.pop('t_rr_0_lin')		
		
		# linear fit on the rising edge after I_RM 
		# key points are with 90% I_RM and 25% I_RM intersections 
		# note the linear fit curves will not necessarily be equivalent to a line through the two points
		d.res['rr_rising_edge_90_25'] = d.CH[d.par['CH_ID']].lin_fit(
			[d.res['t_rr_90pc_RM_rising'], d.res['t_rr_25pc_RM_rising']] )
		I_rr_rising_edge_90_25   = lambda t, a=d.res['rr_rising_edge_90_25'][0], b=d.res['rr_rising_edge_90_25'][1] : [t, a + b*t]
		inv_rr_rising_edge_90_25 = lambda I, a=d.res['rr_rising_edge_90_25'][0], b=d.res['rr_rising_edge_90_25'][1] : [(I - a) / b, I]
		d.res['t_rr_1_lin_90_25'] = inv_rr_rising_edge_90_25(0.0)[0]	
			
		d.res['t_rr'] = d.res['t_rr_1_lin_90_25'] - d.res['t_rr_0']
		d.res['t_rr_int_end'] = d.res['t_rr_0'] + 5 * d.res['t_rr']
		d.res['Q_rr'] = -d.CH[d.par['CH_ID']].integral([d.res['t_rr_0'], d.res['t_rr_int_end']])[0]
		
		turnoff_prod = wfa.arithmetic_operation(
			WFA_list = [d.CH[d.par['CH_VD']], d.CH[d.par['CH_ID']]], 
			tAOI = [d.res['t_rr_0'], d.res['t_rr_int_end']], 
			func = lambda vals : vals[0] * vals[1],
			generate_time_coords = True )
		d.res['E_rr_J'] = -np.trapz(turnoff_prod[1], turnoff_prod[0]) 

		
		# paritioned fits on the rising edge after I_RM - line 1
		# these are used to quantify the bend in the recovery curve (rr_rising_edge_ratio_1)
		# key points are with 90% I_RM and 50% I_RM intersections  
		d.res['rr_rising_edge_90_50'] = d.CH[d.par['CH_ID']].lin_fit(
			[d.res['t_rr_90pc_RM_rising'], d.res['t_rr_50pc_RM_rising']] )
		I_rr_rising_edge_90_50   = lambda t, a=d.res['rr_rising_edge_90_50'][0], b=d.res['rr_rising_edge_90_50'][1] : [t, a + b*t]
		inv_rr_rising_edge_90_50 = lambda I, a=d.res['rr_rising_edge_90_50'][0], b=d.res['rr_rising_edge_90_50'][1] : [(I - a) / b, I]
		d.res['t_rr_1_lin_90_50'] = inv_rr_rising_edge_90_50(0.0)[0]
		
		# paritioned fits on the rising edge after I_RM - line 2
		# key points are with 50% I_RM and 25% I_RM intersections  
		d.res['rr_rising_edge_50_25'] = d.CH[d.par['CH_ID']].lin_fit(
			[d.res['t_rr_50pc_RM_rising'], d.res['t_rr_25pc_RM_rising']] )
		I_rr_rising_edge_50_25   = lambda t, a=d.res['rr_rising_edge_50_25'][0], b=d.res['rr_rising_edge_50_25'][1] : [t, a + b*t]
		inv_rr_rising_edge_50_25 = lambda I, a=d.res['rr_rising_edge_50_25'][0], b=d.res['rr_rising_edge_50_25'][1] : [(I - a) / b, I]
		d.res['t_rr_1_lin_50_25'] = inv_rr_rising_edge_50_25(0.0)[0]
		
		
		d.res['RRSF_dIdt'] = -d.res['rr_falling_edge'][1] / d.res['rr_rising_edge_90_50'][1] # dIrr/dt / dIrf/dt
		d.res['RRSF_tbta'] = (d.res['t_rr_1_lin_90_50'] - d.res['t_rr_RM']) / (d.res['t_rr_RM'] - d.res['t_rr_0_lin']) # trrf / trrr			
		d.res['rr_rising_edge_ratio_1'] = d.res['rr_rising_edge_50_25'][1] / d.res['rr_rising_edge_90_50'][1] 

		
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
		line = self.resolve_placeholders(self.output_table_line_template, purge_unresolved = True) + '\n'
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
			s = re.sub(placeholder_pattern, 'nan',s)
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
		
		headerlines = 22 # TODO: auto-detect / verify headerlines
		self.data.par['header_rows'] = headerlines
		
		if waveform_import.read_file_header_and_data(filename, self.data):
			try: 
				preprocess_data.assign_advanced_analysis_parameters(self.data)
				preprocess_data.prepare_data(self.data)
				print("analysis:")
				self.extract_voltage_and_current_values()
			except AssertionError as e:
				self.print_assertion_error(e)
				return result
			except Exception as e:
				print("\nError: %s\n" % str(e))
				print("\nDebug info:")
				self.print_params_and_results()
				if self.data.args.debug: 
					raise e
				return result
			
			result = True
			
			try: 
				self.extract_rr_timing_markers()
				self.calculate_rr_characteristics()
			except AssertionError as e:
				result = False
				self.print_assertion_error(e)
			except Exception as e:
				result = False
				print("\nError: %s\n" % str(e))
				print("\nDebug info:")
				self.print_params_and_results()
				if self.data.args.debug: 
					raise e
				
			self.data.res['success'] = int(len(self.data.err) == 0) # 1: success, 0: errors occured.
			if self.data.args.noplot is None:
				self.visualize_output(purge_unresolved_placeholders = True)
			
		print("")
		return result
		
		
	def process_file(self, filename):
		global waveform_import, preprocess_data
		# load evaluate_waveform from subdirectory: formats/<args.inputformat>/waveform_import.py
		waveform_import   = importlib.import_module('formats.%s.waveform_import' % self.data.args.inputformat)
		# load evaluate_waveform from subdirectory: setups/<args.setup>/preprocess_data.py
		preprocess_data   = importlib.import_module('setups.%s.preprocess_data'  % self.data.args.setup)
		
		print("processing:\n\t'%s'" % filename)
		
		preprocess_data.assign_basic_analysis_parameters(self.data)
		
		result = self.__process_file(filename)
			
		print("")
		return result
		
		
	def clean_up(self):
		self.data.clean_up()

		
