@echo off
setlocal
cd /d "%~dp0\..\.."

py scripts\bootstrap.py run %*
if not errorlevel 1 goto :eof

python scripts\bootstrap.py run %*
exit /b %errorlevel%
