

def assign_basic_analysis_parameters(analysis_data):
	d = analysis_data
	### basic file information
	d.par['file_ext'] = '.txt'
	d.par['ndatacols'] = 4
	d.par['skipped_header_rows'] = 4
	d.par['R_shunt'] = 0.00984
	d.par['CH_VGE'] = 0 # Channel 1 : LS gate-emitter voltage (optional)
	d.par['CH_VDC'] = 1 # Channel 2 : DC link voltage 
	d.par['CH_VD']  = 2 # Channel 3 : diode voltage
	d.par['CH_ID']  = 3 # Channel 4 : sensed current (shunt voltage * 100 A/V)




	
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
	assert d.par['t_2nd_duration'] > 2E-6, "t_2nd_duration is too short for selected tAOI_1st_fr_event and tAOI_rr_event AOIs. Please re-evaluate switching waveforms and adjust minimum AOI size accordingly."
	d.par['tAOI_1st_fr_event'] = [d.par['t_1st_fall_nom'] - 0, d.par['t_1st_fall_nom'] + min(2E-6, d.par['t_2nd_duration'])]
	d.par['tAOI_1st_fr_event_begin'] = d.par['tAOI_1st_fr_event'][0]
	d.par['tAOI_1st_fr_event_end']   = d.par['tAOI_1st_fr_event'][1]	
	d.par['tAOI_rr_event'] = [d.par['t_2nd_rise_nom'] - 0, d.par['t_2nd_rise_nom'] + min(2E-6, d.par['t_2nd_duration'])]
	d.par['tAOI_rr_event_begin'] = d.par['tAOI_rr_event'][0]
	d.par['tAOI_rr_event_end']   = d.par['tAOI_rr_event'][1]
	# transient event AOIs
	
	
def prepare_data(analysis_data):
	return
	