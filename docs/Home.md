# Ingestion pipeline docs

Notes for `ott-platform-ingestion-pipeline`. Topic pages describe **what is implemented**. Target architecture lives in the [HLD](HLD.md).

| Document | What it covers |
|---|---|
| [High Level Design](HLD.md) | Target architecture, assumptions, goals, open questions |
| [API](api.md) | `POST /api/v1/upload`, status, delete-all MPUs |
| [Development](development.md) | How to run, layout, env |
| [Storage](storage.md) | Current bucket and object keys |
| [Operations](operations.md) | Local run and upload failure handling |

## Service at a glance

| Aspect | Value |
|---|---|
| Purpose | Multipart ingest of mezzanines into S3 |
| Upload | FastAPI; `POST /api/v1/upload`; resume with `upload_id` + `key`; `GET /api/v1/status` |
| Storage | One MinIO/S3 bucket; key `{uuid}/source.{ext}` or client `key` |
| Auth | None |

Diagrams are Mermaid in fenced blocks. Open questions live in the [HLD](HLD.md#open-questions).
