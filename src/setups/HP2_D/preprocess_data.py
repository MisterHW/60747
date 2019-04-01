

def assign_basic_analysis_parameters_m2():
	global par 
	### basic file information
	par['file_ext'] = '.txt'
	par['ndatacols'] = 4
	par['skipped_header_rows'] = 4
	par['R_shunt'] = 0.00984
	par['CH_VGE'] = 0 # Channel 1 : LS gate-emitter voltage (optional)
	par['CH_VDC'] = 1 # Channel 2 : DC link voltage 
	par['CH_VD']  = 2 # Channel 3 : diode voltage
	par['CH_ID']  = 3 # Channel 4 : sensed current (shunt voltage * 100 A/V)




	
def assign_advanced_analysis_parameters_m2():
	print("parameters:")		
	global hdr, par

	# scope channel mapping
	par['TS_VGE'] = float(hdr['dt Cha.1 [Sek]']) # sampling time step 
	par['TS_VDC'] = float(hdr['dt Cha.2 [Sek]'])
	par['TS_VD']  = float(hdr['dt Cha.3 [Sek]'])
	par['TS_ID']  = float(hdr['dt Cha.4 [Sek]'])
	# nominal gate driver timing
	par['t_1st_duration'] =  float(hdr['pre-charge [mS]']) * 1E-3
	par['t_inter_pulse_duration'] = float(hdr['pause [mS]']) * 1E-3
	par['t_2nd_duration'] =  float(hdr['puls [mS]' ]) * 1E-3
	assert par['t_1st_duration'] > 0, "\nduration needs to be positive, typically > 0.5E-6"
	assert par['t_inter_pulse_duration'] > 0, "\nduration needs to be positive, typically > 50E-6"
	assert par['t_2nd_duration'] > 0, "\nduration needs to be positive, typically > 5E-6"
	t_trigger = 0
	par['t_1st_rise_nom'] = t_trigger - par['t_inter_pulse_duration'] - par['t_1st_duration'] 
	par['t_1st_fall_nom'] = t_trigger - par['t_inter_pulse_duration']
	par['t_2nd_rise_nom'] = t_trigger # coincident with trigger (not accounting for propagation delay in the LWL and gate driver circuitry)
	par['t_2nd_fall_nom'] = t_trigger + par['t_2nd_duration']
	# switching event regions
	par['tAOI_turn_off_bounds'] = [par['t_1st_fall_nom'] - 0, par['t_1st_fall_nom'] + par['t_inter_pulse_duration'] * 0.9]
	par['tAOI_turn_off_bounds_begin'] = par['tAOI_turn_off_bounds'][0]
	par['tAOI_turn_off_bounds_end']   = par['tAOI_turn_off_bounds'][1]
	par['tAOI_turn_on_bounds']  = [par['t_2nd_rise_nom'] - 0.5E-6, par['t_2nd_rise_nom'] + par['t_2nd_duration'] * 0.9]
	par['tAOI_turn_on_bounds_begin'] = par['tAOI_turn_on_bounds'][0]
	par['tAOI_turn_on_bounds_end']   = par['tAOI_turn_on_bounds'][1]
	# slow variation AOIs
	par['tAOI_D_FWD'] = [par['t_1st_fall_nom'] + 5E-6, par['t_2nd_rise_nom'] - 2E-6] # AOI for linear forward current and constant diode forward voltage esimtation
	assert par['tAOI_D_FWD'][1] > par['tAOI_D_FWD'][0], "invalid tAOI_D_FWD interval. t_inter_pulse_duration too small or error in t_1st_fall_nom or t_2nd_rise_nom definitions."

	assert par['t_2nd_duration'] > 2E-6, "t_2nd_duration is too short for selected tAOI_1st_fr_event and tAOI_rr_event AOIs. Please re-evaluate switching waveforms and adjust minimum AOI size accordingly."
	par['tAOI_1st_fr_event'] = [par['t_1st_fall_nom'] - 0, par['t_1st_fall_nom'] + min(2E-6, par['t_2nd_duration'])]
	par['tAOI_rr_event'] = [par['t_2nd_rise_nom'] - 0, par['t_2nd_rise_nom'] + min(2E-6, par['t_2nd_duration'])]
	
	# transient event AOIs
	