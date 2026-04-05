@echo off
chcp 65001 > nul
echo ================================================================================
echo 🔄 ترقية تلقائية - UoM Pricelist Module
echo ================================================================================
echo.

echo ⏸️  الخطوة 1: إيقاف Odoo...
echo.
echo يرجى إيقاف Odoo يدوياً إذا كان يعمل (Ctrl+C في نافذة Odoo)
echo.
pause

echo.
echo ✅ تم! الآن سنقوم بالترقية...
echo.

echo 🔄 الخطوة 2: ترقية الموديول...
python odoo-bin -c odoo.conf -u uom_in_pricelist -d lugal --stop-after-init

if %errorlevel% neq 0 (
    echo.
    echo ❌ فشلت الترقية!
    echo تحقق من الأخطاء أعلاه
    pause
    exit /b 1
)

echo.
echo ✅ تمت الترقية بنجاح!
echo.

echo 🚀 الخطوة 3: إعادة تشغيل Odoo...
echo.
echo سيتم تشغيل Odoo الآن...
echo اضغط Ctrl+C لإيقافه لاحقاً
echo.
pause

python odoo-bin -c odoo.conf

echo.
echo ✅ انتهى!



