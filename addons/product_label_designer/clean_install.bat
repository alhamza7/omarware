@echo off
echo ========================================
echo   Clean Installation Script
echo   Product Label Designer
echo ========================================
echo.

echo [1/4] Removing Python cache...
if exist "addons\product_label_designer\__pycache__" rmdir /s /q "addons\product_label_designer\__pycache__"
if exist "addons\product_label_designer\models\__pycache__" rmdir /s /q "addons\product_label_designer\models\__pycache__"
if exist "addons\product_label_designer\wizard\__pycache__" rmdir /s /q "addons\product_label_designer\wizard\__pycache__"
if exist "addons\product_label_designer\controllers\__pycache__" rmdir /s /q "addons\product_label_designer\controllers\__pycache__"
echo    Cache removed!

echo.
echo [2/4] Checking files...
dir /b addons\product_label_designer\*.py
echo    Files OK!

echo.
echo [3/4] Next steps:
echo    1. Restart Odoo server (Ctrl+C then restart)
echo    2. In browser: Ctrl+Shift+Delete (clear cache)
echo    3. Apps - Update Apps List
echo    4. Search "Product Label Designer"
echo    5. Click Install
echo.

echo [4/4] Done! 
echo    Now restart Odoo and install the module.
echo.
pause



