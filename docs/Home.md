# Ingestion pipeline docs

Design notes for `ott-platform-ingestion-pipeline` — content ingest and HLS packaging.

| Document | What it covers |
|---|---|
| [High Level Design](HLD.md) | Purpose, architecture, assumptions, goals, implementation mapping |
| [API and data model](api.md) | Multipart control plane, asset lifecycle, schema |
| [Storage](storage.md) | One S3 bucket, prefixes, CloudFront, IAM, lifecycle |
| [Messaging and leases](messaging.md) | Outbox, SQS, claim rules, ack |
| [Packaging](packaging.md) | HLS tree, CMAF, preview rung, encoder I/O |
| [Operations](operations.md) | Deploy, NFRs, failures, security, takedown, repackage |

## Service at a glance

| Aspect | Value |
|---|---|
| Purpose | Multipart ingest of movie-sized mezzanines, then HLS packaging |
| Upload plane | FastAPI on EKS; presigned S3 multipart (client-direct bytes) |
| Async seam | Transactional outbox → SQS event `video.upload.completed` |
| Processing | Leased worker; FFmpeg v1 (MediaConvert later); preview rung then full ladder |
| Storage | **One S3 bucket**, prefixes `ingest/` and `assets/`; CloudFront origin on `assets/` only |
| Playlist URL | CloudFront, never a raw S3 key |
| Status | Proposed — repo is still a stub |

Diagrams are Mermaid in fenced blocks. The HLD is the spine; topic notes are the source of truth for that topic. Do not reintroduce four output buckets or a second `video.processing` event.

Open questions live in the [HLD](HLD.md#open-questions).
