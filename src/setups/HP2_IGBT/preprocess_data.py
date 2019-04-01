def assign_basic_analysis_parameters_m9():
	global par 
	### basic file information
	par['file_ext'] = '.txt'
	par['ndatacols'] = 4
	par['skipped_header_rows'] = 4
	par['R_shunt'] = 0.00984
	par['CH_VGE'] = 0 # Channel 1 : gate-emitter voltage
	par['CH_VDC'] = 1 # Channel 2 : DC link voltage 
	par['CH_VCE'] = 2 # Channel 3 : collector-shunt voltage (collector-emitter voltage + shunt and contact resistance dropout)
	par['CH_IE']  = 3 # Channel 4 : sensed current (shunt voltage * 100 A/V)
	
	
def assign_advanced_analysis_parameters_m9():
	print("parameters:")		
	global hdr, par
	# scope channel mapping
	par['TS_VGE'] = float(hdr['dt Cha.1 [Sek]']) # sampling time step 
	par['TS_VDC'] = float(hdr['dt Cha.2 [Sek]'])
	par['TS_VCE'] = float(hdr['dt Cha.3 [Sek]'])
	par['TS_IE']  = float(hdr['dt Cha.4 [Sek]'])
	# nominal gate driver timing
	par['t_1st_duration'] =  float(hdr['pre-charge [mS]']) * 1E-3
	par['t_inter_pulse_duration']   = float(hdr['pause [mS]']) * 1E-3
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
	# analysis areas of interest (unit: seconds)
	assert par['t_1st_fall_nom'] < par['t_2nd_rise_nom']-22E-6, "\ntAOI_V_GE_low to be sampled within pause phase, equivalent to par['t_inter_pulse_duration'] > 22E-6"
	par['tAOI_V_GE_low']  = [par['t_2nd_rise_nom']-22E-6, par['t_2nd_rise_nom']- 2E-6] # AOI for off-state gate voltage estimation
	assert par['t_1st_rise_nom'] < par['t_1st_fall_nom']- 1.5E-6, "\ntAOI_V_GE_high to be sampled towards the end of the first pulse, equivalent to t_1st_duration > 1E-6 (pulse too short)"
	par['tAOI_V_GE_high'] = [par['t_1st_fall_nom']- 1E-6, par['t_1st_fall_nom']- 0] # AOI for on-state gate voltage estimation
	par['tAOI_V_DC'] = [par['t_1st_fall_nom'] + 5E-6, par['t_2nd_rise_nom'] - 2E-6] # AOI for DC link voltage estimation after first pulse
	assert par['tAOI_V_DC'][1] > par['tAOI_V_DC'][0], "invalid tAOI_V_DC interval. t_inter_pulse_duration too small or error in t_1st_fall_nom or t_2nd_rise_nom definitions."
	par['tAOI_V_CE'] = [par['t_1st_fall_nom'] - 2E-6, par['t_1st_fall_nom'] - 0E-6] # AOI for CE saturation voltage estimation close to peak current (not compensated for drop across shunt)
	assert  par['t_1st_fall_nom'] + 5E-6 < par['t_2nd_rise_nom'], "tAOI_Ipk_1st_fall overlaps second pulse / t_inter_pulse_duration < 5E-6."
	par['tAOI_Ipk_1st_fall'] = [par['t_1st_fall_nom'] - 0.5E-6, par['t_1st_fall_nom'] + 5E-6] # AOI for peak turn-off current detection
	assert par['t_2nd_rise_nom'] + 4E-6 < par['t_2nd_fall_nom'], "tAOI_Ipk_2nd_rise outside of second pulse / t_2nd_duration < 4E-6."
	par['tAOI_Ipk_2nd_rise'] = [par['t_2nd_rise_nom'] + 0, par['t_2nd_rise_nom'] + 4E-6] # AOI for peak turn-on current detection
	assert par['t_1st_duration'] > 0.5E-6, "tAOI_I_1st_fit requires tAOI_I_1st_fit > 0.5E-6"
	par['tAOI_I_1st_fit'] = [
		par['t_1st_fall_nom'] - max(min(10E-6, 0.8 * par['t_1st_duration']), 0.5E-6),
		par['t_1st_fall_nom'] - 0] # AOI for first pulse current rise (fit near end)
	assert par['t_2nd_rise_nom'] + 5E-6 < par['t_2nd_fall_nom'], "tAOI_I_2nd_fit exceeds beyond second pulse, t_2nd_duration > 5E-6 expected."
	par['tAOI_I_2nd_fit'] = [
		par['t_2nd_rise_nom'] + 4E-6,
		par['t_2nd_rise_nom'] + max(min(15E-6, 0.8 * par['t_2nd_duration']), 5E-6)] # AOI for second pulse current rise (fit near beginning)
		
		
		
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
	