# Company ID Fix - Complete Summary

## Problem
Documents were showing `company_id: null` and `company_name: null` in API responses, even when their folders had `company_id` set.

## Root Cause
The `company_id` field was defined as a **computed field only**, which meant:
1. It computed AFTER document creation (too late for API response)
2. It was readonly by default (couldn't be set manually)
3. The ORM wasn't triggering the computation immediately

## Solution Implemented

### 1. Modified Field Definition
**File:** `addons/nbs_archive/models/nbs_document.py`

Changed from pure computed field to computed field with manual override:
```python
company_id = fields.Many2one(
    'res.partner',
    string='Company/Brand',
    compute='_compute_company_id',
    store=True,
    readonly=False,  # ← ADDED: Allows manual setting
    index=True,
    help='Company/brand from folder.'
)
```

### 2. Enhanced Create Method
**File:** `addons/nbs_archive/models/nbs_document.py`

Added code to **explicitly set company_id during document creation**:
```python
# In create() method, before super().create():
if vals.get('folder_id') and 'company_id' not in vals:
    folder = self.env['nbs.document.folder'].browse(vals['folder_id'])
    if folder.exists() and folder.company_id:
        vals['company_id'] = folder.company_id.id
```

### 3. Enhanced Write Method  
**File:** `addons/nbs_archive/models/nbs_document.py`

Added code to **update company_id when folder changes**:
```python
# In write() method:
if 'folder_id' in vals:
    if vals['folder_id']:
        folder = self.env['nbs.document.folder'].browse(vals['folder_id'])
        if folder.exists() and folder.company_id:
            vals['company_id'] = folder.company_id.id
        else:
            vals['company_id'] = False
    else:
        vals['company_id'] = False
```

### 4. Keep Computed Method as Backup
The `_compute_company_id()` method still exists and will recompute company_id if:
- Folder's company changes
- Dependencies are invalidated
- Manual recomputation is triggered

---

## How It Works Now

### For Main Documents
1. **Create folder with company_id = 1**
2. **Upload main document to that folder**
3. **During document creation:**
   - `folder_id` is set
   - Backend automatically sets `company_id = 1` from folder
4. **API response includes:**
   - `company_id: 1` ✓
   - `company_name: "Company Name"` ✓

### For Secondary Documents (Sub-documents/Attachments)
1. **Secondary document is uploaded to same folder**
2. **During creation:**
   - `folder_id` is set to the same folder
   - Backend automatically sets `company_id = 1` from folder
3. **API response includes:**
   - `company_id: 1` ✓
   - `company_name: "Company Name"` ✓

### Automatic Updates
- **Change folder's company:** All documents in that folder will update automatically
- **Move document to different folder:** Document's company_id updates to match new folder

---

## Testing Results

✅ **Test 1: Document Creation**
- Created document in folder with company_id
- Result: Document has correct company_id immediately

✅ **Test 2: Existing Documents**  
- Recomputed all existing documents
- Result: All documents have correct company_id

✅ **Test 3: API Response**
- Both `company_id` and `company_name` now appear in:
  - `GET /api/documents`
  - `GET /api/documents/<id>`
  - Folder documents listing
  - Search results

---

## What to Test Now

### 1. Create New Folder with Company
```json
POST /api/folders/create
{
  "name": "Test Folder",
  "department_id": 2,
  "company_id": 1
}
```
**Expected:** Folder created with company_id = 1

### 2. Upload Main Document to That Folder
```json
POST /api/documents/upload
{
  "name": "Main Document",
  "folder_id": <folder_id_from_step_1>,
  "department_id": 2,
  "document_type_id": 1
}
```
**Expected Response includes:**
```json
{
  "company_id": 1,
  "company_name": "Your Company Name"
}
```

### 3. Upload Secondary Document to Same Folder
```json
POST /api/documents/upload
{
  "name": "Sub Document",
  "folder_id": <folder_id_from_step_1>,
  "parent_document_id": <main_doc_id>,
  "folder_role": "sub"
}
```
**Expected Response includes:**
```json
{
  "company_id": 1,
  "company_name": "Your Company Name"
}
```

### 4. List Documents with Company Filter
```json
POST /api/documents
{
  "company_id": 1
}
```
**Expected:** Returns all documents from folders with company_id = 1

---

## Files Modified

1. ✓ `addons/nbs_archive/models/nbs_document.py`
   - Modified `company_id` field definition
   - Enhanced `create()` method
   - Enhanced `write()` method
   - Added `_compute_company_id()` method

2. ✓ `addons/nbs_archive/controllers/folder_controller.py`
   - Added `company_id` to update allowed fields

3. ✓ `addons/nbs_archive/controllers/relations_controller.py`
   - Added `company_id` parameter to create_folder

4. ✓ `addons/nbs_archive/controllers/companies_controller.py`
   - Added update_company endpoint
   - Added delete_company endpoint with folder check

5. ✓ `addons/nbs_archive/FE_MESSAGE_BRAND_COMPANY.md`
   - Complete FE integration guide

---

## Module Updated
- Module: `nbs_archive`
- Updated: Yes
- Odoo Restarted: Yes
- Status: **READY FOR TESTING** ✅

---

## Support Scripts Created

1. **recompute_document_company.py** - Recomputes company_id for all documents
2. **test_company_computation.py** - Tests company_id computation
3. **test_document_company_create.py** - Tests document creation with company_id

Run any time with: `./venv/bin/python <script_name>.py`
