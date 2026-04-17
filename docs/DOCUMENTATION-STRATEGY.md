# Documentation Strategy

How to manage context, design iteration, and collaboration across the Asian Auntie project.

## The Problem: Context Load

As the project grows, keeping collaborators aligned without overwhelming them with documentation is challenging:

- **Too little context**: People repeat work or make conflicting decisions
- **Too much context**: Nobody reads it; information gets lost
- **Scattered context**: Decisions buried in chat/email are forgotten

## Our Approach: Layered Documents

We use three layers of documentation, each serving a specific purpose:

### Layer 1: Decision Snapshots (Updated Daily)
**Files**: `design-decisions.md`, `features.md`
**Purpose**: "What have we decided?"
**Frequency**: Update as decisions are made
**Reader time**: 5-10 minutes to scan
**For**: Collaborators who need quick context before jumping in

**What goes here**:
- Decided features and their rationale
- Chosen constraints (scope, platform, technology)
- Trade-offs and why we chose the path we took

**What does NOT go here**:
- Reasoning for rejected ideas (those go to open-questions)
- Theoretical discussions (those go to research docs)

---

### Layer 2: Open Questions & Unknowns (Living Document)
**Files**: `open-questions.md`
**Purpose**: "What are we still figuring out?"
**Frequency**: Update as questions arise, answer them incrementally
**Reader time**: 2-5 minutes to scan for relevance
**For**: Understanding what's in flux and why

**What goes here**:
- Decisions we're debating (with both sides of the tradeoff)
- Unknowns that affect scope
- Strategic questions that unlock other decisions

**Structure**:
- **Still Debating**: Questions actively in discussion (have a decision direction)
- **Unknowns**: Things we haven't figured out yet
- **Core Questions to Lock In**: The 5-6 questions that unblock everything else
- **Additional Questions**: Deeper details for when you're drilling down

**Note**: This doc serves as a quick "litmus test" — if a question isn't here, it's either decided or out of scope.

---

### Layer 3: Detailed Design (Reference When Needed)
**Files**: `features.md`, `problem-statement.md`
**Purpose**: "How do we actually build this?"
**Frequency**: Update when implementing or clarifying edge cases
**Reader time**: 10-30 minutes for one feature
**For**: Developers/designers building the feature

**What goes here**:
- Detailed user stories and workflows
- Acceptance criteria
- Edge cases and error states
- Integration points with other features

---

## When You're Designing a Feature: The Optimal Flow

Instead of one long document, **iterate through these steps**:

### Step 1: Problem & Constraint Snapshot (5 min)
Create a quick problem statement:
- "Why does this feature exist?"
- "Who uses it?"
- "What constraint does it hit?"

**Example** (Manage Perishables):
```
Users have items expiring but forget about them → food waste.
Constraint: Single-user MVP, no household sharing.
```

### Step 2: Core Decisions Only (10 min)
Lock in 3-5 critical decisions:
- "What's the primary interaction?"
- "What's out of scope?"
- "What's the simplest viable version?"

**Example**:
```
Decision 1: Notifications at 3 days, 1 day, 0 days (not configurable in MVP)
Decision 2: Item-level tracking (not quantities)
Decision 3: Photos optional
```

### Step 3: Happy Path User Flow (15 min)
One clear, linear user flow from start to finish:
```
1. User opens app
2. Taps "Add Item"
3. Takes photo (optional)
4. Enters name + expiry date
5. Gets notification 3 days before
6. Marks as used
Done.
```

Only document this one path. Everything else is future.

### Step 4: Open Questions (10 min)
What do you NOT know that blocks implementation?
- "Will photos be fast enough with cloud storage?"
- "Should notification text be 'expires in 3 days' or 'use by Friday'?"

Put these in `open-questions.md` and move on. Don't let them block building.

### Step 5: Build & Learn (⏰ ongoing)
As you implement, you'll discover:
- What UX feels natural (this often differs from spec)
- What data you actually need to track
- What edge cases matter

Update `features.md` with this learning. Don't try to predict it upfront.

---

## Example: Designing Trade Perishables' Give Away Feature

### Step 1: Problem (2 min)
User has excess ingredient, wants to give it away without waste.

### Step 2: Core Decisions (5 min)
- No payment involved (free always)
- Manual pickup (users arrange externally)
- Photos + expiry date optional but encouraged
- Listing expires after 7 days if not claimed

### Step 3: Happy Path (8 min)
```
User journey: "I have tamarind paste I won't use"

1. Open app
2. Tap "List New Item"
3. Select "Give Away"
4. Type "Tamarind paste"
5. Take photo (optional)
6. Enter expiry date (optional)
7. Confirm location (uses their profile location)
8. Post

Listing appears for others to see (sorted by newest).
Other user taps, sees details, contacts via email.
Pickup happens externally.
Done.
```

### Step 4: Open Questions (3 min)
- Should listings auto-expire after 7 days or stay forever?
- Does the giver want to mark "claimed" when someone picks it up, or assume it's taken?
- Should we send a reminder email after 3 days if listing isn't claimed?

### Step 5: Build
Implement the happy path. Let actual usage teach you what else matters.

---

## Context Management: The Rule of 3

**For any feature, answer these 3 questions before starting:**

1. **Problem**: Why do users need this? (1 sentence)
2. **Happy Path**: What's the simplest user flow? (5-10 steps)
3. **Blockers**: What do we NOT know? (2-3 open questions)

If you can't answer all 3 in under 20 minutes, you don't understand the feature yet. Keep iterating until you do.

---

## Cross-Feature Integration: Dependency Map

Instead of duplicating integration questions everywhere, reference this map:

```
Manage Perishables ← → Recommend Recipe
    ↓                        ↓
    └──→ Trade Perishables ←─┘
```

**Integration points to revisit together** (not in MVP, but track):
- Auto-suggest recipes for expiring items?
- Auto-list items to marketplace when expiry is near?
- Search marketplace ingredients while viewing recipes?

Each feature's `open-questions.md` should reference this map, not duplicate the discussion.

---

## How to Avoid Context Overload

### DO:
- ✅ Update decisions as you make them
- ✅ Add open questions as you discover unknowns
- ✅ Link between documents (cross-references)
- ✅ Archive decisions once locked in (move to `design-decisions.md`)
- ✅ Delete questions once answered

### DON'T:
- ❌ Write detailed specifications before validating core decisions
- ❌ Document every possible edge case upfront
- ❌ Keep old questions in `open-questions.md` (archive or delete)
- ❌ Scatter decisions across multiple docs
- ❌ Assume people will read a 10,000-word design document

---

## Document Maintenance

**Weekly**:
- [ ] Review `open-questions.md` for answered questions → move to decision or archive
- [ ] Check `design-decisions.md` for decisions that changed → update rationale

**Monthly**:
- [ ] Review all three features for cross-feature questions that need clarification
- [ ] Check if any decisions conflict with each other

---

*Last updated: 2026-04-17*
