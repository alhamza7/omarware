#!/bin/bash

# Lugal NBS ERP - Local Installation Script
# This script automates the installation of a local development environment

set -e  # Exit on error

echo "============================================================"
echo "Lugal NBS ERP - Local Installation"
echo "============================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "🖥️  Detected OS: $MACHINE"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "1. Checking prerequisites..."
echo ""

# Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo "   ✅ Python: $PYTHON_VERSION"
else
    echo "   ❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# PostgreSQL
if command_exists psql; then
    PG_VERSION=$(psql --version | awk '{print $3}')
    echo "   ✅ PostgreSQL: $PG_VERSION"
else
    echo "   ❌ PostgreSQL not found. Please install PostgreSQL 13+"
    exit 1
fi

# Git
if command_exists git; then
    GIT_VERSION=$(git --version | awk '{print $3}')
    echo "   ✅ Git: $GIT_VERSION"
else
    echo "   ❌ Git not found. Please install Git"
    exit 1
fi

echo ""

# Ask for database name
read -p "Enter database name [lugal_dev]: " DB_NAME
DB_NAME=${DB_NAME:-lugal_dev}

read -p "Enter HTTP port [8069]: " HTTP_PORT
HTTP_PORT=${HTTP_PORT:-8069}

read -p "Enter admin password [admin]: " ADMIN_PASS
ADMIN_PASS=${ADMIN_PASS:-admin}

echo ""
echo "2. Setting up virtual environment..."

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
else
    echo "   ℹ️  Virtual environment already exists"
fi

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo "   ✅ pip upgraded"

echo ""
echo "3. Installing Python dependencies..."

pip install -r requirements.txt
echo "   ✅ Dependencies installed"

echo ""
echo "4. Setting up PostgreSQL database..."

# Check if database exists
if psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "   ⚠️  Database '$DB_NAME' already exists"
    read -p "   Drop and recreate? (y/N): " DROP_DB
    if [ "$DROP_DB" = "y" ] || [ "$DROP_DB" = "Y" ]; then
        dropdb $DB_NAME
        createdb $DB_NAME
        echo "   ✅ Database recreated"
    fi
else
    createdb $DB_NAME
    echo "   ✅ Database created"
fi

echo ""
echo "5. Creating configuration file..."

# Create odoo_local.conf
cat > odoo_local.conf << EOF
[options]
# Basic settings
addons_path = addons,odoo/addons
data_dir = ./filestore
db_host = localhost
db_port = 5432
db_user = $USER
db_password = False
dbfilter = .*

# Ports
http_port = $HTTP_PORT
longpolling_port = 8072

# Performance
workers = 2
max_cron_threads = 2
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_request = 8192
limit_time_cpu = 600
limit_time_real = 1200

# Logging
logfile = odoo_local.log
log_level = info

# Development
dev_mode = reload
EOF

echo "   ✅ Configuration file created: odoo_local.conf"

echo ""
echo "6. Initializing Odoo database..."

# Initialize database with base modules
./venv/bin/python odoo-bin -c odoo_local.conf -d $DB_NAME \
    -i base,web --stop-after-init \
    --without-demo=all

echo "   ✅ Base modules installed"

echo ""
echo "7. Installing custom modules..."

# Install custom modules
./venv/bin/python odoo-bin -c odoo_local.conf -d $DB_NAME \
    -i nbs_archive,sap_integration,pos_perfume_custom,lugal_fragrantica \
    --stop-after-init

echo "   ✅ Custom modules installed"

echo ""
echo "8. Setting up admin user..."

# Set admin password using SQL
psql $DB_NAME << EOF
UPDATE res_users 
SET password = '$ADMIN_PASS' 
WHERE login = 'admin';
EOF

echo "   ✅ Admin password set"

echo ""
echo "9. Setting up exchange rate..."

./venv/bin/python update_exchange_rate.py 1500 || echo "   ⚠️  Exchange rate script not run (optional)"

echo ""
echo "============================================================"
echo "✅ Installation Complete!"
echo "============================================================"
echo ""
echo "📊 Installation Summary:"
echo "   Database: $DB_NAME"
echo "   HTTP Port: $HTTP_PORT"
echo "   Admin User: admin"
echo "   Admin Pass: $ADMIN_PASS"
echo ""
echo "🚀 To start Odoo:"
echo "   ./venv/bin/python odoo-bin -c odoo_local.conf -d $DB_NAME"
echo ""
echo "🌐 Access the system at:"
echo "   http://localhost:$HTTP_PORT"
echo ""
echo "📝 View logs:"
echo "   tail -f odoo_local.log"
echo ""
echo "🛠️  Development mode:"
echo "   ./venv/bin/python odoo-bin -c odoo_local.conf -d $DB_NAME --dev=all"
echo ""
