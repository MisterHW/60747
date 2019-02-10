#!python3

import evaluate_waveform

filen = '../HP2-02-SW6-2R/18-12-17 15-22-51  100 130 .txt'

evaluate_waveform.process_file(filen, headerlines=22, method=9)