cls
@set d="HPDSC-IGBT/"
@del "%d%\*.tmp"
@for %%f in (".\%d%\*.txt") do @del "%d%\%%~nf.plt"
@..\src\batch_process.py -d %d% -f che2018dyn -s HPDSC_IGBT -m 9 -o "HPDSC-IGBT.csv"