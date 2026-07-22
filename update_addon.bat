@echo off
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

set "TARGET_DIR=C:\Program Files\Blender Foundation\Blender 4.4\4.4\scripts\addons_core"
copy /Y "%~dp0level_editor.py" "%TARGET_DIR%\level_editor.py"
if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] level_editor.py copied to addons_core successfully!
) else (
    echo.
    echo [ERROR] Copy failed.
)
echo.
pause
