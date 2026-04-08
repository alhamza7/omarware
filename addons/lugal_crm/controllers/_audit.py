# -*- coding: utf-8 -*-
"""
CRM Audit Logging Helper
========================
Centralised helper for writing CRM audit log entries from controllers.
All calls are non-blocking — a logging failure never breaks the API response.
"""

import json
import logging
from odoo.http import request

_logger = logging.getLogger(__name__)


def crm_audit(action, customer_id=None, branch_id=None,
              record_model=None, record_id=None, details=None):
    """
    Write a CRM audit log entry (non-blocking).

    Call from any controller method after a successful operation.

    Args:
        action      (str):  One of the Selection values in lugal.crm.audit.log.
        customer_id (int):  Optional linked customer.
        branch_id   (int):  Optional linked branch.
        record_model(str):  Odoo model name e.g. 'lugal.crm.ticket'.
        record_id   (int):  ID of the affected record.
        details     (dict): Extra key/value pairs serialised to JSON.

    Example:
        crm_audit('customer_created', customer_id=c.id, record_model='lugal.crm.customer',
                  record_id=c.id, details={'name': c.name, 'phone': c.phone})
    """
    try:
        ip = (request.httprequest.headers.get('X-Forwarded-For')
              or request.httprequest.remote_addr or '')
        details_json = json.dumps(details, ensure_ascii=False, default=str) if details else None
        request.env['lugal.crm.audit.log'].sudo().log_action(
            action=action,
            user_id=request.env.uid,
            customer_id=customer_id,
            branch_id=branch_id,
            record_model=record_model,
            record_id=record_id,
            ip_address=ip,
            details=details_json,
        )
    except Exception as e:
        _logger.warning('crm_audit non-blocking failure [%s]: %s', action, e)
