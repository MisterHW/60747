cls
@set d="HP2-IGBT/"
@del "%d%\*.tmp"
@for %%f in (".\%d%\*.txt") do @del "%d%\%%~nf.plt"
@..\src\batch_process.py -d %d% -f che2018dyn -s HP2_IGBT -m 9 -o "HP2-IGBT.csv"