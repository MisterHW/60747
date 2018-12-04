#!python3

import numpy as np
import math
import scipy.optimize

# range(), np.arange(), np.linspace increment from 0 to n-1
# the erange extends the range functions by one that includes 
# endpoint and accepts step size.
erange = lambda start, stop, step: np.arange(start,stop+step,step) 

### input parameters

L = 50E-6    # H 
C = 11000E-6 # F
R = 0.016 + 0.01 # Ohm (8V drop at 500A plus 10mOhm shunt resistance)

currents     = erange(5, 600, 5)
voltages     = erange(50,350,50)
temperatures = [20] # erange(20,100,20)

fn = "table_I%.2g-%.2gA_V%.2g_%.2gV_T%.2g-%.2gdegC.csv" % (
	min(currents), max(currents),
	min(voltages), max(voltages),
	min(temperatures), max(temperatures)
)

### transformation functions for output value calculation

def HMP4040_CH2_settings(values):
	v_out = 15
	i_out = 0.05
	return [v_out, i_out]

	
def HMP4040_CH3_settings(values):
	v_out = 15
	i_out = 0.05
	return [v_out, i_out]

	
def HMP4040_CH4_settings(values):
	v_out = 0
	i_out = 0
	return [v_out, i_out]
	
	
def udsin(t, phi, k, a, w, c):
	return k*math.exp(-a*t)*math.sin(w*t + phi) + c
	
	
def udsin_prime(t, phi, k, a, w, c):
	return -a*k*math.exp(-a*t)*math.sin(w*t + phi) + w*k*math.exp(-a*t)*math.cos(w*t + phi)
	
	
def estimate_double_pulse_presets(values):
	# overvoltage and pulse duration calculation
	i_lim = 5.0 # power supply current limit
	I_pk  = values['i_pk']
	v_nom = values['v_nom'] 
	v_set = v_nom
	v_tol = values['v_tol']
	v_protect = values['v_protect']
	
	pulse_duration_out_of_range = True
	v_turnoff = 0
	
	for i in range(100): # iterate to find proper voltage settings and re-calculate pulse duration accordingly
	
		# RLC series circuit
		alpha   = R / (2 * L)
		omega_0 = 1.0 / math.sqrt(L * C) 
		omega_d = math.sqrt(omega_0**2 - alpha**2)
		# V(t) = v_nom*exp(-alpha*t)*cos(omega_d*t) 
		# I(t) = Id*exp(-alpha*t)*sin(omega_d*t) 
		# dI/dt= -alpha*Id*exp(-alpha*t)*sin(omega_d*t) + omega_d*Id*exp(-alpha*t)*cos(omega_d*t)
		# V(0) = v_nom = L*dI/dt|_(t=0) = omega_d*L*I_d
		I_d = v_set / (omega_d*L)

		# find pre-charge period based on required I_pk
		t_interval = [0,(2*math.pi)/omega_d*(1/4+1E-6)]
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
			# print("pulse_duration_out_of_range")
			# print("adjusting v_set %fV->%fV" % (v_set, v_next))
			v_set = v_next 
			continue 
			
		v_turnoff = udsin(t_pulse, math.pi/2, v_set, alpha, omega_d, 0)
		
		
		if abs(v_nom - v_turnoff) > v_tol:
			v_next = v_set + (v_nom - v_turnoff)*0.5
			# print(repr(values), v_turnoff)
			# print("adjusting v_set %fV->%fV" % (v_set, v_next))
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
	file.write('#HMP4040-CH2-V\tHMP4040-CH2-I\tHMP4040-CH3-V\tHMP4040-CH3-I\tHMP4040-CH4-V\tHMP4040-CH4-I\tPSI91000-V\tPSI91000-I\tDPULSE-V\tDPULSE-I\tDPULSE-PRECHG-T\tDUT-TEMP\n')
	file.write('#V\tA\tV\tA\tV\tA\tV\tA\tV\tA\ts\t°C\n')   

	
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
			separator = '\t',  
			formatter = {'float_kind':lambda x: '%g' % x}
			).strip('[ ').strip(']')+'\n'
		)

	
if __name__ == "__main__":
	print('\r\noutput = "%s"\r\n' % fn)
	print('I = ', currents)
	print('V = ', voltages)
	print('T = ', temperatures)
	f = open(fn, 'w+')
	header_line(f)
	# set of single acquisition parameters as a dict to enable
	# iterating over more dimensions without changing function signatures
	values = {'v_protect':375, 'v_tol':0.05} 
	for t in temperatures:
		values['temp'] = t
		for v in voltages:
			values['v_nom'] = v
			for i in currents:
				values['i_pk'] = i
				add_line(f, values)

	f.close()

