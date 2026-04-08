# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
Enhanced SAP Dashboard

Advanced dashboard with comprehensive monitoring and analysis capabilities.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import json

from ..core.sap_logger import SapLogger, SapSyncError
from ..core.sap_error_analyzer import SapErrorAnalyzer
from ..core.sap_performance_monitor import SapPerformanceMonitor


class SapDashboardEnhanced(models.AbstractModel):
    """Enhanced SAP Integration Dashboard"""
    _name = 'sap.dashboard.enhanced'
    _description = 'Enhanced SAP Dashboard'
    
    
    @api.model
    def get_dashboard_data(self, backend_id=None, days=7):
        """Get comprehensive dashboard data"""
        try:
            dashboard_data = {
                'overview': self._get_overview_stats(backend_id, days),
                'sync_status': self._get_sync_status(backend_id, days),
                'error_analysis': self._get_error_analysis(backend_id, days),
                'performance_metrics': self._get_performance_metrics(backend_id, days),
                'recent_activities': self._get_recent_activities(backend_id, days),
                'alerts': self._get_active_alerts(backend_id),
                'recommendations': self._get_recommendations(backend_id, days),
                'trends': self._get_trends(backend_id, days)
            }
            
            return {
                'status': 'success',
                'data': dashboard_data
            }
            
        except Exception as e:
            _logger.error(f"Error getting dashboard data: {str(e)}")
            raise SapSyncError(f"Failed to get dashboard data: {str(e)}")
    
    def _get_overview_stats(self, backend_id, days):
        """Get overview statistics"""
        try:
            # Get sync logs for the period
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=days))
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            logs = self.env['sap.sync.log'].search(domain)
            
            # Calculate statistics
            total_operations = len(logs)
            successful_operations = len(logs.filtered(lambda l: l.status == 'success'))
            failed_operations = len(logs.filtered(lambda l: l.status == 'error'))
            warning_operations = len(logs.filtered(lambda l: l.status == 'warning'))
            
            success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0
            error_rate = (failed_operations / total_operations * 100) if total_operations > 0 else 0
            
            # Get unique backends
            backends = logs.mapped('backend_id')
            active_backends = len(backends)
            
            # Get total records processed
            total_records = sum(logs.mapped('records_processed'))
            
            # Get average duration
            durations = logs.mapped('duration')
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                'total_operations': total_operations,
                'successful_operations': successful_operations,
                'failed_operations': failed_operations,
                'warning_operations': warning_operations,
                'success_rate': round(success_rate, 2),
                'error_rate': round(error_rate, 2),
                'active_backends': active_backends,
                'total_records_processed': total_records,
                'average_duration': round(avg_duration, 2)
            }
            
        except Exception as e:
            _logger.error(f"Error getting overview stats: {str(e)}")
            return {}
    
    def _get_sync_status(self, backend_id, days):
        """Get sync status by entity type"""
        try:
            # Get sync logs grouped by model
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=days))
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            logs = self.env['sap.sync.log'].search(domain)
            
            # Group by model
            model_stats = {}
            for log in logs:
                model = log.model_name or 'Unknown'
                if model not in model_stats:
                    model_stats[model] = {
                        'total': 0,
                        'success': 0,
                        'error': 0,
                        'warning': 0
                    }
                
                model_stats[model]['total'] += 1
                model_stats[model][log.status] += 1
            
            # Calculate success rates
            for model, stats in model_stats.items():
                if stats['total'] > 0:
                    stats['success_rate'] = round((stats['success'] / stats['total']) * 100, 2)
                    stats['error_rate'] = round((stats['error'] / stats['total']) * 100, 2)
                else:
                    stats['success_rate'] = 0
                    stats['error_rate'] = 0
            
            return model_stats
            
        except Exception as e:
            _logger.error(f"Error getting sync status: {str(e)}")
            return {}
    
    def _get_error_analysis(self, backend_id, days):
        """Get error analysis data"""
        try:
            error_analyzer = self.env['sap.error.analyzer']
            analysis_result = error_analyzer.analyze_sync_failures(backend_id, days)
            
            if analysis_result['status'] == 'success':
                return analysis_result['analysis']
            else:
                return {}
                
        except Exception as e:
            _logger.error(f"Error getting error analysis: {str(e)}")
            return {}
    
    def _get_performance_metrics(self, backend_id, days):
        """Get performance metrics"""
        try:
            performance_monitor = self.env['sap.performance.monitor']
            performance_result = performance_monitor.analyze_performance(backend_id, days)
            
            if performance_result['status'] == 'success':
                return performance_result['analysis']
            else:
                return {}
                
        except Exception as e:
            _logger.error(f"Error getting performance metrics: {str(e)}")
            return {}
    
    def _get_recent_activities(self, backend_id, days):
        """Get recent activities"""
        try:
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=days))
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            recent_logs = self.env['sap.sync.log'].search(domain, limit=20, order='create_date desc')
            
            activities = []
            for log in recent_logs:
                activities.append({
                    'id': log.id,
                    'timestamp': log.create_date,
                    'operation': log.operation,
                    'model': log.model_name,
                    'status': log.status,
                    'message': log.message,
                    'backend': log.backend_id.name if log.backend_id else 'Unknown',
                    'duration': log.duration,
                    'records_processed': log.records_processed
                })
            
            return activities
            
        except Exception as e:
            _logger.error(f"Error getting recent activities: {str(e)}")
            return []
    
    def _get_active_alerts(self, backend_id):
        """Get active alerts"""
        try:
            domain = [('status', '=', 'active')]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            alerts = self.env['sap.alert'].search(domain, limit=10, order='create_date desc')
            
            alert_list = []
            for alert in alerts:
                alert_list.append({
                    'id': alert.id,
                    'message': alert.message,
                    'priority': alert.priority,
                    'rule': alert.rule_id.name,
                    'backend': alert.backend_id.name if alert.backend_id else 'All',
                    'created': alert.create_date,
                    'details': alert.details
                })
            
            return alert_list
            
        except Exception as e:
            _logger.error(f"Error getting active alerts: {str(e)}")
            return []
    
    def _get_recommendations(self, backend_id, days):
        """Get system recommendations"""
        try:
            recommendations = []
            
            # Get error analysis recommendations
            error_analyzer = self.env['sap.error.analyzer']
            error_analysis = error_analyzer.analyze_sync_failures(backend_id, days)
            
            if error_analysis['status'] == 'success':
                error_recommendations = error_analysis['analysis'].get('recommendations', [])
                recommendations.extend(error_recommendations)
            
            # Get performance recommendations
            performance_monitor = self.env['sap.performance.monitor']
            performance_analysis = performance_monitor.analyze_performance(backend_id, days)
            
            if performance_analysis['status'] == 'success':
                performance_recommendations = performance_analysis['analysis'].get('recommendations', [])
                recommendations.extend(performance_recommendations)
            
            # Add system-level recommendations
            system_recommendations = self._get_system_recommendations(backend_id, days)
            recommendations.extend(system_recommendations)
            
            return recommendations
            
        except Exception as e:
            _logger.error(f"Error getting recommendations: {str(e)}")
            return []
    
    def _get_trends(self, backend_id, days):
        """Get trend data"""
        try:
            # Get daily sync counts
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=days))
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            logs = self.env['sap.sync.log'].search(domain)
            
            # Group by day
            daily_counts = {}
            for log in logs:
                day = log.create_date.date().isoformat()
                if day not in daily_counts:
                    daily_counts[day] = {'total': 0, 'success': 0, 'error': 0}
                
                daily_counts[day]['total'] += 1
                daily_counts[day][log.status] += 1
            
            # Convert to list for charting
            trend_data = []
            for day in sorted(daily_counts.keys()):
                trend_data.append({
                    'date': day,
                    'total': daily_counts[day]['total'],
                    'success': daily_counts[day]['success'],
                    'error': daily_counts[day]['error']
                })
            
            return trend_data
            
        except Exception as e:
            _logger.error(f"Error getting trends: {str(e)}")
            return []
    
    def _get_system_recommendations(self, backend_id, days):
        """Get system-level recommendations"""
        recommendations = []
        
        try:
            # Check for backends without recent activity
            if not backend_id:
                backends = self.env['sap.backend'].search([('active', '=', True)])
                for backend in backends:
                    recent_logs = self.env['sap.sync.log'].search([
                        ('backend_id', '=', backend.id),
                        ('create_date', '>=', fields.Datetime.now() - timedelta(days=days))
                    ])
                    
                    if not recent_logs:
                        recommendations.append({
                            'type': 'system',
                            'priority': 'medium',
                            'title': f'No Recent Activity - {backend.name}',
                            'description': f'Backend {backend.name} has no sync activity in the last {days} days',
                            'suggestion': 'Check if the backend is properly configured and test the connection'
                        })
            
            # Check for high error rates
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=days))
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            logs = self.env['sap.sync.log'].search(domain)
            if logs:
                error_rate = len(logs.filtered(lambda l: l.status == 'error')) / len(logs) * 100
                
                if error_rate > 20:  # More than 20% error rate
                    recommendations.append({
                        'type': 'system',
                        'priority': 'high',
                        'title': 'High Error Rate Detected',
                        'description': f'Error rate is {error_rate:.1f}% over the last {days} days',
                        'suggestion': 'Review error logs and consider adjusting sync settings or fixing data issues'
                    })
            
            # Check for performance issues
            slow_operations = logs.filtered(lambda l: l.duration and l.duration > 300)  # More than 5 minutes
            if len(slow_operations) > len(logs) * 0.1:  # More than 10% slow operations
                recommendations.append({
                    'type': 'performance',
                    'priority': 'medium',
                    'title': 'Performance Issues Detected',
                    'description': f'{len(slow_operations)} operations took longer than 5 minutes',
                    'suggestion': 'Consider optimizing data processing or increasing batch sizes'
                })
            
        except Exception as e:
            _logger.error(f"Error getting system recommendations: {str(e)}")
        
        return recommendations
    
    @api.model
    def run_health_check(self, backend_id=None):
        """Run comprehensive health check"""
        try:
            health_check = {
                'timestamp': fields.Datetime.now(),
                'overall_status': 'healthy',
                'checks': []
            }
            
            # Check backend connections
            if backend_id:
                backends = self.env['sap.backend'].browse(backend_id)
            else:
                backends = self.env['sap.backend'].search([('active', '=', True)])
            
            for backend in backends:
                connection_check = self._check_backend_connection(backend)
                health_check['checks'].append(connection_check)
                
                if connection_check['status'] != 'healthy':
                    health_check['overall_status'] = 'unhealthy'
            
            # Check recent error rates
            error_check = self._check_error_rates(backend_id)
            health_check['checks'].append(error_check)
            
            if error_check['status'] != 'healthy':
                health_check['overall_status'] = 'unhealthy'
            
            # Check alert rules
            alert_check = self._check_alert_rules(backend_id)
            health_check['checks'].append(alert_check)
            
            return {
                'status': 'success',
                'health_check': health_check
            }
            
        except Exception as e:
            _logger.error(f"Error running health check: {str(e)}")
            raise SapSyncError(f"Failed to run health check: {str(e)}")
    
    def _check_backend_connection(self, backend):
        """Check backend connection health"""
        try:
            if backend.connection_status == 'connected':
                return {
                    'name': f'Backend Connection - {backend.name}',
                    'status': 'healthy',
                    'message': 'Connection is active'
                }
            else:
                return {
                    'name': f'Backend Connection - {backend.name}',
                    'status': 'unhealthy',
                    'message': f'Connection status: {backend.connection_status}'
                }
        except Exception as e:
            return {
                'name': f'Backend Connection - {backend.name}',
                'status': 'error',
                'message': str(e)
            }
    
    def _check_error_rates(self, backend_id):
        """Check error rates"""
        try:
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24)),
                ('status', '=', 'error')
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            error_count = self.env['sap.sync.log'].search_count(domain)
            
            if error_count == 0:
                return {
                    'name': 'Error Rate Check',
                    'status': 'healthy',
                    'message': 'No errors in the last 24 hours'
                }
            elif error_count < 10:
                return {
                    'name': 'Error Rate Check',
                    'status': 'healthy',
                    'message': f'{error_count} errors in the last 24 hours'
                }
            else:
                return {
                    'name': 'Error Rate Check',
                    'status': 'unhealthy',
                    'message': f'{error_count} errors in the last 24 hours - high error rate'
                }
        except Exception as e:
            return {
                'name': 'Error Rate Check',
                'status': 'error',
                'message': str(e)
            }
    
    def _check_alert_rules(self, backend_id):
        """Check alert rules configuration"""
        try:
            active_rules = self.env['sap.alert.rule'].search_count([('active', '=', True)])
            triggered_rules = self.env['sap.alert.rule'].search_count([('is_triggered', '=', True)])
            
            if active_rules == 0:
                return {
                    'name': 'Alert Rules Check',
                    'status': 'warning',
                    'message': 'No active alert rules configured'
                }
            elif triggered_rules == 0:
                return {
                    'name': 'Alert Rules Check',
                    'status': 'healthy',
                    'message': f'{active_rules} active rules, none triggered'
                }
            else:
                return {
                    'name': 'Alert Rules Check',
                    'status': 'unhealthy',
                    'message': f'{triggered_rules} out of {active_rules} rules are triggered'
                }
        except Exception as e:
            return {
                'name': 'Alert Rules Check',
                'status': 'error',
                'message': str(e)
            }
