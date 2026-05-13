# Supply Chain Custom Fields Tab Fix Task

This document defines the frontend work required to make the existing **Custom Fields** tab functional for dynamic `extra_fields` in Supply Chain modules.

---

## Issue Found

The **Custom Fields** tab is visible in Supply Chain modules, but it is currently not functional.

Observed problem:

- Custom Fields tab renders in the UI.
- The tab is not clickable or does not switch correctly.
- Clicking the tab does not trigger any API call.
- `extra_fields` data is never fetched or rendered.
- Static text is shown: `No custom fields added`.

This is incomplete frontend integration. The tab must not behave as dead/static UI.

---

## Modules

1. **Purchase Orders**
2. **Item Requests**
3. **Negotiations**

---

## Task

Fix Custom Fields tab functionality for dynamic extra fields across all listed modules.

---

## 1. Tab Click Behavior

Make the **Custom Fields** tab fully clickable.

Expected behavior:

- User clicks the **Custom Fields** tab.
- Active tab state switches correctly.
- The content panel changes to the Custom Fields panel.
- The selected record context is preserved.

No dead, disabled, static, or visually-only tab is allowed.

Debug possible root causes:

- Missing `onClick` handler.
- Missing or incorrect `activeTab` state.
- Tab key/value mismatch.
- Tab panel not mapped.
- Tab component receives disabled state by mistake.
- Click event is blocked by overlay, z-index, or parent handler.

---

## 2. Fetch Data On Tab Open

When the **Custom Fields** tab opens:

- Trigger the required detail or list API call.
- Fetch the selected record's `extra_fields`.
- Verify whether the API already returns `extra_fields` in the detail response or list response.
- Store the returned `extra_fields` in frontend state.

Do not use hardcoded placeholder text as the source of truth.

Implementation guidance:

- If the list response already includes `extra_fields`, preserve it and render it immediately.
- If the list response does not include enough data, fetch the detail endpoint when the Custom Fields tab opens.
- Avoid showing an empty state before the API response is known.

---

## 3. Render `extra_fields`

If `extra_fields` exists and contains keys, render all key/value pairs.

Example:

```text
displaySku : SR-50-GL
priorityTag : urgent
```

Suggested UI:

- Key/value rows
- Table layout
- Stacked layout
- Existing module detail/card style, if available

Rendering rules:

- Show every key returned by the backend.
- Show the corresponding value clearly.
- Do not silently drop unknown keys.
- Render non-string values safely, for example by formatting JSON values for display.

---

## 4. Empty State

If no `extra_fields` exist, show:

```text
No custom fields added
```

Only show this after a real API response confirms that `extra_fields` is empty or missing.

Do not show this message as a static default before loading is complete.

Recommended states:

- Loading: show the existing loader/skeleton/spinner pattern.
- Success with fields: show key/value fields.
- Success with no fields: show `No custom fields added`.
- Error: show a clear error state or retry option according to existing UI patterns.

---

## 5. Add Custom Field Action

Inside the **Custom Fields** tab, show a button:

```text
Add Custom Field
```

Allow the user to:

- Add a key.
- Add a value.
- Save or update the record.

Validation:

- Key is required.
- Value is required if product rules require non-empty values.
- Duplicate keys are not allowed in the same record.
- Trim key and value before submit where appropriate.
- Respect backend key format rules if documented in the backend API guide.

---

## 6. API Integration

Ensure all relevant frontend API flows support `extra_fields`.

Required checks:

- Create API sends `extra_fields`.
- Update API sends `extra_fields`.
- Detail API reads `extra_fields`.
- List API reads `extra_fields` when returned.
- Frontend models/types include `extra_fields`.
- Frontend state stores `extra_fields`.
- API adapters or mappers do not strip `extra_fields`.

Expected payload examples:

Create or save:

```json
{
  "extra_fields": {
    "displaySku": "SR-50-GL",
    "priorityTag": "urgent"
  }
}
```

Update:

```json
{
  "extra_fields": {
    "priorityTag": "urgent"
  }
}
```

Confirm whether backend update behavior is merge-based or full replacement before implementing removal behavior.

---

## 7. Debugging Checklist

Check why the current tab is non-functional.

Possible issues:

- Missing `onClick` handler.
- Missing `activeTab` state.
- Incorrect tab key or enum value.
- Tab panel is not mapped.
- API hook is not connected.
- Detail query is disabled or missing selected record ID.
- Data loader ignores the Custom Fields tab.
- Response mapper strips `extra_fields`.
- Component always renders static `No custom fields added`.

Fix the root cause, not only the visible text.

---

## Module Checklist

### Purchase Orders

- [ ] Custom Fields tab is clickable.
- [ ] Active tab switching works.
- [ ] API call fires on tab open when needed.
- [ ] `extra_fields` is fetched from detail or list response.
- [ ] `extra_fields` key/value pairs render correctly.
- [ ] `Add Custom Field` action works.
- [ ] Empty state appears only after a real empty response.

### Item Requests

- [ ] Custom Fields tab is clickable.
- [ ] Active tab switching works.
- [ ] API call fires on tab open when needed.
- [ ] `extra_fields` is fetched from detail or list response.
- [ ] `extra_fields` key/value pairs render correctly.
- [ ] `Add Custom Field` action works.
- [ ] Empty state appears only after a real empty response.

### Negotiations

- [ ] Custom Fields tab is clickable.
- [ ] Active tab switching works.
- [ ] API call fires on tab open when needed.
- [ ] `extra_fields` is fetched from detail or list response.
- [ ] `extra_fields` key/value pairs render correctly.
- [ ] `Add Custom Field` action works.
- [ ] Empty state appears only after a real empty response.

---

## Acceptance Criteria

- Custom Fields tab is clickable in Purchase Orders, Item Requests, and Negotiations.
- Active tab switching works correctly.
- API call fires on tab open when needed.
- `extra_fields` renders correctly.
- `Add Custom Field` works.
- Empty state is shown only after a real empty API response.
- Create API sends `extra_fields`.
- Update API sends `extra_fields`.
- Detail/list APIs read `extra_fields`.
- No static fake UI remains.

---

## Deliverable

After implementation, fill in:

```text
CUSTOM_FIELDS_TAB_FIX_REPORT.md
```

The report must include:

- Root cause found.
- Files changed.
- APIs verified.
- Modules fixed.
- Pending issues, if any.
