# Custom Pricelist Packaging Module

## Overview
This module extends Odoo's pricelist functionality to support packaging-based pricing. It allows you to set fixed prices for specific product packaging types within pricelist items.

## Features
- Add "Product Packaging" field to pricelist items
- Set fixed prices for specific packaging types
- Automatically apply packaging prices in sales orders
- Fallback to default price × packaging quantity factor if no packaging price is defined

## Installation
1. Copy the module to your Odoo addons directory
2. Update the apps list in Odoo
3. Install the module "Custom Pricelist Packaging"

## Usage

### Setting up Packaging Prices in Pricelist
1. Go to **Sales > Configuration > Pricelists**
2. Open a pricelist and click on **Items** tab
3. Create or edit a pricelist item
4. Select a **Product** (or Product Template)
5. Select a **Product Packaging** from the dropdown
6. Set **Price Type** to "Fixed Price"
7. Enter the **Fixed Price** for this packaging
8. Save

### Using Packaging Prices in Sales Orders
1. Create a new Sales Order
2. Add a product line
3. Select a **Product Packaging** (if available for the product)
4. The system will automatically:
   - Apply the packaging-specific price if defined in the pricelist
   - Otherwise, use the default product price × packaging quantity factor

## Technical Details

### Models Extended
- `product.pricelist.item`: Added `product_packaging_id` field
- `sale.order.line`: Added `product_packaging_id` field and pricing logic

### Dependencies
- `product`
- `sale_management`

## Compatibility
- Odoo 19.0
- Built using inheritance (no core modifications)

## License
LGPL-3


