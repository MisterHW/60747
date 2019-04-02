cls
@set d="HP2-D"
@del %d%\*.tmp
@del %d%\*.plt
@..\src\batch_process.py -d %d% -f che2018dyn -s HP2_D -m 2 -o "HP2-D.csv"