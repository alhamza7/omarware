# -*- coding: utf-8 -*-
"""
SAP Connection Pool Manager
Manages and reuses SAP Service Layer connections for optimal performance
"""

import threading
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class SapConnectionPool:
    """
    Singleton Connection Pool Manager for SAP Service Layer
    - Single connection per backend (reused)
    - Automatic token refresh
    - Thread-safe operations
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_pool()
        return cls._instance
    
    def _init_pool(self):
        """Initialize connection pool"""
        self._connections = {}
        self._stats = {'total_requests': 0, 'cache_hits': 0}
        _logger.info("SAP Connection Pool initialized")
    
    def get_connection(self, backend, force_new=False):
        """
        Get or create connection for a backend
        
        :param backend: sap.backend record
        :param force_new: Force new connection
        :return: SAP Service Layer Connection
        """
        backend_id = backend.id
        
        with self._lock:
            self._stats['total_requests'] += 1
            
            # Check if connection exists and is valid
            if not force_new and backend_id in self._connections:
                conn_info = self._connections[backend_id]
                
                if self._is_valid(conn_info):
                    self._stats['cache_hits'] += 1
                    conn_info['last_used'] = datetime.now()
                    conn_info['request_count'] += 1
                    _logger.debug(f"Reusing connection for backend {backend_id}")
                    return conn_info['connection']
                else:
                    # Try refresh
                    if self._refresh(conn_info):
                        conn_info['last_used'] = datetime.now()
                        conn_info['request_count'] += 1
                        return conn_info['connection']
                    else:
                        # Remove expired connection
                        self._close_connection(backend_id)
            
            # Create new connection
            return self._create_connection(backend)
    
    def _create_connection(self, backend):
        """Create new connection"""
        try:
            from ..models.sap_service_layer import SapServiceLayerConnection
            
            connection = SapServiceLayerConnection(
                base_url=backend.base_url,
                username=backend.username,
                password=backend.password,
                company_db=backend.company_db,
                timeout=getattr(backend, 'timeout', 30),
                verify_ssl=getattr(backend, 'verify_ssl', False)
            )
            
            # Store in pool
            self._connections[backend.id] = {
                'connection': connection,
                'backend_id': backend.id,
                'session_id': connection.session_id,
                'created_at': datetime.now(),
                'expires_at': connection.session_expires_at,
                'last_used': datetime.now(),
                'request_count': 1
            }
            
            _logger.info(f"✅ New connection created for backend {backend.id}")
            return connection
            
        except Exception as e:
            _logger.error(f"❌ Error creating connection: {str(e)}")
            raise
    
    def _is_valid(self, conn_info):
        """Check if session is valid"""
        try:
            if not conn_info['session_id']:
                return False
            
            # Check expiry with 2-minute buffer
            if conn_info['expires_at']:
                buffer = timedelta(minutes=2)
                if datetime.now() >= (conn_info['expires_at'] - buffer):
                    return False
            
            return True
            
        except Exception as e:
            _logger.error(f"Error checking session validity: {str(e)}")
            return False
    
    def _refresh(self, conn_info):
        """Refresh expired session"""
        try:
            connection = conn_info['connection']
            connection._authenticate()
            
            conn_info['session_id'] = connection.session_id
            conn_info['created_at'] = datetime.now()
            conn_info['expires_at'] = connection.session_expires_at
            
            _logger.info(f"✅ Session refreshed for backend {conn_info['backend_id']}")
            return True
            
        except Exception as e:
            _logger.error(f"❌ Error refreshing session: {str(e)}")
            return False
    
    def _close_connection(self, backend_id):
        """Close connection"""
        try:
            if backend_id in self._connections:
                conn_info = self._connections[backend_id]
                connection = conn_info['connection']
                
                if hasattr(connection, 'close_session'):
                    connection.close_session()
                
                del self._connections[backend_id]
                _logger.info(f"Connection closed for backend {backend_id}")
                
        except Exception as e:
            _logger.error(f"Error closing connection: {str(e)}")
    
    def close_all(self):
        """Close all connections"""
        with self._lock:
            backend_ids = list(self._connections.keys())
            for backend_id in backend_ids:
                self._close_connection(backend_id)
    
    def get_stats(self):
        """Get pool statistics"""
        with self._lock:
            stats = {
                'total_connections': len(self._connections),
                'total_requests': self._stats['total_requests'],
                'cache_hits': self._stats['cache_hits'],
                'cache_hit_rate': (self._stats['cache_hits'] / max(self._stats['total_requests'], 1)) * 100,
                'connections': []
            }
            
            for backend_id, conn_info in self._connections.items():
                stats['connections'].append({
                    'backend_id': backend_id,
                    'request_count': conn_info['request_count'],
                    'created_at': conn_info['created_at'].isoformat(),
                    'last_used': conn_info['last_used'].isoformat(),
                    'is_valid': self._is_valid(conn_info)
                })
            
            return stats


# Singleton instance
_pool = SapConnectionPool()


def get_connection_pool():
    """Get singleton connection pool instance"""
    return _pool

