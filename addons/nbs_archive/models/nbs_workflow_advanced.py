# -*- coding: utf-8 -*-
from odoo import models, fields, api


class NBSWorkflowTemplate(models.Model):
    _name = 'nbs.workflow.template'
    _description = 'Workflow Templates'
    
    name = fields.Char(string='Workflow Name', required=True)
    description = fields.Text(string='Description')
    department_id = fields.Many2one('nbs.department', string='Department')
    document_type_id = fields.Many2one('nbs.document.type', string='Document Type')
    
    step_ids = fields.One2many('nbs.workflow.step', 'workflow_id', string='Steps')
    active = fields.Boolean(default=True)


class NBSWorkflowStep(models.Model):
    _name = 'nbs.workflow.step'
    _description = 'Workflow Steps'
    
    workflow_id = fields.Many2one('nbs.workflow.template', string='Workflow', required=True, ondelete='cascade')
    name = fields.Char(string='Step Name', required=True)
    sequence = fields.Integer(default=10)
    
    action_type = fields.Selection([
        ('approval', 'Approval Required'),
        ('review', 'Review'),
        ('sign', 'Signature'),
        ('notify', 'Notification'),
        ('auto', 'Auto Action')
    ], string='Action Type', required=True)
    
    approver_id = fields.Many2one('res.users', string='Approver')
    approver_group_id = fields.Many2one('res.groups', string='Approver Group')
    
    is_mandatory = fields.Boolean(string='Mandatory', default=True)
    auto_approve = fields.Boolean(string='Auto Approve', default=False)


class NBSWorkflowInstance(models.Model):
    _name = 'nbs.workflow.instance'
    _description = 'Workflow Instances'
    
    document_id = fields.Many2one('nbs.document', string='Document', required=True)
    workflow_id = fields.Many2one('nbs.workflow.template', string='Workflow Template')
    
    status = fields.Selection([
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected')
    ], default='running')
    
    current_step_id = fields.Many2one('nbs.workflow.step', string='Current Step')
    completed_steps = fields.Integer(string='Completed Steps', default=0)
    total_steps = fields.Integer(string='Total Steps', compute='_compute_total_steps')
    
    @api.depends('workflow_id.step_ids')
    def _compute_total_steps(self):
        for instance in self:
            instance.total_steps = len(instance.workflow_id.step_ids)
