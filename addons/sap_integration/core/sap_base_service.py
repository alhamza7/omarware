# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Base Service

Base service class for SAP integration operations.
Provides common functionality for all SAP services.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import json
import traceback
from datetime import datetime

from ..config.sap_config import (
    SYNC_CONFIG, ERROR_MESSAGES, VALIDATION_RULES, DEFAULT_VALUES
)
from .sap_logger import SapLogger, SapSyncLog, SapException, SapConnectionError, SapSyncError, SapValidationError


class SapBaseService(models.AbstractModel):
    """Base service class for SAP integration operations"""
    _name = 'sap.base.service'
    _description = 'SAP Base Service'
    
    @property
    def logger(self):
        return SapLogger(f"sap_integration.{self._name}")
    
    def _validate_required_fields(self, data, model_name):
        """Validate required fields for a model"""
        required_fields = VALIDATION_RULES['required_fields'].get(model_name, [])
        missing_fields = []
        
        for field in required_fields:
            if not data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            raise SapValidationError(
                f"Missing required fields: {', '.join(missing_fields)}",
                error_code='MISSING_REQUIRED_FIELDS',
                details={'missing_fields': missing_fields}
            )
    
    def _validate_field_lengths(self, data, model_name):
        """Validate field lengths"""
        max_lengths = VALIDATION_RULES['max_lengths']
        errors = []
        
        for field, max_length in max_lengths.items():
            if field in data and data[field]:
                if len(str(data[field])) > max_length:
                    errors.append(f"{field} exceeds maximum length of {max_length}")
        
        if errors:
            raise SapValidationError(
                f"Field length validation failed: {'; '.join(errors)}",
                error_code='FIELD_LENGTH_EXCEEDED',
                details={'errors': errors}
            )
    
    def _validate_data(self, data, model_name):
        """Validate data before processing"""
        try:
            self._validate_required_fields(data, model_name)
            self._validate_field_lengths(data, model_name)
            return True
        except SapValidationError:
            raise
        except Exception as e:
            raise SapValidationError(
                f"Data validation failed: {str(e)}",
                error_code='VALIDATION_ERROR',
                details={'error': str(e)}
            )
    
    def _apply_default_values(self, data, model_name):
        """Apply default values to data"""
        defaults = DEFAULT_VALUES.get(model_name, {})
        for field, value in defaults.items():
            if field not in data or not data[field]:
                data[field] = value
        return data
    
    def _log_operation(self, backend_id, operation, status, message, **kwargs):
        """Log an operation"""
        return self.env['sap.sync.log'].create_log(
            backend_id=backend_id,
            operation=operation,
            status=status,
            message=message,
            **kwargs
        )
    
    def _log_success(self, backend_id, operation, message, **kwargs):
        """Log a successful operation"""
        return self.env['sap.sync.log'].log_success(
            backend_id=backend_id,
            operation=operation,
            message=message,
            **kwargs
        )
    
    def _log_error(self, backend_id, operation, message, error_type=None, 
                   error_traceback=None, **kwargs):
        """Log an error"""
        return self.env['sap.sync.log'].log_error(
            backend_id=backend_id,
            operation=operation,
            message=message,
            error_type=error_type,
            error_traceback=error_traceback,
            **kwargs
        )
    
    def _log_warning(self, backend_id, operation, message, **kwargs):
        """Log a warning"""
        return self.env['sap.sync.log'].log_warning(
            backend_id=backend_id,
            operation=operation,
            message=message,
            **kwargs
        )
    
    def _log_info(self, backend_id, operation, message, **kwargs):
        """Log an info message"""
        return self.env['sap.sync.log'].log_info(
            backend_id=backend_id,
            operation=operation,
            message=message,
            **kwargs
        )
    
    def _handle_exception(self, backend_id, operation, exception, **kwargs):
        """Handle exceptions and log them appropriately"""
        error_type = type(exception).__name__
        error_traceback = traceback.format_exc()
        
        if isinstance(exception, SapException):
            message = str(exception)
            status = 'error'
        elif isinstance(exception, (UserError, ValidationError)):
            message = str(exception)
            status = 'error'
        else:
            message = f"Unexpected error: {str(exception)}"
            status = 'error'
        
        self._log_error(
            backend_id=backend_id,
            operation=operation,
            message=message,
            error_type=error_type,
            error_traceback=error_traceback,
            **kwargs
        )
        
        self.logger.error(f"{operation} failed: {message}", {
            'backend_id': backend_id,
            'error_type': error_type,
            'traceback': error_traceback
        })
        
        return message, error_type, error_traceback
    
    def _get_backend_connection(self, backend_id):
        """Get SAP backend connection"""
        backend = self.env['sap.backend'].browse(backend_id)
        if not backend.exists():
            raise SapConnectionError(
                f"Backend with ID {backend_id} not found",
                error_code='BACKEND_NOT_FOUND'
            )
        
        if not backend.active:
            raise SapConnectionError(
                ERROR_MESSAGES['backend_inactive'],
                error_code='BACKEND_INACTIVE'
            )
        
        try:
            return backend.get_connection()
        except Exception as e:
            raise SapConnectionError(
                f"{ERROR_MESSAGES['connection_failed']}: {str(e)}",
                error_code='CONNECTION_FAILED',
                details={'error': str(e)}
            )
    
    def _prepare_sync_data(self, data, model_name):
        """Prepare data for synchronization"""
        try:
            # Apply default values
            data = self._apply_default_values(data, model_name)
            
            # Validate data
            self._validate_data(data, model_name)
            
            return data
        except SapValidationError:
            raise
        except Exception as e:
            raise SapValidationError(
                f"Data preparation failed: {str(e)}",
                error_code='DATA_PREPARATION_FAILED',
                details={'error': str(e)}
            )
    
    def _format_sync_summary(self, results):
        """Format synchronization results summary"""
        summary = {
            'total_processed': results.get('total_processed', 0),
            'successful': results.get('successful', 0),
            'failed': results.get('failed', 0),
            'warnings': results.get('warnings', 0),
            'duration': results.get('duration', 0),
        }
        
        if results.get('errors'):
            summary['errors'] = results['errors']
        
        if results.get('warnings_list'):
            summary['warnings_list'] = results['warnings_list']
        
        return summary
    
    def _create_sync_result(self, operation, backend_id, **kwargs):
        """Create a sync result object"""
        return {
            'operation': operation,
            'backend_id': backend_id,
            'timestamp': fields.Datetime.now(),
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'warnings': 0,
            'errors': [],
            'warnings_list': [],
            'duration': 0,
            **kwargs
        }
    
    def _update_sync_result(self, result, **kwargs):
        """Update sync result with new data"""
        result.update(kwargs)
        return result
    
    def _finalize_sync_result(self, result):
        """Finalize sync result with summary"""
        result['summary'] = self._format_sync_summary(result)
        return result
