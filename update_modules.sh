#!/bin/bash
# Update SAP Integration, POS Perfume, Multi Warehouse, and UOM in Pricelist modules

cd L:\Lugal-ai

echo "========================================"
echo "Updating Modules..."
echo "========================================"
echo ""

echo "Stopping any running Odoo processes..."
pkill -f "odoo-bin.*lugal" 2>/dev/null

echo ""
echo "Starting Odoo with module updates..."
echo ""

venv/bin/python odoo-bin -c odoo.conf -d lugal --http-port=8070 -u sap_integration,pos_perfume_custom,sale_order_line_multi_warehouse,uom_in_pricelist --dev=reload

