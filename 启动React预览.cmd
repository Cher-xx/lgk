@echo off
cd /d "%~dp0"
set "INSPIRATION_PNPM=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd"
set "PATH=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;%PATH%"
if exist "%INSPIRATION_PNPM%" (
  call "%INSPIRATION_PNPM%" dev
) else (
  call npm run dev
)
pause
