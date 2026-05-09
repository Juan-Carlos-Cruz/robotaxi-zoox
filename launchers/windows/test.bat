@echo off
setlocal
cd /d "%~dp0\..\.."

py scripts\bootstrap.py test %*
if not errorlevel 1 goto :eof

python scripts\bootstrap.py test %*
exit /b %errorlevel%
