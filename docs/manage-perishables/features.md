# Features

## MVP Features

### 1. Add Perishable Item

**User Story**: As a user, I want to quickly add an item to my inventory so I can track when it expires.

**Workflow**:
1. Tap "+" or "Add Item"
2. Take a photo (optional) or skip
3. Enter item name (required)
4. Enter expiry date (required) — format: MM/DD/YYYY or date picker
5. Save

**Details**:
- Photo is stored with the item as a visual reference
- Item name should be searchable (free text, auto-complete nice-to-have)
- Expiry date validation: warn if date is in the past
- Confirmation screen before saving

**Screen**: Mobile form with camera access

---

### 2. View Inventory (Dashboard)

**User Story**: As a user, I want to see all my items at a glance to know what I have.

**Display Options**:

#### Default View: Sorted by Expiry Date
- **Urgent** (expires today): Red badge
- **Soon** (expires in 1-3 days): Yellow badge
- **Later** (expires 4+ days): Gray text
- Each item shows: name, expiry date, photo thumbnail

#### Search & Filter
- Search by item name
- Filter by: "Expires soon", "Expires later", "All"

**Details**:
- Tap item to see full details
- Swipe to delete (with confirmation)
- Item count summary at top

**Screen**: Mobile list view with cards

---

### 3. Item Detail View

**User Story**: As a user, I want to see full details of an item and manage it.

**Displays**:
- Photo (full-size)
- Item name
- Expiry date (formatted readably)
- Days until expiry (e.g., "5 days remaining")
- Urgency status badge (Expires Today / Soon / Later)

**Actions**:
- **Mark as Used** — removes item from inventory
- **Edit** — update name or expiry date
- **Delete** — remove without marking used
- **Share** — (future) send to household members

**Screen**: Mobile detail page

---

### 4. Notifications

**Expiry Alerts**:
- **3 days before**: "Milk expires in 3 days — use soon"
- **1 day before**: "Milk expires tomorrow"
- **On expiry day**: "Milk expires today — use now!"

**Notification Behavior**:
- Delivered as push notifications (mobile)
- Dismissable but persistent (re-appear at next check-in if item not marked used)
- Quiet notifications (no sound by default, respects Do Not Disturb)

**Web Dashboard** (future):
- Email digest of expiring items (daily or weekly)

---

### 5. Delete/Archive Item

**User Story**: As a user, I want to remove items from my inventory.

**Workflows**:

#### Mark as Used
- Item is removed from active inventory
- Counted toward usage history (future analytics)

#### Delete
- Item is removed immediately
- Counted toward waste/lost items (future analytics)

**Confirmation**: "Are you sure?" warning if deleting item that expires in 1+ week

---

## Future Features (v2+)

### Recipe Integration
- Suggest recipes based on items expiring soon
- Link from recipe → required ingredients from inventory
- Cross off ingredients as you cook

### Analytics & Insights
- "You waste ~30% of dairy items"
- "Cilantro lasts 5 days on average for you"
- Spending over time
- Waste patterns by category

### Household/Shared Inventory
- Share inventory with household members
- Conflict resolution (who used it?)
- Notifications for others when items are about to expire

### Supermarket Integration
- Know current prices of items you frequently buy
- Shopping list generation ("You're out of milk, it's $3.99 at X store")
- Best-by-date alerts ("Milk is 50% off this week, you usually buy it")

### Advanced Tracking
- Quantity tracking ("3 jars of peanut butter")
- Item categories (Dairy, Produce, Pantry, etc.)
- Storage location ("Fridge shelf 2")
- Barcode scanning for standard products

### Web Dashboard (Full Admin)
- Full inventory management
- Bulk add/edit items
- Export inventory to CSV
- Advanced filtering and sorting

---

## Acceptance Criteria for MVP Launch

- [ ] Users can add items with photos and expiry dates
- [ ] Inventory displays sorted by expiry date with urgency badges
- [ ] Users receive notifications 3 days, 1 day, and 0 days before expiry
- [ ] Users can mark items as used or delete them
- [ ] Photos are stored and displayed with items
- [ ] Data persists locally (no cloud requirement for MVP)

---

*Last updated: 2026-04-16*
