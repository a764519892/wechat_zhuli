@echo off
:: �����ύ��Ϣ
set /p msg=�������ύ��Ϣ��Ĭ�ϣ������ļ����� 
if "%msg%"=="" set msg=�����ļ�

echo.
echo === ��Ӹ��� ===
git add .

echo.
echo === �ύ���� ===
git commit -m "%msg%"

echo.
echo === ���͵� GitHub ===
git push origin master

pause
