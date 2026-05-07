# Supply container reminder — Frontend integration

Guide for the SPA to **create**, **read**, **update**, and **delete** container reminders. Use the same **base URL** and **JWT** as the rest of the Supply CRM app.

---

## 1. Authentication

| Header | Value |
|--------|--------|
| `Authorization` | `Bearer <access_token>` |

Same token as other supply chain routes (`POST /api/crm/supply/po/list`, vendors, shipments, etc.).

---

## 2. Create or update reminder (JSON-RPC)

**POST** `/api/crm/supply/containers/{container_id}/set_reminder`

- **Routing:** Odoo **JSON-RPC** (`type='jsonrpc'`), not plain REST JSON.
- **Path:** replace `{container_id}` with the numeric `lugal.supply.container` id.

### JSON-RPC body

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "reminder_date": "2026-05-10 14:00:00",
    "reminder_note": "Follow up with vendor"
  },
  "id": 1
}
```

| Field | Required | Notes |
|-------|----------|--------|
| `reminder_date` | Yes for **new** reminders | String: `YYYY-MM-DD HH:MM:SS`, ISO with `T`, or date-only `YYYY-MM-DD`. Invalid format → error. |
| `reminder_note` | No | String; omit or use `""` for empty. |

### Behaviour

- **No existing reminder:** `reminder_date` must be provided and valid.
- **Reminder already exists:** you can send both fields to replace date and note. If `reminder_date` is omitted or empty but a reminder **already exists**, only `reminder_note` is updated (date kept). If there is **no** reminder yet and `reminder_date` is missing → error: `reminder_date is required`.

### Success (`result`)

```json
{
  "success": true,
  "data": {}
}
```

`data` is the **full container** object (same family as other container APIs), including:

| Key | Type | Notes |
|-----|------|--------|
| `reminder_date` | string \| null | `YYYY-MM-DD HH:MM:SS` when set |
| `reminder_note` | string | Empty string when cleared |

### Errors

| Shape | Typical cases |
|-------|----------------|
| `{ "success": false, "error": "Unauthorized", "data": null }` | Missing or invalid JWT |
| `{ "success": false, "error": "Container not found", "data": null }` | Bad id or soft-deleted container |
| `{ "success": false, "error": "reminder_date is required", "data": null }` | New reminder without date |
| `{ "success": false, "error": "Invalid reminder_date; use ISO or YYYY-MM-DD HH:MM:SS", "data": null }` | Unparseable date |

---

## 3. Get reminder (HTTP)

**GET** `/api/crm/supply/containers/{container_id}/reminder`

- Plain **HTTP** JSON response (not JSON-RPC).
- Use for **edit modal** / view: load current `reminder_date` and `reminder_note`.

### Success (`200`)

```json
{
  "success": true,
  "data": {
    "container_id": 17,
    "reminder_date": "2026-05-10 14:00:00",
    "reminder_note": "Follow up with vendor"
  }
}
```

When nothing is configured: `reminder_date` is `null`, `reminder_note` is `""`.

### Errors

| HTTP | Body |
|------|------|
| `401` | `{ "success": false, "error": "Unauthorized" }` |
| `404` | `{ "success": false, "error": "Container not found", "data": null }` |
| `501` | Reminder fields not available (module not upgraded) |

### CORS / preflight

`OPTIONS` is supported for browser clients; responses include permissive CORS headers.

---

## 4. Delete reminder (HTTP)

**DELETE** `/api/crm/supply/containers/{container_id}/reminder`

- Clears `reminder_date` and sets `reminder_note` to `""`.

### Success (`200`)

```json
{
  "success": true,
  "message": "Reminder deleted successfully"
}
```

### Errors

Same pattern as GET (`401`, `404`, `501`).

After delete, refresh the reminder section in the UI (or refetch container/shipment payloads — see below).

---

## 5. Reminder fields on other responses

Container and shipment payloads returned elsewhere (lists, detail, actions) also include:

- `reminder_date`
- `reminder_note`

You can sync the UI after save/delete by refetching those endpoints if you do not call GET `/reminder` again.

---

## 6. Suggested FE flow

| User action | Call |
|-------------|------|
| Open “add / edit reminder” | **GET** `.../reminder` → bind form |
| Save | **JSON-RPC POST** `.../set_reminder` with `reminder_date` + `reminder_note` |
| Delete | **HTTP DELETE** `.../reminder` → clear local state / refetch |

Store **`container_id`** from the container or shipment row you are editing.

---

## 7. Server requirement

After deploying backend changes, the database must be upgraded so columns exist:

```bash
./odoo-bin -u lugal_crm -d <database_name>
```

---

*End of integration guide.*
