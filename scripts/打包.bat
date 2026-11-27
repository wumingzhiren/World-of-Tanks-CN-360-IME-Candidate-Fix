@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] 未找到 python
    echo         请安装 Python 3 并加入 PATH 后重试。
    pause
    exit /b 1
)

python build_package.py
if errorlevel 1 echo. & echo [FAILED] 详见上方提示。

echo.
pause
