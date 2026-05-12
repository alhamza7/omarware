# -*- coding: utf-8 -*-
"""
CRM Error Helper
================
Centralised exception handler for all CRM JSON-RPC controllers.

Usage in every controller except block:
    except Exception as e:
        return crm_error(e, 'handler_name')

Why rollback?
    Odoo JSON-RPC handlers run inside a transaction that Odoo's retrying()
    wrapper commits (cr.flush → cr.commit) after the handler returns.
    If a DB error occurs inside the handler and we catch it ourselves,
    the transaction is left in the "aborted" state.  Odoo then tries to
    flush pending ORM computations (e.g. res.partner._compute_partner_share)
    against the aborted transaction, which raises a second
    psycopg2.errors.InFailedSqlTransaction and returns a hard Odoo Server
    Error instead of our clean JSON.

    Calling cr.rollback() here resets the transaction so Odoo's post-handler
    flush has nothing to do and the connection goes back to the pool cleanly.
"""

import logging
from odoo.http import request

_logger = logging.getLogger(__name__)


def crm_error(exc: Exception, handler: str = '') -> dict:
    """
    Roll back the current DB transaction and return a standard error dict.

    Always call this instead of a bare `return {'success': False, 'error': ...}`
    inside an except block that caught a DB-level exception.
    """
    _logger.exception('%s error', handler)
    try:
        request.env.cr.rollback()
    except Exception:
        pass  # cr may already be closed in edge cases; ignore
    return {'success': False, 'error': str(exc)}
# TODO: remove - cherry-pick marker
