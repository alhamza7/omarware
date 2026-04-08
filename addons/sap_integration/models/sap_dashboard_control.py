# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Dashboard Control Panel

Comprehensive dashboard control panel for SAP integration management.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import json
import threading
import logging

from ..core.sap_logger import SapLogger, SapSyncError
from ..core.sap_base_service import SapBaseService

_logger = logging.getLogger(__name__)


class SapDashboardControl(models.TransientModel):
    """SAP Dashboard Control Panel"""
    _name = 'sap.dashboard.control'
    _description = 'SAP Dashboard Control Panel'
    
    _sync_operations = {}
    _control_lock = threading.Lock()
    
    # Wizard fields
    backend_id = fields.Many2one('sap.backend', string='Backend')
    
    # Dashboard metric fields
    total_syncs = fields.Integer(string='Total Syncs', readonly=True, compute='_compute_dashboard_metrics')
    successful_syncs = fields.Integer(string='Successful Syncs', readonly=True, compute='_compute_dashboard_metrics')
    failed_syncs = fields.Integer(string='Failed Syncs', readonly=True, compute='_compute_dashboard_metrics')
    success_rate = fields.Float(string='Success Rate (%)', readonly=True, compute='_compute_dashboard_metrics')
    active_backends = fields.Integer(string='Active Backends', readonly=True, compute='_compute_dashboard_metrics')
    total_errors = fields.Integer(string='Total Errors', readonly=True, compute='_compute_dashboard_metrics')
    critical_errors = fields.Integer(string='Critical Errors', readonly=True, compute='_compute_dashboard_metrics')
    average_response_time = fields.Float(string='Avg Response Time (s)', readonly=True, compute='_compute_dashboard_metrics')
    
    # Dashboard data fields (JSON text fields)
    sync_status = fields.Text(string='Sync Status', readonly=True, compute='_compute_dashboard_data')
    recent_activities = fields.Text(string='Recent Activities', readonly=True, compute='_compute_dashboard_data')
    alerts = fields.Text(string='Alerts', readonly=True, compute='_compute_dashboard_data')
    performance_metrics = fields.Text(string='Performance Metrics', readonly=True, compute='_compute_dashboard_data')
    system_health = fields.Text(string='System Health', readonly=True, compute='_compute_dashboard_data')
    configuration = fields.Text(string='Configuration', readonly=True, compute='_compute_dashboard_data')
    charts = fields.Text(string='Charts', readonly=True, compute='_compute_dashboard_data')
    
    @api.depends('backend_id')
    def _compute_dashboard_metrics(self):
        """Compute dashboard metrics"""
        for record in self:
            logs = self.env['sap.sync.log'].search([])
            record.total_syncs = len(logs)
            record.successful_syncs = len(logs.filtered(lambda l: l.status == 'success'))
            record.failed_syncs = len(logs.filtered(lambda l: l.status == 'error'))
            record.success_rate = (record.successful_syncs / record.total_syncs * 100) if record.total_syncs > 0 else 0
            record.active_backends = self.env['sap.backend'].search_count([('active', '=', True)])
            record.total_errors = record.failed_syncs
            record.critical_errors = 0
            record.average_response_time = 0.0
    
    @api.depends('backend_id')
    def _compute_dashboard_data(self):
        """Compute dashboard data"""
        for record in self:
            record.sync_status = json.dumps({'status': 'ok'})
            record.recent_activities = json.dumps([])
            record.alerts = json.dumps([])
            record.performance_metrics = json.dumps({})
            record.system_health = json.dumps({'status': 'healthy'})
            record.configuration = json.dumps({})
            record.charts = json.dumps({})
    
    @property
    def logger(self):
        return SapLogger(f"sap_integration.{self._name}")
    
    @api.model
    def get_dashboard_data(self, backend_id=None, refresh_cache=False):
        """
        Get comprehensive dashboard data
        
        :param backend_id: Specific backend ID (None for all)
        :param refresh_cache: Whether to refresh cached data
        :return: Dictionary with dashboard data
        """
        try:
            _logger.info(f"Getting dashboard data for backend: {backend_id}")
            
            dashboard_data = {
                'timestamp': fields.Datetime.now(),
                'overview': self._get_overview_metrics(backend_id),
                'sync_status': self._get_sync_status(backend_id),
                'recent_activities': self._get_recent_activities(backend_id),
                'alerts': self._get_active_alerts(backend_id),
                'performance_metrics': self._get_performance_metrics(backend_id),
                'system_health': self._get_system_health(backend_id),
                'configuration': self._get_configuration_summary(backend_id),
                'charts': self._get_chart_data(backend_id)
            }
            
            return {
                'status': 'success',
                'data': dashboard_data
            }
            
        except Exception as e:
            _logger.error(f"Error getting dashboard data: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _get_overview_metrics(self, backend_id):
        """Get overview metrics"""
        try:
            # Get sync statistics
            sync_stats = self._get_sync_statistics(backend_id)
            
            # Get error statistics
            error_stats = self._get_error_statistics(backend_id)
            
            # Get performance statistics
            performance_stats = self._get_performance_statistics(backend_id)
            
            return {
                'total_syncs': sync_stats.get('total_syncs', 0),
                'successful_syncs': sync_stats.get('successful_syncs', 0),
                'failed_syncs': sync_stats.get('failed_syncs', 0),
                'success_rate': sync_stats.get('success_rate', 0),
                'active_backends': sync_stats.get('active_backends', 0),
                'total_errors': error_stats.get('total_errors', 0),
                'critical_errors': error_stats.get('critical_errors', 0),
                'average_response_time': performance_stats.get('average_response_time', 0),
                'throughput': performance_stats.get('throughput', 0)
            }
            
        except Exception as e:
            _logger.error(f"Error getting overview metrics: {str(e)}")
            return {}
    
    def _get_sync_status(self, backend_id):
        """Get sync status information"""
        try:
            domain = []
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            # Get recent sync logs
            recent_logs = self.env['sap.sync.log'].search(
                domain, 
                order='create_date desc', 
                limit=10
            )
            
            # Get sync status by entity
            entity_status = {}
            for log in recent_logs:
                entity = log.model_name or 'Unknown'
                if entity not in entity_status:
                    entity_status[entity] = {
                        'total': 0,
                        'success': 0,
                        'failed': 0,
                        'in_progress': 0
                    }
                
                entity_status[entity]['total'] += 1
                entity_status[entity][log.status] += 1
            
            # Calculate success rates
            for entity, stats in entity_status.items():
                if stats['total'] > 0:
                    stats['success_rate'] = (stats['success'] / stats['total']) * 100
                else:
                    stats['success_rate'] = 0
            
            return {
                'recent_logs': [{
                    'id': log.id,
                    'timestamp': log.create_date,
                    'entity': log.model_name,
                    'operation': log.operation,
                    'status': log.status,
                    'message': log.message,
                    'duration': log.duration
                } for log in recent_logs],
                'entity_status': entity_status,
                'overall_status': self._get_overall_sync_status(backend_id)
            }
            
        except Exception as e:
            _logger.error(f"Error getting sync status: {str(e)}")
            return {}
    
    def _get_recent_activities(self, backend_id):
        """Get recent activities"""
        try:
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24))
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            activities = self.env['sap.sync.log'].search(
                domain, 
                order='create_date desc', 
                limit=20
            )
            
            return [{
                'id': activity.id,
                'timestamp': activity.create_date,
                'type': activity.operation,
                'entity': activity.model_name,
                'status': activity.status,
                'message': activity.message,
                'backend': activity.backend_id.name if activity.backend_id else 'Unknown',
                'duration': activity.duration
            } for activity in activities]
            
        except Exception as e:
            _logger.error(f"Error getting recent activities: {str(e)}")
            return []
    
    def _get_active_alerts(self, backend_id):
        """Get active alerts"""
        try:
            domain = [('status', '=', 'active')]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            alerts = self.env['sap.alert'].search(domain, limit=10)
            
            return [{
                'id': alert.id,
                'message': alert.message,
                'priority': alert.priority,
                'rule': alert.rule_id.name if alert.rule_id else 'Manual',
                'backend': alert.backend_id.name if alert.backend_id else 'All',
                'created': alert.create_date,
                'details': alert.details
            } for alert in alerts]
            
        except Exception as e:
            _logger.error(f"Error getting active alerts: {str(e)}")
            return []
    
    def _get_performance_metrics(self, backend_id):
        """Get performance metrics"""
        try:
            # Get performance data from last 24 hours
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24))
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            logs = self.env['sap.sync.log'].search(domain)
            
            if not logs:
                return {
                    'average_duration': 0,
                    'total_operations': 0,
                    'throughput_per_hour': 0,
                    'error_rate': 0
                }
            
            # Calculate metrics
            durations = [log.duration for log in logs if log.duration]
            average_duration = sum(durations) / len(durations) if durations else 0
            
            total_operations = len(logs)
            successful_operations = len(logs.filtered(lambda l: l.status == 'success'))
            error_rate = ((total_operations - successful_operations) / total_operations * 100) if total_operations > 0 else 0
            
            # Calculate throughput (operations per hour)
            hours = 24
            throughput_per_hour = total_operations / hours if hours > 0 else 0
            
            return {
                'average_duration': round(average_duration, 2),
                'total_operations': total_operations,
                'throughput_per_hour': round(throughput_per_hour, 2),
                'error_rate': round(error_rate, 2)
            }
            
        except Exception as e:
            _logger.error(f"Error getting performance metrics: {str(e)}")
            return {}
    
    def _get_system_health(self, backend_id):
        """Get system health information"""
        try:
            health_status = {
                'overall_status': 'healthy',
                'components': {},
                'issues': []
            }
            
            # Check backend connections
            if backend_id:
                backends = self.env['sap.backend'].browse(backend_id)
            else:
                backends = self.env['sap.backend'].search([('active', '=', True)])
            
            for backend in backends:
                connection_status = self._check_backend_health(backend)
                health_status['components'][backend.name] = connection_status
                
                if connection_status['status'] != 'healthy':
                    health_status['issues'].append({
                        'component': backend.name,
                        'issue': connection_status['message'],
                        'severity': connection_status['severity']
                    })
            
            # Check for critical errors
            critical_errors = self._get_critical_errors(backend_id)
            if critical_errors > 0:
                health_status['issues'].append({
                    'component': 'Sync Engine',
                    'issue': f'{critical_errors} critical errors in last hour',
                    'severity': 'high'
                })
                health_status['overall_status'] = 'warning'
            
            # Check system resources
            resource_status = self._check_system_resources()
            health_status['components']['System Resources'] = resource_status
            
            if resource_status['status'] != 'healthy':
                health_status['overall_status'] = 'warning'
            
            return health_status
            
        except Exception as e:
            _logger.error(f"Error getting system health: {str(e)}")
            return {'overall_status': 'error', 'components': {}, 'issues': []}
    
    def _get_configuration_summary(self, backend_id):
        """Get configuration summary"""
        try:
            if backend_id:
                backends = self.env['sap.backend'].browse(backend_id)
            else:
                backends = self.env['sap.backend'].search([('active', '=', True)])
            
            config_summary = {
                'backends': [],
                'total_mappings': 0,
                'active_alerts': 0,
                'sync_schedules': 0
            }
            
            for backend in backends:
                backend_config = {
                    'id': backend.id,
                    'name': backend.name,
                    'status': backend.connection_status,
                    'last_sync': backend.last_connection,
                    'sync_count': len(self.env['sap.sync.log'].search([
                        ('backend_id', '=', backend.id)
                    ]))
                }
                config_summary['backends'].append(backend_config)
            
            # Get mapping count
            config_summary['total_mappings'] = self.env['sap.uom.mapping'].search_count([
                ('active', '=', True)
            ])
            
            # Get active alerts count
            config_summary['active_alerts'] = self.env['sap.alert'].search_count([
                ('status', '=', 'active')
            ])
            
            return config_summary
            
        except Exception as e:
            _logger.error(f"Error getting configuration summary: {str(e)}")
            return {}
    
    def _get_chart_data(self, backend_id):
        """Get chart data for dashboard"""
        try:
            # Get sync trends for last 7 days
            sync_trends = self._get_sync_trends(backend_id, days=7)
            
            # Get error trends
            error_trends = self._get_error_trends(backend_id, days=7)
            
            # Get performance trends
            performance_trends = self._get_performance_trends(backend_id, days=7)
            
            return {
                'sync_trends': sync_trends,
                'error_trends': error_trends,
                'performance_trends': performance_trends
            }
            
        except Exception as e:
            _logger.error(f"Error getting chart data: {str(e)}")
            return {}
    
    def _get_sync_statistics(self, backend_id):
        """Get sync statistics"""
        try:
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=30))
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            logs = self.env['sap.sync.log'].search(domain)
            
            total_syncs = len(logs)
            successful_syncs = len(logs.filtered(lambda l: l.status == 'success'))
            failed_syncs = len(logs.filtered(lambda l: l.status == 'failed'))
            success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0
            
            # Count active backends
            active_backends = len(self.env['sap.backend'].search([('active', '=', True)]))
            
            return {
                'total_syncs': total_syncs,
                'successful_syncs': successful_syncs,
                'failed_syncs': failed_syncs,
                'success_rate': round(success_rate, 2),
                'active_backends': active_backends
            }
            
        except Exception as e:
            _logger.error(f"Error getting sync statistics: {str(e)}")
            return {}
    
    def _get_error_statistics(self, backend_id):
        """Get error statistics"""
        try:
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=7)),
                ('status', '=', 'failed')
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            error_logs = self.env['sap.sync.log'].search(domain)
            
            total_errors = len(error_logs)
            critical_errors = len(error_logs.filtered(lambda l: 'critical' in l.message.lower()))
            
            return {
                'total_errors': total_errors,
                'critical_errors': critical_errors
            }
            
        except Exception as e:
            _logger.error(f"Error getting error statistics: {str(e)}")
            return {}
    
    def _get_performance_statistics(self, backend_id):
        """Get performance statistics"""
        try:
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24))
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            logs = self.env['sap.sync.log'].search(domain)
            
            if not logs:
                return {
                    'average_response_time': 0,
                    'throughput': 0
                }
            
            durations = [log.duration for log in logs if log.duration]
            average_response_time = sum(durations) / len(durations) if durations else 0
            
            throughput = len(logs) / 24  # operations per hour
            
            return {
                'average_response_time': round(average_response_time, 2),
                'throughput': round(throughput, 2)
            }
            
        except Exception as e:
            _logger.error(f"Error getting performance statistics: {str(e)}")
            return {}
    
    def _get_overall_sync_status(self, backend_id):
        """Get overall sync status"""
        try:
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(hours=1))
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            recent_logs = self.env['sap.sync.log'].search(domain)
            
            if not recent_logs:
                return 'idle'
            
            # Check if any syncs are in progress
            in_progress = recent_logs.filtered(lambda l: l.status == 'in_progress')
            if in_progress:
                return 'running'
            
            # Check for recent failures
            recent_failures = recent_logs.filtered(lambda l: l.status == 'failed')
            if recent_failures:
                return 'warning'
            
            return 'healthy'
            
        except Exception as e:
            _logger.error(f"Error getting overall sync status: {str(e)}")
            return 'error'
    
    def _check_backend_health(self, backend):
        """Check backend health"""
        try:
            if backend.connection_status == 'connected':
                return {
                    'status': 'healthy',
                    'message': 'Connected',
                    'severity': 'low'
                }
            elif backend.connection_status == 'error':
                return {
                    'status': 'error',
                    'message': f'Connection error: {backend.error_message}',
                    'severity': 'high'
                }
            else:
                return {
                    'status': 'warning',
                    'message': f'Status: {backend.connection_status}',
                    'severity': 'medium'
                }
                
        except Exception as e:
            _logger.error(f"Error checking backend health: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'severity': 'high'
            }
    
    def _get_critical_errors(self, backend_id):
        """Get count of critical errors"""
        try:
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(hours=1)),
                ('status', '=', 'failed'),
                ('message', 'ilike', 'critical')
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            return self.env['sap.sync.log'].search_count(domain)
            
        except Exception as e:
            _logger.error(f"Error getting critical errors: {str(e)}")
            return 0
    
    def _check_system_resources(self):
        """Check system resources"""
        try:
            # This is a simplified check - in a real scenario, you'd check
            # actual system resources like CPU, memory, disk space, etc.
            return {
                'status': 'healthy',
                'message': 'System resources normal',
                'severity': 'low'
            }
            
        except Exception as e:
            _logger.error(f"Error checking system resources: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'severity': 'high'
            }
    
    def _get_sync_trends(self, backend_id, days=7):
        """Get sync trends for charting"""
        try:
            trends = []
            for i in range(days):
                date = fields.Datetime.now() - timedelta(days=i)
                start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=1)
                
                domain = [
                    ('create_date', '>=', start_date),
                    ('create_date', '<', end_date)
                ]
                if backend_id:
                    domain.append(('backend_id', '=', backend_id))
                
                logs = self.env['sap.sync.log'].search(domain)
                
                trends.append({
                    'date': start_date.strftime('%Y-%m-%d'),
                    'total': len(logs),
                    'success': len(logs.filtered(lambda l: l.status == 'success')),
                    'failed': len(logs.filtered(lambda l: l.status == 'failed'))
                })
            
            return trends[::-1]  # Reverse to get chronological order
            
        except Exception as e:
            _logger.error(f"Error getting sync trends: {str(e)}")
            return []
    
    def _get_error_trends(self, backend_id, days=7):
        """Get error trends for charting"""
        try:
            trends = []
            for i in range(days):
                date = fields.Datetime.now() - timedelta(days=i)
                start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=1)
                
                domain = [
                    ('create_date', '>=', start_date),
                    ('create_date', '<', end_date),
                    ('status', '=', 'failed')
                ]
                if backend_id:
                    domain.append(('backend_id', '=', backend_id))
                
                error_count = self.env['sap.sync.log'].search_count(domain)
                
                trends.append({
                    'date': start_date.strftime('%Y-%m-%d'),
                    'errors': error_count
                })
            
            return trends[::-1]  # Reverse to get chronological order
            
        except Exception as e:
            _logger.error(f"Error getting error trends: {str(e)}")
            return []
    
    def _get_performance_trends(self, backend_id, days=7):
        """Get performance trends for charting"""
        try:
            trends = []
            for i in range(days):
                date = fields.Datetime.now() - timedelta(days=i)
                start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=1)
                
                domain = [
                    ('create_date', '>=', start_date),
                    ('create_date', '<', end_date)
                ]
                if backend_id:
                    domain.append(('backend_id', '=', backend_id))
                
                logs = self.env['sap.sync.log'].search(domain)
                
                durations = [log.duration for log in logs if log.duration]
                avg_duration = sum(durations) / len(durations) if durations else 0
                
                trends.append({
                    'date': start_date.strftime('%Y-%m-%d'),
                    'avg_duration': round(avg_duration, 2),
                    'operations': len(logs)
                })
            
            return trends[::-1]  # Reverse to get chronological order
            
        except Exception as e:
            _logger.error(f"Error getting performance trends: {str(e)}")
            return []
    
    @api.model
    def start_sync_operation(self, backend_id, entity_types=None, sync_type='full'):
        """Start a sync operation"""
        try:
            with self._control_lock:
                operation_id = f"sync_{backend_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Check if sync is already running
                if self._is_sync_running(backend_id):
                    raise SapSyncError("Sync operation is already running for this backend")
                
                # Start sync operation
                sync_engine = self.env['sap.sync.engine']
                result = sync_engine.sync_all_entities(
                    backend_id=backend_id,
                    entity_types=entity_types,
                    direction='bidirectional'
                )
                
                # Store operation info
                self._sync_operations[operation_id] = {
                    'backend_id': backend_id,
                    'entity_types': entity_types,
                    'sync_type': sync_type,
                    'status': 'running',
                    'start_time': datetime.now(),
                    'result': result
                }
                
                _logger.info(f"Started sync operation {operation_id}")
                
                return {
                    'status': 'success',
                    'operation_id': operation_id,
                    'message': 'Sync operation started successfully'
                }
                
        except Exception as e:
            _logger.error(f"Error starting sync operation: {str(e)}")
            raise SapSyncError(f"Failed to start sync operation: {str(e)}")
    
    def _is_sync_running(self, backend_id):
        """Check if sync is running for backend"""
        try:
            for operation in self._sync_operations.values():
                if (operation['backend_id'] == backend_id and 
                    operation['status'] == 'running'):
                    return True
            return False
            
        except Exception as e:
            _logger.error(f"Error checking sync status: {str(e)}")
            return False
    
    @api.model
    def stop_sync_operation(self, operation_id):
        """Stop a sync operation"""
        try:
            with self._control_lock:
                if operation_id not in self._sync_operations:
                    raise SapSyncError("Sync operation not found")
                
                operation = self._sync_operations[operation_id]
                operation['status'] = 'stopped'
                operation['end_time'] = datetime.now()
                
                _logger.info(f"Stopped sync operation {operation_id}")
                
                return {
                    'status': 'success',
                    'message': 'Sync operation stopped successfully'
                }
                
        except Exception as e:
            _logger.error(f"Error stopping sync operation: {str(e)}")
            raise SapSyncError(f"Failed to stop sync operation: {str(e)}")
    
    @api.model
    def get_sync_operations(self):
        """Get all sync operations"""
        try:
            return list(self._sync_operations.values())
            
        except Exception as e:
            _logger.error(f"Error getting sync operations: {str(e)}")
            return []
    
    def action_refresh_dashboard(self):
        """Refresh dashboard data"""
        self.ensure_one()
        return {'type': 'ir.actions.client', 'tag': 'reload'}
    
    def action_export_dashboard(self):
        """Export dashboard data"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/export/sap_dashboard',
            'target': 'new'
        }
