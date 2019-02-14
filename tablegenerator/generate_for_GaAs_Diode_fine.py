#!python3

import numpy as np
import dptablegen

# range(), np.arange(), np.linspace increment from 0 to n-1
# the erange extends the range functions by one that includes 
# endpoint and accepts step size.
erange = lambda start, stop, step: np.arange(start,stop+step,step) 

### input parameters

p =  {} # parameters dictionary

p['L'] = 4.7E-6  # H 
p['C'] = 0.75E-6 # F
p['R'] = 0.05 + 0.02 # Ohm (50mOhm Rds(on) + 20mOhm shunt resistance)

p['currents']     = erange( 1,50,2)
p['voltages']     = erange(50,350,50)
p['temperatures'] = [25.9, 84.8,99.5]
p['protection_voltage'] = 10000

# [high, low] gate driver isolation converter input voltages
# these voltages have been determined empirically to result in 
# [10,10], [15,15] and [18,15] V for the high and low voltage levels, respectively
p['gatesupply_voltages'] = [[19.8, 17.2]] 

p['fn'] = "GaAs_D_table_I%.2g-%.2gA_V%.2g_%.2gV_T%.2g-%.2gdegC_fine.csv" % (
	min(p['currents']), max(p['currents']),
	min(p['voltages']), max(p['voltages']),
	min(p['temperatures']), max(p['temperatures'])
)


if __name__ == "__main__":
	dptablegen.generate_table(p)
	