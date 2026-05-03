#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     تثبيت جميع المكتبات المطلوبة لـ Odoo                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai

echo -e "${YELLOW}جاري تثبيت جميع المكتبات...${NC}"
echo ""

./venv/bin/pip install \
    psycopg2-binary \
    Babel \
    chardet \
    cryptography \
    decorator \
    docutils \
    ebaysdk \
    freezegun \
    geoip2 \
    gevent \
    greenlet \
    idna \
    Jinja2 \
    libsass \
    lxml \
    lxml_html_clean \
    MarkupSafe \
    num2words \
    ofxparse \
    passlib \
    Pillow \
    polib \
    psutil \
    pydot \
    pyparsing \
    PyPDF2 \
    pyserial \
    python-dateutil \
    python-stdnum \
    pytz \
    pyusb \
    qrcode \
    reportlab \
    requests \
    rjsmin \
    urllib3 \
    vobject \
    Werkzeug \
    xlrd \
    XlsxWriter \
    xlwt \
    zeep \
    opensearch-py \
    PyJWT \
    pyOpenSSL \
    cbor2 \
    pynacl \
    cachetools \
    asn1crypto \
    --quiet

echo ""
echo -e "${GREEN}✅ تم تثبيت جميع المكتبات${NC}"
echo ""
echo -e "${YELLOW}التحقق من التثبيت...${NC}"
echo ""

./venv/bin/python -c "
import sys
packages = [
    'babel', 'psycopg2', 'lxml', 'Pillow', 'werkzeug',
    'OpenSSL', 'cbor2', 'nacl', 'cachetools', 'asn1crypto'
]
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg}')
    except:
        print(f'❌ {pkg}')
        sys.exit(1)
"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 ✅ اكتمل التثبيت!                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
