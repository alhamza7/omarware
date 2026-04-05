#!/bin/bash
# Install qrcode library for Python
# Run this on the server

echo "Installing qrcode library..."
source /home/lugalai/Lugal-ai/venv/bin/activate
pip install qrcode[pil]

echo "Testing qrcode generation..."
python3 << 'PYEOF'
import qrcode
import io
import base64

# Generate QR code
qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data('TEST|12345')
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
buffer = io.BytesIO()
img.save(buffer, format='PNG')
buffer.seek(0)
img_base64 = base64.b64encode(buffer.read()).decode('ascii')
print("✓ QR Code generated successfully!")
print(f"Base64 length: {len(img_base64)}")
PYEOF

echo "Done! Now create a helper method in Odoo."

