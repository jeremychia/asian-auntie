---
name: feedback-flask-test-app-context
description: Push a fresh inner app context in the function-scoped db fixture so each test gets its own Flask g (avoids stale g._login_user across tests)
metadata:
  type: feedback
---

Push a fresh inner app context in the function-scoped `db` fixture in `tests/conftest.py`.

**Why:** Flask's `g` is stored on the app context. With a session-scoped outer `with _app.app_context():`, all requests share the same `g`. `login_user()` sets `g._login_user`, which persists across tests — causing the deleted user from a previous test to appear "already authenticated", short-circuiting login and leaking stale state into subsequent tests.

**How to apply:** In the `db` fixture, do `ctx = app.app_context(); ctx.push()` before yield and `ctx.pop()` in teardown. This gives each test a fresh inner app context (and thus a fresh `g`), while the outer session-scope context still handles schema creation/teardown.

Related: [[feedback-testing-staticpool]] — StaticPool fix for in-memory SQLite visibility.
