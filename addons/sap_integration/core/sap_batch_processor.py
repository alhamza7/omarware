# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Batch Processor

Batch processing system for large data sets with parallel processing and progress tracking.
"""

from odoo import models, fields, api
import logging
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty

from .sap_logger import SapLogger, SapSyncError, SapValidationError
from .sap_base_service import SapBaseService
from ..config.sap_config import SYNC_CONFIG


class SapBatchProcessor(SapBaseService):
    """Batch processing system for SAP operations"""
    _name = 'sap.batch.processor'
    _description = 'SAP Batch Processor'
    
    _processing_jobs = {}
    _job_lock = threading.Lock()
    
    @api.model
    def process_batch(self, backend_id, entity_type, records, operation_type, 
                     batch_size=None, max_workers=None, progress_callback=None):
        """
        Process a batch of records
        
        :param backend_id: ID of the SAP backend
        :param entity_type: Type of entity being processed
        :param records: List of records to process
        :param operation_type: Type of operation (sync, import, export, etc.)
        :param batch_size: Size of each batch
        :param max_workers: Maximum number of worker threads
        :param progress_callback: Callback function for progress updates
        :return: Dictionary with processing results
        """
        try:
            batch_size = batch_size or SYNC_CONFIG['default_batch_size']
            max_workers = max_workers or 4  # Default to 4 workers
            
            _logger.info(f"Starting batch processing for {len(records)} {entity_type} records")
            
            # Create job ID
            job_id = self._create_job(backend_id, entity_type, len(records), operation_type)
            
            # Split records into batches
            batches = self._split_into_batches(records, batch_size)
            
            # Process batches in parallel
            results = self._process_batches_parallel(
                job_id, backend_id, entity_type, batches, operation_type, 
                max_workers, progress_callback
            )
            
            # Update job status
            self._update_job_status(job_id, 'completed', results)
            
            # Log summary
            _logger.info(f"Batch processing completed for job {job_id} - "
                           f"Processed: {results['total_processed']}, "
                           f"Success: {results['successful']}, "
                           f"Failed: {results['failed']}")
            
            return results
            
        except Exception as e:
            _logger.error(f"Error in process_batch: {str(e)}")
            if 'job_id' in locals():
                self._update_job_status(job_id, 'failed', {'error': str(e)})
            raise SapSyncError(f"Failed to process batch: {str(e)}")
    
    def _create_job(self, backend_id, entity_type, total_records, operation_type):
        """Create a new processing job"""
        try:
            job_id = f"job_{backend_id}_{entity_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with self._job_lock:
                self._processing_jobs[job_id] = {
                    'backend_id': backend_id,
                    'entity_type': entity_type,
                    'total_records': total_records,
                    'operation_type': operation_type,
                    'status': 'running',
                    'start_time': datetime.now(),
                    'processed_records': 0,
                    'successful_records': 0,
                    'failed_records': 0,
                    'progress': 0.0
                }
            
            _logger.info(f"Created processing job {job_id}")
            return job_id
            
        except Exception as e:
            _logger.error(f"Error creating job: {str(e)}")
            raise
    
    def _update_job_status(self, job_id, status, results=None):
        """Update job status"""
        try:
            with self._job_lock:
                if job_id in self._processing_jobs:
                    self._processing_jobs[job_id]['status'] = status
                    self._processing_jobs[job_id]['end_time'] = datetime.now()
                    
                    if results:
                        self._processing_jobs[job_id].update(results)
                    
                    # Calculate duration
                    if 'start_time' in self._processing_jobs[job_id]:
                        duration = datetime.now() - self._processing_jobs[job_id]['start_time']
                        self._processing_jobs[job_id]['duration'] = duration.total_seconds()
            
        except Exception as e:
            _logger.error(f"Error updating job status: {str(e)}")
    
    def _split_into_batches(self, records, batch_size):
        """Split records into batches"""
        try:
            batches = []
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                batches.append(batch)
            
            _logger.info(f"Split {len(records)} records into {len(batches)} batches")
            return batches
            
        except Exception as e:
            _logger.error(f"Error splitting records into batches: {str(e)}")
            raise
    
    def _process_batches_parallel(self, job_id, backend_id, entity_type, batches, 
                                 operation_type, max_workers, progress_callback):
        """Process batches in parallel"""
        try:
            results = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'batches_processed': 0,
                'batches_failed': 0
            }
            
            # Create thread pool
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all batches
                future_to_batch = {
                    executor.submit(
                        self._process_single_batch, 
                        job_id, backend_id, entity_type, batch, operation_type
                    ): batch for batch in batches
                }
                
                # Process completed batches
                for future in as_completed(future_to_batch):
                    batch = future_to_batch[future]
                    try:
                        batch_result = future.result()
                        
                        # Update results
                        results['total_processed'] += batch_result.get('total_processed', 0)
                        results['successful'] += batch_result.get('successful', 0)
                        results['failed'] += batch_result.get('failed', 0)
                        results['skipped'] += batch_result.get('skipped', 0)
                        results['batches_processed'] += 1
                        
                        # Update job progress
                        self._update_job_progress(job_id, results)
                        
                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(job_id, results)
                            
                    except Exception as e:
                        _logger.error(f"Error processing batch: {str(e)}")
                        results['batches_failed'] += 1
            
            return results
            
        except Exception as e:
            _logger.error(f"Error processing batches in parallel: {str(e)}")
            raise
    
    def _process_single_batch(self, job_id, backend_id, entity_type, batch, operation_type):
        """Process a single batch of records"""
        try:
            _logger.info(f"Processing batch of {len(batch)} {entity_type} records")
            
            batch_results = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0
            }
            
            # Process each record in the batch
            for record in batch:
                try:
                    batch_results['total_processed'] += 1
                    
                    # Process record based on operation type
                    if operation_type == 'sync':
                        result = self._sync_record(backend_id, entity_type, record)
                    elif operation_type == 'import':
                        result = self._import_record(backend_id, entity_type, record)
                    elif operation_type == 'export':
                        result = self._export_record(backend_id, entity_type, record)
                    else:
                        raise SapValidationError(f"Unknown operation type: {operation_type}")
                    
                    # Update results
                    if result['status'] == 'success':
                        batch_results['successful'] += 1
                    elif result['status'] == 'skipped':
                        batch_results['skipped'] += 1
                    else:
                        batch_results['failed'] += 1
                        
                except Exception as e:
                    _logger.error(f"Error processing record {record}: {str(e)}")
                    batch_results['failed'] += 1
            
            return batch_results
            
        except Exception as e:
            _logger.error(f"Error processing single batch: {str(e)}")
            raise
    
    def _sync_record(self, backend_id, entity_type, record):
        """Sync a single record"""
        try:
            # Get sync engine
            sync_engine = self.env['sap.sync.engine']
            
            # Determine sync direction based on record type
            if hasattr(record, 'ref') and record.ref:
                # Odoo record - sync to SAP
                return sync_engine._sync_odoo_to_sap_single(backend_id, entity_type, record)
            else:
                # SAP record - sync to Odoo
                return sync_engine._sync_sap_to_odoo_single(backend_id, entity_type, record)
                
        except Exception as e:
            _logger.error(f"Error syncing record: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _import_record(self, backend_id, entity_type, record):
        """Import a single record from SAP to Odoo"""
        try:
            # Get sync engine
            sync_engine = self.env['sap.sync.engine']
            
            # Import from SAP to Odoo
            return sync_engine._sync_sap_to_odoo_single(backend_id, entity_type, record)
            
        except Exception as e:
            _logger.error(f"Error importing record: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _export_record(self, backend_id, entity_type, record):
        """Export a single record from Odoo to SAP"""
        try:
            # Get sync engine
            sync_engine = self.env['sap.sync.engine']
            
            # Export from Odoo to SAP
            return sync_engine._sync_odoo_to_sap_single(backend_id, entity_type, record)
            
        except Exception as e:
            _logger.error(f"Error exporting record: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _update_job_progress(self, job_id, results):
        """Update job progress"""
        try:
            with self._job_lock:
                if job_id in self._processing_jobs:
                    job = self._processing_jobs[job_id]
                    job['processed_records'] = results['total_processed']
                    job['successful_records'] = results['successful']
                    job['failed_records'] = results['failed']
                    
                    # Calculate progress percentage
                    if job['total_records'] > 0:
                        job['progress'] = (results['total_processed'] / job['total_records']) * 100
                    
        except Exception as e:
            _logger.error(f"Error updating job progress: {str(e)}")
    
    @api.model
    def get_job_status(self, job_id):
        """Get status of a processing job"""
        try:
            with self._job_lock:
                return self._processing_jobs.get(job_id, {})
                
        except Exception as e:
            _logger.error(f"Error getting job status: {str(e)}")
            return {}
    
    @api.model
    def get_all_jobs(self, backend_id=None, status=None):
        """Get all processing jobs"""
        try:
            with self._job_lock:
                jobs = list(self._processing_jobs.values())
                
                # Filter by backend if specified
                if backend_id:
                    jobs = [job for job in jobs if job.get('backend_id') == backend_id]
                
                # Filter by status if specified
                if status:
                    jobs = [job for job in jobs if job.get('status') == status]
                
                return jobs
                
        except Exception as e:
            _logger.error(f"Error getting all jobs: {str(e)}")
            return []
    
    @api.model
    def cancel_job(self, job_id):
        """Cancel a processing job"""
        try:
            with self._job_lock:
                if job_id in self._processing_jobs:
                    self._processing_jobs[job_id]['status'] = 'cancelled'
                    self._processing_jobs[job_id]['end_time'] = datetime.now()
                    
                    _logger.info(f"Cancelled job {job_id}")
                    return True
                else:
                    return False
                    
        except Exception as e:
            _logger.error(f"Error cancelling job: {str(e)}")
            return False
    
    @api.model
    def cleanup_old_jobs(self, days_old=7):
        """Clean up old completed jobs"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            with self._job_lock:
                jobs_to_remove = []
                
                for job_id, job in self._processing_jobs.items():
                    if (job.get('status') in ['completed', 'failed', 'cancelled'] and
                        job.get('end_time') and job['end_time'] < cutoff_date):
                        jobs_to_remove.append(job_id)
                
                for job_id in jobs_to_remove:
                    del self._processing_jobs[job_id]
                
                _logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
                
        except Exception as e:
            _logger.error(f"Error cleaning up old jobs: {str(e)}")
    
    @api.model
    def get_processing_statistics(self, backend_id=None, days_back=7):
        """Get processing statistics"""
        try:
            domain = [
                ('create_date', '>=', fields.Datetime.now() - timedelta(days=days_back)),
                ('operation', 'ilike', 'batch')
            ]
            
            if backend_id:
                domain.append(('backend_id', '=', backend_id))
            
            batch_logs = self.env['sap.sync.log'].search(domain)
            
            stats = {
                'total_batch_operations': len(batch_logs),
                'successful_batches': len(batch_logs.filtered(lambda l: l.status == 'success')),
                'failed_batches': len(batch_logs.filtered(lambda l: l.status == 'failed')),
                'total_records_processed': sum(log.records_processed for log in batch_logs if hasattr(log, 'records_processed')),
                'average_batch_size': 0,
                'average_processing_time': 0,
                'by_entity_type': {},
                'by_backend': {}
            }
            
            # Calculate averages
            if batch_logs:
                total_records = sum(log.records_processed for log in batch_logs if hasattr(log, 'records_processed'))
                stats['average_batch_size'] = total_records / len(batch_logs)
                
                total_time = sum(log.duration for log in batch_logs if hasattr(log, 'duration'))
                stats['average_processing_time'] = total_time / len(batch_logs)
            
            # Group by entity type
            for log in batch_logs:
                entity_type = log.model_name
                if entity_type not in stats['by_entity_type']:
                    stats['by_entity_type'][entity_type] = 0
                stats['by_entity_type'][entity_type] += 1
            
            # Group by backend
            for log in batch_logs:
                backend_name = log.backend_id.name if log.backend_id else 'Unknown'
                if backend_name not in stats['by_backend']:
                    stats['by_backend'][backend_name] = 0
                stats['by_backend'][backend_name] += 1
            
            return stats
            
        except Exception as e:
            _logger.error(f"Error getting processing statistics: {str(e)}")
            return {}
    
    @api.model
    def optimize_batch_size(self, backend_id, entity_type, historical_data=None):
        """Optimize batch size based on historical data"""
        try:
            if not historical_data:
                # Get historical data
                domain = [
                    ('backend_id', '=', backend_id),
                    ('model_name', '=', entity_type),
                    ('create_date', '>=', fields.Datetime.now() - timedelta(days=30))
                ]
                
                historical_logs = self.env['sap.sync.log'].search(domain)
                historical_data = [log for log in historical_logs]
            
            if not historical_data:
                # No historical data - use default batch size
                return SYNC_CONFIG['default_batch_size']
            
            # Analyze historical data
            batch_sizes = []
            success_rates = []
            
            for log in historical_data:
                if hasattr(log, 'batch_size') and hasattr(log, 'success_rate'):
                    batch_sizes.append(log.batch_size)
                    success_rates.append(log.success_rate)
            
            if not batch_sizes:
                return SYNC_CONFIG['default_batch_size']
            
            # Find optimal batch size (highest success rate with reasonable size)
            optimal_size = SYNC_CONFIG['default_batch_size']
            best_success_rate = 0
            
            for i, size in enumerate(batch_sizes):
                if success_rates[i] > best_success_rate and size <= 1000:  # Cap at 1000
                    best_success_rate = success_rates[i]
                    optimal_size = size
            
            _logger.info(f"Optimized batch size for {entity_type}: {optimal_size}")
            
            return optimal_size
            
        except Exception as e:
            _logger.error(f"Error optimizing batch size: {str(e)}")
            return SYNC_CONFIG['default_batch_size']
