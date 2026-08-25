# Messaging and leases

Back to [HLD](HLD.md). Related: [API](api.md).

## Decisions

| Aspect | Decision |
|---|---|
| Broker (v1) | **Amazon SQS**. Visibility timeout is the lease with less custom code. |
| RabbitMQ | Only if it is already the platform broker **and** consumer timeout / heartbeats cover a **multi-hour** encode. Default RMQ timeouts will kill movie jobs. |
| Event | `video.upload.completed` only. There is no second `video.processing` event. |
| Payload | `asset_id`, `source_bucket`, `source_key`, `size_bytes` (from HeadObject), `occurred_at` |
| Publish | **Outbox only** — never publish in the HTTP handler after a second commit |
| Publisher | Dedicated loop (sidecar on the API deployment, or its own deployment). Polls `published_at IS NULL`, publishes, then sets `published_at`. |
| Delivery | At-least-once |
| Prefetch / concurrency | 1 message per worker consumer |
| DLQ | After N failed leases / poison probe |

Catalog notifications (`asset.preview_ready`, `asset.ready`) are a separate product decision — see [open questions](HLD.md#open-questions). Do not overload `video.upload.completed` for that.

## Outbox

1. `POST /complete` writes `assets.status = queued` and one outbox row in the **same transaction**.
2. Unique constraint on `(asset_id, event_type)` for this event so retries cannot insert a second row.
3. Publisher is **not** the request thread. HTTP 200 means durable complete, not “already on SQS”.
4. If SQS publish succeeds but `published_at` update fails, the next poll republishes; workers must be idempotent.

## Leases

Columns: `lease_owner`, `lease_until`.

Claim **only** rows that are still in-flight:

```sql
UPDATE assets
SET lease_owner = :worker_id,
    lease_until = now() + :lease_ttl,
    status = 'processing'
WHERE id = :asset_id
  AND status IN ('queued', 'processing', 'preview_ready')
  AND (lease_until IS NULL OR lease_until < now())
RETURNING *;
```

Do **not** claim on `lease_until < now()` alone. That can steal `ready`, `failed`, or `aborted`.

| Rule | Behavior |
|---|---|
| Heartbeat | Worker extends `lease_until` every N minutes while FFmpeg runs |
| Preview | After preview upload, set `preview_ready` and keep the lease; do not clear it |
| Ack | After `ready` or `failed` is persisted |
| Duplicate | If `ready`, ack and skip. If another worker holds a live lease, nack without steal |
| SQS visibility | Extend (change-message-visibility) in lockstep with `lease_until` so the broker does not redeliver a live encode |

`preview_ready` rows with an expired lease may be claimed again to finish the ladder. Overwrite deterministic keys; keep the existing preview tree until the new preview is uploaded.
