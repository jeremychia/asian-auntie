# Features

## MVP Features

### 1. Ingredient Input

**User Story**: As a user, I want to tell the app what ingredients I have so I can get recipe recommendations.

**Workflow**:
1. Land on homepage with search/input field
2. Type ingredient name (e.g., "chicken", "soy sauce", "garlic")
3. Autocomplete suggests matching ingredients from known list
4. Press Add or select from dropdown
5. Ingredient appears in "My Ingredients" list
6. Repeat to add more ingredients
7. Clear or remove any ingredient with X button

**Details**:
- Autocomplete prevents typos and unifies ingredient names (e.g., "SOY SAUCE" vs "soy sauce" treated identically)
- No minimum/maximum ingredients required
- Users can search recipes with zero ingredients (browse all) or multiple
- Empty state helpful hint: "Add ingredients to get started"

**Screen**: Single-page app with ingredient input + recipe results below

---

### 2. Recipe Recommendation

**User Story**: As a user, I want recipe suggestions based on my ingredients.

**Display**:
- Real-time as ingredients are added (no "search" button needed)
- Ranked by ingredient match percentage (highest match first)
- Shows:
  - Recipe title
  - Source name & link (e.g., "From Rasamalaysia")
  - Ingredient list (highlighted: which of user's ingredients are in recipe)
  - Cuisine/category (optional: Malaysian, Vegetarian, etc.)
  - Community rating (v2: number of likes if available)

**Matching Logic**:
- Percentage match = (ingredients in recipe that user has) / (total ingredients in recipe)
- Example: User has chicken, garlic, soy sauce. Recipe needs chicken, garlic, soy sauce, oyster sauce, ginger
  - Match = 3/5 = 60%
- Display recipes in descending order by match %
- All recipes shown, not filtered to "must have 80%+ match"

**Filtering/Sorting** (v2):
- Filter by cuisine (Malaysian, Thai, Vietnamese, etc.)
- Filter by dietary (vegetarian, vegan, gluten-free)
- Sort by rating (if available)

**Screen**: Recipe cards in vertical feed or grid

---

### 3. Recipe Detail

**User Story**: As a user, I want to see full recipe details so I can cook it.

**Displays**:
- Recipe title
- Source & source link (clickable — goes to original recipe)
- Author/creator (if available)
- Ingredients list (full quantities)
- Cooking instructions (scraped from source)
- Estimated cook time (if available)
- Dietary info (vegetarian, vegan, etc.)
- Cuisine/category tags
- Your match % (how many of your ingredients does this use?)

**Actions**:
- **Like/Dislike** button — thumbs up/down for rating
- **Share** (v2) — send recipe to friend or social
- **Save** (v2) — bookmark for later
- **Go to Source** — button linking to original recipe

**Screen**: Full-page recipe detail

---

### 4. Like/Dislike Rating

**User Story**: As a user, I want to rate recipes so the app learns what I like.

**Implementation**:
- Thumbs up/down buttons on recipe detail view
- Rating is stored locally (device storage, v1)
- Visual feedback: button highlights when clicked
- No accounts or logins required

**Data**:
- Rating = user preference signal
- Used in v2+ to improve recommendations and community ratings

**Screen**: Simple buttons within recipe detail

---

## Future Features (v2+)

### Auto-Ingredient Recognition
- Users take photo of fridge/cabinet
- OCR/vision detects labels and items
- Auto-populates ingredient list
- Manual editing allowed for corrections

### Reviews & Community
- Users write reviews with ratings (1-5 stars)
- Users upload photos of their cooked dish
- Community leaderboard (most-rated recipes, most-reviewed chefs)
- User profiles and following system

### Advanced Recommendations
- Machine learning: recommend recipes liked by users with similar tastes
- Dietary filters: show only vegetarian, vegan, gluten-free, etc.
- Cuisine filters: show only Thai, Malaysian, Vietnamese, etc.
- Difficulty level: filter by Easy/Medium/Hard

### Multi-Source Recipe Expansion
- Recipes from multiple food blogs and sources (not just Rasamalaysia)
- Verification process for new sources to ensure quality and authenticity
- Cultural authenticity badges (curated by community experts)

### Meal Planning
- Save favorite recipes
- Generate weekly meal plan based on saved recipes
- Auto-generate shopping list from meal plan

### Integration with Manage Perishables
- Pull ingredient list from perishables inventory
- "Cook this tonight" suggestions based on items expiring soon
- Check off ingredients as you use them

### Recipe Personalization
- User preferences (favorite cuisines, dietary restrictions)
- Learning: improve recommendations based on likes/dislikes
- "Saved recipes" collection

### Mobile App
- Native iOS/Android apps with same features as web
- Offline recipe browsing
- Shareable recipe cards with photos

---

## Acceptance Criteria for MVP Launch

- [ ] Users can input ingredients via text input with autocomplete
- [ ] Recipe database contains Rasamalaysia recipes with ingredients parsed
- [ ] Recommendations display in real-time as ingredients are added
- [ ] Recipes ranked by ingredient match percentage
- [ ] Each recipe displays source, link, ingredients, and instructions
- [ ] Users can like/dislike recipes
- [ ] Ratings stored locally (no backend required for MVP)
- [ ] "Go to Source" link works and links to original recipe
- [ ] Mobile-friendly responsive design

---

*Last updated: 2026-04-16*
