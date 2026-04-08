# NBS CRM — Delete Customer API (for Frontend)

**Endpoint:** `POST /api/crm/customers/<customer_id>/delete`  
**Auth:** Required — `Authorization: Bearer <jwt_token>`  
**Behavior:** Soft-delete (sets `is_deleted = true`, `active = false`). Record remains in DB for audit.

---

## Request

| Item    | Value |
|---------|--------|
| Method  | `POST` |
| URL     | `{baseUrl}/api/crm/customers/{customer_id}/delete` |
| Headers | `Content-Type: application/json`<br>`Authorization: Bearer <jwt>` |

**Body (JSON-RPC 2.0):**  
No body fields required beyond standard JSON-RPC. `customer_id` is in the path.

### Example request payload

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    "db": "lugal_db"
  }
}
```

*Note: If your client adds `db` automatically, an empty params object `{}` is enough.*

### cURL example

```bash
curl -X POST "http://localhost:8070/api/crm/customers/42/delete" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"jsonrpc":"2.0","id":1,"method":"call","params":{"db":"lugal_db"}}'
```

---

## Response type

### Success (200)

**Body:** JSON-RPC envelope with `result.success === true`. No `data` field.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true
  }
}
```

**TypeScript (FE):**

```ts
interface DeleteCustomerSuccess {
  success: true;
  data?: undefined;
}

interface ApiResult<T = void> {
  success: boolean;
  data?: T;
  error?: string;
}

// Usage: Promise<ApiResult<void>>
const result = await deleteCustomer(customerId);
if (result.success) {
  // Remove from list / redirect / show toast
} else {
  console.error(result.error);
}
```

### Error — Unauthorized (200 + result.success: false)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": false,
    "error": "Unauthorized"
  }
}
```

### Error — Customer not found (200 + result.success: false)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": false,
    "error": "Customer not found"
  }
}
```

---

## Summary for FE

| Aspect        | Value |
|---------------|--------|
| Method        | `POST` |
| Path          | `/api/crm/customers/:id/delete` |
| Path param    | `id` (number) — customer ID |
| Body params   | None (optional `db` if your client sends it) |
| Success body  | `{ success: true }` — no `data` |
| Error body    | `{ success: false, error: string }` |
| Auth          | Bearer JWT required |

Frontend service (already integrated):

```ts
// customerService.deleteCustomer(id: number) => Promise<ApiResult<DeleteCustomerResponse>>
const result = await customerService.deleteCustomer(42);
if (result.success) {
  // success
} else {
  // result.error
}
```
