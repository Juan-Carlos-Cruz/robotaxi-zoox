@echo off
setlocal
cd /d "%~dp0\..\.."

py scripts\bootstrap.py doctor %*
if not errorlevel 1 goto :eof

python scripts\bootstrap.py doctor %*
exit /b %errorlevel%
