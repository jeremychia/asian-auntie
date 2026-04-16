# Design Decisions

## Recipe Source & Trust

### Decision: Phase 1 uses curated sources only (no LLM-generated recipes)
- **Rationale**: Users explicitly want recipes from real sources, not AI-generated. This builds trust and avoids hallucinations.
- **Phase 1**: Hand-curated recipes from Rasamalaysia (Malaysian food site, trusted source)
- **Phase 2**: Expand to multiple vetted recipe sources (e.g., food blogs, cookbooks, cultural sites)
- **Never**: Don't generate recipes via LLM; use AI only for matching ingredients to existing recipes
- **Status**: Decided
- **Updated**: 2026-04-16

### Decision: Every recipe must include source attribution
- **Rationale**: Transparency builds trust. Users need to know where recipes come from.
- **Display**: Recipe card includes: source name, link to original, author/creator (if available)
- **Status**: Decided
- **Updated**: 2026-04-16

---

## Ingredient Input

### Decision: Phase 1 requires manual ingredient entry
- **Rationale**: Simpler MVP, no camera/OCR complexity. Users type what they have.
- **Phase 2**: Auto-recognition via photo (scan fridge, cabinet labels, etc.)
- **UX**: Autocomplete/dropdown from known ingredient list to reduce typos
- **Status**: Decided
- **Updated**: 2026-04-16

### Decision: Ingredient list is optional, not all-or-nothing
- **Rationale**: Users might browse recipes without having specific ingredients on hand. Matching is best-effort, not strict.
- **Logic**: "Show me recipes that use most of these" not "only recipes using all ingredients"
- **Status**: Decided
- **Updated**: 2026-04-16

---

## Recommendation Algorithm

### Decision: Content-based matching (not pure AI ranking)
- **Rationale**: Transparent, reproducible, user-understandable matching logic
- **Approach**: 
  - Count ingredient overlap (how many user's ingredients are in the recipe?)
  - Rank by overlap percentage
  - Secondary sort by community rating (future)
- **Avoids**: Black-box ML models that users can't understand why a recipe was suggested
- **Status**: Decided
- **Updated**: 2026-04-16

---

## User Feedback & Learning

### Decision: Ratings & reviews, not reinforcement learning (v1)
- **Rationale**: "Reinforcement learning" is complex; simple ratings are more transparent and practical
- **MVP**: Like/dislike button on each recipe recommendation
- **Future**: Use ratings to improve ranking (e.g., recipes liked by similar users)
- **Data**: Ratings stay local (v1) or sync to community (v2+)
- **Status**: Decided
- **Updated**: 2026-04-16

---

## Community & Social

### Decision: Reviews & photos are v2 feature
- **Rationale**: Adds complexity (user accounts, moderation, photo storage). MVP focuses on recommendations.
- **Phase 1**: Individual ratings only
- **Phase 2**: User reviews with photos, community leaderboard
- **Status**: Deferred
- **Updated**: 2026-04-16

---

## Platform & Scope

### Decision: Web-first MVP with mobile secondary
- **Rationale**: Recipe browsing is content-heavy; web offers better layout. Mobile app comes if demand exists.
- **Interactive elements**: Ingredient input is dynamic; recommendations appear on same page
- **Status**: Decided
- **Updated**: 2026-04-16

### Decision: No user accounts required for MVP
- **Rationale**: Reduces friction. Ratings can be local (device storage) initially.
- **Future**: Optional accounts for cross-device sync and community features
- **Status**: Decided
- **Updated**: 2026-04-16

---

*Last updated: 2026-04-16*
