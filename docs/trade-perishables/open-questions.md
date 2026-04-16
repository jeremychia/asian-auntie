# Open Questions

## Still Debating

### 1. Group Buy mechanics: Pre-order or marketplace?
- **Current approach**: Soft coordination (organizer posts, people express interest)
- **Question**: Should this be more formal? (e.g., pre-order with payment)
- **Tradeoff**:
  - Soft: Low commitment, flexible, but might fizzle out
  - Formal: Binding, ensures fulfillment, but complex (payments, logistics)
- **Related**: How will group buys actually work? (Unknown #7)
- **Strategic**: Can you launch with just "Give Away"? Skip Trade and Group Buy for v1?
- **TBD**: What feels right for a neighborhood marketplace?

### 2. Contact method: In-app chat or external email/phone?
- **Current decision**: External (email/phone only, no in-app messaging)
- **Rationale**: Simpler MVP, but less convenient for users
- **Question**: Is friction acceptable, or should we add messaging?
- **Strategic**: Would in-app messaging remove enough friction to be worth the complexity?
- **TBD**: Can MVP launch without in-app messaging?

### 3. Trust & safety: How much moderation needed?
- **Current decision**: Minimal (flag & remove abuse)
- **Question**: Is this enough, or do we need verification (ID, reviews)?
- **Concern**: Unverified marketplace might feel risky
- **Strategic**: What liability exposure exists for a peer-to-peer marketplace? (Unknown #10)
- **TBD**: What builds enough trust without heavy overhead?

### 4. Geographic scope: How large should the radius be?
- **Current thought**: Neighborhood/1-3 km radius
- **Question**: Too small (limited inventory) or too large (logistics hard)?
- **Strategic**: What's the neighborhood definition? Zip code? 1km radius? Walking distance?
- **Related**: Network effects — does this only work if 100+ neighbors are on it?
- **TBD**: What's the right balance for MVP?

### 5. Anonymous or identity-required?
- **Current decision**: Optional anonymity (users can choose)
- **Question**: Does anonymity reduce trust, or is it a feature?
- **Concern**: Some people want privacy; others want to know who they're trading with
- **Strategic**: Would you trade with a complete stranger in your neighborhood, or only people you know?
- **TBD**: Should we require identity verification?

### 6. Food safety & expiration accuracy
- **Current approach**: User is responsible, photos/expiry dates encouraged
- **Question**: What if someone lists something as fresh but it's already bad?
- **Concern**: Food safety liability and health risks
- **Strategic**: Are there food sharing regulations in your area? Good Samaritan laws?
- **TBD**: How strict should verification be before launch?

---

## Unknowns

### 7. Will users actually use a trade feature vs. just give away?
- **Assumption**: Users want to trade for things they need
- **Question**: Is give-away more likely? Will trade listings ever match?
- **Strategic**: Why would someone trade instead of donating to food banks or just throwing it away?
- **Impact**: Affects whether complex trade logic is worth building

### 8. How will group buys actually work?
- **Challenge**: Coordinating payment, bulk purchase, and distribution is messy
- **Question**: Is this realistic for MVP, or should we defer?
- **Strategic**: Should this integrate with "Manage Perishables"? Auto-list items about to expire?
- **Impact**: Might be too complex for v1; could simplify to "post bulk items for sale"

### 9. What's the "critical mass" for the marketplace to feel useful?
- **Question**: How many listings does it take before MVP feels alive?
- **Concern**: Sparse marketplace (5 listings) might feel dead
- **Strategic**: Can you launch with just "Give Away"? Does network density matter for viability?
- **Impact**: Affects launch strategy (seed listings, build community first, etc.)

### 10. Will pickup logistics actually work?
- **Assumption**: Users will arrange their own pickups (cafe, lobby, etc.)
- **Question**: Is this realistic, or too much friction?
- **Strategic**: Does asking for a neighbor's phone number to arrange pickup feel awkward or natural?
- **Impact**: Affects whether marketplace feels frictionless

### 11. Legal liability & food safety
- **Question**: What liability exposure exists for a peer-to-peer marketplace?
- **Concern**: Users trading potentially harmful items (allergens, contamination, expired items)
- **Strategic**: What disclaimer/TOS is required pre-launch? Food sharing regulations in your area?
- **Impact**: Affects legal structure and compliance needed before launch

### 12. Payment for trades: Cash, apps, or no payment?
- **Assumption**: MVP is barter (no money), all trades free or negotiated
- **Question**: Should we support payment apps (Venmo, etc.) in MVP?
- **Strategic**: How do you monetize this, or is it a passion project forever?
- **Impact**: Affects scope and payment infrastructure

### 13. Competitive positioning
- **Question**: Who are actual competitors? Nextdoor, Facebook Groups, OLIO, Food Rescue, Reddit/local Slack?
- **Strategic**: What's the gap you're solving that they don't? Why not just use existing platforms?
- **Impact**: Affects market viability and feature differentiation

### 14. Integration with other features
- **Question**: Should this integrate with Manage Perishables and Recommend Recipe?
- **Scenarios**:
  - Auto-list items expiring soon from Manage Perishables?
  - Search for ingredients from Recommend Recipe recipes on Trade Perishables?
  - Coordinate bulk buys of ingredients people need for recipes?
- **Impact**: Affects product cohesion and scope

---

## Core Questions to Lock In

These shape everything else — pick 3-5 to decide first:

- [ ] **Scope**: Give Away only (simpler), or include Trade + Group Buy?
- [ ] **Contact**: In-app messaging (convenient, complex) or email/phone only (simple, friction)?
- [ ] **Trust**: Required identity verification (safer, friction) or optional anonymity (flexible, risky)?
- [ ] **Monetization**: How do you sustain this? Free forever, ads, premium features, commission?
- [ ] **Ecosystem**: Standalone app or integrated with Manage Perishables + Recommend Recipe?
- [ ] **Legal**: Can you launch without lawyers, or do you need liability coverage + TOS review?

---

## Design Feedback Needed

- [ ] Does the three trade types (Give/Trade/Group Buy) feel intuitive, or confusing?
- [ ] Should anonymity be default or opt-in?
- [ ] For Group Buy, should we show payment integration or keep it simple coordination?
- [ ] Does the listing creation flow feel quick and easy, or cumbersome?
- [ ] What core emotion should users feel? Noble (waste reduction), lucky (found what I needed), community (connected), or economic (saved money)?

---

## Next Steps

1. **Answer core questions above** — these lock in scope and viability
2. **Define geographic boundaries** — neighborhood radius and criteria
3. **Clarify Group Buy scope** — how formal should coordination be?
4. **Address legal/safety** — what terms of service and liability coverage needed?
5. **Plan launch strategy** — how to seed listings and build initial community?
6. **Competitive analysis** — what gap does this fill vs. Nextdoor, OLIO, Facebook Groups?
7. **Wireframe the marketplace UI** — browse, listing detail, creation flow

---

*Last updated: 2026-04-16*
