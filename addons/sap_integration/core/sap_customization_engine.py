# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Customization Engine

Customization engine for business-specific requirements and extensions.
"""

from odoo import models, fields, api
import logging
from odoo.exceptions import UserError, ValidationError
import json
import ast
import inspect
from datetime import datetime

from .sap_logger import SapLogger, SapValidationError
from .sap_base_service import SapBaseService


class SapCustomizationRule(models.Model):
    """SAP Customization Rule"""
    _name = 'sap.customization.rule'
    _description = 'SAP Customization Rule'
    _order = 'sequence, name'
    
    # Basic Information
    name = fields.Char(
        string='Rule Name',
        required=True,
        index=True
    )
    description = fields.Text(
        string='Description',
        help="Rule description and purpose"
    )
    
    # Rule Configuration
    rule_type = fields.Selection([
        ('data_mapping', 'Data Mapping'),
        ('validation', 'Validation'),
        ('transformation', 'Transformation'),
        ('business_logic', 'Business Logic'),
        ('notification', 'Notification'),
        ('custom', 'Custom')
    ], string='Rule Type', required=True)
    
    # Trigger Configuration
    trigger_model = fields.Char(
        string='Trigger Model',
        help="Model that triggers this rule"
    )
    trigger_field = fields.Char(
        string='Trigger Field',
        help="Field that triggers this rule"
    )
    trigger_condition = fields.Text(
        string='Trigger Condition',
        help="Python expression for trigger condition"
    )
    
    # Execution Configuration
    execution_order = fields.Integer(
        string='Execution Order',
        default=10,
        help="Order of execution (lower numbers execute first)"
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    # Rule Logic
    rule_code = fields.Text(
        string='Rule Code',
        required=True,
        help="Python code for the rule logic"
    )
    
    # Configuration
    config_data = fields.Text(
        string='Configuration Data',
        help="JSON configuration data for the rule"
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Statistics
    execution_count = fields.Integer(
        string='Execution Count',
        default=0,
        readonly=True
    )
    success_count = fields.Integer(
        string='Success Count',
        default=0,
        readonly=True
    )
    error_count = fields.Integer(
        string='Error Count',
        default=0,
        readonly=True
    )
    last_execution = fields.Datetime(
        string='Last Execution',
        readonly=True
    )
    
    # Constraints
    _sql_constraints = [
        ('unique_name', 'unique(name)', 
         'Rule name must be unique.'),
    ]
    
    def action_test_rule(self):
        """Test rule execution"""
        try:
            customization_engine = self.env['sap.customization.engine']
            result = customization_engine.execute_rule(
                rule_id=self.id,
                test_data={'test': True, 'message': 'Test execution'}
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Rule Test',
                    'message': f'Rule test completed: {result.get("status", "unknown")}',
                    'type': 'success' if result.get('success') else 'warning'
                }
            }
            
        except Exception as e:
            _logger.error(f"Error testing rule: {str(e)}")
            raise UserError(f"Failed to test rule: {str(e)}")
    
    def action_view_executions(self):
        """View rule executions"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Executions for {self.name}',
            'res_model': 'sap.customization.execution',
            'view_mode': 'tree,form',
            'domain': [('rule_id', '=', self.id)],
            'context': {'default_rule_id': self.id}
        }


class SapCustomizationExecution(models.Model):
    """SAP Customization Execution Log"""
    _name = 'sap.customization.execution'
    _description = 'SAP Customization Execution'
    _order = 'execution_time desc'
    
    # Rule Information
    rule_id = fields.Many2one(
        'sap.customization.rule',
        string='Rule',
        required=True,
        ondelete='cascade'
    )
    
    # Execution Information
    execution_time = fields.Datetime(
        string='Execution Time',
        default=fields.Datetime.now,
        required=True
    )
    
    input_data = fields.Text(
        string='Input Data',
        help="Input data for the rule execution"
    )
    
    output_data = fields.Text(
        string='Output Data',
        help="Output data from the rule execution"
    )
    
    # Status
    success = fields.Boolean(
        string='Success',
        default=False
    )
    
    error_message = fields.Text(
        string='Error Message',
        help="Error message if execution failed"
    )
    
    execution_duration = fields.Float(
        string='Execution Duration (ms)',
        help="Execution duration in milliseconds"
    )
    
    # Context
    context_data = fields.Text(
        string='Context Data',
        help="Context data for the execution"
    )


class SapCustomizationEngine(SapBaseService):
    """SAP Customization Engine"""
    _name = 'sap.customization.engine'
    _description = 'SAP Customization Engine'
    
    _rule_cache = {}
    
    @api.model
    def execute_rule(self, rule_id, input_data, context=None):
        """Execute a customization rule"""
        try:
            rule = self.env['sap.customization.rule'].browse(rule_id)
            if not rule.exists() or not rule.active:
                raise SapValidationError(f"Rule {rule_id} not found or inactive")
            
            # Prepare execution context
            exec_context = self._prepare_execution_context(rule, input_data, context)
            
            # Execute rule
            start_time = datetime.now()
            result = self._execute_rule_code(rule, exec_context)
            execution_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log execution
            self._log_execution(rule, input_data, result, execution_duration, context)
            
            # Update rule statistics
            rule.execution_count += 1
            if result.get('success', False):
                rule.success_count += 1
            else:
                rule.error_count += 1
            rule.last_execution = fields.Datetime.now()
            
            return result
            
        except Exception as e:
            _logger.error(f"Error executing rule {rule_id}: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    def _prepare_execution_context(self, rule, input_data, context):
        """Prepare execution context for rule"""
        try:
            exec_context = {
                'input_data': input_data,
                'context': context or {},
                'rule': rule,
                'env': self.env,
                'logger': _logger,
                'datetime': datetime,
                'json': json,
                'fields': fields,
                'api': api
            }
            
            # Add configuration data
            if rule.config_data:
                try:
                    config = json.loads(rule.config_data)
                    exec_context.update(config)
                except json.JSONDecodeError:
                    _logger.warning(f"Invalid configuration data for rule {rule.name}")
            
            return exec_context
            
        except Exception as e:
            _logger.error(f"Error preparing execution context: {str(e)}")
            raise SapValidationError(f"Failed to prepare execution context: {str(e)}")
    
    def _execute_rule_code(self, rule, exec_context):
        """Execute rule code"""
        try:
            # Create a safe execution environment
            safe_globals = {
                '__builtins__': {
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'min': min,
                    'max': max,
                    'sum': sum,
                    'abs': abs,
                    'round': round,
                    'sorted': sorted,
                    'reversed': reversed,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'any': any,
                    'all': all,
                    'isinstance': isinstance,
                    'hasattr': hasattr,
                    'getattr': getattr,
                    'setattr': setattr,
                    'type': type,
                    'range': range,
                    'print': print,
                    'json': json,
                    'datetime': datetime,
                    'fields': fields,
                    'api': api
                }
            }
            
            # Add rule context
            safe_globals.update(exec_context)
            
            # Execute rule code
            exec(rule.rule_code, safe_globals)
            
            # Get result from context
            result = safe_globals.get('result', {
                'success': True,
                'message': 'Rule executed successfully'
            })
            
            return result
            
        except Exception as e:
            _logger.error(f"Error executing rule code: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    def _log_execution(self, rule, input_data, result, execution_duration, context):
        """Log rule execution"""
        try:
            self.env['sap.customization.execution'].create({
                'rule_id': rule.id,
                'input_data': json.dumps(input_data) if input_data else '',
                'output_data': json.dumps(result) if result else '',
                'success': result.get('success', False),
                'error_message': result.get('error_message', ''),
                'execution_duration': execution_duration,
                'context_data': json.dumps(context) if context else ''
            })
            
        except Exception as e:
            _logger.error(f"Error logging execution: {str(e)}")
    
    @api.model
    def execute_rules_for_model(self, model_name, record_id, trigger_field=None, context=None):
        """Execute rules for a specific model and record"""
        try:
            # Find applicable rules
            domain = [
                ('active', '=', True),
                ('trigger_model', '=', model_name)
            ]
            
            if trigger_field:
                domain.append(('trigger_field', '=', trigger_field))
            
            rules = self.env['sap.customization.rule'].search(domain, order='execution_order')
            
            if not rules:
                return {
                    'success': True,
                    'message': 'No applicable rules found',
                    'executed_rules': 0
                }
            
            # Get record data
            record = self.env[model_name].browse(record_id)
            if not record.exists():
                raise SapValidationError(f"Record {record_id} not found in model {model_name}")
            
            # Prepare input data
            input_data = {
                'model_name': model_name,
                'record_id': record_id,
                'record_data': record.read()[0] if record else {},
                'trigger_field': trigger_field
            }
            
            # Execute rules
            executed_rules = []
            for rule in rules:
                try:
                    # Check trigger condition
                    if rule.trigger_condition:
                        if not self._evaluate_trigger_condition(rule, input_data):
                            continue
                    
                    # Execute rule
                    result = self.execute_rule(rule.id, input_data, context)
                    executed_rules.append({
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'result': result
                    })
                    
                except Exception as e:
                    _logger.error(f"Error executing rule {rule.name}: {str(e)}")
                    executed_rules.append({
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'result': {
                            'success': False,
                            'error_message': str(e)
                        }
                    })
            
            return {
                'success': True,
                'message': f'Executed {len(executed_rules)} rules',
                'executed_rules': len(executed_rules),
                'results': executed_rules
            }
            
        except Exception as e:
            _logger.error(f"Error executing rules for model: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    def _evaluate_trigger_condition(self, rule, input_data):
        """Evaluate trigger condition"""
        try:
            if not rule.trigger_condition:
                return True
            
            # Create safe evaluation context
            safe_globals = {
                '__builtins__': {
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'min': min,
                    'max': max,
                    'sum': sum,
                    'abs': abs,
                    'round': round,
                    'sorted': sorted,
                    'reversed': reversed,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'any': any,
                    'all': all,
                    'isinstance': isinstance,
                    'hasattr': hasattr,
                    'getattr': getattr,
                    'setattr': setattr,
                    'type': type,
                    'range': range,
                    'print': print,
                    'json': json,
                    'datetime': datetime
                }
            }
            
            # Add input data to context
            safe_globals.update(input_data)
            
            # Evaluate condition
            result = eval(rule.trigger_condition, safe_globals)
            
            return bool(result)
            
        except Exception as e:
            _logger.error(f"Error evaluating trigger condition: {str(e)}")
            return False
    
    @api.model
    def create_rule(self, name, rule_type, rule_code, **kwargs):
        """Create customization rule"""
        try:
            rule_vals = {
                'name': name,
                'rule_type': rule_type,
                'rule_code': rule_code,
                'description': kwargs.get('description', ''),
                'trigger_model': kwargs.get('trigger_model'),
                'trigger_field': kwargs.get('trigger_field'),
                'trigger_condition': kwargs.get('trigger_condition'),
                'execution_order': kwargs.get('execution_order', 10),
                'config_data': json.dumps(kwargs.get('config_data', {})),
                'active': kwargs.get('active', True)
            }
            
            rule = self.env['sap.customization.rule'].create(rule_vals)
            
            _logger.info(f"Created customization rule: {name}")
            
            return rule
            
        except Exception as e:
            _logger.error(f"Error creating rule: {str(e)}")
            raise SapValidationError(f"Failed to create rule: {str(e)}")
    
    @api.model
    def validate_rule_code(self, rule_code):
        """Validate rule code syntax"""
        try:
            # Try to compile the code
            compile(rule_code, '<string>', 'exec')
            
            return {
                'valid': True,
                'message': 'Rule code is valid'
            }
            
        except SyntaxError as e:
            return {
                'valid': False,
                'message': f'Syntax error: {str(e)}'
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f'Error: {str(e)}'
            }
    
    @api.model
    def get_rule_statistics(self, rule_id=None, days=30):
        """Get rule execution statistics"""
        try:
            domain = [
                ('execution_time', '>=', fields.Datetime.now() - timedelta(days=days))
            ]
            
            if rule_id:
                domain.append(('rule_id', '=', rule_id))
            
            executions = self.env['sap.customization.execution'].search(domain)
            
            stats = {
                'total_executions': len(executions),
                'successful_executions': len(executions.filtered('success')),
                'failed_executions': len(executions.filtered(lambda e: not e.success)),
                'success_rate': 0,
                'average_duration': 0,
                'by_rule': {}
            }
            
            if executions:
                stats['success_rate'] = (len(executions.filtered('success')) / len(executions)) * 100
                stats['average_duration'] = sum(executions.mapped('execution_duration')) / len(executions)
            
            # Group by rule
            for execution in executions:
                rule_name = execution.rule_id.name
                if rule_name not in stats['by_rule']:
                    stats['by_rule'][rule_name] = 0
                stats['by_rule'][rule_name] += 1
            
            return stats
            
        except Exception as e:
            _logger.error(f"Error getting rule statistics: {str(e)}")
            return {}
    
    @api.model
    def get_available_functions(self):
        """Get available functions for rule code"""
        try:
            functions = {
                'data_manipulation': [
                    'len', 'str', 'int', 'float', 'bool',
                    'list', 'dict', 'tuple', 'set',
                    'min', 'max', 'sum', 'abs', 'round',
                    'sorted', 'reversed', 'enumerate', 'zip',
                    'map', 'filter', 'any', 'all'
                ],
                'type_checking': [
                    'isinstance', 'hasattr', 'getattr', 'setattr', 'type'
                ],
                'iteration': [
                    'range', 'enumerate', 'zip', 'map', 'filter'
                ],
                'json_operations': [
                    'json.dumps', 'json.loads'
                ],
                'datetime_operations': [
                    'datetime.now', 'datetime.strptime', 'datetime.strftime'
                ],
                'odoo_specific': [
                    'fields.Datetime.now', 'fields.Datetime.to_string',
                    'api.Environment', 'env'
                ]
            }
            
            return functions
            
        except Exception as e:
            _logger.error(f"Error getting available functions: {str(e)}")
            return {}
