# دليل API - ميزة الشركات/البراندات

## التاريخ: 2026-02-16

---

## 📋 نظرة عامة

تم إضافة نظام كامل لإدارة الشركات/البراندات في نظام الأرشفة، يتيح:

✅ ربط الإضبارات بالشركات  
✅ فلترة الإضبارات والوثائق حسب الشركة  
✅ إنشاء عدة إضبارات لنفس الشركة  
✅ تقارير وإحصائيات حسب الشركة  

---

## 🔌 Endpoints الجديدة

### 1. قائمة الشركات / GET /api/companies

**الطلب:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "search": "ABC",  // اختياري: البحث في الاسم
    "limit": 100      // اختياري: عدد النتائج (افتراضي: 100)
  },
  "id": 1
}
```

**الاستجابة:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": [
      {
        "id": 10,
        "name": "ABC Corporation",
        "phone": "+123456789",
        "email": "info@abc.com",
        "vat": "123456",
        "street": "123 Main St",
        "city": "Amman",
        "country_name": "Jordan"
      }
    ],
    "count": 1
  }
}
```

---

### 2. تفاصيل شركة مع إحصائيات / GET /api/companies/<id>

**الطلب:**
```bash
POST /api/companies/10
```

**الاستجابة:**
```json
{
  "success": true,
  "data": {
    "id": 10,
    "name": "ABC Corporation",
    "phone": "+123456789",
    "email": "info@abc.com",
    "folder_count": 15,        // عدد الإضبارات
    "document_count": 245      // عدد الوثائق
  }
}
```

---

### 3. إنشاء شركة جديدة / POST /api/companies/create

**الطلب:**
```json
{
  "name": "DEF Company",      // مطلوب
  "phone": "+962123456",      // اختياري
  "email": "info@def.com",    // اختياري
  "vat": "789456123",         // اختياري
  "street": "456 Business St", // اختياري
  "city": "Amman"             // اختياري
}
```

**الاستجابة:**
```json
{
  "success": true,
  "message": "Company created successfully",
  "data": {
    "id": 15,
    "name": "DEF Company"
  }
}
```

---

### 4. إحصائيات الشركة / GET /api/companies/<id>/stats

**الطلب:**
```bash
POST /api/companies/10/stats
```

**الاستجابة:**
```json
{
  "success": true,
  "data": {
    "company": {
      "id": 10,
      "name": "ABC Corporation"
    },
    "totals": {
      "folders": 15,
      "documents": 245,
      "main_documents": 15,
      "sub_documents": 230
    },
    "by_department": {
      "Human Resources": {"count": 50, "main": 5, "sub": 45},
      "Finance": {"count": 100, "main": 8, "sub": 92},
      "Legal": {"count": 95, "main": 2, "sub": 93}
    },
    "by_type": {
      "Contract": 80,
      "Invoice": 120,
      "Report": 45
    }
  }
}
```

---

## 📁 Endpoints المحدثة

### 1. إنشاء إضبارة مع شركة / Create Folder with Company

**الطلب:**
```json
POST /api/folders/create
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "name": "عقود 2024",
    "code": "CONTRACTS-2024",
    "department_id": 4,
    "company_id": 10,          // جديد! / NEW!
    "description": "عقود شركة ABC"
  },
  "id": 1
}
```

---

### 2. فلترة الإضبارات / Filter Folders

**بدون فلترة (جميع الإضبارات):**
```json
POST /api/folders
{
  "params": {}
}
```

**فلترة حسب الشركة:**
```json
POST /api/folders
{
  "params": {
    "company_id": 10  // فقط إضبارات شركة ABC
  }
}
```

**فلترة مركبة:**
```json
POST /api/folders
{
  "params": {
    "company_id": 10,      // الشركة
    "department_id": 4,    // القسم
    "state": "active"      // الحالة
  }
}
```

---

### 3. فلترة الوثائق / Filter Documents

**حسب الشركة فقط:**
```json
POST /api/documents
{
  "params": {
    "company_id": 10,
    "page": 1,
    "per_page": 20
  }
}
```

**فلترة متقدمة:**
```json
POST /api/documents
{
  "params": {
    "company_id": 10,           // الشركة
    "department_id": 4,         // القسم
    "document_type_id": 5,      // نوع الوثيقة
    "status": "active",         // الحالة
    "search": "عقد"             // بحث في العنوان
  }
}
```

---

## 🎯 أمثلة الاستخدام / Usage Examples

### مثال 1: إضافة شركة وإنشاء إضبارات لها

```javascript
// 1. إضافة شركة جديدة
const company = await createCompany({
  name: "شركة الرواد للتجارة",
  phone: "+962777123456",
  email: "info@rawad.jo",
  city: "عمان"
});

console.log(`تم إنشاء شركة: ${company.name} (ID: ${company.id})`);

// 2. إنشاء إضبارات لهذه الشركة
const folders = [
  {name: "عقود الموظفين", dept: 4, company: company.id},
  {name: "فواتير 2024", dept: 2, company: company.id},
  {name: "تقارير سنوية", dept: 1, company: company.id}
];

for (const folder of folders) {
  await createFolder(folder.name, folder.dept, folder.company);
}

console.log(`تم إنشاء ${folders.length} إضبارات للشركة`);

// 3. عرض جميع إضبارات هذه الشركة
const companyFolders = await getFolders({
  company_id: company.id
});

console.log(`الشركة لديها ${companyFolders.length} إضبارات`);
```

---

### مثال 2: فلترة ديناميكية

```javascript
const CompanyFilter = () => {
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [documents, setDocuments] = useState([]);
  
  // تحميل الشركات عند بداية التشغيل
  useEffect(() => {
    async function loadCompanies() {
      const result = await fetch('/api/companies', {...});
      setCompanies(result.data);
    }
    loadCompanies();
  }, []);
  
  // تحميل الوثائق عند تغيير الشركة
  useEffect(() => {
    if (selectedCompany) {
      async function loadDocs() {
        const result = await fetch('/api/documents', {
          params: {company_id: selectedCompany}
        });
        setDocuments(result.data);
      }
      loadDocs();
    }
  }, [selectedCompany]);
  
  return (
    <div>
      <select onChange={e => setSelectedCompany(e.target.value)}>
        <option value="">جميع الشركات</option>
        {companies.map(c => (
          <option key={c.id} value={c.id}>{c.name}</option>
        ))}
      </select>
      
      <div>
        <h3>الوثائق ({documents.length})</h3>
        {documents.map(doc => (
          <div key={doc.id}>
            <p>{doc.title}</p>
            <small>الشركة: {doc.company_name}</small>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## 📊 استعلامات مفيدة / Useful Queries

### 1. جميع الشركات مع عدد الإضبارات

```sql
SELECT 
    p.id,
    p.name,
    COUNT(f.id) as folder_count
FROM res_partner p
LEFT JOIN nbs_document_folder f ON f.company_id = p.id AND f.active = true
WHERE p.is_company = true AND p.active = true
GROUP BY p.id, p.name
ORDER BY folder_count DESC;
```

### 2. الشركات الأكثر استخدامًا

```sql
SELECT 
    p.name as company_name,
    COUNT(DISTINCT f.id) as folders,
    COUNT(d.id) as documents
FROM res_partner p
LEFT JOIN nbs_document_folder f ON f.company_id = p.id
LEFT JOIN nbs_document d ON d.company_id = p.id AND d.is_deleted = false
WHERE p.is_company = true
GROUP BY p.name
HAVING COUNT(d.id) > 0
ORDER BY COUNT(d.id) DESC;
```

### 3. إضبارات بدون شركة

```sql
SELECT id, name, code
FROM nbs_document_folder
WHERE company_id IS NULL
  AND active = true;
```

---

## 🎨 واجهة المستخدم / UI Components

### قائمة منسدلة للشركات / Companies Dropdown

```jsx
<select name="company_id">
  <option value="">-- اختر الشركة --</option>
  {companies.map(company => (
    <option key={company.id} value={company.id}>
      {company.name}
    </option>
  ))}
</select>
```

### بطاقة إحصائيات الشركة / Company Stats Card

```jsx
const CompanyStatsCard = ({ companyId }) => {
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    fetchCompanyStats(companyId).then(setStats);
  }, [companyId]);
  
  if (!stats) return <div>جاري التحميل...</div>;
  
  return (
    <div className="company-stats">
      <h3>{stats.company.name}</h3>
      <div className="stats-grid">
        <div>
          <span>الإضبارات</span>
          <strong>{stats.totals.folders}</strong>
        </div>
        <div>
          <span>الوثائق</span>
          <strong>{stats.totals.documents}</strong>
        </div>
        <div>
          <span>وثائق رئيسية</span>
          <strong>{stats.totals.main_documents}</strong>
        </div>
      </div>
    </div>
  );
};
```

---

## 🔄 الترحيل / Migration

### للإضبارات الموجودة / For Existing Folders

الإضبارات الحالية ستبقى بدون شركة (`company_id = null`) حتى تقوم بتحديثها:

Existing folders will remain without company until you update them:

```sql
-- تحديث إضبارة لإضافة شركة
-- Update folder to add company
UPDATE nbs_document_folder
SET company_id = 10  -- ABC Corporation
WHERE id IN (100, 101, 102);
```

**أو عبر API:**
```bash
POST /api/folders/114/update
{
  "company_id": 10
}
```

---

## 📱 أمثلة cURL

### الحصول على الشركات

```bash
curl -X POST http://localhost:8070/api/companies \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {},
    "id": 1
  }'
```

### إنشاء شركة

```bash
curl -X POST http://localhost:8070/api/companies/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "شركة النجاح",
    "phone": "+962779999999",
    "email": "info@najah.jo",
    "city": "عمان"
  }'
```

### فلترة الإضبارات حسب شركة

```bash
curl -X POST http://localhost:8070/api/folders \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "company_id": 10
    },
    "id": 1
  }'
```

### فلترة الوثائق حسب شركة

```bash
curl -X POST http://localhost:8070/api/documents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "company_id": 10,
      "page": 1,
      "per_page": 20
    },
    "id": 1
  }'
```

---

## 🎯 حالات استخدام شائعة / Common Use Cases

### 1. نظام Multi-Tenant

إذا كان لديك عدة شركات/عملاء يستخدمون نفس النظام:

```javascript
// كل عميل له شركة
const client1 = await createCompany("العميل الأول");
const client2 = await createCompany("العميل الثاني");

// عزل البيانات
const client1Docs = await getDocuments({company_id: client1.id});
const client2Docs = await getDocuments({company_id: client2.id});

// لا تداخل في البيانات!
```

### 2. براندات متعددة

```javascript
// شركة أم لديها عدة براندات
const nike = await createCompany("Nike");
const adidas = await createCompany("Adidas");

// كل براند له إضباراته
await createFolder("Nike Spring 2024", 1, nike.id);
await createFolder("Nike Fall 2024", 1, nike.id);

await createFolder("Adidas Spring 2024", 1, adidas.id);
await createFolder("Adidas Fall 2024", 1, adidas.id);

// فصل كامل بين البراندات
```

### 3. تقارير حسب الشركة

```javascript
async function generateCompanyReport(companyId) {
  const stats = await getCompanyStats(companyId);
  const folders = await getFolders({company_id: companyId});
  const documents = await getDocuments({company_id: companyId});
  
  return {
    company: stats.company.name,
    summary: stats.totals,
    folders: folders,
    documents: documents,
    departments: stats.by_department,
    types: stats.by_type
  };
}
```

---

## 🔍 البحث والفلترة / Search & Filtering

### فلترة متعددة المستويات

```javascript
// مثال: وثائق قسم الموارد البشرية لشركة ABC من نوع عقد
const results = await getDocuments({
  company_id: 10,        // شركة ABC
  department_id: 4,      // الموارد البشرية
  document_type_id: 5,   // عقد
  status: 'active',      // نشط
  search: '2024'         // يحتوي على 2024
});

console.log(`النتائج: ${results.length} وثيقة`);
```

---

## 📚 التوثيق الكامل / Complete Documentation

### الملفات ذات الصلة:

1. **FEATURE_COMPANY_BRAND_FOLDERS.md** - التوثيق الإنجليزي
2. **COMPANY_FEATURE_API_GUIDE_AR.md** - هذا الملف (عربي)

### Endpoints Summary:

| Endpoint | الوصف | Description |
|----------|--------|-------------|
| `POST /api/companies` | قائمة الشركات | List companies |
| `POST /api/companies/<id>` | تفاصيل شركة | Company details |
| `POST /api/companies/create` | إنشاء شركة | Create company |
| `POST /api/companies/<id>/stats` | إحصائيات الشركة | Company statistics |
| `POST /api/folders` | **محدث:** فلترة حسب company_id | **Updated:** Filter by company_id |
| `POST /api/documents` | **محدث:** فلترة حسب company_id | **Updated:** Filter by company_id |
| `POST /api/folders/create` | **محدث:** إضافة company_id | **Updated:** Add company_id |

---

## ✅ الملخص / Summary

### ما تم إضافته:

1. ✅ حقل company_id في الإضبارات
2. ✅ حقل company_id محسوب في الوثائق
3. ✅ 4 endpoints جديدة للشركات
4. ✅ فلترة في API الإضبارات
5. ✅ فلترة في API الوثائق
6. ✅ إحصائيات ديناميكية

### الفوائد:

- 🏢 تنظيم أفضل للإضبارات
- 🔍 فلترة قوية ومرنة
- 📊 تقارير حسب الشركة
- 🎯 فصل بيانات الشركات
- 📈 قابلية التوسع

---

**الحالة / Status:** ✅ قيد النشر / Deploying  
**الإصدار / Version:** 2.1.0  

**الميزة جاهزة للاستخدام بعد اكتمال تحديث Odoo!**  
**Feature ready to use after Odoo update completes!** 🎉
