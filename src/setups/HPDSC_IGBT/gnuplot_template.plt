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

I1_a = isNaN({I_1st_fit_a}) ? 0 : {I_1st_fit_a}
I1_b = isNaN({I_1st_fit_b}) ? 0 : {I_1st_fit_b}
I2_a = isNaN({I_2nd_fit_a}) ? 0 : {I_2nd_fit_a}
I2_b = isNaN({I_2nd_fit_b}) ? 0 : {I_2nd_fit_b}
I1(t) = I1_a + I1_b * t
I2(t) = I2_a + I2_b * t

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


set key box top right noautotitle width 1.25 height 1.25
set xzeroaxis
set title "Doppelpulstest: {file_base}" font 'Verdana,16'
set mxtics 5
set mytics 5 
set xtics nomirror
set x2tics nomirror offset 0,-0.5
set grid ytics xtics
set link x2 via x inverse x
set mx2tics 4
set format x2 ""

decimation = 2
t_offset_us = {TS_VDC}*{n_samples} * 0.5 * 1E+6
set xrange [-t_offset_us:t_offset_us]
set x2range [-t_offset_us:t_offset_us]

set style rect fc lt -1 fs transparent solid 0.1 noborder
set obj rect from {tAOI_turn_off_bounds_begin}*1E+6, graph 0 to {tAOI_turn_off_bounds_end}*1E+6, graph 1
set obj rect from {tAOI_turn_on_bounds_begin}*1E+6 , graph 0 to {tAOI_turn_on_bounds_end}*1E+6, graph 1

# set x2tics add ("" -1E+6) # catch element for tics at NaN (workaround for "add_tic_user: list sort error")

if (!isNaN({turn_off_t1})){\
	set label 1 "90% V_G_E " at {turn_off_t1}*1E+6, 0.9*{V_GE_high} point pt 1 ps 2 front right offset 0,0 rotate by -45; \
	set x2tics add ("A" {turn_off_t1}*1E+6)}
if (!isNaN({turn_off_t2})){\
	set label 2 "90% I_p_k" at {turn_off_t2}*1E+6, 0.9*{Ipk_turnoff} point pt 1 ps 2 front rotate by 45; \
	set x2tics add ("B" {turn_off_t2}*1E+6)} 
if (!isNaN({turn_off_t3})){\
	set label 3 "10% I_p_k" at {turn_off_t3}*1E+6, 0.1*{Ipk_turnoff} point pt 1 ps 2 front rotate by 45; \
	set x2tics add ("C" {turn_off_t3}*1E+6)} 
if (!isNaN({turn_off_t4})){\
	set label 4 "2% I_p_k" at {turn_off_t4}*1E+6, 0.02*{Ipk_turnoff} point pt 1 ps 2 front; \
	set x2tics add ("D" {turn_off_t4}*1E+6)}

if (!isNaN({turn_on_t1})){\
	set label 5 "10% V_G_E " at {turn_on_t1}*1E+6, 0.1*{V_GE_high} point pt 1 ps 2 front right offset 0,0 rotate by -45; \
	set x2tics add ("E" {turn_on_t1}*1E+6)}
if (!isNaN({turn_on_t2})){\
	set label 6 "10% I_p_k" at {turn_on_t2}*1E+6, 0.1*{Ipk_turnoff} point pt 1 ps 2 front rotate by 45; \
	set x2tics add ("F" {turn_on_t2}*1E+6)}
if (!isNaN({turn_on_t3})){\
	set label 7 "90% I_p_k" at {turn_on_t3}*1E+6, 0.9*{Ipk_turnoff} point pt 1 ps 2 front rotate by 45; \
	set x2tics add ("G" {turn_on_t3}*1E+6)}
if (!isNaN({turn_on_t4})){\
	set label 8 sprintf("%.1f%% V_D_C",{DET_turn_on_t4_fraction}*100) at {turn_on_t4}*1E+6, {DET_turn_on_t4_fraction}*{V_DC} point pt 1 ps 2 front; \
	set x2tics add ("H" {turn_on_t4}*1E+6)}


set xlabel 'time (µs)'
set ylabel 'voltage (V) / current (A)'

# current channel coefficient (nominally 100 A/V (10 mOhm shunt), actual value 102.145 A/V (9.79 mOhm shunt))
Ic = 1 / (100.0 * Rshunt)

{insertion_before_plot}
plot \
	$IEData u ($1*1E+6):2 w l t 'I_E(fit)' lc rgb 'gray' lw 2,\
	fn skip headerlines u ($0*{TS_VDC}*1E+6 * decimation - t_offset_us):(column({CH_VDC_raw}+1) + Rshunt * Ic * column({CH_IE_raw}+1)) every decimation w l lw 2 t "V_D_C",\
	fn skip headerlines u ($0*{TS_VCE}*1E+6 * decimation - t_offset_us):(column({CH_VCE_raw}+1)) every decimation w l lw 2 t "V_C_E",\
	fn skip headerlines u ($0*{TS_VGE}*1E+6 * decimation - t_offset_us):(column({CH_VGE_raw}+1)) every decimation w l lw 2 t "V_G_E",\
	fn skip headerlines u ($0*{TS_IE}*1E+6 * decimation - t_offset_us):(Ic * column({CH_IE_raw}+1)) every decimation w l lw 2 t "I_E"
{insertion_after_plot}
 
	 
	 