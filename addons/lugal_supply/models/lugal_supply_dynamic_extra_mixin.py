# -*- coding: utf-8 -*-
"""Reusable JSON `extra_fields` for supply documents (no per-key DB columns)."""

import json
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_KEY_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9_.-]{0,127}$')


class LugalSupplyDynamicExtraMixin(models.AbstractModel):
    _name = 'lugal.supply.dynamic.extra.mixin'
    _description = 'Dynamic JSON extra fields (custom FE / integration keys)'

    extra_fields = fields.Json(
        string='Extra fields',
        default=lambda self: {},
        copy=True,
        help='Arbitrary JSON object for custom keys from frontend or integrations '
             '(values must be JSON-serializable).',
    )

    @staticmethod
    def validate_extra_field_key(key):
        if not isinstance(key, str):
            key = str(key)
        key = key.strip()
        if not key or not _KEY_RE.match(key):
            raise UserError(
                _('Invalid extra field key "%s". Use a non-empty string starting with a letter; '
                  'allowed: letters, digits, underscore, dot, hyphen (max 128 chars).') % (key[:80],)
            )
        return key

    @api.model
    def assert_json_serializable(self, value):
        """Raise UserError if value cannot be stored in a JSON column."""
        try:
            json.dumps(value)
        except (TypeError, ValueError) as e:
            raise UserError(_('Value must be JSON-serializable (string, number, bool, null, list, object).')) from e

    def get_extra_fields_dict(self):
        """Return a copy of ``extra_fields``; invalid DB payloads become ``{}`` (read-safe)."""
        self.ensure_one()
        raw = self.extra_fields
        if raw is None or raw is False:
            return {}
        if isinstance(raw, dict):
            return dict(raw)
        # Rare: legacy or import stored JSON as a string in the jsonb column.
        if isinstance(raw, str) and raw.strip():
            try:
                loaded = json.loads(raw)
            except (TypeError, ValueError):
                return {}
            return dict(loaded) if isinstance(loaded, dict) else {}
        return {}

    def get_dynamic_field(self, key, default=None):
        """Read one key from ``extra_fields``."""
        self.ensure_one()
        k = self.validate_extra_field_key(key)
        return self.get_extra_fields_dict().get(k, default)

    def set_dynamic_field(self, key, value):
        """Set one key on ``extra_fields`` (single write)."""
        self.ensure_one()
        k = self.validate_extra_field_key(key)
        self.assert_json_serializable(value)
        data = self.get_extra_fields_dict()
        data[k] = value
        self.write({'extra_fields': data})

    def merge_extra_fields(self, partial):
        """Merge many keys into ``extra_fields`` (one write)."""
        self.ensure_one()
        if partial is None:
            return
        if not isinstance(partial, dict):
            raise UserError(_('merge_extra_fields expects a dict.'))
        data = self.get_extra_fields_dict()
        for key, value in partial.items():
            k = self.validate_extra_field_key(key)
            self.assert_json_serializable(value)
            data[k] = value
        self.write({'extra_fields': data})

    @api.model
    def sanitize_extra_fields_input(self, payload):
        """Validate and return a clean dict for create/write from API or RPC."""
        if payload is None:
            return {}
        if not isinstance(payload, dict):
            raise UserError(_('extra_fields must be a JSON object.'))
        out = {}
        for key, value in payload.items():
            k = self.validate_extra_field_key(key)
            self.assert_json_serializable(value)
            out[k] = value
        return out
