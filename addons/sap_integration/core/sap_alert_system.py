# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Alert System

Advanced alert system for critical sync failures and monitoring.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from ..config.sap_config import ERROR_MESSAGES
from .sap_logger import SapLogger, SapSyncError

_logger = logging.getLogger(__name__)


class SapAlertRule(models.Model):
    """Alert rules for SAP integration monitoring"""
    _name = 'sap.alert.rule'
    _description = 'SAP Alert Rule'
    _order = 'priority desc, name'
    
    name = fields.Char('Rule Name', required=True)
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], 'Priority', default='medium', required=True)
    
    # Alert conditions
    condition_type = fields.Selection([
        ('error_count', 'Error Count Threshold'),
        ('error_rate', 'Error Rate Threshold'),
        ('sync_failure', 'Sync Failure'),
        ('connection_failure', 'Connection Failure'),
        ('data_mismatch', 'Data Mismatch'),
        ('missing_records', 'Missing Records'),
        ('performance_degradation', 'Performance Degradation')
    ], 'Condition Type', required=True)
    
    threshold_value = fields.Float('Threshold Value', help="Threshold value for the condition")
    threshold_period = fields.Integer('Threshold Period (minutes)', default=60, 
                                    help="Time period in minutes to evaluate the condition")
    
    # Alert scope
    backend_id = fields.Many2one('sap.backend', 'Backend', 
                                help="Specific backend to monitor (leave empty for all)")
    model_name = fields.Char('Model Name', help="Specific model to monitor (leave empty for all)")
    operation = fields.Char('Operation', help="Specific operation to monitor (leave empty for all)")
    
    # Alert actions
    notify_users = fields.Boolean('Notify Users', default=True)
    user_ids = fields.Many2many('res.users', 'sap_alert_rule_users', 
                               string='Users to Notify')
    email_notification = fields.Boolean('Email Notification', default=False)
    email_template_id = fields.Many2one('mail.template', 'Email Template')
    
    # Alert state
    last_triggered = fields.Datetime('Last Triggered', readonly=True)
    trigger_count = fields.Integer('Trigger Count', default=0, readonly=True)
    is_triggered = fields.Boolean('Currently Triggered', default=False, readonly=True)
    
    @api.model
    def check_all_rules(self):
        """Check all active alert rules"""
        active_rules = self.search([('active', '=', True)])
        triggered_rules = []
        
        for rule in active_rules:
            if rule._evaluate_condition():
                rule._trigger_alert()
                triggered_rules.append(rule)
        
        return {
            'checked_rules': len(active_rules),
            'triggered_rules': len(triggered_rules),
            'triggered_rule_names': [rule.name for rule in triggered_rules]
        }
    
    def _evaluate_condition(self):
        """Evaluate if the alert condition is met"""
        try:
            if self.condition_type == 'error_count':
                return self._check_error_count()
            elif self.condition_type == 'error_rate':
                return self._check_error_rate()
            elif self.condition_type == 'sync_failure':
                return self._check_sync_failure()
            elif self.condition_type == 'connection_failure':
                return self._check_connection_failure()
            elif self.condition_type == 'data_mismatch':
                return self._check_data_mismatch()
            elif self.condition_type == 'missing_records':
                return self._check_missing_records()
            elif self.condition_type == 'performance_degradation':
                return self._check_performance_degradation()
            
            return False
        except Exception as e:
            _logger.error(f"Error evaluating alert rule {self.name}: {str(e)}")
            return False
    
    def _check_error_count(self):
        """Check if error count exceeds threshold"""
        domain = [
            ('status', '=', 'error'),
            ('create_date', '>=', fields.Datetime.now() - timedelta(minutes=self.threshold_period))
        ]
        
        if self.backend_id:
            domain.append(('backend_id', '=', self.backend_id.id))
        if self.model_name:
            domain.append(('model_name', '=', self.model_name))
        if self.operation:
            domain.append(('operation', '=', self.operation))
        
        error_count = self.env['sap.sync.log'].search_count(domain)
        return error_count >= self.threshold_value
    
    def _check_error_rate(self):
        """Check if error rate exceeds threshold"""
        # Get total operations in the period
        total_domain = [
            ('create_date', '>=', fields.Datetime.now() - timedelta(minutes=self.threshold_period))
        ]
        if self.backend_id:
            total_domain.append(('backend_id', '=', self.backend_id.id))
        if self.model_name:
            total_domain.append(('model_name', '=', self.model_name))
        if self.operation:
            total_domain.append(('operation', '=', self.operation))
        
        total_operations = self.env['sap.sync.log'].search_count(total_domain)
        
        if total_operations == 0:
            return False
        
        # Get error count
        error_domain = total_domain + [('status', '=', 'error')]
        error_count = self.env['sap.sync.log'].search_count(error_domain)
        
        error_rate = (error_count / total_operations) * 100
        return error_rate >= self.threshold_value
    
    def _check_sync_failure(self):
        """Check for sync failures"""
        domain = [
            ('status', '=', 'error'),
            ('create_date', '>=', fields.Datetime.now() - timedelta(minutes=self.threshold_period)),
            ('operation', 'ilike', 'sync')
        ]
        
        if self.backend_id:
            domain.append(('backend_id', '=', self.backend_id.id))
        if self.model_name:
            domain.append(('model_name', '=', self.model_name))
        
        return self.env['sap.sync.log'].search_count(domain) > 0
    
    def _check_connection_failure(self):
        """Check for connection failures"""
        domain = [
            ('status', '=', 'error'),
            ('create_date', '>=', fields.Datetime.now() - timedelta(minutes=self.threshold_period)),
            ('error_type', 'in', ['ConnectionError', 'TimeoutError', 'AuthenticationError'])
        ]
        
        if self.backend_id:
            domain.append(('backend_id', '=', self.backend_id.id))
        
        return self.env['sap.sync.log'].search_count(domain) > 0
    
    def _check_data_mismatch(self):
        """Check for data mismatches"""
        # This would require integration with the error analyzer
        # For now, check for validation errors
        domain = [
            ('status', '=', 'error'),
            ('create_date', '>=', fields.Datetime.now() - timedelta(minutes=self.threshold_period)),
            ('error_type', '=', 'ValidationError')
        ]
        
        if self.backend_id:
            domain.append(('backend_id', '=', self.backend_id.id))
        if self.model_name:
            domain.append(('model_name', '=', self.model_name))
        
        return self.env['sap.sync.log'].search_count(domain) > 0
    
    def _check_missing_records(self):
        """Check for missing records"""
        # This would require integration with the error analyzer
        # For now, check for specific error messages
        domain = [
            ('status', '=', 'error'),
            ('create_date', '>=', fields.Datetime.now() - timedelta(minutes=self.threshold_period)),
            ('message', 'ilike', 'not found')
        ]
        
        if self.backend_id:
            domain.append(('backend_id', '=', self.backend_id.id))
        if self.model_name:
            domain.append(('model_name', '=', self.model_name))
        
        return self.env['sap.sync.log'].search_count(domain) > 0
    
    def _check_performance_degradation(self):
        """Check for performance degradation"""
        # Check for operations taking longer than threshold
        domain = [
            ('create_date', '>=', fields.Datetime.now() - timedelta(minutes=self.threshold_period)),
            ('duration', '>', self.threshold_value)
        ]
        
        if self.backend_id:
            domain.append(('backend_id', '=', self.backend_id.id))
        if self.model_name:
            domain.append(('model_name', '=', self.model_name))
        if self.operation:
            domain.append(('operation', '=', self.operation))
        
        return self.env['sap.sync.log'].search_count(domain) > 0
    
    def _trigger_alert(self):
        """Trigger the alert"""
        try:
            # Update rule state
            self.last_triggered = fields.Datetime.now()
            self.trigger_count += 1
            self.is_triggered = True
            
            # Create alert record
            alert = self.env['sap.alert'].create({
                'rule_id': self.id,
                'backend_id': self.backend_id.id if self.backend_id else None,
                'model_name': self.model_name,
                'operation': self.operation,
                'priority': self.priority,
                'message': self._generate_alert_message(),
                'details': self._generate_alert_details()
            })
            
            # Send notifications
            if self.notify_users and self.user_ids:
                self._send_user_notifications(alert)
            
            if self.email_notification and self.email_template_id:
                self._send_email_notification(alert)
            
            _logger.warning(f"Alert triggered: {self.name}")
            
        except Exception as e:
            _logger.error(f"Error triggering alert {self.name}: {str(e)}")
    
    def _generate_alert_message(self):
        """Generate alert message"""
        base_message = f"Alert: {self.name}"
        
        if self.backend_id:
            base_message += f" (Backend: {self.backend_id.name})"
        
        if self.model_name:
            base_message += f" (Model: {self.model_name})"
        
        if self.operation:
            base_message += f" (Operation: {self.operation})"
        
        return base_message
    
    def _generate_alert_details(self):
        """Generate detailed alert information"""
        details = {
            'rule_name': self.name,
            'condition_type': self.condition_type,
            'threshold_value': self.threshold_value,
            'threshold_period': self.threshold_period,
            'trigger_count': self.trigger_count,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None
        }
        
        return json.dumps(details)
    
    def _send_user_notifications(self, alert):
        """Send notifications to users"""
        for user in self.user_ids:
            # Create notification
            self.env['mail.message'].create({
                'model': 'sap.alert',
                'res_id': alert.id,
                'subject': alert.message,
                'body': alert.details,
                'partner_ids': [(4, user.partner_id.id)],
                'message_type': 'notification'
            })
    
    def _send_email_notification(self, alert):
        """Send email notification"""
        if not self.email_template_id:
            return
        
        # This would require email template implementation
        # For now, just log the action
        _logger.info(f"Email notification would be sent for alert: {alert.message}")


class SapAlert(models.Model):
    """Alert records for SAP integration"""
    _name = 'sap.alert'
    _description = 'SAP Alert'
    _order = 'create_date desc'
    
    rule_id = fields.Many2one('sap.alert.rule', 'Alert Rule', required=True)
    backend_id = fields.Many2one('sap.backend', 'Backend')
    model_name = fields.Char('Model')
    operation = fields.Char('Operation')
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], 'Priority', required=True)
    
    message = fields.Char('Message', required=True)
    details = fields.Text('Details')
    
    status = fields.Selection([
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved')
    ], 'Status', default='active')
    
    acknowledged_by = fields.Many2one('res.users', 'Acknowledged By')
    acknowledged_date = fields.Datetime('Acknowledged Date')
    resolved_by = fields.Many2one('res.users', 'Resolved By')
    resolved_date = fields.Datetime('Resolved Date')
    resolution_notes = fields.Text('Resolution Notes')
    
    def acknowledge(self):
        """Acknowledge the alert"""
        self.status = 'acknowledged'
        self.acknowledged_by = self.env.user.id
        self.acknowledged_date = fields.Datetime.now()
    
    def resolve(self, notes=None):
        """Resolve the alert"""
        self.status = 'resolved'
        self.resolved_by = self.env.user.id
        self.resolved_date = fields.Datetime.now()
        if notes:
            self.resolution_notes = notes
        
        # Reset rule trigger state
        if self.rule_id:
            self.rule_id.is_triggered = False


class SapAlertSystem(models.AbstractModel):
    """Alert system management"""
    _name = 'sap.alert.system'
    _description = 'SAP Alert System'
    
    
    @api.model
    def run_alert_checks(self):
        """Run all alert checks (called by cron job)"""
        try:
            result = self.env['sap.alert.rule'].check_all_rules()
            _logger.info(f"Alert checks completed: {result}")
            return result
        except Exception as e:
            _logger.error(f"Error running alert checks: {str(e)}")
            raise
    
    @api.model
    def create_default_rules(self):
        """Create default alert rules"""
        default_rules = [
            {
                'name': 'High Error Rate',
                'description': 'Alert when error rate exceeds 20%',
                'condition_type': 'error_rate',
                'threshold_value': 20.0,
                'threshold_period': 60,
                'priority': 'high'
            },
            {
                'name': 'Connection Failures',
                'description': 'Alert on connection failures',
                'condition_type': 'connection_failure',
                'threshold_value': 1.0,
                'threshold_period': 15,
                'priority': 'critical'
            },
            {
                'name': 'Sync Failures',
                'description': 'Alert on sync operation failures',
                'condition_type': 'sync_failure',
                'threshold_value': 1.0,
                'threshold_period': 30,
                'priority': 'high'
            },
            {
                'name': 'Performance Issues',
                'description': 'Alert when operations take longer than 5 minutes',
                'condition_type': 'performance_degradation',
                'threshold_value': 300.0,  # 5 minutes in seconds
                'threshold_period': 60,
                'priority': 'medium'
            }
        ]
        
        created_rules = []
        for rule_data in default_rules:
            if not self.env['sap.alert.rule'].search([('name', '=', rule_data['name'])]):
                rule = self.env['sap.alert.rule'].create(rule_data)
                created_rules.append(rule)
        
        return {
            'status': 'success',
            'created_rules': len(created_rules),
            'rule_names': [rule.name for rule in created_rules]
        }
