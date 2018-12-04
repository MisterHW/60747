#!python3

import numpy as np

class WaveformAnalyzer:
	s = []; # 1D sample data
	timebase = 1.0
	timebase_unitstr = 'a.u.'
	id_str = 'waveform'
	t0_samplepos = 0
	
	
	def __init__(self, samples_data, 
			timebase = timebase, t0_samplepos = t0_samplepos, 
			timebase_unitstr = timebase_unitstr, id_str = id_str):
			
		self.s = samples_data
		self.timebase = timebase
		self.t0_samplepos = t0_samplepos 
		self.timebase_unitstr = timebase_unitstr
		self.id_str = id_str 
		
		
	def __force_inrange(self, sAOI):
		initial_sAOI = sAOI
		for i in range(0, len(sAOI)):
			sAOI[i] = max(0, min(len(self.s)-1, sAOI[i]))
		if sAOI != initial_sAOI:
			print("warning: sample AOI out of range. Values changed from" + 
					repr(initial_sAOI) + " to " + repr(sAOI))
					
		
	def smp_to_time(self, sAOI):
		# self.__force_inrange(sAOI) # not used, time values are not directly used with self.s
		smp_to_t = lambda s: (s - self.t0_samplepos) * self.timebase
		tAOI = [smp_to_t(sAOI[i]) for i in range(0, len(sAOI))]
		return tAOI
	
	
	def time_to_smp(self, tAOI, force_inrange = True):
		t_to_smp = lambda t: t / self.timebase + self.t0_samplepos
		sAOI = [t_to_smp(tAOI[i]) for i in range(0, len(tAOI))]
		if force_inrange:
			self.__force_inrange(sAOI)
		return sAOI
		
	def time_span(self):
		return self.smp_to_time([0,len(self.s)-1])
		
		
	def waveform_integral(self, tAOI):
		sAOI = self.time_to_smp(tAOI)
		nsmp = sAOI[1] - sAOI[0] + 1
		av = np.sum(self.s[round(sAOI[0]):round(sAOI[1])])
		return [av, nsmp]

		
	def average(self, tAOI):
		av, nsmp = self.waveform_integral(tAOI)
		return [av/nsmp, nsmp]
		
		
	def percentile_values(self, tAOI, percentiles):
		sAOI = self.time_to_smp(tAOI)
		sorted_samples = np.sort(self.s[round(sAOI[0]):round(sAOI[1])]) # quicksort ascending
		nsmp = len(sorted_samples)
		vals  = [ sorted_samples[max(0, min(round((nsmp-1)*p), nsmp-1))] for p in percentiles]
		return vals 
		
		
	def samples_in_AOI(tAOI):
		# TODO 
		return []
		
		
	def samples_in_rect(tAOI, yAOI):
		# TODO
		return []
		
		
	def percentile_value(self, tAOI, percentile):
		return self.percentile_values(tAOI, [percentile])[0]
		
		
	def samples_t(self, tAOI, nsmp = 0):
		sAOI = list(map(round, self.time_to_smp(tAOI)))
		if nsmp == 0:
			nsmp = sAOI[1] - sAOI[0] + 1
		return np.linspace(start = tAOI[0], stop = tAOI[1] , num = nsmp)
		
		
	def lin_fit(self, tAOI):
		a, b, success = 0, 0, False # polynomial coefficients for p(x) * a + b*x and success result
		sAOI = list(map(round, self.time_to_smp(tAOI)))
		s_y = self.s[sAOI[0]:sAOI[1]+1]
		nsmp = len(s_y)
		if nsmp > 1:
			# formula: https://en.wikipedia.org/wiki/Simple_linear_regression
			s_x = self.samples_t(tAOI)	
			mean_x = np.mean(s_x)
			mean_y = np.mean(s_y)
			cov_matrix = np.cov(s_x, s_y) 
			cov_xy = cov_matrix[0][1]
			var_x  = cov_matrix[0][0]
			b = cov_xy / var_x
			a = mean_y - b * mean_x
			success = True
		else: 
			a = samples_y[0]
			b = 0
			success = False 
		return [a,b, success]
		
		
	def find_level_crossing(self, tAOI, level, edge='both'):
		#	find level crossing within time AOI 
		success = False
		t, dydt = None, 0
		# prepare data 
		sAOI = list(map(round, self.time_to_smp(tAOI)))
		s_y = self.s[sAOI[0]:sAOI[1]+1]
		#	find first crossing with appropriate edge type 
		#	define time interval around crossing
		#	generate linear fit and re-calculate intersection
		return [t, dydt]
		

	def resampled_region(self, tAOI, nsmp):	
		t_x  = np.linspace(start = tAOI[0], stop = tAOI[1] , num = nsmp, endpoint = False)
		s_x  = self.time_to_smp(t_x) 
		# list index out of range handling: repeat nearest neighbour			
		if s_x[-1] + 1 > len(self.s) - 1:
			s_x[-1] = s_x[-2] 
		# create linear interpolated 1D data 
		r_re = [ 
			self.s[int(s_x[i])    ]*(1 - (s_x[i] - int(s_x[i]))) + 
			self.s[int(s_x[i]) + 1]*(    (s_x[i] - int(s_x[i]))) 
				for i in range(0, len(s_x)) ]
		return r_re
		

def arithmetic_operation(WFA_list, tAOI, func, generate_time_coords = False):
# assume equidistant samples, find smallest timestep via list of AOI sample lengths
	n = [np.dot(wfa.time_to_smp(tAOI), [-1, 1]) + 1 for wfa in WFA_list]
	n_max = max(n)
	first_match_index = lambda list, value: next((idx for idx,val in enumerate(list) if val == value), 0) 
	idx_max = first_match_index(n, n_max)
	n_max = int(round(n_max)) # force integer to avoid float type aliasing / array length mismatch (+/-1 errors)	
# prepare resampled data 
	rdata = np.array([wfa.resampled_region(tAOI, n_max) for wfa in WFA_list]).transpose()
# feed list of individual samples to arithmetic function
	outp_t = []
	outp_y = list(map(func, rdata))	
	if generate_time_coords:
		outp_t = WFA_list[idx_max].samples_t(tAOI, n_max)
	return [outp_t, outp_y]