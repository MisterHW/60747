import sys
import os
same_path_as_script = lambda filename: os.path.join(os.path.dirname(__file__), filename)
sys.path.append(same_path_as_script('../../'))
import wfa


def assign_basic_analysis_parameters(analysis_data):
	d = analysis_data
	
	### basic file information
	d.par['file_ext'] = '.txt'
	d.par['ndatacols'] = 4
	d.par['skipped_header_rows'] = 4
	d.par['R_shunt'] = 0.009888
	d.par['CH_VGE_raw'] = 0 # Channel 1 : LS gate-emitter voltage (optional)
	d.par['CH_VGE'] = d.par['CH_VGE_raw']
	d.par['CH_VDC_raw'] = 1 # Channel 2 : DC link voltage (uncorrected)
	# d.par['CH_VDC'] see prepare_data()
	d.par['CH_VD_raw']  = 2 # Channel 3 : diode voltage
	d.par['CH_VD'] = d.par['CH_VD_raw']
	d.par['CH_ID_raw']  = 3 # Channel 4 : sensed current (shunt voltage * 100 A/V)
	d.par['CH_ID'] = d.par['CH_ID_raw']

	
def assign_advanced_analysis_parameters(analysis_data):
	d = analysis_data
	
	print("parameters:")		

	# scope channel mapping
	d.par['TS_VGE'] = float(d.hdr['dt Cha.1 [Sek]']) # sampling time step 
	d.par['TS_VDC'] = float(d.hdr['dt Cha.2 [Sek]'])
	d.par['TS_VD']  = float(d.hdr['dt Cha.3 [Sek]'])
	d.par['TS_ID']  = float(d.hdr['dt Cha.4 [Sek]'])
	# nominal gate driver timing
	d.par['t_1st_duration'] =  float(d.hdr['pre-charge [mS]']) * 1E-3
	d.par['t_inter_pulse_duration'] = float(d.hdr['pause [mS]']) * 1E-3
	d.par['t_2nd_duration'] =  float(d.hdr['puls [mS]' ]) * 1E-3
	assert d.par['t_1st_duration'] > 0, "\nduration needs to be positive, typically > 0.5E-6"
	assert d.par['t_inter_pulse_duration'] > 0, "\nduration needs to be positive, typically > 50E-6"
	assert d.par['t_2nd_duration'] > 0, "\nduration needs to be positive, typically > 5E-6"
	t_trigger = 0
	d.par['t_1st_rise_nom'] = t_trigger - d.par['t_inter_pulse_duration'] - d.par['t_1st_duration'] 
	d.par['t_1st_fall_nom'] = t_trigger - d.par['t_inter_pulse_duration']
	d.par['t_2nd_rise_nom'] = t_trigger # coincident with trigger (not accounting for propagation delay in the LWL and gate driver circuitry)
	d.par['t_2nd_fall_nom'] = t_trigger + d.par['t_2nd_duration']
	# switching event regions
	d.par['tAOI_turn_off_bounds'] = [d.par['t_1st_fall_nom'] - 0, d.par['t_1st_fall_nom'] + d.par['t_inter_pulse_duration'] * 0.9]
	d.par['tAOI_turn_off_bounds_begin'] = d.par['tAOI_turn_off_bounds'][0]
	d.par['tAOI_turn_off_bounds_end']   = d.par['tAOI_turn_off_bounds'][1]
	d.par['tAOI_turn_on_bounds']  = [d.par['t_2nd_rise_nom'] - 0.5E-6, d.par['t_2nd_rise_nom'] + d.par['t_2nd_duration'] * 0.9]
	d.par['tAOI_turn_on_bounds_begin'] = d.par['tAOI_turn_on_bounds'][0]
	d.par['tAOI_turn_on_bounds_end']   = d.par['tAOI_turn_on_bounds'][1]
	# slow variation AOIs
	d.par['tAOI_D_FWD'] = [d.par['t_1st_fall_nom'] + 5E-6, d.par['t_2nd_rise_nom'] - 2E-6] # AOI for linear forward current and constant diode forward voltage esimtation
	assert d.par['tAOI_D_FWD'][1] > d.par['tAOI_D_FWD'][0], "invalid tAOI_D_FWD interval. t_inter_pulse_duration too small or error in t_1st_fall_nom or t_2nd_rise_nom definitions."
	d.par['tAOI_D_FWD_begin'] = d.par['tAOI_D_FWD'][0]
	d.par['tAOI_D_FWD_end'] = d.par['tAOI_D_FWD'][1]
	# transient event AOIs
	assert d.par['t_2nd_duration'] > 2E-6, "t_2nd_duration is too short for selected tAOI_1st_fr_event and tAOI_rr_event AOIs. Please re-evaluate switching waveforms and adjust minimum AOI size accordingly."
	d.par['tAOI_1st_fr_event'] = [d.par['t_1st_fall_nom'] - 0, d.par['t_1st_fall_nom'] + min(2.5E-6, 0.9*d.par['t_inter_pulse_duration'])]
	d.par['tAOI_1st_fr_event_begin'] = d.par['tAOI_1st_fr_event'][0]
	d.par['tAOI_1st_fr_event_end']   = d.par['tAOI_1st_fr_event'][1]	
	d.par['tAOI_rr_event'] = [d.par['t_2nd_rise_nom'] - 0, d.par['t_2nd_rise_nom'] + min(2.5E-6, 0.9*d.par['t_2nd_duration'])]
	d.par['tAOI_rr_event_begin'] = d.par['tAOI_rr_event'][0]
	d.par['tAOI_rr_event_end']   = d.par['tAOI_rr_event'][1]

	
	
def prepare_data(analysis_data):
	d = analysis_data

	# Note: files are not overwritten, all plots have to copy the following corrections.
	
	# apply real shunt value conversion factor (scope has been set up with 10mOhm nominal shunt resistance)
	d.CH[d.par['CH_ID']].multiply_by(1/(100.0 * d.par['R_shunt']))
	
	# shunt and DC link capacitor are series connected 
	# * note: forward voltage is recorded as negative, current as positive
	# * add shunt voltage to VDC_raw

	V_DC_corrected = None
	
	if ( (d.CH[d.par['CH_VDC_raw']].timebase == d.CH[d.par['CH_ID']].timebase) and 
		(d.CH[d.par['CH_VDC_raw']].t0_samplepos == d.CH[d.par['CH_ID']].t0_samplepos) and 
		(len(d.CH[d.par['CH_VDC_raw']].s) == len(d.CH[d.par['CH_ID']].s)) ):
		# shortcut: work directly on the waveform data 
		# assuming channels have equal and aligned number of equidistant samples
		V_DC_corrected = d.CH[d.par['CH_VDC_raw']].s + d.par['R_shunt'] * d.CH[d.par['CH_ID']].s
	else:	
		# fallback: slow version with interpolation
		# create additional V_CE_corr waveform corrected for shunt dropout voltage
		shunt_dropout_correction =  lambda vals, R=d.par['R_shunt'] : vals[0] + R * vals[1]

		V_DC_corrected = wfa.arithmetic_operation(
			WFA_list = [d.CH[d.par['CH_VDC_raw']], d.CH[d.par['CH_ID']]], 
			tAOI = d.CH[d.par['CH_VDC_raw']].time_span(), 
			func = shunt_dropout_correction )[1]

	d.CH.append( wfa.WaveformAnalyzer(
		samples_data     = V_DC_corrected , 
		timebase         = d.CH[d.par['CH_VDC_raw']].timebase, 
		t0_samplepos     = d.CH[d.par['CH_VDC_raw']].t0_samplepos,
		timebase_unitstr = 's',
		id_str           = 'Channel %d (corr)' % (d.par['CH_VDC_raw']+1) ))
		
	# update channel reference
	d.par['CH_VDC'] = len(d.CH) - 1
	