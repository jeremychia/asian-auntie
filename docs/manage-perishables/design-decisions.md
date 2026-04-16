# Design Decisions

## Platform & Scope

### Decision: Mobile-first with web as secondary
- **Rationale**: Primary interaction happens while shopping, cooking, and checking inventory — contexts where users have phones in hand. Web can serve as a full-inventory dashboard and admin interface.
- **Implications**: Navigation should favor thumb-friendly UI. Web gets parity later, not in MVP.
- **Status**: Decided
- **Updated**: 2026-04-16

### Decision: Single-user app for MVP (no household sharing)
- **Rationale**: Reduces complexity significantly. Avoids conflict resolution ("who used the milk?"), permission management, and notification chaos in shared spaces.
- **Future**: Can add household/shared inventory in v2 if demand exists.
- **Status**: Decided
- **Updated**: 2026-04-16

---

## Core Features

### Decision: Scan + manual entry hybrid (not barcode-only)
- **Rationale**: Barcode scanning alone is unrealistic for international/bulk products. Photos + manual entry is more flexible and reliable.
- **Process**: User can take a photo for memory, then manually record item name and expiry date.
- **Status**: Decided
- **Updated**: 2026-04-16

### Decision: Item-level tracking (not quantity)
- **Rationale**: MVP focuses on "what expires" not "how much is left". Reduces UI complexity.
- **Tradeoff**: Won't support "3 jars of peanut butter" as separate line items initially.
- **Status**: Decided
- **Updated**: 2026-04-16

---

## Notifications & Reminders

### Decision: Configurable expiry warning windows
- **Default**: Notifications trigger 3 days before expiry date
- **Rationale**: Enough lead time to plan usage or donate, but not so early that users ignore them (notification fatigue).
- **Future**: Users can customize per item or globally.
- **Status**: Decided
- **Updated**: 2026-04-16

### Decision: "Use today" alert on expiry day
- **Rationale**: A sharp, actionable alert on the day something expires maximizes chance of use vs. waste.
- **Status**: Decided
- **Updated**: 2026-04-16

---

## Data & Privacy

### Decision: Local-first with cloud sync (future)
- **Rationale**: MVP can use local storage to reduce backend complexity. Cloud sync comes later for multi-device support.
- **Status**: Decided
- **Updated**: 2026-04-16

### Decision: No tracking of user behavior for analytics (initial)
- **Rationale**: Privacy-first approach. User insights (waste patterns) remain on-device until explicitly requested.
- **Status**: Decided
- **Updated**: 2026-04-16

---

## Nice-to-Haves (Deferred)

### Decision: Recipe integration deferred to v2
- **Rationale**: Adds complexity (recipe database, ingredient parsing). MVP focuses on core tracking + notifications.
- **Status**: Deferred
- **Updated**: 2026-04-16

### Decision: Supermarket API integration deferred to v2
- **Rationale**: Requires external dependencies and pricing data. Scope creep for MVP.
- **Status**: Deferred
- **Updated**: 2026-04-16

---

*Last updated: 2026-04-16*
