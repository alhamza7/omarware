@echo off
echo ========================================
echo   Restarting Odoo with wkhtmltopdf
echo ========================================
echo.

echo [1/3] Checking wkhtmltopdf...
"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe" --version
if %errorlevel% neq 0 (
    echo ERROR: wkhtmltopdf not found!
    pause
    exit /b 1
)
echo    wkhtmltopdf OK!

echo.
echo [2/3] Clearing Python cache...
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "addons\product_label_designer\__pycache__" rmdir /s /q "addons\product_label_designer\__pycache__"
if exist "addons\product_label_designer\models\__pycache__" rmdir /s /q "addons\product_label_designer\models\__pycache__"
if exist "addons\product_label_designer\wizard\__pycache__" rmdir /s /q "addons\product_label_designer\wizard\__pycache__"
if exist "addons\product_label_designer\controllers\__pycache__" rmdir /s /q "addons\product_label_designer\controllers\__pycache__"
echo    Cache cleared!

echo.
echo [3/3] Ready to start Odoo!
echo.
echo Now run:
echo    venv\Scripts\python odoo-bin -c odoo.conf
echo.
echo Or if not using venv:
echo    python odoo-bin -c odoo.conf
echo.
pause


