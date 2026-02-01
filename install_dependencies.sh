#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          تثبيت متطلبات Odoo على Ubuntu/Debian             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "هذا السكريبت سيثبت جميع المكتبات المطلوبة لتشغيل Odoo"
echo "سيطلب منك كلمة سر sudo"
echo ""
read -p "هل تريد المتابعة? (y/N): " CONTINUE

if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
    echo "❌ تم الإلغاء"
    exit 0
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "1️⃣  تحديث قوائم الحزم..."
echo "════════════════════════════════════════════════════════════"
echo ""

sudo apt update

echo ""
echo "════════════════════════════════════════════════════════════"
echo "2️⃣  تثبيت Python و PostgreSQL..."
echo "════════════════════════════════════════════════════════════"
echo ""

sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3.12-venv \
    postgresql \
    postgresql-contrib \
    libpq-dev

echo ""
echo "════════════════════════════════════════════════════════════"
echo "3️⃣  تثبيت مكتبات التطوير..."
echo "════════════════════════════════════════════════════════════"
echo ""

sudo apt install -y \
    build-essential \
    git \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    tcl8.6-dev \
    tk8.6-dev \
    libssl-dev \
    libffi-dev

echo ""
echo "════════════════════════════════════════════════════════════"
echo "4️⃣  تثبيت أدوات إضافية..."
echo "════════════════════════════════════════════════════════════"
echo ""

sudo apt install -y \
    wkhtmltopdf \
    node-less \
    npm

echo ""
echo "════════════════════════════════════════════════════════════"
echo "5️⃣  إعداد PostgreSQL..."
echo "════════════════════════════════════════════════════════════"
echo ""

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create PostgreSQL user
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='capo7amzah'" | grep -q 1; then
    echo "✅ مستخدم PostgreSQL موجود مسبقاً"
else
    sudo -u postgres createuser -s capo7amzah
    echo "✅ تم إنشاء مستخدم PostgreSQL: capo7amzah"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   ✅ اكتمل التثبيت!                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🎉 تم تثبيت جميع المتطلبات بنجاح!"
echo ""
echo "الآن يمكنك تشغيل:"
echo ""
echo "  bash setup_local_complete.sh"
echo ""
