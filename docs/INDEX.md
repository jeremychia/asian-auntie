# Documentation Index

Quick reference for all docs. Start here.

## Core Reference

**New to the project?** Read in this order:

1. [Problem statement: Manage Perishables](manage-perishables/problem-statement.md) — What are we solving?
2. [MVP Checklist: Manage Perishables](manage-perishables/mvp-checklist.yaml) — What are we building?
3. [Flows: Manage Perishables](manage-perishables/flows.yaml) — How do users interact with features?
4. [Decisions: Manage Perishables](manage-perishables/decisions.yaml) — Why did we choose this approach?

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

- [MVP Checklist](manage-perishables/mvp-checklist.yaml) — What to build & acceptance criteria
- [Flows](manage-perishables/flows.yaml) — Step-by-step user interactions, edge cases, data specs
- [Decisions](manage-perishables/decisions.yaml) — Why we made choices & what could go wrong
- [Open questions](manage-perishables/questions.yaml) — Known unknowns to design around

### Collaborator (joining mid-project)

1. [DESIGN-FAQ.md](../DESIGN-FAQ.md) — Context loading strategy (this answers your questions)
2. [DOCUMENTATION-STRATEGY.md](DOCUMENTATION-STRATEGY.md) — How we organize docs
3. Then read feature README.md for your area

---

## Engineering

### Setup & Running the App

- [Engineering Setup](engineering/setup.md) — prerequisites, local dev, env vars, phone access, cloud deploy

### Design

- [Design System](engineering/design-system.md) — colour palette, typography, spacing, component specs

### Auth

- [Auth Flows](auth/flows.yaml) — register, login, logout, token refresh — happy paths, decision points, edge cases

---

## Strategic Guides

### Decision Making

- [DOCUMENTATION-STRATEGY.md](DOCUMENTATION-STRATEGY.md) — How to avoid context overload
- [DESIGN-FAQ.md](../DESIGN-FAQ.md) — Why we design iteratively using YAML (not prose)

### Understanding Risks

- [Decisions](manage-perishables/decisions.yaml) — Each decision includes unintended consequences & mitigations
- [Questions](manage-perishables/questions.yaml) — Critical questions organized by first principles, inversion, & failure modes

### Building Features

- [MVP Checklist](manage-perishables/mvp-checklist.yaml) — Acceptance criteria & scope
- [Flows](manage-perishables/flows.yaml) — Happy paths, decision points, edge cases, data specs

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
├── flows.yaml             (user flows: happy path, decision points, edge cases, data specs)
├── mvp-checklist.yaml     (MVP scope + acceptance criteria)
└── future-features.yaml   (v2+ roadmap with priorities)
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

→ Read `mvp-checklist.yaml` for acceptance criteria
→ Reference `flows.yaml` for step-by-step interactions, edge cases, data specs
→ Check `decisions.yaml` for why we chose this approach
→ Review `questions.yaml` for known risks to design around

### If you're clarifying scope:

→ Check `mvp-checklist.yaml` for what's in MVP & what's excluded
→ Check `future-features.yaml` for v2+ roadmap
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

| Feature            | Problem | MVP | Flows | Decisions | Future | Questions |
| ------------------ | ------- | --- | ----- | --------- | ------ | --------- |
| Manage Perishables | ✅      | ✅  | ✅    | 5 locked  | ✅     | 25        |
| Recommend Recipe   | ✅      | ✅  | ✅    | 4 locked  | ✅     | 28        |
| Trade Perishables  | ✅      | ✅  | ✅    | 5 locked  | ✅     | 39        |

**How to move forward**:

1. For implementation: Use `mvp-checklist.yaml` + `flows.yaml` as the spec
2. For scope decisions: Reference `mvp-checklist.yaml` to see what's in/out
3. For learning & iteration: Update `decisions.yaml` with real-world findings as you build

---

_Last updated: 2026-04-17 — Restructured: removed features.md, added mvp-checklist.yaml & future-features.yaml_
