# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Integration Logger

Centralized logging system for SAP integration operations.
"""

import logging
import json
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError

from ..config.sap_config import LOG_CONFIG, ERROR_MESSAGES


class SapLogger:
    """Centralized logger for SAP integration operations"""
    
    def __init__(self, name=None):
        self.logger = logging.getLogger(name or LOG_CONFIG['logger_name'])
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger configuration"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(LOG_CONFIG['log_format'])
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(getattr(logging, LOG_CONFIG['log_level']))
    
    def info(self, message, extra_data=None):
        """Log info message"""
        self._log('info', message, extra_data)
    
    def warning(self, message, extra_data=None):
        """Log warning message"""
        self._log('warning', message, extra_data)
    
    def error(self, message, extra_data=None):
        """Log error message"""
        self._log('error', message, extra_data)
    
    def debug(self, message, extra_data=None):
        """Log debug message"""
        self._log('debug', message, extra_data)
    
    def _log(self, level, message, extra_data=None):
        """Internal logging method"""
        if extra_data:
            message = f"{message} | Extra: {json.dumps(extra_data, default=str)}"
        
        getattr(self.logger, level)(message)


class SapSyncLog(models.Model):
    """Model to store SAP synchronization logs"""
    _name = 'sap.sync.log'
    _description = 'SAP Synchronization Log'
    _order = 'create_date desc'
    _rec_name = 'operation'
    
    # Basic Information
    backend_id = fields.Many2one(
        'sap.backend',
        string='SAP Backend',
        required=True,
        ondelete='cascade'
    )
    operation = fields.Char(
        string='Operation',
        required=True,
        help="Type of operation performed (e.g., 'Import Customer', 'Export Product')"
    )
    model_name = fields.Char(
        string='Model',
        help="Odoo model name affected by this operation"
    )
    external_id = fields.Char(
        string='External ID',
        help="External ID from SAP (e.g., CardCode, ItemCode)"
    )
    odoo_id = fields.Integer(
        string='Odoo ID',
        help="Odoo record ID affected by this operation"
    )
    
    # Status Information
    status = fields.Selection([
        ('success', 'Success'),
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('info', 'Info'),
    ], string='Status', required=True, default='info')
    
    # Message and Details
    message = fields.Text(
        string='Message',
        required=True,
        help="Log message describing what happened"
    )
    details = fields.Text(
        string='Details',
        help="Additional details in JSON format"
    )
    
    # Timing Information
    start_time = fields.Datetime(
        string='Start Time',
        help="When the operation started"
    )
    end_time = fields.Datetime(
        string='End Time',
        help="When the operation completed"
    )
    duration = fields.Float(
        string='Duration (seconds)',
        compute='_compute_duration',
        store=True,
        help="Duration of the operation in seconds"
    )
    
    # Error Information
    error_type = fields.Char(
        string='Error Type',
        help="Type of error that occurred"
    )
    error_traceback = fields.Text(
        string='Error Traceback',
        help="Full traceback of the error"
    )
    retry_count = fields.Integer(
        string='Retry Count',
        default=0,
        help="Number of times this operation was retried"
    )
    
    # Data Information
    data_size = fields.Integer(
        string='Data Size (bytes)',
        help="Size of data processed in bytes"
    )
    records_processed = fields.Integer(
        string='Records Processed',
        help="Number of records processed in this operation"
    )
    
    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        """Compute duration of the operation"""
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.duration = delta.total_seconds()
            else:
                record.duration = 0.0
    
    @api.model
    def create_log(self, backend_id, operation, status='info', message='', 
                   model_name=None, external_id=None, odoo_id=None, 
                   details=None, error_type=None, error_traceback=None,
                   start_time=None, end_time=None, data_size=0, 
                   records_processed=0, retry_count=0):
        """Create a new log entry"""
        return self.create({
            'backend_id': backend_id,
            'operation': operation,
            'status': status,
            'message': message,
            'model_name': model_name,
            'external_id': external_id,
            'odoo_id': odoo_id,
            'details': json.dumps(details) if details else None,
            'error_type': error_type,
            'error_traceback': error_traceback,
            'start_time': start_time or fields.Datetime.now(),
            'end_time': end_time or fields.Datetime.now(),
            'data_size': data_size,
            'records_processed': records_processed,
            'retry_count': retry_count,
        })
    
    @api.model
    def log_success(self, backend_id, operation, message, **kwargs):
        """Log a successful operation"""
        return self.create_log(
            backend_id=backend_id,
            operation=operation,
            status='success',
            message=message,
            **kwargs
        )
    
    @api.model
    def log_error(self, backend_id, operation, message, error_type=None, 
                  error_traceback=None, **kwargs):
        """Log an error"""
        return self.create_log(
            backend_id=backend_id,
            operation=operation,
            status='error',
            message=message,
            error_type=error_type,
            error_traceback=error_traceback,
            **kwargs
        )
    
    @api.model
    def log_warning(self, backend_id, operation, message, **kwargs):
        """Log a warning"""
        return self.create_log(
            backend_id=backend_id,
            operation=operation,
            status='warning',
            message=message,
            **kwargs
        )
    
    @api.model
    def log_info(self, backend_id, operation, message, **kwargs):
        """Log an info message"""
        return self.create_log(
            backend_id=backend_id,
            operation=operation,
            status='info',
            message=message,
            **kwargs
        )
    
    def get_logs_by_backend(self, backend_id, limit=100):
        """Get logs for a specific backend"""
        return self.search([
            ('backend_id', '=', backend_id)
        ], limit=limit)
    
    def get_error_logs(self, backend_id=None, limit=100):
        """Get error logs"""
        domain = [('status', '=', 'error')]
        if backend_id:
            domain.append(('backend_id', '=', backend_id))
        return self.search(domain, limit=limit)
    
    def get_recent_logs(self, hours=24, limit=100):
        """Get recent logs within specified hours"""
        from datetime import timedelta
        cutoff_time = fields.Datetime.now() - timedelta(hours=hours)
        return self.search([
            ('create_date', '>=', cutoff_time)
        ], limit=limit)
    
    def cleanup_old_logs(self, days=30):
        """Clean up logs older than specified days"""
        from datetime import timedelta
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_logs = self.search([
            ('create_date', '<', cutoff_date)
        ])
        old_logs.unlink()
        return len(old_logs)


class SapException(UserError):
    """Custom exception for SAP integration errors"""
    
    def __init__(self, message, error_code=None, details=None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class SapConnectionError(SapException):
    """Exception for SAP connection errors"""
    pass


class SapSyncError(SapException):
    """Exception for SAP synchronization errors"""
    pass


class SapValidationError(SapException):
    """Exception for SAP data validation errors"""
    pass
