# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Error Analyzer

Advanced error detection and analysis system for SAP integration.
"""

from odoo import models, fields, api
import logging
from odoo.exceptions import UserError
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from ..config.sap_config import ERROR_MESSAGES, VALIDATION_RULES
from .sap_logger import SapLogger, SapSyncError, SapValidationError


class SapErrorAnalyzer(models.AbstractModel):
    """Advanced error analysis and detection system"""
    _name = 'sap.error.analyzer'
    _description = 'SAP Error Analyzer'
    
    def _setup(self):
        super()._setup()
        _logger = SapLogger(f"sap_integration.{self._name}")
    
    def analyze_sync_failures(self, backend_id=None, days=7):
        """Analyze sync failures and provide detailed insights"""
        try:
            # Get error logs for the specified period
            domain = [
                ('status', '=', 'error'),
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=days))
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            error_logs = self.env['sap.sync.log'].search(domain)
            
            if not error_logs:
                return {
                    'status': 'no_errors',
                    'message': 'No sync errors found in the specified period',
                    'analysis': {}
                }
            
            # Perform detailed analysis
            analysis = {
                'total_errors': len(error_logs),
                'error_types': self._analyze_error_types(error_logs),
                'operation_breakdown': self._analyze_operations(error_logs),
                'backend_breakdown': self._analyze_backends(error_logs),
                'model_breakdown': self._analyze_models(error_logs),
                'time_patterns': self._analyze_time_patterns(error_logs),
                'common_issues': self._identify_common_issues(error_logs),
                'recommendations': self._generate_recommendations(error_logs),
                'trends': self._analyze_trends(error_logs, days)
            }
            
            return {
                'status': 'success',
                'analysis': analysis,
                'summary': self._generate_analysis_summary(analysis)
            }
            
        except Exception as e:
            _logger.error(f"Error analyzing sync failures: {str(e)}")
            raise SapSyncError(f"Failed to analyze sync failures: {str(e)}")
    
    def detect_missing_records(self, backend_id, model_name, external_ids):
        """Detect missing records in SAP or Odoo"""
        try:
            missing_records = {
                'sap_missing': [],
                'odoo_missing': [],
                'binding_missing': []
            }
            
            # Check for missing records in Odoo
            for external_id in external_ids:
                # Check if binding exists
                binding_model = self._get_binding_model(model_name)
                if binding_model:
                    binding = self.env[binding_model].search([
                        ('backend_id', '=', backend_id),
                        ('external_id', '=', external_id)
                    ])
                    
                    if not binding:
                        missing_records['binding_missing'].append(external_id)
                    else:
                        # Check if Odoo record exists
                        odoo_record = binding.odoo_id
                        if not odoo_record.exists():
                            missing_records['odoo_missing'].append(external_id)
            
            # Check for missing records in SAP
            connection = self.env['sap.backend'].browse(backend_id).get_connection()
            for external_id in external_ids:
                if not self._check_record_exists_in_sap(connection, model_name, external_id):
                    missing_records['sap_missing'].append(external_id)
            
            connection.close_session()
            
            return {
                'status': 'success',
                'missing_records': missing_records,
                'summary': {
                    'total_checked': len(external_ids),
                    'sap_missing_count': len(missing_records['sap_missing']),
                    'odoo_missing_count': len(missing_records['odoo_missing']),
                    'binding_missing_count': len(missing_records['binding_missing'])
                }
            }
            
        except Exception as e:
            _logger.error(f"Error detecting missing records: {str(e)}")
            raise SapSyncError(f"Failed to detect missing records: {str(e)}")
    
    def detect_field_mismatches(self, backend_id, model_name, records_data):
        """Detect field mismatches between SAP and Odoo records"""
        try:
            mismatches = []
            
            for record_data in records_data:
                external_id = record_data.get('external_id')
                if not external_id:
                    continue
                
                # Get Odoo record
                odoo_record = self._get_odoo_record(model_name, external_id, backend_id)
                if not odoo_record:
                    continue
                
                # Compare fields
                field_mismatches = self._compare_record_fields(
                    record_data, odoo_record, model_name
                )
                
                if field_mismatches:
                    mismatches.append({
                        'external_id': external_id,
                        'odoo_id': odoo_record.id,
                        'mismatches': field_mismatches
                    })
            
            return {
                'status': 'success',
                'mismatches': mismatches,
                'summary': {
                    'total_checked': len(records_data),
                    'mismatch_count': len(mismatches),
                    'total_field_mismatches': sum(len(m['mismatches']) for m in mismatches)
                }
            }
            
        except Exception as e:
            _logger.error(f"Error detecting field mismatches: {str(e)}")
            raise SapSyncError(f"Failed to detect field mismatches: {str(e)}")
    
    def detect_data_type_conflicts(self, records_data, model_name):
        """Detect data type conflicts in records"""
        try:
            conflicts = []
            validation_rules = VALIDATION_RULES.get(model_name, {})
            
            for record_data in records_data:
                record_conflicts = []
                
                # Check field types
                for field_name, value in record_data.items():
                    if not value:
                        continue
                    
                    # Check string length
                    if field_name in VALIDATION_RULES['max_lengths']:
                        max_length = VALIDATION_RULES['max_lengths'][field_name]
                        if len(str(value)) > max_length:
                            record_conflicts.append({
                                'field': field_name,
                                'issue': 'length_exceeded',
                                'value': str(value),
                                'max_length': max_length,
                                'actual_length': len(str(value))
                            })
                    
                    # Check data type
                    if field_name in ['price_unit', 'quantity', 'weight']:
                        try:
                            float(value)
                        except (ValueError, TypeError):
                            record_conflicts.append({
                                'field': field_name,
                                'issue': 'invalid_numeric',
                                'value': value,
                                'expected_type': 'numeric'
                            })
                    
                    # Check email format
                    if field_name == 'email' and value:
                        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                        if not re.match(email_pattern, value):
                            record_conflicts.append({
                                'field': field_name,
                                'issue': 'invalid_email',
                                'value': value
                            })
                
                if record_conflicts:
                    conflicts.append({
                        'external_id': record_data.get('external_id', 'unknown'),
                        'conflicts': record_conflicts
                    })
            
            return {
                'status': 'success',
                'conflicts': conflicts,
                'summary': {
                    'total_checked': len(records_data),
                    'conflict_count': len(conflicts),
                    'total_conflicts': sum(len(c['conflicts']) for c in conflicts)
                }
            }
            
        except Exception as e:
            _logger.error(f"Error detecting data type conflicts: {str(e)}")
            raise SapSyncError(f"Failed to detect data type conflicts: {str(e)}")
    
    def generate_error_report(self, backend_id=None, days=7):
        """Generate comprehensive error report"""
        try:
            # Get analysis data
            failure_analysis = self.analyze_sync_failures(backend_id, days)
            
            # Get recent error logs
            domain = [
                ('status', '=', 'error'),
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=days))
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            error_logs = self.env['sap.sync.log'].search(domain, limit=100)
            
            # Generate report
            report = {
                'generated_at': fields.Datetime.now(),
                'period_days': days,
                'backend_id': backend_id,
                'analysis': failure_analysis.get('analysis', {}),
                'recent_errors': self._format_recent_errors(error_logs),
                'recommendations': failure_analysis.get('analysis', {}).get('recommendations', []),
                'summary': failure_analysis.get('summary', '')
            }
            
            return {
                'status': 'success',
                'report': report
            }
            
        except Exception as e:
            _logger.error(f"Error generating error report: {str(e)}")
            raise SapSyncError(f"Failed to generate error report: {str(e)}")
    
    def _analyze_error_types(self, error_logs):
        """Analyze error types and their frequency"""
        error_types = Counter()
        for log in error_logs:
            error_types[log.error_type or 'Unknown'] += 1
        
        return dict(error_types.most_common())
    
    def _analyze_operations(self, error_logs):
        """Analyze operations that are failing"""
        operations = Counter()
        for log in error_logs:
            operations[log.operation] += 1
        
        return dict(operations.most_common())
    
    def _analyze_backends(self, error_logs):
        """Analyze errors by backend"""
        backends = Counter()
        for log in error_logs:
            backends[log.backend_id.name] += 1
        
        return dict(backends.most_common())
    
    def _analyze_models(self, error_logs):
        """Analyze errors by model"""
        models = Counter()
        for log in error_logs:
            if log.model_name:
                models[log.model_name] += 1
        
        return dict(models.most_common())
    
    def _analyze_time_patterns(self, error_logs):
        """Analyze error patterns over time"""
        hourly_pattern = defaultdict(int)
        daily_pattern = defaultdict(int)
        
        for log in error_logs:
            hour = log.create_date.hour
            day = log.create_date.strftime('%Y-%m-%d')
            hourly_pattern[hour] += 1
            daily_pattern[day] += 1
        
        return {
            'hourly': dict(hourly_pattern),
            'daily': dict(daily_pattern)
        }
    
    def _identify_common_issues(self, error_logs):
        """Identify common error patterns and issues"""
        common_issues = []
        
        # Group errors by message patterns
        message_patterns = defaultdict(list)
        for log in error_logs:
            if log.message:
                # Extract key words from error message
                key_words = re.findall(r'\b\w+\b', log.message.lower())
                pattern = ' '.join(sorted(set(key_words))[:3])  # Top 3 words
                message_patterns[pattern].append(log)
        
        # Find patterns with multiple occurrences
        for pattern, logs in message_patterns.items():
            if len(logs) > 1:
                common_issues.append({
                    'pattern': pattern,
                    'count': len(logs),
                    'percentage': (len(logs) / len(error_logs)) * 100,
                    'sample_messages': [log.message for log in logs[:3]]
                })
        
        return sorted(common_issues, key=lambda x: x['count'], reverse=True)
    
    def _generate_recommendations(self, error_logs):
        """Generate recommendations based on error analysis"""
        recommendations = []
        
        # Analyze error types
        error_types = self._analyze_error_types(error_logs)
        
        if 'ConnectionError' in error_types:
            recommendations.append({
                'type': 'connection',
                'priority': 'high',
                'message': 'Multiple connection errors detected. Check SAP Service Layer connectivity and credentials.',
                'action': 'Verify SAP backend configuration and test connections.'
            })
        
        if 'ValidationError' in error_types:
            recommendations.append({
                'type': 'validation',
                'priority': 'medium',
                'message': 'Data validation errors detected. Review field mappings and data formats.',
                'action': 'Check field mappings in configuration and validate data before sync.'
            })
        
        if 'TimeoutError' in error_types:
            recommendations.append({
                'type': 'performance',
                'priority': 'medium',
                'message': 'Timeout errors detected. Consider increasing timeout values or reducing batch sizes.',
                'action': 'Adjust timeout and batch size settings in backend configuration.'
            })
        
        return recommendations
    
    def _analyze_trends(self, error_logs, days):
        """Analyze error trends over time"""
        # Group errors by day
        daily_errors = defaultdict(int)
        for log in error_logs:
            day = log.create_date.strftime('%Y-%m-%d')
            daily_errors[day] += 1
        
        # Calculate trend
        if len(daily_errors) > 1:
            days_list = sorted(daily_errors.keys())
            first_half = sum(daily_errors[day] for day in days_list[:len(days_list)//2])
            second_half = sum(daily_errors[day] for day in days_list[len(days_list)//2:])
            
            if second_half > first_half:
                trend = 'increasing'
            elif second_half < first_half:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'trend': trend,
            'daily_counts': dict(daily_errors),
            'total_errors': len(error_logs)
        }
    
    def _generate_analysis_summary(self, analysis):
        """Generate a summary of the analysis"""
        total_errors = analysis['total_errors']
        top_error_type = max(analysis['error_types'].items(), key=lambda x: x[1]) if analysis['error_types'] else ('None', 0)
        top_operation = max(analysis['operations'].items(), key=lambda x: x[1]) if analysis['operations'] else ('None', 0)
        
        return f"""
        Error Analysis Summary:
        - Total Errors: {total_errors}
        - Most Common Error Type: {top_error_type[0]} ({top_error_type[1]} occurrences)
        - Most Problematic Operation: {top_operation[0]} ({top_operation[1]} occurrences)
        - Common Issues Found: {len(analysis['common_issues'])}
        - Recommendations: {len(analysis['recommendations'])}
        """
    
    def _get_binding_model(self, model_name):
        """Get binding model name for a given model"""
        binding_mapping = {
            'res.partner': 'sap.res.partner',
            'product.product': 'sap.product.product',
            'sale.order': 'sap.sale.order',
            'account.move': 'sap.account.move'
        }
        return binding_mapping.get(model_name)
    
    def _check_record_exists_in_sap(self, connection, model_name, external_id):
        """Check if record exists in SAP"""
        try:
            if model_name == 'res.partner':
                result = connection.get_customers(filter_query=f"CardCode eq '{external_id}'")
            elif model_name == 'product.product':
                result = connection.get_products(filter_query=f"ItemCode eq '{external_id}'")
            else:
                return False
            
            return len(result.get('value', [])) > 0
        except:
            return False
    
    def _get_odoo_record(self, model_name, external_id, backend_id):
        """Get Odoo record by external ID"""
        try:
            binding_model = self._get_binding_model(model_name)
            if not binding_model:
                return None
            
            binding = self.env[binding_model].search([
                ('backend_id', '=', backend_id),
                ('external_id', '=', external_id)
            ], limit=1)
            
            return binding.odoo_id if binding else None
        except:
            return None
    
    def _compare_record_fields(self, sap_data, odoo_record, model_name):
        """Compare fields between SAP and Odoo records"""
        mismatches = []
        
        # Define field mappings for comparison
        field_mappings = {
            'res.partner': {
                'CardName': 'name',
                'CardCode': 'ref',
                'EmailAddress': 'email',
                'Phone1': 'phone'
            }
        }
        
        mappings = field_mappings.get(model_name, {})
        
        for sap_field, odoo_field in mappings.items():
            sap_value = sap_data.get(sap_field, '')
            odoo_value = getattr(odoo_record, odoo_field, '')
            
            if str(sap_value).strip() != str(odoo_value).strip():
                mismatches.append({
                    'sap_field': sap_field,
                    'odoo_field': odoo_field,
                    'sap_value': sap_value,
                    'odoo_value': odoo_value
                })
        
        return mismatches
    
    def _format_recent_errors(self, error_logs):
        """Format recent errors for report"""
        formatted_errors = []
        
        for log in error_logs:
            formatted_errors.append({
                'id': log.id,
                'timestamp': log.create_date,
                'operation': log.operation,
                'model': log.model_name,
                'external_id': log.external_id,
                'error_type': log.error_type,
                'message': log.message,
                'backend': log.backend_id.name if log.backend_id else 'Unknown'
            })
        
        return formatted_errors
