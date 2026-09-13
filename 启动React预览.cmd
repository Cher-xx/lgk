@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "INSPIRATION_PNPM=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd"
set "MATERIAL_NODE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
set "PATH=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;%PATH%"

if exist "node_modules\vite\bin\vite.js" goto :start
if exist "%INSPIRATION_PNPM%" goto :pnpm_install
goto :npm_install

:pnpm_install
echo First-time setup: installing website dependencies...
call "%INSPIRATION_PNPM%" install
if errorlevel 1 goto :failed
goto :start

:npm_install
echo First-time setup: installing website dependencies...
call npm install
if errorlevel 1 goto :failed
goto :start

:start
if not exist "node_modules\vite\bin\vite.js" goto :failed
echo Starting local preview. Your browser will open when it is ready...
if exist "%MATERIAL_NODE%" (
  "%MATERIAL_NODE%" "scripts\sync-assets.mjs"
  if errorlevel 1 goto :failed
  "%MATERIAL_NODE%" "node_modules\vite\bin\vite.js" --host 127.0.0.1 --open
) else (
  node "scripts\sync-assets.mjs"
  if errorlevel 1 goto :failed
  node "node_modules\vite\bin\vite.js" --host 127.0.0.1 --open
)
goto :end

:failed
echo.
echo Preview could not start. Check the error above, then run this file again.

:end
pause
