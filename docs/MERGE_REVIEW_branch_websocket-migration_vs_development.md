# Merge review: `branch_websocket-migration` vs `development`

**Generated:** 2026-04-27  
**Purpose:** Single inventory of everything that differs from the `development` branch before merging.

---

## 1. Git state (important)

| Item | Value |
|------|--------|
| **Current branch** | `branch_websocket-migration` |
| **Local `development` tip** | `aba906d04` — *fix(crm): allow image/* for chat, CRM uploads, and stories* |
| **Relationship to `development`** | `HEAD` and `development` point to the **same commit**. There is **no commit gap** between the two branches in this workspace. |

**What is “different from development” here**

All work listed in this document is **uncommitted**: **modified tracked files** plus **untracked files**. It is **not** yet expressed as commits on top of `development`.

**Before merging into `development`**

1. Stage and commit the intended source changes (addons, configs you want shared).  
2. Add or extend `.gitignore` for sandbox filestores, logs, and session blobs if those should never be committed.  
3. Then merge `branch_websocket-migration` into `development` (or open a PR) as your process requires.

---

## 2. Database and Odoo configuration names

Configuration in the repo uses **multiple database names** depending on environment:

| Config file | `db_name` | Notes |
|-------------|-----------|--------|
| `odoo_simple.conf` | `nbs_lugalai` | Example / deployment-style config in repo (`data_dir` path in file may point to another machine). |
| `odoo_local.conf` | `lugal_local` | Local dev; `http_port` 8070, `data_dir` → `filestore_local`. |
| `odoo_ws.conf` (untracked) | `lugal_ws_sandbox` | **WebSocket migration sandbox only** — `http_port` 8075, `gevent_port` 8076, `data_dir` → `filestore_ws`. |

**Branch work** for WebSocket and realtime testing is intended against **`lugal_ws_sandbox`** per `odoo_ws.conf`, not `lugal_local`.

---

## 3. Diff statistics (tracked files only)

Command: `git diff` (working tree vs last commit).

| Metric | Value |
|--------|--------|
| **Files changed** | 21 |
| **Lines** | +2,242 / −186 |

---

## 4. Modified addons and files (tracked)

### 4.1 `lugal_auth`

| File | Summary of changes |
|------|-------------------|
| `controllers/auth_controller.py` | **WebSocket session cookie** on login/refresh via `_attach_ws_session` (Odoo `session_id` + `Set-Cookie`). **`remember_me`** → longer refresh token. **`ws_session_id`** in JSON response. **Forgot/reset password** JSON-RPC routes. Triggers **`lugal.email.idle.watcher`** after successful login so IMAP IDLE starts sooner. |
| `models/lugal_jwt_service.py` | JWT service updates aligned with `remember_me` and token behavior. |

### 4.2 `lugal_crm`

| File | Summary of changes |
|------|-------------------|
| `controllers/crm_notifications_controller.py` | Adjustments for notifications in the WS / realtime context. |
| `controllers/supply_chat_controller.py` | Large update: **bus/WebSocket-oriented** messaging — dual publish to `supply_chat.<id>` and `supply_user.<uid>` for new messages, **resubscribe** signaling for new conversations, **web push** hooks for chat, Riyadh timezone helpers, attachment URL usage, etc. |
| `controllers/supply_controller.py` | Supply API adjustments (related to above work). |
| `controllers/supply_stories_controller.py` | Stories flow updates (bus / realtime / uploads). |
| `controllers/upload_controller.py` | Upload handling tweaks (e.g. image types / URLs). |
| `controllers/user_controller.py` | New endpoint **`POST /api/crm/users/me/update`** — authenticated user can update profile, partner fields, **`avatar_128`** / `image_128`. |
| `controllers/workforce_controller.py` | Workforce-related API expansion. |
| `models/crm_supply_conversation.py` | Model fields/logic for conversations. |
| `models/crm_supply_message.py` | Message model updates. |
| `models/crm_supply_story.py` | Story model updates. |

### 4.3 `lugal_email`

| File | Summary of changes |
|------|-------------------|
| `controllers/crm_email_controller.py` | CRM email API changes (WS / realtime). |
| `controllers/email_controller.py` | Substantial email controller changes (sync, bus, APIs). |
| `controllers/settings_email_controller.py` | Settings API adjustments. |
| `data/cron.xml` | Cron scheduling for IDLE supervision / sync. |
| `models/__init__.py` | Imports new model(s). |
| `models/email_account.py` | **IMAP IDLE integration** — `create` → schedule IDLE start, `action_test_connection` triggers supervisor, `_schedule_idle_start`, sync/IDLE hooks. |
| `models/email_message.py` | Message model hooks (e.g. bus / WS-related). |
| `security/ir.model.access.csv` | Access rules for new models. |

### 4.4 Repository config (tracked)

| File | Summary of changes |
|------|-------------------|
| `odoo_local.conf` | **`limit_upload`** increased from **100 MB** to **1 GB**. |

---

## 5. New tracked content expected after you `git add` (currently untracked)

### 5.1 New Odoo addon: `lugal_ws_migration`

**Role:** WebSocket migration layer (manifest states: sandbox / migration branch; session bridge, bus overrides, push registration).

**Files (12):**

- `__init__.py`, `__manifest__.py`
- `controllers/__init__.py`, `controllers/ws_session.py`, `controllers/push_controller.py`
- `models/__init__.py`, `models/lugal_ir_http.py`, `models/lugal_ir_websocket.py`, `models/lugal_email_ws.py`, `models/lugal_push_notification.py`
- `data/ws_config.xml`
- `security/ir.model.access.csv`

**Notable HTTP routes (from code):**

- `POST /api/crm/ws/session` — JWT → Odoo session cookie for WebSocket.
- `GET /api/crm/ws/config` — feature flag for WebSocket vs long-poll.
- `GET /api/crm/push/vapid-public-key`
- `POST /api/crm/push/subscribe`, `POST /api/crm/push/unsubscribe` (jsonrpc)

**Model behavior highlights:**

- `ir.websocket` inheritance: stale session handling, auto-subscribe supply chat / stories / email channels.
- Push subscription storage and sending (used from supply chat).

### 5.2 New Odoo addon: `lugal_localsend`

**Role:** LocalSend device and transfer tracking; REST-style controller for registration and transfers.

**Files (12):** standard module layout — `controllers/localsend_controller.py`, `models/localsend_device.py`, `models/localsend_transfer.py`, views, security, manifest.

### 5.3 New email module file: `lugal_email/models/email_idle_watcher.py`

**Role:** **IMAP IDLE** watcher — deduplicated connections per credential group, advisory locking across workers, backoff, supervisor cron integration, watchdog for new accounts (see file docstring).

---

## 6. Untracked documentation and frontend prompts (root and `44/`)

These are **markdown / Vite** artifacts; include in the merge only if your team wants them in `development`.

**FE / WebSocket / realtime prompts and guides**

- `FE_EMAIL_WS_PROMPT.md`
- `FE_FINAL_WS_FIX.md`
- `FE_LIVE_CONNECTION_FINAL_PROMPT.md`
- `FE_LIVE_CONNECTION_FIXES.md`
- `FE_PASSWORD_MANAGEMENT_PROMPT.md`
- `FE_PUSH_NOTIFICATIONS_PROMPT.md`
- `FE_REALTIME_ON_LOGIN_FIX.md`
- `FE_WEBSOCKET_INTEGRATION_GUIDE.md`
- `FE_WEBSOCKET_URL_FIX_PROMPT.md`
- `FE_WS_DEDUP_FIX.md`
- `FirstConnectionWSIssue.md`
- `REALTIME_BUS_AND_WEBSOCKET_MIGRATION.md`
- `WEBSOCKET_COMPLETE_SETUP.md`
- `WS_MIGRATION_CHANGES.md`
- `WS_MIGRATION_PLAN.md`

**Other docs**

- `LOCALSEND_API.md`
- `backend_watch.md`

**Odd path**

- `44/vite.config.ts` — likely accidental path; confirm before committing.

---

## 7. Untracked sandbox / runtime artifacts (usually exclude from merge)

| Path / file | Description |
|-------------|-------------|
| `odoo_ws.conf` | Sandbox Odoo config (`lugal_ws_sandbox`, ports 8075/8076). **Often committed** as team documentation; may contain machine-specific paths — review before add. |
| `filestore_ws/` | Odoo **`data_dir`** for WS sandbox — **binary filestore + sessions** (~257 files under `filestore_ws` in this workspace). **Do not merge** into `development` unless you intentionally version a demo filestore (rare). |
| `odoo_ws_nohup.out` | Process log — **do not commit**; add to `.gitignore`. |

---

## 8. Merge checklist

- [ ] Decide **database policy**: production/staging DB names vs `lugal_ws_sandbox`-only modules (`lugal_ws_migration` manifest warns: sandbox only).  
- [ ] **Commit** addon code: `lugal_ws_migration`, `lugal_localsend`, `email_idle_watcher.py`, and all intentional `lugal_*` edits.  
- [ ] **Ignore or delete** `filestore_ws/` contents and `odoo_ws_nohup.out` from version control.  
- [ ] Optionally commit **`odoo_ws.conf`** after stripping secrets / normalizing paths.  
- [ ] Decide whether **markdown prompts** belong in the main repo or an internal wiki.  
- [ ] Run Odoo **`-u`** updates on target DBs for changed modules and new addons.  
- [ ] Confirm **`odoo_local.conf`** 1 GB upload limit is desired on all environments that use that file.

---

## 9. Remote note

`git fetch origin development` failed in this environment with **SSH permission denied**; the review used **local** `development` at `aba906d04`. Before merging, run `git fetch` where you have credentials and confirm **origin/development** has not moved ahead.

---

*End of merge review.*
