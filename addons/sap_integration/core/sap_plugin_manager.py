# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Plugin Manager

Plugin architecture for easy extension and customization of SAP integration.
"""

from odoo import models, fields, api
import logging
from odoo.exceptions import UserError, ValidationError
import importlib
import inspect
import json
import os
from datetime import datetime

from .sap_logger import SapLogger, SapValidationError
from .sap_base_service import SapBaseService


class SapPluginManager(SapBaseService):
    """SAP Plugin Manager for extensibility"""
    _name = 'sap.plugin.manager'
    _description = 'SAP Plugin Manager'
    
    _plugin_registry = {}
    _plugin_instances = {}
    
    @api.model
    def register_plugin(self, plugin_class, plugin_info):
        """
        Register a new plugin
        
        :param plugin_class: Plugin class to register
        :param plugin_info: Plugin information dictionary
        :return: Registration result
        """
        try:
            plugin_id = plugin_info.get('id')
            if not plugin_id:
                raise SapValidationError("Plugin ID is required")
            
            if plugin_id in self._plugin_registry:
                raise SapValidationError(f"Plugin {plugin_id} is already registered")
            
            # Validate plugin class
            if not self._validate_plugin_class(plugin_class):
                raise SapValidationError("Invalid plugin class")
            
            # Register plugin
            self._plugin_registry[plugin_id] = {
                'class': plugin_class,
                'info': plugin_info,
                'status': 'registered',
                'registered_at': datetime.now()
            }
            
            _logger.info(f"Registered plugin: {plugin_id}")
            
            return {
                'status': 'success',
                'plugin_id': plugin_id,
                'message': f'Plugin {plugin_id} registered successfully'
            }
            
        except Exception as e:
            _logger.error(f"Error registering plugin: {str(e)}")
            raise SapValidationError(f"Failed to register plugin: {str(e)}")
    
    def _validate_plugin_class(self, plugin_class):
        """Validate plugin class structure"""
        try:
            # Check if class has required methods
            required_methods = ['initialize', 'execute', 'cleanup']
            for method in required_methods:
                if not hasattr(plugin_class, method):
                    return False
            
            # Check if class is a subclass of SapBasePlugin
            try:
                from .sap_base_plugin import SapBasePlugin
                return issubclass(plugin_class, SapBasePlugin)
            except ImportError:
                return False
            
        except Exception as e:
            _logger.error(f"Error validating plugin class: {str(e)}")
            return False
    
    @api.model
    def unregister_plugin(self, plugin_id):
        """Unregister a plugin"""
        try:
            if plugin_id not in self._plugin_registry:
                raise SapValidationError(f"Plugin {plugin_id} is not registered")
            
            # Cleanup plugin instance if exists
            if plugin_id in self._plugin_instances:
                self._cleanup_plugin_instance(plugin_id)
            
            # Remove from registry
            del self._plugin_registry[plugin_id]
            
            _logger.info(f"Unregistered plugin: {plugin_id}")
            
            return {
                'status': 'success',
                'message': f'Plugin {plugin_id} unregistered successfully'
            }
            
        except Exception as e:
            _logger.error(f"Error unregistering plugin: {str(e)}")
            raise SapValidationError(f"Failed to unregister plugin: {str(e)}")
    
    @api.model
    def get_plugin(self, plugin_id):
        """Get plugin instance"""
        try:
            if plugin_id not in self._plugin_registry:
                raise SapValidationError(f"Plugin {plugin_id} is not registered")
            
            # Create instance if not exists
            if plugin_id not in self._plugin_instances:
                self._create_plugin_instance(plugin_id)
            
            return self._plugin_instances[plugin_id]
            
        except Exception as e:
            _logger.error(f"Error getting plugin: {str(e)}")
            raise SapValidationError(f"Failed to get plugin: {str(e)}")
    
    def _create_plugin_instance(self, plugin_id):
        """Create plugin instance"""
        try:
            plugin_info = self._plugin_registry[plugin_id]
            plugin_class = plugin_info['class']
            
            # Create instance
            instance = plugin_class(self.env)
            
            # Initialize plugin
            instance.initialize()
            
            # Store instance
            self._plugin_instances[plugin_id] = instance
            
            _logger.info(f"Created plugin instance: {plugin_id}")
            
        except Exception as e:
            _logger.error(f"Error creating plugin instance: {str(e)}")
            raise SapValidationError(f"Failed to create plugin instance: {str(e)}")
    
    def _cleanup_plugin_instance(self, plugin_id):
        """Cleanup plugin instance"""
        try:
            if plugin_id in self._plugin_instances:
                instance = self._plugin_instances[plugin_id]
                instance.cleanup()
                del self._plugin_instances[plugin_id]
                
                _logger.info(f"Cleaned up plugin instance: {plugin_id}")
                
        except Exception as e:
            _logger.error(f"Error cleaning up plugin instance: {str(e)}")
    
    @api.model
    def execute_plugin(self, plugin_id, context=None):
        """Execute plugin"""
        try:
            plugin = self.get_plugin(plugin_id)
            
            # Execute plugin
            result = plugin.execute(context or {})
            
            _logger.info(f"Executed plugin: {plugin_id}")
            
            return {
                'status': 'success',
                'plugin_id': plugin_id,
                'result': result
            }
            
        except Exception as e:
            _logger.error(f"Error executing plugin: {str(e)}")
            raise SapValidationError(f"Failed to execute plugin: {str(e)}")
    
    @api.model
    def get_registered_plugins(self):
        """Get list of registered plugins"""
        try:
            plugins = []
            for plugin_id, plugin_info in self._plugin_registry.items():
                plugins.append({
                    'id': plugin_id,
                    'name': plugin_info['info'].get('name', plugin_id),
                    'version': plugin_info['info'].get('version', '1.0.0'),
                    'description': plugin_info['info'].get('description', ''),
                    'author': plugin_info['info'].get('author', ''),
                    'status': plugin_info['status'],
                    'registered_at': plugin_info['registered_at']
                })
            
            return plugins
            
        except Exception as e:
            _logger.error(f"Error getting registered plugins: {str(e)}")
            return []
    
    @api.model
    def load_plugins_from_directory(self, directory_path):
        """Load plugins from directory"""
        try:
            if not os.path.exists(directory_path):
                raise SapValidationError(f"Directory {directory_path} does not exist")
            
            loaded_plugins = []
            
            for filename in os.listdir(directory_path):
                if filename.endswith('.py') and not filename.startswith('__'):
                    try:
                        # Load plugin module
                        module_name = filename[:-3]
                        module_path = os.path.join(directory_path, filename)
                        
                        spec = importlib.util.spec_from_file_location(module_name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Find plugin classes
                        for name, obj in inspect.getmembers(module):
                            if (inspect.isclass(obj) and 
                                hasattr(obj, '__module__') and 
                                obj.__module__ == module_name):
                                
                                # Check if it's a plugin class
                                if self._is_plugin_class(obj):
                                    plugin_info = self._extract_plugin_info(obj)
                                    self.register_plugin(obj, plugin_info)
                                    loaded_plugins.append(plugin_info['id'])
                        
                    except Exception as e:
                        _logger.warning(f"Error loading plugin from {filename}: {str(e)}")
                        continue
            
            _logger.info(f"Loaded {len(loaded_plugins)} plugins from {directory_path}")
            
            return {
                'status': 'success',
                'loaded_plugins': loaded_plugins,
                'message': f'Loaded {len(loaded_plugins)} plugins'
            }
            
        except Exception as e:
            _logger.error(f"Error loading plugins from directory: {str(e)}")
            raise SapValidationError(f"Failed to load plugins: {str(e)}")
    
    def _is_plugin_class(self, obj):
        """Check if class is a plugin class"""
        try:
            from .sap_base_plugin import SapBasePlugin
            return (inspect.isclass(obj) and 
                    issubclass(obj, SapBasePlugin) and 
                    obj != SapBasePlugin)
        except (ImportError, Exception):
            return False
    
    def _extract_plugin_info(self, plugin_class):
        """Extract plugin information from class"""
        try:
            # Get plugin metadata
            plugin_info = {
                'id': getattr(plugin_class, 'PLUGIN_ID', plugin_class.__name__.lower()),
                'name': getattr(plugin_class, 'PLUGIN_NAME', plugin_class.__name__),
                'version': getattr(plugin_class, 'PLUGIN_VERSION', '1.0.0'),
                'description': getattr(plugin_class, 'PLUGIN_DESCRIPTION', ''),
                'author': getattr(plugin_class, 'PLUGIN_AUTHOR', ''),
                'category': getattr(plugin_class, 'PLUGIN_CATEGORY', 'general'),
                'dependencies': getattr(plugin_class, 'PLUGIN_DEPENDENCIES', []),
                'config_schema': getattr(plugin_class, 'PLUGIN_CONFIG_SCHEMA', {})
            }
            
            return plugin_info
            
        except Exception as e:
            _logger.error(f"Error extracting plugin info: {str(e)}")
            return {
                'id': plugin_class.__name__.lower(),
                'name': plugin_class.__name__,
                'version': '1.0.0',
                'description': '',
                'author': '',
                'category': 'general',
                'dependencies': [],
                'config_schema': {}
            }
    
    @api.model
    def validate_plugin_dependencies(self, plugin_id):
        """Validate plugin dependencies"""
        try:
            if plugin_id not in self._plugin_registry:
                raise SapValidationError(f"Plugin {plugin_id} is not registered")
            
            plugin_info = self._plugin_registry[plugin_id]
            dependencies = plugin_info['info'].get('dependencies', [])
            
            missing_dependencies = []
            for dep in dependencies:
                if dep not in self._plugin_registry:
                    missing_dependencies.append(dep)
            
            if missing_dependencies:
                return {
                    'status': 'error',
                    'missing_dependencies': missing_dependencies,
                    'message': f'Missing dependencies: {", ".join(missing_dependencies)}'
                }
            
            return {
                'status': 'success',
                'message': 'All dependencies are satisfied'
            }
            
        except Exception as e:
            _logger.error(f"Error validating plugin dependencies: {str(e)}")
            raise SapValidationError(f"Failed to validate dependencies: {str(e)}")
    
    @api.model
    def get_plugin_configuration(self, plugin_id):
        """Get plugin configuration"""
        try:
            if plugin_id not in self._plugin_registry:
                raise SapValidationError(f"Plugin {plugin_id} is not registered")
            
            plugin_info = self._plugin_registry[plugin_id]
            config_schema = plugin_info['info'].get('config_schema', {})
            
            return {
                'plugin_id': plugin_id,
                'config_schema': config_schema,
                'current_config': self._get_plugin_config(plugin_id)
            }
            
        except Exception as e:
            _logger.error(f"Error getting plugin configuration: {str(e)}")
            raise SapValidationError(f"Failed to get plugin configuration: {str(e)}")
    
    def _get_plugin_config(self, plugin_id):
        """Get current plugin configuration"""
        try:
            # This would typically read from a configuration store
            # For now, return empty config
            return {}
            
        except Exception as e:
            _logger.error(f"Error getting plugin config: {str(e)}")
            return {}
    
    @api.model
    def update_plugin_configuration(self, plugin_id, config):
        """Update plugin configuration"""
        try:
            if plugin_id not in self._plugin_registry:
                raise SapValidationError(f"Plugin {plugin_id} is not registered")
            
            # Validate configuration
            plugin_info = self._plugin_registry[plugin_id]
            config_schema = plugin_info['info'].get('config_schema', {})
            
            if not self._validate_config(config, config_schema):
                raise SapValidationError("Invalid configuration")
            
            # Update configuration
            self._set_plugin_config(plugin_id, config)
            
            _logger.info(f"Updated configuration for plugin: {plugin_id}")
            
            return {
                'status': 'success',
                'message': f'Configuration updated for plugin {plugin_id}'
            }
            
        except Exception as e:
            _logger.error(f"Error updating plugin configuration: {str(e)}")
            raise SapValidationError(f"Failed to update configuration: {str(e)}")
    
    def _validate_config(self, config, schema):
        """Validate configuration against schema"""
        try:
            # Simple validation - in a real scenario, you'd use a proper schema validator
            for key, value in config.items():
                if key not in schema:
                    return False
                
                expected_type = schema[key].get('type')
                if expected_type and not isinstance(value, expected_type):
                    return False
            
            return True
            
        except Exception as e:
            _logger.error(f"Error validating config: {str(e)}")
            return False
    
    def _set_plugin_config(self, plugin_id, config):
        """Set plugin configuration"""
        try:
            # This would typically store in a configuration store
            # For now, just log the configuration
            _logger.info(f"Setting config for plugin {plugin_id}: {config}")
            
        except Exception as e:
            _logger.error(f"Error setting plugin config: {str(e)}")
    
    @api.model
    def get_plugin_status(self, plugin_id):
        """Get plugin status"""
        try:
            if plugin_id not in self._plugin_registry:
                return {
                    'status': 'not_registered',
                    'message': 'Plugin is not registered'
                }
            
            plugin_info = self._plugin_registry[plugin_id]
            instance_exists = plugin_id in self._plugin_instances
            
            return {
                'status': plugin_info['status'],
                'registered_at': plugin_info['registered_at'],
                'instance_exists': instance_exists,
                'dependencies': plugin_info['info'].get('dependencies', [])
            }
            
        except Exception as e:
            _logger.error(f"Error getting plugin status: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @api.model
    def cleanup_all_plugins(self):
        """Cleanup all plugin instances"""
        try:
            for plugin_id in list(self._plugin_instances.keys()):
                self._cleanup_plugin_instance(plugin_id)
            
            _logger.info("Cleaned up all plugin instances")
            
            return {
                'status': 'success',
                'message': 'All plugin instances cleaned up'
            }
            
        except Exception as e:
            _logger.error(f"Error cleaning up plugins: {str(e)}")
            raise SapValidationError(f"Failed to cleanup plugins: {str(e)}")
