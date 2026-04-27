# Projects & Tasks — Full API Reference

> **Protocol:** JSON-RPC 2.0 over HTTP POST  
> **Auth:** JWT Bearer token — `Authorization: Bearer <token>`  
> **Base URL:** `http(s)://<server>`  
> **All endpoints:** `POST`, `Content-Type: application/json`

---

## How Every Request Works

```json
POST /api/crm/projects/list
Authorization: Bearer eyJhbGc...

{
  "jsonrpc": "2.0",
  "method":  "call",
  "id":      1,
  "params":  { ...endpoint params here... }
}
```

**Success response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": { ... }
  }
}
```

**Error response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": false,
    "error": "Human-readable error message",
    "code": 404
  }
}
```

**`*` = required parameter**

---

## Index

| # | Section | Endpoints |
|---|---------|-----------|
| 1 | [Projects](#1-projects) | 7 endpoints |
| 2 | [Kanban Stages](#2-kanban-stages) | 4 endpoints |
| 3 | [Project Tasks](#3-project-tasks) | 8 endpoints |
| 4 | [Milestones](#4-milestones) | 5 endpoints |
| 5 | [Checklists](#5-checklists) | 6 endpoints |
| 6 | [Project Members](#6-project-members) | 3 endpoints |
| 7 | [Project Tags](#7-project-tags) | 2 endpoints |
| 8 | [Attachments](#8-attachments) | 5 endpoints |

**Total: 40 endpoints**

---

## 1. Projects

### 1.1 List Projects

```
POST /api/crm/projects/list
```

**Parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `search` | string | `""` | Filter by project name (case-insensitive) |
| `my` | bool | `false` | Return only projects where the caller is manager or member |
| `page` | int | `1` | Page number |
| `per_page` | int | `20` | Results per page |

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 5,
    "page": 1,
    "per_page": 20,
    "items": [
      {
        "id": 1,
        "name": "Website Redesign",
        "description": "Revamp the corporate site",
        "color": 3,
        "date_start": "2026-01-01",
        "date_end": "2026-06-30",
        "privacy": "employees",
        "is_favorite": false,
        "manager": {
          "id": 5,
          "name": "Rami Hassan",
          "avatar": "/web/image/res.users/5/avatar_128"
        },
        "stage": { "id": 2, "name": "In Progress" },
        "last_update_status": "on_track",
        "allow_milestones": true,
        "milestone_progress": 40.0,
        "tag_ids": [1, 3],
        "tags": [
          { "id": 1, "name": "Frontend", "color": 2 },
          { "id": 3, "name": "Design",   "color": 5 }
        ],
        "task_count": 18,
        "open_task_count": 12,
        "closed_task_count": 6,
        "task_completion_pct": 33.3,
        "milestone_count": 3,
        "milestone_count_reached": 1
      }
    ]
  }
}
```

---

### 1.2 Create Project

```
POST /api/crm/projects/create
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name`* | string | Yes | Project name |
| `description` | string | No | Rich text / plain description |
| `manager_id` | int | No | User ID of project manager (defaults to caller) |
| `date_start` | string | No | `YYYY-MM-DD` |
| `date_end` | string | No | `YYYY-MM-DD` |
| `privacy` | string | No | `employees` \| `followers` \| `portal` \| `invited_users` (default `employees`) |
| `tag_ids` | int[] | No | List of existing project tag IDs |
| `allow_milestones` | bool | No | Enable milestones feature (default `true`) |

**Response:** Full project object (same shape as list item above, including stats)

**Example request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "name": "Mobile App v2",
    "manager_id": 5,
    "date_start": "2026-04-01",
    "date_end": "2026-09-30",
    "privacy": "employees",
    "allow_milestones": true
  }
}
```

---

### 1.3 Get Project

```
POST /api/crm/projects/<id>/get
```

Returns full project detail including task and milestone statistics.

**Parameters:** _(none — project ID is in the URL)_

**Response:**
```json
{ "success": true, "data": { ...full project object with stats... } }
```

---

### 1.4 Update Project

```
POST /api/crm/projects/<id>/update
```

All fields are optional. Only the fields you send are changed.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | New project name |
| `description` | string | New description |
| `manager_id` | int | New manager user ID |
| `date_start` | string | `YYYY-MM-DD` |
| `date_end` | string | `YYYY-MM-DD` |
| `privacy` | string | Visibility level |
| `color` | int | Color index `0`–`11` |
| `tag_ids` | int[] | **Replaces** all existing tags |
| `allow_milestones` | bool | Toggle milestones |
| `last_update_status` | string | `on_track` \| `at_risk` \| `off_track` \| `on_hold` \| `to_define` \| `done` |

**Response:** Updated project object

---

### 1.5 Archive Project

```
POST /api/crm/projects/<id>/archive
```

Soft-deletes the project (`active = false`). Recoverable from the Odoo backend.

**Response:**
```json
{ "success": true, "data": { "id": 1, "archived": true } }
```

---

### 1.6 Kanban Board

```
POST /api/crm/projects/<id>/kanban
```

Returns the complete Kanban board — every stage (column) with its tasks pre-grouped inside.

**Parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `include_done` | bool | `false` | Include tasks in `1_done` or `1_canceled` state |

**Response:**
```json
{
  "success": true,
  "data": {
    "project": { ...project object... },
    "columns": [
      {
        "stage": { "id": 10, "name": "To Do", "sequence": 1, "color": 0, "fold": false },
        "task_count": 5,
        "tasks": [ ...task objects... ]
      },
      {
        "stage": { "id": 11, "name": "In Progress", "sequence": 2, "color": 2, "fold": false },
        "task_count": 3,
        "tasks": [ ...task objects... ]
      },
      {
        "stage": { "id": 12, "name": "Done", "sequence": 3, "color": 10, "fold": true },
        "task_count": 0,
        "tasks": []
      }
    ]
  }
}
```

> Tasks without a stage appear in an extra `{ "id": null, "name": "No Stage" }` column at the end.

---

### 1.7 Project Stats

```
POST /api/crm/projects/<id>/stats
```

Lightweight counter endpoint — useful for dashboard widgets.

**Response:**
```json
{
  "success": true,
  "data": {
    "project_id": 1,
    "task_count": 18,
    "open_task_count": 12,
    "closed_task_count": 6,
    "task_completion_pct": 33.3,
    "milestone_count": 3,
    "milestone_count_reached": 1,
    "milestone_progress": 33.3,
    "last_update_status": "on_track"
  }
}
```

---

## 2. Kanban Stages

Stages are **shared** Kanban columns. A single stage can be linked to multiple projects.

---

### 2.1 List Stages for a Project

```
POST /api/crm/projects/<project_id>/stages/list
```

Returns stages ordered by `sequence` (left → right on the board).

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      { "id": 10, "name": "To Do",       "sequence": 1, "color": 0,  "fold": false },
      { "id": 11, "name": "In Progress", "sequence": 2, "color": 2,  "fold": false },
      { "id": 12, "name": "Done",        "sequence": 3, "color": 10, "fold": true  }
    ]
  }
}
```

---

### 2.2 Create Stage

```
POST /api/crm/projects/stages/create
```

Creates a new stage and immediately links it to the given project.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id`* | int | Yes | Project to attach this stage to |
| `name`* | string | Yes | Stage label |
| `sequence` | int | No | Sort order (lower = leftmost column) |
| `color` | int | No | Color index `0`–`11` (default `0`) |

**Response:** Stage object

---

### 2.3 Update Stage

```
POST /api/crm/projects/stages/<stage_id>/update
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | New label |
| `sequence` | int | New position |
| `color` | int | New color index |
| `fold` | bool | Collapse column in Kanban view |

**Response:** Updated stage object

---

### 2.4 Delete Stage

```
POST /api/crm/projects/stages/<stage_id>/delete
```

Permanently deletes the stage. Tasks that were in this stage become stageless (they still exist, just without a column).

**Response:**
```json
{ "success": true, "data": { "id": 10, "deleted": true } }
```

---

## 3. Project Tasks

> Route prefix: `/api/crm/projects/ptasks/`  
> `ptasks` prefix avoids naming conflicts with the existing CRM tasks API (`/api/crm/tasks/`).

---

### Task Object — Full Shape

```json
{
  "id": 55,
  "name": "Design homepage mockup",
  "description": "Figma file must be approved first.",
  "project_id": 1,
  "project_name": "Website Redesign",
  "stage": { "id": 11, "name": "In Progress" },
  "priority": "1",
  "priority_label": "High",
  "state": "01_in_progress",
  "state_label": "In Progress",
  "is_closed": false,
  "date_deadline": "2026-04-15",
  "assignees": [
    { "id": 5, "name": "Rami Hassan", "avatar": "/web/image/res.users/5/avatar_128" }
  ],
  "assignee_ids": [5],
  "tag_ids": [7],
  "tags": [{ "id": 7, "name": "Design" }],
  "milestone": { "id": 2, "name": "MVP Launch", "is_reached": false },
  "parent_task": null,
  "subtask_count": 3,
  "closed_subtask_count": 1,
  "color": 0,
  "created_at": "2026-02-01T08:00:00",
  "updated_at": "2026-03-20T14:22:00"
}
```

> `checklists` array is included only when using **Get Task** (`/get`) or **Create Task** response.

---

### 3.1 List Tasks

```
POST /api/crm/projects/ptasks/list
```

**Parameters (all optional):**

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | int | Restrict to a specific project |
| `stage_id` | int | Restrict to a specific Kanban column |
| `assignee_id` | int | Tasks assigned to this user |
| `milestone_id` | int | Tasks linked to this milestone |
| `priority` | string | `"0"` (Normal) or `"1"` (High) |
| `state` | string | e.g. `"01_in_progress"`, `"1_done"` |
| `search` | string | Name filter (case-insensitive contains) |
| `page` | int | Default `1` |
| `per_page` | int | Default `30` |

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 12,
    "page": 1,
    "per_page": 30,
    "items": [ ...task objects... ]
  }
}
```

---

### 3.2 Create Task

```
POST /api/crm/projects/ptasks/create
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name`* | string | Yes | Task title |
| `project_id` | int | No | Parent project |
| `stage_id` | int | No | Initial Kanban stage |
| `assignee_ids` | int[] | No | User IDs (defaults to caller if omitted) |
| `description` | string | No | |
| `priority` | string | No | `"0"` Normal / `"1"` High |
| `date_deadline` | string | No | `YYYY-MM-DD` |
| `milestone_id` | int | No | |
| `parent_id` | int | No | Create as sub-task of this task |
| `tag_ids` | int[] | No | |

**Response:** Full task object including `checklists: []`

---

### 3.3 Get Task

```
POST /api/crm/projects/ptasks/<id>/get
```

Returns full task detail **including checklists**.

**Response:**
```json
{
  "success": true,
  "data": {
    ...task object...,
    "checklists": [
      {
        "id": 10,
        "name": "Acceptance Criteria",
        "description": "",
        "item_count": 3,
        "items": [
          { "id": 31, "name": "Mobile responsive",       "description": "", "sequence": 1 },
          { "id": 32, "name": "Passes accessibility audit", "description": "", "sequence": 2 },
          { "id": 33, "name": "Approved by QA",          "description": "", "sequence": 3 }
        ]
      }
    ]
  }
}
```

---

### 3.4 Update Task

```
POST /api/crm/projects/ptasks/<id>/update
```

All fields are optional.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | |
| `description` | string | |
| `priority` | string | `"0"` or `"1"` |
| `state` | string | See [Task State enum](#task-state) |
| `date_deadline` | string | `YYYY-MM-DD` or `null` to clear |
| `stage_id` | int | Move to a different stage |
| `milestone_id` | int | Link to milestone, or `null` to clear |
| `color` | int | `0`–`11` |
| `tag_ids` | int[] | **Replaces** all existing tags |
| `assignee_ids` | int[] | **Replaces** all assignees |

**Response:** Updated task object

---

### 3.5 Assign Task

```
POST /api/crm/projects/ptasks/<id>/assign
```

Convenience endpoint that **replaces** the full assignee list.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assignee_ids`* | int[] | Yes | New list of user IDs. Pass `[]` to unassign everyone. |

**Response:** Updated task object

---

### 3.6 Move Task to Stage

```
POST /api/crm/projects/ptasks/<id>/move
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stage_id`* | int | Yes | Target stage ID |

**Response:** Updated task object

---

### 3.7 Delete Task

```
POST /api/crm/projects/ptasks/<id>/delete
```

Soft-deletes the task (`active = false`). Recoverable from the Odoo backend.

**Response:**
```json
{ "success": true, "data": { "id": 55, "archived": true } }
```

---

### 3.8 List Subtasks

```
POST /api/crm/projects/ptasks/<id>/subtasks
```

Lists all direct child (sub-)tasks of the given parent task.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | `1` | |
| `per_page` | int | `30` | |

**Response:**
```json
{
  "success": true,
  "data": {
    "parent_task_id": 55,
    "total": 3,
    "items": [ ...task objects... ]
  }
}
```

---

## 4. Milestones

---

### 4.1 List Milestones

```
POST /api/crm/projects/<project_id>/milestones/list
```

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 2,
        "name": "MVP Launch",
        "deadline": "2026-05-01",
        "is_reached": false,
        "reached_date": null,
        "task_count": 8,
        "done_task_count": 3,
        "is_deadline_exceeded": false
      }
    ]
  }
}
```

---

### 4.2 Create Milestone

```
POST /api/crm/projects/<project_id>/milestones/create
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name`* | string | Yes | Milestone name |
| `deadline` | string | No | `YYYY-MM-DD` |

**Response:** Milestone object

---

### 4.3 Update Milestone

```
POST /api/crm/projects/milestones/<id>/update
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | New name |
| `deadline` | string | `YYYY-MM-DD` or `null` to clear |

**Response:** Updated milestone object

---

### 4.4 Toggle Reached

```
POST /api/crm/projects/milestones/<id>/toggle
```

Flips `is_reached` between `true` and `false`. Sets `reached_date` automatically when marking as reached.

**Response:** Updated milestone object

---

### 4.5 Delete Milestone

```
POST /api/crm/projects/milestones/<id>/delete
```

**Response:**
```json
{ "success": true, "data": { "id": 2, "deleted": true } }
```

---

## 5. Checklists

> Powered by the **Cybrosys `projects_task_checklists`** module.  
> If the module is not installed, all checklist endpoints return `500` with a descriptive error.

A **checklist** is a named group of to-do items that lives on a task.  
Example: task "Build login page" → checklist "Acceptance Criteria" → items ["Unit tests pass", "QA approved", "PM sign-off"].

---

### 5.1 List Checklists on Task

```
POST /api/crm/projects/ptasks/<task_id>/checklists/list
```

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": 55,
    "items": [
      {
        "id": 10,
        "name": "Acceptance Criteria",
        "description": "",
        "item_count": 3,
        "items": [
          { "id": 31, "name": "Mobile responsive",          "description": "", "sequence": 1 },
          { "id": 32, "name": "Passes accessibility audit", "description": "", "sequence": 2 },
          { "id": 33, "name": "Approved by QA",             "description": "", "sequence": 3 }
        ]
      }
    ]
  }
}
```

---

### 5.2 Create Checklist on Task

```
POST /api/crm/projects/ptasks/<task_id>/checklists/create
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name`* | string | Yes | Checklist group title |
| `description` | string | No | Optional notes |

**Response:** New checklist object (with `items: []`)

---

### 5.3 Delete Checklist

```
POST /api/crm/projects/checklists/<checklist_id>/delete
```

Permanently deletes the checklist **and all its items**.

**Response:**
```json
{ "success": true, "data": { "id": 10, "deleted": true } }
```

---

### 5.4 Add Item to Checklist

```
POST /api/crm/projects/checklists/<checklist_id>/items/add
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name`* | string | Yes | Item label |
| `description` | string | No | |
| `sequence` | int | No | Sort order (lower = higher in list) |

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 34,
    "name": "Final sign-off",
    "description": "",
    "sequence": 4,
    "checklist_id": 10
  }
}
```

---

### 5.5 Update Checklist Item

```
POST /api/crm/projects/checklists/items/<item_id>/update
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | New label |
| `description` | string | |
| `sequence` | int | New sort position |

**Response:**
```json
{
  "success": true,
  "data": { "id": 34, "name": "Final sign-off (updated)", "description": "", "sequence": 4 }
}
```

---

### 5.6 Delete Checklist Item

```
POST /api/crm/projects/checklists/items/<item_id>/delete
```

**Response:**
```json
{ "success": true, "data": { "id": 34, "deleted": true } }
```

---

## 6. Project Members

Project members are stored as **favourite users** on the project record. The project manager is **not** automatically in this list — check `manager_id` separately.

---

### 6.1 List Members

```
POST /api/crm/projects/<project_id>/members/list
```

**Response:**
```json
{
  "success": true,
  "data": {
    "project_id": 1,
    "manager_id": 5,
    "items": [
      {
        "id": 5,
        "name": "Rami Hassan",
        "email": "rami@example.com",
        "avatar": "/web/image/res.users/5/avatar_128",
        "is_manager": true
      },
      {
        "id": 7,
        "name": "Lina Karim",
        "email": "lina@example.com",
        "avatar": "/web/image/res.users/7/avatar_128",
        "is_manager": false
      }
    ]
  }
}
```

---

### 6.2 Add Members

```
POST /api/crm/projects/<project_id>/members/add
```

Adds users to the member list. **Non-destructive** — existing members are kept.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_ids`* | int[] | Yes | List of user IDs to add |

**Response:**
```json
{ "success": true, "data": { "project_id": 1, "added": [7, 8] } }
```

---

### 6.3 Remove Members

```
POST /api/crm/projects/<project_id>/members/remove
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_ids`* | int[] | Yes | List of user IDs to remove |

**Response:**
```json
{ "success": true, "data": { "project_id": 1, "removed": [7] } }
```

---

## 7. Project Tags

Tags are **global** labels shared across all projects.

---

### 7.1 List Tags

```
POST /api/crm/projects/tags/list
```

| Field | Type | Description |
|-------|------|-------------|
| `search` | string | Filter by name (optional) |

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      { "id": 1, "name": "Frontend", "color": 2 },
      { "id": 2, "name": "Backend",  "color": 3 },
      { "id": 3, "name": "Design",   "color": 5 }
    ]
  }
}
```

---

### 7.2 Create Tag

```
POST /api/crm/projects/tags/create
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name`* | string | Yes | Tag label |
| `color` | int | No | Color index `0`–`11` (default `0`) |

**Response:**
```json
{ "success": true, "data": { "id": 9, "name": "DevOps", "color": 6 } }
```

---

## Enumerations

### Task State

| Value | Label | `is_closed` |
|-------|-------|-------------|
| `01_in_progress` | In Progress | `false` |
| `02_changes_requested` | Changes Requested | `false` |
| `03_approved` | Approved | `false` |
| `04_waiting_normal` | Waiting | `false` |
| `1_done` | Done | `true` |
| `1_canceled` | Canceled | `true` |

### Task Priority

| Value | Label |
|-------|-------|
| `0` | Normal |
| `1` | High |

### Project Status (`last_update_status`)

| Value | Display |
|-------|---------|
| `on_track` | On Track |
| `at_risk` | At Risk |
| `off_track` | Off Track |
| `on_hold` | On Hold |
| `to_define` | Not Set |
| `done` | Done |

### Project Privacy (`privacy_visibility`)

| Value | Who can see it |
|-------|---------------|
| `employees` | All internal users |
| `followers` | Followers + manager only |
| `portal` | Portal users + employees |
| `invited_users` | Only explicitly invited users |

### Color Index (projects, stages, tags)

`0` = Grey · `1` = Red · `2` = Orange · `3` = Yellow · `4` = Light Blue · `5` = Dark Purple  
`6` = Salmon · `7` = Medium Blue · `8` = Light Purple · `9` = Fuchsia · `10` = Green · `11` = Purple

---

## Error Reference

| Error Message | Cause |
|---------------|-------|
| `Unauthorized` | JWT token missing, expired, or invalid |
| `Project not found` | Project ID does not exist or is archived |
| `Stage not found` | Stage ID does not exist |
| `Task not found` | Task ID does not exist or is archived |
| `Milestone not found` | Milestone ID does not exist |
| `Checklist not found` | Checklist ID does not exist |
| `Item not found` | Checklist item ID does not exist |
| `name is required` | Required `name` field was empty or missing |
| `project_id and name are required` | Both fields required for stage creation |
| `Checklist module ... is not installed` | `projects_task_checklists` module absent |

---

## 8. Attachments

> **Upload endpoints use `multipart/form-data`** — not JSON-RPC.  
> List and delete endpoints use standard JSON-RPC.  
> Max file size: **25 MB**.

### Attachment Object

```json
{
  "id":          301,
  "name":        "design-mockup.pdf",
  "mimetype":    "application/pdf",
  "file_size":   204800,
  "url":         "http://server/web/content/301?access_token=abc123",
  "res_model":   "project.task",
  "res_id":      55,
  "created_at":  "2026-03-27T10:00:00",
  "uploaded_by": { "id": 5, "name": "Rami Hassan" }
}
```

> `url` is a direct download link with an embedded access token — no extra auth header needed.

---

### Allowed File Types

| Category | Extensions |
|----------|-----------|
| Images | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`, `.bmp` |
| Documents | `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx` |
| Archives | `.zip` |
| Text | `.txt`, `.csv` |

---

### 8.1 List Attachments on Task

```
POST /api/crm/projects/ptasks/<task_id>/attachments/list
Content-Type: application/json
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": 55,
    "total": 2,
    "items": [ ...attachment objects... ]
  }
}
```

---

### 8.2 List Attachments on Project

```
POST /api/crm/projects/<project_id>/attachments/list
Content-Type: application/json
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "project_id": 1,
    "total": 4,
    "items": [ ...attachment objects... ]
  }
}
```

---

### 8.3 Upload File to Task

```
POST /api/crm/projects/ptasks/<task_id>/attachments/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Form fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `file` | Yes | The file binary |
| `name` | No | Custom display name (defaults to original filename) |

**Example (curl):**
```bash
curl -X POST "http://server/api/crm/projects/ptasks/55/attachments/upload" \
  -H "Authorization: Bearer eyJhbGc..." \
  -F "file=@/path/to/mockup.pdf" \
  -F "name=Homepage Mockup v2"
```

**Example (JavaScript / fetch):**
```js
const form = new FormData();
form.append('file', fileInput.files[0]);
form.append('name', 'Homepage Mockup v2');

const res = await fetch('/api/crm/projects/ptasks/55/attachments/upload', {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}` },
  body: form,
});
const json = await res.json();
// json.data.url  ← direct download URL
// json.data.id   ← attachment ID (needed for delete)
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id":          301,
    "name":        "Homepage Mockup v2",
    "mimetype":    "application/pdf",
    "file_size":   204800,
    "url":         "http://server/web/content/301?access_token=abc123",
    "res_model":   "project.task",
    "res_id":      55,
    "created_at":  "2026-03-27T10:05:00",
    "uploaded_by": { "id": 5, "name": "Rami Hassan" }
  }
}
```

---

### 8.4 Upload File to Project

```
POST /api/crm/projects/<project_id>/attachments/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

Same form fields and response shape as task upload above.

**Example (curl):**
```bash
curl -X POST "http://server/api/crm/projects/1/attachments/upload" \
  -H "Authorization: Bearer eyJhbGc..." \
  -F "file=@/path/to/spec.docx"
```

---

### 8.5 Delete Attachment

```
POST /api/crm/projects/attachments/<attachment_id>/delete
Content-Type: application/json
Authorization: Bearer <token>
```

Permanently deletes the attachment. Only attachments belonging to a `project.project` or `project.task` can be deleted via this endpoint.

**Response:**
```json
{ "success": true, "data": { "id": 301, "deleted": true } }
```

**Errors:**

| Error | Cause |
|-------|-------|
| `Attachment not found` | ID does not exist |
| `Not a project/task attachment` | Attempt to delete an unrelated system attachment |
