@echo off
title ShallotPeel - Token Usage Tracker
cd /d "%~dp0"
python tracker.py --all
echo.
pause
