@echo off
setlocal
cd /d "%~dp0"
pushd ..

rem 需要 JPEXS Free Flash Decompiler 的 ffdec-cli.exe
rem 默认从 PATH 查找；也可先 set FFDEC=<绝对路径> 指定
if "%FFDEC%"=="" set "FFDEC=ffdec-cli.exe"
"%FFDEC%" -help >nul 2>nul
if errorlevel 9009 (
    echo [ERROR] 找不到 ffdec-cli.exe
    echo         请安装 JPEXS Free Flash Decompiler，把 ffdec-cli.exe 放进 PATH，
    echo         或先执行： set FFDEC=D:\path\to\ffdec-cli.exe
    popd
    pause
    exit /b 1
)

if not exist "build\ime_orig.swf" (
    echo [ERROR] 缺少 build\ime_orig.swf ^(原版基线^)
    echo         请从客户端 res\packages\gui.pkg 中提取 gui/flash/ime.swf，
    echo         另存为 build\ime_orig.swf 后重试。详见 README。
    popd
    pause
    exit /b 1
)

echo 正在用 src\ 下的补丁重编译 build\ime.swf ...
"%FFDEC%" -importScript "build\ime_orig.swf" "build\ime.swf" "src"
if errorlevel 1 (
    echo [FAILED] importScript 执行失败
    popd
    pause
    exit /b 1
)

echo.
echo [OK] build\ime.swf 已生成
echo 散装安装：复制 build\ime.swf 到
echo   ^<游戏目录^>\res_mods\^<版本号^>\gui\flash\ime.swf
popd
pause
