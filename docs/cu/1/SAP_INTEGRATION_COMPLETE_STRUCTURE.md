# 🏗️ الهيكل الكامل لمودل SAP Integration

## 📋 جدول المحتويات
1. [نظرة عامة](#نظرة-عامة)
2. [هيكل المجلدات والملفات](#هيكل-المجلدات-والملفات)
3. [نماذج البيانات (Models)](#نماذج-البيانات-models)
4. [المكونات (Components)](#المكونات-components)
5. [العمليات المتاحة](#العمليات-المتاحة)
6. [تدفق البيانات](#تدفق-البيانات)
7. [الخدمات الأساسية](#الخدمات-الأساسية)

---

## 🎯 نظرة عامة

### الوصف
نظام متكامل للربط بين Odoo و SAP Business One باستخدام SAP Service Layer API.

### التقنيات المستخدمة
- **OCA Connector Framework** - إطار عمل الربط
- **Component Architecture** - معمارية المكونات
- **Event-Driven System** - نظام قائم على الأحداث
- **REST API Integration** - تكامل عبر REST API

### الميزات الرئيسية
✅ استيراد وتصدير ثنائي الاتجاه
✅ مزامنة تلقائية
✅ إدارة الأخطاء والمحاولات
✅ دعم العمليات الدُفعية (Batch)
✅ تتبع شامل للبيانات
✅ لوحة تحكم تحليلية

---

## 📁 هيكل المجلدات والملفات

```
addons/sap_integration/
│
├── __init__.py                          # نقطة الدخول الرئيسية + post_init_hook
├── __manifest__.py                      # بيانات المودل والاعتماديات
│
├── config/                              # ملفات التكوين
│   ├── __init__.py
│   ├── sap_config.py                   # إعدادات SAP (URLs, Fields Mapping)
│   └── sap_constants.py                # الثوابت المستخدمة
│
├── core/                                # الخدمات الأساسية
│   ├── __init__.py
│   ├── sap_api_framework.py           # إطار عمل API
│   ├── sap_base_plugin.py             # قاعدة الإضافات
│   ├── sap_batch_processor.py         # معالج العمليات الدفعية
│   ├── sap_customization_engine.py    # محرك التخصيص
│   ├── sap_data_validator.py          # التحقق من البيانات
│   ├── sap_error_handler.py           # معالج الأخطاء
│   ├── sap_logger.py                  # نظام السجلات
│   ├── sap_mapper.py                  # تحويل البيانات
│   ├── sap_plugin_manager.py          # إدارة الإضافات
│   ├── sap_retry_mechanism.py         # آلية إعادة المحاولة
│   ├── sap_sync_engine.py             # محرك المزامنة
│   └── sap_webhook_system.py          # نظام Webhooks
│
├── components/                          # مكونات OCA Connector
│   ├── __init__.py
│   ├── adapter.py                      # محولات SAP API
│   ├── binder.py                       # ربط السجلات
│   ├── mapper.py                       # تحويل البيانات
│   ├── importer.py                     # الاستيراد من SAP
│   ├── exporter.py                     # التصدير إلى SAP
│   └── listener.py                     # مستمعي الأحداث
│
├── models/                              # نماذج البيانات
│   ├── __init__.py
│   ├── sap_backend.py                  # إعدادات الاتصال بـ SAP
│   ├── sap_binding.py                  # نماذج الربط (Binding Models)
│   ├── sap_dashboard.py                # لوحة التحكم
│   ├── sap_dashboard_control.py        # عناصر التحكم
│   ├── sap_service_layer.py            # اتصال Service Layer
│   ├── sap_sync_log.py                 # سجلات المزامنة
│   ├── sap_synced_data.py              # البيانات المتزامنة
│   └── ... (نماذج أخرى)
│
├── services/                            # خدمات الأعمال
│   ├── __init__.py
│   ├── sap_customer_service.py         # خدمة العملاء
│   ├── sap_invoice_service.py          # خدمة الفواتير
│   ├── sap_product_service.py          # خدمة المنتجات
│   └── sap_quotation_service.py        # خدمة عروض الأسعار
│
├── wizard/                              # معالجات التفاعل
│   ├── __init__.py
│   ├── sap_import_wizard.py            # معالج الاستيراد
│   ├── sap_export_wizard.py            # معالج التصدير
│   ├── sap_sync_wizard.py              # معالج المزامنة
│   └── ... (معالجات أخرى)
│
├── views/                               # واجهات المستخدم (XML)
│   ├── sap_backend_views.xml
│   ├── sap_binding_views.xml
│   ├── sap_dashboard_views.xml
│   ├── sap_sync_log_views.xml
│   └── ... (ملفات XML أخرى)
│
├── security/                            # الصلاحيات
│   ├── ir.model.access.csv             # صلاحيات الوصول
│   └── sap_security.xml                # مجموعات المستخدمين
│
├── data/                                # بيانات أولية
│   ├── sap_cron.xml                    # مهام جدولة
│   └── sap_data.xml                    # بيانات افتراضية
│
└── static/                              # الملفات الثابتة
    ├── description/
    │   └── icon.png
    └── src/
        ├── js/                          # JavaScript
        ├── css/                         # Stylesheets
        └── xml/                         # QWeb Templates
```

---

## 📊 نماذج البيانات (Models)

### 1. SAP Backend (`sap.backend`)

**الغرض:** إدارة اتصالات SAP

```python
class SapBackend(models.Model):
    _name = 'sap.backend'
    _inherit = 'connector.backend'
    _backend_type = 'sap'
```

**الحقول الرئيسية:**
- `name` - اسم الاتصال
- `base_url` - رابط SAP Service Layer
- `username` - اسم المستخدم
- `password` - كلمة المرور
- `company_db` - قاعدة بيانات الشركة
- `active` - حالة التفعيل
- `version` - إصدار SAP

**العمليات:**
- `action_test_connection()` - اختبار الاتصال
- `action_sync_metadata()` - مزامنة البيانات الوصفية
- `get_connection()` - الحصول على اتصال Service Layer

---

### 2. نماذج الربط (Binding Models)

#### 2.1 SAP Partner (`sap.res.partner`)

**الغرض:** ربط العملاء/الموردين بين Odoo و SAP

```python
class SapResPartner(models.Model):
    _name = 'sap.res.partner'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'res.partner': 'odoo_id'}
```

**الحقول:**
- `odoo_id` - المرجع إلى res.partner
- `backend_id` - مرجع Backend
- `external_id` - SAP CardCode
- `sap_card_name` - اسم البطاقة في SAP
- `sap_card_type` - نوع البطاقة (عميل/مورد)
- `sync_date` - تاريخ آخر مزامنة
- `sync_error` - رسالة الخطأ (إن وجدت)

**العمليات:**
```python
# استيراد دفعي من SAP
result = env['sap.res.partner'].import_batch(backend, filters=None)

# استيراد سجل واحد
binding = env['sap.res.partner'].import_record(backend, external_id)

# تصدير إلى SAP
binding.export_to_sap()

# مزامنة
binding.sync_with_sap()
```

#### 2.2 SAP Product (`sap.product.product`)

**الغرض:** ربط المنتجات

```python
class SapProductProduct(models.Model):
    _name = 'sap.product.product'
    _inherits = {'product.product': 'odoo_id'}
```

**الحقول:**
- `odoo_id` - المرجع إلى product.product
- `backend_id` - مرجع Backend
- `external_id` - SAP ItemCode
- `sap_item_name` - اسم الصنف في SAP
- `sap_item_type` - نوع الصنف

#### 2.3 SAP Sale Order (`sap.sale.order`)

**الغرض:** ربط أوامر البيع

```python
class SapSaleOrder(models.Model):
    _name = 'sap.sale.order'
    _inherits = {'sale.order': 'odoo_id'}
```

**الحقول:**
- `odoo_id` - المرجع إلى sale.order
- `backend_id` - مرجع Backend
- `external_id` - SAP DocEntry
- `sap_doc_num` - رقم المستند في SAP

#### 2.4 SAP Invoice (`sap.account.move`)

**الغرض:** ربط الفواتير

```python
class SapAccountMove(models.Model):
    _name = 'sap.account.move'
    _inherits = {'account.move': 'odoo_id'}
```

---

### 3. نماذج التتبع والإدارة

#### 3.1 SAP Sync Log (`sap.sync.log`)

**الغرض:** تسجيل عمليات المزامنة

**الحقول:**
- `backend_id` - Backend المستخدم
- `model_name` - اسم النموذج
- `operation_type` - نوع العملية (import/export/sync)
- `status` - الحالة (success/failed/pending)
- `record_count` - عدد السجلات
- `error_message` - رسالة الخطأ
- `start_date` - تاريخ البداية
- `end_date` - تاريخ الانتهاء
- `duration` - المدة الزمنية

#### 3.2 SAP Synced Data (`sap.synced.data`)

**الغرض:** تتبع جميع البيانات المتزامنة

**الحقول:**
- `backend_id` - Backend
- `model_name` - نموذج Odoo
- `odoo_id` - معرف السجل في Odoo
- `external_id` - معرف السجل في SAP
- `sync_status` - حالة المزامنة
- `last_sync_date` - آخر مزامنة
- `sync_direction` - اتجاه المزامنة

#### 3.3 SAP Dashboard (`sap.dashboard`)

**الغرض:** لوحة التحكم والتحليلات

**الحقول المحسوبة:**
- `total_backends` - عدد الاتصالات
- `active_backends` - الاتصالات النشطة
- `total_partners` - عدد العملاء
- `total_products` - عدد المنتجات
- `total_orders` - عدد الطلبات
- `total_errors` - عدد الأخطاء
- `last_sync_date` - آخر مزامنة
- `avg_sync_time` - متوسط وقت المزامنة

---

## 🔧 المكونات (Components)

### 1. Adapters (المحولات)

**الغرض:** التواصل المباشر مع SAP Service Layer API

#### 1.1 Base Adapter (`SapAdapter`)
```python
class SapAdapter(AbstractComponent):
    _name = 'sap.adapter'
    _inherit = 'base.backend.adapter'
    _usage = 'backend.adapter'
    _collection = 'sap.backend'
```

#### 1.2 CRUD Adapter (`SapCRUDAdapter`)
```python
class SapCRUDAdapter(SapAdapter):
    _name = 'sap.adapter.crud'
    
    def search(filters, skip, top):
        """البحث في SAP"""
    
    def read(external_id):
        """قراءة سجل من SAP"""
    
    def create(data):
        """إنشاء سجل في SAP"""
    
    def write(external_id, data):
        """تحديث سجل في SAP"""
    
    def delete(external_id):
        """حذف سجل من SAP"""
```

#### 1.3 Specialized Adapters

**Partner Adapter:**
```python
class SapPartnerAdapter(Component):
    _name = 'sap.partner.adapter'
    _inherit = 'sap.adapter.crud'
    _apply_on = 'sap.res.partner'
    _sap_model = 'BusinessPartners'
```

**Product Adapter:**
```python
class SapProductAdapter(Component):
    _name = 'sap.product.adapter'
    _apply_on = 'sap.product.product'
    _sap_model = 'Items'
```

**Sale Order Adapter:**
```python
class SapSaleOrderAdapter(Component):
    _name = 'sap.sale.order.adapter'
    _apply_on = 'sap.sale.order'
    _sap_model = 'Orders'
```

---

### 2. Binders (الربط)

**الغرض:** إدارة الربط بين سجلات Odoo و SAP

```python
class SapBinder(Component):
    _name = 'sap.binder'
    _inherit = 'base.binder'
    _collection = 'sap.backend'
    
    def to_external(binding_id):
        """الحصول على external_id من binding_id"""
    
    def to_internal(external_id):
        """الحصول على binding_id من external_id"""
    
    def bind(external_id, binding_id):
        """ربط سجل Odoo بسجل SAP"""
    
    def unwrap_binding(binding_id):
        """الحصول على السجل الأصلي من الـ binding"""
```

---

### 3. Mappers (المحولات)

**الغرض:** تحويل البيانات بين صيغ SAP و Odoo

#### 3.1 Import Mappers

**Partner Import Mapper:**
```python
class SapPartnerImportMapper(Component):
    _name = 'sap.partner.import.mapper'
    _apply_on = 'sap.res.partner'
    
    @mapping
    def name(self, record):
        return {'name': record['CardName']}
    
    @mapping
    def contact_details(self, record):
        return {
            'email': record.get('EmailAddress'),
            'phone': record.get('Phone1'),
            'mobile': record.get('Cellular'),
        }
    
    @mapping
    def address(self, record):
        return {
            'street': record.get('Address'),
            'city': record.get('City'),
            'zip': record.get('ZipCode'),
        }
```

#### 3.2 Export Mappers

**Partner Export Mapper:**
```python
class SapPartnerExportMapper(Component):
    _name = 'sap.partner.export.mapper'
    _apply_on = 'sap.res.partner'
    
    @mapping
    def card_code(self, record):
        return {'CardCode': record.ref or record.id}
    
    @mapping
    def card_name(self, record):
        return {'CardName': record.name}
    
    @mapping
    def contact_details(self, record):
        return {
            'EmailAddress': record.email,
            'Phone1': record.phone,
            'Cellular': record.mobile,
        }
```

---

### 4. Importers (المستوردون)

**الغرض:** استيراد البيانات من SAP إلى Odoo

#### 4.1 Base Importer
```python
class SapImporter(Component):
    _name = 'sap.importer'
    _usage = 'record.importer'
    _collection = 'sap.backend'
    
    def run(self, external_id):
        """استيراد سجل واحد"""
        # 1. قراءة البيانات من SAP
        # 2. تحويل البيانات
        # 3. إنشاء/تحديث في Odoo
        # 4. ربط السجلات
```

#### 4.2 Batch Importer
```python
class SapBatchImporter(Component):
    _name = 'sap.batch.importer'
    _usage = 'batch.importer'
    
    def run(self, filters=None):
        """استيراد دفعي"""
        # 1. البحث في SAP
        # 2. استيراد كل سجل
        # 3. تتبع التقدم
        # 4. معالجة الأخطاء
```

#### 4.3 Specialized Importers
- `SapPartnerImporter` - استيراد العملاء
- `SapProductImporter` - استيراد المنتجات
- `SapSaleOrderImporter` - استيراد الطلبات
- `SapInvoiceImporter` - استيراد الفواتير

---

### 5. Exporters (المصدرون)

**الغرض:** تصدير البيانات من Odoo إلى SAP

```python
class SapExporter(Component):
    _name = 'sap.exporter'
    _usage = 'record.exporter'
    
    def run(self, binding_id):
        """تصدير سجل واحد"""
        # 1. قراءة البيانات من Odoo
        # 2. تحويل البيانات
        # 3. إنشاء/تحديث في SAP
        # 4. ربط السجلات
```

---

### 6. Listeners (المستمعون)

**الغرض:** الاستماع للأحداث والمزامنة التلقائية

#### 6.1 Binding Listeners
```python
class SapBindingListener(Component):
    _name = 'sap.binding.listener'
    _inherit = 'base.event.listener'
    _collection = 'sap.backend'
    
    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        """عند تحديث سجل binding"""
        # تصدير التغييرات إلى SAP
```

#### 6.2 Model Listeners
```python
class ResPartnerListener(Component):
    _name = 'res.partner.listener'
    _apply_on = ['res.partner']
    
    def on_record_create(self, record, fields=None):
        """عند إنشاء عميل جديد"""
        # إنشاء binding تلقائياً
        # تصدير إلى SAP
    
    def on_record_write(self, record, fields=None):
        """عند تحديث عميل"""
        # تحديث في SAP
```

---

## ⚙️ العمليات المتاحة

### 1. عمليات الاستيراد (Import Operations)

#### 1.1 استيراد دفعي
```python
# استيراد جميع العملاء
backend = env['sap.backend'].browse(1)
result = env['sap.res.partner'].import_batch(backend)

# استيراد مع فلترة
filters = "startswith(CardName, 'A')"
result = env['sap.res.partner'].import_batch(backend, filters=filters)

# استيراد منتجات
result = env['sap.product.product'].import_batch(backend)

# استيراد طلبات
result = env['sap.sale.order'].import_batch(backend)
```

#### 1.2 استيراد سجل واحد
```python
# استيراد عميل محدد بـ CardCode
binding = env['sap.res.partner'].import_record(backend, 'C00001')

# استيراد منتج محدد بـ ItemCode
binding = env['sap.product.product'].import_record(backend, 'ITEM001')
```

#### 1.3 استيراد عبر Wizard
```python
# فتح معالج الاستيراد
wizard = env['sap.import.wizard'].create({
    'backend_id': backend.id,
    'entity_type': 'partner',  # partner, product, order, invoice
    'import_mode': 'all',  # all, filtered, specific
    'batch_size': 100,
    'skip_existing': True,
})

# تنفيذ الاستيراد
wizard.action_start_import()
```

---

### 2. عمليات التصدير (Export Operations)

#### 2.1 تصدير يدوي
```python
# تصدير عميل
partner = env['res.partner'].browse(1)
binding = env['sap.res.partner'].create({
    'odoo_id': partner.id,
    'backend_id': backend.id,
})
binding.export_to_sap()

# تصدير منتج
product = env['product.product'].browse(1)
binding = env['sap.product.product'].create({
    'odoo_id': product.id,
    'backend_id': backend.id,
})
binding.export_to_sap()
```

#### 2.2 تصدير عبر Wizard
```python
wizard = env['sap.export.wizard'].create({
    'backend_id': backend.id,
    'entity_type': 'product',
    'record_ids': [(6, 0, product_ids)],
})
wizard.action_start_export()
```

#### 2.3 تصدير تلقائي
```python
# يتم تلقائياً عند:
# - إنشاء سجل جديد في Odoo
# - تحديث سجل موجود
# - إذا كان Backend مفعلاً ونشطاً
```

---

### 3. عمليات المزامنة (Sync Operations)

#### 3.1 مزامنة كاملة
```python
# مزامنة جميع البيانات
backend.action_sync_all()

# مزامنة نوع معين
backend.action_sync_partners()
backend.action_sync_products()
backend.action_sync_orders()
```

#### 3.2 مزامنة ثنائية الاتجاه
```python
# استيراد من SAP ثم تصدير التغييرات
wizard = env['sap.sync.wizard'].create({
    'backend_id': backend.id,
    'sync_direction': 'both',  # import, export, both
    'entity_types': ['partner', 'product'],
})
wizard.action_start_sync()
```

#### 3.3 مزامنة جدولية (Cron)
```xml
<!-- في data/sap_cron.xml -->
<record id="ir_cron_sap_sync" model="ir.cron">
    <field name="name">SAP: Sync All Data</field>
    <field name="model_id" ref="model_sap_backend"/>
    <field name="state">code</field>
    <field name="code">model.action_cron_sync_all()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">hours</field>
</record>
```

---

### 4. عمليات الإدارة (Management Operations)

#### 4.1 اختبار الاتصال
```python
backend = env['sap.backend'].browse(1)
result = backend.action_test_connection()
# Returns: {'status': 'success', 'message': 'Connected successfully'}
```

#### 4.2 إعادة المحاولة للسجلات الفاشلة
```python
# إعادة محاولة جميع السجلات الفاشلة
failed_bindings = env['sap.res.partner'].search([
    ('sync_error', '!=', False),
    ('sync_retry_count', '<', 3)
])

for binding in failed_bindings:
    binding.retry_sync()
```

#### 4.3 حذف الربط
```python
# حذف الربط وإبقاء السجل في Odoo
binding.action_unbind()

# حذف من SAP أيضاً
binding.action_delete_from_sap()
```

---

## 🔄 تدفق البيانات

### 1. تدفق الاستيراد (Import Flow)

```
SAP → Adapter → Mapper → Importer → Binder → Odoo

التفاصيل:
1. Adapter: يقرأ البيانات من SAP Service Layer
2. Mapper: يحول البيانات من صيغة SAP إلى Odoo
3. Importer: 
   - يفحص إذا كان السجل موجود
   - يُنشئ السجل الأساسي (res.partner)
   - يُنشئ سجل الربط (sap.res.partner)
4. Binder: يربط external_id مع binding_id
5. النتيجة: سجل في Odoo مرتبط بسجل في SAP
```

### 2. تدفق التصدير (Export Flow)

```
Odoo → Binder → Mapper → Exporter → Adapter → SAP

التفاصيل:
1. Binder: يحصل على السجل الأساسي من binding
2. Mapper: يحول البيانات من صيغة Odoo إلى SAP
3. Exporter:
   - يفحص إذا كان السجل موجود في SAP
   - يُنشئ أو يُحدّث في SAP
4. Adapter: يرسل البيانات إلى SAP Service Layer
5. Binder: يحفظ external_id الجديد
```

### 3. تدفق المزامنة التلقائية

```
حدث في Odoo → Listener → Queue → Background Job → Export

التفاصيل:
1. Listener يستمع لأحداث create/write
2. يفحص شروط المزامنة (skip_if)
3. يضع المهمة في queue
4. Background job ينفذ التصدير
5. يسجل النتيجة في sync.log
```

---

## 🛠️ الخدمات الأساسية

### 1. SAP Service Layer Connection

**الملف:** `models/sap_service_layer.py`

```python
class SapServiceLayerConnection:
    """إدارة الاتصال بـ SAP Service Layer"""
    
    def __init__(self, base_url, username, password, company_db):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.company_db = company_db
        self.session_id = None
    
    def login(self):
        """تسجيل الدخول والحصول على Session"""
    
    def get_customers(self, skip=0, top=100, filter_query=None):
        """جلب العملاء من SAP"""
    
    def create_business_partner(self, data):
        """إنشاء عميل في SAP"""
    
    def update_business_partner(self, card_code, data):
        """تحديث عميل في SAP"""
    
    def get_products(self, skip=0, top=100, filter_query=None):
        """جلب المنتجات من SAP"""
    
    def create_quotation(self, data):
        """إنشاء عرض سعر في SAP"""
    
    def close_session(self):
        """إغلاق الجلسة"""
```

### 2. Logger System

**الملف:** `core/sap_logger.py`

```python
class SapLogger:
    """نظام تسجيل متقدم"""
    
    def log_sync_start(self, backend, model, operation):
        """تسجيل بداية عملية مزامنة"""
    
    def log_sync_success(self, log_id, record_count):
        """تسجيل نجاح العملية"""
    
    def log_sync_error(self, log_id, error_message):
        """تسجيل فشل العملية"""
    
    def log_record_sync(self, binding, direction, status):
        """تسجيل مزامنة سجل واحد"""
```

### 3. Error Handler

**الملف:** `core/sap_error_handler.py`

```python
class SapErrorHandler:
    """معالج الأخطاء"""
    
    def handle_connection_error(self, error):
        """معالجة أخطاء الاتصال"""
    
    def handle_authentication_error(self, error):
        """معالجة أخطاء المصادقة"""
    
    def handle_validation_error(self, error):
        """معالجة أخطاء التحقق"""
    
    def handle_api_error(self, error):
        """معالجة أخطاء API"""
    
    def should_retry(self, error):
        """تحديد إذا كان يجب إعادة المحاولة"""
```

### 4. Retry Mechanism

**الملف:** `core/sap_retry_mechanism.py`

```python
class SapRetryMechanism:
    """آلية إعادة المحاولة"""
    
    max_retries = 3
    retry_delay = 5  # seconds
    
    def retry_operation(self, operation, *args, **kwargs):
        """إعادة محاولة العملية مع backoff"""
        
    def schedule_retry(self, binding, delay):
        """جدولة إعادة محاولة لاحقة"""
```

### 5. Batch Processor

**الملف:** `core/sap_batch_processor.py`

```python
class SapBatchProcessor:
    """معالج العمليات الدفعية"""
    
    def process_batch(self, records, operation, batch_size=100):
        """معالجة دفعة من السجلات"""
        
    def split_into_batches(self, records, batch_size):
        """تقسيم السجلات إلى دفعات"""
        
    def monitor_progress(self, total, processed, errors):
        """متابعة التقدم"""
```

---

## 📈 أمثلة الاستخدام الشاملة

### مثال 1: استيراد العملاء من SAP

```python
# 1. الحصول على Backend
backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# 2. اختبار الاتصال
result = backend.action_test_connection()
if result['status'] != 'success':
    raise Exception(result['message'])

# 3. استيراد دفعي
import_result = env['sap.res.partner'].import_batch(
    backend,
    filters="CardType eq 'cCustomer'"  # عملاء فقط
)

# 4. النتيجة
print(f"تم استيراد: {import_result['imported_count']}")
print(f"تم تخطي: {import_result['skipped_count']}")
print(f"أخطاء: {import_result['error_count']}")

# 5. عرض السجلات المستوردة
bindings = env['sap.res.partner'].search([
    ('backend_id', '=', backend.id),
    ('create_date', '>=', fields.Datetime.now())
])

for binding in bindings:
    print(f"CardCode: {binding.external_id}, Name: {binding.name}")
```

### مثال 2: تصدير منتج إلى SAP

```python
# 1. إنشاء منتج في Odoo
product = env['product.product'].create({
    'name': 'منتج جديد',
    'type': 'product',
    'list_price': 100.00,
    'standard_price': 50.00,
    'default_code': 'PROD001',
})

# 2. إنشاء Binding وتصدير
backend = env['sap.backend'].browse(1)
binding = env['sap.product.product'].create({
    'odoo_id': product.id,
    'backend_id': backend.id,
})

# 3. تصدير إلى SAP
try:
    binding.export_to_sap()
    print(f"تم التصدير بنجاح. ItemCode: {binding.external_id}")
except Exception as e:
    print(f"فشل التصدير: {str(e)}")
```

### مثال 3: مزامنة ثنائية الاتجاه

```python
# 1. إنشاء معالج المزامنة
wizard = env['sap.sync.wizard'].create({
    'backend_id': backend.id,
    'sync_direction': 'both',
    'entity_types': ['partner', 'product', 'order'],
    'import_new': True,
    'export_changes': True,
    'conflict_resolution': 'sap_wins',  # sap_wins, odoo_wins, manual
})

# 2. تنفيذ المزامنة
wizard.action_start_sync()

# 3. متابعة التقدم
while wizard.state == 'in_progress':
    print(f"التقدم: {wizard.progress}%")
    time.sleep(5)

# 4. النتيجة
if wizard.state == 'done':
    print(f"تمت المزامنة بنجاح!")
    print(f"مستورد: {wizard.imported_count}")
    print(f"مُصدّر: {wizard.exported_count}")
else:
    print(f"فشلت المزامنة: {wizard.error_message}")
```

### مثال 4: معالجة الأخطاء وإعادة المحاولة

```python
# 1. البحث عن السجلات الفاشلة
failed_partners = env['sap.res.partner'].search([
    ('sync_error', '!=', False),
    ('backend_id', '=', backend.id)
])

print(f"عدد السجلات الفاشلة: {len(failed_partners)}")

# 2. إعادة المحاولة
for binding in failed_partners:
    try:
        # إعادة تعيين الخطأ
        binding.write({
            'sync_error': False,
            'sync_retry_count': 0,
        })
        
        # إعادة المحاولة
        binding.sync_with_sap()
        
        print(f"✓ نجح: {binding.name}")
    except Exception as e:
        print(f"✗ فشل: {binding.name} - {str(e)}")
```

---

## 🔐 الصلاحيات والأمان

### مجموعات المستخدمين

```xml
<!-- security/sap_security.xml -->

<!-- 1. SAP User - صلاحيات القراءة فقط -->
<record id="group_sap_user" model="res.groups">
    <field name="name">SAP User</field>
    <field name="category_id" ref="module_category_sap"/>
</record>

<!-- 2. SAP Manager - صلاحيات الإدارة -->
<record id="group_sap_manager" model="res.groups">
    <field name="name">SAP Manager</field>
    <field name="category_id" ref="module_category_sap"/>
    <field name="implied_ids" eval="[(4, ref('group_sap_user'))]"/>
</record>

<!-- 3. SAP Administrator - جميع الصلاحيات -->
<record id="group_sap_admin" model="res.groups">
    <field name="name">SAP Administrator</field>
    <field name="category_id" ref="module_category_sap"/>
    <field name="implied_ids" eval="[(4, ref('group_sap_manager'))]"/>
</record>
```

### صلاحيات الوصول

```csv
# security/ir.model.access.csv

id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_sap_backend_user,sap.backend user,model_sap_backend,group_sap_user,1,0,0,0
access_sap_backend_manager,sap.backend manager,model_sap_backend,group_sap_manager,1,1,1,0
access_sap_backend_admin,sap.backend admin,model_sap_backend,group_sap_admin,1,1,1,1
access_sap_binding_user,sap.res.partner user,model_sap_res_partner,group_sap_user,1,0,0,0
access_sap_binding_manager,sap.res.partner manager,model_sap_res_partner,group_sap_manager,1,1,1,1
```

---

## 📊 الإحصائيات والتقارير

### لوحة التحكم الرئيسية

تعرض:
- ✅ عدد الاتصالات النشطة
- ✅ إجمالي السجلات المتزامنة
- ✅ عدد الأخطاء الحالية
- ✅ آخر وقت مزامنة
- ✅ متوسط وقت المزامنة
- ✅ رسوم بيانية للنشاط

### السجلات والتقارير

1. **Sync Log** - سجل جميع عمليات المزامنة
2. **Error Log** - سجل الأخطاء مع التفاصيل
3. **Performance Report** - تقرير الأداء
4. **Data Quality Report** - تقرير جودة البيانات

---

## 🚀 نصائح الأداء

### 1. العمليات الدفعية
- استخدم `batch_size` مناسب (100-500)
- قسّم العمليات الكبيرة إلى دفعات
- استخدم Background jobs للعمليات الطويلة

### 2. التخزين المؤقت
- استخدم `@cached_property` للبيانات الثابتة
- قلل استدعاءات API المتكررة

### 3. المزامنة
- جدول المزامنة في أوقات قليلة الاستخدام
- استخدم الفلاتر لتقليل البيانات المنقولة
- فعّل `skip_existing` عند الاستيراد

### 4. معالجة الأخطاء
- راقب سجل الأخطاء بانتظام
- نظف السجلات القديمة دورياً
- استخدم Retry Mechanism للأخطاء المؤقتة

---

## 📚 موارد إضافية

### الوثائق
- [SAP Service Layer API Documentation](https://help.sap.com/viewer/68a8bcc3f0d542e5a6d70b01d4e8785d)
- [OCA Connector Framework](https://github.com/OCA/connector)
- [Odoo Development Documentation](https://www.odoo.com/documentation/17.0/developer.html)

### الدعم
- فريق التطوير: dev@yourcompany.com
- التقارير الفنية: support@yourcompany.com
- المستندات الداخلية: wiki.yourcompany.com/sap

---

**آخر تحديث:** 21 أكتوبر 2025
**الإصدار:** 2.0.0
**الحالة:** ✅ نشط ومُختبر

