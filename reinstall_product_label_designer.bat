@echo off
chcp 65001 > nul
echo ================================================================================
echo 🔄 إعادة تثبيت Product Label Designer Module
echo ================================================================================
echo.

echo ⚠️  يرجى إيقاف Odoo أولاً إذا كان يعمل (Ctrl+C في نافذة Odoo)
echo.
pause

echo.
echo 🔄 الخطوة 1: تحديث الموديول...
echo.
cd L:\Lugal-ai
venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070 -u product_label_designer --stop-after-init

if %errorlevel% neq 0 (
    echo.
    echo ❌ فشل التحديث!
    echo تحقق من الأخطاء أعلاه
    pause
    exit /b 1
)

echo.
echo ✅ تم التحديث بنجاح!
echo.
echo 🚀 الخطوة 2: إعادة تشغيل Odoo...
echo.
echo سيتم تشغيل Odoo الآن...
echo اضغط Ctrl+C لإيقافه لاحقاً
echo.
pause

venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070

echo.
echo ✅ انتهى!


