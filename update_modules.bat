@echo off
REM Update SAP Integration, POS Perfume, Multi Warehouse, and UOM in Pricelist modules

cd /d L:\Lugal-ai

echo ========================================
echo Updating Modules...
echo ========================================
echo.

echo Stopping any running Odoo processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *odoo*" 2>nul

echo.
echo Starting Odoo with module updates...
echo.

venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070 -u sap_integration,pos_perfume_custom,sale_order_line_multi_warehouse,uom_in_pricelist --dev=reload

pause

