# ميزة جديدة: تصنيف الإضبارات حسب الشركة/البراند
# New Feature: Company/Brand Classification for Folders

## التاريخ / Date: 2026-02-15

## 📋 الوصف / Description

### بالعربي

تم إضافة إمكانية ربط كل إضبارة بشركة أو براند معين، مما يتيح:

1. **إنشاء عدة إضبارات لنفس الشركة**
   - يمكن للشركة الواحدة أن يكون لها عدة إضبارات
   - مثال: شركة ABC لديها 10 إضبارات مختلفة

2. **فلترة الإضبارات حسب الشركة**
   - عرض جميع الإضبارات التابعة لشركة معينة
   - تسهيل التنظيم والبحث

3. **فلترة الوثائق حسب الشركة**
   - عرض جميع الوثائق التابعة لشركة معينة
   - الوثائق ترث الشركة من الإضبارة

### In English

Added ability to link each folder to a specific company/brand, enabling:

1. **Create multiple folders for same company**
   - One company can have many folders
   - Example: ABC Company has 10 different folders

2. **Filter folders by company**
   - Show all folders belonging to specific company
   - Easier organization and search

3. **Filter documents by company**
   - Show all documents belonging to specific company
   - Documents inherit company from folder

---

## 🔧 التغييرات التقنية / Technical Changes

### 1. نموذج الإضبارة / Folder Model

**File:** `addons/nbs_archive/models/nbs_folder.py`

**حقل جديد / New Field:**
```python
company_id = fields.Many2one(
    'res.partner',
    string='Company/Brand',
    domain="[('is_company', '=', True)]",
    index=True,
    help='Company or brand this folder belongs to'
)
```

**الخصائص / Properties:**
- اختياري (غير مطلوب) / Optional (not required)
- يربط بشركة من res.partner / Links to company from res.partner
- مفهرس للبحث السريع / Indexed for fast search
- فلتر: فقط الشركات (is_company=True) / Filter: only companies

---

### 2. نموذج الوثيقة / Document Model

**File:** `addons/nbs_archive/models/nbs_document.py`

**حقل محسوب / Computed Field:**
```python
company_id = fields.Many2one(
    'res.partner',
    string='Company/Brand',
    related='folder_id.company_id',
    store=True,
    index=True,
    help='Company from folder'
)
```

**الخصائص / Properties:**
- محسوب من الإضبارة / Computed from folder
- مخزن في قاعدة البيانات / Stored in database
- يتحدث تلقائيًا / Updates automatically
- يمكن الفلترة به / Can be filtered

---

## 📡 تحديثات API / API Updates

### 1. قائمة الإضبارات / Get Folders

**Endpoint:** `POST /api/folders`

**معامل جديد / New Parameter:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "department_id": 4,        // اختياري / Optional
    "company_id": 10,          // جديد! / NEW!
    "parent_id": null,
    "state": "active"
  },
  "id": 1
}
```

**الاستجابة / Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 100,
      "name": "HR-Contracts-2024",
      "code": "HR-001",
      "company_id": 10,        // جديد! / NEW!
      "company_name": "ABC Corporation",  // جديد! / NEW!
      "department_id": 4,
      "department_name": "Human Resources",
      "document_count": 15
    }
  ]
}
```

---

### 2. قائمة الوثائق / Get Documents

**Endpoint:** `POST /api/documents`

**معامل جديد / New Parameter:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "department_id": 4,
    "company_id": 10,          // جديد! / NEW!
    "document_type_id": 5,
    "status": "active",
    "page": 1,
    "per_page": 20
  },
  "id": 1
}
```

**الاستجابة / Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 85,
      "title": "Employee Contract",
      "folder_id": 100,
      "folder_name": "HR-Contracts-2024",
      "company_id": 10,          // جديد! / NEW!
      "company_name": "ABC Corporation",  // جديد! / NEW!
      "department_id": 4,
      "is_main_document": true
    }
  ]
}
```

---

### 3. إنشاء إضبارة / Create Folder

**Endpoint:** `POST /api/folders/create`

**معامل جديد / New Parameter:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "name": "Project Files 2024",
    "code": "PROJ-2024",
    "department_id": 4,
    "company_id": 10,          // جديد! / NEW!
    "description": "All project documents for ABC Corp"
  },
  "id": 1
}
```

---

## 🎯 حالات الاستخدام / Use Cases

### حالة 1: إضبارات متعددة لشركة واحدة
### Case 1: Multiple Folders for One Company

```
شركة ABC Corporation (company_id: 10)
├── Contracts 2024 (folder_id: 100)
│   ├── Contract A.pdf (main)
│   └── Contract B.pdf (sub)
├── Invoices 2024 (folder_id: 101)
│   ├── Invoice Jan.pdf (main)
│   └── Invoice Feb.pdf (sub)
└── Reports (folder_id: 102)
    └── Q1 Report.pdf (main)
```

**إنشاء / Create:**
```bash
# Folder 1
POST /api/folders/create
{
  "name": "Contracts 2024",
  "department_id": 4,
  "company_id": 10
}

# Folder 2
POST /api/folders/create
{
  "name": "Invoices 2024",
  "department_id": 4,
  "company_id": 10  // نفس الشركة / Same company
}

# Folder 3
POST /api/folders/create
{
  "name": "Reports",
  "department_id": 4,
  "company_id": 10  // نفس الشركة / Same company
}
```

---

### حالة 2: فلترة حسب الشركة
### Case 2: Filter by Company

**الحصول على جميع إضبارات شركة ABC:**
**Get all folders for ABC Company:**

```bash
POST /api/folders
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "company_id": 10  // عرض إضبارات ABC فقط / Show ABC folders only
  },
  "id": 1
}
```

**النتيجة / Result:**
```json
{
  "data": [
    {"id": 100, "name": "Contracts 2024", "company_name": "ABC Corporation"},
    {"id": 101, "name": "Invoices 2024", "company_name": "ABC Corporation"},
    {"id": 102, "name": "Reports", "company_name": "ABC Corporation"}
  ]
}
```

---

### حالة 3: فلترة الوثائق حسب الشركة
### Case 3: Filter Documents by Company

**الحصول على جميع وثائق شركة ABC:**
**Get all documents for ABC Company:**

```bash
POST /api/documents
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "company_id": 10,  // فلترة حسب الشركة / Filter by company
    "page": 1,
    "per_page": 50
  },
  "id": 1
}
```

**النتيجة / Result:**
- جميع الوثائق في إضبارات شركة ABC / All documents in ABC company folders
- ترث الشركة من الإضبارة / Inherit company from folder

---

### حالة 4: فلترة مركبة
### Case 4: Combined Filters

**وثائق شركة ABC في قسم الموارد البشرية:**
**ABC Company documents in HR department:**

```bash
POST /api/documents
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "company_id": 10,      // الشركة / Company
    "department_id": 4,    // القسم / Department
    "document_type_id": 5, // نوع الوثيقة / Document type
    "status": "active"     // الحالة / Status
  },
  "id": 1
}
```

---

## 🏢 إدارة الشركات / Company Management

### إضافة شركات جديدة / Adding New Companies

**الطريقة 1: عبر واجهة Odoo**
**Method 1: Via Odoo Interface**

1. افتح Odoo → Contacts / Open Odoo → Contacts
2. إنشاء → شركة / Create → Company
3. املأ البيانات / Fill details:
   - الاسم / Name: ABC Corporation
   - هو شركة / Is a Company: ✓
   - العنوان، الهاتف، etc.

**الطريقة 2: عبر SQL**
**Method 2: Via SQL**

```sql
INSERT INTO res_partner (
    name, is_company, active, create_date
) VALUES (
    'XYZ Company', true, true, NOW()
) RETURNING id;
```

**الطريقة 3: عبر API (مستقبلاً)**
**Method 3: Via API (Future)**

```bash
POST /api/companies/create
{
  "name": "DEF Corporation",
  "is_company": true
}
```

---

### الحصول على قائمة الشركات
### Get Companies List

**SQL Query:**
```sql
SELECT id, name 
FROM res_partner 
WHERE is_company = true 
  AND active = true
ORDER BY name;
```

**يمكن إضافة endpoint:**
**Can add endpoint:**

```python
@http.route('/api/companies', type='jsonrpc', auth='none', methods=['POST'])
def get_companies(self, **kwargs):
    companies = request.env['res.partner'].search([
        ('is_company', '=', True),
        ('active', '=', True)
    ], order='name')
    
    return {
        'success': True,
        'data': [{
            'id': c.id,
            'name': c.name,
            'phone': c.phone,
            'email': c.email
        } for c in companies]
    }
```

---

## 💡 أمثلة عملية / Practical Examples

### مثال 1: مؤسسة لها عدة شركات تابعة
### Example 1: Organization with Multiple Subsidiaries

```
المؤسسة / Organization:
├── شركة A / Company A (ID: 10)
│   ├── إضبارة العقود / Contracts Folder
│   ├── إضبارة الفواتير / Invoices Folder
│   └── إضبارة التقارير / Reports Folder
│
├── شركة B / Company B (ID: 11)
│   ├── إضبارة العقود / Contracts Folder
│   ├── إضبارة الفواتير / Invoices Folder
│   └── إضبارة التقارير / Reports Folder
│
└── شركة C / Company C (ID: 12)
    ├── إضبارة العقود / Contracts Folder
    └── إضبارة المشاريع / Projects Folder
```

**الفلترة / Filtering:**
```javascript
// الحصول على جميع إضبارات شركة A
// Get all folders for Company A
const companyAFolders = await getFolders({company_id: 10});

// الحصول على جميع وثائق شركة B
// Get all documents for Company B
const companyBDocuments = await getDocuments({company_id: 11});
```

---

### مثال 2: براندات مختلفة
### Example 2: Different Brands

```
الشركة الأم / Parent Company: XYZ Group
├── براند: Nike (ID: 20)
│   └── إضبارات المنتجات / Product Folders
├── براند: Adidas (ID: 21)
│   └── إضبارات المنتجات / Product Folders
└── براند: Puma (ID: 22)
    └── إضبارات المنتجات / Product Folders
```

---

## 🎨 تكامل Frontend / Frontend Integration

### JavaScript مثال / JavaScript Example

```javascript
// 1. الحصول على قائمة الشركات
// 1. Get companies list
async function getCompanies() {
  const response = await fetch('/api/companies', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'call',
      params: {},
      id: 1
    })
  });
  
  const result = await response.json();
  return result.result.data;
}

// 2. إنشاء إضبارة مع شركة
// 2. Create folder with company
async function createFolderWithCompany(name, departmentId, companyId) {
  const response = await fetch('/api/folders/create', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'call',
      params: {
        name: name,
        code: name.toUpperCase(),
        department_id: departmentId,
        company_id: companyId  // إضافة الشركة / Add company
      },
      id: 1
    })
  });
  
  return await response.json();
}

// 3. فلترة الإضبارات حسب الشركة
// 3. Filter folders by company
async function getFoldersByCompany(companyId) {
  const response = await fetch('/api/folders', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'call',
      params: {
        company_id: companyId  // فلترة / Filter
      },
      id: 1
    })
  });
  
  const result = await response.json();
  return result.result.data;
}

// 4. فلترة الوثائق حسب الشركة
// 4. Filter documents by company
async function getDocumentsByCompany(companyId) {
  const response = await fetch('/api/documents', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type: application/json'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'call',
      params: {
        company_id: companyId,  // فلترة / Filter
        page: 1,
        per_page: 50
      },
      id: 1
    })
  });
  
  const result = await response.json();
  return result.result.data;
}
```

---

### React مثال / React Example

```jsx
import React, { useState, useEffect } from 'react';

const FoldersByCompany = () => {
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [folders, setFolders] = useState([]);
  
  // تحميل الشركات / Load companies
  useEffect(() => {
    loadCompanies();
  }, []);
  
  // تحميل الإضبارات عند تغيير الشركة
  // Load folders when company changes
  useEffect(() => {
    if (selectedCompany) {
      loadFoldersByCompany(selectedCompany);
    }
  }, [selectedCompany]);
  
  return (
    <div>
      <h2>فلترة حسب الشركة / Filter by Company</h2>
      
      {/* قائمة الشركات / Companies dropdown */}
      <select onChange={(e) => setSelectedCompany(e.target.value)}>
        <option value="">جميع الشركات / All Companies</option>
        {companies.map(c => (
          <option key={c.id} value={c.id}>{c.name}</option>
        ))}
      </select>
      
      {/* قائمة الإضبارات / Folders list */}
      <div>
        <h3>الإضبارات / Folders ({folders.length})</h3>
        {folders.map(folder => (
          <div key={folder.id}>
            <h4>{folder.name}</h4>
            <p>الشركة / Company: {folder.company_name}</p>
            <p>الوثائق / Documents: {folder.document_count}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## 📊 مثال كامل / Complete Example

### السيناريو / Scenario:

شركة لديها 3 براندات، كل براند له عدة إضبارات:

A company has 3 brands, each brand has multiple folders:

```javascript
// إنشاء الشركات/البراندات أولاً
// Create companies/brands first
const nike = await createCompany('Nike');
const adidas = await createCompany('Adidas');  
const puma = await createCompany('Puma');

// إنشاء إضبارات Nike
// Create Nike folders
await createFolder('Nike Products 2024', 4, nike.id);
await createFolder('Nike Marketing', 4, nike.id);
await createFolder('Nike Contracts', 4, nike.id);

// إنشاء إضبارات Adidas
// Create Adidas folders
await createFolder('Adidas Products 2024', 4, adidas.id);
await createFolder('Adidas Marketing', 4, adidas.id);

// إنشاء إضبارات Puma
// Create Puma folders
await createFolder('Puma Products 2024', 4, puma.id);

// الآن يمكن الفلترة
// Now can filter

// جميع إضبارات Nike
// All Nike folders
const nikeFolders = await getFolders({company_id: nike.id});
// Returns: 3 folders

// جميع وثائق Adidas
// All Adidas documents
const adidasDocs = await getDocuments({company_id: adidas.id});
```

---

## 🗄️ تحديثات قاعدة البيانات / Database Updates

### حقول جديدة / New Fields

**جدول: nbs_document_folder**
```sql
ALTER TABLE nbs_document_folder
ADD COLUMN company_id INTEGER REFERENCES res_partner(id);

CREATE INDEX idx_folder_company ON nbs_document_folder(company_id);
```

**جدول: nbs_document** (محسوب/مخزن)
```sql
ALTER TABLE nbs_document
ADD COLUMN company_id INTEGER REFERENCES res_partner(id);

CREATE INDEX idx_document_company ON nbs_document(company_id);
```

**ملاحظة:** Odoo سيقوم بهذا تلقائيًا عند التحديث  
**Note:** Odoo will do this automatically on module update

---

## 📋 API Endpoints Summary

### Updated Endpoints:

| Endpoint | New Parameter | Description |
|----------|--------------|-------------|
| `POST /api/folders` | `company_id` | فلترة الإضبارات / Filter folders |
| `POST /api/documents` | `company_id` | فلترة الوثائق / Filter documents |
| `POST /api/folders/create` | `company_id` | تحديد الشركة / Set company |

### Response Fields Added:

| Field | Type | Description |
|-------|------|-------------|
| `company_id` | Integer/null | معرف الشركة / Company ID |
| `company_name` | String/null | اسم الشركة / Company name |

---

## 🔍 استعلامات مفيدة / Useful Queries

### 1. عدد الإضبارات لكل شركة
### 1. Count Folders per Company

```sql
SELECT 
    p.name as company_name,
    COUNT(f.id) as folder_count
FROM nbs_document_folder f
JOIN res_partner p ON f.company_id = p.id
WHERE f.active = true
GROUP BY p.name
ORDER BY folder_count DESC;
```

### 2. عدد الوثائق لكل شركة
### 2. Count Documents per Company

```sql
SELECT 
    p.name as company_name,
    COUNT(d.id) as document_count
FROM nbs_document d
JOIN res_partner p ON d.company_id = p.id
WHERE d.is_deleted = false
GROUP BY p.name
ORDER BY document_count DESC;
```

### 3. الشركات بدون إضبارات
### 3. Companies Without Folders

```sql
SELECT p.id, p.name
FROM res_partner p
WHERE p.is_company = true
  AND NOT EXISTS (
    SELECT 1 FROM nbs_document_folder f 
    WHERE f.company_id = p.id AND f.active = true
  )
ORDER BY p.name;
```

---

## 🎯 حالة خاصة / Special Cases

### إضبارات بدون شركة
### Folders Without Company

- `company_id = null` صالح / Valid
- للإضبارات العامة / For general folders
- لا تنتمي لشركة معينة / Don't belong to specific company

### الوثائق خارج الإضبارات
### Documents Outside Folders

- `company_id = null` (لأن folder_id = null)
- الوثائق المستقلة / Standalone documents
- لا شركة / No company

---

## 🚀 حالة النشر / Deployment Status

### التغييرات المطبقة / Changes Applied:

- ✅ إضافة company_id للإضبارة / Added company_id to folder
- ✅ إضافة company_id للوثيقة (محسوب) / Added company_id to document (computed)
- ✅ تحديث API الإضبارات / Updated folders API
- ✅ تحديث API الوثائق / Updated documents API
- ✅ تحديث إنشاء الإضبارة / Updated folder creation
- ✅ تحديث الاستجابات / Updated responses

### الخدمة / Service:

- ✅ الموديول قيد التحديث / Module updating
- ✅ Odoo PID: 2304504
- ✅ التحديث سيكتمل قريباً / Update will complete soon

---

## 📝 الخطوات التالية / Next Steps

### 1. إنشاء API للشركات (اختياري)
### 1. Create Companies API (Optional)

```python
# في controller جديد / In new controller
@http.route('/api/companies', type='jsonrpc', ...)
def list_companies(self, **kwargs):
    # قائمة الشركات / List companies
    
@http.route('/api/companies/create', type='http', ...)
def create_company(self, name, **kwargs):
    # إنشاء شركة / Create company
```

### 2. إضافة dashboard للشركات
### 2. Add Company Dashboard

```python
@http.route('/api/companies/<int:company_id>/stats', ...)
def get_company_stats(self, company_id):
    return {
        'folder_count': ...,
        'document_count': ...,
        'total_size': ...,
        'recent_documents': ...
    }
```

### 3. تقرير حسب الشركة
### 3. Company Reports

```python
@http.route('/api/reports/by-company', ...)
def company_report(self):
    # تقرير شامل لكل شركة / Comprehensive report per company
```

---

## 🎓 ملاحظات مهمة / Important Notes

### 1. الحقل اختياري / Field is Optional

- `company_id` غير مطلوب / Not required
- يمكن إنشاء إضبارات بدون شركة / Can create folders without company
- متوافق مع الوضع الحالي / Backward compatible

### 2. الوثائق ترث من الإضبارة / Documents Inherit from Folder

- `company_id` في الوثيقة محسوب / company_id in document is computed
- يتحدث تلقائيًا / Updates automatically
- إذا نقلت وثيقة لإضبارة أخرى، تتغير الشركة / If you move document to another folder, company changes

### 3. الفلترة مرنة / Flexible Filtering

يمكن الجمع بين عدة فلاتر:
Can combine multiple filters:

```javascript
getFolders({
  department_id: 4,   // القسم / Department
  company_id: 10,     // الشركة / Company
  parent_id: null     // الجذر / Root level
})
```

---

## ✅ الملخص / Summary

### ما تم إضافته / What Was Added:

1. ✅ حقل `company_id` في الإضبارة / company_id field in folder
2. ✅ حقل `company_id` محسوب في الوثيقة / Computed company_id in document
3. ✅ فلترة الإضبارات حسب الشركة / Filter folders by company
4. ✅ فلترة الوثائق حسب الشركة / Filter documents by company
5. ✅ حقول company_name في الاستجابات / company_name in responses
6. ✅ دعم إنشاء إضبارات مع شركة / Support creating folders with company

### المميزات / Features:

- 🏢 ربط الإضبارات بالشركات / Link folders to companies
- 📁 عدة إضبارات لشركة واحدة / Multiple folders per company
- 🔍 فلترة قوية / Powerful filtering
- 🔄 ورثة تلقائية للوثائق / Automatic inheritance for documents
- 📊 إمكانية التقارير حسب الشركة / Enable company-based reports

---

**الإصدار / Version:** 2.1.0  
**الأولوية / Priority:** ميزة جديدة / New Feature  
**الحالة / Status:** ✅ قيد النشر / Deploying

**الميزة جاهزة! بعد اكتمال تحديث الموديول، يمكنك استخدام الفلترة حسب الشركة!**  
**Feature ready! After module update completes, you can use company filtering!** 🎉
