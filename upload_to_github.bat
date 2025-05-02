@echo off
:: 设置提交信息
set /p msg=请输入提交信息（默认：更新文件）： 
if "%msg%"=="" set msg=更新文件

echo.
echo === 添加更改 ===
git add .

echo.
echo === 提交更改 ===
git commit -m "%msg%"

echo.
echo === 推送到 GitHub ===
git push origin master

pause
