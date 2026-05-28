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
  ip_hash text
);
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
  --command "select created_at, email, name, player_level, interests, message from interest_submissions order by created_at desc limit 50;"
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
- Notification email when a new interest form is submitted.
- Turnstile verification before accepting submissions.
- Duplicate email handling, such as update existing row, ignore duplicates, or
  store a latest-submission timestamp.
- Optional CSV export helper script that writes only to an ignored private
  output directory.
