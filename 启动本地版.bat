@echo off
rem ============================================
rem  RP Hub 本地启动器
rem  以 http://localhost:8000 打开本地版：
rem   - sharellm 等带 Origin 白名单的 API 可用
rem   - 本地 127.0.0.1:8317 等 HTTP 服务可用（无混合内容限制）
rem   - 设置与 Pages 版共用浏览器存储则互不影响
rem ============================================
cd /d %~dp0
echo 正在启动 RP Hub 本地服务器... 关闭本窗口即停止。
start "" "http://localhost:8000"
python -m http.server 8000 --bind 127.0.0.1
if errorlevel 1 (
    echo.
    echo [错误] 未找到 Python。请先安装 Python，或在文件夹内用 VS Code Live Server 打开 index.html。
)
pause
