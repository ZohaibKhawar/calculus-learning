# CalcLearners privacy playbook

How the site's promises in `static/privacy.html`, `static/terms.html` and `static/cookies.html`
are kept in practice. Not legal advice; written against PIPEDA's fair information principles.

## What is held, and where

| Data | Where | Kept until |
| --- | --- | --- |
| Visitor ID, display name, progress, quiz scores, notes, streak days | `calclearners.db` on the host | Deleted by the visitor, or 12 months after the browser's last visit (`forget_inactive` in `server.py`) |
| Forum posts, likes and dislikes, reports | `calclearners.db` | Deleted by the author or a moderator; unlinked from the visitor after 12 months |
| CalcBot chat messages | Not stored on the host. The visitor's browser tab keeps them (session storage) | Until the tab is closed |
| Uploaded PDFs kept for AI lessons, and the lessons | `uploads/` and `calclearners.db` | Same as the visitor who uploaded them |
| Abuse-limit counters (include IP addresses) | `calclearners.db` | A few days |
| Feedback | `calclearners.db` | Same as the visitor who sent it |
| Emails to the contact address | The contact mailbox | Until dealt with |

No names, email addresses or passwords are collected by the site. Copies of the database
(backups, downloads) count as the data too: do not keep them longer than needed.

When `ANTHROPIC_API_KEY` is set, chat messages and the text of new forum posts are sent to Anthropic
(`chatbot.py`, `moderation.py`), without the visitor ID or display name. The privacy policy says so in
sections 1 to 3: keep it in step if what is sent ever changes.

## Requests about someone's information

Requests arrive by email or in the "Anything else?" box of the feedback form.

1. Note the date and what was asked in the log below. Answer within 30 days.
2. A request from the feedback form is tied to that browser's visitor ID, so it can be acted on directly.
3. For an email request, ask for details only that visitor would know (display name, what they posted)
   before sharing or changing anything. If it cannot be matched with reasonable confidence, say so.
4. Deletion: point them to "Delete my data" on the My progress page, or delete the visitor's rows.
5. If a request is refused, say why, and mention the Office of the Privacy Commissioner of Canada.

## Reported posts and copyright complaints

- Reported posts show up at `/#/admin` (moderator passcode: `ADMIN_KEY` in `secrets.env`).
- Check reports at least weekly. Take down harassment, personal details, and anything unlawful.
- Copyright complaint by email: take the content down promptly, tell the complainant, note it in the log.

## If information leaks or the site is broken into

1. Contain it: take the site offline or fix the hole, and change `secret_key` and `ADMIN_KEY`.
2. Work out what was exposed, to how many visitors, and whether it creates a real risk of significant harm.
3. If it does: post a notice on the site (there is no other way to reach visitors) and report it to the
   Office of the Privacy Commissioner of Canada.
4. Record every incident in the log below, even minor ones, and keep the record for 24 months.

## Log

| Date | Kind (request / report / incident) | What happened | What was done | Closed on |
| --- | --- | --- | --- | --- |
