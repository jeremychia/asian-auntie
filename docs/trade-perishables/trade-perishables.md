# Trade Perishables

## Problem Statement

You live alone or cook niche cuisines. Supermarket quantities are too large for your needs.
You have sealed, unopened ingredients taking up space and approaching expiry — and no easy way to
find someone nearby who wants them.

## Scope Decision: What this feature covers in MVP

Three use cases were initially identified:
1. **Give away excess** (item expiring, someone nearby can use it)
2. **Split bulk purchases** (coordinate before buying to share cost)
3. **Trade items** (barter exchange)

MVP covers **give-away only**. Reasoning:
- Give-away has the most urgent timing (item expiring now)
- Lowest coordination cost — giver decides, receiver accepts or doesn't
- No value exchange to negotiate, no pre-purchase coordination
- Directly reduces waste, which is the core motivation
- Splitting and trading are harder coordination problems — build them on top of a working give-away base

## Design Constraints

### Sealed/unopened items only (MVP)

Partial quantity transfers (e.g., 600g of tamarind paste from a 1kg jar) introduce:
- Hygiene risk (open container, handling, re-sealing)
- Verification difficulty (how much is really left?)
- Physical logistics (containers, weighing, mess)

MVP: only sealed, original-packaging items can be listed.
This eliminates the hygiene and quantity verification problems entirely.
"I have an unopened 1kg bag of rice flour" is a clean, verifiable offer.

### Hyper-local launch

Cold start: without users nearby, no listings exist, no one finds the feature useful, no one lists.
Solution: launch within a specific, pre-committed community (e.g., a single HDB block, a building,
or an existing group chat) where trust and proximity already exist.

Do not launch as a public city-wide marketplace. Start contained. Expand when there's activity.

### Food safety

Trading food between individuals carries implicit safety responsibility.
Mitigations for MVP:
- Sealed items only (original packaging reduces contamination risk)
- Listing must include purchase date and expiry date (visible from packaging)
- Clear disclaimer: "Items are shared as-is. Verify packaging integrity before accepting."
- No liability accepted by the platform for item condition

## How it works (MVP: give-away flow)

### Listing an item
- Giver taps "List for give-away" (accessible from item detail in manage-perishables, or standalone)
- System pre-fills from inventory if item exists: name, expiry date, photo
- Giver confirms or adds: item condition (sealed — required), pickup notes (optional)
- Item listed to their community/building

### Finding and claiming
- Receiver opens trade feed — shows items listed in their community
- Feed shows: photo, item name, expiry date, distance/location hint (building/area, not exact address)
- Receiver taps "I'll take it" → giver gets a notification
- Giver confirms pickup arrangement (in-app message or their preferred contact method)
- Item marked as claimed, removed from feed

### After pickup
- Receiver marks "Picked up" → item archived
- Optional: receiver can leave a brief note ("Thanks! Great condition")
- No rating system in MVP — trust comes from community context, not scores

## What is explicitly not in scope (MVP)

- Partial quantity transfers (v2 — requires hygiene/container design)
- Splitting bulk purchases (v2 — requires pre-purchase coordination flow)
- Barter / value exchange (v2+)
- City-wide or public marketplace (only after community model is validated)
- In-app payment or financial exchange (never — legal complexity, licensing required)
- Rating/reputation system (v2 — needs activity volume to be meaningful)

## Cold start strategy

Before launch:
1. Identify a specific community willing to pilot (e.g., Jeremy's building, a cooking group)
2. Seed with real listings from the primary user
3. Measure: do any items get claimed? How long before claim?
4. Only expand community scope when give-away loop is working within the pilot group

"Build it and they will come" does not work for marketplace features. Seed first.

---

*Last updated: 2026-04-17*
