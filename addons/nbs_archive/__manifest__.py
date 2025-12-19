# -*- coding: utf-8 -*-
{
    'name': 'NBS Archive System',
    'version': '1.0.0',
    'category': 'Document Management',
    'summary': 'Enterprise Document Archiving System for Noor Al Nibras (NBS)',
    'description': """
NBS Archive System
==================

Complete enterprise document management and archiving system featuring:

* **Department-based document management** with isolation
* **Advanced search** with OCR support (Arabic + English)
* **Version control** with approval workflow
* **Barcode generation** and scanning
* **Audit logging** for all operations
* **REST API** for external integrations
* **Bilingual support** (Arabic RTL + English)
* **Real-time notifications** via WebSocket
* **OpenSearch integration** for full-text search
* **No hard delete** - archive only policy

Designed for FMCG companies with strict compliance requirements.
    """,
    'author': 'NBS IT Team',
    'website': 'https://nbs.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
    ],
    'data': [
        # Security
        'security/nbs_security.xml',
        'security/ir.model.access.csv',
        'security/nbs_record_rules.xml',
        
        # Data
        'data/ir_sequence_data.xml',
        'data/nbs_admin_setup.xml',
        'data/nbs_department_data.xml',
        'data/nbs_document_type_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

