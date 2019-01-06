#!python3

import evaluate_waveform



# 10 V
# filen = '../HP2-02-SW6-2R/18-12-17 15-32-40  350 605 .txt'

# 15 V
# filen = '../HP2-02-SW6-2R/18-12-17 16-33-25  300 605 .txt'

# 18 V
#filen = '../HP2-02-SW6-2R/18-12-17 17-37-18  350 605 .txt'

filen = '../HP2-02-SW2-10R/19-01-02 13-15-16 HP2-02-SW2 50 105 .txt'

evaluate_waveform.process_file(filen, headerlines=22)