# Storage

Back to [HLD](HLD.md). Related: [Packaging](packaging.md), [Operations](operations.md).

**v1 default: one S3 bucket**, two prefixes. HLS video, audio, and subtitles stay on the **same host** so relative playlist URIs work. Ingested mezzanines share that bucket; they are isolated by prefix, IAM, lifecycle, and CloudFront origin path — not by a second bucket.

## Layout

Bucket name (example): `ott-media`

```text
ott-media
├── ingest/{asset_id}/source          # private mezzanine
└── assets/{asset_id}/
    └── hls/
        ├── master.m3u8
        ├── video/{360p,480p,720p,1080p}/index.m3u8 + segments
        ├── audio/{lang}_{codec}/index.m3u8 + segments
        └── subtitles/{lang}_{role}.vtt
```

| Prefix | Contents | Writers | Readers | Lifecycle |
|---|---|---|---|---|
| `ingest/{asset_id}/source` | Private mezzanine | API (presign MPU) | Workers only (IRSA) | Glacier / expire after QC |
| `assets/{asset_id}/hls/**` | master + video + audio + VTT | Workers only | CloudFront OAC | Long TTL; no Glacier |

Keep the mezzanine after pack for QC and [repackage](operations.md). Do not expire it on `ready`.

## CloudFront

- Origin is this bucket with **origin path `/assets/`** (or a cache behavior that only matches `/assets/*`).
- Never origin the bucket root. A guessed `ingest/{asset_id}/source` URL must not be a CDN object.
- OAC `GetObject` only on `assets/*`.
- Long cache TTL on segments; shorter TTL or cache-bust query on `master.m3u8` if playlists are rewritten during preview → ready.
- Playback URLs returned by the API are CloudFront URLs, never S3.

## IAM (prefix-scoped)

| Principal | Allow |
|---|---|
| API role | `CreateMultipartUpload` / presign PUT parts / complete / abort on `ingest/*` only |
| Worker role | `GetObject` on `ingest/*`; `PutObject` (and overwrite) on `assets/*`; `GetObject` on `assets/*` for resume |
| CloudFront OAC | `GetObject` on `assets/*` only |
| Humans / QC | Separate role for `ingest/*` read; not the API role |

Block public access on the bucket. CORS only as needed for browser MPU to `ingest/` (studios); player traffic goes through CloudFront.

## Notifications and lifecycle

- Event notifications (if used) filter by prefix. Do not fire encode jobs off `assets/` puts.
- Abort incomplete MPUs after N days (S3 abort-incomplete-multipart-upload).
- Transition `ingest/` to Glacier after the QC window. Never Glacier `assets/`.

## What not to do

| Layout | Verdict |
|---|---|
| Four buckets (source, video, audio, subs) | Reject — relative playlist URIs break; CTV CORS/cookies fail |
| One bucket, CloudFront on the whole bucket | Reject — masters become origin objects |
| Two buckets (ingest vs packaged) | Optional later — only if legal needs the CDN origin to be physically unable to read masters even with a mis-set origin path |

Event payloads still carry `source_bucket` + `source_key` so a later split is configuration, not a schema change.

## Local development

One MinIO bucket with the same prefixes. Do not run a two-bucket compose for v1.
