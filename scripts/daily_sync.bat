@echo off
cd /d C:\Users\SAMUEL\Desktop\MyProjects\predictz\predictz_football
echo ---- %date% %time% >> data\sync.log
.venv\Scripts\python.exe -m predictz.cli sync >> data\sync.log 2>&1