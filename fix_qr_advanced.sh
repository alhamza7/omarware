#!/bin/bash
# Advanced fix for QR code generation in reportlab
# Run this script on the server: bash fix_qr_advanced.sh

echo "=========================================="
echo "Advanced QR Code Fix for Reportlab"
echo "=========================================="

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Step 1: Activating virtual environment...${NC}"
source /home/lugalai/Lugal-ai/venv/bin/activate

echo -e "${YELLOW}Step 2: Checking current reportlab installation...${NC}"
pip show reportlab

echo -e "${YELLOW}Step 3: Installing additional Cairo dependencies...${NC}"
sudo apt-get install -y \
    libgirepository1.0-dev \
    gir1.2-gtk-3.0 \
    python3-cairo \
    python3-gi \
    python3-gi-cairo

echo -e "${YELLOW}Step 4: Uninstalling and reinstalling reportlab with renderPM support...${NC}"
pip uninstall -y reportlab
pip install --no-cache-dir reportlab

echo -e "${YELLOW}Step 5: Trying alternative: Install reportlab with rlPyCairo from source...${NC}"
pip install --upgrade --force-reinstall pycairo

echo -e "${YELLOW}Step 6: Check if _rl_renderPM module exists...${NC}"
python3 << 'PYEOF'
import sys
print("Python path:", sys.path)
print("\nTrying to import renderPM backends:")

try:
    import rlPyCairo
    print("✓ rlPyCairo found")
except ImportError as e:
    print(f"✗ rlPyCairo not found: {e}")

try:
    import _rl_renderPM
    print("✓ _rl_renderPM found")
except ImportError as e:
    print(f"✗ _rl_renderPM not found: {e}")

try:
    import cairo
    print(f"✓ cairo found (version: {cairo.version})")
except ImportError as e:
    print(f"✗ cairo not found: {e}")
PYEOF

echo -e "${YELLOW}Step 7: Trying to build reportlab from source with renderPM...${NC}"
pip install --no-binary reportlab reportlab

echo -e "${YELLOW}Step 8: Alternative solution - Install python3-reportlab system package...${NC}"
sudo apt-get install -y python3-reportlab

echo -e "${YELLOW}Step 9: Final test with PIL backend (fallback)...${NC}"
python3 << 'PYEOF'
import os
os.environ['REPORTLAB_RENDERPM'] = 'pil'  # Force PIL backend

try:
    from reportlab.graphics.barcode import createBarcodeDrawing
    barcode = createBarcodeDrawing('QR', value='TEST|12345', format='png', width=300, height=300)
    png_data = barcode.asString('png')
    print("✓ QR Code generation with PIL backend PASSED")
    print("\nSolution: Use PIL backend by setting environment variable")
    exit(0)
except Exception as e:
    print(f"✗ QR Code generation FAILED: {e}")
    exit(1)
PYEOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo -e "✓ Solution found!"
    echo -e "=========================================="
    echo ""
    echo -e "${YELLOW}Next step: Add environment variable to Odoo startup${NC}"
    echo ""
    echo "Add this line to your Odoo startup script or systemd service:"
    echo ""
    echo -e "${GREEN}export REPORTLAB_RENDERPM=pil${NC}"
    echo ""
    echo "Or add to odoo.conf:"
    echo "[options]"
    echo "# ... other options ..."
    echo ""
    echo "Then restart Odoo"
else
    echo -e "${RED}=========================================="
    echo -e "Still having issues..."
    echo -e "=========================================="
fi

