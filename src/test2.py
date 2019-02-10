#!python3

import evaluate_waveform

filen = '../HP2-02-D2/19-01-03 16-47-57 HP2-02-D2 200 455 .txt'

evaluate_waveform.process_file(filen, headerlines=22, method=2)