# -*- coding: utf-8 -*-
{
    'name': 'Lugal Auth',
    'version': '1.1.2',
    'category': 'Technical',
    'summary': 'Centralized JWT authentication service for the Lugal suite',
    'description': """
Lugal Auth
==========

Lightweight, standalone JWT authentication module.
No business logic. No dependency on any other Lugal module.

Any Lugal module that needs JWT authentication depends on THIS module — not on
each other.  This keeps all business modules independently installable.

Features:
- lugal.jwt.service         — sign / verify access & refresh tokens (with jti)
- lugal.jwt.blacklist       — revoke tokens on logout / force-revoke
- lugal.auth.rate.limit     — brute-force protection on login endpoint
- /lugal/auth/login         — obtain tokens (rate-limited)
- /lugal/auth/refresh       — renew access token
- /lugal/auth/logout        — revoke current token immediately
- Cron: daily blacklist purge + rate-limit record cleanup
- Migration fallback: accepts tokens signed with legacy nbs_archive key
    """,
    'author': 'NBS IT Team',
    'website': 'https://nbs.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/auth_cron.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
