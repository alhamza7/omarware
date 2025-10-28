@echo off
echo ================================================
echo   UPGRADING POS PERFUME MODULE
echo ================================================
echo.
echo Please STOP Odoo first (Ctrl+C in the terminal)
echo Then run this script
echo.
pause

echo.
echo Starting upgrade...
echo.

python odoo-bin -u pos_perfume_custom -d your_database_name --stop-after-init

echo.
echo ================================================
echo   UPGRADE COMPLETE!
echo ================================================
echo.
echo Now start Odoo again:
echo   python odoo-bin -c odoo.conf
echo.
pause




