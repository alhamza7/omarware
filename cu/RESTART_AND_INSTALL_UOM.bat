@echo off
echo ================================================================================
echo اعادة تشغيل Odoo وتثبيت UoM in Pricelist
echo ================================================================================
echo.

echo 1. ايقاف Odoo...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Odoo*" 2>nul
timeout /t 3 >nul

echo.
echo 2. تشغيل Odoo مع تحديث الوحدة...
start "Odoo Server" python odoo-bin -c odoo.conf -u uom_in_pricelist -d lugal

echo.
echo 3. انتظار تشغيل Odoo (30 ثانية)...
timeout /t 30

echo.
echo 4. تثبيت الوحدة...
python install_uom_pricelist.py

echo.
echo ================================================================================
echo تم الانتهاء!
echo ================================================================================
pause

