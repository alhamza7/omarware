# -*- coding: utf-8 -*-
{
    'name': 'Lugal Supply',
    'version': '1.0.1',
    'category': 'Inventory/Inventory',
    'summary': 'Vendors and containers — موردين وحاويات',
    'description': """
Lugal Supply
============

موديول منفصل للموردين والحاويات. أوامر الشراء (مشتريات) تبقى في lugal_crm وترتبط بالحاويات هنا.
- Containers / الحاويات: B/L, clearance, tracking, status (Searates)
- Vendors: استخدام res.partner (supplier_rank)
يُدخل إليه من نفس واجهة الـ CRM (نفس الـ API base).
    """,
    'author': 'NBS IT Team',
    'website': 'https://nbs.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'product'],
    'data': ['security/ir.model.access.csv'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
