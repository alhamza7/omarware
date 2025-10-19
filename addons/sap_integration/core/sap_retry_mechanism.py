# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Retry Mechanism

Intelligent retry mechanism with exponential backoff and circuit breaker pattern.
"""

from odoo import models, fields, api
import logging
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import time
import random
import threading
from enum import Enum

from .sap_logger import SapLogger, SapSyncError, SapValidationError, SapConnectionError
from .sap_base_service import SapBaseService
from ..config.sap_config import SYNC_CONFIG


class RetryStrategy(Enum):
    """Retry strategy enumeration"""
    FIXED = 'fixed'
    EXPONENTIAL = 'exponential'
    LINEAR = 'linear'
    CUSTOM = 'custom'


class CircuitState(Enum):
    """Circuit breaker state enumeration"""
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'


class SapRetryMechanism(SapBaseService):
    """Intelligent retry mechanism for SAP operations"""
    _name = 'sap.retry.mechanism'
    _description = 'SAP Retry Mechanism'
    
    _circuit_breakers = {}
    _retry_lock = threading.Lock()
    
    @api.model
    def execute_with_retry(self, operation_func, operation_name, backend_id, 
                          max_retries=None, strategy=RetryStrategy.EXPONENTIAL, 
                          base_delay=1, max_delay=300, jitter=True):
        """
        Execute operation with retry mechanism
        
        :param operation_func: Function to execute
        :param operation_name: Name of the operation for logging
        :param backend_id: ID of the SAP backend
        :param max_retries: Maximum number of retries
        :param strategy: Retry strategy to use
        :param base_delay: Base delay in seconds
        :param max_delay: Maximum delay in seconds
        :param jitter: Whether to add random jitter
        :return: Result of the operation
        """
        try:
            max_retries = max_retries or SYNC_CONFIG['default_retry_attempts']
            backend = self._get_backend(backend_id)
            
            # Check circuit breaker
            if not self._is_circuit_breaker_open(backend_id, operation_name):
                return self._execute_with_circuit_breaker(
                    operation_func, operation_name, backend_id, 
                    max_retries, strategy, base_delay, max_delay, jitter
                )
            else:
                raise SapConnectionError(f"Circuit breaker is open for {operation_name} on backend {backend.name}")
                
        except Exception as e:
            _logger.error(f"Error in execute_with_retry: {str(e)}")
            raise SapSyncError(f"Failed to execute operation with retry: {str(e)}")
    
    def _execute_with_circuit_breaker(self, operation_func, operation_name, backend_id, 
                                    max_retries, strategy, base_delay, max_delay, jitter):
        """Execute operation with circuit breaker pattern"""
        try:
            # Try to execute the operation
            result = operation_func()
            
            # Success - reset circuit breaker
            self._reset_circuit_breaker(backend_id, operation_name)
            
            return result
            
        except Exception as e:
            # Failure - handle retry logic
            return self._handle_operation_failure(
                operation_func, operation_name, backend_id, e,
                max_retries, strategy, base_delay, max_delay, jitter
            )
    
    def _handle_operation_failure(self, operation_func, operation_name, backend_id, 
                                error, max_retries, strategy, base_delay, max_delay, jitter):
        """Handle operation failure with retry logic"""
        try:
            # Check if error is retryable
            if not self._is_retryable_error(error):
                self._log_error(
                    backend_id=backend_id,
                    model_name='sap.retry.mechanism',
                    record_id=0,
                    external_id=operation_name,
                    operation='retry_check',
                    message=f"Non-retryable error: {str(error)}",
                    error_type=type(error).__name__,
                    stack_trace=_logger.format_exception(),
                    sync_direction='none'
                )
                raise error
            
            # Get current retry count
            retry_count = self._get_retry_count(backend_id, operation_name)
            
            if retry_count >= max_retries:
                # Max retries reached - open circuit breaker
                self._open_circuit_breaker(backend_id, operation_name)
                raise SapSyncError(f"Maximum retries ({max_retries}) exceeded for {operation_name}")
            
            # Calculate delay
            delay = self._calculate_delay(retry_count, strategy, base_delay, max_delay, jitter)
            
            # Log retry attempt
            self._log_info(
                backend_id=backend_id,
                model_name='sap.retry.mechanism',
                record_id=0,
                external_id=operation_name,
                operation='retry_attempt',
                message=f"Retry attempt {retry_count + 1}/{max_retries} after {delay}s delay",
                sync_direction='none'
            )
            
            # Wait before retry
            time.sleep(delay)
            
            # Increment retry count
            self._increment_retry_count(backend_id, operation_name)
            
            # Retry the operation
            return self.execute_with_retry(
                operation_func, operation_name, backend_id,
                max_retries, strategy, base_delay, max_delay, jitter
            )
            
        except Exception as e:
            _logger.error(f"Error in _handle_operation_failure: {str(e)}")
            raise
    
    def _is_retryable_error(self, error):
        """Check if error is retryable"""
        retryable_errors = [
            SapConnectionError,
            ConnectionError,
            TimeoutError,
            OSError,
            # Add more retryable error types as needed
        ]
        
        return any(isinstance(error, error_type) for error_type in retryable_errors)
    
    def _calculate_delay(self, retry_count, strategy, base_delay, max_delay, jitter):
        """Calculate delay for retry attempt"""
        try:
            if strategy == RetryStrategy.FIXED:
                delay = base_delay
            elif strategy == RetryStrategy.EXPONENTIAL:
                delay = min(base_delay * (2 ** retry_count), max_delay)
            elif strategy == RetryStrategy.LINEAR:
                delay = min(base_delay * (retry_count + 1), max_delay)
            else:
                delay = base_delay
            
            # Add jitter if enabled
            if jitter:
                jitter_amount = delay * 0.1  # 10% jitter
                delay += random.uniform(-jitter_amount, jitter_amount)
            
            return max(0, delay)
            
        except Exception as e:
            _logger.error(f"Error calculating delay: {str(e)}")
            return base_delay
    
    def _is_circuit_breaker_open(self, backend_id, operation_name):
        """Check if circuit breaker is open"""
        try:
            circuit_key = f"{backend_id}_{operation_name}"
            
            if circuit_key not in self._circuit_breakers:
                return False
            
            circuit = self._circuit_breakers[circuit_key]
            
            if circuit['state'] == CircuitState.OPEN:
                # Check if enough time has passed to try half-open
                if datetime.now() - circuit['last_failure'] > timedelta(minutes=5):
                    circuit['state'] = CircuitState.HALF_OPEN
                    return False
                return True
            
            return False
            
        except Exception as e:
            _logger.error(f"Error checking circuit breaker: {str(e)}")
            return False
    
    def _open_circuit_breaker(self, backend_id, operation_name):
        """Open circuit breaker for operation"""
        try:
            circuit_key = f"{backend_id}_{operation_name}"
            
            self._circuit_breakers[circuit_key] = {
                'state': CircuitState.OPEN,
                'last_failure': datetime.now(),
                'failure_count': 0
            }
            
            _logger.warning(f"Circuit breaker opened for {operation_name} on backend {backend_id}")
            
        except Exception as e:
            _logger.error(f"Error opening circuit breaker: {str(e)}")
    
    def _reset_circuit_breaker(self, backend_id, operation_name):
        """Reset circuit breaker for operation"""
        try:
            circuit_key = f"{backend_id}_{operation_name}"
            
            if circuit_key in self._circuit_breakers:
                self._circuit_breakers[circuit_key]['state'] = CircuitState.CLOSED
                self._circuit_breakers[circuit_key]['failure_count'] = 0
                
                _logger.info(f"Circuit breaker reset for {operation_name} on backend {backend_id}")
            
        except Exception as e:
            _logger.error(f"Error resetting circuit breaker: {str(e)}")
    
    def _get_retry_count(self, backend_id, operation_name):
        """Get current retry count for operation"""
        try:
            # This could be stored in a dedicated model or cache
            # For now, we'll use a simple in-memory counter
            retry_key = f"{backend_id}_{operation_name}_retry_count"
            
            if not hasattr(self, '_retry_counts'):
                self._retry_counts = {}
            
            return self._retry_counts.get(retry_key, 0)
            
        except Exception as e:
            _logger.error(f"Error getting retry count: {str(e)}")
            return 0
    
    def _increment_retry_count(self, backend_id, operation_name):
        """Increment retry count for operation"""
        try:
            retry_key = f"{backend_id}_{operation_name}_retry_count"
            
            if not hasattr(self, '_retry_counts'):
                self._retry_counts = {}
            
            self._retry_counts[retry_key] = self._retry_counts.get(retry_key, 0) + 1
            
        except Exception as e:
            _logger.error(f"Error incrementing retry count: {str(e)}")
    
    def _reset_retry_count(self, backend_id, operation_name):
        """Reset retry count for operation"""
        try:
            retry_key = f"{backend_id}_{operation_name}_retry_count"
            
            if not hasattr(self, '_retry_counts'):
                self._retry_counts = {}
            
            self._retry_counts[retry_key] = 0
            
        except Exception as e:
            _logger.error(f"Error resetting retry count: {str(e)}")
    
    @api.model
    def get_circuit_breaker_status(self, backend_id=None):
        """Get circuit breaker status for all or specific backend"""
        try:
            if backend_id:
                # Get status for specific backend
                backend_circuits = {
                    key: circuit for key, circuit in self._circuit_breakers.items()
                    if key.startswith(f"{backend_id}_")
                }
                return backend_circuits
            else:
                # Get status for all backends
                return self._circuit_breakers
                
        except Exception as e:
            _logger.error(f"Error getting circuit breaker status: {str(e)}")
            return {}
    
    @api.model
    def reset_all_circuit_breakers(self, backend_id=None):
        """Reset all circuit breakers for backend or all backends"""
        try:
            if backend_id:
                # Reset for specific backend
                keys_to_remove = [
                    key for key in self._circuit_breakers.keys()
                    if key.startswith(f"{backend_id}_")
                ]
                for key in keys_to_remove:
                    del self._circuit_breakers[key]
                
                _logger.info(f"Reset all circuit breakers for backend {backend_id}")
            else:
                # Reset all circuit breakers
                self._circuit_breakers.clear()
                _logger.info("Reset all circuit breakers")
                
        except Exception as e:
            _logger.error(f"Error resetting circuit breakers: {str(e)}")
    
    @api.model
    def get_retry_statistics(self, backend_id=None, days_back=7):
        """Get retry statistics for analysis"""
        try:
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=days_back)),
                ('operation', 'ilike', 'retry')
            ]
            
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            retry_logs = self.env['sap.sync.log'].search(domain)
            
            stats = {
                'total_retry_attempts': len(retry_logs),
                'successful_retries': len(retry_logs.filtered(lambda l: l.status == 'success')),
                'failed_retries': len(retry_logs.filtered(lambda l: l.status == 'failed')),
                'by_operation': {},
                'by_backend': {},
                'average_retry_count': 0
            }
            
            # Group by operation
            for log in retry_logs:
                operation = log.operation
                if operation not in stats['by_operation']:
                    stats['by_operation'][operation] = 0
                stats['by_operation'][operation] += 1
            
            # Group by backend
            for log in retry_logs:
                backend_name = log.backend_id.name if log.backend_id else 'Unknown'
                if backend_name not in stats['by_backend']:
                    stats['by_backend'][backend_name] = 0
                stats['by_backend'][backend_name] += 1
            
            # Calculate average retry count
            if retry_logs:
                total_retries = sum(log.retry_count for log in retry_logs if hasattr(log, 'retry_count'))
                stats['average_retry_count'] = total_retries / len(retry_logs)
            
            return stats
            
        except Exception as e:
            _logger.error(f"Error getting retry statistics: {str(e)}")
            return {}
    
    @api.model
    def optimize_retry_strategy(self, backend_id, operation_name, historical_data=None):
        """Optimize retry strategy based on historical data"""
        try:
            if not historical_data:
                # Get historical data for the operation
                domain = [
                    ('backend_id', '=', backend_id),
                    ('operation', '=', operation_name),
                    ('create_date', '>=', fields.Datetime.now() - timedelta(days=30))
                ]
                
                historical_logs = self.env['sap.sync.log'].search(domain)
                historical_data = [log for log in historical_logs]
            
            if not historical_data:
                # No historical data - use default strategy
                return {
                    'strategy': RetryStrategy.EXPONENTIAL,
                    'max_retries': SYNC_CONFIG['default_retry_attempts'],
                    'base_delay': 1,
                    'max_delay': 300
                }
            
            # Analyze historical data
            success_rate = len([log for log in historical_data if log.status == 'success']) / len(historical_data)
            average_retry_count = sum(log.retry_count for log in historical_data if hasattr(log, 'retry_count')) / len(historical_data)
            
            # Optimize based on success rate and retry count
            if success_rate > 0.9:
                # High success rate - reduce retries
                max_retries = max(1, int(SYNC_CONFIG['default_retry_attempts'] * 0.5))
                base_delay = 0.5
            elif success_rate > 0.7:
                # Medium success rate - keep current settings
                max_retries = SYNC_CONFIG['default_retry_attempts']
                base_delay = 1
            else:
                # Low success rate - increase retries and delay
                max_retries = int(SYNC_CONFIG['default_retry_attempts'] * 1.5)
                base_delay = 2
            
            # Choose strategy based on error patterns
            if average_retry_count > 3:
                strategy = RetryStrategy.EXPONENTIAL
            else:
                strategy = RetryStrategy.LINEAR
            
            optimized_strategy = {
                'strategy': strategy,
                'max_retries': max_retries,
                'base_delay': base_delay,
                'max_delay': 300,
                'jitter': True
            }
            
            _logger.info(f"Optimized retry strategy for {operation_name}: {optimized_strategy}")
            
            return optimized_strategy
            
        except Exception as e:
            _logger.error(f"Error optimizing retry strategy: {str(e)}")
            return {
                'strategy': RetryStrategy.EXPONENTIAL,
                'max_retries': SYNC_CONFIG['default_retry_attempts'],
                'base_delay': 1,
                'max_delay': 300
            }
