@echo off
echo ========================================================
echo YOUTUBE AUTOMATION DAILY RUN
echo %date% %time%
echo ========================================================

:: Change directory to the automation folder
cd /d "d:\youtube_automation"

:: Run the python daily job script
echo [TASK] Launching YOUTUBE AUTOMATION ...
d:\youtube_automation\venv\Scripts\python.exe daily_job.py

echo ========================================================
echo DAILY RUN COMPLETE
echo %date% %time%
echo ========================================================
pause
