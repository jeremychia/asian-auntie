# Features

## MVP Features

### 1. User Account & Location

**User Story**: As a user, I want to set up an account and location so others know where I am.

**Workflow**:
1. Sign up with email or phone
2. Set name/username (anonymous option available)
3. Set location/neighborhood (zip code or neighborhood name)
4. Set contact method (email, phone, both)
5. Done

**Details**:
- Minimal profile — no long bio or complex setup
- Location is used for geofencing (only show trades within X km)
- Contact info is revealed only when user initiates contact (not public)
- Users can opt for partial anonymity if desired

**Screen**: Simple signup flow, 3-5 steps

---

### 2. Create Listing (Give Away)

**User Story**: As a user, I want to list an excess item I'm giving away.

**Workflow**:
1. Click "List New Item"
2. Choose type: "Give Away" / "Trade" / "Group Buy"
3. Enter item name (e.g., "Tamarind paste, opened jar")
4. Upload photo (optional but encouraged)
5. Enter expiry date (optional but encouraged)
6. Add description (optional, e.g., "kept in fridge, lightly used")
7. Set pickup location (home, specific cafe, etc.)
8. Available until when? (date picker)
9. Post

**Details**:
- Photos stored on-device or CDN
- Expiry date field highlights item urgency
- Available-until date helps prevent stale listings
- Item status: "Available", "Pending" (negotiating), "Claimed"
- Photos and expiry dates shown prominently to build trust

**Screen**: Form with preview of listing before post

---

### 3. Create Listing (Trade 1:1)

**User Story**: As a user, I want to trade one ingredient for another.

**Workflow**:
1. Click "List New Item"
2. Choose type: "Trade"
3. Item I'm offering: name, photo, expiry
4. Item I want: name (what are you looking for?)
5. Add note (optional, e.g., "Must be fresh")
6. Post

**Details**:
- "Item I want" is a search field — browse existing items to find matches, or type what you're looking for
- Notifications when someone posts matching items
- Can lead to matching or negotiation

**Screen**: Trade form + "Find matches" section

---

### 4. Create Listing (Group Buy)

**User Story**: As a user, I want to coordinate a group purchase of a bulk item.

**Workflow**:
1. Click "List New Item"
2. Choose type: "Group Buy"
3. Item name (e.g., "Bulk tamarind paste, 1kg")
4. Cost & how to split (total price, estimated per-person cost)
5. How many shares available? (e.g., 4 people)
6. Current shares claimed (updates as people join)
7. Organizer info: Will this person buy and distribute, or coordinate together?
8. Deadline: By when should shares be claimed?
9. Post

**Details**:
- Shows interest from others ("3 people interested")
- Organizer coordinates timing and logistics
- Group buy feels like a poll/pre-order, not a binding contract
- Platform facilitates connection, not payment

**Screen**: Group buy form + interest tracker

---

### 5. Browse & Search Listings

**User Story**: As a user, I want to find items I need.

**Workflow**:
1. Land on "Browse" page
2. See list of nearby listings (sorted by newest)
3. Filter by type: All / Give Away / Trade / Group Buy
4. Search by item name
5. Tap listing to view details

**Details**:
- Map view (v2): Show listings geographically
- Listings show:
  - Item name & type (Give/Trade/Group Buy)
  - Photo thumbnail
  - Expiry date (if available, highlighted if urgent)
  - Distance from you
  - Posted by (first name or anonymous)
- Urgent items (expiring <2 days) marked with banner
- Empty state hint: "No items near you yet. Post something to get started!"

**Screen**: Feed/list view with filtering

---

### 6. View Listing Detail

**User Story**: As a user, I want full details before contacting someone.

**Display**:
- Full photo(s)
- Item name & description
- Expiry date (if available)
- Type (Give Away / Trade / Group Buy)
- Posted by (first name)
- Location/distance
- Pickup instructions
- Date posted & "Available until" date
- Contact info (revealed on tap or contact attempt)

**Actions**:
- **Contact** button (email or phone, depending on preference)
- **Flag** (if suspicious)
- Back to browse

**Details**:
- Contact reveals user's name/number to the other party
- No in-app messaging (v1) — users coordinate externally
- Flag system for spam/abuse

**Screen**: Full-page listing detail

---

### 7. User Profile

**User Story**: As a user, I want others to see my activity and build trust.

**Displays**:
- Name/username
- Location
- "Items posted" count
- "Items claimed" count (successful trades)
- "Join date"
- Contact method (revealed on trade)

**Details**:
- Minimal info, no lengthy bios
- Reputation signals through activity
- Later: Ratings, reviews if community grows

**Screen**: Simple public profile

---

## Future Features (v2+)

### Messaging & In-App Chat
- Direct messaging between traders
- Reduce friction of emailing/texting
- Conversation history in one place

### Map View
- See listings on a map
- Geospatial search (within X km radius)
- Pick up points marked

### Ratings & Reviews
- 1-5 star ratings per trade
- Written reviews
- Reputation badges (e.g., "Trusted trader")

### Notifications
- New listings matching your interests
- Someone interested in your item
- Group buy reaching required shares

### Payment Integration
- Optional, trust-based payments for trades
- Split bills for group buys
- Reduces cash exchange friction

### Expiration Management
- Integrate with "Manage Perishables" app
- Auto-list items expiring soon
- Notify network when something is about to expire

### Community Features
- Verified neighborhoods (verify resident status)
- Community moderators
- Leaderboard (most active traders)
- Events (swap meets, bulk buying groups)

### Advanced Search
- Filter by cuisine type (if integrated with Recommend Recipe)
- Dietary preferences (vegan, organic, etc.)
- Quality/condition filters

---

## Acceptance Criteria for MVP Launch

- [ ] Users can sign up with email and location
- [ ] Users can list items (Give Away, Trade, Group Buy)
- [ ] Users can upload photos and expiry dates
- [ ] Listings display with photos, expiry, and distance
- [ ] Users can search listings by item name
- [ ] Users can filter by listing type
- [ ] Listings geofenced to local area
- [ ] Users can contact listing creators
- [ ] Flag system works for reporting abuse
- [ ] User profiles show activity/reputation signals
- [ ] No in-app messaging required for MVP

---

*Last updated: 2026-04-16*
