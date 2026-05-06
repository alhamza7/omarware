# -*- coding: utf-8 -*-
{
    'name': 'Lugal Email',
    'version': '1.1.2',
    'category': 'Communication',
    'summary': 'IMAP/SMTP email engine for the Lugal suite — accounts, inbox, send, notifications',
    'description': """
Lugal Email
===========
Full email management module for the Lugal suite.

Features
--------
- lugal.email.account  — IMAP/SMTP account configuration per user
- lugal.email.message  — Stored/cached email messages
- /api/lugal/email/*   — REST HTTP API (Bearer-JWT auth)
- /api/crm/email/*     — CRM-context wrappers (JSON-RPC)
- /api/crm/settings/email/* — Settings CRUD (JSON-RPC)
""",
    'depends': ['base', 'mail', 'lugal_auth'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
