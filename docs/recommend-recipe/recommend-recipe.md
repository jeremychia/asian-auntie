# Recommend Recipe

## Problem Statement

You have ingredients in your fridge and pantry.
You want to know what Asian recipes you can cook with what you have — recipes that are real, sourced,
and culturally grounded, not invented by an LLM.

## Design Principles

1. **Inventory-first**: primary ingredient source is the user's manage-perishables inventory — not manual typing
2. **Source-grounded**: every suggestion links to a real recipe with its source shown
3. **Partial matching is fine**: show recipes you can *almost* make, with clear gap information
4. **Narrow and honest**: Phase 1 covers Malaysian and Southeast Asian recipes — this is stated upfront

## How it works

### Step 1: Ingredient source

**Primary (one tap):** "Use my pantry" — pulls non-expired items from manage-perishables inventory.
User can deselect items they don't want to cook with (e.g., "ignore the fish sauce, I'm saving it").

**Fallback (manual):** User types ingredients. Fuzzy autocomplete from the same Asian pantry list
used in manage-perishables. For users who haven't logged their inventory, or want to add items
they have but didn't log.

### Step 2: Recipe search and matching

System searches the recipe corpus against available ingredients.
Results are ranked by ingredient match percentage — not filtered to exact matches only.

Each result shows:
- Recipe name
- Source (e.g., "Rasa Malaysia", "Woks of Life")
- Ingredient match: "6 of 8 ingredients" with the gap listed ("Missing: palm sugar, galangal")
- Cook time and difficulty (if available from source)

This lets the user decide: "I can get galangal — let me make this" vs. "too many missing, skip."

### Step 3: Feedback

After viewing a recipe, user can mark:
- "Made this" (positive signal — recipe surfaced again for similar ingredient sets)
- Optional structured reason if skipping: "Too complex", "Missing key ingredient", "Not my taste"

Binary like/dislike is avoided — it gives no signal on *why*, which makes improvement impossible.

## Recipe corpus

### Phase 1: Curated Malaysian and Southeast Asian sources
- Rasa Malaysia (primary seed source)
- Additional SE Asian sources to be identified
- Recipes stored in a structured format: name, source URL, ingredients list, cuisine tag

Scope is narrow and honest. The onboarding and empty states explicitly say:
*"We focus on Malaysian and Southeast Asian recipes to start."*
This prevents disappointment from users with Japanese or Korean pantries.

### Phase 2: Expand to other Asian cuisines
Priority order based on common pantry types:
1. Chinese (Cantonese, Sichuan)
2. Japanese
3. Korean
4. Vietnamese / Thai (closer to SE Asian, easier to add)

Each added cuisine requires a trusted source — not AI-generated recipes.
Candidate sources: Woks of Life (Chinese), Just One Cookbook (Japanese), Maangchi (Korean).

### Phase 3 (not before Phase 2 is stable): Dynamic search
Automatically discover recipes from pre-vetted sources.
Must maintain source transparency — no AI-generated content surfaced without clear labeling.

## What is explicitly not in scope

- Community photo sharing (v3+ — requires moderation, accounts, content policy)
- Reinforcement / machine learning (replaced by structured feedback; ML requires scale)
- LLM-generated recipes (contradicts the core trust model)
- Recipe instructions displayed inline (copyright — always link to source)

---

*Last updated: 2026-04-17*
