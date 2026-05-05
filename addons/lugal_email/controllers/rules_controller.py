# -*- coding: utf-8 -*-
"""
Email Rules  &  Quick Steps REST API
=====================================

Rules endpoints:
  GET    /api/lugal/email/rules            — list current user's rules
  POST   /api/lugal/email/rules            — create a rule
  GET    /api/lugal/email/rules/<id>       — get one rule
  PUT    /api/lugal/email/rules/<id>       — full update
  PATCH  /api/lugal/email/rules/<id>       — partial update
  DELETE /api/lugal/email/rules/<id>       — delete
  POST   /api/lugal/email/rules/<id>/test  — dry-run a rule against a message

Quick Steps endpoints:
  GET    /api/lugal/email/quick_steps            — list
  POST   /api/lugal/email/quick_steps            — create
  GET    /api/lugal/email/quick_steps/<id>       — get one
  PUT    /api/lugal/email/quick_steps/<id>       — update
  DELETE /api/lugal/email/quick_steps/<id>       — delete
  POST   /api/lugal/email/messages/<id>/apply_quick_step — apply to a message
"""
import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _ensure_jwt():
    """Return user_id from JWT or None."""
    from .email_controller import ensure_jwt_user_id
    return ensure_jwt_user_id()


def _json_ok(data, status=200):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
    }
    body = json.dumps({'success': True, 'data': data})
    return request.make_response(body, headers=headers, status=status)


def _json_err(msg, status=400):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
    }
    body = json.dumps({'success': False, 'error': msg})
    return request.make_response(body, headers=headers, status=status)


def _rule_dict(rule):
    return {
        'id':                 rule.id,
        'name':               rule.name,
        'is_active':          rule.is_active,
        'sequence':           rule.sequence,
        'match_mode':         rule.match_mode,
        'account_id':         rule.account_id.id if rule.account_id else None,
        'conditions':         json.loads(rule.conditions_json or '[]'),
        'actions':            json.loads(rule.actions_json or '[]'),
        'stop_processing':    rule.stop_processing,
        'last_triggered_at':  rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
        'trigger_count':      rule.trigger_count,
    }


def _qs_dict(qs):
    return {
        'id':          qs.id,
        'name':        qs.name,
        'description': qs.description or '',
        'sequence':    qs.sequence,
        'icon':        qs.icon or '',
        'steps':       json.loads(qs.steps_json or '[]'),
        'use_count':   qs.use_count,
    }


# ── Rules controller ───────────────────────────────────────────────────────────

class EmailRulesController(http.Controller):

    # ── List ──────────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def rules_list(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok([])
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rules = request.env['lugal.email.rule'].sudo().search([
                ('user_id', '=', uid),
            ], order='sequence asc, id asc')
            return _json_ok([_rule_dict(r) for r in rules])
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Create ────────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules', type='http', auth='none', csrf=False,
                methods=['POST'])
    def rules_create(self, **kwargs):
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            body = json.loads(request.httprequest.data or '{}')
            name = (body.get('name') or '').strip()
            if not name:
                return _json_err('name is required', 400)
            account_id = body.get('account_id')
            if account_id:
                acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
                if not acc.exists() or acc.user_id.id != uid:
                    return _json_err('Account not found', 404)
            rule = request.env['lugal.email.rule'].sudo().create({
                'name':             name,
                'user_id':          uid,
                'account_id':       int(account_id) if account_id else False,
                'is_active':        body.get('is_active', True),
                'sequence':         int(body.get('sequence', 10)),
                'match_mode':       body.get('match_mode', 'all'),
                'conditions_json':  json.dumps(body.get('conditions', [])),
                'actions_json':     json.dumps(body.get('actions', [])),
                'stop_processing':  bool(body.get('stop_processing', False)),
            })
            request.env.cr.commit()
            return _json_ok(_rule_dict(rule), status=201)
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Get one ───────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def rules_get(self, rule_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)
            return _json_ok(_rule_dict(rule))
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Update (PUT / PATCH) ──────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>', type='http', auth='none', csrf=False,
                methods=['PUT', 'PATCH', 'OPTIONS'])
    def rules_update(self, rule_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)
            body = json.loads(request.httprequest.data or '{}')
            write_vals = {}
            if 'name'            in body: write_vals['name']             = (body['name'] or '').strip()
            if 'is_active'       in body: write_vals['is_active']        = bool(body['is_active'])
            if 'sequence'        in body: write_vals['sequence']         = int(body['sequence'])
            if 'match_mode'      in body: write_vals['match_mode']       = body['match_mode']
            if 'conditions'      in body: write_vals['conditions_json']  = json.dumps(body['conditions'])
            if 'actions'         in body: write_vals['actions_json']     = json.dumps(body['actions'])
            if 'stop_processing' in body: write_vals['stop_processing']  = bool(body['stop_processing'])
            if 'account_id'      in body:
                account_id = body['account_id']
                if account_id:
                    acc = request.env['lugal.email.account'].sudo().browse(int(account_id))
                    if not acc.exists() or acc.user_id.id != uid:
                        return _json_err('Account not found', 404)
                write_vals['account_id'] = int(account_id) if account_id else False
            if write_vals:
                rule.write(write_vals)
                request.env.cr.commit()
            return _json_ok(_rule_dict(rule))
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Delete ────────────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>', type='http', auth='none', csrf=False,
                methods=['DELETE'])
    def rules_delete(self, rule_id, **kwargs):
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)
            rule.unlink()
            request.env.cr.commit()
            return _json_ok({'deleted': True, 'id': rule_id})
        except Exception as exc:
            return _json_err(str(exc), 500)

    # ── Dry-run test ──────────────────────────────────────────────────────────

    @http.route('/api/lugal/email/rules/<int:rule_id>/test', type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'])
    def rules_test(self, rule_id, **kwargs):
        """Dry-run: return whether the rule would match a given message_id (no side effects)."""
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            rule = request.env['lugal.email.rule'].sudo().browse(rule_id)
            if not rule.exists() or rule.user_id.id != uid:
                return _json_err('Not found', 404)
            body       = json.loads(request.httprequest.data or '{}')
            message_id = body.get('message_id')
            if not message_id:
                return _json_err('message_id required', 400)
            msg = request.env['lugal.email.message'].sudo().browse(int(message_id))
            if not msg.exists() or msg.account_id.user_id.id != uid:
                return _json_err('Message not found', 404)
            msg_vals = {
                'from_address':   msg.from_address or '',
                'to_addresses':   msg.to_addresses or '',
                'cc_addresses':   msg.cc_addresses or '',
                'subject':        msg.subject or '',
                'body_text':      msg.body_text or '',
                'has_attachments': False,
                'is_important':   msg.is_important,
                'is_read':        msg.is_read,
                'is_starred':     msg.is_starred,
                'folder':         msg.folder or '',
            }
            matched     = rule._matches(msg_vals)
            would_apply = []
            if matched:
                for act in rule._get_actions():
                    would_apply.append(act)
            return _json_ok({
                'rule_id':      rule_id,
                'message_id':   int(message_id),
                'matched':      matched,
                'would_apply':  would_apply,
                'stop_after':   rule.stop_processing and matched,
            })
        except Exception as exc:
            return _json_err(str(exc), 500)


# ── Quick Steps controller ─────────────────────────────────────────────────────

class EmailQuickStepsController(http.Controller):

    @http.route('/api/lugal/email/quick_steps', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def qs_list(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok([])
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            items = request.env['lugal.email.quick.step'].sudo().search([
                ('user_id', '=', uid),
            ], order='sequence asc, id asc')
            return _json_ok([_qs_dict(q) for q in items])
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/quick_steps', type='http', auth='none', csrf=False,
                methods=['POST'])
    def qs_create(self, **kwargs):
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            body = json.loads(request.httprequest.data or '{}')
            name = (body.get('name') or '').strip()
            if not name:
                return _json_err('name is required', 400)
            qs = request.env['lugal.email.quick.step'].sudo().create({
                'name':        name,
                'description': body.get('description', ''),
                'user_id':     uid,
                'sequence':    int(body.get('sequence', 10)),
                'icon':        body.get('icon', ''),
                'steps_json':  json.dumps(body.get('steps', [])),
            })
            request.env.cr.commit()
            return _json_ok(_qs_dict(qs), status=201)
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/quick_steps/<int:qs_id>', type='http', auth='none', csrf=False,
                methods=['GET', 'OPTIONS'])
    def qs_get(self, qs_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            qs = request.env['lugal.email.quick.step'].sudo().browse(qs_id)
            if not qs.exists() or qs.user_id.id != uid:
                return _json_err('Not found', 404)
            return _json_ok(_qs_dict(qs))
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/quick_steps/<int:qs_id>', type='http', auth='none', csrf=False,
                methods=['PUT', 'PATCH', 'OPTIONS'])
    def qs_update(self, qs_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            qs = request.env['lugal.email.quick.step'].sudo().browse(qs_id)
            if not qs.exists() or qs.user_id.id != uid:
                return _json_err('Not found', 404)
            body = json.loads(request.httprequest.data or '{}')
            write_vals = {}
            if 'name'        in body: write_vals['name']        = body['name']
            if 'description' in body: write_vals['description'] = body['description']
            if 'sequence'    in body: write_vals['sequence']    = int(body['sequence'])
            if 'icon'        in body: write_vals['icon']        = body['icon']
            if 'steps'       in body: write_vals['steps_json']  = json.dumps(body['steps'])
            if write_vals:
                qs.write(write_vals)
                request.env.cr.commit()
            return _json_ok(_qs_dict(qs))
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/quick_steps/<int:qs_id>', type='http', auth='none', csrf=False,
                methods=['DELETE'])
    def qs_delete(self, qs_id, **kwargs):
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            qs = request.env['lugal.email.quick.step'].sudo().browse(qs_id)
            if not qs.exists() or qs.user_id.id != uid:
                return _json_err('Not found', 404)
            qs.unlink()
            request.env.cr.commit()
            return _json_ok({'deleted': True, 'id': qs_id})
        except Exception as exc:
            return _json_err(str(exc), 500)

    @http.route('/api/lugal/email/messages/<int:message_id>/apply_quick_step',
                type='http', auth='none', csrf=False, methods=['POST', 'OPTIONS'])
    def apply_quick_step(self, message_id, **kwargs):
        """Apply a quick step to a message.

        Body: { "quick_step_id": 5 }
        """
        if request.httprequest.method == 'OPTIONS':
            return _json_ok({})
        uid = _ensure_jwt()
        if not uid:
            return _json_err('Unauthorized', 401)
        try:
            body    = json.loads(request.httprequest.data or '{}')
            qs_id   = body.get('quick_step_id')
            if not qs_id:
                return _json_err('quick_step_id required', 400)
            msg = request.env['lugal.email.message'].sudo().browse(message_id)
            if not msg.exists() or msg.is_deleted or msg.account_id.user_id.id != uid:
                return _json_err('Message not found', 404)
            qs = request.env['lugal.email.quick.step'].sudo().browse(int(qs_id))
            if not qs.exists() or qs.user_id.id != uid:
                return _json_err('Quick step not found', 404)
            qs.apply_to_message(msg)
            request.env.cr.commit()
            return _json_ok({'applied': True, 'message_id': message_id, 'quick_step_id': qs_id})
        except Exception as exc:
            return _json_err(str(exc), 500)
