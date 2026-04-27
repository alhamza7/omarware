# -*- coding: utf-8 -*-
{
    "name": "Lugal LocalSend Bridge",
    "version": "1.0.1",
    "category": "Tools",
    "summary": "Manage LocalSend devices and transfer sessions in Odoo",
    "description": """
Lugal LocalSend Bridge
======================
Initial module for integrating LocalSend workflows with Lugal.

Features
--------
- Register devices available in local networks
- Create and track transfer sessions between users/devices
- Track statuses and keep operational history
    """,
    "author": "NBS IT Team",
    "website": "https://nbs.com",
    "license": "LGPL-3",
    "depends": ["base", "mail", "lugal_auth"],
    "data": [
        "security/localsend_security.xml",
        "security/ir.model.access.csv",
        "views/localsend_device_views.xml",
        "views/localsend_transfer_views.xml",
        "views/localsend_menu.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
