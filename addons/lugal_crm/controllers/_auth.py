# -*- coding: utf-8 -*-
# JWT guard helpers for lugal_crm.
# Delegates to lugal_auth._auth — keeping this file as a thin re-export so
# that all existing controllers in lugal_crm keep their current import path.

from odoo.addons.lugal_auth.controllers._auth import (
    _verify_jwt_token,
    ensure_jwt_user_id,
)

__all__ = ['_verify_jwt_token', 'ensure_jwt_user_id']
