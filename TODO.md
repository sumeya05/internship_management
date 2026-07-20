# Fix: "Not Permitted" Error for Public Pages

## Steps

- [x] Step 1: Analyze the issue - Understand all the problems
- [x] Step 2: Read all relevant source files for complete understanding
- [x] Step 3: Consolidate `public_page_helper.py` with direct implementation (remove fragile delegation)
- [x] Step 4: Update `hooks_public_pages_fix.py` to be backward-compatible re-export wrapper
- [x] Step 5: Fix `hooks.py` - permission hook function references were pointing to non-existent functions
- [x] Step 6: Add `has_general_permission()` function to `permissioning.py`
- [x] Step 7: Clear Frappe cache and test

## Root Causes Found

### Cause 1: Fragile delegation chain
`hooks.py` → `public_page_helper.py` (delegates via try/except to) → `hooks_public_pages_fix.py`
If the import failed silently, `public_page` flag was never set → **"Not Permitted"**

### Cause 2: Empty/root path not handled
When visiting `/`, path was empty string → `fix_public_pages_for_app_prefix()` returned early
without setting `public_page = True`

### Cause 3: Wrong function names in `hooks.py` ⬅️ **MAIN ISSUE**
`permission_query_conditions` referenced `get_permission_query_conditions` (doesn't exist)
`has_permission` referenced `has_permission` (doesn't exist in permissioning.py)

Actual functions in `permissioning.py`:
- `get_conditions_intern_profile`, `get_conditions_intern_attendance`, etc.
- No `has_permission` function existed at all

## Fix Summary

### `public_page_helper.py` - Consolidated implementation
- Moved full implementation here (eliminates fragile import delegation)
- Added root URL `/` handling (sets `public_page = True` for empty path)
- Clean error logging

### `hooks_public_pages_fix.py` - Backward-compatible wrapper
- Now delegates TO `public_page_helper` instead of the other way around

### `hooks.py` - Fixed permission hook references
- `permission_query_conditions`: now points to correct function names
- `has_permission`: now points to `has_general_permission`

### `permissioning.py` - Added missing function
- Added `has_general_permission()` function with proper role-based logic

