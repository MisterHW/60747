cls
@set d="HPDSC-IGBT"
@del "%d%\*.tmp" >nul 2>&1
@for %%f in (".\%d%\*.txt") do @del /s "%d%\%%~nf.plt" >nul 2>&1
@..\src\batch_process.py -d %d% -f che2018dyn -s HPDSC_IGBT -m 9 -o "%d%.csv"