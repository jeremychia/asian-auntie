# Documentation Index

Quick reference for all docs. Start here.

## Core Reference

**New to the project?** Read in this order:
1. [Problem statement: Manage Perishables](manage-perishables/problem-statement.md) — What are we solving?
2. [Decisions: Manage Perishables](manage-perishables/decisions.yaml) — What did we decide?
3. [Features: Manage Perishables](manage-perishables/features.md) — What are we building?
4. [Flows: Manage Perishables](manage-perishables/flows.yaml) — How do users actually use this?

**Want to understand a specific feature?** Go to its folder:
- [Manage Perishables](manage-perishables/README.md)
- [Recommend Recipe](recommend-recipe/README.md)
- [Trade Perishables](trade-perishables/README.md)

---

## By Role

### Product Manager / Designer
- [Problem statements](manage-perishables/problem-statement.md) — User research
- [Decisions](manage-perishables/decisions.yaml) — Constraints, tradeoffs & unintended consequences
- [Open questions](manage-perishables/questions.yaml) — What still needs deciding (including first principles)
- [Flows](manage-perishables/flows.yaml) — Happy paths, decision points & edge cases

### Developer
- [Features](manage-perishables/features.md) — What to build & acceptance criteria
- [Flows](manage-perishables/flows.yaml) — How users interact with the feature
- [Decisions](manage-perishables/decisions.yaml) — Why we made choices & what could go wrong
- [Open questions](manage-perishables/questions.yaml) — Known unknowns to design around

### Collaborator (joining mid-project)
1. [DESIGN-FAQ.md](../DESIGN-FAQ.md) — Context loading strategy (this answers your questions)
2. [DOCUMENTATION-STRATEGY.md](DOCUMENTATION-STRATEGY.md) — How we organize docs
3. Then read feature README.md for your area

---

## Strategic Guides

### Decision Making
- [DOCUMENTATION-STRATEGY.md](DOCUMENTATION-STRATEGY.md) — How to avoid context overload
- [DESIGN-FAQ.md](../DESIGN-FAQ.md) — Why we design iteratively using YAML (not prose)

### Understanding Risks
- [Decisions](manage-perishables/decisions.yaml) — Each decision includes unintended consequences & mitigations
- [Questions](manage-perishables/questions.yaml) — Critical questions organized by first principles, inversion, & failure modes

### Building Features
- [Flows](manage-perishables/flows.yaml) — Happy paths, decision points, edge cases
- [Features](manage-perishables/features.md) — Detailed acceptance criteria

### Evaluating Scope
- [Questions](manage-perishables/questions.yaml) — What we're still debating (organized by impact)
- [Decisions](manage-perishables/decisions.yaml) — What we've already locked in with rationale

---

## Document Structure

Each feature folder has:

```
feature/
├── README.md              (navigation hub)
├── problem-statement.md   (why, who, what problem)
├── decisions.yaml         (locked decisions + rationale + unintended consequences)
├── questions.yaml         (open questions organized by first principles & failure modes)
├── flows.yaml             (user flows: happy path, decision points, edge cases)
└── features.md            (detailed specs + acceptance criteria)
```

**Master docs** (not in feature folders):
- `DESIGN-FAQ.md` — Why we use YAML, how to manage context & avoid overload
- `DOCUMENTATION-STRATEGY.md` — Philosophy & maintenance guidelines

---

## How to Use These Docs

### If you're making a decision:
→ Check `decisions.yaml` to see if it's already made
→ If not, check `questions.yaml` to understand the tradeoffs
→ Once decided, update `decisions.yaml` with rationale + unintended consequences

### If you're building a feature:
→ Read `features.md` for acceptance criteria
→ Reference `flows.yaml` for the happy path
→ Check `decisions.yaml` for why we chose this approach
→ Review `questions.yaml` for known risks to design around

### If you're clarifying scope:
→ Check `features.md` for what's in MVP
→ Check `questions.yaml` for what's deferred and why
→ Check `decisions.yaml` for why we chose scope (including risks)

### If you're reviewing design:
→ Read `problem-statement.md` to understand context
→ Check `decisions.yaml` for decisions + unintended consequences
→ Reference `flows.yaml` for user impact
→ Ask: Does the flow match the decisions? Are risks being mitigated?

### If you're evaluating risk:
→ Read `decisions.yaml` — each decision includes unintended consequences
→ Review `questions.yaml` for first principles questions
→ Ask: What could go wrong? Are we thinking inversely?

---

## Maintenance

**Weekly**: 
- [ ] Review `questions.yaml` — are any answered? Move to `decisions.yaml` with full context.
- [ ] Update any docs that had decisions made during the week

**Monthly**:
- [ ] Check for conflicts between feature decisions
- [ ] Audit links — are cross-references still valid?
- [ ] Review unintended consequences — are any emerging in actual usage?

---

## Current Status

| Feature | Problem | Decisions | Features | Flows | Questions |
|---------|---------|-----------|----------|-------|-----------|
| Manage Perishables | ✅ | 5 locked | ✅ | ✅ | 25 |
| Recommend Recipe | ✅ | 4 locked | ✅ | ✅ | 28 |
| Trade Perishables | ✅ | 5 locked | ✅ | ✅ | 39 |

**Next steps**:
1. Choose 3 "core blockers" per feature to answer first
2. Build with decisions + flows as your spec
3. Learn from implementation, update decisions with real findings

---

*Last updated: 2026-04-17*
