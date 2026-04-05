# System Improvement Plan — Lugal AI / NBS CRM

> **Date:** 2026-03-30  
> **Scope:** Full-stack (Backend, Frontend, Infrastructure, Security, Performance)

---

## Executive Summary

The system is functional and production-ready at its core. However, several architectural gaps reduce reliability, developer productivity, and user experience. This plan identifies those gaps and defines a prioritized roadmap with concrete deliverables.

---

## 1. API Architecture & Consistency

### Current Problems

| Problem | Impact |
|---------|--------|
| Two protocols co-exist: JSON-RPC (CRM) and REST (POS) | Frontend must maintain two different request wrappers |
| No API versioning in CRM routes (`/api/crm/...` with no `/v1/`) | Breaking changes affect all clients simultaneously |
| No standardized pagination across all list endpoints | Some endpoints return `total + items`, others return just `items` |
| No request ID / correlation ID in responses | Impossible to trace a specific request through logs |
| POS uses HTTP verbs (GET/PUT/POST) but CRM uses POST-only JSON-RPC | Confuses frontend developers |

### Proposed Improvements

**1.1 — Unified API Gateway Layer**

Introduce a thin gateway module (`lugal_api_gateway`) that:
- Normalizes all responses into a single envelope: `{ success, data, meta, error }`
- Adds `request_id` (UUID) to every response for traceability
- Enforces pagination contract: `{ items, total, offset, limit }`

**1.2 — Add Version Prefix to CRM Routes**

```
Current:  POST /api/crm/customers/list
Target:   POST /api/crm/v1/customers/list
```

Allows `/v2/` routes to be introduced without breaking existing clients.

**1.3 — Standardize Pagination**

All list endpoints should accept:
```json
{ "offset": 0, "limit": 50 }
```
And return:
```json
{ "items": [...], "total": 500, "offset": 0, "limit": 50 }
```

---

## 2. Authentication & Security

### Current Problems

| Problem | Impact |
|---------|--------|
| JWT secrets stored in `ir.config_parameter` (database) | Secret exposure if DB is compromised |
| No token rotation on sensitive operations (password change, etc.) | Stolen token remains valid after password change |
| Rate limiting is in-memory per worker | 9 workers = 9× the allowed attempts before lockout |
| No audit trail on failed login attempts | Cannot detect brute-force attacks |
| Admin API has no 2FA requirement | High-privilege actions require only a JWT |

### Proposed Improvements

**2.1 — Shared Rate Limiter (Redis)**

Move rate limiting state from per-worker in-memory to Redis:
```
Current:  9 workers × 10 attempts = 90 actual attempts before lockout
Target:   1 shared Redis counter = exactly 10 attempts before lockout
```

**2.2 — Token Invalidation on Password Change**

When a user changes their password:
- Blacklist all existing refresh tokens for that user
- Force re-login

**2.3 — Audit Log for Auth Events**

Add to `lugal.crm.audit.log`:
- `login_success` with IP and device
- `login_failure` with IP (for brute-force detection)
- `password_changed`
- `token_refreshed`

**2.4 — Admin Action Confirmation**

For admin-only actions (system param update, SAP test), require a short-lived "admin confirmation token" that expires in 5 minutes — similar to `sudo` mode in GitHub.

---

## 3. Real-Time & WebSocket

### Current Problem

The system has no real-time push capability. The frontend must **poll** for:
- New tickets / messages
- Shift check-in/out status
- KPI changes
- Notification alerts

This creates unnecessary server load and delays.

### Proposed Improvements

**3.1 — Odoo Bus Integration (Short Term)**

Use Odoo's built-in `bus.bus` (longpolling on port 8072) to push:
- New message notifications
- Ticket status changes
- Agent online/offline status

**3.2 — WebSocket Events (Long Term)**

Define a structured event schema:
```typescript
interface BusEvent {
  type: 'new_ticket' | 'new_message' | 'kpi_update' | 'shift_update';
  payload: unknown;
  user_id: number;
  branch_id: number | null;
  timestamp: string;
}
```

Frontend subscribes once on login and processes events reactively.

---

## 4. Data Synchronization (SAP Integration)

### Current Problems

| Problem | Impact |
|---------|--------|
| SAP sync runs as a cron job (polling) | Up to 5-minute delay between SAP and Odoo |
| No retry queue for failed SAP operations | A network glitch permanently loses a sync event |
| Exchange rate is synced manually or via cron | Orders can be created with wrong exchange rate |
| No status dashboard for SAP sync health | Admins cannot see what is failing without reading logs |

### Proposed Improvements

**4.1 — SAP Sync Queue**

Introduce a `sap.sync.queue` model:
```
Fields: model, record_id, operation (create/update/delete), status (pending/retry/failed/done), attempt_count, last_error
```

Every SAP write is enqueued rather than called inline. A background worker processes the queue with exponential backoff.

**4.2 — SAP Health Dashboard API**

```
GET /api/crm/admin/integrations/sap/health
```
Returns:
```json
{
  "queue_pending":     12,
  "queue_failed":       3,
  "last_sync_success": "2026-03-30T10:45:00",
  "last_sync_error":   null,
  "today_synced":     450,
  "today_failed":       2
}
```

**4.3 — Webhook from SAP (Long Term)**

Configure SAP B1 Service Layer to POST change notifications to Odoo instead of Odoo polling SAP. This reduces sync delay from minutes to seconds.

---

## 5. Performance & Scalability

### Current Problems

| Problem | Impact |
|---------|--------|
| Product list API loads all 6,000+ products in one query | Slow initial POS load |
| No caching on pricelists / product data | Same pricelist computed for every request |
| No database query optimization on analytics endpoints | Heavy GROUP BY queries on large tables |
| Workers set to 9 but no load balancer in front | Single point of failure; no graceful zero-downtime restart |

### Proposed Improvements

**5.1 — Redis Caching for Hot Data**

Cache frequently read, rarely changed data:

| Data | TTL |
|------|-----|
| Active pricelists | 5 minutes |
| Product category tree | 10 minutes |
| Branch list | 30 minutes |
| Invoice types | 1 hour |
| System params | 5 minutes |

**5.2 — Database Indexes**

Add missing indexes on high-traffic queries:
```sql
-- Ticket queries
CREATE INDEX IF NOT EXISTS idx_crm_ticket_status_branch ON lugal_crm_ticket(status, branch_id);
CREATE INDEX IF NOT EXISTS idx_crm_ticket_assigned_user ON lugal_crm_ticket(assigned_user_id, status);

-- KPI queries
CREATE INDEX IF NOT EXISTS idx_crm_employee_kpi_user_date ON lugal_crm_employee_kpi(user_id, date);

-- Audit logs
CREATE INDEX IF NOT EXISTS idx_crm_audit_log_user_date ON lugal_crm_audit_log(user_id, create_date);
```

**5.3 — Nginx + Upstream Load Balancing**

Place Nginx in front of Odoo to:
- Distribute requests across workers
- Enable zero-downtime restarts (rolling worker recycling)
- Serve static assets directly (skip Odoo entirely for JS/CSS)
- Add gzip compression on API responses

**5.4 — Lazy Loading in POS API**

Add `has_price_only` filter as default (skip products with `price = 0`). Add cursor-based pagination to replace offset-based for large datasets:
```
GET /api/pos_perfume/v1/products?after_id=500&limit=50
```
This performs dramatically better on large tables than `OFFSET 500`.

---

## 6. Frontend Architecture

### Current Problems

| Problem | Impact |
|---------|--------|
| Settings stored only in Zustand (fixed by new API) | ✅ Fixed |
| No optimistic updates pattern for settings | UI appears slow — waits for server before updating |
| No skeleton loading states on settings pages | Poor perceived performance |
| Invoice types hardcoded in frontend fallback | Frontend and backend can get out of sync |
| API error messages shown raw to users | Bad UX, sometimes exposes internal details |

### Proposed Improvements

**6.1 — Optimistic Updates**

Settings changes should update the UI immediately, then sync to backend asynchronously:
```typescript
const updateTheme = (newTheme) => {
  // Update UI immediately
  setTheme(newTheme);
  // Sync in background
  settingsApi.updatePreferences({ theme: newTheme }).catch(() => {
    // Rollback on failure
    setTheme(previousTheme);
    toast.error('Failed to save theme. Changes reverted.');
  });
};
```

**6.2 — TanStack Query for Settings**

Use TanStack Query to manage settings data lifecycle:
```typescript
const { data: preferences } = useQuery({
  queryKey:    ['user-preferences'],
  queryFn:     () => settingsApi.getPreferences(token),
  staleTime:   5 * 60 * 1000,  // 5 min
  gcTime:      30 * 60 * 1000, // 30 min
  refetchOnWindowFocus: false,
});
```

**6.3 — Error Message Sanitization**

Map backend error strings to user-friendly Arabic/English messages:
```typescript
const ERROR_MAP: Record<string, string> = {
  'Unauthorized':           'انتهت جلسة العمل، يرجى تسجيل الدخول',
  'Admin role required':    'هذه الصفحة للمسؤولين فقط',
  'KPI rule not found':     'القاعدة غير موجودة',
};

function friendlyError(raw: string): string {
  return ERROR_MAP[raw] ?? 'حدث خطأ، يرجى المحاولة لاحقاً';
}
```

---

## 7. Observability & Monitoring

### Current Problems

- No structured logging (logs are plain text in `odoo_local.log`)
- No metrics collection (CPU, memory, request latency, error rate)
- No alerting when SAP integration fails
- No uptime monitoring
- Cannot correlate a user complaint with a specific log entry

### Proposed Improvements

**7.1 — Structured Logging**

Adopt JSON logging format:
```json
{
  "timestamp": "2026-03-30T10:45:00Z",
  "level": "ERROR",
  "module": "pos_perfume",
  "request_id": "abc123",
  "user_id": 5,
  "message": "Pricelist resolution failed",
  "error": "NoneType object has no attribute id"
}
```

**7.2 — Prometheus + Grafana**

Expose a `/metrics` endpoint for:
- Request rate and latency (P50, P95, P99)
- Error rate per endpoint
- SAP queue depth
- Active worker count

**7.3 — Automated Alerts**

Set up alerts for:
- SAP connection status changes to `error`
- Error rate > 5% in any 5-minute window
- Server memory > 80%
- Any `500` response to a known API endpoint

---

## 8. Developer Experience

### Current Problems

- No automated API tests — every change must be manually tested
- No local development seed data — fresh installs are empty
- No Postman/Insomnia collection for the API
- No CI/CD pipeline — deployments are manual

### Proposed Improvements

**8.1 — API Test Suite**

Write automated tests for every endpoint using Python's `requests` library + pytest:
```python
def test_preferences_round_trip(auth_token):
    r = crm_post('/api/crm/users/me/preferences', {}, auth_token)
    assert r['success'] is True
    assert 'theme' in r['data']
    
    r2 = crm_post('/api/crm/users/me/preferences/update',
                  {'theme': [{'id': 'theme-mode', 'type': 'select', 'value': 'light'}]},
                  auth_token)
    assert r2['success'] is True
```

**8.2 — Postman Collection**

Export a `Lugal_API.postman_collection.json` with all endpoints, example requests, and pre-request scripts for automatic token injection.

**8.3 — CI/CD Pipeline (GitHub Actions)**

```yaml
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run API Tests
        run: pytest tests/api/ -v
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: ./scripts/deploy.sh
```

---

## Implementation Priority Matrix

| # | Improvement | Impact | Effort | Priority |
|---|-------------|--------|--------|----------|
| 1 | Redis shared rate limiter | 🔴 High (Security) | Medium | **P0** |
| 2 | SAP sync queue with retry | 🔴 High (Reliability) | High | **P0** |
| 3 | Database indexes for hot queries | 🟠 High (Performance) | Low | **P1** |
| 4 | Nginx load balancer + zero-downtime | 🟠 High (Reliability) | Medium | **P1** |
| 5 | Redis caching for pricelists/branches | 🟡 Medium (Performance) | Medium | **P1** |
| 6 | Odoo Bus real-time notifications | 🟠 High (UX) | Medium | **P1** |
| 7 | Optimistic updates on frontend | 🟡 Medium (UX) | Low | **P2** |
| 8 | API versioning (`/v1/` prefix) | 🟡 Medium (Maintainability) | Low | **P2** |
| 9 | Structured logging + Prometheus | 🟡 Medium (Observability) | Medium | **P2** |
| 10 | Automated API test suite | 🟡 Medium (Quality) | High | **P2** |
| 11 | WebSocket push events | 🟢 High (UX) | High | **P3** |
| 12 | Cursor-based pagination | 🟢 Medium (Performance) | Medium | **P3** |
| 13 | SAP webhook integration | 🟢 High (Performance) | High | **P3** |
| 14 | CI/CD pipeline | 🟡 Medium (DevEx) | Medium | **P3** |
| 15 | Admin 2FA confirmation | 🟢 Medium (Security) | High | **P3** |

---

## Recommended Next Sprint (P0 + P1)

1. ✅ **Add database indexes** — 1 day, zero risk, immediate performance gain
2. ✅ **Move rate limiter to shared DB table** (use PostgreSQL advisory locks as Redis alternative if Redis not available) — 2 days
3. ✅ **Implement SAP sync retry queue** — 3 days, prevents data loss
4. ✅ **Set up Nginx reverse proxy** — 1 day, enables zero-downtime restarts
5. ✅ **Integrate Odoo Bus for new message/ticket notifications** — 3 days, major UX improvement

**Estimated sprint: 10 working days, 2 engineers**
