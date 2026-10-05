# CalcLearners privacy playbook

How the site's promises in `static/privacy.html`, `static/terms.html` and `static/cookies.html`
are kept in practice. Not legal advice; written against PIPEDA's fair information principles.

## What is held, and where

| Data | Where | Kept until |
| --- | --- | --- |
| Visitor ID, display name, progress, quiz scores, notes, streak days | `calclearners.db` on the host | Deleted by the visitor, or 12 months after the browser's or account's last visit (`forget_inactive` in `server.py`) |
| Account username, password hash and recovery-code hash, for visitors who chose to make an account | `accounts` table in `calclearners.db` | Deleted with the account by its owner ("Delete my account"), or 12 months after the account was last used |
| Forum posts, likes and dislikes, reports | `calclearners.db` | Deleted by the author or a moderator; unlinked from the visitor after 12 months |
| CalcBot chat messages | Not stored on the host. The visitor's browser tab keeps them (session storage) | Until the tab is closed |
| Pictures sent to CalcBot | Not stored anywhere. The page shrinks each one and re-saves it as a JPEG before sending, which drops photo details such as location (`chat.js`) | Until the page is left or reloaded |
| Uploaded PDFs kept for AI lessons, and the lessons | `uploads/` and `calclearners.db` | Same as the visitor who uploaded them |
| Abuse-limit counters (include IP addresses and, for sign-in and password-reset tries, the username tried) | `calclearners.db` | A few days |
| Feedback | `calclearners.db` | Same as the visitor who sent it |
| Emails to the contact address | The contact mailbox | Until dealt with |

No names or email addresses are collected by the site. Accounts are optional: a username, a
password and a recovery code. The password and the code are kept only as salted scrypt hashes
(`accounts.py`), so neither can be read back by anyone. Copies of the database (backups,
downloads) count as the data too, hashes included: do not keep them longer than needed.

When `ANTHROPIC_API_KEY` is set, chat messages, pictures attached to them and the text of new forum posts are sent to Anthropic
(`chatbot.py`, `moderation.py`), without the visitor ID or display name. The privacy policy says so in
sections 1 to 3: keep it in step if what is sent ever changes.

## Requests about someone's information

Requests arrive by email or in the "Anything else?" box of the feedback form.

1. Note the date and what was asked in the log below. Answer within 30 days.
2. A request from the feedback form is tied to that browser's visitor ID (the account's, when they were
   signed in), so it can be acted on directly.
3. For an email request, ask for details only that visitor would know (username, display name, what they
   posted) before sharing or changing anything. If it cannot be matched with reasonable confidence, say so.
4. Deletion: point them to "Delete my data" on the My progress page, or "Delete my account" on their
   profile page, or delete the visitor's rows.
5. Forgotten password: they reset it themselves with their recovery code ("Forgot your password?" on the
   sign-in page). Without the code there is no way to check who is asking, so do not set a new password
   or recovery code for anyone on request. They can make a new account.
6. If a request is refused, say why, and mention the Office of the Privacy Commissioner of Canada.

## Reported posts and copyright complaints

- Reported posts show up at `/#/admin` (moderator passcode: `ADMIN_KEY` in `secrets.env`).
- Check reports at least weekly. Take down harassment, personal details, and anything unlawful.
- Copyright complaint by email: take the content down promptly, tell the complainant, note it in the log.

## If information leaks or the site is broken into

1. Contain it: take the site offline or fix the hole, and change `secret_key` and `ADMIN_KEY`. A new
   `secret_key` signs every account out and gives every browser without an account a fresh visitor ID.
2. Work out what was exposed, to how many visitors, and whether it creates a real risk of significant harm.
   If the database may have been copied, the password hashes went with it: the notice should ask people to
   change their password here and anywhere else they used the same one.
3. If it does: post a notice on the site (there is no other way to reach visitors) and report it to the
   Office of the Privacy Commissioner of Canada.
4. Record every incident in the log below, even minor ones, and keep the record for 24 months.

## Log

| Date | Kind (request / report / incident) | What happened | What was done | Closed on |
| --- | --- | --- | --- | --- |
