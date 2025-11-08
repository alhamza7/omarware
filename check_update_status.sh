#!/bin/bash
# Check if Odoo module update is complete

echo "========================================"
echo "Checking Odoo Update Status..."
echo "========================================"
echo ""

# Method 1: Check log file for completion messages
echo "1. Checking log file for update completion..."
if [ -f "odoo.log" ]; then
    echo "   Looking for 'Module updated' or 'Upgrade finished' messages..."
    tail -n 50 odoo.log | grep -i "module.*updated\|upgrade.*finished\|loading.*module" | tail -5
else
    echo "   Log file not found at odoo.log"
fi

echo ""
echo "2. Checking for errors in log..."
if [ -f "odoo.log" ]; then
    ERROR_COUNT=$(tail -n 100 odoo.log | grep -i "error\|exception\|traceback" | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "   ⚠️  Found $ERROR_COUNT potential errors in last 100 lines"
        echo "   Recent errors:"
        tail -n 100 odoo.log | grep -i "error\|exception" | tail -3
    else
        echo "   ✅ No errors found in recent log"
    fi
fi

echo ""
echo "3. Checking if Odoo process is running..."
if pgrep -f "odoo-bin.*lugal" > /dev/null; then
    echo "   ✅ Odoo process is running"
    echo "   Process info:"
    ps aux | grep "odoo-bin.*lugal" | grep -v grep | head -1
else
    echo "   ⚠️  Odoo process not found"
fi

echo ""
echo "4. Checking database for updated modules..."
echo "   Run this SQL query in PostgreSQL:"
echo "   SELECT name, state, latest_version FROM ir_module_module WHERE name IN ('sap_integration', 'pos_perfume_custom', 'sale_order_line_multi_warehouse', 'uom_in_pricelist');"
echo ""

echo "========================================"
echo "Update Status Check Complete"
echo "========================================"

