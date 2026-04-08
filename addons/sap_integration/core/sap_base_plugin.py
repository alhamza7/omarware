# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Base Plugin

Base plugin class for extending SAP integration functionality.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .sap_logger import SapLogger, SapValidationError

_logger = logging.getLogger(__name__)


class SapBasePlugin:
    """Base plugin class for SAP integration extensions"""
    
    # Plugin Metadata (must be overridden in subclasses)
    PLUGIN_ID = None
    PLUGIN_NAME = None
    PLUGIN_VERSION = '1.0.0'
    PLUGIN_DESCRIPTION = ''
    PLUGIN_AUTHOR = ''
    PLUGIN_CATEGORY = 'general'
    PLUGIN_DEPENDENCIES = []
    PLUGIN_CONFIG_SCHEMA = {}
    
    def __init__(self, env=None, config=None):
        """
        Initialize the plugin
        
        :param env: Odoo environment
        :param config: Plugin configuration dictionary
        """
        if not self.PLUGIN_ID:
            raise SapValidationError("PLUGIN_ID must be defined in plugin class")
        if not self.PLUGIN_NAME:
            raise SapValidationError("PLUGIN_NAME must be defined in plugin class")
        
        self.env = env
        self.config = config or {}
        self.logger = SapLogger(f"sap_integration.plugin.{self.PLUGIN_ID}")
        self._initialized = False
        self._state = {}
        
    def initialize(self):
        """
        Initialize the plugin
        Called once when plugin is loaded
        Override this method in subclasses
        """
        self.logger.info(f"Initializing plugin: {self.PLUGIN_NAME} v{self.PLUGIN_VERSION}")
        self._validate_config()
        self._initialized = True
        
    def execute(self, context=None):
        """
        Execute the plugin
        Override this method in subclasses
        
        :param context: Execution context dictionary
        :return: Execution result dictionary
        """
        if not self._initialized:
            raise SapValidationError(f"Plugin {self.PLUGIN_ID} not initialized")
        
        self.logger.info(f"Executing plugin: {self.PLUGIN_NAME}")
        
        return {
            'status': 'success',
            'message': 'Plugin executed successfully',
            'plugin_id': self.PLUGIN_ID,
            'plugin_name': self.PLUGIN_NAME,
        }
    
    def cleanup(self):
        """
        Cleanup the plugin
        Called when plugin is unloaded
        Override this method in subclasses
        """
        self.logger.info(f"Cleaning up plugin: {self.PLUGIN_NAME}")
        self._initialized = False
        self._state = {}
    
    def get_config(self, key, default=None):
        """
        Get configuration value
        
        :param key: Configuration key
        :param default: Default value if key not found
        :return: Configuration value
        """
        return self.config.get(key, default)
    
    def set_config(self, config):
        """
        Set plugin configuration
        
        :param config: Configuration dictionary
        """
        self.config = config or {}
        self._validate_config()
    
    def get_state(self, key, default=None):
        """
        Get plugin state value
        
        :param key: State key
        :param default: Default value if key not found
        :return: State value
        """
        return self._state.get(key, default)
    
    def set_state(self, key, value):
        """
        Set plugin state value
        
        :param key: State key
        :param value: State value
        """
        self._state[key] = value
    
    def _validate_config(self):
        """Validate plugin configuration"""
        if not self.PLUGIN_CONFIG_SCHEMA:
            return
        
        for param_name, param_schema in self.PLUGIN_CONFIG_SCHEMA.items():
            param_required = param_schema.get('required', False)
            param_type = param_schema.get('type')
            param_default = param_schema.get('default')
            
            if param_required and param_name not in self.config:
                if param_default is not None:
                    self.config[param_name] = param_default
                else:
                    raise SapValidationError(
                        f"Required configuration parameter '{param_name}' not provided for plugin {self.PLUGIN_ID}"
                    )
            
            if param_name in self.config and param_type:
                value = self.config[param_name]
                if not isinstance(value, param_type):
                    raise SapValidationError(
                        f"Configuration parameter '{param_name}' must be of type {param_type.__name__}"
                    )
    
    def get_info(self):
        """
        Get plugin information
        
        :return: Plugin information dictionary
        """
        return {
            'id': self.PLUGIN_ID,
            'name': self.PLUGIN_NAME,
            'version': self.PLUGIN_VERSION,
            'description': self.PLUGIN_DESCRIPTION,
            'author': self.PLUGIN_AUTHOR,
            'category': self.PLUGIN_CATEGORY,
            'dependencies': self.PLUGIN_DEPENDENCIES,
            'initialized': self._initialized,
        }
    
    def is_initialized(self):
        """Check if plugin is initialized"""
        return self._initialized


class SapDataProcessorPlugin(SapBasePlugin):
    """Base plugin for data processing"""
    
    PLUGIN_CATEGORY = 'data_processing'
    
    def execute(self, context=None):
        """
        Execute data processing
        
        :param context: Context with 'data' key containing data to process
        :return: Processed data result
        """
        if not self._initialized:
            raise SapValidationError(f"Plugin {self.PLUGIN_ID} not initialized")
        
        data = context.get('data', []) if context else []
        processed_data = self.process_data(data, context)
        
        return {
            'status': 'success',
            'message': 'Data processed successfully',
            'plugin_id': self.PLUGIN_ID,
            'processed_data': processed_data,
            'record_count': len(processed_data) if isinstance(processed_data, list) else 1,
        }
    
    def process_data(self, data, context=None):
        """
        Process data - override in subclasses
        
        :param data: Data to process
        :param context: Processing context
        :return: Processed data
        """
        raise NotImplementedError("process_data method must be implemented in subclass")


class SapSyncPlugin(SapBasePlugin):
    """Base plugin for synchronization operations"""
    
    PLUGIN_CATEGORY = 'sync'
    
    def execute(self, context=None):
        """
        Execute synchronization
        
        :param context: Context with 'backend_id' and 'entity_type'
        :return: Sync result
        """
        if not self._initialized:
            raise SapValidationError(f"Plugin {self.PLUGIN_ID} not initialized")
        
        backend_id = context.get('backend_id') if context else None
        entity_type = context.get('entity_type') if context else None
        
        if not backend_id or not entity_type:
            raise SapValidationError("backend_id and entity_type are required for sync plugins")
        
        result = self.sync_data(backend_id, entity_type, context)
        
        return {
            'status': 'success',
            'message': 'Sync completed successfully',
            'plugin_id': self.PLUGIN_ID,
            'result': result,
        }
    
    def sync_data(self, backend_id, entity_type, context=None):
        """
        Sync data - override in subclasses
        
        :param backend_id: SAP backend ID
        :param entity_type: Entity type to sync
        :param context: Sync context
        :return: Sync result
        """
        raise NotImplementedError("sync_data method must be implemented in subclass")


class SapValidationPlugin(SapBasePlugin):
    """Base plugin for validation operations"""
    
    PLUGIN_CATEGORY = 'validation'
    
    def execute(self, context=None):
        """
        Execute validation
        
        :param context: Context with 'data' key containing data to validate
        :return: Validation result
        """
        if not self._initialized:
            raise SapValidationError(f"Plugin {self.PLUGIN_ID} not initialized")
        
        data = context.get('data') if context else None
        
        if data is None:
            raise SapValidationError("data is required for validation plugins")
        
        result = self.validate_data(data, context)
        
        return {
            'status': 'success',
            'message': 'Validation completed',
            'plugin_id': self.PLUGIN_ID,
            'validation_result': result,
        }
    
    def validate_data(self, data, context=None):
        """
        Validate data - override in subclasses
        
        :param data: Data to validate
        :param context: Validation context
        :return: Validation result with 'valid', 'errors', 'warnings' keys
        """
        raise NotImplementedError("validate_data method must be implemented in subclass")


class SapTransformationPlugin(SapBasePlugin):
    """Base plugin for data transformation operations"""
    
    PLUGIN_CATEGORY = 'transformation'
    
    def execute(self, context=None):
        """
        Execute transformation
        
        :param context: Context with 'data' key containing data to transform
        :return: Transformation result
        """
        if not self._initialized:
            raise SapValidationError(f"Plugin {self.PLUGIN_ID} not initialized")
        
        data = context.get('data') if context else None
        
        if data is None:
            raise SapValidationError("data is required for transformation plugins")
        
        transformed_data = self.transform_data(data, context)
        
        return {
            'status': 'success',
            'message': 'Transformation completed',
            'plugin_id': self.PLUGIN_ID,
            'transformed_data': transformed_data,
        }
    
    def transform_data(self, data, context=None):
        """
        Transform data - override in subclasses
        
        :param data: Data to transform
        :param context: Transformation context
        :return: Transformed data
        """
        raise NotImplementedError("transform_data method must be implemented in subclass")


