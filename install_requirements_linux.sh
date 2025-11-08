#!/bin/bash
# Install required Python packages for Odoo on Linux

echo "========================================"
echo "Installing Odoo Requirements..."
echo "========================================"
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

echo ""
echo "Upgrading pip..."
pip install --upgrade pip

echo ""
echo "Installing required packages..."
pip install passlib
pip install psycopg2-binary
pip install python-dateutil
pip install babel
pip install pytz
pip install lxml
pip install werkzeug
pip install decorator
pip install requests
pip install pillow
pip install reportlab
pip install cachetools

echo ""
echo "Or install all requirements from requirements.txt if exists..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"

