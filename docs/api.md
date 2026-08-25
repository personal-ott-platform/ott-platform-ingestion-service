# API and data model

Back to [HLD](HLD.md). Related: [Messaging](messaging.md), [Storage](storage.md).

The upload API is a **control plane**. Bytes never transit the service. Clients PUT parts directly to S3 using short-lived presigned URLs.

## Primary flow

```mermaid
sequenceDiagram
    autonumber
    participant C as Studio / CMS
    participant A as Upload API
    participant S as S3
    participant D as Postgres
    participant P as Outbox publisher
    participant Q as SQS
    participant W as Worker
    participant CF as CloudFront

    C->>A: POST /v1/uploads (filename, size, content_type)
    A->>S: CreateMultipartUpload (key = ingest/{id}/source)
    A->>D: insert asset uploading
    A-->>C: asset_id, part_size, part_count

    loop batches of parts
        C->>A: POST /parts
        A-->>C: presigned PUTs
        C->>S: PUT part
        S-->>C: ETag
    end

    C->>A: POST /complete (ETags, optional checksum)
    A->>S: CompleteMultipartUpload (idempotent)
    A->>S: HeadObject (actual size vs cap)
    A->>D: queued + outbox row (one txn)
    A-->>C: 200 queued
    D->>P: unpublished outbox rows
    P->>Q: video.upload.completed

    Q->>W: deliver
    W->>D: claim lease
    W->>S: ffprobe via ranged GET or local copy
    W->>W: encode preview rung first
    W->>S: upload preview HLS under assets/
    W->>D: preview_ready (playlist URL is CloudFront)
    W->>W: remaining ladder + audio + subs
    W->>S: upload rest (same prefix)
    W->>D: ready, release lease
    W->>Q: ack

    C->>A: GET /v1/assets/{id}
    A-->>C: status + CloudFront playlist URL
```

Abort: `POST /v1/uploads/{id}/abort` while `uploading`. Incomplete MPUs that are never aborted are cleaned by an S3 lifecycle rule (days).

**Idempotent complete.** If the client retries `POST /complete` after S3 already finished the MPU, treat it as success: `HeadObject`, ensure `queued` + outbox exist, return the same 200. Do not create a second outbox row for the same asset.

## Asset lifecycle

```mermaid
stateDiagram-v2
    [*] --> uploading: POST /v1/uploads
    uploading --> queued: complete + outbox
    uploading --> aborted: POST /abort
    queued --> processing: worker claims lease
    processing --> preview_ready: first playable rung uploaded
    preview_ready --> ready: full package
    processing --> queued: lease expired, redelivered
    preview_ready --> queued: lease expired mid-ladder
    processing --> failed: poison / retries exhausted
    preview_ready --> failed: later rung fails (keep preview objects)
    ready --> [*]
    failed --> [*]
    aborted --> [*]
```

`preview_ready` is a **stable** status, not a blip. While remaining rungs encode, `GET /v1/assets/{id}` still returns the CloudFront playlist URL. Do not drop back to `processing`.

Lease expiry from `preview_ready` requeues the job; the new worker overwrites deterministic keys and must not delete the preview tree until a replacement preview exists.

## HTTP surface (v1)

| Method | Path | Role |
|---|---|---|
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | Readiness (Postgres + publisher loop healthy) |
| `POST` | `/v1/uploads` | Start MPU + asset |
| `POST` | `/v1/uploads/{id}/parts` | Presign parts |
| `POST` | `/v1/uploads/{id}/complete` | Complete MPU, HeadObject, outbox |
| `POST` | `/v1/uploads/{id}/abort` | Abort MPU |
| `GET` | `/v1/assets/{id}` | Status, probe, **CloudFront** playlist URL |

v1.1: `POST /v1/assets/{id}/subtitles` for sidecar SRT/VTT (movies often ship captions separately). Repackage without re-upload is described in [Operations](operations.md).

**Statuses:** `uploading` | `queued` | `processing` | `preview_ready` | `ready` | `failed` | `aborted`.

Auth: **required** even on the mesh (JWT or mTLS). Presign is a write path into `ingest/`.

`GET /v1/assets/{id}` must never return a raw S3 URI for playback. `outputs.playlist_url` is a CloudFront URL under `/assets/{id}/hls/master.m3u8`.

## Data model

### `assets`

| Field | Notes |
|---|---|
| `id` | UUID; S3 prefix |
| `filename` | Display name only — **not** in the object key |
| `content_type`, `declared_size_bytes`, `actual_size_bytes` | HeadObject after complete |
| `checksum` | Optional client checksum verified after complete |
| `source_bucket`, `source_key` | Bucket + `ingest/{id}/source` (bucket in payload so a later split is config) |
| `s3_upload_id` | While uploading |
| `status`, `error` | Lifecycle |
| `lease_owner`, `lease_until` | Encode claim |
| `probe`, `outputs` | JSON (`outputs.playlist_url` is CloudFront) |
| `created_at`, `updated_at` | UTC |

### `outbox`

`id`, `asset_id`, `payload`, `published_at` (null until broker ack). Unique on `asset_id` for `video.upload.completed` so complete retries cannot double-publish.
