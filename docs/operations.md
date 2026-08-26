# Operations

Back to [HLD](HLD.md). Related: [Storage](storage.md), [API](api.md).

Local stack: MinIO (one bucket) + Postgres in Compose (unused by the API). Use a short test file. See [Development](development.md).

## Failure handling

| Failure | Handling |
|---|---|
| Stream / S3 error mid-upload | Do not abort MPU; **502** with `upload_id` and `key`; retry `POST /api/v1/upload` with file + both |
| Empty upload | Abort MPU; **500** |
| `DELETE /api/v1/delete_all_parts` | Aborts every in-progress MPU in the bucket |

Do not log credentials. Routes are unauthenticated.

Target deploy shape, NFRs, packaging failures, and takedown: [HLD](HLD.md).
