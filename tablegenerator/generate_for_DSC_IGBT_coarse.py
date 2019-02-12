#!python3

import numpy as np
import dptablegen

# range(), np.arange(), np.linspace increment from 0 to n-1
# the erange extends the range functions by one that includes 
# endpoint and accepts step size.
erange = lambda start, stop, step: np.arange(start,stop+step,step) 

### input parameters

p =  {} # parameters dictionary

p['L'] = 51E-6  # H 
p['C'] = 840E-6 # F
p['R'] = 0.004 + 0.00984 # Ohm (linearized voltage drop contribution to damping (2V @ 500A) + 10mOhm shunt resistance)

p['currents']     = erange( 5,605,25)
p['voltages']     = erange(50,350,50)
p['protection_voltage'] = 420
p['temperatures'] = [25.9, 65.4, 84.8]

# [high, low] gate driver isolation converter input voltages
# these voltages have been determined empirically to result in 
# [10,10], [15,15] and [18,15] V for the high and low voltage levels, respectively
p['gatesupply_voltages'] = [[17.2,17.2], [19.8, 17.2]] # note: [12.0,12.0] removed

p['fn'] = "HPDSC_IGBT_table_I%.2g-%.2gA_V%.2g_%.2gV_T%.2g-%.2gdegC_coarse.csv" % (
	min(p['currents']), max(p['currents']),
	min(p['voltages']), max(p['voltages']),
	min(p['temperatures']), max(p['temperatures'])
)


if __name__ == "__main__":
	dptablegen.generate_table(p)
	