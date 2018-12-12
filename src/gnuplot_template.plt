reset
set term wxt enhanced persist
fn = '{file_base}'

###
Rshunt      = {R_shunt}
headerlines = {header_rows}
t_1st_pulse = {t_1st_duration}
t_delay     = {t_inter_pulse_duration}
t_2nd_pulse = {t_2nd_duration}
t_zero      = 0

I1_a = {I_1st_fit_a}
I1_b = {I_1st_fit_b}
I2_a = {I_2nd_fit_a}
I2_b = {I_2nd_fit_b}
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


set key box top right noautotitle
set xzeroaxis
set title "Doppelpulstest: {file_base}" font 'Verdana,14'
set mxtics 5
set mytics 5 
set xtics nomirror
set x2tics font 'Verdana Bold, 12' offset 0, -0.25
set format x2 ""
set grid ytics x2tics

decimation = 1
t_offset_us = {TS_VDC}*{n_samples} * 0.5 * 1E+6
set xrange [-t_offset_us:t_offset_us]
set x2range [-t_offset_us:t_offset_us]

set style rect fc lt -1 fs transparent solid 0.1 noborder
set obj rect from {tAOI_turn_off_bounds_start}*1E+6, graph 0 to {tAOI_turn_off_bounds_end}*1E+6, graph 1
set obj rect from {tAOI_turn_on_bounds_start}*1E+6 , graph 0 to {tAOI_turn_on_bounds_end}*1E+6, graph 1

set xlabel 'time (µs)'
set ylabel 'voltage (V) / current (A)'
{insertion_before_plot}
plot \
	$IEData u ($1*1E+6):2 w l t 'I_E(fit)' lc rgb 'gray' lw 2,\
	fn skip headerlines u ($0*{TS_VDC}*1E+6 * decimation - t_offset_us):(column({CH_VDC}+1)) every decimation w l lw 2 t "V_D_C",\
	fn skip headerlines u ($0*{TS_VCE}*1E+6 * decimation - t_offset_us):(column({CH_VCE}+1)-Rshunt*column({CH_IE}+1)) every decimation w l lw 2 t "V_C_E",\
	fn skip headerlines u ($0*{TS_VGE}*1E+6 * decimation - t_offset_us):(column({CH_VGE}+1)) every decimation w l lw 2 t "V_G_E",\
	fn skip headerlines u ($0*{TS_IE}*1E+6 * decimation - t_offset_us):(column({CH_IE}+1)) every decimation w l lw 2 t "I_E"
{insertion_after_plot}
 
	 
	 