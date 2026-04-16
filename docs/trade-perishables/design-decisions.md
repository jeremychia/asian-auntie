# Design Decisions

## Trade Models

### Decision: Support three trade models (Give, Trade 1:1, Group Buy)
- **Give**: "I have excess, take it for free" — low friction, builds goodwill
- **Trade 1:1**: "I have X, I want Y" — peer-to-peer swaps
- **Group Buy**: "Let's split this bulk purchase together" — coordinated buying
- **Rationale**: Different users have different needs; flexibility increases platform utility
- **Status**: Decided
- **Updated**: 2026-04-16

---

## Scope & Geography

### Decision: Location-based, hyper-local (neighborhood/building focus)
- **Rationale**: Logistics (pickup, delivery) must be feasible. Small geographic radius keeps trades realistic.
- **MVP scope**: Single neighborhood/area (you can expand)
- **Pickup model**: Users arrange their own logistics (coffee shop, building lobby, etc.)
- **No shipping**: This is for local, same-day or next-day trades only
- **Status**: Decided
- **Updated**: 2026-04-16

### Decision: Trust through community, not formal ratings (v1)
- **Rationale**: For a neighborhood, reputation spreads naturally. Formal systems can wait.
- **Phase 1**: Users are neighbors, likely to see each other again (incentive to be honest)
- **Phase 2**: Ratings and reviews if community grows
- **Status**: Decided
- **Updated**: 2026-04-16

---

## Item Listings

### Decision: Item freshness is user's responsibility
- **Rationale**: Reduces compliance burden. Users should only trade fresh items — trust + reputation prevents abuse.
- **Safeguard**: Users can upload photos and expiry dates to prove freshness
- **Status**: Decided
- **Updated**: 2026-04-16

### Decision: Photos and expiry dates are optional but encouraged
- **Rationale**: Transparency builds trust. Photos prove item condition; expiry date proves freshness.
- **Incentive**: Items with photos/expiry info likely to get more interest
- **Status**: Decided
- **Updated**: 2026-04-16

---

## Platform & Access

### Decision: Web-first MVP (mobile secondary)
- **Rationale**: Browsing listings is content-heavy. Mobile app can follow if traction exists.
- **Responsive design**: Works on phone browsers during MVP
- **Status**: Decided
- **Updated**: 2026-04-16

### Decision: Light-weight user accounts (not social networks)
- **Rationale**: You need to contact people to trade, but no need for full profiles initially.
- **Phase 1**: Email/phone for contact, basic profile (name, neighborhood)
- **Phase 2**: Reputation system, messaging, profiles if scale warrants
- **Status**: Decided
- **Updated**: 2026-04-16

---

## Logistics & Safety

### Decision: No platform-mediated payment or logistics
- **Rationale**: Keeps MVP simple. Users arrange their own exchanges (cash, free, etc.) and pickup/delivery.
- **Trade agreements**: Between users directly, platform is matchmaker only
- **Liability**: Platform does not handle or ship goods
- **Status**: Decided
- **Updated**: 2026-04-16

### Decision: Geofencing to prevent distant trades
- **Rationale**: Enforces hyper-local scope and practicality
- **Implementation**: Show only listings within X km of user's location
- **Status**: Decided
- **Updated**: 2026-04-16

---

## Community Moderation

### Decision: Minimal moderation (flag & remove only)
- **Rationale**: MVP should be low-overhead. Community moderation scales better than paid staff.
- **Abuse handling**: Users can flag suspicious listings; admin reviews and removes if needed
- **Phase 2**: More formal moderation if scale requires
- **Status**: Decided
- **Updated**: 2026-04-16

---

*Last updated: 2026-04-16*
