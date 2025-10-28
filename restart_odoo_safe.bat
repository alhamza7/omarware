@echo off
echo ================================================================================
echo RESTART ODOO SAFELY
echo ================================================================================
echo.

echo Step 1: Stopping Odoo...
taskkill /F /IM python.exe 2>nul
timeout /t 3 /nobreak >nul

echo Step 2: Starting Odoo...
echo.
echo Starting Odoo server...
echo Access at: http://localhost:8069
echo.

start python odoo-bin -c odoo.conf

echo.
echo ================================================================================
echo Odoo is restarting!
echo Wait 10-15 seconds then open: http://localhost:8069
echo ================================================================================



