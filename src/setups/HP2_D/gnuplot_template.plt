reset
set term wxt enhanced persist size 1200,800 font 'Verdana,14'
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

set key box bottom right noautotitle width 1.25 height 1.25
set xzeroaxis
set title "Doppelpulstest: {file_base}" font 'Verdana,16'
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
t_offset_us = {TS_VDC}*{n_samples} * 0.5 * 1E+6
set xrange [-t_offset_us:t_offset_us]

set style rect fc lt -1 fs transparent solid 0.1 noborder
set style line 1 lt 1 lw 1 lc rgb '#505050'
set style line 2 lt 3 lw 2 lc rgb 'black'
set style arrow 7 nohead ls 1 front
set style arrow 8 heads size screen 0.008,90 ls 2 front

annotation = 5

if(annotation == 1) \
	set title "turn-off and turn-on AOIs"; \
	set obj rect from {tAOI_turn_off_bounds_begin}*1E+6, graph 0 to {tAOI_turn_off_bounds_end}*1E+6, graph 1; \
	set obj rect from {tAOI_turn_on_bounds_begin}*1E+6, graph 0 to {tAOI_turn_on_bounds_end}*1E+6, graph 1

if(annotation == 2) \
	set title "first and second pulse intervals"; \
	set obj rect from {t_1st_rise_nom}*1E+6, graph 0 to {t_1st_fall_nom}*1E+6, graph 1; \
	set obj rect from {t_2nd_rise_nom}*1E+6, graph 0 to {t_2nd_fall_nom}*1E+6, graph 1
	
if(annotation == 3) \
	set title "forward-recovery and reverse-recovery AOIs"; \
	set obj rect from {tAOI_1st_fr_event_begin}*1E+6, graph 0 to {tAOI_1st_fr_event_end}*1E+6, graph 1; \
	set obj rect from {tAOI_rr_event_begin}*1E+6, graph 0 to {tAOI_rr_event_end}*1E+6, graph 1

if(annotation == 4) \
	set title 'tAOI\_D\_FWD'; \
	set obj rect from {tAOI_D_FWD_begin}*1E+6, graph 0 to {tAOI_D_FWD_end}*1E+6, graph 1; \
	set arrow from {tAOI_D_FWD_begin}*1E+6, {V_D_1st_on_av} to {tAOI_D_FWD_end}*1E+6, {V_D_1st_on_av} as 8; \
	set label sprintf("V_D = %.3f V", {V_D_1st_on_av} ) at ({tAOI_D_FWD_begin}+{tAOI_D_FWD_end})*0.5*1E+6,{V_D_1st_on_av} center offset 0,-0.75 front; \
	set arrow from {tAOI_D_FWD_begin}*1E+6, {V_DC_1st_on_av} to {tAOI_D_FWD_end}*1E+6, {V_DC_1st_on_av} as 8; \
	set label sprintf("V_D_C = %.3f V", {V_DC_1st_on_av} ) at ({tAOI_D_FWD_begin}+{tAOI_D_FWD_end})*0.5*1E+6,{V_DC_1st_on_av} center offset 0,0.75 front; \
	set arrow from {t_1st_fall_nom}*1E+6, -{I_1st_fr_peak_lin_estimate}  to {t_2nd_rise_nom}*1E+6, -{I_rr_fwd_lin_estimate} as 8; \
	set label sprintf("%.3f A", -{I_1st_fr_peak_lin_estimate} ) at {t_1st_fall_nom}*1E+6, -{I_1st_fr_peak_lin_estimate} right offset -0.5,0 front; \
	set label sprintf("I_F_M = %.3f A", -{I_rr_fwd_lin_estimate} ) at {t_2nd_rise_nom}*1E+6, -{I_rr_fwd_lin_estimate} left offset 0.5,0 front
	
if(annotation == 5) \
	set title 'reverse-recovery event'; \
	set obj rect from {tAOI_rr_event_begin}*1E+6, graph 0 to {tAOI_rr_event_end}*1E+6, graph 1; \
	set xrange [{tAOI_rr_event_begin}*1E+6-0.5:{tAOI_rr_event_end}*1E+6+0.5]; \
	set y2tics add ("I_F_M" {I_rr_fwd_max} ); \
	set arrow from {tAOI_rr_event_begin}*1E+6, 1.0*{I_rr_fwd_max}  to {tAOI_rr_event_end}*1E+6, 1.0*{I_rr_fwd_max} as 7 back; \
	set y2tics add ("0.5*I_F_M" 0.5*{I_rr_fwd_max} ); \
	set arrow from {tAOI_rr_event_begin}*1E+6, 0.5*{I_rr_fwd_max}  to {tAOI_rr_event_end}*1E+6, 0.5*{I_rr_fwd_max} as 7 back; \
	set y2tics add ("0.25*I_R_M" 0.25*{I_rr_rev_max} ); \
	set arrow from {tAOI_rr_event_begin}*1E+6, 0.25*{I_rr_rev_max}  to {tAOI_rr_event_end}*1E+6, 0.25*{I_rr_rev_max} as 7 back; \
	set y2tics add ("0.5*I_R_M" 0.5*{I_rr_rev_max} ); \
	set arrow from {tAOI_rr_event_begin}*1E+6, 0.5*{I_rr_rev_max}  to {tAOI_rr_event_end}*1E+6, 0.5*{I_rr_rev_max} as 7 back; \
	set y2tics add ("I_R_M" {I_rr_rev_max} ); \
	set arrow from {tAOI_rr_event_begin}*1E+6, 1.0*{I_rr_rev_max}  to {tAOI_rr_event_end}*1E+6, 1.0*{I_rr_rev_max} as 7 back; \
	set label 1 "50% I_F_M" at {t_rr_50pc_FM_falling}*1E+6, 0.5*{I_rr_fwd_max} point pt 1 ps 2 front right offset -0.5,0.5; \
	set label 2 "t_0"   at {t_rr_0}*1E+6, 0 point pt 1 ps 2 front right offset -0.5,0.5; \
	set label 3 "50% I_R_M" at {t_rr_50pc_RM_falling}*1E+6, 0.5*{I_rr_rev_max} point pt 1 ps 2 front right offset -0.5,0.5; \
	set label 4 "t_R_M"     at {t_rr_RM}*1E+6, {I_rr_rev_max} point pt 1 ps 2 front center offset 0,-0.75; \
	set label 5 "90% I_R_M" at {t_rr_90pc_RM_rising}*1E+6, 0.9*{I_rr_rev_max} point pt 1 ps 2 front left offset 0.5,0.5; \
	set label 6 "25% I_R_M" at {t_rr_25pc_RM_rising}*1E+6, 0.25*{I_rr_rev_max} point pt 1 ps 2 front left offset 0.5,0.5; \
	set label 7 "t_r_r_,_e_n_d" at {t_rr_1_90_25}*1E+6, 0 point pt 1 ps 2 front left rotate by 45; \
	set label 8 "t_i_,_e_n_d" at {t_rr_int_end}*1E+6, 0 point pt 1 ps 2 front left rotate by 45; \
	set arrow from {t_rr_90pc_RM_rising}*1E+6, 0.9*{I_rr_rev_max}  to {t_rr_1_90_25}*1E+6, 0 as 7 back

	
set xlabel 'time (µs)'
set ylabel 'voltage (V) / current (A)'
filter(t,min,max,y_in, y_out) = (t > min && t < max) ? y_in : y_out

{insertion_before_plot}
plot \
	fn skip headerlines u ($0*{TS_VDC}*1E+6 * decimation - t_offset_us):( column({CH_VDC}+1)) every decimation w l lw 2 t "V_D_C",\
	fn skip headerlines u ($0*{TS_VD} *1E+6 * decimation - t_offset_us):( column({CH_VD}+1)) every decimation w l lw 2 t "V_D",\
	fn skip headerlines u ($0*{TS_ID} *1E+6 * decimation - t_offset_us):(-column({CH_ID}+1)) every decimation w l lw 2 t "I_D",\
	fn skip headerlines u ($0*{TS_ID} *1E+6 * decimation - t_offset_us):(-column({CH_ID}+1)):( \
		filter(($0*{TS_ID} *1E+6 * decimation - t_offset_us), {t_rr_0}*1E+6, {t_rr_int_end}*1E+6, 0.0, -column({CH_ID}+1)) \
		) every decimation with filledcurves fs transparent solid 0.50 lc rgb "gold" 
		
{insertion_after_plot}
 
	 
	 