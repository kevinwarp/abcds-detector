# AI Creative Review — Internal API Reference

**Base URL:** `https://app.aicreativereview.com`  
**Version:** 2.1  
**Internal Use Only**

---

## API Key

```
YOUR_KEY_HERE
```

> **To generate your key:** Log into `https://app.aicreativereview.com`, open DevTools console (⌘+Option+J), and run:
> ```js
> const r = await fetch('/auth/api-keys', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'internal-integration'})});
> const d = await r.json(); console.log(d.key);
> ```
> Replace `YOUR_KEY_HERE` above with the `acr_...` value. **The key is shown once — save it.**

---

## Authentication

Pass the API key as a header on every request:

```
X-API-Key: acr_<your-key>
```

---

## Quick Start

### Analyze a video file
```bash
curl -X POST https://app.aicreativereview.com/api/evaluate_file \
  -H "X-API-Key: acr_<your-key>" \
  -F "file=@ad.mp4"
```

### Analyze a YouTube ad
```bash
curl -X POST https://app.aicreativereview.com/api/evaluate_file \
  -H "X-API-Key: acr_<your-key>" \
  -F "url=https://www.youtube.com/watch?v=VIDEO_ID"
```

### Get results JSON
```bash
curl https://app.aicreativereview.com/api/results/{report_id} \
  -H "X-API-Key: acr_<your-key>"
```

---

## Endpoints

### POST /api/evaluate\_file — Analyze a Video (Recommended)

Upload an MP4 file or YouTube URL. Returns full analysis as a single JSON response — best for programmatic use.

**Request** (`multipart/form-data`):

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `file` | MP4 | one of `file`/`url` | Max 32 MB, max 60 s |
| `url` | string | one of `file`/`url` | YouTube only |
| `use_abcd` | bool | `true` | ABCD framework scoring |
| `use_shorts` | bool | `false` | YouTube Shorts heuristics |
| `use_ci` | bool | `true` | Creative Intelligence features |

**Response `200`:**
```json
{
  "report_id": "a1b2c3d4",
  "report_url": "https://app.aicreativereview.com/report/a1b2c3d4",
  "duration_seconds": 30.0,
  "tokens_used": 300,
  "credits_remaining": 2700,
  "abcd": {
    "score": 82,
    "features": [
      { "id": "abcd_attention", "name": "Attention", "detected": true, "confidence": 0.91 }
    ]
  },
  "persuasion": { "density": 74, "features": [ ... ] },
  "accessibility": { "score": 68, "features": [ ... ] },
  "predictions": { "overall_score": 77 },
  "brand_intelligence": { "brand_name": "Acme", "product_service": "Consumer App" },
  "scenes": [
    {
      "scene_number": 1,
      "start_time": "0:00",
      "end_time": "0:05",
      "description": "Opening hook with product reveal",
      "transcript": "Introducing the new...",
      "emotion": "excited",
      "sentiment_score": 0.82
    }
  ]
}
```

---

### POST /api/upload — Upload Video (Two-Step Flow)

Upload first, then evaluate separately. Use this when you want a GCS URI to reuse across multiple evaluation configs.

**Request** (`multipart/form-data`):

| Field | Type | Notes |
|-------|------|-------|
| `file` | MP4 | Max 32 MB, max 60 s |

**Response `200`:**
```json
{
  "status": "uploaded",
  "filename": "ad.mp4",
  "gcs_uri": "gs://bucket/ad.mp4",
  "size_mb": 12.4
}
```

---

### POST /api/evaluate — Analyze with SSE Stream

Evaluates a GCS URI or YouTube URL and streams real-time progress via Server-Sent Events.

**Request** (`multipart/form-data`):

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `gcs_uri` | string | required | GCS URI or YouTube URL |
| `use_abcd` | bool | `true` | |
| `use_shorts` | bool | `false` | |
| `use_ci` | bool | `true` | |

**Event stream:**
```
data: {"step": "render_estimate", "estimated_render_seconds": 138}
data: {"step": "extracting_frames", "message": "...", "pct": 10}
data: {"step": "analyzing", "message": "...", "pct": 60}
data: {"step": "complete", "pct": 100, "data": { ...full results... }}
data: {"step": "error", "message": "..."}
```

---

### POST /api/evaluate\_compare — Compare Ad Variants

Evaluate 2–5 videos in parallel. Returns a winner recommendation with feature-level diffs.

**Request** (`application/json`):
```json
{
  "video_uris": ["gs://bucket/v1.mp4", "gs://bucket/v2.mp4"],
  "use_abcd": true,
  "use_ci": true
}
```

| Field | Type | Notes |
|-------|------|-------|
| `video_uris` | array | 2–5 GCS URIs or YouTube URLs |
| `use_abcd` | bool | ABCD scoring |
| `use_ci` | bool | Creative Intelligence |

**Response `200`:**
```json
{
  "comparison_id": "x1y2z3w4",
  "comparison": {
    "recommended_winner": {
      "index": 0,
      "video_name": "v1.mp4",
      "justification": "v1.mp4 leads with performance score 79, ABCD 82%..."
    },
    "variants": [
      { "index": 0, "video_name": "v1.mp4", "abcd_score": 82, "performance_score": 79 },
      { "index": 1, "video_name": "v2.mp4", "abcd_score": 78, "performance_score": 75 }
    ],
    "deltas": [{ "vs": "v2 vs v1", "abcd_delta": -4, "performance_delta": -4 }],
    "feature_diffs": [{ "feature_id": "abcd_attention", "results": [true, false] }]
  }
}
```

---

### GET /api/results/{report\_id} — Fetch Cached Results

Returns the full results JSON for any prior evaluation.

```bash
curl https://app.aicreativereview.com/api/results/a1b2c3d4 \
  -H "X-API-Key: acr_<your-key>"
```

---

### GET /report/{report\_id} — Shareable HTML Report

Returns a standalone HTML report page — **no auth required**, safe to share externally.

```
https://app.aicreativereview.com/report/a1b2c3d4
```

---

### GET /api/report/{report\_id}/pdf — Download PDF

Returns `application/pdf`.

```bash
curl https://app.aicreativereview.com/api/report/a1b2c3d4/pdf \
  -H "X-API-Key: acr_<your-key>" \
  -o report.pdf
```

---

### GET /api/keyframe/{report\_id}/{scene\_idx} — Scene Keyframe Image

Returns `image/jpeg` for the scene at index `scene_idx` (0-based).

---

### POST /api/report/{report\_id}/feedback — Submit Feedback

Flag a feature detection as correct or incorrect to improve the model.

```bash
curl -X POST https://app.aicreativereview.com/api/report/a1b2c3d4/feedback \
  -H "X-API-Key: acr_<your-key>" \
  -H "Content-Type: application/json" \
  -d '{"feature_id": "abcd_attention", "verdict": "correct"}'
```

---

## Credits

| Parameter | Value |
|-----------|-------|
| Rate | 10 credits / second of video |
| Max video | 60 seconds = 600 credits max |
| Minimum to start | 100 credits |
| New account bonus | 3,000 credits |

Credits are deducted **after** a successful evaluation. Failed evaluations are not charged.

### Check balance
```bash
curl https://app.aicreativereview.com/billing/packs \
  -H "X-API-Key: acr_<your-key>"
```

**Response:**
```json
{
  "credits_balance": 2700,
  "packs": [
    { "key": "TOKENS_1000", "usd": 10, "tokens": 1000 },
    { "key": "TOKENS_3000", "usd": 25, "tokens": 3000 }
  ]
}
```

---

## API Key Management

### List keys
```bash
curl https://app.aicreativereview.com/auth/api-keys \
  -H "X-API-Key: acr_<your-key>"
```

### Revoke a key
```bash
curl -X DELETE https://app.aicreativereview.com/auth/api-keys/{key_id} \
  -H "X-API-Key: acr_<your-key>"
```

---

## Limits & Errors

| Constraint | Limit |
|------------|-------|
| Format | MP4 only |
| Max file size | 32 MB |
| Max duration | 60 seconds |
| Concurrent evaluations | 1 per user |
| Rate limit | 200 req/min (5/min on evaluate endpoints) |
| Max API keys | 10 per user |
| Max compare variants | 5 |

| Status | Meaning |
|--------|---------|
| `401` | Invalid or missing API key |
| `402` | Insufficient credits |
| `413` | File too large (>32 MB) |
| `415` | Unsupported format or non-YouTube URL |
| `429` | Rate limited or concurrent job in progress |

---

## Health Check

```bash
curl https://app.aicreativereview.com/health
```

```json
{ "status": "healthy", "version": "2.1", "database": "ok" }
```
