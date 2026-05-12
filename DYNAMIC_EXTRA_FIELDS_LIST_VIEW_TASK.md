# Supply Chain Dynamic Extra Fields — List View Frontend Task

This document defines the frontend work required to render backend `extra_fields` data in Supply Chain list views.

Backend list APIs may already return `extra_fields`, but the frontend list pages currently do not expose custom field key/value data to users. In the current UI, custom fields may appear only as a tab or hidden detail area, and the tab is not always reachable/clickable from the list workflow. The frontend must not drop or hide `extra_fields` when the backend sends it.

---

## Issue

Backend list APIs return `extra_fields`, but frontend list pages do not display custom field key/value data.

Affected modules:

1. **Item Requests list**
2. **Negotiations list**
3. **Purchase Orders list**

---

## Task

Audit and fix list-view support for `extra_fields` in each module.

For each module:

- Verify the list API response contains `extra_fields`.
- Verify the frontend model/types include `extra_fields`.
- Verify the frontend list state stores `extra_fields` without stripping it.
- Render visible custom field key/value data in the list UI.
- Fix any non-clickable or hidden custom-fields tab/section that prevents users from seeing backend data.

---

## API Audit Requirements

Check the live/staging network response or the frontend API client mapping for each list endpoint.

| Module | Check | Expected result |
|--------|-------|-----------------|
| Item Requests | List API returns `extra_fields` | `extra_fields` is present on each record when data exists |
| Negotiations | List API returns `extra_fields` | `extra_fields` is present on each record when data exists |
| Purchase Orders | List API returns `extra_fields` | `extra_fields` is present on each record when data exists |

If the backend response includes `extra_fields`, the frontend must preserve it through:

- API response parsing / adapter functions
- TypeScript interfaces or models
- Component state
- Table/card row data
- Detail drawer/modal data loaded from the selected list item

---

## UI Requirement

Show custom fields in list/detail cards or table rows.

Suggested rendering when `extra_fields` exists:

```text
Custom Fields:
displaySku: SR-50-GL
priorityTag: urgent
```

Possible UI placements:

- Expandable row
- Tooltip or popover
- Extra table column
- Card section
- Detail drawer/list item preview section

The selected placement must make the field key and value visible to the user. Do not rely on a hidden or non-clickable tab as the only way to access this data.

---

## Empty State

If no `extra_fields` exist for a record, either show nothing or show:

```text
No custom fields
```

Use whichever pattern matches the existing list UI.

---

## Module Checklist

### Item Requests List

- [ ] Confirm list API response includes `extra_fields`.
- [ ] Add or verify `extra_fields` in frontend item request types/models.
- [ ] Ensure list state stores `extra_fields`.
- [ ] Render custom field key/value pairs in the list row, card, expandable area, tooltip, popover, or detail preview.
- [ ] Confirm selecting/opening a row still preserves `extra_fields`.

### Negotiations List

- [ ] Confirm list API response includes `extra_fields`.
- [ ] Add or verify `extra_fields` in frontend negotiation types/models.
- [ ] Ensure list state stores `extra_fields`.
- [ ] Render custom field key/value pairs in the list row, card, expandable area, tooltip, popover, or detail preview.
- [ ] Confirm selecting/opening a row still preserves `extra_fields`.

### Purchase Orders List

- [ ] Confirm list API response includes `extra_fields`.
- [ ] Add or verify `extra_fields` in frontend purchase order types/models.
- [ ] Ensure list state stores `extra_fields`.
- [ ] Render custom field key/value pairs in the list row, card, expandable area, tooltip, popover, or detail preview.
- [ ] Confirm selecting/opening a row still preserves `extra_fields`.

---

## Acceptance Criteria

- Item Requests list renders `extra_fields`.
- Negotiations list renders `extra_fields`.
- Purchase Orders list renders `extra_fields`.
- Field key/value pairs are visible to the user.
- Frontend types/models include `extra_fields`.
- Frontend state stores `extra_fields`.
- No backend `extra_fields` data is lost, stripped, or hidden by the frontend.
- If a Custom Fields tab or section exists in the list/detail workflow, it is clickable/reachable and displays the same data.

---

## Deliverable

Implement the frontend changes, then fill in `DYNAMIC_EXTRA_FIELDS_LIST_REPORT.md` with:

- APIs checked
- Whether list APIs return `extra_fields`
- Frontend rendering status
- Files changed
- Pending issues
