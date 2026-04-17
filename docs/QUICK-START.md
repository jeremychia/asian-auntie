# Quick Start: Design Phase

You have 3 features to design. Here's the fastest path to building.

## The Process (Per Feature)

### Day 1: Lock Core Decisions (1 hour)

**Time**: 1 hour per feature

**Output**: Answers to "Core Questions to Lock In"

For **Manage Perishables**, pick 3:
- [ ] Notification timing: 3 days before expiry?
- [ ] Photo optional or mandatory?
- [ ] Scale: single-user or future household?

For **Recommend Recipe**, pick 3:
- [ ] Rasamalaysia only, or multi-source?
- [ ] Real-time recommendations or Search button?
- [ ] How to scrape recipes (manual vs. automated)?

For **Trade Perishables**, pick 3:
- [ ] Give Away only, or include Trade + Group Buy?
- [ ] In-app messaging or email/phone only?
- [ ] What's the neighborhood boundary?

**Don't overthink it.** Pick best guesses; you'll learn from building.

---

### Day 2: Define Happy Paths (1.5 hours)

**Time**: 30 minutes per feature

**Output**: One clear user flow per feature (in USER-FLOWS.md)

Example for Manage Perishables "Add Item":
```
1. User taps "+"
2. Takes photo (optional)
3. Types item name
4. Selects expiry date
5. Taps Save
→ Item appears in dashboard
```

That's it. Don't add edge cases yet; just the happy path.

---

### Day 3: Start Building (∞)

You're ready. You have:
- ✅ Core decisions made
- ✅ Happy path documented
- ✅ Acceptance criteria (from features.md)
- ✅ Known edge cases (from user-flows.md)

Build the happy path first. Edge cases come later.

---

## How to Answer "Core Questions to Lock In"

**Rule**: Answer in 10 minutes. If you're still debating, flip a coin.

You'll validate your answer by building. Wrong answers now → learning opportunity later.

**Example decision**:
- Q: "Photo optional or mandatory?"
- A: "Optional. Users can skip for speed."
- Why: Reduces friction, but might hurt quality. We'll learn from usage.
- Test: If no one uses photos, we'll make them optional-but-highlighted in v2.

---

## What NOT to Do

❌ Don't write detailed specs before building  
❌ Don't try to answer all 20 open questions  
❌ Don't design all edge cases upfront  
❌ Don't wait for perfect alignment — good enough wins  
❌ Don't overthink aesthetics (mobile first, then polish)

---

## What to Do

✅ Answer 3 core questions per feature  
✅ Write one happy path per feature  
✅ Build the happy path end-to-end  
✅ Learn from building (update docs as you go)  
✅ Keep docs lightweight (no more than 100 lines per section)

---

## Timeline

```
Day 1: Lock decisions (3 hours total)
  - Manage Perishables: 1 hour
  - Recommend Recipe: 1 hour
  - Trade Perishables: 1 hour

Day 2: Happy paths (1.5 hours total)
  - 30 min per feature

Day 3-14: Build MVP
  - Choose one feature
  - Build the happy path
  - Learn & iterate
  - Update docs as you go

Week 3: Expand & refine
  - Add edge cases
  - Start second feature
  - Answer more open questions as needed
```

---

## How to Know You're Ready to Build

Ask yourself:

1. **Can I explain the core problem in 1 sentence?**
   - "Users waste food because they forget what they have and when it expires"
   - ✅ Yes → Ready

2. **Can I walk through the happy path in 2 minutes?**
   - "User adds item, gets notified before expiry, marks as used" 
   - ✅ Yes → Ready

3. **Do I know the 3-5 biggest decisions?**
   - "Notifications at 3 days. Photos optional. Single user only."
   - ✅ Yes → Ready

4. **Can I list 2-3 open questions that don't block building?**
   - "We'll figure out item categories, bulk quantities later"
   - ✅ Yes → Ready

If you answered ✅ to all 4, **start coding today**. You know enough.

---

*Last updated: 2026-04-17*
