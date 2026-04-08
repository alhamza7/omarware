# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CrmAuditLog(models.Model):
    """Immutable audit trail for all CRM operations — cannot be deleted."""
    _name = 'lugal.crm.audit.log'
    _description = 'CRM Audit Log'
    _order = 'timestamp desc, id desc'
    _rec_name = 'action'

    timestamp = fields.Datetime(
        string='Timestamp',
        default=fields.Datetime.now,
        required=True,
        readonly=True,
        index=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='User / المستخدم',
        required=True,
        readonly=True,
        index=True,
        ondelete='restrict',
    )
    action = fields.Selection([
        # Customer
        ('customer_created', 'Customer Created'),
        ('customer_updated', 'Customer Updated'),
        ('customer_deleted', 'Customer Deleted'),
        ('customer_stage_moved', 'Customer Stage Moved'),
        # Call
        ('call_created', 'Call Created'),
        ('call_ended', 'Call Ended'),
        ('call_deleted', 'Call Deleted'),
        ('call_recording_attached', 'Call Recording Attached'),
        # Ticket
        ('ticket_created', 'Ticket Created'),
        ('ticket_updated', 'Ticket Updated'),
        ('ticket_status_changed', 'Ticket Status Changed'),
        ('ticket_assigned', 'Ticket Assigned'),
        ('ticket_escalated', 'Ticket Escalated'),
        ('ticket_deleted', 'Ticket Deleted'),
        # Task
        ('task_created', 'Task Created'),
        ('task_updated', 'Task Updated'),
        ('task_status_changed', 'Task Status Changed'),
        ('task_assigned', 'Task Assigned'),
        ('task_deleted', 'Task Deleted'),
        # Omnichannel
        ('message_created', 'Message Created'),
        ('message_assigned', 'Message Assigned'),
        ('message_replied', 'Message Replied'),
        ('message_resolved', 'Message Resolved'),
        ('message_transferred', 'Message Transferred'),
        # Supply
        ('po_created', 'PO Created'),
        ('po_updated', 'PO Updated'),
        ('po_deleted', 'PO Deleted'),
        ('vendor_created', 'Vendor Created'),
        ('vendor_updated', 'Vendor Updated'),
        ('vendor_deleted', 'Vendor Deleted'),
        ('container_created', 'Container Created'),
        ('container_updated', 'Container Updated'),
        ('container_deleted', 'Container Deleted'),
        # Knowledge Base
        ('article_created', 'KB Article Created'),
        ('article_updated', 'KB Article Updated'),
        ('article_deleted', 'KB Article Deleted'),
        ('notification_pushed', 'KB Notification Pushed'),
        # Config
        ('tag_created', 'Tag Created'),
        ('tag_deleted', 'Tag Deleted'),
        ('stage_created', 'Stage Created'),
        ('stage_deleted', 'Stage Deleted'),
        ('script_created', 'Call Script Created'),
        ('script_deleted', 'Call Script Deleted'),
        # Branch
        ('branch_created', 'Branch Created'),
        ('branch_updated', 'Branch Updated'),
        ('branch_deleted', 'Branch Deleted'),
        # QA
        ('qa_review_created', 'QA Review Created'),
        ('qa_review_submitted', 'QA Review Submitted'),
    ], string='Action / الإجراء', required=True, readonly=True, index=True)

    # Optional CRM record references
    customer_id = fields.Many2one(
        'lugal.crm.customer',
        string='Customer / العميل',
        readonly=True,
        index=True,
        ondelete='set null',
    )
    branch_id = fields.Many2one(
        'lugal.crm.branch',
        string='Branch / الفرع',
        readonly=True,
        index=True,
        ondelete='set null',
    )
    record_model = fields.Char(
        string='Record Model',
        readonly=True,
        help='Odoo model name of the affected record',
    )
    record_id = fields.Integer(
        string='Record ID',
        readonly=True,
        index=True,
    )
    ip_address = fields.Char(string='IP Address', readonly=True)
    details = fields.Text(
        string='Details / التفاصيل',
        readonly=True,
        help='JSON-formatted additional details',
    )

    _sql_constraints = [
        ('no_delete', 'CHECK(1=1)', 'CRM Audit logs cannot be deleted!'),
    ]

    def unlink(self):
        """Prevent hard-deletion of audit log records."""
        raise ValidationError('CRM Audit logs cannot be deleted. They are permanent compliance records.')

    @api.model
    def log_action(self, action, user_id=None, customer_id=None, branch_id=None,
                   record_model=None, record_id=None, ip_address=None, details=None):
        """
        Create a CRM audit log entry (non-blocking — catches exceptions internally).

        Usage:
            request.env['lugal.crm.audit.log'].sudo().log_action(
                action='customer_created',
                customer_id=customer.id,
                branch_id=customer.branch_id.id,
                record_model='lugal.crm.customer',
                record_id=customer.id,
                details='{"name": "Ali Hassan"}',
            )
        """
        try:
            vals = {
                'action': action,
                'user_id': user_id or self.env.uid,
            }
            if customer_id:
                vals['customer_id'] = customer_id
            if branch_id:
                vals['branch_id'] = branch_id
            if record_model:
                vals['record_model'] = record_model
            if record_id:
                vals['record_id'] = record_id
            if ip_address:
                vals['ip_address'] = ip_address
            if details:
                vals['details'] = details
            return self.sudo().create(vals)
        except Exception as e:
            _logger.warning('CRM audit log failed (non-blocking): %s', e)
            return None
