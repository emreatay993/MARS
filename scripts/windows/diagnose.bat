@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "MARS_NO_PAUSE=0"
:scan
if "%~1"=="" goto run
if /i "%~1"=="--no-pause" set "MARS_NO_PAUSE=1"
if /i "%~1"=="-NoPause" set "MARS_NO_PAUSE=1"
shift
goto scan
:run
powershell.exe -NoProfile -File "%~dp0diagnose.ps1" %* -NoPause
set "MARS_RESULT=%ERRORLEVEL%"
echo Diagnostic exit code: %MARS_RESULT%
if "%MARS_NO_PAUSE%"=="0" set /p "MARS_ENTER=Press Enter to close: "
exit /b %MARS_RESULT%
