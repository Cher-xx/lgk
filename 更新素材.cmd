@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo Updating inspiration library...
echo Images folder: image
echo Spreadsheet and API key folder: private-data
echo.

set "MATERIAL_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%MATERIAL_PYTHON%" (
  "%MATERIAL_PYTHON%" -X utf8 "%~dp0update_materials.py"
) else (
  python -X utf8 "%~dp0update_materials.py"
)
if errorlevel 1 goto :failed

set "MATERIAL_NODE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
if exist "%MATERIAL_NODE%" (
  "%MATERIAL_NODE%" "%~dp0scripts\sync-assets.mjs"
) else (
  node "%~dp0scripts\sync-assets.mjs"
)
if errorlevel 1 goto :failed

echo.
echo Update complete. React website data is synchronized.
echo Refresh the browser with Ctrl+F5 if the preview is open.
if /i "%~1"=="--no-pause" exit /b 0
pause
exit /b 0

:failed
echo.
echo Update stopped. Existing website data was not replaced.
echo Check private-data files, Python dependencies, and the error above.
if /i "%~1"=="--no-pause" exit /b 1
pause
exit /b 1
