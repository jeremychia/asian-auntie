# Memory Index

- [No Claude co-author in commits](feedback_no_claude_coauthor.md) — Never add Co-Authored-By: Claude to git commit messages
- [Pico CSS button height fix](feedback_pico_button_height.md) — Use `<span role="button">` instead of `<button>` to avoid Pico CSS forcing height-expanding styles
- [Flask test app context isolation](feedback_flask_test_app_context.md) — Push fresh inner app context in db fixture so each test gets its own Flask g, preventing stale g.\_login_user across tests
