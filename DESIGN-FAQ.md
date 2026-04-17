# Design FAQ

Quick answers to common questions. For the full decision log, see [DESIGN-DECISIONS.yaml](DESIGN-DECISIONS.yaml).

## Context Load

**Q: Won't this require a lot of context from the model?**

A: Yes, if the log grows. That's why we use YAML instead of prose — it's ~70% more token-efficient and queryable.

**Strategy**:
- Keep each decision concise (1 line for decision, 1 line for rationale, 1 line for blockers)
- Archive old decisions annually
- Query by `status: pending` or `status: locked` instead of reading everything

Current size: ~30 decisions = ~200 lines of YAML = 400-500 tokens. Manageable.

---

## How to Use

**Reading a decision**:
1. Look up `status: locked` decisions to understand what's already committed
2. Look up `status: pending` decisions to see what's still TBD
3. Check the `blockers` field to see what question needs answering

**Adding a new decision**:
1. Add a new entry to `DESIGN-DECISIONS.yaml`
2. Set `status: pending` until it's locked
3. Move to `status: locked` after you've decided
4. Move to `status: shipped` after it's implemented

---

## FAQ

**Q: What do I do with pending decisions?**

A: These need to be answered before the feature enters development. Pick 3-5 core blockers per feature and lock them in.

**Q: What if a decision changes?**

A: Update the entry, set `status: locked`, and add a note in the `decision` field (e.g., "Changed from X to Y on 2026-04-20").

**Q: What about rejected ideas?**

A: Delete them. A decision log should be current decisions only, not decision history. If you need history, use git.

**Q: How many decisions should I have?**

A: Ideally 3-5 *locked* decisions per feature before development. Everything else is optional detail.

---

**Last updated**: 2026-04-17
