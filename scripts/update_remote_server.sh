#!/bin/bash
# تحديث الكود على السيرفر البعيد

echo "🔄 Pulling latest changes from GitHub..."
cd ~/Lugal-ai
git pull origin main

echo "✅ Code updated!"
echo ""
echo "📋 Next steps:"
echo "1. Restart Odoo or upgrade the modules: sap_integration and pos_perfume_custom"
echo "2. Test creating a new order with invoice_type"
echo ""
echo "في Odoo Web Interface:"
echo "   Apps → SAP Integration → Upgrade"
echo "   Apps → POS Perfume Custom → Upgrade"

