reset
set term wxt enhanced persist
nan = NaN
isNaN(x) = x == NaN ? 1 : 0 
fn = '{file_base}'

###
Rshunt      = {R_shunt}
headerlines = {header_rows}
t_1st_pulse = {t_1st_duration}
t_delay     = {t_inter_pulse_duration}
t_2nd_pulse = {t_2nd_duration}
t_zero      = 0

t_1st_pulse_rising  = t_zero - t_delay - t_1st_pulse
t_1st_pulse_falling = t_zero - t_delay
t_2nd_pulse_rising  = t_zero
t_2nd_pulse_falling = t_zero + t_2nd_pulse
t_3rd_period_end    = t_zero + t_2nd_pulse_falling + t_delay
###


set key box top right noautotitle width 1.25
set xzeroaxis
set title "Doppelpulstest: {file_base}" font 'Verdana,14'
set mxtics 5
set mytics 5 
set xtics nomirror
set x2tics font 'Verdana Bold, 12' offset 0, -0.25
set format x2 ""
set grid ytics x2tics

decimation = 2
t_offset_us = {TS_VDC}*{n_samples} * 0.5 * 1E+6
set xrange [-t_offset_us:t_offset_us]


set xlabel 'time (µs)'
set ylabel 'voltage (V) / current (A)'
{insertion_before_plot}
plot \
	fn skip headerlines u ($0*{TS_VDC}*1E+6 * decimation - t_offset_us):( column({CH_VDC}+1)) every decimation w l lw 2 t "V_D_C",\
	fn skip headerlines u ($0*{TS_VD} *1E+6 * decimation - t_offset_us):(-column({CH_VD} +1)) every decimation w l lw 2 t "V_D",\
	fn skip headerlines u ($0*{TS_ID} *1E+6 * decimation - t_offset_us):(-column({CH_ID} +1)) every decimation w l lw 2 t "I_D"
{insertion_after_plot}
 
	 
	 