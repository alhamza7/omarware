# -*- coding: utf-8 -*-
from odoo import models, fields, api
import difflib


class NBSDocumentVersionAdvanced(models.Model):
    _inherit = 'nbs.document.version'
    
    # Version comparison
    changes_summary = fields.Text(string='Changes Summary', compute='_compute_changes')
    diff_content = fields.Html(string='Content Diff')
    
    # Version tags
    version_tag = fields.Char(string='Version Tag', help='e.g., v1.0, draft, final')
    is_major = fields.Boolean(string='Major Version', default=False)
    
    # Approval workflow
    approval_status = fields.Selection([
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Approval Status', default='pending')
    
    approved_by = fields.Many2one('res.users', string='Approved By')
    approved_at = fields.Datetime(string='Approved At')
    rejection_reason = fields.Text(string='Rejection Reason')
    
    def _compute_changes(self):
        for version in self:
            # Get previous version
            previous = self.search([
                ('document_id', '=', version.document_id.id),
                ('version_number', '<', version.version_number)
            ], order='version_number desc', limit=1)
            
            if previous:
                version.changes_summary = f"Changes from v{previous.version_number}"
            else:
                version.changes_summary = "Initial version"
    
    def compare_with_version(self, other_version_id):
        """Compare this version with another"""
        self.ensure_one()
        other = self.browse(other_version_id)
        
        # Simple text comparison
        diff = difflib.unified_diff(
            self.content.split('\n') if self.content else [],
            other.content.split('\n') if other.content else [],
            lineterm=''
        )
        
        return {
            'diff': '\n'.join(diff),
            'version_1': self.version_number,
            'version_2': other.version_number
        }
    
    def approve_version(self):
        """Approve this version"""
        self.ensure_one()
        self.write({
            'approval_status': 'approved',
            'approved_by': self.env.user.id,
            'approved_at': fields.Datetime.now()
        })
    
    def rollback_to_this_version(self):
        """Rollback document to this version"""
        self.ensure_one()
        # Implementation for rollback
        pass
