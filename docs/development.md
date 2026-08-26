# Development

Back to [Home](Home.md). Contract: [API](api.md). Architecture: [HLD](HLD.md).

FastAPI streams a mezzanine into S3/MinIO multipart. Resume uses query `upload_id` + `key` and `seek` on the incoming `UploadFile`. Postgres is in Compose but is not used by the app.

Run uvicorn from the **repo root** so `app.settings.Settings` can load `.env`.

```bash
docker compose up -d
# Create the MinIO bucket named in S3_BUCKET (e.g. videos) before the first upload.
uv run uvicorn app.main:app --reload --timeout-keep-alive 3600
```

Open `/docs` (or `GET /`, which redirects there).

## HTTP

Routes are **`/api/v1/...`**, from `APIRouter(prefix='/api/v1')` in `app/api/v1/uploads.py`.

| Method | Path |
|---|---|
| `POST` | `/api/v1/upload` |
| `GET` | `/api/v1/status` |
| `DELETE` | `/api/v1/delete_all_parts` |

## Layout

```text
ott-platform-ingestion-pipeline/
  .env                      # local secrets (gitignored)
  docker-compose.yml        # MinIO + Postgres (Postgres unused by the app)
  app/
    main.py                 # FastAPI app, include uploads router, GET / → /docs
    settings.py             # pydantic-settings from .env
    api/
      v1/
        uploads.py          # S3 client + POST upload, GET status, DELETE all MPUs
```

S3 calls live in the router (`boto3.client` at import).

| Module | Does |
|---|---|
| `api/v1/uploads.py` | HTTP, MPU create/list/upload/complete/abort, resume `seek` |
| `settings.py` | `S3_*`, `PART_SIZE_BYTES` |
| `main.py` | App + router + docs redirect |

## Config

`.env` at the **repo root**. `app/settings.py` uses `env_file=".env"`.

| Variable | Purpose |
|---|---|
| `S3_ENDPOINT_URL` | MinIO, e.g. `http://localhost:9000` |
| `S3_ACCESS_KEY`, `S3_SECRET_KEY` | Local MinIO root user |
| `S3_BUCKET`, `S3_REGION` | One bucket (create it in MinIO before `CreateMultipartUpload`) |
| `PART_SIZE_BYTES` | Optional; default **8 MiB**. Every part except the last must be ≥ 5 MiB |

S3 addressing uses path style when `S3_ENDPOINT_URL` starts with `http`.

Raise proxy/uvicorn keep-alive timeouts for a long `POST /api/v1/upload`. Resume is a **second** POST with the same file, `upload_id`, and `key`.

## Local dependencies

`docker-compose.yml`: MinIO (`9000` / console `9001`) and Postgres 16 (`5432`, database `video`). The upload API talks only to MinIO. Create **one** bucket matching `S3_BUCKET`.

## Upload behavior

1. **New upload** — `CreateMultipartUpload` at `key` or `{uuid}/source.{suffix}`, then `UploadPart` in `PART_SIZE_BYTES` chunks, then complete.
2. **Resume** — `ListParts`, `file.file.seek(len(parts) * PART_SIZE_BYTES)`, upload remaining parts, complete. Client must send **`key`** as well as `upload_id`.
3. **Status** — `ListParts` for `key` + `upload_id`.
4. **Delete all** — abort every in-progress MPU in the bucket.

Filename suffix is taken from `filename.split('.')[-1]` (case-sensitive). On S3 error the MPU is left open (except the empty-file abort). Allowed extensions: `mp4`, `mkv`.

S3 requires every part except the last to be at least **5 MiB**.
