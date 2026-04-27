# SAP Integration Points - Product Label Designer

## Overview
This document outlines how `product_label_designer` module integrates with the existing `sap_integration` module.

---

## Integration Architecture

```
product_label_designer
    ↓ depends on
sap_integration
    ↓ connects to
SAP Business One Service Layer API
```

---

## Key Integration Points

### 1. Model: `product.label.template`

**File**: `addons/product_label_designer/models/product_label.py`

#### New Fields Added:
```python
sap_mode_enabled = fields.Boolean('Enable SAP Mode')
sap_backend_id = fields.Many2one('sap.backend', 'SAP Backend')
show_sap_uom = fields.Boolean('Show SAP Unit of Measure')
sap_uom_format = fields.Selection([...], 'UoM Format')
# ... position and styling fields for SAP elements
```

#### Key Method:
```python
def get_sap_product_info(self, barcode):
    """
    Get product information from SAP by barcode using existing sap_integration module
    
    Process:
    1. Validates SAP mode is enabled and backend is configured
    2. Gets SAP connection from sap_backend_id
    3. Searches SAP Items by barcode (BarCode field or ItemCode field)
    4. Extracts product data (ItemName, SalesUnit, Price, etc.)
    5. Creates or updates product in Odoo
    6. Returns product info for printing
    """
```

**SAP API Call**:
```python
connection.get('Items', params={
    '$filter': f"BarCode eq '{barcode}' or ItemCode eq '{barcode}'",
    '$top': 1
})
```

---

### 2. Model: `product.product`

**New Method**:
```python
@api.model
def get_sap_product_info_from_barcode(self, barcode):
    """
    Public method callable via RPC from web interface.
    Finds first SAP-enabled template and uses its SAP connection.
    """
```

**New Fields**:
```python
sap_product_name = fields.Char('SAP Product Name', readonly=True)
sap_uom = fields.Char('SAP Unit of Measure', readonly=True)
last_sap_sync = fields.Datetime('Last SAP Sync', readonly=True)
```

---

### 3. Controller: `LabelDesignerController`

**File**: `addons/product_label_designer/controllers/label_designer.py`

#### Route: `/sap/label/lookup`
```python
@http.route('/sap/label/lookup', type='json', auth='user', methods=['POST'], csrf=False)
def sap_product_lookup(self, barcode, template_id):
    """
    AJAX endpoint for barcode scanning interface
    
    Flow:
    1. Receives barcode and template_id from web UI
    2. Calls template.get_sap_product_info(barcode)
    3. Returns product data and print URL
    """
```

**Request**:
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "barcode": "1234567890",
        "template_id": 1
    }
}
```

**Response (Success)**:
```json
{
    "success": true,
    "product_id": 123,
    "product_name": "Product Name from Odoo",
    "sap_product_name": "Product Name from SAP",
    "sap_uom": "PCS",
    "barcode": "1234567890",
    "print_url": "/report/pdf/product_label_designer.report_label_simple/123?template_id=1"
}
```

**Response (Error)**:
```json
{
    "success": false,
    "error": "Product with barcode 1234567890 not found in SAP"
}
```

---

### 4. Views: Label Template Form

**File**: `addons/product_label_designer/views/product_label_views.xml`

**New Page in Template Form**:
```xml
<page string="SAP Integration" name="sap_integration">
    <group>
        <field name="sap_mode_enabled"/>
        <field name="sap_backend_id" 
               domain="[('active', '=', True)]"
               required="sap_mode_enabled"/>
        <field name="show_sap_uom"/>
        <field name="sap_uom_format"/>
    </group>
    <!-- Position and styling fields for SAP elements -->
</page>
```

---

### 5. Continuous Printing Interface

**File**: `addons/product_label_designer/views/sap_label_printer_interface.xml`

**JavaScript Integration**:
```javascript
$('#barcode_input').on('keypress', function(e) {
    if (e.which === 13) { // Enter key
        var barcode = $(this).val();
        var templateId = $('#template_select').val();
        
        // Call /sap/label/lookup via RPC
        odoo.rpc('/sap/label/lookup', {
            barcode: barcode,
            template_id: templateId
        }).then(function(result) {
            if (result.success) {
                // Display product info
                // Trigger auto-print
            }
        });
    }
});
```

---

## SAP Data Flow

### Barcode Scan → SAP → Odoo → Print

```
1. User scans barcode
   → JavaScript captures input
   
2. AJAX call to /sap/label/lookup
   → Controller: sap_product_lookup()
   
3. Template.get_sap_product_info(barcode)
   → backend.get_connection()
   → SapServiceLayerConnection.get('Items', ...)
   
4. SAP Service Layer API
   → GET /b1s/v1/Items?$filter=BarCode eq 'XXX' or ItemCode eq 'XXX'
   
5. SAP Response
   → {ItemCode, ItemName, SalesUnit, SalesUnitMeasure, Price, ...}
   
6. Odoo Processing
   → Find or create product.product
   → Update sap_product_name, sap_uom, last_sap_sync
   
7. Return to Web UI
   → Display product info
   → Generate PDF label
   → Auto-print
```

---

## SAP Backend Configuration

The module uses `sap.backend` records from `sap_integration` module:

**Model**: `sap.backend`  
**Required Fields**:
- `name`: Backend name
- `base_url`: SAP Service Layer URL (e.g., https://server:50000/b1s/v1)
- `username`: SAP username
- `password`: SAP password
- `company_db`: SAP company database name
- `active`: Must be True

**Connection Method**:
```python
backend = self.env['sap.backend'].browse(backend_id)
connection = backend.get_connection()  # Returns SapServiceLayerConnection instance
```

---

## SAP API Endpoints Used

### GET /Items
**Filter**: `BarCode eq '{barcode}' or ItemCode eq '{barcode}'`  
**Fields Retrieved**:
- `ItemCode`: Product code
- `ItemName`: Product name
- `BarCode`: Barcode
- `SalesUnit`: Sales unit code
- `SalesUnitMeasure`: Sales unit description
- `Price`: Product price
- `PurchasePrice`: Purchase price

---

## Error Handling

### Template Level
```python
if not self.sap_mode_enabled:
    return {'success': False, 'error': 'SAP mode not enabled'}

if not self.sap_backend_id:
    return {'success': False, 'error': 'No SAP backend configured'}

if not backend.active:
    return {'success': False, 'error': 'SAP backend is not active'}
```

### Connection Level
```python
try:
    connection = backend.get_connection()
    result = connection.get('Items', ...)
except Exception as e:
    return {'success': False, 'error': f'Error connecting to SAP: {str(e)}'}
```

### Not Found
```python
if not result or not result.get('value') or len(result['value']) == 0:
    return {'success': False, 'error': f'Product with barcode {barcode} not found in SAP'}
```

---

## Dependencies

**Manifest**: `addons/product_label_designer/__manifest__.py`

```python
'depends': [
    'product',
    'stock',
    'web',
    'base',
    'sap_integration',  # NEW DEPENDENCY
]
```

**Why No `requests`?**  
The module now relies on `sap_integration` which already handles HTTP requests to SAP Service Layer. No need for direct `requests` dependency.

---

## Benefits of This Integration

1. **Reuses Existing Infrastructure**: No need for duplicate SAP connection code
2. **Centralized Configuration**: All SAP backends managed in one place
3. **Connection Pooling**: `sap_integration` uses connection pooling for better performance
4. **Session Management**: Automatic session renewal and error handling
5. **Consistent Error Handling**: Uses proven error handling from `sap_integration`
6. **Security**: Credentials stored once in `sap.backend`, not per template
7. **Maintainability**: Changes to SAP connection logic only need to be made in `sap_integration`

---

## Testing

### Manual Test Flow

1. **Setup SAP Backend**:
   ```
   SAP Integration > Configuration > SAP Backends
   → Create or activate a backend
   → Test connection
   ```

2. **Configure Template**:
   ```
   Inventory > Product Labels > Label Templates
   → Open a template
   → SAP Integration tab
   → Enable SAP Mode
   → Select SAP Backend
   ```

3. **Test Barcode Lookup**:
   ```
   Inventory > Product Labels > SAP Label Printer
   → Select template
   → Scan a barcode that exists in SAP
   → Verify product info appears
   → Verify label prints
   ```

---

## Future Enhancements

- [ ] Support for multiple UoMs (UoMGroupEntry, sub-units)
- [ ] Batch printing (scan multiple, print all at once)
- [ ] Custom field mapping (allow user to choose which SAP fields to display)
- [ ] Offline mode (cache SAP data locally)
- [ ] Print queue management
- [ ] Integration with SAP item images

---

**Version**: 2.0  
**Last Updated**: December 2024  
**Developed By**: Lugal AI

