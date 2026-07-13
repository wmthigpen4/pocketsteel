create table if not exists interest_digest_deliveries (
  id text primary key,
  window_start text not null,
  window_end text not null,
  content_hash text not null,
  title text not null,
  included_row_ids_json text not null default '[]',
  status text not null default 'pending'
    check (status in ('pending', 'sending', 'failed', 'ambiguous', 'sent')),
  claim_token text,
  claimed_at text,
  lease_expires_at text,
  completed_at text,
  last_error text,
  created_at text not null,
  updated_at text not null,
  unique (window_start, window_end)
);

create table if not exists interest_digest_delivery_parts (
  delivery_id text not null,
  part_index integer not null check (part_index >= 0),
  part_count integer not null check (part_count > 0),
  content_hash text not null,
  title text not null,
  message text not null,
  status text not null default 'pending'
    check (status in ('pending', 'sending', 'failed', 'ambiguous', 'sent')),
  attempts integer not null default 0 check (attempts >= 0),
  attempt_started_at text,
  sent_at text,
  last_error text,
  created_at text not null,
  updated_at text not null,
  primary key (delivery_id, part_index),
  foreign key (delivery_id) references interest_digest_deliveries(id) on delete cascade
);

create index if not exists interest_digest_deliveries_status_window_idx
  on interest_digest_deliveries(status, window_start, window_end);

create index if not exists interest_digest_delivery_parts_status_idx
  on interest_digest_delivery_parts(delivery_id, status, part_index);
