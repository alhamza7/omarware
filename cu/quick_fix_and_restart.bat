@echo off
echo ========================================
echo اصلاح وترقية UOM Pricelist Module
echo ========================================
echo.

echo الخطوة 1: ترقية الموديول...
python odoo-bin -c odoo.conf -u uom_in_pricelist -d lugal --stop-after-init

if %errorlevel% neq 0 (
    echo.
    echo ❌ فشل الترقية!
    echo تحقق من الأخطاء أعلاه
    pause
    exit /b 1
)

echo.
echo ✅ تمت الترقية بنجاح!
echo.
echo الخطوة 2: إعادة تشغيل Odoo...
echo.
echo ملاحظة: سيتم تشغيل Odoo الآن
echo اضغط Ctrl+C لإيقافه عند الحاجة
echo.
pause

python odoo-bin -c odoo.conf



