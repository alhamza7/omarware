#!/bin/bash

echo "============================================"
echo "Installing NBS Archive Missing Dependencies"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# System packages for OCR
echo -e "${YELLOW}Installing system packages for OCR...${NC}"
sudo apt update
sudo apt install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-eng \
    poppler-utils \
    libpoppler-cpp-dev

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ System packages installed${NC}"
else
    echo -e "${RED}❌ Failed to install system packages${NC}"
    exit 1
fi

echo ""

# Python packages
echo -e "${YELLOW}Installing Python packages...${NC}"
./venv/bin/pip install \
    pytesseract \
    pdf2image \
    python-barcode \
    Pillow

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Python packages installed${NC}"
else
    echo -e "${RED}❌ Failed to install Python packages${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✅ All dependencies installed successfully!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Next steps:"
echo "1. Restart Odoo: pkill -f odoo-bin && ./start_local.sh"
echo "2. Test OCR API: POST /api/documents/ocr"
echo "3. Test Barcode API: POST /api/documents/generate-barcode"
echo ""
