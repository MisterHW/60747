reset
set term win enhanced
fn = '18-10-26 18-40-53 HP2-1-SW2-LS 350 155 .txt'

###
Rshunt      = 0.00984
headerlines = 19
t_1st_pulse = 2.21395e-05
t_delay     = 7.5e-05
t_2nd_pulse = 5e-06
t_zero      = 0

I1_a = 708.4883186922577
I1_b = 7310698.616830349
I2_a = 143.43176611687198
I2_b = 7497161.346529449
I1(t) = I1_a + I1_b*t
I2(t) = I2_a + I2_b*t

t_1st_pulse_rising  = t_zero - t_delay - t_1st_pulse
t_1st_pulse_falling = t_zero - t_delay
t_2nd_pulse_rising  = t_zero
t_2nd_pulse_falling = t_zero + t_2nd_pulse
t_3rd_period_end    = t_zero + t_2nd_pulse_falling + t_delay
###

tmp = fn.'.tmp'
set print tmp
print t_1st_pulse_rising , I1(t_1st_pulse_rising)
print t_1st_pulse_falling, I1(t_1st_pulse_falling)
print t_2nd_pulse_rising , I2(t_2nd_pulse_rising)
print t_2nd_pulse_falling, I2(t_2nd_pulse_falling)
print t_3rd_period_end, I2(t_2nd_pulse_falling) - (I1(t_1st_pulse_falling) - I2(t_2nd_pulse_rising))
unset print
set table $IEData
plot tmp
unset table 


set key box center right noautotitle
set xzeroaxis
set title "Doppelpulstest: '18-10-26 18-40-53 HP2-1-SW2-LS 350 155 .txt'" font 'Verdana,14'
set mxtics 5
set mytics 5 
set grid

decimation = 10
t_offset_us = 5e-10*400002 * 0.5 * 1E+6
set xrange [-t_offset_us:t_offset_us]

set style rect fc lt -1 fs transparent solid 0.1 noborder
set obj rect from -7.999999999999999e-05*1E+6, graph 0 to -7.4999999999999926e-06*1E+6 , graph 1
set obj rect from -5e-06*1E+6 , graph 0 to 4.5e-06*1E+6, graph 1

set xlabel 'time (µs)'
set ylabel 'voltage (V) / current (A)'
plot \
	$IEData u ($1*1E+6):2 w l t 'I_E(fit)' lc rgb 'gray' lw 2,\
	fn skip headerlines u ($0*5e-10*1E+6 * decimation - t_offset_us):(column(1+1)) every decimation w l t "V_D_C",\
	fn skip headerlines u ($0*5e-10*1E+6 * decimation - t_offset_us):(column(2+1)-Rshunt*column(3+1)) every decimation w l t "V_C_E",\
	fn skip headerlines u ($0*5e-10*1E+6 * decimation - t_offset_us):(column(0+1)) every decimation w l t "V_G_E",\
	fn skip headerlines u ($0*5e-10 *1E+6 * decimation - t_offset_us):(column(3+1)) every decimation w l t "I_E"
	
 
	 
	 