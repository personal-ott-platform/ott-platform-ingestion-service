# Packaging

Back to [HLD](HLD.md). Related: [Storage](storage.md).

Movie VOD packaging produces **one HLS tree** under `assets/{asset_id}/hls/`. Do not split video, audio, or subtitles across hosts.

## v1 defaults

| Choice | v1 default | Movie note |
|---|---|---|
| Container | **CMAF / fMP4** (`.m4s` + fMP4 playlists) | Avoids a catalog re-encode if DRM lands within a year. MPEG-TS only if product confirms no DRM for 12+ months. |
| Video | H.264, ladder 360–1080, no upscale | 4K / HDR = managed encoder, not the first FFmpeg image |
| Audio | AAC stereo from first track | Plan `audio/{lang}` groups; 5.1 later |
| Segments | 6 s, GOP aligned | Independent segments for ABR |
| Order | **Preview rung first**, then rest | Hours of 1080p must not block first playable |
| Subs | Extract embedded WebVTT as complete files; sidecar API next | Feature films often ship captions separately |
| Encoder | FFmpeg on CPU nodes for 1080p SDR | MediaConvert (or similar) as the same worker backend later — same S3 layout, same asset row |

DRM **license servers** stay out of this service. CMAF is the packaging choice so Widevine/FairPlay can attach later without restreaming the catalog.

## Preview then ladder

1. Probe the source.
2. Encode and upload one playable rung (e.g. 480p or 720p) plus enough audio/subs to play.
3. Persist `preview_ready` and a CloudFront `master.m3u8` URL.
4. Encode remaining rungs into the **same** prefix; rewrite `master.m3u8` when the full ladder is up.
5. Persist `ready`, release lease, ack.

`GET /v1/assets/{id}` keeps returning the playlist URL throughout step 4.

## Encoder I/O

Do not size workers as `2 × mezzanine + all rungs` by default.

| Source | Approach |
|---|---|
| Progressive MP4 with a usable index | FFmpeg HTTP + ranged GET (presigned) from S3 |
| MOV / poorly interleaved / IMF | Local copy (or fuse/mount) — seek will otherwise thrash |
| Probe | `ffprobe` via ranged read when possible |

“Never download” is a goal, not a guarantee. Document scratch disk on the node when local copy is required; still avoid keeping every output rung on disk if S3 upload can stream per rendition.

## Encoder path

Start with FFmpeg on CPU nodes. When queue time or 4K shows up, swap the worker backend to MediaConvert. API, asset row, and prefix layout do not change.
