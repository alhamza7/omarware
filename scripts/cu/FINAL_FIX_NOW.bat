@echo off
chcp 65001 > nul
cls
echo ========================================
echo ✅ الإصلاح النهائي - جاهز للتطبيق
echo ========================================
echo.

echo 📋 الإصلاحات المطبقة:
echo    1. ✅ product_uom -^> product_uom_id
echo    2. ✅ تصحيح _compute_price signature (Odoo 19)
echo    3. ✅ إصلاح القائمة parent
echo    4. ✅ نظام الأولويات الذكي
echo.

echo ⚠️  يجب إيقاف Odoo أولاً!
echo.
pause

echo.
echo 🔄 جاري الترقية...
python odoo-bin -c odoo.conf -u uom_in_pricelist -d lugal --stop-after-init

if %errorlevel% neq 0 (
    echo.
    echo ❌ فشلت الترقية!
    pause
    exit /b 1
)

echo.
echo ✅ تمت الترقية بنجاح!
echo.
echo 🚀 إعادة تشغيل Odoo...
pause

start "Odoo Server" python odoo-bin -c odoo.conf

echo.
echo ✅ تم!
echo.
echo 📖 اختبر الآن:
echo    1. افتح المتصفح: http://localhost:8069
echo    2. Ctrl+F5 (تحديث)
echo    3. Sales -^> Orders -^> Create
echo    4. أضف منتج وغيّر UoM
echo    5. ✅ يجب أن يعمل بدون أخطاء!
echo.
pause

