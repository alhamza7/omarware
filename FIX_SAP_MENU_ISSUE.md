# Fix SAP Integration Menu Issue

## Problem

When opening SAP Integration from the menu, it was showing only the "Complete Migration" popup wizard instead of the dashboard.

## Root Cause

The main menu item `menu_sap_integration` in `sap_menus_minimal.xml` was defined without an action:

```xml
<menuitem id="menu_sap_integration"
          name="SAP Integration"
          sequence="10"/>
```

When a menu item doesn't have an action, Odoo may:
1. Show nothing (blank page)
2. Show the first available wizard/action it finds
3. Cause unpredictable behavior

In this case, it was showing the `sap.product.complete.migration` wizard.

## Solution

### Step 1: Add action to menu

Added the `action_sap_dashboard` to the main menu item:

```xml
<menuitem id="menu_sap_integration"
          name="SAP Integration"
          action="action_sap_dashboard"
          sequence="10"/>
```

### Step 2: Fix loading order (CRITICAL)

The action must be defined BEFORE the menu that uses it!

Changed the loading order in `__manifest__.py`:

```python
# Before (WRONG - caused error):
'views/sap_menus_minimal.xml',            # Menu loaded first
'views/sap_dashboard_action_minimal.xml', # Action loaded second ❌

# After (CORRECT):
'views/sap_dashboard_action_minimal.xml', # Action loaded first ✅
'views/sap_menus_minimal.xml',            # Menu loaded second
```

**Why this matters:**
- Odoo loads XML files sequentially
- When menu references `action="action_sap_dashboard"`, the action must already exist
- Loading menu before action causes: `ValueError: External ID not found: sap_integration.action_sap_dashboard`

## Files Modified

- `addons/sap_integration/views/sap_menus_minimal.xml`
  - Added `action="action_sap_dashboard"` attribute to menu_sap_integration
  
- `addons/sap_integration/__manifest__.py`
  - Reordered data files: action BEFORE menu

## Result

✅ Clicking "SAP Integration" menu now opens the SAP Dashboard
✅ Complete Migration wizard accessible from Tools submenu only
✅ Proper menu structure maintained

## Testing

1. Open Odoo: http://localhost:8070
2. Click: SAP Integration (main menu)
3. Expected: SAP Dashboard opens
4. Access migration wizard: SAP Integration → Management Tools → Complete Product Migration

---

**Fixed:** 2026-02-01
**Status:** ✅ Resolved
