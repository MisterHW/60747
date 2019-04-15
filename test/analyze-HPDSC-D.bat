cls
@set d="HPDSC-D"
@del "%d%\*.tmp"
@for %%f in (".\%d%\*.txt") do @del "%d%\%%~nf.plt"
@..\src\batch_process.py -d %d% -f che2018dyn -s HPDSC_D -m 2 -o "HPDSC-D.csv"