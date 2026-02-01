# Navigation Audit Report - TV-CBIA

## Summary
🔴 **Navigation is NOT uniform across all pages** and has significant gaps in accessibility.

---

## Page-by-Page Navigation Analysis

### ✅ PAGES USING base.html (Auto-get 3-button nav)
These pages inherit the main navigation from `base.html`:

| Page | Template | Routes Available | Status |
|------|----------|------------------|--------|
| **Library/Gestión** | `index.html` | ✅ Watch TV, Library, Channels | ✅ Complete |
| **Channels** | `canales.html` | ✅ Watch TV, Library, Channels | ✅ Complete |

**Navigation they show:**
- 📺 Watch TV (vertele)
- 📚 Library (gestion)
- 🎯 Channels (canales)

---

### ⚠️ PAGES WITH CUSTOM NAVIGATION (Stand-alone)
These pages have their own navigation and DON'T inherit from `base.html`:

| Page | URL | Top Nav | Additional Nav | Status |
|------|-----|---------|-----------------|--------|
| **Edit Video** | `/edit/<id>` | ✅ 3 buttons | ✅ Tags link | ✅ Good |
| **Upload** | `/upload` | ✅ 4 buttons | ✅ Mods/Patches | ✅ Good |
| **Upload Series** | `/upload_series` | ✅ 3 buttons | ✅ Series Mgmt | ✅ Good |
| **Upload Commercials** | `/upload_commercials` | ✅ 3 buttons | ✅ All Videos | ✅ Good |
| **Series Management** | `/series` | ✅ 3 buttons | ✅ Create/Manage | ✅ Good |
| **VCR Admin** | `/vcr_admin` | ✅ 3 buttons | ✅ Tape Mgmt | ✅ Good |
| **Watch TV** | `/vertele` | ⚠️ Limited | ❌ Outdated links | ⚠️ Needs Fix |
| **Mod Manager** | `/mod_manager` | ✅ 4 buttons | ✅ Patches/Upload | ✅ Good |
| **Patches** | `/patches` | ✅ 4 buttons | ✅ Mods/Upload | ✅ Good |

---

### 🔴 PAGES WITH OUTDATED LINKS (Still reference `/index`)

**Critical Issue:** Several pages still link to `/index` instead of `/gestion`:

1. **edit.html** (line 219-220) - OLD FOOTER NAV still references `index`
   ```html
   <a href="{{ url_for('index') }}">Back</a>
   <a href="{{ url_for('tags') }}">Tags</a>
   ```

2. **vertele.html** (lines 104, 140) - References `/index` instead of `/gestion`
   ```html
   <a href="{{ url_for('index') }}">Back to Home</a>
   ```

3. **upload.html** (line 164) - OLD NAV still has `index`
   ```html
   <a href="{{ url_for('index') }}">Back</a>
   ```

4. **upload_commercials.html** (line 129) - Cancel button references `/index`
   ```html
   <a href="{{ url_for('index') }}">Cancel</a>
   ```

5. **upload_series.html** (line 160) - Cancel button references `/index`
   ```html
   <a href="{{ url_for('index') }}">Cancel</a>
   ```

6. **series.html** (line 109) - OLD footer still has `index`
   ```html
   <a href="{{ url_for('index') }}">Back to Admin</a>
   ```

7. **video.html** - No navigation at all
   ```html
   <a href="{{ url_for('index') }}">Back</a>  <!-- Only link, references old route -->
   ```

---

## Navigation Access Matrix

### What can you access FROM each page?

```
FROM gestion (index.html):
  ├─ ✅ vertele (Watch TV)
  ├─ ✅ canales (Channels)
  ├─ ✅ edit_video (via content)
  ├─ ✅ upload (via buttons)
  ├─ ✅ series_page (via buttons)
  └─ ✅ vcr_admin (via buttons)

FROM vertele (Watch TV):
  ├─ ❌ gestion (uses old /index)
  ├─ ❌ canales (NOT AVAILABLE)
  └─ ❌ upload (NOT AVAILABLE)

FROM canales (Channels):
  ├─ ✅ gestion (via base.html)
  ├─ ✅ vertele (via base.html)
  └─ ✅ All features from index

FROM edit.html:
  ├─ ⚠️ gestion (header has it)
  ├─ ⚠️ tags (specific link)
  ├─ ⚠️ vertele (header has it)
  └─ ⚠️ Old footer still has /index

FROM upload.html:
  ├─ ✅ gestion
  ├─ ✅ vertele
  ├─ ✅ canales
  ├─ ✅ mod_manager
  ├─ ✅ patches
  └─ ⚠️ Line 164 still has old /index

FROM mod_manager:
  ├─ ✅ gestion
  ├─ ✅ vertele
  ├─ ✅ patches
  └─ ✅ upload

FROM patches:
  ├─ ✅ gestion
  ├─ ✅ vertele
  ├─ ✅ mod_manager
  └─ ✅ upload
```

---

## Issues Found

### 🔴 Critical Issues
1. **Inconsistent Route Names**: Mix of `url_for('index')` and `url_for('gestion')` throughout codebase
2. **Watch TV (vertele) Isolated**: Can only go to index (which redirects), not directly to gestion/canales/upload
3. **Multiple Navigation Patterns**: Some pages use base.html nav, others have custom nav
4. **Old Footer Navigation**: Remnants of old `/index` links still exist in several pages

### ⚠️ Medium Issues
1. **Canales page** extends base.html but doesn't add extra management features
2. **Video.html** has no main navigation, only back link
3. **player.html** has no obvious navigation (might be intentional)

### 📋 Minor Issues
1. Some pages have duplicate navigation (header + footer)
2. Inconsistent emoji usage across nav buttons
3. Some pages missing Mods/Patches buttons

---

## Recommendations

### 1. **Standardize All Pages to Use base.html**
- Make ALL pages inherit from `base.html` for consistent 3-button nav
- Override only when needed for specific page requirements

### 2. **Fix All `/index` References**
- Replace `url_for('index')` with `url_for('gestion')` globally
- Remove old footer navigation links

### 3. **Add Consistent Footer Navigation**
- All pages should have: Back | Watch TV | Upload | Channels
- Optional: Add Mods and Patches buttons to all pages

### 4. **Create Navigation Mixin**
Add a reusable nav pattern for standalone pages:
```html
<!-- All standalone pages include this -->
<div class="main-nav flex flex-wrap justify-center gap-2 mb-6">
  <a href="{{ url_for('gestion') }}" class="nav-btn">📚 Gestión</a>
  <a href="{{ url_for('vertele') }}" class="nav-btn">📺 Ver TV</a>
  <a href="{{ url_for('canales') }}" class="nav-btn">🎯 Canales</a>
  <a href="{{ url_for('upload') }}" class="nav-btn">📤 Upload</a>
  <a href="/mod_manager" class="nav-btn">📦 Mods</a>
  <a href="/patches" class="nav-btn">🔧 Patches</a>
</div>
```

### 5. **Add Page Context Variable**
Make it easier to highlight current page:
```python
# Every route should pass active_page
return render_template('page.html', active_page='gestión', ...)
```

---

## Action Items

| Priority | Issue | Pages Affected | Fix Time |
|----------|-------|-----------------|----------|
| 🔴 HIGH | Replace all `url_for('index')` with `url_for('gestion')` | 7 pages | 10 min |
| 🔴 HIGH | Add footer nav to vertele.html | 1 page | 5 min |
| ⚠️ MEDIUM | Standardize navigation styling | All pages | 15 min |
| ⚠️ MEDIUM | Add mods/patches buttons to all pages | 5 pages | 10 min |
| 🟢 LOW | Remove duplicate footer nav | Multiple pages | 5 min |
| 🟢 LOW | Add navigation to video.html | 1 page | 3 min |

---

## Current Status
- **Uniform Navigation**: ❌ NO (2 patterns: base.html vs custom)
- **Full Access**: ❌ NO (Watch TV isolated, old links still present)
- **User Experience**: ⚠️ MODERATE (Can navigate but inconsistent)

