# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Base Plugin

Base class for SAP integration plugins.
"""

from odoo import models, fields, api
import logging
from odoo.exceptions import UserError, ValidationError
import json

from .sap_logger import SapLogger, SapValidationError
from .sap_base_service import SapBaseService


class SapBasePlugin:
    """Base class for SAP integration plugins"""
    
    # Plugin metadata
    PLUGIN_ID = 'base_plugin'
    PLUGIN_NAME = 'Base Plugin'
    PLUGIN_VERSION = '1.0.0'
    PLUGIN_DESCRIPTION = 'Base plugin class'
    PLUGIN_AUTHOR = 'SAP Integration Team'
    PLUGIN_CATEGORY = 'general'
    PLUGIN_DEPENDENCIES = []
    PLUGIN_CONFIG_SCHEMA = {}
    
    def __init__(self, env=None):
        """Initialize the plugin"""
        self.env = env
        self._config = {}
        self._initialized = False
        self._logger = SapLogger(f"sap_integration.plugin.{self.PLUGIN_ID}")
    
    def initialize(self):
        """Initialize the plugin"""
        raise NotImplementedError("Subclasses must implement initialize method")
    
    def execute(self, context=None):
        """Execute the plugin"""
        raise NotImplementedError("Subclasses must implement execute method")
    
    def cleanup(self):
        """Cleanup the plugin"""
        raise NotImplementedError("Subclasses must implement cleanup method")
    
    def get_plugin_info(self):
        """Get plugin information"""
        return {
            'id': self.PLUGIN_ID,
            'name': self.PLUGIN_NAME,
            'version': self.PLUGIN_VERSION,
            'description': self.PLUGIN_DESCRIPTION,
            'author': self.PLUGIN_AUTHOR,
            'category': self.PLUGIN_CATEGORY,
            'dependencies': self.PLUGIN_DEPENDENCIES,
            'config_schema': self.PLUGIN_CONFIG_SCHEMA
        }
    
    def set_config(self, config):
        """Set plugin configuration"""
        try:
            self._config = config or {}
            _logger.info(f"Configuration set for plugin {self.PLUGIN_ID}")
            
        except Exception as e:
            _logger.error(f"Error setting configuration: {str(e)}")
            raise SapValidationError(f"Failed to set configuration: {str(e)}")
    
    def get_config(self, key=None, default=None):
        """Get plugin configuration"""
        try:
            if key is None:
                return self._config
            
            return self._config.get(key, default)
            
        except Exception as e:
            _logger.error(f"Error getting configuration: {str(e)}")
            return default
    
    def validate_config(self, config):
        """Validate plugin configuration"""
        try:
            schema = self.PLUGIN_CONFIG_SCHEMA
            if not schema:
                return True
            
            for key, value in config.items():
                if key not in schema:
                    raise SapValidationError(f"Unknown configuration key: {key}")
                
                expected_type = schema[key].get('type')
                if expected_type and not isinstance(value, expected_type):
                    raise SapValidationError(f"Invalid type for {key}: expected {expected_type}")
                
                # Validate required fields
                if schema[key].get('required', False) and not value:
                    raise SapValidationError(f"Required configuration key {key} is missing")
            
            return True
            
        except Exception as e:
            _logger.error(f"Error validating configuration: {str(e)}")
            raise SapValidationError(f"Configuration validation failed: {str(e)}")
    
    def log_plugin_activity(self, activity_type, message, data=None):
        """Log plugin activity"""
        try:
            _logger.info(f"Plugin {self.PLUGIN_ID} - {activity_type}: {message}")
            
            # Log to activity log if available
            if hasattr(self.env, 'sap.user.activity.log'):
                self.env['sap.user.activity.log'].log_activity(
                    user_id=self.env.user.id,
                    activity_type='plugin_activity',
                    description=f"Plugin {self.PLUGIN_ID}: {message}",
                    additional_data={
                        'plugin_id': self.PLUGIN_ID,
                        'activity_type': activity_type,
                        'data': data
                    }
                )
            
        except Exception as e:
            _logger.error(f"Error logging plugin activity: {str(e)}")
    
    def get_dependencies(self):
        """Get plugin dependencies"""
        return self.PLUGIN_DEPENDENCIES
    
    def check_dependencies(self):
        """Check if all dependencies are satisfied"""
        try:
            plugin_manager = self.env['sap.plugin.manager']
            
            for dep in self.PLUGIN_DEPENDENCIES:
                if not plugin_manager._plugin_registry.get(dep):
                    return False
            
            return True
            
        except Exception as e:
            _logger.error(f"Error checking dependencies: {str(e)}")
            return False
    
    def get_status(self):
        """Get plugin status"""
        return {
            'initialized': self._initialized,
            'config': self._config,
            'dependencies_satisfied': self.check_dependencies()
        }


class SapDataProcessorPlugin(SapBasePlugin):
    """Base class for data processing plugins"""
    # _name = 'sap.data.processor.plugin'  # Not a model
    # _description = 'SAP Data Processor Plugin'  # Not a model
    
    PLUGIN_CATEGORY = 'data_processing'
    
    def process_data(self, data, context=None):
        """Process data"""
        raise NotImplementedError("Subclasses must implement process_data method")
    
    def execute(self, context=None):
        """Execute data processing"""
        try:
            data = context.get('data', [])
            result = self.process_data(data, context)
            
            self.log_plugin_activity('data_processing', f'Processed {len(data)} records')
            
            return {
                'status': 'success',
                'processed_count': len(data),
                'result': result
            }
            
        except Exception as e:
            _logger.error(f"Error processing data: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }


class SapSyncPlugin(SapBasePlugin):
    """Base class for sync plugins"""
    # _name = 'sap.sync.plugin'  # Not a model
    # _description = 'SAP Sync Plugin'  # Not a model
    
    PLUGIN_CATEGORY = 'sync'
    
    def sync_data(self, backend_id, entity_type, context=None):
        """Sync data"""
        raise NotImplementedError("Subclasses must implement sync_data method")
    
    def execute(self, context=None):
        """Execute sync operation"""
        try:
            backend_id = context.get('backend_id')
            entity_type = context.get('entity_type')
            
            if not backend_id or not entity_type:
                raise SapValidationError("Backend ID and entity type are required")
            
            result = self.sync_data(backend_id, entity_type, context)
            
            self.log_plugin_activity('sync', f'Synced {entity_type} for backend {backend_id}')
            
            return {
                'status': 'success',
                'backend_id': backend_id,
                'entity_type': entity_type,
                'result': result
            }
            
        except Exception as e:
            _logger.error(f"Error syncing data: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }


class SapValidationPlugin(SapBasePlugin):
    """Base class for validation plugins"""
    # _name = 'sap.validation.plugin'  # Not a model
    # _description = 'SAP Validation Plugin'  # Not a model
    
    PLUGIN_CATEGORY = 'validation'
    
    def validate_data(self, data, context=None):
        """Validate data"""
        raise NotImplementedError("Subclasses must implement validate_data method")
    
    def execute(self, context=None):
        """Execute validation"""
        try:
            data = context.get('data', {})
            result = self.validate_data(data, context)
            
            self.log_plugin_activity('validation', f'Validated data for {data.get("entity_type", "unknown")}')
            
            return {
                'status': 'success',
                'valid': result.get('valid', False),
                'errors': result.get('errors', []),
                'warnings': result.get('warnings', [])
            }
            
        except Exception as e:
            _logger.error(f"Error validating data: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }


class SapNotificationPlugin(SapBasePlugin):
    """Base class for notification plugins"""
    # _name = 'sap.notification.plugin'  # Not a model
    # _description = 'SAP Notification Plugin'  # Not a model
    
    PLUGIN_CATEGORY = 'notification'
    
    def send_notification(self, message, recipients, context=None):
        """Send notification"""
        raise NotImplementedError("Subclasses must implement send_notification method")
    
    def execute(self, context=None):
        """Execute notification"""
        try:
            message = context.get('message', '')
            recipients = context.get('recipients', [])
            
            if not message or not recipients:
                raise SapValidationError("Message and recipients are required")
            
            result = self.send_notification(message, recipients, context)
            
            self.log_plugin_activity('notification', f'Sent notification to {len(recipients)} recipients')
            
            return {
                'status': 'success',
                'recipients_count': len(recipients),
                'result': result
            }
            
        except Exception as e:
            _logger.error(f"Error sending notification: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }


class SapReportPlugin(SapBasePlugin):
    """Base class for report plugins"""
    # _name = 'sap.report.plugin'  # Not a model
    # _description = 'SAP Report Plugin'  # Not a model
    
    PLUGIN_CATEGORY = 'reporting'
    
    def generate_report(self, report_type, parameters, context=None):
        """Generate report"""
        raise NotImplementedError("Subclasses must implement generate_report method")
    
    def execute(self, context=None):
        """Execute report generation"""
        try:
            report_type = context.get('report_type')
            parameters = context.get('parameters', {})
            
            if not report_type:
                raise SapValidationError("Report type is required")
            
            result = self.generate_report(report_type, parameters, context)
            
            self.log_plugin_activity('report', f'Generated {report_type} report')
            
            return {
                'status': 'success',
                'report_type': report_type,
                'result': result
            }
            
        except Exception as e:
            _logger.error(f"Error generating report: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
