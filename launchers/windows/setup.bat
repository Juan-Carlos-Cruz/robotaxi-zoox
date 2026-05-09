@echo off
setlocal
cd /d "%~dp0\..\.."

py scripts\bootstrap.py setup %*
if not errorlevel 1 goto :eof

python scripts\bootstrap.py setup %*
exit /b %errorlevel%
