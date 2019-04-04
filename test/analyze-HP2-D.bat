cls
@set d="HP2-D"
@del "%d%\*.tmp"
@for %%f in (".\%d%\*.txt") do @del "%d%\%%~nf.plt"
@..\src\batch_process.py -d %d% -f che2018dyn -s HP2_D -m 2 -o "HP2-D.csv"