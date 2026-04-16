# Open Questions

## Still Debating

### 1. Rasamalaysia as sole Phase 1 source — good choice?
- **Current decision**: Yes, Phase 1 only
- **Question**: Is Rasamalaysia the right starting point? Are recipes detailed enough to parse?
- **Concern**: Limited recipe count might mean limited recommendations
- **TBD**: Should we add a second source in Phase 1, or keep it lean?

### 2. Ingredient matching: Exact or fuzzy?
- **Current decision**: Content-based, simple overlap counting
- **Question**: Should "chicken breast" match "chicken" or are they separate?
- **Options**:
  - Strict: "chicken breast" ≠ "chicken" (more precise but rigid)
  - Fuzzy: "chicken breast" ≈ "chicken" (flexible but might over-match)
  - Semantic: Use AI to understand "chicken breast is a type of chicken" (complex)
- **TBD**: What level of matching feels right?

### 3. Real-time recommendations vs. Search button?
- **Current decision**: Real-time (update as you type)
- **Question**: Is real-time too much (overwhelming results), or just right?
- **Alt**: Add a "Search" button to keep recommendations stable until user clicks
- **TBD**: What feels better in practice?

### 4. How to scrape/parse Rasamalaysia recipes?
- **Challenge**: Extract ingredients, instructions, cook time reliably
- **Options**:
  - Manual curation (hand-enter recipes) — slow but reliable
  - Web scraping — fast but fragile if site structure changes
  - Work with Rasamalaysia directly — ideal but requires partnership
- **TBD**: What's the most sustainable approach?

### 5. Ingredient list scope: How detailed?
- **Question**: How specific should ingredient names be?
- **Examples**:
  - "Chicken" vs. "Chicken breast" vs. "Boneless chicken breast"
  - "Oil" vs. "Vegetable oil" vs. "Olive oil"
- **Impact**: Affects matching accuracy and ingredient input complexity
- **TBD**: What's the right balance between specificity and usability?

---

## Unknowns

### 6. Will users trust recipe sources?
- Assumption: Users will trust Rasamalaysia as a source
- **Question**: Is one source enough to build credibility, or does variety matter?
- **Impact**: Affects whether MVP feels trustworthy

### 7. How many recipes in Phase 1 MVP?
- **Question**: How many Rasamalaysia recipes are available/parseable?
- **Concern**: If <50 recipes, users might not find recommendations useful
- **Impact**: Affects whether we need a second source in Phase 1

### 8. Ingredient database: How many ingredients?
- **Question**: Should autocomplete handle 100, 500, or 5000+ ingredients?
- **Concern**: More ingredients = better matching, but maintenance burden
- **Impact**: Affects complexity of ingredient curation

### 9. User motivation for v1: Just recommendations, or more?
- **Question**: Is "get recipe suggestions" enough, or do you need ratings/reviews to feel engaged?
- **Impact**: Affects whether MVP feels complete

### 10. Performance: How many recommendations are too many?
- **Question**: If a user adds "chicken", should we show 200 recipes, or limit to top 20?
- **UX concern**: Long lists are overwhelming
- **TBD**: Pagination, infinite scroll, or show-all?

---

## Design Feedback Needed

- [ ] Does the layout feel good with ingredient input at top and recipe results below?
- [ ] Should we show match % as a percentage, a bar, or just "High/Medium/Low"?
- [ ] Would you use "Go to Source" immediately, or is the recipe detail enough?
- [ ] Is like/dislike enough for feedback, or do you want 1-5 star ratings in MVP?

---

## Next Steps

1. **Decide on recipe scraping approach** — manual vs. automated
2. **Clarify ingredient matching rules** — exact vs. fuzzy
3. **Define Rasamalaysia data** — count recipes and ingredient types
4. **Mockup the UI** — ingredient input + recipe results layout
5. **Set up recipe database schema** — how to store recipes and ingredients

---

*Last updated: 2026-04-16*
