@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 main.py dev %*
) else (
    python main.py dev %*
)
exit /b %ERRORLEVEL%
