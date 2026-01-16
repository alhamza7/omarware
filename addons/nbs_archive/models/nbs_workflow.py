# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


class NBSFolderWorkflow(models.Model):
    _name = 'nbs.folder.workflow'
    _description = 'Folder Workflow'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)

    department_id = fields.Many2one('nbs.department', string='Department', index=True)

    state_ids = fields.One2many('nbs.folder.workflow.state', 'workflow_id', string='States')
    transition_ids = fields.One2many('nbs.folder.workflow.transition', 'workflow_id', string='Transitions')

    initial_state_id = fields.Many2one(
        'nbs.folder.workflow.state',
        compute='_compute_initial_state',
        store=False,
    )

    @api.depends('state_ids.is_initial')
    def _compute_initial_state(self):
        for wf in self:
            init = wf.state_ids.filtered(lambda s: s.is_initial)[:1]
            wf.initial_state_id = init.id if init else False


class NBSFolderWorkflowState(models.Model):
    _name = 'nbs.folder.workflow.state'
    _description = 'Folder Workflow State'
    _order = 'workflow_id, sequence, id'

    workflow_id = fields.Many2one('nbs.folder.workflow', required=True, ondelete='cascade', index=True)
    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)

    is_initial = fields.Boolean(default=False)
    is_final = fields.Boolean(default=False)

    _sql_constraints = [
        ('wf_state_code_unique', 'unique(workflow_id, code)', 'State code must be unique per workflow.'),
    ]

    @api.constrains('is_initial')
    def _check_single_initial(self):
        for rec in self:
            if rec.is_initial:
                others = self.search([
                    ('workflow_id', '=', rec.workflow_id.id),
                    ('id', '!=', rec.id),
                    ('is_initial', '=', True),
                ], limit=1)
                if others:
                    raise ValidationError(_('Only one initial state is allowed per workflow.'))


class NBSFolderWorkflowTransition(models.Model):
    _name = 'nbs.folder.workflow.transition'
    _description = 'Folder Workflow Transition'
    _order = 'workflow_id, id'

    workflow_id = fields.Many2one('nbs.folder.workflow', required=True, ondelete='cascade', index=True)
    name = fields.Char(required=True)

    from_state_id = fields.Many2one('nbs.folder.workflow.state', required=True, ondelete='restrict', index=True)
    to_state_id = fields.Many2one('nbs.folder.workflow.state', required=True, ondelete='restrict', index=True)

    # Role-based control (simple, matches your current 3 groups)
    allow_employee = fields.Boolean(default=True)
    allow_manager = fields.Boolean(default=True)
    allow_admin = fields.Boolean(default=True)

    # Optional request gating
    requires_request = fields.Selection([
        ('none', 'None'),
        ('edit', 'Edit Request'),
        ('signature', 'Signature Request'),
        ('approval', 'Approval'),
    ], default='none', required=True)

    _sql_constraints = [
        ('wf_transition_unique', 'unique(workflow_id, from_state_id, to_state_id)', 'Duplicate transition.'),
    ]

    @api.constrains('from_state_id', 'to_state_id')
    def _check_same_workflow(self):
        for tr in self:
            if tr.from_state_id.workflow_id.id != tr.workflow_id.id or tr.to_state_id.workflow_id.id != tr.workflow_id.id:
                raise ValidationError(_('Transition states must belong to the same workflow.'))




















