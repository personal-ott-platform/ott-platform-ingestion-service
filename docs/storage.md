# Storage

Back to [HLD](HLD.md). Related: [Development](development.md), [API](api.md).

One MinIO/S3 bucket (`S3_BUCKET`). The upload API writes `{uuid}/source.{ext}` or a client-supplied query `key`.

Create the bucket to match `S3_BUCKET` before the first `CreateMultipartUpload`. Compose also starts Postgres; the upload API does not use it. Env: [Development](development.md).

Target prefixes (`ingest/`, `assets/`), CloudFront, and IAM: [HLD](HLD.md).
