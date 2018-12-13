reset
set term wxt enhanced persist
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
set title "Doppelpulstest: 18-10-26 18-40-53 HP2-1-SW2-LS 350 155 .txt" font 'Verdana,14'
set mxtics 5
set mytics 5 
set xtics nomirror
set x2tics font 'Verdana Bold, 12' offset 0, -0.25
set format x2 ""
set grid ytics x2tics

decimation = 2
t_offset_us = 5e-10*400002 * 0.5 * 1E+6
set xrange [-t_offset_us:t_offset_us]
set x2range [-t_offset_us:t_offset_us]

set style rect fc lt -1 fs transparent solid 0.1 noborder
set obj rect from -7.999999999999999e-05*1E+6, graph 0 to -7.4999999999999926e-06*1E+6, graph 1
set obj rect from -5e-06*1E+6 , graph 0 to 4.5e-06*1E+6, graph 1

# debug markers
set label 1 "90% V_G_E" at -7.49185e-05*1E+6, 0.9*14.869999668 point pt 1 ps 2 front rotate by 45
set label 2 "90% I_p_k" at -8e-05*1E+6, 0.9*163.599997222 point pt 1 ps 2 front rotate by 45
set label 3 "10% I_p_k" at -7.40875e-05*1E+6, 0.1*163.599997222 point pt 1 ps 2 front rotate by 45
set label 4 "2% I_p_k" at -7.3753e-05*1E+6, 0.02*163.599997222 point pt 1 ps 2 front rotate by 45
set label 5 "10% V_G_E" at 5.105e-07*1E+6, 0.1*14.869999668 point pt 1 ps 2 front rotate by 45
set label 6 "10% I_p_k" at 5.89e-07*1E+6, 0.1*163.599997222 point pt 1 ps 2 front rotate by 45
set label 7 "90% I_p_k" at 6.505000000000001e-07*1E+6, 0.9*163.599997222 point pt 1 ps 2 front rotate by 45
set label 8 "2% V_D_C" at {turn_on_t4}*1E+6, 0.02*351.400000021 point pt 1 ps 2 front rotate by 45

set xlabel 'time (µs)'
set ylabel 'voltage (V) / current (A)'
set x2tics add ("A" -7.49185e-05*1E+6)
set x2tics add ("B" -8e-05*1E+6)
set x2tics add ("C" -7.40875e-05*1E+6)
set x2tics add ("D" -7.3753e-05*1E+6)

plot \
	$IEData u ($1*1E+6):2 w l t 'I_E(fit)' lc rgb 'gray' lw 2,\
	fn skip headerlines u ($0*5e-10*1E+6 * decimation - t_offset_us):(column(1+1)) every decimation w l lw 2 t "V_D_C",\
	fn skip headerlines u ($0*5e-10*1E+6 * decimation - t_offset_us):(column(2+1)-Rshunt*column(3+1)) every decimation w l lw 2 t "V_C_E",\
	fn skip headerlines u ($0*5e-10*1E+6 * decimation - t_offset_us):(column(0+1)) every decimation w l lw 2 t "V_G_E",\
	fn skip headerlines u ($0*5e-10*1E+6 * decimation - t_offset_us):(column(3+1)) every decimation w l lw 2 t "I_E"

 
	 
	 