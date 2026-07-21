# Fix 403 Errors on Public Asset Routes (`/website_script.js`, `/login`, etc.)

## Problem
The `before_request` hook in `public_page_helper.py` was returning early for `.js`/`.css` paths (in `before_request()`) and listing public asset filenames in `IGNORE_ROUTES` (in `fix_public_pages_for_app_prefix()`), preventing the `public_page` flag from being set for Guest users. This caused Frappe to return **403 Forbidden** for public assets like `/website_script.js`.

## Root Cause
1. `before_request()` returned early for paths ending in `.js` or `.css` **before** calling `fix_public_pages_for_app_prefix()`.
2. Inside `fix_public_pages_for_app_prefix()`, the `IGNORE_ROUTES` set included public asset filenames (`website_script.js`, `website_style.css`, etc.), so the function returned early **before** the `PUBLIC_ASSETS` check could set `frappe.local.flags.public_page = True`.

## Fix Applied

### Changes to `public_page_helper.py`

1. **`before_request()`** — Removed `path.endswith(".js")`, `path.endswith(".css")`, and `path in ("/sw.js", "/website_script.js")` from the early-return guard clause. These paths now flow through to `fix_public_pages_for_app_prefix()`.

2. **`IGNORE_ROUTES`** — Removed public asset filenames (`website_script.js`, `website_style.css`, `website.bundle.css`, `sw.js`, `favicon.ico`, `robots.txt`). These are only in `PUBLIC_ASSETS`, which correctly sets `public_page = True`.

3. **Updated docstrings** to reflect the new behavior.

### Result
- `/website_script.js` → flows to `fix_public_pages_for_app_prefix()` → matches `PUBLIC_ASSETS` → sets `public_page = True` → Frappe serves it to Guest users
- `/login?redirect-to=/login` → The login page can now load `/website_script.js` and function properly

## Next Steps
- [ ] `bench --site internship.localhost clear-cache`
- [ ] `bench restart`
- [ ] Test: visit `http://internship.localhost:8000/login` — should load without 403
- [ ] Test: check browser devtools for `/website_script.js` — should return 200

