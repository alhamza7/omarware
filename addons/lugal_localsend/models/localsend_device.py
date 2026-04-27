# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LugalLocalSendDevice(models.Model):
    _name = "lugal.localsend.device"
    _description = "LocalSend Device"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    device_uid = fields.Char(
        string="Device UID",
        help="Stable identifier reported by the LocalSend client.",
        index=True,
    )
    protocol = fields.Selection(
        [("http", "HTTP"), ("https", "HTTPS")],
        default="http",
        required=True,
    )
    ip_address = fields.Char(required=True, tracking=True)
    port = fields.Integer(default=53317, required=True)
    require_pin = fields.Boolean(default=False)
    pin_code = fields.Char(
        help="Optional receiver PIN required by LocalSend prepare-upload.",
        groups="lugal_localsend.group_lugal_localsend_manager",
    )
    user_id = fields.Many2one("res.users", string="Owner", tracking=True)
    active = fields.Boolean(default=True)
    is_online = fields.Boolean(default=False, tracking=True)
    last_seen = fields.Datetime(tracking=True)
    note = fields.Text()

    transfer_sent_ids = fields.One2many(
        "lugal.localsend.transfer",
        "source_device_id",
        string="Transfers Sent",
    )
    transfer_received_ids = fields.One2many(
        "lugal.localsend.transfer",
        "target_device_id",
        string="Transfers Received",
    )
    transfer_count = fields.Integer(compute="_compute_transfer_count")

    _sql_constraints = [
        (
            "lugal_localsend_device_uid_unique",
            "unique(device_uid)",
            "Device UID must be unique.",
        ),
    ]

    @api.depends("transfer_sent_ids", "transfer_received_ids")
    def _compute_transfer_count(self):
        for record in self:
            record.transfer_count = len(record.transfer_sent_ids) + len(record.transfer_received_ids)
