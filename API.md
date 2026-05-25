# AI Creative Review API

**Base URL:** `https://app.aicreativereview.com`  
**Version:** 2.1

---

## Table of Contents

- [Authentication](#authentication)
- [API Key Management](#api-key-management)
- [Core Workflow](#core-workflow)
  - [Upload Video](#1-upload-video)
  - [Evaluate (SSE Stream)](#2-evaluate-sse-stream)
  - [Evaluate File (Single-call JSON)](#3-evaluate-file-single-call-json--recommended)
  - [Compare Variants](#4-compare-variants)
- [Reports & Results](#reports--results)
- [Feedback](#feedback)
- [Credits & Billing](#credits--billing)
- [Account](#account)
- [Limits & Error Codes](#limits--error-codes)
- [Health](#health)

---

## Authentication

All API requests require an API key passed as a header:

```
X-API-Key: acr_<your-key>
```

Session cookie auth is also accepted for browser-based requests. API key auth takes precedence when both are present.

To generate a key, see [Create API Key](#create-api-key) below or use the in-app settings.

---

## API Key Management

### Create API Key

```
POST /auth/api-keys
Content-Type: application/json
```

**Request body:**
```json
{
  "name": "my-integration"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | yes | Label for the key. Max 64 characters. |

**Response `201`:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "my-integration",
  "key": "acr_a1b2c3d4e5f6...",
  "key_prefix": "acr_a1b2c3d4",
  "created_at": "2026-05-24T00:00:00",
  "warning": "Save this key — it will not be shown again."
}
```

> The full key is returned **once only** at creation. Store it securely (e.g. an environment variable). Only the prefix is stored server-side.

---

### List API Keys

```
GET /auth/api-keys
```

**Response `200`:**
```json
{
  "api_keys": [
    {
      "id": "550e8400-...",
      "name": "my-integration",
      "key_prefix": "acr_a1b2c3d4",
      "is_active": true,
      "created_at": "2026-05-24T00:00:00",
      "last_used_at": "2026-05-25T00:45:00"
    }
  ]
}
```

---

### Revoke API Key

```
DELETE /auth/api-keys/{key_id}
```

**Response `200`:**
```json
{ "status": "revoked", "id": "550e8400-..." }
```

---

## Core Workflow

The recommended integration path:

```
Upload video → Evaluate → Poll or receive results
```

Or use **Evaluate File** for a single-call approach that handles both steps.

---

### 1. Upload Video

```
POST /api/upload
Content-Type: multipart/form-data
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `file` | MP4 file | yes | Max 32 MB, max 60 seconds |

**Response `200`:**
```json
{
  "status": "uploaded",
  "filename": "my-video.mp4",
  "gcs_uri": "gs://bucket/my-video.mp4",
  "size_mb": 12.4
}
```

Use the returned `gcs_uri` as input to `/api/evaluate`.

**Errors:**
| Status | Error | Description |
|--------|-------|-------------|
| `413` | `file_too_large` | File exceeds 32 MB |
| `415` | `unsupported_format` | Only `.mp4` is supported |
| `402` | `insufficient_credits` | Balance below minimum (100 credits) |

---

### 2. Evaluate (SSE Stream)

Evaluates a previously uploaded video or YouTube URL. Streams progress in real time via [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events).

```
POST /api/evaluate
Content-Type: multipart/form-data
```

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `gcs_uri` | string | required | GCS URI from `/api/upload`, or a YouTube URL |
| `use_abcd` | bool | `true` | ABCD framework scoring |
| `use_shorts` | bool | `false` | YouTube Shorts heuristics |
| `use_ci` | bool | `true` | Creative Intelligence features |

**Event stream format:**

```
data: {"step": "render_estimate", "estimated_render_seconds": 138, "render_started_at": "...", "render_factor": 23.0}

data: {"step": "extracting_frames", "message": "Extracting keyframes", "pct": 10}

data: {"step": "analyzing", "message": "Running ABCD detection", "pct": 40}

data: {"step": "complete", "pct": 100, "data": { ...full results object... }}

data: {"step": "error", "message": "Evaluation failed: ..."}
```

The `data` payload of the `complete` event matches the [Results Object](#results-object) schema below.

**Example (curl):**
```bash
curl -X POST https://app.aicreativereview.com/api/evaluate \
  -H "X-API-Key: acr_<your-key>" \
  -F "gcs_uri=gs://bucket/my-video.mp4" \
  -F "use_abcd=true" \
  -F "use_ci=true" \
  --no-buffer
```

---

### 3. Evaluate File (Single-call JSON) — Recommended

Upload an MP4 file **or** provide a YouTube URL and receive the full evaluation as a single synchronous JSON response. Best for API integrations that don't want to handle SSE.

```
POST /api/evaluate_file
Content-Type: multipart/form-data
```

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `file` | MP4 file | one of `file`/`url` required | Mutually exclusive with `url` |
| `url` | string | one of `file`/`url` required | YouTube URL (`youtube.com` or `youtu.be`) |
| `use_abcd` | bool | `true` | ABCD framework scoring |
| `use_shorts` | bool | `false` | YouTube Shorts heuristics |
| `use_ci` | bool | `true` | Creative Intelligence features |

**Response `200`:** See [Results Object](#results-object).

**Example — file upload:**
```bash
curl -X POST https://app.aicreativereview.com/api/evaluate_file \
  -H "X-API-Key: acr_<your-key>" \
  -F "file=@my-video.mp4" \
  -F "use_abcd=true" \
  -F "use_ci=true"
```

**Example — YouTube URL:**
```bash
curl -X POST https://app.aicreativereview.com/api/evaluate_file \
  -H "X-API-Key: acr_<your-key>" \
  -F "url=https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  -F "use_abcd=true"
```

---

### 4. Compare Variants

Evaluate 2–5 videos in parallel and receive a side-by-side comparison report with a recommended winner.

```
POST /api/evaluate_compare
Content-Type: application/json
```

**Request body:**
```json
{
  "video_uris": [
    "gs://bucket/ad-v1.mp4",
    "gs://bucket/ad-v2.mp4"
  ],
  "use_abcd": true,
  "use_shorts": false,
  "use_ci": true
}
```

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `video_uris` | array of strings | required | 2–5 GCS URIs or YouTube URLs |
| `use_abcd` | bool | `true` | ABCD scoring |
| `use_shorts` | bool | `false` | Shorts heuristics |
| `use_ci` | bool | `true` | Creative Intelligence |

Credits are deducted per video. All variants must succeed to generate the comparison.

**Response `200`:**
```json
{
  "comparison_id": "x1y2z3w4",
  "timestamp": "2026-05-24T00:00:00",
  "comparison": {
    "variant_count": 2,
    "variants": [
      {
        "index": 0,
        "video_name": "ad-v1.mp4",
        "abcd_score": 82,
        "persuasion_density": 74,
        "performance_score": 79,
        "accessibility_score": 68,
        "report_id": "a1b2c3d4"
      },
      {
        "index": 1,
        "video_name": "ad-v2.mp4",
        "abcd_score": 78,
        "persuasion_density": 71,
        "performance_score": 75,
        "accessibility_score": 72,
        "report_id": "e5f6g7h8"
      }
    ],
    "deltas": [
      {
        "vs": "ad-v2.mp4 vs ad-v1.mp4",
        "abcd_delta": -4,
        "persuasion_delta": -3,
        "performance_delta": -4
      }
    ],
    "feature_diffs": [
      {
        "feature_id": "abcd_attention",
        "feature_name": "Attention",
        "results": [true, false]
      }
    ],
    "recommended_winner": {
      "index": 0,
      "video_name": "ad-v1.mp4",
      "justification": "ad-v1.mp4 leads with a performance score of 79, ABCD 82%, and accessibility 68%. Outperforms ad-v2.mp4 by +4 on performance."
    }
  },
  "variants": [ ...full results objects for each video... ],
  "errors": []
}
```

**View comparison report (HTML):**
```
GET /report/compare/{comparison_id}
```

---

## Results Object

Returned by `/api/evaluate_file`, the SSE `complete` event, and `/api/results/{report_id}`.

```json
{
  "report_id": "a1b2c3d4",
  "report_url": "https://app.aicreativereview.com/report/a1b2c3d4",
  "timestamp": "2026-05-24T00:00:00",
  "video_name": "my-video.mp4",
  "duration_seconds": 30.0,
  "tokens_used": 300,
  "credits_remaining": 2700,

  "abcd": {
    "score": 82,
    "features": [
      {
        "id": "abcd_attention",
        "name": "Attention",
        "detected": true,
        "confidence": 0.91,
        "timestamps": [
          { "start": "0:00", "end": "0:03", "label": "Hook" }
        ]
      }
    ]
  },

  "persuasion": {
    "density": 74,
    "features": [ ... ]
  },

  "accessibility": {
    "score": 68,
    "features": [ ... ]
  },

  "predictions": {
    "overall_score": 77
  },

  "brand_intelligence": {
    "product_service": "Consumer App",
    "brand_name": "Acme",
    "target_audience": "18-34"
  },

  "scenes": [
    {
      "scene_number": 1,
      "start_time": "0:00",
      "end_time": "0:05",
      "description": "Opening hook with product reveal",
      "transcript": "Introducing the new...",
      "emotion": "excited",
      "sentiment_score": 0.82,
      "music_mood": "upbeat",
      "has_music": true,
      "speech_ratio": 0.6
    }
  ],

  "video_metadata": {
    "duration_seconds": 30.0,
    "resolution": "1920x1080",
    "fps": 30
  }
}
```

---

## Reports & Results

### Get JSON Results
```
GET /api/results/{report_id}
```
Returns the full [Results Object](#results-object). Results are cached server-side after evaluation.

### View HTML Report
```
GET /report/{report_id}
```
Returns a standalone shareable HTML page. **No authentication required** — safe to share externally.

### Download PDF Report
```
GET /api/report/{report_id}/pdf
```
Returns `application/pdf`. Filename: `abcd_report_{video_name}_{report_id}.pdf`.

### Get Scene Keyframe Image
```
GET /api/keyframe/{report_id}/{scene_idx}
```
Returns `image/jpeg` for the scene at `scene_idx` (0-based).

### Stream Video
```
GET /api/video/{report_id}
```
Returns `video/mp4` streamed from storage. Cached for 24 hours.

---

## Feedback

Submit human feedback on individual feature detections to improve model calibration.

```
POST /api/report/{report_id}/feedback
Content-Type: application/json
```

**Request body:**
```json
{
  "feature_id": "abcd_attention",
  "verdict": "correct"
}
```

| Field | Type | Values |
|-------|------|--------|
| `feature_id` | string | Feature ID from the results object |
| `verdict` | string | `"correct"` or `"incorrect"` |

**Response `200`:**
```json
{ "status": "ok" }
```

---

## Credits & Billing

### How Credits Work

| Parameter | Value |
|-----------|-------|
| Rate | 10 credits / second of video |
| Max video duration | 60 seconds |
| Max credits per evaluation | 600 |
| Minimum balance to start | 100 credits |
| New account bonus | 3,000 credits |

Credits are deducted **after** a successful evaluation based on actual video duration. Failed evaluations are not charged.

### Credit Packs

| Pack key | Credits | Price |
|----------|---------|-------|
| `TOKENS_1000` | 1,000 | $10 |
| `TOKENS_3000` | 3,000 | $25 |

### Get Balance & Available Packs
```
GET /billing/packs
```

**Response `200`:**
```json
{
  "credits_balance": 2700,
  "packs": [
    { "key": "TOKENS_1000", "usd": 10, "tokens": 1000, "available": true },
    { "key": "TOKENS_3000", "usd": 25, "tokens": 3000, "available": true }
  ]
}
```

### Credit Transaction History
```
GET /billing/history
```

Also available at `GET /auth/transactions`.

**Response `200`:**
```json
{
  "credits_balance": 2700,
  "transactions": [
    {
      "id": "uuid",
      "type": "debit",
      "amount": 300,
      "reason": "video_evaluation",
      "job_id": "a1b2c3d4",
      "created_at": "2026-05-24T00:00:00"
    }
  ]
}
```

### Create Stripe Checkout Session
```
POST /billing/checkout-session
Content-Type: application/json
```

```json
{ "pack": "TOKENS_1000" }
```

**Response `200`:**
```json
{ "checkout_url": "https://checkout.stripe.com/pay/cs_..." }
```

Redirect the user to `checkout_url` to complete payment. Credits are added automatically on success.

---

## Account

### Get Current User
```
GET /auth/me
```

**Response `200`:**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "email_verified": true,
    "has_google": true,
    "credits_balance": 2700,
    "created_at": "2026-01-01T00:00:00"
  }
}
```

---

## Limits & Error Codes

### Rate Limits

| Endpoint | Limit |
|----------|-------|
| All endpoints | 200 req/min |
| `POST /api/evaluate` | 5 req/min |
| `POST /api/evaluate_file` | 5 req/min |
| Auth endpoints | 10 attempts / 5 min per IP |

### Concurrent Jobs

Only **1 evaluation at a time** per user. Starting a second evaluation while one is in progress returns `429`.

### File Constraints

| Constraint | Limit |
|------------|-------|
| Format | MP4 only |
| Max file size | 32 MB |
| Max duration | 60 seconds |
| Max API keys per user | 10 |
| Max variants (compare) | 5 |

### Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable description"
}
```

### HTTP Status Codes

| Status | Error Code | Description |
|--------|------------|-------------|
| `400` | `missing_input` | Required field not provided |
| `400` | `ambiguous_input` | Conflicting fields provided |
| `400` | `video_too_long` | Video exceeds 60 seconds |
| `401` | — | Missing or invalid API key / session |
| `402` | `insufficient_credits` | Credit balance too low |
| `409` | — | Resource conflict (e.g. duplicate email) |
| `413` | `file_too_large` | File exceeds 32 MB |
| `415` | `unsupported_format` | File format not supported |
| `415` | `unsupported_url` | Non-YouTube URL provided |
| `429` | `rate_limited` | Too many requests |
| `429` | `concurrent_limit` | Evaluation already in progress |
| `500` | — | Internal server error |

---

## Health

```
GET /health
```

**Response `200`:**
```json
{
  "status": "healthy",
  "version": "2.1",
  "database": "ok"
}
```

Returns `503` with `"status": "degraded"` if the database is unreachable.
