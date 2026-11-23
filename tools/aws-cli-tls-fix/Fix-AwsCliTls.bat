@echo off
rem Double-click wrapper for Fix-AwsCliTls.ps1 (must sit in the same folder).
rem -ExecutionPolicy Bypass applies to this one run only. It is needed because files
rem downloaded from the internet or a release are blocked by default policy.
rem Any arguments are passed through, for example: Fix-AwsCliTls.bat -WhatIf
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Fix-AwsCliTls.ps1" %*
set EXITCODE=%ERRORLEVEL%
echo.
if %EXITCODE%==0 (echo Finished. Close and reopen any open terminals.) else (echo FAILED. See the messages above.)
rem Pause only when launched by double-click, so the window does not vanish.
echo %cmdcmdline% | findstr /i /c:"%~nx0" >nul
if not errorlevel 1 pause
exit /b %EXITCODE%
