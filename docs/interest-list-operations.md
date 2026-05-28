# Interest List Operations

This runbook documents how to view, export, and clean public landing-page
interest-form submissions stored in Cloudflare D1.

This is an operations-only document. Do not deploy, change DNS, expose RAG,
expose Ollama, expose Chroma, run scraping, or touch corpus, embeddings, vector
data, or private beta services while using it.

## Storage

- D1 database name: `steel_rag_interest`
- Table: `interest_submissions`
- Public form endpoint: `https://steelguitarrag.com/api/interest`
- Expected production response for a stored submission:

```json
{"ok":true,"stored":true,"storage":"d1"}
```

The table stores contact details and operational metadata:

```sql
create table if not exists interest_submissions (
  id text primary key,
  created_at text not null,
  name text,
  email text not null,
  player_level text,
  interests text,
  message text,
  user_agent text,
  ip_hash text,
  status text default 'new',
  spam_score integer default 0,
  admin_notes text,
  notified_at text,
  source text default 'landing_page'
);
```

If the table already exists with only the original capture fields, add the
operational fields manually. Run each statement once against the remote D1
database:

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "alter table interest_submissions add column status text default 'new';"

npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "alter table interest_submissions add column spam_score integer default 0;"

npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "alter table interest_submissions add column admin_notes text;"

npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "alter table interest_submissions add column notified_at text;"

npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "alter table interest_submissions add column source text default 'landing_page';"
```

Check the final table shape:

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "pragma table_info(interest_submissions);"
```

## View Recent Submissions In Cloudflare

1. Open the Cloudflare dashboard.
2. Select the account that owns `steelguitarrag.com`.
3. Go to `Workers & Pages`.
4. Open `D1 SQL Database`.
5. Select the database named `steel_rag_interest`.
6. Open the console, query, or table browser view.
7. Run a read-only query such as the recent-submissions query below.

Do not paste real user emails into issue trackers, AI prompts, chat threads, or
public notes. If you need to share examples, use redacted addresses or test rows.

## Wrangler Setup

Use Wrangler for repeatable local operations:

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "select count(*) as count from interest_submissions;"
```

Use `--remote` for the production Cloudflare D1 database. Leaving it off may
query local development state instead of the public landing-page submissions.

## SQL Queries

### Recent Submissions

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "select created_at, email, name, player_level, interests, message, status, spam_score, notified_at from interest_submissions order by created_at desc limit 50;"
```

### Status Meanings

- `new`: real-looking lead ready for weekly notification.
- `review`: stored, but suspicious enough to inspect before treating as a real
  lead.
- `test`: stored test/example-domain submission.
- `spam`: known junk that should be excluded from normal follow-up.

The interest form and digest jobs do not delete rows automatically.

### Query By Status

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "select created_at, email, name, player_level, interests, message, spam_score, admin_notes from interest_submissions where status = 'new' order by created_at desc limit 50;"

npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "select created_at, email, name, player_level, interests, message, spam_score, admin_notes from interest_submissions where status = 'review' order by created_at desc limit 50;"

npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "select created_at, email, name, player_level, interests, message, spam_score, admin_notes from interest_submissions where status in ('spam', 'test') order by created_at desc limit 50;"
```

### Pending Weekly Digest Rows

This mirrors the scheduled digest candidate query:

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "select created_at, email, name, player_level, interests, message, status, spam_score, notified_at from interest_submissions where (created_at >= datetime('now', '-7 days') or notified_at is null) and lower(coalesce(status, 'new')) in ('new', 'review') order by created_at asc;"
```

### Count All Submissions

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "select count(*) as count from interest_submissions;"
```

### Search By Email

Use an exact lower-case email when checking one address:

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "select id, created_at, email, name, player_level, interests, message from interest_submissions where email = 'person@example.com' order by created_at desc;"
```

Use a partial match when debugging test submissions:

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "select id, created_at, email, name from interest_submissions where email like '%example.com%' order by created_at desc;"
```

### Delete Test Rows

Delete only known test rows. Prefer deleting by exact email or by exact `id`
after reviewing the row.

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "delete from interest_submissions where email in ('ops-smoke@example.com', 'test@example.com');"
```

Confirm cleanup:

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "select count(*) as count from interest_submissions where email in ('ops-smoke@example.com', 'test@example.com');"
```

If you want to keep test rows for audit history instead of deleting them, mark
them as spam/test noise:

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "update interest_submissions set status = 'spam', spam_score = 100, admin_notes = coalesce(admin_notes || char(10), '') || 'manual ops: known test row' where email in ('ops-smoke@example.com', 'test@example.com');"
```

### Export-Friendly Select

Use stable column order and simple aliases for spreadsheet import:

```bash
npx --yes wrangler@latest d1 execute steel_rag_interest --remote \
  --command "select created_at as submitted_at, email, name, player_level, interests, message, id from interest_submissions order by created_at desc;"
```

For a SQL backup/export, use Wrangler's D1 export command:

```bash
mkdir -p private_exports/interest-list

npx --yes wrangler@latest d1 export steel_rag_interest --remote \
  --output private_exports/interest-list/steel_rag_interest_YYYY-MM-DD.sql
```

## Suggested CSV Export Path

Use an ignored local folder for CSV exports:

```text
private_exports/interest-list/steel_rag_interest_YYYY-MM-DD.csv
```

Do not commit exported CSV, SQL, JSON, or spreadsheet files. They contain real
contact information and should stay local/private.

If you export through the Cloudflare dashboard, move the downloaded file into
the same private export folder and keep it out of git.

## Weekly Pushover Digest

The scheduled digest Worker lives at:

```text
workers/interest-digest.js
```

It is intended to be deployed as a standalone Cloudflare Worker with a Cron
Trigger. It does not expose `/api/answer`, does not call the RAG backend, and
does not touch `app.steelguitarrag.com`, Chroma, embeddings, scraping, or corpus
data.

Suggested weekly schedule:

```text
0 14 * * 1
```

Cloudflare Cron Triggers run on UTC. `0 14 * * 1` runs Monday at 14:00 UTC,
which is Monday morning for US Central time: 8 AM during daylight time and 9 AM
during standard time.

### Required Bindings And Secrets

Configure these in Cloudflare before enabling the Cron Trigger:

```text
STEEL_RAG_INTEREST_D1
PUSHOVER_APP_TOKEN
PUSHOVER_USER_KEY
```

Optional manual dry-run secret:

```text
INTEREST_DIGEST_ADMIN_TOKEN
```

Do not put Pushover or admin tokens in source files, docs, issue comments, shell
history snippets, or screenshots.

### Digest Query

Each run queries D1 for rows that are either recent or have never been notified:

```sql
select id, created_at, name, email, player_level, interests, message,
       coalesce(status, 'new') as status,
       coalesce(spam_score, 0) as spam_score,
       admin_notes, notified_at, coalesce(source, 'landing_page') as source
from interest_submissions
where (created_at >= ? or notified_at is null)
  and lower(coalesce(status, 'new')) in ('new', 'review')
order by created_at asc;
```

The `?` value is the ISO timestamp for seven days before the scheduled run.

### Filtering Rules

The Worker does not delete rows automatically.

- Obvious test emails such as `test@example.com` and `ops-smoke@example.com`
  are skipped, marked `status = 'spam'`, and assigned `spam_score = 100`.
- Real-looking submissions stay included in the digest.
- Duplicate emails are grouped together in the Pushover body so one person with
  multiple submissions is easy to review.
- URL-heavy messages are included but marked `status = 'review'` with an
  elevated spam score.
- Blank submissions apart from email are included but marked `status = 'review'`.

### Successful Send Behavior

After Pushover returns success, every included row receives:

```text
notified_at = current scheduled-run timestamp
```

Included rows move to `status = 'notified'` unless they are already in
`status = 'review'`. Review rows keep that status so a human can inspect them.
If Pushover fails, `notified_at` is not updated.

### Manual Dry Run

Dry-run mode returns the digest summary without sending Pushover and without
marking rows notified.

With a Worker dev server and `INTEREST_DIGEST_ADMIN_TOKEN` configured:

```bash
curl -sS \
  -H "Authorization: Bearer $INTEREST_DIGEST_ADMIN_TOKEN" \
  "http://localhost:8787/dry-run"
```

The same handler also accepts:

```text
/?dry_run=1
```

Only use dry run in a trusted environment. The JSON response can include real
user emails and messages.

### Testing The Scheduled Worker

First run local syntax and unit tests:

```bash
node --check workers/interest-digest.js
.venv/bin/python -m pytest tests/test_public_landing_page.py
```

When a Worker project configuration exists for this script, Wrangler can invoke
the scheduled handler locally:

```bash
npx --yes wrangler@latest dev --test-scheduled
curl "http://localhost:8787/__scheduled?cron=0+14+*+*+1"
```

Use a test D1 database or a dry-run path when validating behavior. Do not run
live scraping or any RAG/backend task as part of digest testing.

### Disable The Weekly Job

To disable the alert without changing stored submissions:

1. Open Cloudflare dashboard.
2. Go to `Workers & Pages`.
3. Open the standalone interest digest Worker.
4. Remove or disable the Cron Trigger.
5. Save/deploy the Worker trigger configuration.

If the Worker is configured through Wrangler, remove the `crons` entry from the
Worker config and deploy that config change. Cron Trigger changes can take a few
minutes to propagate.

## Privacy Notes

- Do not commit exports.
- Do not paste real user emails into issues, pull requests, prompts, chat
  threads, screenshots, or public documentation.
- Test rows can be deleted after verification.
- Keep exports on the Mac mini or another private storage location with
  appropriate access controls.
- If a real user asks to be removed, delete their row by exact email and confirm
  with a count/search query.

## Future Improvements

- Admin page for viewing and filtering submissions without raw SQL.
- Turnstile verification before accepting submissions.
- Optional CSV export helper script that writes only to an ignored private
  output directory.
