@echo off
cd %~dp0
call vbot\scripts\activate.bat
python bot.py
pause
