# Document Reference Fields Added

## ✅ Added Missing Reference Number Fields

**Date:** February 12, 2026  
**Issue:** Document APIs were missing important reference number fields

---

## 📋 Fields Added to Document APIs

The following fields are now included in **all** document API responses:

### Reference Numbers (حقول أرقام المراجع)

| Field | Arabic | Type | Description |
|-------|--------|------|-------------|
| `po_number` | رقم أمر الشراء | string | Purchase Order Number |
| `bl_number` | رقم بوليصة الشحن | string | Bill of Lading Number |
| `container_number` | رقم الحاوية | string | Container Number |
| `invoice_number` | رقم الفاتورة | string | Invoice Number |
| `envoy_number` | رقم الإرسالية | string | Envoy/Shipment Number |

---

## 📊 Updated API Responses

### 1. Document List API

**Endpoint:** `POST /api/documents`

**Response now includes:**
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "title": "Financial Document",
      "barcode": "DOC-123",
      "po_number": "PO-2026-001",          // ✅ NEW
      "bl_number": "BL-12345",             // ✅ NEW
      "container_number": "CONT-789",      // ✅ NEW
      "invoice_number": "INV-2026-100",    // ✅ NEW
      "envoy_number": "ENV-456",           // ✅ NEW
      "department_id": 2,
      "department_name": "Finance",
      "document_type_id": 5,
      "document_type_name": "Contract",
      "uploader_id": 2,
      "uploader_name": "Ahmed",
      "upload_date": "2026-01-15T10:00:00",
      "status": "active",
      "confidentiality_level": "internal",
      "file_name": "contract.pdf",
      "file_size": 102400,
      "parent_document_id": null,
      "relation_type": null,
      "note_count": 3,
      "last_modified": "2026-02-11T14:00:00"
    }
  ],
  "pagination": {...}
}
```

---

### 2. Single Document API

**Endpoint:** `POST /api/documents/<document_id>`

**Response now includes:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "title": "Financial Document",
    "barcode": "DOC-123",
    "po_number": "PO-2026-001",          // ✅ NEW
    "bl_number": "BL-12345",             // ✅ NEW
    "container_number": "CONT-789",      // ✅ NEW
    "invoice_number": "INV-2026-100",    // ✅ NEW
    "envoy_number": "ENV-456",           // ✅ NEW
    "department_id": 2,
    "department_name": "Finance",
    "document_type_id": 5,
    "document_type_name": "Contract",
    "uploader_id": 2,
    "uploader_name": "Ahmed",
    "upload_date": "2026-01-15T10:00:00",
    "status": "active",
    "confidentiality_level": "internal",
    "file_name": "contract.pdf",
    "file_size": 102400,
    "parent_document_id": null,
    "relation_type": null,
    "note_count": 3,
    "last_modified": "2026-02-11T14:00:00",
    "is_locked": true,
    "ocr_status": "completed",
    "ocr": {...},
    "tags": [...],
    "versions": [...]
  }
}
```

---

## 🔍 These Fields Are Already Searchable

The global search already searches in these fields:
```python
doc_domain = [
    ('state', '=', 'active'),
    ('is_deleted', '=', False),
    '|', '|', '|', '|', '|',
    ('name', 'ilike', query),
    ('barcode', 'ilike', query),
    ('po_number', 'ilike', query),        // ✅ Already in search
    ('bl_number', 'ilike', query),        // ✅ Already in search
    ('container_number', 'ilike', query), // ✅ Already in search
    ('invoice_number', 'ilike', query),   // ✅ Already in search
]
```

So you can search by PO number, BL number, etc., and now the results will **display** those fields too!

---

## 💡 Use Cases

### Example 1: Search by PO Number
```bash
POST /api/search/global
{
  "query": "PO-2026-001"
}
```

**Result:** Returns documents with that PO number, and the response includes all reference fields.

### Example 2: Display Document Details
When showing document details in UI, you can now display:
```jsx
<div className="document-details">
  <h3>{document.title}</h3>
  <div className="reference-numbers">
    {document.po_number && <span>PO: {document.po_number}</span>}
    {document.bl_number && <span>BL: {document.bl_number}</span>}
    {document.container_number && <span>Container: {document.container_number}</span>}
    {document.invoice_number && <span>Invoice: {document.invoice_number}</span>}
    {document.envoy_number && <span>Envoy: {document.envoy_number}</span>}
  </div>
</div>
```

---

## 📱 TypeScript Interface Update

```typescript
interface Document {
  id: number;
  title: string;
  barcode: string | null;
  
  // Reference Numbers (NEW)
  po_number: string | null;
  bl_number: string | null;
  container_number: string | null;
  invoice_number: string | null;
  envoy_number: string | null;
  
  // Existing fields
  department_id: number;
  department_name: string;
  document_type_id: number;
  document_type_name: string;
  uploader_id: number;
  uploader_name: string;
  upload_date: string;
  status: string;
  confidentiality_level: string;
  file_name: string | null;
  file_size: number;
  
  // Relationship fields
  parent_document_id: number | null;
  relation_type: 'attachment' | 'secondary_document' | null;
  
  // Metadata
  note_count: number;
  last_modified: string;
  is_locked: boolean;
  ocr_status: string;
}
```

---

## 🧪 Testing

### Test Document List API
```bash
curl -X POST "http://localhost:3003/api/documents" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "jsonrpc":"2.0",
    "method":"call",
    "params": {"page": 1},
    "id":1
  }'
```

**Expected:** Each document now includes `po_number`, `bl_number`, `container_number`, `invoice_number`, `envoy_number`

### Test Single Document API
```bash
curl -X POST "http://localhost:3003/api/documents/123" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

**Expected:** Document details include all reference numbers

---

## ✅ Status

- [x] Added 5 reference number fields to document list API
- [x] Added 5 reference number fields to single document API
- [x] Fields are searchable (already were)
- [x] Odoo restarted
- [x] Ready for testing

---

## 🚀 Result

Frontend can now display and work with all document reference numbers!

**Date:** February 12, 2026  
**Odoo:** Running on 192.168.116.15:8070  
**Status:** ✅ Complete
