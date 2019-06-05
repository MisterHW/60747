reset
set term wxt enhanced persist
nan = NaN
isNaN(x) = x == NaN ? 1 : 0 
fn = '19-03-16 15-53-41 HPDSC-D 300 105 .txt'

###
Rshunt      = 0.00984
headerlines = 22
t_1st_pulse = 1.7804500000000002e-05
t_delay     = 7.5e-05
t_2nd_pulse = 2e-05
t_zero      = 0

t_1st_pulse_rising  = t_zero - t_delay - t_1st_pulse
t_1st_pulse_falling = t_zero - t_delay
t_2nd_pulse_rising  = t_zero
t_2nd_pulse_falling = t_zero + t_2nd_pulse
t_3rd_period_end    = t_zero + t_2nd_pulse_falling + t_delay
###

set key box bottom right noautotitle width 1.25
set xzeroaxis
set title "Doppelpulstest: 19-03-16 15-53-41 HPDSC-D 300 105 .txt" font 'Verdana,14'
set mxtics 5
set mytics 5 
set xtics nomirror
set x2tics nomirror
set ytics nomirror
set grid ytics xtics
set link x2 via x inverse x
set link y2 via y inverse y
set mx2tics 4
set format x2 ""
set format y2 ""
set y2tics ("0" 0) out

decimation = 1
t_offset_us = 2e-09*100002 * 0.5 * 1E+6
set xrange [-t_offset_us:t_offset_us]

set style rect fc lt -1 fs transparent solid 0.1 noborder
set style line 1 lt 1 lw 1 lc rgb '#505050'
set style line 2 lt 3 lw 2 lc rgb 'black'
set style arrow 7 nohead ls 1 front
set style arrow 8 heads size screen 0.008,90 ls 2 front

annotation = 5

if(annotation == 1) \
	set title "turn-off and turn-on AOIs"; \
	set obj rect from -7.5e-05*1E+6, graph 0 to -7.4999999999999926e-06*1E+6, graph 1; \
	set obj rect from -5e-07*1E+6, graph 0 to 1.8e-05*1E+6, graph 1

if(annotation == 2) \
	set title "first and second pulse intervals"; \
	set obj rect from -9.28045e-05*1E+6, graph 0 to -7.5e-05*1E+6, graph 1; \
	set obj rect from 0*1E+6, graph 0 to 2e-05*1E+6, graph 1
	
if(annotation == 3) \
	set title "forward-recovery and reverse-recovery AOIs"; \
	set obj rect from -7.5e-05*1E+6, graph 0 to -7.249999999999999e-05*1E+6, graph 1; \
	set obj rect from 0*1E+6, graph 0 to 2.5e-06*1E+6, graph 1

if(annotation == 4) \
	set title 'tAOI\_D\_FWD'; \
	set obj rect from -7e-05*1E+6, graph 0 to -2e-06*1E+6, graph 1; \
	set arrow from -7e-05*1E+6, -1.4709024066992147 to -2e-06*1E+6, -1.4709024066992147 as 8; \
	set label sprintf("V_D = %.3f V", -1.4709024066992147 ) at (-7e-05+-2e-06)*0.5*1E+6,-1.4709024066992147 center offset 0,-0.75 front; \
	set arrow from -7e-05*1E+6, 300.8279572688089 to -2e-06*1E+6, 300.8279572688089 as 8; \
	set label sprintf("V_D_C = %.3f V", 300.8279572688089 ) at (-7e-05+-2e-06)*0.5*1E+6,300.8279572688089 center offset 0,0.75 front; \
	set arrow from -7.5e-05*1E+6, -113.72408449346344  to 0*1E+6, -101.61063133532355 as 8; \
	set label sprintf("%.3f A", -113.72408449346344 ) at -7.5e-05*1E+6, -113.72408449346344 right offset -0.5,0 front; \
	set label sprintf("I_F_M = %.3f A", -101.61063133532355 ) at 0*1E+6, -101.61063133532355 left offset 0.5,0 front
	
if(annotation == 5) \
	set title 'reverse-recovery event'; \
	set obj rect from 0*1E+6, graph 0 to 2.5e-06*1E+6, graph 1; \
	set xrange [0*1E+6-0.5:2.5e-06*1E+6+0.5]; \
	set y2tics add ("I_F_M" 102.831997633 ); \
	set arrow from 0*1E+6, 1.0*102.831997633  to 2.5e-06*1E+6, 1.0*102.831997633 as 7 back; \
	set y2tics add ("0.5*I_F_M" 0.5*102.831997633 ); \
	set arrow from 0*1E+6, 0.5*102.831997633  to 2.5e-06*1E+6, 0.5*102.831997633 as 7 back; \
	set y2tics add ("0.25*I_R_M" 0.25*-117.164005905 ); \
	set arrow from 0*1E+6, 0.25*-117.164005905  to 2.5e-06*1E+6, 0.25*-117.164005905 as 7 back; \
	set y2tics add ("0.5*I_R_M" 0.5*-117.164005905 ); \
	set arrow from 0*1E+6, 0.5*-117.164005905  to 2.5e-06*1E+6, 0.5*-117.164005905 as 7 back; \
	set y2tics add ("I_R_M" -117.164005905 ); \
	set arrow from 0*1E+6, 1.0*-117.164005905  to 2.5e-06*1E+6, 1.0*-117.164005905 as 7 back; \
	set label 1 "50% I_F_M" at 2.0035094911119917e-07*1E+6, 0.5*102.831997633 point pt 1 ps 2 front right offset -0.5,0.5; \
	set label 2 "t_0"   at 2.0870925489754095e-07*1E+6, 0 point pt 1 ps 2 front right offset -0.5,0.5; \
	set label 3 "50% I_R_M" at 2.200691855592237e-07*1E+6, 0.5*-117.164005905 point pt 1 ps 2 front right offset -0.5,0.5; \
	set label 4 "t_R_M"     at 2.365225513744329e-07*1E+6, -117.164005905 point pt 1 ps 2 front center offset 0,-0.75; \
	set label 5 "90% I_R_M" at 2.44e-07*1E+6, 0.9*-117.164005905 point pt 1 ps 2 front left offset 0.5,0.5; \
	set label 6 "25% I_R_M" at 2.66e-07*1E+6, 0.25*-117.164005905 point pt 1 ps 2 front left offset 0.5,0.5; \
	set label 7 "t_r_r_,_e_n_d" at 2.744615384615385e-07*1E+6, 0 point pt 1 ps 2 front left rotate by 45; \
	set label 8 "t_i_,_e_n_d" at 5.374663597076181e-07*1E+6, 0 point pt 1 ps 2 front left rotate by 45; \
	set arrow from 2.44e-07*1E+6, 0.9*-117.164005905  to 2.744615384615385e-07*1E+6, 0 as 7 back

	
set xlabel 'time (µs)'
set ylabel 'voltage (V) / current (A)'
filter(t,min,max,y_in, y_out) = (t > min && t < max) ? y_in : y_out


plot \
	fn skip headerlines u ($0*2e-09*1E+6 * decimation - t_offset_us):( column(1+1)) every decimation w l lw 2 t "V_D_C",\
	fn skip headerlines u ($0*2e-09 *1E+6 * decimation - t_offset_us):( column(2+1)) every decimation w l lw 2 t "V_D",\
	fn skip headerlines u ($0*2e-09 *1E+6 * decimation - t_offset_us):( column(3+1)) every decimation w l lw 2 t "I_D",\
	fn skip headerlines u ($0*2e-09 *1E+6 * decimation - t_offset_us):( column(3+1)):( \
		filter(($0*2e-09 *1E+6 * decimation - t_offset_us), 2.0870925489754095e-07*1E+6, 5.374663597076181e-07*1E+6, 0.0, column(3+1)) \
		) every decimation with filledcurves fs transparent solid 0.50 lc rgb "gold" 
		

 
	 
	 