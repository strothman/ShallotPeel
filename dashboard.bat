@echo off
title ShallotPeel - Token Usage Dashboard
cd /d "%~dp0"
python generate_dashboard.py
pause
