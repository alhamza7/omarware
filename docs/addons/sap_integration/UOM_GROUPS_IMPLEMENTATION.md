# SAP UoM Groups Integration in Odoo

## 📋 Overview

This enhancement adds SAP UoM (Unit of Measure) Groups functionality to Odoo, restricting UoM selection in sale orders to only the UoMs that belong to the product's SAP UoM Group.

## 🎯 What Was Implemented

### 1. **Product Template Extension** (`product_template_uom.py`)
Added fields to `product.template` and `product.product`:
- `sap_uom_group_id`: Link to SAP UoM Group
- `sap_uom_group_entry`: SAP AbsEntry number
- `available_product_uom_ids`: Computed list of allowed UoMs

### 2. **SAP Product Extended** (`sap_product_extended.py`)
Added fields to `sap.product.extended`:
- `sap_uom_group_id`: Direct link to UoM Group
- `sap_uom_group_entry`: SAP entry number

Modified `_prepare_extended_values_from_sap()` to:
- Read `UoMGroupEntry` from SAP
- Link product to corresponding `sap.uom.group`
- Log warnings if group not found

### 3. **Sale Order Line Restriction** (`sale_order_line_uom.py`)
Extended `sale.order.line` with:
- `available_uom_ids`: Computed field that gets UoMs from product's UoM Group
- `sap_uom_group_id`: Related field for display
- Modified `product_uom_id` domain to restrict selection: `[('id', 'in', available_uom_ids)]`
- Auto-reset UoM when product changes if current UoM not in allowed list

**Fallback Behavior:**
- If product has NO UoM Group → All UoMs allowed
- If UoM Group has NO UoMs → All UoMs allowed (with warning)

### 4. **Views** (`product_uom_group_views.xml`)
Added XML views:
- Product Template form: Shows UoM Group after `uom_id` field
- Product Template notebook: Detailed UoM Group info page
- Sale Order Line: Domain restriction on `product_uom_id`

## 📊 How It Works

```
SAP B1 Item
  └─> UoMGroupEntry (e.g., 5)
       │
       ▼
  sap.uom.group (AbsEntry: 5, Name: "Beverages")
       ├─> sap.uom.sync (Entry: 101, Code: "0.5L", UoM: "0.5 ميلو")
       ├─> sap.uom.sync (Entry: 102, Code: "1L", UoM: "كغم")
       └─> sap.uom.sync (Entry: 103, Code: "0.25L", UoM: "0.25 كغم بلاستك")
       │
       ▼
product.template (via sap.product.extended)
  └─> sap_uom_group_id = 5
       │
       ▼
sale.order.line
  └─> available_uom_ids = [0.5 ميلو, كغم, 0.25 كغم بلاستك]
  └─> product_uom_id restricted to these UoMs only
```

## 🔄 Complete Migration Flow

When running Complete Migration from SAP:

1. **Fetch Item from SAP** → Get `UoMGroupEntry`
2. **Import Product** → Create/update `product.product`
3. **Import Extended Info** → Create/update `sap.product.extended`
   - Save `UoMGroupEntry`
   - Search for `sap.uom.group` by `sap_abs_entry`
   - Link product to group if found
4. **Sale Order** → User can only select UoMs from that group

## ✨ Features

### ✅ What Works:
- ✅ Products are linked to SAP UoM Groups during migration
- ✅ Sale order lines restrict UoM selection based on product's group
- ✅ Fallback to all UoMs if product has no group
- ✅ UI shows UoM Group info in product form
- ✅ Automatic UoM reset when product changes
- ✅ **No modifications to Odoo core** - everything is in `sap_integration` module

### 🎛️ Configuration:
- **Automatic**: Products get UoM Groups from SAP during Complete Migration
- **Manual**: Can assign UoM Group in product form (will appear after first sync)
- **Sync UoM Groups**: Use "SAP → UoM Management → UoM Groups" menu

## 📝 Files Created/Modified

### New Files:
1. `addons/sap_integration/models/product_template_uom.py` - Product template extension
2. `addons/sap_integration/models/sale_order_line_uom.py` - Sale order line restriction
3. `addons/sap_integration/views/product_uom_group_views.xml` - Views

### Modified Files:
1. `addons/sap_integration/models/sap_product_extended.py` - Added UoM Group fields + linking
2. `addons/sap_integration/models/__init__.py` - Imported new models
3. `addons/sap_integration/__manifest__.py` - Added new view file

## 🧪 Testing

To test the implementation:

1. **Sync UoM Groups from SAP** (if not done):
   ```
   SAP Integration → UoM Management → UoM Groups → Import from SAP
   ```

2. **Run Complete Migration**:
   ```
   SAP Integration → Products → Complete Product Migration
   ```
   - Check logs for "Linked product to UoM Group" messages

3. **Verify in Product Form**:
   - Open any product
   - Check if `SAP UoM Group` field appears after `Unit of Measure`
   - Go to "SAP UoM Group" tab to see available UoMs

4. **Test in Sale Order**:
   - Create new sale order
   - Add product line
   - Click on UoM dropdown
   - Should see ONLY UoMs from that product's UoM Group
   - Try selecting a different UoM - should be restricted

## 🔍 Troubleshooting

### Problem: "UoM Group with Entry X not found"
**Solution**: Sync UoM Groups first:
```
SAP Integration → UoM Management → UoM Groups → Import from SAP
```

### Problem: "All UoMs still available in sale order"
**Reason**: Product has no UoM Group (fallback behavior)
**Solution**: 
1. Check if product has `sap_uom_group_id` set
2. Re-run Complete Migration for that product
3. Manually assign UoM Group in product form

### Problem: "UoM dropdown is empty"
**Reason**: UoM Group has no UoMs linked
**Solution**:
1. Open UoM Group form
2. Click "Sync from SAP" button
3. Check if UoMs appear in "UoMs in Group" tab

## 📚 Technical Notes

- **No Core Modifications**: All changes are in `sap_integration` module
- **Backward Compatible**: Products without UoM Groups work as before
- **Performance**: `available_uom_ids` is computed on-demand (not stored)
- **Multi-Backend**: Supports multiple SAP backends (uses `backend_id`)

## 🎯 Next Steps

Possible enhancements:
1. **Bulk UoM Group Assignment**: Wizard to assign groups to multiple products
2. **UoM Group Validation**: Warning if product UoM not in group
3. **Purchase Orders**: Extend same restriction to purchase orders
4. **Inventory Moves**: Restrict UoM in stock moves

---

**Module**: `sap_integration`  
**Version**: 2.0.0+  
**Compatible with**: Odoo 19.0  
**Date**: November 2025


