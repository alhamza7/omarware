#!/bin/bash

# Stop any existing Odoo instances
pkill -f "odoo-bin" 2>/dev/null || true
sleep 2

clear
echo "╔════════════════════════════════════════════════════════════╗"
echo "║          Starting Lugal NBS ERP - Local Version            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "  📊 Database: lugal_local"
echo "  🌐 URL:      http://localhost:8070"
echo "  👤 User:     admin"
echo "  🔑 Password: admin"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "Starting Odoo..."
echo "════════════════════════════════════════════════════════════"
echo ""

cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
./venv/bin/python odoo-bin -c odoo_local.conf --dev=all

echo ""
echo "════════════════════════════════════════════════════════════"
echo "Odoo stopped."
echo "════════════════════════════════════════════════════════════"
