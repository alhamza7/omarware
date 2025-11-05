# -*- coding: utf-8 -*-

def run(env, pricelist_id, product_id, packaging_uom_id, qty=1.0):
    """Quick verifier for packaging pricing logic.

    Usage (odoo shell):
        from addons.custom_pricelist_packaging.scripts.check_pricing import run
        run(env, pricelist_id=1, product_id=42, packaging_uom_id=7, qty=1)
    """
    PricelistItem = env['product.pricelist.item']
    Product = env['product.product']
    UoM = env['uom.uom']
    Pricelist = env['product.pricelist']
    Partner = env['res.partner']
    SaleOrder = env['sale.order']
    SaleOrderLine = env['sale.order.line']

    pricelist = Pricelist.browse(pricelist_id)
    product = Product.browse(product_id)
    packaging = UoM.browse(packaging_uom_id)
    partner = Partner.search([], limit=1)

    assert pricelist.exists(), 'Invalid pricelist_id'
    assert product.exists(), 'Invalid product_id'
    assert packaging.exists(), 'Invalid packaging_uom_id'

    # Create transient order/line for accurate pricing
    order = SaleOrder.create({'partner_id': partner.id, 'pricelist_id': pricelist.id})
    line = SaleOrderLine.create({
        'order_id': order.id,
        'product_id': product.id,
        'product_uom_qty': qty,
    })
    line.product_packaging_id = packaging.id
    line._onchange_product_packaging_id()

    # Match rule manually (variant -> template -> packaging-only)
    rule = False
    if product.id:
        rule = PricelistItem.search([
            ('pricelist_id', '=', pricelist.id),
            ('product_packaging_id', '=', packaging.id),
            ('product_id', '=', product.id),
        ], limit=1, order='id DESC')
    if not rule:
        rule = PricelistItem.search([
            ('pricelist_id', '=', pricelist.id),
            ('product_packaging_id', '=', packaging.id),
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
        ], limit=1, order='id DESC')
    if not rule:
        rule = PricelistItem.search([
            ('pricelist_id', '=', pricelist.id),
            ('product_packaging_id', '=', packaging.id),
        ], limit=1, order='id DESC')

    # Price via our logic on the line
    computed_price = line._get_pricelist_price()

    details = {
        'pricelist_id': pricelist.id,
        'product_id': product.id,
        'packaging_uom_id': packaging.id,
        'line_uom_id': line.product_uom_id.id,
        'line_qty': line.product_uom_qty,
        'matched_rule_id': rule.id if rule else False,
        'matched_rule_type': rule.compute_price if rule else None,
        'matched_rule_fixed': rule.fixed_price if (rule and rule.compute_price == 'fixed') else None,
        'final_price': computed_price,
    }

    # Cleanup
    order.unlink()

    # Pretty print
    print('Packaging Pricing Check ->')
    for k, v in details.items():
        print(f'  {k}: {v}')

    return details




