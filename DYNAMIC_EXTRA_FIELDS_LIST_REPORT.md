# Supply Chain Dynamic Extra Fields — List View Frontend Report

**Project:** Supply Chain — `extra_fields` list-view rendering  
**Task file:** `DYNAMIC_EXTRA_FIELDS_LIST_VIEW_TASK.md`  
**Date:** _YYYY-MM-DD_  
**Author:** _Name / team_

---

## APIs checked

Document the API endpoints or frontend API client methods verified for each module.

| Module | API / client method checked | Evidence / notes |
|--------|-----------------------------|------------------|
| Item Requests | _Example: item requests list endpoint or client method_ | |
| Negotiations | _Example: negotiations list endpoint or client method_ | |
| Purchase Orders | _Example: purchase orders list endpoint or client method_ | |

---

## List APIs returning `extra_fields` yes/no

| Module | Returns `extra_fields`? | Response shape / notes |
|--------|--------------------------|------------------------|
| Item Requests | ☐ Yes ☐ No ☐ Not checked | |
| Negotiations | ☐ Yes ☐ No ☐ Not checked | |
| Purchase Orders | ☐ Yes ☐ No ☐ Not checked | |

Example expected shape when data exists:

```json
{
  "id": 29,
  "extra_fields": {
    "displaySku": "SR-50-GL",
    "priorityTag": "urgent"
  }
}
```

---

## Frontend rendering fixed

Confirm whether each module now renders custom field key/value data in list views or list-connected detail UI.

| Module | Model/types include `extra_fields` | List state stores `extra_fields` | UI renders key/value data | Placement used |
|--------|------------------------------------|----------------------------------|---------------------------|----------------|
| Item Requests | ☐ Yes ☐ No | ☐ Yes ☐ No | ☐ Yes ☐ No | _Expandable row / tooltip / popover / column / card section / detail preview_ |
| Negotiations | ☐ Yes ☐ No | ☐ Yes ☐ No | ☐ Yes ☐ No | _Expandable row / tooltip / popover / column / card section / detail preview_ |
| Purchase Orders | ☐ Yes ☐ No | ☐ Yes ☐ No | ☐ Yes ☐ No | _Expandable row / tooltip / popover / column / card section / detail preview_ |

Required display when `extra_fields` exists:

```text
Custom Fields:
displaySku: SR-50-GL
priorityTag: urgent
```

Empty-state behavior:

| Module | Empty state used |
|--------|------------------|
| Item Requests | ☐ Hidden when empty ☐ Shows `No custom fields` |
| Negotiations | ☐ Hidden when empty ☐ Shows `No custom fields` |
| Purchase Orders | ☐ Hidden when empty ☐ Shows `No custom fields` |

---

## Files changed

List all frontend files changed.

| File | Change summary |
|------|----------------|
| | |
| | |
| | |

Examples of expected file categories:

- API client or response adapter files
- TypeScript model/interface files
- List page components
- Table/card row components
- Detail drawer/modal components
- Shared custom-fields display component, if created

---

## Pending issues

Document anything still blocking or requiring backend/product confirmation.

| ID | Description | Owner | Severity | Next action |
|----|-------------|-------|----------|-------------|
| | | | | |

Possible pending issues:

- A list API does not return `extra_fields`.
- The frontend API adapter strips unknown fields.
- A Custom Fields tab exists but is not clickable or reachable from the list workflow.
- Non-string JSON values need a display decision.
- The list UI needs product approval for placement: column, popover, expandable row, or card section.

---

## Final verification

| Acceptance criterion | Status | Notes |
|----------------------|--------|-------|
| Item Requests list renders `extra_fields` | ☐ Pass ☐ Fail | |
| Negotiations list renders `extra_fields` | ☐ Pass ☐ Fail | |
| Purchase Orders list renders `extra_fields` | ☐ Pass ☐ Fail | |
| Field key/value pairs are visible to the user | ☐ Pass ☐ Fail | |
| No backend `extra_fields` data is lost in frontend | ☐ Pass ☐ Fail | |
| Custom Fields tab/section is clickable or an alternative visible placement exists | ☐ Pass ☐ Fail | |
