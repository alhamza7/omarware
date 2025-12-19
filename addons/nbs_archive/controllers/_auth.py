#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared API authentication helpers.

The frontend uses Bearer JWT tokens (see `nbs.jwt.service`).
Most API routes therefore run with `auth='none'` and validate tokens manually,
then switch the request environment to the authenticated user.
"""

from odoo.http import request

from .main import NBSMainController


def ensure_jwt_user_id():
    """
    Validate Authorization: Bearer <jwt> and update request env.

    Returns:
        int|None: authenticated user id or None if missing/invalid token
    """
    uid = NBSMainController()._verify_jwt_token()
    if not uid:
        return None
    request.update_env(user=uid)
    return uid



