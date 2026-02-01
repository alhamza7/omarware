#!/bin/bash

cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai

echo "============================================================"
echo "Starting Lugal NBS ERP - Local Version"
echo "============================================================"
echo ""
echo "Database: lugal_local"
echo "Port: http://localhost:8070"
echo "User: admin"
echo "Pass: admin"
echo ""
echo "Starting Odoo..."
echo ""

./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_local --dev=all

echo ""
echo "Odoo stopped."
