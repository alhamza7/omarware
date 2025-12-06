#!/bin/bash
# Script to install QR code dependencies for Odoo reportlab
# Run this script on the server: bash install_qr_dependencies.sh

echo "=========================================="
echo "Installing QR Code Dependencies for Odoo"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Updating package lists...${NC}"
sudo apt-get update

echo -e "${YELLOW}Step 2: Installing system dependencies...${NC}"
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    libjpeg-dev \
    libfreetype6-dev \
    zlib1g-dev \
    libcairo2-dev \
    pkg-config \
    build-essential

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ System dependencies installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install system dependencies${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 3: Activating virtual environment...${NC}"
source /home/lugalai/Lugal-ai/venv/bin/activate

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}✗ Failed to activate virtual environment${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 4: Upgrading pip...${NC}"
pip install --upgrade pip

echo -e "${YELLOW}Step 5: Installing Python packages (pillow, pycairo)...${NC}"
pip install --upgrade pillow pycairo

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python packages installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install Python packages${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 6: Testing QR code generation...${NC}"
python3 << 'PYEOF'
try:
    from reportlab.graphics.barcode import createBarcodeDrawing
    barcode = createBarcodeDrawing('QR', value='TEST|12345', format='png', width=300, height=300)
    png_data = barcode.asString('png')
    print("✓ QR Code generation test PASSED")
    exit(0)
except Exception as e:
    print(f"✗ QR Code generation test FAILED: {e}")
    exit(1)
PYEOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo -e "✓ Installation completed successfully!"
    echo -e "=========================================="
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Restart Odoo service"
    echo "2. Upgrade the product_label_designer module"
    echo "3. Test QR code printing"
    echo ""
    echo -e "${YELLOW}To restart Odoo, run:${NC}"
    echo "  sudo systemctl restart odoo"
    echo "  OR"
    echo "  ps aux | grep odoo-bin"
    echo "  kill -9 <PID>"
    echo "  cd /home/lugalai/Lugal-ai"
    echo "  source venv/bin/activate"
    echo "  python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069"
else
    echo -e "${RED}=========================================="
    echo -e "✗ Installation failed!"
    echo -e "=========================================="
    echo ""
    echo -e "${YELLOW}Please check the error messages above${NC}"
    exit 1
fi

