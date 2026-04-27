# FE: Brand/Company support for folders and filtering

Hi,

Backend now supports **Company/Brand** per folder. One company can have multiple folders; you can filter folders and documents by company. Here's what you need to integrate.

---

## 1. Companies (brands) list

- **Endpoint:** `POST /api/companies`
- **Params:** `search` (optional), `limit` (optional, default 100)
- **Response:** `{ success, data: [{ id, name, phone, email, vat, street, city, country_id, country_name }], count }`

Use this to populate a company/brand dropdown when creating/editing folders and for filter dropdowns.

**List countries** (for autocomplete/dropdown)  
- **Endpoint:** `POST /api/countries`  
- **Params:** `search` (optional), `limit` (optional, default 100)  
- **Response:** `{ success, data: [{ id, name, code, phone_code }], count }`
- **Example:** `search: "iraq"` returns `[{ id: 106, name: "Iraq", code: "IQ", phone_code: 964 }]`

Use this for country autocomplete when creating/editing companies. Users can type country name and select from list.

**Create company** (managers only)  
- **Endpoint:** `POST /api/companies/create`  
- **Body (JSON):** 
  - `name` (required)
  - `phone`, `email`, `vat`, `street`, `city`, `website` (optional)
  - `country_id` (optional) - Country ID
  - `country_name` (optional) - Country name as string (e.g., "United States", "Saudi Arabia")
    - If country doesn't exist, it will be created automatically
    - Use either `country_id` OR `country_name`, not both
- **Response:** `{ success, message, data: { id, name } }`

**Update company** (managers only)  
- **Endpoint:** `POST /api/companies/<company_id>/update`  
- **Body (JSON):** `name`, `phone`, `email`, `vat`, `street`, `city`, `country_id`, `country_name`, `website`
  - Use either `country_id` OR `country_name`
  - If `country_name` is provided and country doesn't exist, it will be created automatically
- **Response:** `{ success, message, data: { id, name } }`

**Delete company** (managers only)  
- **Endpoint:** `DELETE /api/companies/<company_id>`  
- **Rule:** Deleting is **not allowed** if the company has any folders. The API returns:
  - **400** with `success: false`, `code: 'COMPANY_HAS_FOLDERS'`, `folder_count`, and `message_ar`: "لا يمكن حذف الشركة لوجود فولدرات مرتبطة بها. قم بإزالة أو نقل الفولدرات أولاً."
- If the company has no folders, it is archived (soft delete). Response: `{ success, message, data: { id } }`.

---

## 2. Folders - new field and filter

**List folders**  
- **Endpoint:** `POST /api/folders`
- **New optional param:** `company_id` (int) - filter folders by company.
- **Response:** Each folder now includes:
  - `company_id`: number or `null`
  - `company_name`: string or `null`
  - `created_at`: datetime (when folder was created)
  - `last_modified`: datetime (last modification to folder, documents, or notes)

**Create folder**  
- **Endpoint:** `POST /api/folders/create` (jsonrpc)
- **New optional param:** `company_id` (int) - set the folder's company/brand.

**Update folder**  
- **Endpoint:** `POST /api/folders/<folder_id>/update` (jsonrpc)
- **New optional param:** `company_id` (int) - change the folder's company/brand.

**Get folder (single)**  
- Response for a folder now includes `company_id` and `company_name`.

---

## 3. Documents - filter by company

Documents get their `company_id` automatically from their folder. Both main documents and secondary documents (sub-documents/attachments) inherit the company from the folder they belong to.

**How it works:**
- When a folder has a `company_id`, **all documents** in that folder (main and secondary) will automatically have the same `company_id`.
- When you update a folder's `company_id`, all documents in that folder will be updated automatically.
- If a folder has no `company_id`, its documents will have `company_id: null`.

**List documents**  
- **Endpoint:** `POST /api/documents` (or your current "get documents" endpoint).
- **New optional param:** `company_id` (int) - filter documents by the company of their folder.
- **Response:** Each document now includes:
  - `company_id`: number or `null`
  - `company_name`: string or `null`

---

## 4. Bulk Upload - new parameter

**Start bulk upload job**  
- **Endpoint:** `POST /api/documents/bulk-upload/start`
- **New optional param:** `company_id` (int) - Company for auto-created folders when using `create_folder_per_file: true`
- **How it works:** When `create_folder_per_file: true` and `company_id` is provided, all auto-created folders will have this company_id, and all documents will inherit it.

**Example:**
```json
{
  "department_id": 8,
  "document_type_id": 10,
  "create_folder_per_file": true,
  "company_id": 1,  // NEW! Auto-created folders will have this company
  "confidentiality_level": "internal"
}
```

**Result:** Each uploaded file gets its own folder with `company_id: 1`, and the document inherits `company_id: 1`.

---

## 5. UI changes to implement

1. **Folder create/edit**
   - Add optional "Company/Brand" dropdown; options from `POST /api/companies`. Send `company_id` when creating/updating a folder.

2. **Folder list**
   - Add optional filter by company (dropdown or selector); call list folders with `company_id` when a company is selected.
   - Show `company_name` in folder rows/cards if present.

3. **Document list**
   - Add optional filter by company; call list documents with `company_id` when selected.
   - Optionally show `company_name` on document rows (from folder's company).

4. **Relations / tree**
   - If you use the relations API for folders, use the new `company_id` filter and the `company_id` / `company_name` in the response the same way as above.

5. **Companies management** (optional)
   - **Add:** Form calling `POST /api/companies/create` with name and optional fields.
   - **Edit:** Form calling `POST /api/companies/<id>/update` with allowed fields.
   - **Delete:** Call `DELETE /api/companies/<id>`. If the response is 400 with `code: 'COMPANY_HAS_FOLDERS'`, show `message_ar` (or a friendly message) and do not remove the company from the list.

No other existing APIs were changed; only these new parameters and response fields were added.

Thanks.
