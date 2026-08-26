# ott-platform-ingestion-pipeline

Studios or CMS operators upload mezzanines through FastAPI into S3 multipart.

Stream a file with `POST /api/v1/upload`. On failure retry with the same file,
`upload_id`, and `key`. Status is `GET /api/v1/status`.
`DELETE /api/v1/delete_all_parts` aborts every in-progress MPU in the bucket.

How to run: [docs/development.md](docs/development.md). Routes: [docs/api.md](docs/api.md).
Target architecture (Postgres, packaging, `/v1`): [docs/HLD.md](docs/HLD.md).

## How it works

1. Client `POST /api/v1/upload` with the file stream. The API creates an S3 MPU
   at `{uuid}/source.{ext}` (or query `key`) and writes parts. On success it
   completes the object.
2. If S3 or the stream fails, the **502** body includes `upload_id` and `key`.
   Client may `GET /api/v1/status?key=&upload_id=` then `POST` again with the
   **same file**, `upload_id`, and `key`. The handler `seek`s past uploaded parts.
3. `DELETE /api/v1/delete_all_parts` aborts every in-progress MPU in the bucket.

Open `/docs` after `uv run uvicorn app.main:app --reload`.

## Documentation

| Document | What it covers |
|---|---|
| [Docs index](docs/Home.md) | Map of the notes |
| [High Level Design](docs/HLD.md) | Target architecture |
| [API](docs/api.md) | Current `/api/v1` routes |
| [Development](docs/development.md) | Run locally, env |
| [Storage](docs/storage.md) | Bucket and keys |
| [Operations](docs/operations.md) | Local run and upload failures |

Diagrams are Mermaid in Markdown. GitHub renders them natively; VS Code / Cursor
preview needs the `bierner.markdown-mermaid` extension.
