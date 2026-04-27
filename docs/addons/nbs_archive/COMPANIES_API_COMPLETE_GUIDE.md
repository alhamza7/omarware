# Companies API - Complete Guide

## 📋 All Endpoints

### 1️⃣ List Companies

**Endpoint:** `POST /api/companies`  
**Type:** jsonrpc  
**Auth:** Required

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "search": "optional search term",
    "limit": 100
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": [
      {
        "id": 1,
        "name": "My Company",
        "phone": "+123456789",
        "email": "info@company.com",
        "vat": "123456789",
        "street": "123 Main St",
        "city": "City Name",
        "country_id": 233,
        "country_name": "United States"
      }
    ],
    "count": 1
  }
}
```

---

### 2️⃣ List Countries (NEW!)

**Endpoint:** `POST /api/countries`  
**Type:** jsonrpc  
**Auth:** Required

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "search": "united",
    "limit": 100
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": [
      {
        "id": 233,
        "name": "United States",
        "code": "US",
        "phone_code": 1
      },
      {
        "id": 77,
        "name": "United Kingdom",
        "code": "GB",
        "phone_code": 44
      },
      {
        "id": 1,
        "name": "United Arab Emirates",
        "code": "AE",
        "phone_code": 971
      }
    ],
    "count": 3
  }
}
```

**Use for:** Country autocomplete/dropdown when creating/editing companies.

---

### 3️⃣ Create Company (Managers Only)

**Endpoint:** `POST /api/companies/create`  
**Type:** http (NOT jsonrpc)  
**Auth:** Required (Manager only)

**Request (Option 1: Using country_id):**
```json
{
  "name": "International Corp",
  "phone": "+1-555-0100",
  "email": "info@intl.com",
  "vat": "US123456789",
  "street": "123 Wall Street",
  "city": "New York",
  "country_id": 233,
  "website": "www.intl.com"
}
```

**Request (Option 2: Using country_name - NEW!):**
```json
{
  "name": "International Corp",
  "phone": "+1-555-0100",
  "email": "info@intl.com",
  "vat": "US123456789",
  "street": "123 Wall Street",
  "city": "New York",
  "country_name": "United States",
  "website": "www.intl.com"
}
```

**How country_name works:**
1. Backend searches for country by name (case-insensitive)
2. If found → uses existing country
3. If NOT found → creates new country automatically with 2-letter code

**Response:**
```json
{
  "success": true,
  "message": "Company created successfully",
  "data": {
    "id": 2,
    "name": "International Corp"
  }
}
```

---

### 4️⃣ Update Company (Managers Only)

**Endpoint:** `POST /api/companies/<company_id>/update`  
**Type:** http (NOT jsonrpc)  
**Auth:** Required (Manager only)

**Example:** `POST /api/companies/2/update`

**Request:**
```json
{
  "name": "Updated Corp Name",
  "phone": "+1-555-9999",
  "email": "new@email.com",
  "vat": "NEW_VAT_123",
  "street": "456 New Address",
  "city": "Los Angeles",
  "country_name": "United States",
  "website": "www.newsite.com"
}
```

**Note:** Send only fields you want to update. Accepts both `country_id` and `country_name`.

**Response:**
```json
{
  "success": true,
  "message": "Company updated successfully",
  "data": {
    "id": 2,
    "name": "Updated Corp Name"
  }
}
```

---

### 5️⃣ Delete Company (Managers Only)

**Endpoint:** `DELETE /api/companies/<company_id>`  
**Type:** http  
**Auth:** Required (Manager only)

**Example:** `DELETE /api/companies/2`

**Success Response:**
```json
{
  "success": true,
  "message": "Company deleted successfully",
  "data": {
    "id": 2
  }
}
```

**Error (has folders):**
```json
{
  "success": false,
  "error": "Cannot delete company that has folders",
  "code": "COMPANY_HAS_FOLDERS",
  "folder_count": 5,
  "message_ar": "لا يمكن حذف الشركة لوجود فولدرات مرتبطة بها. قم بإزالة أو نقل الفولدرات أولاً."
}
```

---

### 6️⃣ Get Company Details

**Endpoint:** `POST /api/companies/<company_id>`  
**Type:** jsonrpc  
**Auth:** Required

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": {
      "id": 1,
      "name": "My Company",
      "phone": "+123456789",
      "email": "info@company.com",
      "vat": "123456789",
      "street": "123 Main St",
      "city": "New York",
      "country_id": 233,
      "country_name": "United States",
      "website": "www.company.com",
      "folder_count": 5,
      "document_count": 12
    }
  }
}
```

---

### 7️⃣ Get Company Statistics

**Endpoint:** `POST /api/companies/<company_id>/stats`  
**Type:** jsonrpc  
**Auth:** Required

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": {
      "company": {
        "id": 1,
        "name": "My Company"
      },
      "totals": {
        "folders": 5,
        "documents": 12,
        "main_documents": 8,
        "sub_documents": 4
      },
      "by_department": {
        "Finance": { "count": 7, "main": 5, "sub": 2 },
        "HR": { "count": 5, "main": 3, "sub": 2 }
      },
      "by_type": {
        "Contract": 5,
        "Invoice": 4,
        "Report": 3
      }
    }
  }
}
```

---

## 🎨 UI Implementation Examples

### Company Creation Form

**With Country Autocomplete:**

```javascript
// 1. User types in country field
onCountrySearch(searchTerm) {
  // Call countries API
  POST /api/countries
  params: { search: searchTerm, limit: 10 }
  
  // Show dropdown with results
  // User selects: "United States"
}

// 2. Submit company form
onSubmitCompany(formData) {
  POST /api/companies/create
  body: {
    name: formData.name,
    phone: formData.phone,
    email: formData.email,
    vat: formData.vat,
    street: formData.street,
    city: formData.city,
    country_name: formData.countryName,  // "United States"
    website: formData.website
  }
  
  // Backend handles finding/creating country automatically
}
```

**With Country Dropdown:**

```javascript
// Option 1: Load all countries on form open
async loadCountries() {
  const response = await POST('/api/countries', { limit: 300 })
  this.countries = response.result.data
  // Show as dropdown
}

// Option 2: Use country_name directly (simpler)
onSubmitCompany(formData) {
  POST /api/companies/create
  body: {
    name: formData.name,
    country_name: formData.countryInput,  // User types "Saudi Arabia"
    ...
  }
  // Backend creates country if doesn't exist
}
```

---

### Company Edit Form

```javascript
async editCompany(companyId, updates) {
  POST `/api/companies/${companyId}/update`
  body: {
    name: updates.name,
    phone: updates.phone,
    email: updates.email,
    country_name: updates.country,  // Can use country_name
    ...
  }
}
```

---

### Company Delete with Error Handling

```javascript
async deleteCompany(companyId) {
  try {
    const response = await DELETE(`/api/companies/${companyId}`)
    
    if (response.success) {
      alert('Company deleted successfully')
      refreshList()
    }
  } catch (error) {
    if (error.code === 'COMPANY_HAS_FOLDERS') {
      // Show Arabic message or custom message
      alert(error.message_ar)
      // OR
      alert(`Cannot delete: ${error.folder_count} folders are linked to this company`)
    } else {
      alert(error.error)
    }
  }
}
```

---

## 📊 Quick Reference

| Endpoint | Method | Type | Permission | Purpose |
|----------|--------|------|------------|---------|
| `/api/companies` | POST | jsonrpc | Any | List companies |
| `/api/countries` | POST | jsonrpc | Any | List countries (NEW!) |
| `/api/companies/create` | POST | http | Manager | Create company |
| `/api/companies/<id>/update` | POST | http | Manager | Update company |
| `/api/companies/<id>` | DELETE | http | Manager | Delete company |
| `/api/companies/<id>` | POST | jsonrpc | Any | Get company details |
| `/api/companies/<id>/stats` | POST | jsonrpc | Any | Get statistics |

---

## 🌍 Country Handling

### Two Options for FE:

**Option 1: Use country_name (Simpler)**
- User types country name as text
- Send `country_name: "United States"`
- Backend handles finding/creating country
- ✅ No need to load countries list
- ✅ Works for any country (even if not in DB)

**Option 2: Use country_id (More structured)**
- Load countries via `POST /api/countries`
- Show autocomplete dropdown
- User selects country
- Send `country_id: 233`
- ✅ Better UX with autocomplete
- ✅ Validates country exists

**Recommendation:** Use Option 1 (`country_name`) with autocomplete from `/api/countries` for best UX.

---

## ✅ All Features Ready

- ✅ Create company with `country_name` (auto-creates country if needed)
- ✅ Update company with `country_name`
- ✅ List countries for autocomplete
- ✅ Delete company (with folder protection)
- ✅ Get company statistics

**Odoo restarted and ready for testing!** 🚀
