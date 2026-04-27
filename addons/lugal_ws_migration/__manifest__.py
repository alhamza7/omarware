{
    'name': 'Lugal WS Migration',
    'version': '1.0.0',
    'summary': 'WebSocket migration layer — sandbox/migration branch only',
    'description': """
        Provides:
          - Session bridge: POST /api/crm/ws/session (JWT → Odoo session)
          - Feature flag:   GET  /api/crm/ws/config
          - _build_bus_channel_list() override for supply chat/stories/email channels
          - Phase 4: lugal.email.message create hook → crm.email.message.new bus event

        NEVER install on lugal_local. Sandbox (lugal_ws_sandbox) only.
        Completely inert unless installed — does not affect dev or production.
    """,
    'depends': ['bus', 'lugal_crm', 'lugal_auth'],
    'data': [
        'security/ir.model.access.csv',
        'data/ws_config.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
