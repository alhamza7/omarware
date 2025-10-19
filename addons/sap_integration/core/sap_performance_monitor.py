# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Performance Monitor

Advanced performance monitoring and bottleneck detection system.
"""

from odoo import models, fields, api
import logging
from odoo.exceptions import UserError
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from .sap_logger import SapLogger, SapSyncError


class SapPerformanceMetrics(models.Model):
    """Performance metrics storage"""
    _name = 'sap.performance.metrics'
    _description = 'SAP Performance Metrics'
    _order = 'timestamp desc'
    
    backend_id = fields.Many2one('sap.backend', 'Backend', required=True)
    operation = fields.Char('Operation', required=True)
    model_name = fields.Char('Model')
    
    # Performance metrics
    duration = fields.Float('Duration (seconds)', required=True)
    records_processed = fields.Integer('Records Processed', default=0)
    records_per_second = fields.Float('Records/Second', compute='_compute_records_per_second', store=True)
    memory_usage = fields.Float('Memory Usage (MB)', help="Memory usage during operation")
    cpu_usage = fields.Float('CPU Usage (%)', help="CPU usage during operation")
    
    # Timing breakdown
    connection_time = fields.Float('Connection Time (seconds)')
    data_retrieval_time = fields.Float('Data Retrieval Time (seconds)')
    processing_time = fields.Float('Processing Time (seconds)')
    mapping_time = fields.Float('Mapping Time (seconds)')
    validation_time = fields.Float('Validation Time (seconds)')
    
    # Data metrics
    data_size = fields.Integer('Data Size (bytes)')
    batch_size = fields.Integer('Batch Size')
    success_count = fields.Integer('Success Count', default=0)
    error_count = fields.Integer('Error Count', default=0)
    
    # System metrics
    timestamp = fields.Datetime('Timestamp', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', 'User')
    
    # Performance indicators
    is_slow = fields.Boolean('Slow Operation', compute='_compute_performance_indicators', store=True)
    is_bottleneck = fields.Boolean('Bottleneck', compute='_compute_performance_indicators', store=True)
    performance_score = fields.Float('Performance Score', compute='_compute_performance_indicators', store=True)
    
    @api.depends('duration', 'records_processed')
    def _compute_records_per_second(self):
        """Compute records per second"""
        for record in self:
            if record.duration > 0:
                record.records_per_second = record.records_processed / record.duration
            else:
                record.records_per_second = 0.0
    
    @api.depends('duration', 'records_per_second', 'error_count', 'success_count')
    def _compute_performance_indicators(self):
        """Compute performance indicators"""
        for record in self:
            # Get baseline metrics for comparison
            baseline = self._get_baseline_metrics(record.operation, record.model_name)
            
            # Calculate performance score (0-100)
            score = 100.0
            
            # Duration penalty
            if baseline['avg_duration'] > 0:
                duration_ratio = record.duration / baseline['avg_duration']
                if duration_ratio > 2.0:  # More than 2x average
                    score -= 30
                elif duration_ratio > 1.5:  # More than 1.5x average
                    score -= 15
            
            # Error penalty
            if record.success_count + record.error_count > 0:
                error_rate = record.error_count / (record.success_count + record.error_count)
                score -= error_rate * 50  # Up to 50 points penalty for errors
            
            # Speed penalty
            if baseline['avg_records_per_second'] > 0:
                speed_ratio = record.records_per_second / baseline['avg_records_per_second']
                if speed_ratio < 0.5:  # Less than half the average speed
                    score -= 20
                elif speed_ratio < 0.75:  # Less than 75% of average speed
                    score -= 10
            
            record.performance_score = max(0.0, min(100.0, score))
            
            # Determine if operation is slow
            record.is_slow = (
                record.duration > baseline['avg_duration'] * 2.0 or
                record.records_per_second < baseline['avg_records_per_second'] * 0.5
            )
            
            # Determine if it's a bottleneck
            record.is_bottleneck = (
                record.performance_score < 50 or
                record.error_count > record.success_count * 0.1  # More than 10% errors
            )
    
    def _get_baseline_metrics(self, operation, model_name):
        """Get baseline metrics for comparison"""
        domain = [
            ('operation', '=', operation),
            ('timestamp', '>=', fields.Datetime.now() - timedelta(days=30))
        ]
        
        if model_name:
            domain.append(('model_name', '=', model_name))
        
        metrics = self.search(domain, limit=100)
        
        if not metrics:
            return {
                'avg_duration': 0.0,
                'avg_records_per_second': 0.0,
                'avg_error_rate': 0.0
            }
        
        durations = [m.duration for m in metrics if m.duration > 0]
        records_per_second = [m.records_per_second for m in metrics if m.records_per_second > 0]
        
        error_rates = []
        for m in metrics:
            if m.success_count + m.error_count > 0:
                error_rates.append(m.error_count / (m.success_count + m.error_count))
        
        return {
            'avg_duration': statistics.mean(durations) if durations else 0.0,
            'avg_records_per_second': statistics.mean(records_per_second) if records_per_second else 0.0,
            'avg_error_rate': statistics.mean(error_rates) if error_rates else 0.0
        }


class SapPerformanceMonitor(models.AbstractModel):
    """Performance monitoring system"""
    _name = 'sap.performance.monitor'
    _description = 'SAP Performance Monitor'
    
    @api.model
    def record_operation(self, backend_id, operation, model_name=None, **metrics):
        """Record performance metrics for an operation"""
        try:
            metric_data = {
                'backend_id': backend_id,
                'operation': operation,
                'model_name': model_name,
                'user_id': self.env.user.id,
                **metrics
            }
            
            metric = self.env['sap.performance.metrics'].create(metric_data)
            _logger.debug(f"Performance metric recorded: {operation}")
            
            return metric.id
            
        except Exception as e:
            _logger.error(f"Error recording performance metrics: {str(e)}")
    
    @api.model
    def analyze_performance(self, backend_id=None, days=7):
        """Analyze performance metrics and identify bottlenecks"""
        try:
            # Get metrics for the specified period
            domain = [
                ('timestamp', '>=', fields.Datetime.now() - timedelta(days=days))
            ]
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            metrics = self.env['sap.performance.metrics'].search(domain)
            
            if not metrics:
                return {
                    'status': 'no_data',
                    'message': 'No performance data available for the specified period'
                }
            
            # Analyze performance
            analysis = {
                'total_operations': len(metrics),
                'performance_summary': self._analyze_performance_summary(metrics),
                'bottlenecks': self._identify_bottlenecks(metrics),
                'slow_operations': self._identify_slow_operations(metrics),
                'trends': self._analyze_performance_trends(metrics),
                'recommendations': self._generate_performance_recommendations(metrics),
                'backend_comparison': self._compare_backend_performance(metrics),
                'operation_breakdown': self._analyze_operation_performance(metrics)
            }
            
            return {
                'status': 'success',
                'analysis': analysis
            }
            
        except Exception as e:
            _logger.error(f"Error analyzing performance: {str(e)}")
            raise SapSyncError(f"Failed to analyze performance: {str(e)}")
    
    def _analyze_performance_summary(self, metrics):
        """Analyze overall performance summary"""
        total_duration = sum(m.duration for m in metrics)
        total_records = sum(m.records_processed for m in metrics)
        total_errors = sum(m.error_count for m in metrics)
        total_success = sum(m.success_count for m in metrics)
        
        avg_duration = total_duration / len(metrics) if metrics else 0
        avg_records_per_second = total_records / total_duration if total_duration > 0 else 0
        error_rate = total_errors / (total_errors + total_success) if (total_errors + total_success) > 0 else 0
        
        return {
            'total_duration': total_duration,
            'total_records_processed': total_records,
            'average_duration': avg_duration,
            'average_records_per_second': avg_records_per_second,
            'error_rate': error_rate,
            'total_operations': len(metrics)
        }
    
    def _identify_bottlenecks(self, metrics):
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        # Group by operation and model
        operation_groups = defaultdict(list)
        for metric in metrics:
            key = f"{metric.operation}_{metric.model_name or 'all'}"
            operation_groups[key].append(metric)
        
        for operation, group_metrics in operation_groups.items():
            if len(group_metrics) < 3:  # Need at least 3 samples
                continue
            
            # Calculate statistics
            durations = [m.duration for m in group_metrics]
            avg_duration = statistics.mean(durations)
            std_duration = statistics.stdev(durations) if len(durations) > 1 else 0
            
            # Identify outliers (more than 2 standard deviations above mean)
            threshold = avg_duration + (2 * std_duration)
            outliers = [m for m in group_metrics if m.duration > threshold]
            
            if outliers:
                bottlenecks.append({
                    'operation': operation,
                    'outlier_count': len(outliers),
                    'total_operations': len(group_metrics),
                    'average_duration': avg_duration,
                    'outlier_threshold': threshold,
                    'worst_duration': max(durations),
                    'outliers': [{
                        'id': m.id,
                        'duration': m.duration,
                        'timestamp': m.timestamp,
                        'records_processed': m.records_processed
                    } for m in outliers]
                })
        
        return sorted(bottlenecks, key=lambda x: x['outlier_count'], reverse=True)
    
    def _identify_slow_operations(self, metrics):
        """Identify consistently slow operations"""
        slow_operations = []
        
        # Group by operation
        operation_groups = defaultdict(list)
        for metric in metrics:
            operation_groups[metric.operation].append(metric)
        
        for operation, group_metrics in operation_groups.items():
            if len(group_metrics) < 5:  # Need at least 5 samples
                continue
            
            # Calculate performance score
            scores = [m.performance_score for m in group_metrics]
            avg_score = statistics.mean(scores)
            
            # Consider slow if average score is below 60
            if avg_score < 60:
                slow_operations.append({
                    'operation': operation,
                    'average_score': avg_score,
                    'operation_count': len(group_metrics),
                    'worst_score': min(scores),
                    'best_score': max(scores),
                    'recommendations': self._get_operation_recommendations(operation, group_metrics)
                })
        
        return sorted(slow_operations, key=lambda x: x['average_score'])
    
    def _analyze_performance_trends(self, metrics):
        """Analyze performance trends over time"""
        # Group by day
        daily_metrics = defaultdict(list)
        for metric in metrics:
            day = metric.timestamp.date()
            daily_metrics[day].append(metric)
        
        trends = []
        for day, day_metrics in sorted(daily_metrics.items()):
            avg_duration = statistics.mean([m.duration for m in day_metrics])
            avg_records_per_second = statistics.mean([m.records_per_second for m in day_metrics if m.records_per_second > 0])
            total_operations = len(day_metrics)
            
            trends.append({
                'date': day.isoformat(),
                'average_duration': avg_duration,
                'average_records_per_second': avg_records_per_second,
                'operation_count': total_operations
            })
        
        return trends
    
    def _generate_performance_recommendations(self, metrics):
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Analyze common issues
        slow_operations = [m for m in metrics if m.is_slow]
        error_prone_operations = [m for m in metrics if m.error_count > 0]
        
        if len(slow_operations) > len(metrics) * 0.2:  # More than 20% slow operations
            recommendations.append({
                'type': 'performance',
                'priority': 'high',
                'title': 'High Number of Slow Operations',
                'description': f"{len(slow_operations)} out of {len(metrics)} operations were slow",
                'suggestion': 'Consider optimizing data processing or increasing batch sizes'
            })
        
        if len(error_prone_operations) > len(metrics) * 0.1:  # More than 10% error-prone
            recommendations.append({
                'type': 'reliability',
                'priority': 'medium',
                'title': 'High Error Rate',
                'description': f"{len(error_prone_operations)} operations had errors",
                'suggestion': 'Review error handling and data validation processes'
            })
        
        # Check for specific bottlenecks
        bottlenecks = self._identify_bottlenecks(metrics)
        if bottlenecks:
            recommendations.append({
                'type': 'bottleneck',
                'priority': 'high',
                'title': 'Performance Bottlenecks Detected',
                'description': f"Found {len(bottlenecks)} operation groups with performance issues",
                'suggestion': 'Focus on optimizing the identified bottleneck operations'
            })
        
        return recommendations
    
    def _compare_backend_performance(self, metrics):
        """Compare performance across different backends"""
        backend_groups = defaultdict(list)
        for metric in metrics:
            backend_groups[metric.backend_id.name].append(metric)
        
        comparison = []
        for backend_name, backend_metrics in backend_groups.items():
            avg_duration = statistics.mean([m.duration for m in backend_metrics])
            avg_records_per_second = statistics.mean([m.records_per_second for m in backend_metrics if m.records_per_second > 0])
            total_operations = len(backend_metrics)
            
            comparison.append({
                'backend': backend_name,
                'average_duration': avg_duration,
                'average_records_per_second': avg_records_per_second,
                'operation_count': total_operations
            })
        
        return sorted(comparison, key=lambda x: x['average_duration'])
    
    def _analyze_operation_performance(self, metrics):
        """Analyze performance by operation type"""
        operation_groups = defaultdict(list)
        for metric in metrics:
            operation_groups[metric.operation].append(metric)
        
        operation_analysis = []
        for operation, group_metrics in operation_groups.items():
            avg_duration = statistics.mean([m.duration for m in group_metrics])
            avg_records_per_second = statistics.mean([m.records_per_second for m in group_metrics if m.records_per_second > 0])
            total_operations = len(group_metrics)
            error_rate = sum(m.error_count for m in group_metrics) / sum(m.success_count + m.error_count for m in group_metrics) if any(m.success_count + m.error_count for m in group_metrics) else 0
            
            operation_analysis.append({
                'operation': operation,
                'average_duration': avg_duration,
                'average_records_per_second': avg_records_per_second,
                'operation_count': total_operations,
                'error_rate': error_rate
            })
        
        return sorted(operation_analysis, key=lambda x: x['average_duration'], reverse=True)
    
    def _get_operation_recommendations(self, operation, metrics):
        """Get specific recommendations for an operation"""
        recommendations = []
        
        # Analyze timing breakdown if available
        connection_times = [m.connection_time for m in metrics if m.connection_time]
        processing_times = [m.processing_time for m in metrics if m.processing_time]
        
        if connection_times and statistics.mean(connection_times) > 10:  # More than 10 seconds
            recommendations.append("Consider connection pooling or optimizing SAP Service Layer connectivity")
        
        if processing_times and statistics.mean(processing_times) > 30:  # More than 30 seconds
            recommendations.append("Consider optimizing data processing logic or increasing batch sizes")
        
        # Check for memory issues
        memory_usage = [m.memory_usage for m in metrics if m.memory_usage]
        if memory_usage and statistics.mean(memory_usage) > 500:  # More than 500MB
            recommendations.append("Consider optimizing memory usage or processing smaller batches")
        
        return recommendations
