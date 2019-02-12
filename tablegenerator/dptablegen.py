#!python3

import numpy as np
import math
import scipy.optimize

import logging, sys
#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

### transformation functions for output value calculation


def HMP4040_CH2_settings(values):
	v_out = values['gate_supply'][1]
	i_out = 0.5
	return [v_out, i_out]

	
def HMP4040_CH3_settings(values):
	v_out = values['gate_supply'][0]
	i_out = 0.5
	return [v_out, i_out]

	
def HMP4040_CH4_settings(values):
	v_out = 0
	i_out = 0
	return [v_out, i_out]
	
	
def udsin(t, phi, k, a, w, c): 
	# underdamped sinusoidal oscillation
	return k*math.exp(-a*t)*math.sin(w*t + phi) + c
	
	
def udsin_prime(t, phi, k, a, w, c): 
	# first time derivative of the underdamped sinusoidal oscillation as defined above
	return -a*k*math.exp(-a*t)*math.sin(w*t + phi) + w*k*math.exp(-a*t)*math.cos(w*t + phi)
	
	
def estimate_double_pulse_presets(values):
	# overvoltage and pulse duration calculation
	i_lim = 5.0 # power supply current limit
	I_pk  = values['i_pk']
	v_nom = values['v_nom'] 
	v_tol = values['v_tol']
	v_protect = values['v_protect']
	R = values['R']
	L = values['L']
	C = values['C']
			
	# RLC series circuit quantities
	alpha   = R / (2 * L)
	omega_0 = 1.0 / math.sqrt(L * C) 
	tau_0   = 2 * math.pi / omega_0
	omega_d = math.sqrt(omega_0**2 - alpha**2)
	
	# estimate initial voltage assuming 
	# E_C_initial = E_C_after_first_pulse + E_L_after_first_pulse + 0.5 * E_RLC_loss_per_period 
	# E_RLC_loss_per_period = (1-exp(-t * R/L)) * E_C_initial
	# E_C_initial = 1/(exp(-tau * R/L)) * (E_C_after_first_pulse + E_L_after_first_pulse)
	E_C_after_first_pulse = 0.5 * C * v_nom**2
	E_L_after_first_pulse = 0.5 * L * I_pk**2
	E_C_initial = (E_C_after_first_pulse + E_L_after_first_pulse) / (math.exp(-0.5 * tau_0 * R/L))
	v_set = math.sqrt(2 * E_C_initial / C) # goes to v_nom for R -> 0 , L -> 0
	
	pulse_duration_out_of_range = True
	v_turnoff = 0

	for i in range(100): # iterate to find proper voltage settings and re-calculate pulse duration accordingly
	
		# V(t) = v_nom*exp(-alpha*t)*cos(omega_d*t) 
		# I(t) = Id*exp(-alpha*t)*sin(omega_d*t) 
		# dI/dt= -alpha*Id*exp(-alpha*t)*sin(omega_d*t) + omega_d*Id*exp(-alpha*t)*cos(omega_d*t)
		# V(0) = v_nom = L*dI/dt|_(t=0) = omega_d*L*I_d
		I_d = v_set / (omega_d*L)

		# find pre-charge period based on required I_pk
		t_interval = [0,(2*math.pi)/omega_d*(1/4+1E-6)]
		if abs(I_pk / I_d) > 1:
			# logging.error("Error: I_pk / I_d > 1, %g / %g" % (I_pk, I_d))
			continue
			
		t_est = math.asin(I_pk / I_d) / omega_d # initial guess based on alpha = 0 -> I_pk / I_d = sin(omega_d*t_est) 
		t_pulse = scipy.optimize.newton(
			func   = udsin,
			x0     = t_est,
			fprime = udsin_prime,
			args   = (0, I_d, alpha, omega_d, -I_pk),
			tol    = 1E-8
			)
	
		pulse_duration_out_of_range = (t_pulse < t_interval[0]) or (t_pulse > t_interval[1])
		if pulse_duration_out_of_range:
			# I(t) does not reach I_pk during first quarter period.
			t_pulse = t_interval[1]
			v_next = v_set * 1.25
			logging.debug("pulse_duration_out_of_range")
			logging.debug("adjusting v_set %fV->%fV" % (v_set, v_next))
			v_set = v_next 
			continue 
			
		v_turnoff = udsin(t_pulse, math.pi/2, v_set, alpha, omega_d, 0)
		
		if abs(v_nom - v_turnoff) > v_tol:
			v_next = v_set + (v_nom - v_turnoff)*0.5
			logging.debug(repr(values) + ' ' + str(v_turnoff))
			logging.debug("adjusting v_set %fV->%fV" % (v_set, v_next))
			v_set = v_next
			continue
		else:
			break
		
	if abs(v_nom - v_turnoff) > v_tol:
		print("at %s, I(t_max) = %fA" % (repr(values),udsin(t_interval[1], 0, I_d, alpha, omega_d, 0)))
		print("failed to adjust v_set.")
		return None
		
	if pulse_duration_out_of_range:
		print("at %s, I(t_max) = %fA" % (repr(values),udsin(t_interval[1], 0, I_d, alpha, omega_d, 0)))
		print("error: t_pulse = %fs outside range [%fs:%fs]." % (t_pulse, t_interval[0], t_interval[1]))
		return None
	
	if v_set > v_protect:
		print("error v_set = %fV violates v_protection = %fV." % (v_set, v_protect))
		return None
	
	return [v_set, i_lim, t_pulse]

### output generation functions
	
def header_line(file):
	file.write('"HMP4040-CH2-V";"HMP4040-CH2-I";"HMP4040-CH3-V";"HMP4040-CH3-I";"HMP4040-CH4-V";"HMP4040-CH4-I";"PSI91000-V";"PSI91000-I";"DPULSE-V";"DPULSE-I";"DPULSE-PRECHG-T";"DUT-TEMP"\n')
	file.write('"V";"A";"V";"A";"V";"A";"V";"A";"V";"A";"s";"°C"\n') 
	
	
def add_line(file, values):
	ch2 = HMP4040_CH2_settings(values)
	ch3 = HMP4040_CH3_settings(values)
	ch4 = HMP4040_CH4_settings(values)
	dpp = estimate_double_pulse_presets(values)
	if dpp == None:
		print("skipping single measurement.")
		return 
	cells = np.concatenate(
		(ch2, ch3, ch4, [dpp[0], dpp[1], values['v_nom'], values['i_pk'], dpp[2], values['temp']]), 
		axis = None,
		)
	file.write(
		np.array2string(
			cells, 
			separator = ';',  # '\t'
			formatter = {'float_kind':lambda x: '%g' % x}
			).strip('[ ').strip(']').replace('\n ', '')+'\n'
		)

	
def generate_table(input_params):
	print('\r\noutput = "%s"\r\n' % input_params['fn'])
	print('I = ', input_params['currents'])
	print('V = ', input_params['voltages'])
	print('T = ', input_params['temperatures'])
	print('Vg= ', input_params['gatesupply_voltages'])
	
	f = open(input_params['fn'], 'w+')
	header_line(f)
	# set of single acquisition parameters as a dict to enable
	# iterating over more dimensions without changing function signatures
	values = {
		'v_protect':input_params['protection_voltage'],
		'v_tol':0.05, 
		'R':input_params['R'],
		'L':input_params['L'],
		'C':input_params['C'],
		}
	
	for gate_supply in input_params['gatesupply_voltages']:
		values['gate_supply'] = gate_supply
		for t in input_params['temperatures']:
			values['temp'] = t
			for v in input_params['voltages']:
				values['v_nom'] = v
				for i in input_params['currents']:
					values['i_pk'] = i
					add_line(f, values)

	f.close()

