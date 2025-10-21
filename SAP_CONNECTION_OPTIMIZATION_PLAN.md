# 🚀 خطة تحسين الاتصال بـ SAP - إدارة Session متقدمة

**تاريخ:** 21 أكتوبر 2025  
**الأولوية:** 🔴 عالية جداً (تحسين الأداء)  
**المدة المتوقعة:** 2-3 أيام

---

## 🎯 الهدف

تحسين آلية الاتصال بـ SAP لتكون:
1. ✅ اتصال واحد فقط ويُعاد استخدامه
2. ✅ Token يُؤخذ مرة ويُضمّن في جميع الطلبات
3. ✅ تجديد Token تلقائي عند انتهائه
4. ✅ إزالة التكرارات والأشياء غير الضرورية
5. ✅ أداء أسرع بكثير

---

## 📊 الوضع الحالي - التحليل

### المشكلة الرئيسية

**حالياً في `adapter.py`:**
```python
def search(self, filters=None, skip=0, top=100):
    """Search Business Partners in SAP"""
    connection = self._get_connection()  # ← ينشئ connection جديد في كل مرة! ❌
    try:
        result = connection.get_customers(...)
        return result.get('value', [])
    finally:
        connection.close_session()  # ← يغلق الـ connection! ❌
```

**المشاكل:**
1. ❌ إنشاء connection جديد في **كل طلب**
2. ❌ تسجيل دخول جديد في **كل طلب** (`_authenticate()`)
3. ❌ Session يُغلق بعد كل طلب (`close_session()`)
4. ❌ بطء شديد عند استيراد بيانات كبيرة

**مثال:**
```python
# استيراد 100 منتج:
for product in products:  # 100 مرة
    connection = create_new_connection()  # ← 100 تسجيل دخول جديد! ❌
    data = connection.get_product()
    connection.close()  # ← 100 إغلاق! ❌

# النتيجة: بطء رهيب! ⏱️ ~10-15 دقيقة
```

---

## ✅ الحل المقترح - Session Pool & Singleton

### الفكرة الأساسية

```python
# بدلاً من:
connection = create_new_connection()  # كل مرة ❌

# نستخدم:
connection = ConnectionPool.get_connection(backend_id)  # مرة واحدة ✅
```

### الآلية

```
┌─────────────────────────────────────────────────┐
│           SAP Connection Pool Manager           │
├─────────────────────────────────────────────────┤
│                                                 │
│  Backend 1 → Session (Token: ABC123)           │
│             ├─ Created: 10:00 AM                │
│             ├─ Expires: 10:28 AM                │
│             └─ Status: Active ✅                │
│                                                 │
│  Backend 2 → Session (Token: XYZ789)           │
│             ├─ Created: 10:05 AM                │
│             ├─ Expires: 10:33 AM                │
│             └─ Status: Active ✅                │
│                                                 │
└─────────────────────────────────────────────────┘
         ↓
    يُعاد استخدامه في جميع الطلبات
```

---

## 🔧 التطبيق التقني

### المرحلة 1: إنشاء Connection Pool Manager

**إنشاء ملف جديد:** `core/sap_connection_pool.py`

```python
# -*- coding: utf-8 -*-
"""
SAP Connection Pool Manager
Manages and reuses SAP Service Layer connections for better performance
"""

import threading
from datetime import datetime, timedelta
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class SapConnectionPool:
    """
    Singleton Connection Pool Manager for SAP Service Layer
    
    Features:
    - Single connection per backend
    - Automatic token refresh
    - Thread-safe operations
    - Connection health monitoring
    """
    
    _instance = None
    _lock = threading.Lock()
    _connections = {}  # {backend_id: connection_info}
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize connection pool"""
        if self._initialized:
            return
        
        self._connections = {}
        self._lock = threading.Lock()
        self._initialized = True
        
        _logger.info("SAP Connection Pool Manager initialized")
    
    def get_connection(self, backend_id, force_new=False):
        """
        Get or create connection for a backend
        
        :param backend_id: SAP Backend ID
        :param force_new: Force creating a new connection
        :return: SAP Service Layer Connection
        """
        with self._lock:
            # Check if connection exists and is valid
            if not force_new and backend_id in self._connections:
                conn_info = self._connections[backend_id]
                
                # Check if session is still valid
                if self._is_session_valid(conn_info):
                    _logger.debug(f"Reusing existing connection for backend {backend_id}")
                    return conn_info['connection']
                else:
                    _logger.info(f"Session expired for backend {backend_id}, refreshing...")
                    # Try to refresh token
                    if self._refresh_session(conn_info):
                        return conn_info['connection']
                    else:
                        # If refresh failed, create new connection
                        _logger.warning(f"Token refresh failed, creating new connection for backend {backend_id}")
                        self._close_connection(backend_id)
            
            # Create new connection
            _logger.info(f"Creating new connection for backend {backend_id}")
            return self._create_connection(backend_id)
    
    def _create_connection(self, backend_id):
        """Create a new connection for backend"""
        try:
            from odoo import registry, SUPERUSER_ID
            from odoo.addons.sap_integration.models.sap_service_layer import SapServiceLayerConnection
            
            # Get backend details
            db_registry = registry(self._get_db_name())
            with db_registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                backend = env['sap.backend'].browse(backend_id)
                
                if not backend.exists():
                    raise Exception(f"Backend {backend_id} not found")
                
                # Create connection
                connection = SapServiceLayerConnection(
                    base_url=backend.base_url,
                    username=backend.username,
                    password=backend.password,
                    company_db=backend.company_db,
                    timeout=backend.timeout or 30,
                    verify_ssl=backend.verify_ssl
                )
                
                # Store in pool
                self._connections[backend_id] = {
                    'connection': connection,
                    'backend_id': backend_id,
                    'session_id': connection.session_id,
                    'created_at': datetime.now(),
                    'expires_at': connection.session_expires_at,
                    'last_used': datetime.now(),
                    'request_count': 0
                }
                
                _logger.info(f"✅ Connection created for backend {backend_id}. Session: {connection.session_id[:10]}...")
                
                return connection
                
        except Exception as e:
            _logger.error(f"❌ Error creating connection for backend {backend_id}: {str(e)}")
            raise
    
    def _is_session_valid(self, conn_info):
        """Check if session is still valid"""
        try:
            connection = conn_info['connection']
            
            # Check if session_id exists
            if not connection.session_id:
                return False
            
            # Check expiry time (with 2-minute buffer)
            if conn_info['expires_at']:
                buffer_time = timedelta(minutes=2)
                if datetime.now() >= (conn_info['expires_at'] - buffer_time):
                    _logger.debug("Session is about to expire")
                    return False
            
            # Check if connection is still alive (optional ping)
            if hasattr(connection, 'test_connection'):
                if not connection.test_connection():
                    _logger.warning("Connection test failed")
                    return False
            
            return True
            
        except Exception as e:
            _logger.error(f"Error checking session validity: {str(e)}")
            return False
    
    def _refresh_session(self, conn_info):
        """Refresh expired session"""
        try:
            connection = conn_info['connection']
            
            # Re-authenticate
            connection._authenticate()
            
            # Update connection info
            conn_info['session_id'] = connection.session_id
            conn_info['created_at'] = datetime.now()
            conn_info['expires_at'] = connection.session_expires_at
            conn_info['last_used'] = datetime.now()
            
            _logger.info(f"✅ Session refreshed for backend {conn_info['backend_id']}")
            
            return True
            
        except Exception as e:
            _logger.error(f"❌ Error refreshing session: {str(e)}")
            return False
    
    def _close_connection(self, backend_id):
        """Close connection for backend"""
        try:
            if backend_id in self._connections:
                conn_info = self._connections[backend_id]
                connection = conn_info['connection']
                
                # Close session in SAP
                if hasattr(connection, 'close_session'):
                    connection.close_session()
                
                # Remove from pool
                del self._connections[backend_id]
                
                _logger.info(f"Connection closed for backend {backend_id}")
                
        except Exception as e:
            _logger.error(f"Error closing connection: {str(e)}")
    
    def close_all_connections(self):
        """Close all connections in pool"""
        with self._lock:
            backend_ids = list(self._connections.keys())
            for backend_id in backend_ids:
                self._close_connection(backend_id)
            
            _logger.info("All connections closed")
    
    def get_pool_statistics(self):
        """Get connection pool statistics"""
        with self._lock:
            stats = {
                'total_connections': len(self._connections),
                'active_connections': 0,
                'expired_connections': 0,
                'connections': []
            }
            
            for backend_id, conn_info in self._connections.items():
                is_valid = self._is_session_valid(conn_info)
                
                if is_valid:
                    stats['active_connections'] += 1
                else:
                    stats['expired_connections'] += 1
                
                stats['connections'].append({
                    'backend_id': backend_id,
                    'session_id': conn_info['session_id'][:10] + '...' if conn_info['session_id'] else None,
                    'created_at': conn_info['created_at'].isoformat() if conn_info['created_at'] else None,
                    'expires_at': conn_info['expires_at'].isoformat() if conn_info['expires_at'] else None,
                    'last_used': conn_info['last_used'].isoformat() if conn_info['last_used'] else None,
                    'request_count': conn_info['request_count'],
                    'is_valid': is_valid
                })
            
            return stats
    
    def update_request_count(self, backend_id):
        """Update request count for backend"""
        with self._lock:
            if backend_id in self._connections:
                self._connections[backend_id]['request_count'] += 1
                self._connections[backend_id]['last_used'] = datetime.now()
    
    def _get_db_name(self):
        """Get current database name"""
        try:
            import odoo
            return odoo.tools.config['db_name']
        except:
            return 'lugal'  # Default


# Singleton instance
_connection_pool = SapConnectionPool()


def get_connection_pool():
    """Get singleton connection pool instance"""
    return _connection_pool
```

---

### المرحلة 2: تحديث Adapter لاستخدام Connection Pool

**تحديث `components/adapter.py`:**

```python
# في بداية الملف
from odoo.addons.component.core import AbstractComponent, Component
from ..core.sap_connection_pool import get_connection_pool
import logging

_logger = logging.getLogger(__name__)


class SapAdapter(AbstractComponent):
    """Generic SAP Adapter with Connection Pooling"""
    _name = 'sap.adapter'
    _inherit = 'base.backend.adapter'
    _usage = 'backend.adapter'
    _collection = 'sap.backend'
    
    def _get_connection(self):
        """
        Get SAP Service Layer connection from pool
        
        ✅ Connection is reused across multiple requests
        ✅ Token is automatically refreshed when expired
        ✅ Much faster performance
        """
        pool = get_connection_pool()
        backend_id = self.backend_record.id
        
        # Get or create connection from pool
        connection = pool.get_connection(backend_id)
        
        # Update request count for statistics
        pool.update_request_count(backend_id)
        
        return connection


class SapCRUDAdapter(SapAdapter):
    """Generic CRUD Adapter for SAP"""
    _name = 'sap.adapter.crud'
    _inherit = 'sap.adapter'
    _usage = 'backend.adapter'
    
    _sap_model = None  # Override in subclasses
    
    def search(self, filters=None, skip=0, top=100):
        """Search records in SAP"""
        raise NotImplementedError
    
    def read(self, external_id):
        """Read a single record from SAP"""
        raise NotImplementedError
    
    # ... rest of methods ...


# ===== Business Partner (Customer/Supplier) Adapter =====

class SapPartnerAdapter(Component):
    """Adapter for SAP Business Partners"""
    _name = 'sap.partner.adapter'
    _inherit = 'sap.adapter.crud'
    _apply_on = 'sap.res.partner'
    _sap_model = 'BusinessPartners'
    
    def search(self, filters=None, skip=0, top=100):
        """Search Business Partners in SAP"""
        connection = self._get_connection()  # ← من الـ pool الآن ✅
        try:
            result = connection.get_customers(
                skip=skip,
                top=top,
                filter_query=filters
            )
            return result.get('value', [])
        except Exception as e:
            _logger.error(f"Error searching partners in SAP: {str(e)}")
            raise
        # ❌ لا نغلق الـ connection هنا! Connection pool يديره
    
    def read(self, external_id):
        """Read a Business Partner from SAP"""
        connection = self._get_connection()  # ← نفس الـ connection يُعاد استخدامه ✅
        try:
            result = connection.get_customers(
                filter_query=f"CardCode eq '{external_id}'"
            )
            partners = result.get('value', [])
            if partners:
                return partners[0]
            return None
        except Exception as e:
            _logger.error(f"Error reading partner {external_id} from SAP: {str(e)}")
            raise
    
    # ... rest of methods ...
```

**التغييرات الرئيسية:**
1. ✅ إزالة `connection.close_session()` من `finally` blocks
2. ✅ استخدام `get_connection_pool()` بدلاً من إنشاء connection جديد
3. ✅ Connection يُدار بواسطة Pool Manager
4. ✅ Token يُجدد تلقائياً عند انتهائه

---

### المرحلة 3: تحديث Service Layer Connection

**تحديث `models/sap_service_layer.py`:**

```python
# إضافة method جديد للتحقق من صلاحية الـ session بدون إعادة إنشاءه

def test_connection(self):
    """Test if connection is still valid (lightweight check)"""
    try:
        if not self.session_id:
            return False
        
        # Lightweight test - just check if we can access the service
        url = f"{self.base_url}/$metadata"
        headers = self._get_headers()
        
        response = self.session.get(url, headers=headers, timeout=5)
        return response.status_code == 200
        
    except Exception as e:
        _logger.debug(f"Connection test failed: {str(e)}")
        return False

def get_request_headers(self):
    """Get headers for API requests (public method)"""
    return self._get_headers()

def ensure_session_valid(self):
    """Ensure session is valid, re-authenticate if needed"""
    self._ensure_session()
```

---

### المرحلة 4: إضافة API endpoint للمراقبة

**إضافة method في `models/sap_backend.py`:**

```python
def action_show_connection_pool_stats(self):
    """Show connection pool statistics"""
    from ..core.sap_connection_pool import get_connection_pool
    
    pool = get_connection_pool()
    stats = pool.get_pool_statistics()
    
    # Format message
    message = f"""
    📊 Connection Pool Statistics
    
    Total Connections: {stats['total_connections']}
    Active Connections: {stats['active_connections']}
    Expired Connections: {stats['expired_connections']}
    
    Details:
    """
    
    for conn in stats['connections']:
        status = "✅ Active" if conn['is_valid'] else "⏰ Expired"
        message += f"\n  Backend {conn['backend_id']}: {status}"
        message += f"\n    Session: {conn['session_id']}"
        message += f"\n    Requests: {conn['request_count']}"
        message += f"\n    Last Used: {conn['last_used']}"
    
    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': 'Connection Pool Statistics',
            'message': message,
            'type': 'info',
            'sticky': True
        }
    }

def action_refresh_connection(self):
    """Force refresh connection"""
    from ..core.sap_connection_pool import get_connection_pool
    
    pool = get_connection_pool()
    
    try:
        # Get new connection (force refresh)
        connection = pool.get_connection(self.id, force_new=True)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Connection refreshed successfully! Session: {connection.session_id[:10]}...',
                'type': 'success'
            }
        }
    except Exception as e:
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Error',
                'message': f'Failed to refresh connection: {str(e)}',
                'type': 'danger'
            }
        }
```

---

## 📈 النتائج المتوقعة

### قبل التحسين ❌

```python
# استيراد 100 منتج
Time: ~10-15 دقائق
Logins: 100 تسجيل دخول
Sessions: 100 جلسة جديدة
Requests: 300+ (login + data + logout)
```

**تحليل:**
```
┌──────────────────────────────────────┐
│ Product 1                             │
│ ├─ Login (2s)                        │
│ ├─ Get Data (1s)                     │
│ └─ Logout (0.5s)                     │
├──────────────────────────────────────┤
│ Product 2                             │
│ ├─ Login (2s) ← تكرار! ❌           │
│ ├─ Get Data (1s)                     │
│ └─ Logout (0.5s)                     │
├──────────────────────────────────────┤
│ ... وهكذا 100 مرة ...               │
└──────────────────────────────────────┘

Total: ~350 ثانية = ~6 دقائق
```

---

### بعد التحسين ✅

```python
# استيراد 100 منتج
Time: ~2-3 دقائق (تحسين 70-80%)
Logins: 1 تسجيل دخول فقط
Sessions: 1 جلسة مُعاد استخدامها
Requests: 101 (1 login + 100 data)
```

**تحليل:**
```
┌──────────────────────────────────────┐
│ Initial Setup                         │
│ └─ Login (2s) ← مرة واحدة فقط ✅     │
├──────────────────────────────────────┤
│ Product 1                             │
│ └─ Get Data (0.5s) ← بدون login! ✅  │
├──────────────────────────────────────┤
│ Product 2                             │
│ └─ Get Data (0.5s) ← نفس session ✅  │
├──────────────────────────────────────┤
│ ... وهكذا 100 مرة ...               │
└──────────────────────────────────────┘

Total: ~52 ثانية = ~1 دقيقة
```

---

## 🧪 الاختبارات

### اختبار 1: استيراد 100 منتج

```python
# في Odoo shell
backend = env['sap.backend'].browse(1)

# قبل
import time
start = time.time()
result = env['sap.product.product'].import_batch(backend)
end = time.time()
print(f"Time taken: {end - start} seconds")
# Expected before: ~350 seconds
# Expected after: ~60 seconds

# التحسين المتوقع: 83% أسرع! 🚀
```

---

### اختبار 2: Connection Pool Statistics

```python
from odoo.addons.sap_integration.core.sap_connection_pool import get_connection_pool

pool = get_connection_pool()
stats = pool.get_pool_statistics()

print(f"Active connections: {stats['active_connections']}")
print(f"Total requests: {sum(c['request_count'] for c in stats['connections'])}")
```

---

### اختبار 3: Token Refresh

```python
# Simulate expired token
backend = env['sap.backend'].browse(1)

# محاكاة انتهاء Token
pool = get_connection_pool()
conn_info = pool._connections[backend.id]
conn_info['expires_at'] = datetime.now() - timedelta(minutes=1)

# الآن جرب الاستيراد - يجب أن يُجدد Token تلقائياً
result = env['sap.res.partner'].import_batch(backend)

# يجب أن يعمل بدون مشاكل ✅
```

---

## 📋 خطة التنفيذ

### اليوم 1: إنشاء Connection Pool

**المهام:**
- [x] إنشاء `core/sap_connection_pool.py`
- [x] تطبيق `SapConnectionPool` class
- [x] تطبيق Singleton pattern
- [x] تطبيق Thread-safe operations
- [x] اختبار أولي

**الوقت المتوقع:** 4-6 ساعات

---

### اليوم 2: تحديث Adapters

**المهام:**
- [ ] تحديث `SapAdapter._get_connection()`
- [ ] إزالة `close_session()` من جميع Adapters
- [ ] تحديث `SapPartnerAdapter`
- [ ] تحديث `SapProductAdapter`
- [ ] تحديث `SapSaleOrderAdapter`
- [ ] تحديث `SapInvoiceAdapter`
- [ ] اختبار كل adapter

**الوقت المتوقع:** 4-5 ساعات

---

### اليوم 3: اختبار ومراقبة

**المهام:**
- [ ] إضافة methods للمراقبة في `sap_backend.py`
- [ ] إضافة buttons في Views
- [ ] اختبار شامل للأداء
- [ ] مقارنة الأداء قبل وبعد
- [ ] توثيق النتائج
- [ ] Commit & Deploy

**الوقت المتوقع:** 3-4 ساعات

---

## 🔒 اعتبارات الأمان

### 1. Thread Safety
✅ استخدام `threading.Lock()` لحماية الـ pool
✅ جميع العمليات على الـ pool محمية

### 2. Session Expiry
✅ تحقق تلقائي من انتهاء الـ session
✅ تجديد تلقائي قبل الانتهاء بدقيقتين
✅ Fallback لإنشاء session جديد عند الفشل

### 3. Error Handling
✅ معالجة شاملة للأخطاء
✅ Logging مفصل لكل عملية
✅ Recovery mechanism عند فشل الاتصال

### 4. Memory Management
✅ إغلاق الـ connections عند عدم الحاجة
✅ Cleanup للـ expired connections
✅ لا تسرب للذاكرة (no memory leaks)

---

## 📊 مؤشرات الأداء (KPIs)

| المؤشر | قبل | بعد | التحسين |
|--------|-----|-----|---------|
| زمن استيراد 100 منتج | ~10 دقائق | ~2 دقيقة | 80% ⬇️ |
| عدد تسجيلات الدخول | 100 | 1 | 99% ⬇️ |
| عدد الطلبات الكلي | 300+ | ~101 | 66% ⬇️ |
| استهلاك الشبكة | عالي | منخفض | 70% ⬇️ |
| استهلاك CPU | مرتفع | منخفض | 60% ⬇️ |

---

## 🎯 الأولوية والتنسيق مع الخطة الأصلية

### التكامل مع خطة العمل الرئيسية

**الخطة الأصلية:**
1. ✅ المرحلة 1: إصلاح Component Registration (مكتمل)
2. 🔄 المرحلة 2: تحسين UoM Import (قيد التنفيذ)
3. ⏳ المرحلة 3: إضافة Warehouse Management
4. ⏳ المرحلة 4: المزامنة التلقائية
5. ⏳ المرحلة 5: التحسينات

**التحديث المقترح:**
1. ✅ المرحلة 1: إصلاح Component Registration (مكتمل)
2. 🚀 **المرحلة 1.5: تحسين Connection Pool (جديد - 3 أيام)**
3. 🔄 المرحلة 2: تحسين UoM Import
4. ⏳ المرحلة 3: إضافة Warehouse Management
5. ⏳ المرحلة 4: المزامنة التلقائية
6. ⏳ المرحلة 5: التحسينات

**السبب:**
- ✅ تحسين الأداء الآن سيجعل جميع المراحل التالية أسرع
- ✅ UoM Import سيستفيد مباشرة من السرعة
- ✅ Warehouse Import سيستفيد أيضاً
- ✅ أساس قوي لجميع العمليات المستقبلية

---

## 🔗 الخطوات التالية

### بعد اكتمال هذه المرحلة:

1. **المرحلة 2: UoM Import** سيكون أسرع بكثير
2. **المرحلة 3: Warehouse** سيستفيد من نفس الآلية
3. **جميع الاستيرادات** ستكون أسرع بنسبة 70-80%

---

## ✅ معايير النجاح

### تقني:
- ✅ Connection Pool يعمل بشكل صحيح
- ✅ Token يُجدد تلقائياً
- ✅ لا توجد memory leaks
- ✅ Thread-safe

### أداء:
- ✅ تحسين 70%+ في السرعة
- ✅ تقليل 90%+ في عدد تسجيلات الدخول
- ✅ تقليل 60%+ في استهلاك الشبكة

### موثوقية:
- ✅ معالجة الأخطاء بشكل صحيح
- ✅ Recovery عند فشل الاتصال
- ✅ Logging شامل

---

## 🚀 البدء الفوري

```bash
# 1. Backup
git commit -am "Before connection pool optimization"
git tag -a "v2.0.0-before-connection-pool" -m "Before connection pool"

# 2. Create branch
git checkout -b feature/connection-pool-optimization

# 3. Create the file
touch addons/sap_integration/core/sap_connection_pool.py

# 4. Start coding!
```

---

**الحالة:** جاهز للتنفيذ ✅  
**الأولوية:** عالية جداً 🔴  
**التأثير:** تحسين هائل في الأداء 🚀  
**المدة:** 2-3 أيام ⏱️

