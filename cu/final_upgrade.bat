@echo off
chcp 65001 > nul
echo ================================================================================
echo ✅ إصلاح نهائي وترقية - نظام التسعير الذكي
echo ================================================================================
echo.

echo 📋 ملخص التحديثات:
echo    1. ✅ نظام أولويات ذكي (Pricelist أولاً، ثم المعامل)
echo    2. ✅ إصلاح product_uom -^> product_uom_id
echo    3. ✅ إصلاح القائمة (menu parent)
echo    4. ✅ دعم Sales ^& POS
echo.

echo ⚠️  يجب إيقاف Odoo أولاً!
echo.
echo هل Odoo يعمل حالياً؟
echo    - إذا نعم: اذهب لنافذة Odoo واضغط Ctrl+C
echo    - إذا لا: اضغط Enter للمتابعة
echo.
pause

echo.
echo 🔄 الخطوة 1: ترقية الموديول...
python odoo-bin -c odoo.conf -u uom_in_pricelist -d lugal --stop-after-init

if %errorlevel% neq 0 (
    echo.
    echo ❌ فشلت الترقية!
    echo.
    echo 💡 الحلول المحتملة:
    echo    1. تأكد من إيقاف Odoo تماماً
    echo    2. احذف __pycache__: rmdir /s /q addons\uom_in_pricelist\__pycache__
    echo    3. حاول مرة أخرى
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ تمت الترقية بنجاح!
echo.

echo 🚀 الخطوة 2: إعادة تشغيل Odoo...
echo.
echo سيتم تشغيل Odoo الآن...
echo بعد التشغيل:
echo    1. افتح المتصفح: http://localhost:8069
echo    2. حدّث الصفحة: Ctrl+F5
echo    3. Sales -^> Orders -^> Create
echo    4. اختر منتج وغيّر UoM
echo    5. ✅ النظام الذكي يعمل!
echo.
pause

start "Odoo Server" python odoo-bin -c odoo.conf

echo.
echo ========================================
echo ✅ تم!
echo ========================================
echo.
echo 🎉 النظام الذكي نشط الآن!
echo.
echo 📖 للاختبار:
echo    python test_smart_pricing.py
echo.

