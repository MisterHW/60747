cls
@set d="W:/AVT/_Projekte/Schaeffler/2017 Charakterisierung wassergekuehlter Leistungsmodule/00000 Messdaten/20190102 Doppelpulstest HP2/HP2-02-SW6-2R/"
@del %d%\*.tmp
@del %d%\*.plt
@src\batch_process.py --directory %d% --headerlines 22 --method 9