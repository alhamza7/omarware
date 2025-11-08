#!/bin/bash
# Update SAP Integration, POS Perfume, Multi Warehouse, and UOM in Pricelist modules
# For Linux Server

# Change to your Odoo directory (adjust path as needed)
cd /path/to/odoo

echo "========================================"
echo "Updating Modules..."
echo "========================================"
echo ""

echo "Stopping any running Odoo processes..."
pkill -f "odoo-bin.*lugal" 2>/dev/null || true

echo ""
echo "Starting Odoo with module updates..."
echo ""

# Adjust the path to your Python and odoo-bin
# If using virtual environment:
# source venv/bin/activate
# python3 odoo-bin -c odoo.conf -d lugal --http-port=8070 -u sap_integration,pos_perfume_custom,sale_order_line_multi_warehouse,uom_in_pricelist --dev=reload

# Or if using system Python:
python3 odoo-bin -c odoo.conf -d lugal --http-port=8070 -u sap_integration,pos_perfume_custom,sale_order_line_multi_warehouse,uom_in_pricelist --dev=reload

