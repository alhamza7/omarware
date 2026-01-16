@echo off
chcp 65001 > nul
echo ========================================
echo     تجهيز بيانات Fragrantica للتصدير
echo ========================================
echo.

python prepare_export.py

echo.
echo ========================================
echo اضغط أي زر للإغلاق...
pause > nul









