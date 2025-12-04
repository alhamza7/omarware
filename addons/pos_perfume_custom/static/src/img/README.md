# NBS Invoice Images

## Required Images for NBS Invoice Template

To complete the NBS invoice design, you need to add two image files in this directory:

### 1. Header Image: `nbs_header.png`
- **Dimensions**: 777px × 160px
- **Content**: 
  - NBS logo on the left
  - Arabic company name "شركة نور الانبراس للتجارة العامة" on the right
  - "Noor Alnibras For General Trading" text below the Arabic name
- **File format**: PNG (transparent background recommended)
- **Location**: Copy from HTML template image or scan from existing invoice

### 2. Footer Image: `nbs_footer.png`
- **Dimensions**: 778px × 46px  
- **Content**: 
  - Company contact information and branding
  - Footer design from the HTML template
- **File format**: PNG (transparent background recommended)
- **Location**: Copy from HTML template image or scan from existing invoice

## How to Add the Images

1. Extract images from the HTML template:
   - `InvoiceLogo 2023_3A1B1F3E-B98E-42B5-9691-AAA8FBAD8264_.png` → rename to `nbs_header.png`
   - `InvoiceLogo 2023_4E4FEFA1-9A9A-4233-BE01-CC379475C5C5_.png` → rename to `nbs_footer.png`

2. Copy the renamed images to this directory:
   ```
   addons/pos_perfume_custom/static/src/img/
   ```

3. Restart Odoo server and update the module:
   ```bash
   cd L:\Lugal-ai
   venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070 -u pos_perfume_custom
   ```

## Alternative: Create Images from Existing HTML

If you want to extract the images from the HTML file:

1. Open `html/InvoiceLogo 20231.html` in a web browser
2. Right-click on the header/footer images
3. Save them as PNG files
4. Rename and place them in this directory

## Verify Installation

After adding the images:
1. Go to POS Perfume Orders in Odoo
2. Open any order
3. Click "Print" → "فاتورة NBS - طلب العطور"
4. The invoice should display with the header and footer images

## Troubleshooting

If images don't appear:
- Check file permissions (should be readable)
- Verify file names match exactly: `nbs_header.png` and `nbs_footer.png`
- Clear browser cache and regenerate the report
- Check Odoo logs for any image loading errors






