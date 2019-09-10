cls
@set d="HP2-IGBT"
@del "%d%\*.tmp" >nul 2>&1
@for %%f in (".\%d%\*.txt") do @del /s "%d%\%%~nf.plt" >nul 2>&1
@..\src\batch_process.py -d %d% -f che2018dyn -s HP2_IGBT -m 9 -o "%d%.csv"