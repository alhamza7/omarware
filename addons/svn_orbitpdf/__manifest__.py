# -*- coding: utf-8 -*-
# Copyright 2025 Sveltware Solutions

{
    'name': 'OrbitPDF Document Engine',
    'category': 'Extra Tools',
    'summary': 'The next-generation HTML-to-PDF engine, foundation for document rendering in Odoo, bringing next-generation PDF engines into real-world deployments without disrupting existing QWeb templates, built on PlutoPrint. PDF reports, pdf watermark, pdf print, export pdf, direct print, template report, accounting reports, financial reports, account financial reports, general ledger, cash book, day book, bank book financial reports, VAT reports, POS reports, POS print, POS receipt design, payslip report, print journal entries, attendance dashboard.',
    'version': '1.0.0',
    'license': 'Other OSI approved licence',
    'author': 'Sveltware Solutions',
    'website': 'https://www.linkedin.com/in/sveltware',
    'images': [
        'static/description/banner.png',
    ],
    'depends': ['web'],
    'external_dependencies': {
        'python': ['plutoprint'],
    },
    'data': [
        'data/paperformat_data.xml',
        'views/report_paperformat.xml',
        'views/ir_actions.xml',
    ],
}
