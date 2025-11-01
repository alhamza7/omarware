@echo off
echo ========================================
echo   RESTART ODOO - Full Restart
echo ========================================
echo.

echo [1/4] Stopping Odoo processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq odoo*" 2>nul
timeout /t 2 /nobreak >nul
echo    Odoo stopped!

echo.
echo [2/4] Clearing cache...
if exist "__pycache__" rmdir /s /q "__pycache__" 2>nul
if exist "addons\product_label_designer\__pycache__" rmdir /s /q "addons\product_label_designer\__pycache__" 2>nul
if exist "addons\product_label_designer\models\__pycache__" rmdir /s /q "addons\product_label_designer\models\__pycache__" 2>nul
if exist "addons\product_label_designer\wizard\__pycache__" rmdir /s /q "addons\product_label_designer\wizard\__pycache__" 2>nul
if exist "addons\product_label_designer\controllers\__pycache__" rmdir /s /q "addons\product_label_designer\controllers\__pycache__" 2>nul
echo    Cache cleared!

echo.
echo [3/4] Verifying wkhtmltopdf...
"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe" --version
if %errorlevel% neq 0 (
    echo ERROR: wkhtmltopdf not found!
    pause
    exit /b 1
)
echo    wkhtmltopdf OK!

echo.
echo [4/4] Starting Odoo...
echo.
echo Starting Odoo server...
echo Please wait...
echo.

start "Odoo Server" python odoo-bin -c odoo.conf

echo.
echo ========================================
echo   Odoo is starting in new window!
echo ========================================
echo.
echo Wait 30 seconds, then:
echo   1. Go to browser
echo   2. F5 (Reload)
echo   3. Apps - Upgrade "Product Label Designer"
echo   4. Try printing!
echo.
echo ========================================
pause


