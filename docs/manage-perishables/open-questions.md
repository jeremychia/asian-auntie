# Open Questions

## Still Debating

### 1. Photo Requirement: Optional or Mandatory?
- **Current decision**: Optional (user can skip)
- **Reasoning**: Reduces friction for quick adds, but might lead to missing visual context
- **Tradeoff**: 
  - Mandatory = higher data quality, slower adds
  - Optional = faster adds, less consistent data
- **TBD**: How important is the photo for recognition/memory?

### 2. Expiry Date Format: Manual Entry or Date Picker?
- **Options**:
  - Free text (MM/DD/YYYY) — requires parsing
  - Date picker (calendar UI) — guaranteed valid but slower
  - Both — best UX but more complex
- **Question**: Which reduces errors and friction best for your use case?

### 3. Notification Timing: 3 days the right window?
- **Current decision**: 3 days before expiry
- **Concern**: 
  - Too early = notification fatigue, users ignore it
  - Too late = not enough time to use item
- **TBD**: Is 3 days right for your typical cooking patterns? Should it be configurable immediately or in v2?

### 4. Item Name Input: Free text or controlled vocabulary?
- **Options**:
  - Free text — user can type anything, less consistent
  - Dropdown/autocomplete — suggests common items, faster, more searchable
  - Hybrid — autocomplete with ability to add custom
- **Question**: Would autocomplete help or slow you down?

---

## Unknowns

### 5. How accurate will expiry date entry be?
- Some items have clear "Use by" dates
- Others might be estimates ("cilantro lasts about a week")
- **Impact**: Affects whether notifications are reliable
- **TBD**: Should we build in a "best guess" feature or ask users to be exact?

### 6. What's the actual add flow timing?
- Do you add items **immediately after shopping** (while at home unpacking)?
- Or **as needed** (only when you remember to)?
- Or **batch weekly** (Sunday prep)?
- **Impact**: Affects notification strategy and feature priority

### 7. Will you actually use photos?
- Honest question: Will you take photos consistently, or skip them?
- **Impact**: Should we invest in photo storage/display or keep it minimal?

### 8. How many items are we actually tracking?
- Dozens (5-30 items)? Hundreds (100+)?
- **Impact**: Affects UI complexity (need search/filter immediately or later?)

### 9. Scale: Just you, or future household?
- MVP is single-user, but are you building toward sharing?
- **Impact**: Should architecture support multi-user from the start, or refactor later?

### 10. Offline-first priority?
- Should the app work without internet?
- **Impact**: Database choice (local SQLite vs. cloud-based)

---

## Design Feedback Needed

- [ ] Do the urgency badges (Red/Yellow/Gray) feel right, or would you prefer different visual cues?
- [ ] Should the dashboard show a count of expiring items, or is that noise?
- [ ] Does "Mark as Used" feel natural, or should it be "Remove" or "Consume"?

---

## Next Steps

1. **Answer unknowns 5-7** — these shape immediate design decisions
2. **Decide on photo flow** — impacts complexity and UI/UX
3. **Lock in notification timing** — affects reliability for users
4. **Wireframe the mobile UI** — before building
5. **Set up project tracking** — Figma, Linear, or wherever you want to track this

---

*Last updated: 2026-04-16*
