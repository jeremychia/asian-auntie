# Problem Statement

## The Core Problem

Users have leftover or available ingredients at home and want to know what Asian recipes they can cook, but:

1. **Recipe trust**: LLM-generated suggestions feel random or inaccurate
2. **Ingredient waste**: Want to use what's on hand, not buy more
3. **Cultural authenticity**: Want real Asian recipes, not generic adaptations
4. **Source transparency**: Need to know where recipes come from

### Pain Points

1. **Guesswork**: "What can I make with these ingredients?" requires searching multiple sites
2. **Unreliable suggestions**: LLMs can hallucinate ingredients or techniques
3. **Missing context**: Don't know if a recipe is from a trusted source or culturally authentic
4. **Time-consuming**: Manual search across recipe sites is tedious
5. **Language barriers**: Some authentic Asian recipes aren't available in English or easy to find

## Target Users

### Primary User Persona 1: Home Cook

**Demographics**:
- Home cook interested in Asian cuisine
- Has leftover/available ingredients
- Wants to minimize food waste
- Skeptical of AI-generated recipes

**Pain Points**:
- Struggles to find recipes matching exact ingredients
- Wastes food because they don't know what to cook
- Frustrated by LLM hallucinations or inaccurate recipes
- Wants culturally authentic recipes, not adaptations

**Goals**:
- Quick recipe recommendations based on what they have
- Trust in recipe sources
- Discover new Asian recipes
- Reduce food waste

### Secondary User Persona: Curious Eater

**Demographics**:
- Exploring Asian cuisines
- Wants to learn about authentic recipes and techniques
- Values knowing the source of recipes

**Pain Points**:
- Hard to find curated, authentic Asian recipes
- Overwhelmed by recipe variations online

**Goals**:
- Discover authentic Asian recipes
- Understand recipe origins and sources

## Related Insights

- Users care deeply about **recipe source** — trust is earned, not given
- **Authenticity** matters — they want real recipes from real sources, not LLM inventions
- **Ingredient matching** is the entry point — "what can I cook?" is the primary question
- **Partial matches are useful** — "you have 6 of 8 ingredients" is actionable information
- **Inventory integration** removes double-entry friction — users already logged their pantry
- **Community aspect** is desirable long-term but introduces moderation complexity — deferred to v3+
- **Corpus breadth vs. depth tension**: a narrow, well-curated corpus is more trustworthy than a broad,
  inconsistent one — better to cover SE Asian well than all of Asia poorly

## Revised Scope Constraints

- Phase 1 recipe source: Malaysian + SE Asian only — stated explicitly in UI to set expectations
- Recipe instructions are never displayed inline — always linked to original source (copyright)
- Community features not in scope until moderation and accounts infrastructure exists
- Feedback mechanism is structured (reason-based), not binary like/dislike

---

*Last updated: 2026-04-17*
