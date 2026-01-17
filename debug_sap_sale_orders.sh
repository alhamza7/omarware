#!/bin/bash
# Script to monitor SAP Sale Order conversion issues

LOG_FILE="c:/Users/Capo/.cursor/projects/d-capo-dev-Lugal-ai/terminals/2.txt"

echo "=== 🔍 Monitoring SAP Sale Order Conversions ==="
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

# Monitor in real-time
tail -f "$LOG_FILE" | grep --line-buffered -E "(Sale Order Created|State changed from draft to sale|Converting quotation|Successfully converted|Error converting|Failed to convert|DocEntry|DocNum)" --color=always

