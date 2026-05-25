Copyright 2024 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

# Disclaimer

ABCDs Detector is NOT an official Google product.

## June, 2025 Update: Enhanced Capabilities and Flexibility

We're excited to announce major enhancements to the ABCDs Detector, significantly expanding its capabilities and offering greater flexibility in how you analyze your video creatives.

### What's New:

1.  **YouTube Shorts Evaluation:**
    *   Introducing **SHORTS evaluation**, specifically tailored for YouTube Shorts. This includes support for a dedicated set of features designed to evaluate the unique characteristics of short-form video content.

    **New YouTube Shorts Evaluation Features** (The availability and functionality of these features may be updated based on ongoing Google research.)
    *   **Shorts Production Style**
    *   **Shorts TV Ad Style**
    *   **Native Content Style (Low Adaptation)**
    *   **SFV Adaptation Balance (Medium Adaptation)**
    *   **Short Form Video Adaptation (High Adaptation)**
    *   **Emoji Usage**
    *   **Micro-Trend Usage**
    *   **Meso-Trend Usage**
    *   **Macro-Trend Implementation**
    *   **Traditional Ad Style**
    *   **Partial Social Style (25-50%)**
    *   **Predominantly Social Style (75%+)**
    *   **Creative Transitions**
    *   **Creative Gap Utilization**
    *   **Product/Service Result**
    *   **Creator Name Mention**
    *   **Partnership Clearly Disclosed**
    *   **Personal Character Talk**
    *   **Native Brand Context**
    *   **Personal Character Type**
    *   **Product Context**
    *   **Video Format**
    *   **Ad Style Analysis (Creator vs. Traditional)**

2.  **Direct YouTube URL Support:**
    *   You can now directly provide **YouTube URLs** for evaluation. This is applicable for public YouTube videos or videos from channels where the user is the owner.
    *   **Important Note:** Currently, YouTube URLs are evaluated using **LLMs only**. Annotation-based evaluation for YouTube URLs is not supported.

3.  **Flexible Creative Provisioning with Factory Pattern:**
    *   A new **Creative Provider** architecture, built on a factory pattern, allows developers to easily integrate and pull creatives from various data sources.
    *   **Supported Providers:**
        *   **Google Cloud Storage Creative Provider:** Retrieve individual videos or folders of videos from a GCS bucket.
        *   **YouTube Creative Provider:** Designed to retrieve a list of YouTube URLs. This can be adapted to integrate with the YouTube API for automated retrieval.
    *   **Custom Providers:** Implement your own creative providers by registering them in the `creative_provider_registry.py` file. Ensure your custom provider class implements the `get_creative_uris` method as specified in the `creative_provider_proto.py` file to return a list of creative URIs. Configuration in the system's `configuration.py` file is required to specify the provider type, please see the `set_parameters` function.

4.  **Feature Evaluation Methods:**
    *   Features are now evaluated using one of three methods:
        *   **LLMs Only:** Ideal for abstract concepts or when annotations are not available.
        *   **Annotations Only:** For features that can be reliably extracted or calculated from video metadata and vision models.
        *   **Combination of LLMs and Annotations:** For features requiring both structured data and nuanced understanding, especially those involving reasoning and calculations.
    *   The specific evaluation method for each feature is determined by extensive research and testing during pipeline implementation.

5.  **Custom Evaluation Functions for Core ABCDs:**
    *   For **Core ABCDs evaluation**, users can now implement their own custom evaluation functions for individual features. This is particularly useful for scenarios requiring a unique combination of LLMs and Annotations.
    *   Simply ensure your custom function complies with the defined interface and returns the expected standard evaluation response. You can return either True/False or an object with the evaluation details, please see the `VIDEO_RESPONSE_SCHEMA` object in `models.py` for more details.

6.  **Dynamic and Configurable Features:**
    *   All features are now **dynamic and configurable** via the `features_repository.py` file.
    *   To introduce a new feature, simply add it to the feature array within `features_repository.py` and configure its parameters; ABCD Detector will automatically evaluate it.
    *   Features can be **grouped** to be evaluated in a single prompt for efficiency, or configured with `NO_GROUPING` for individual evaluation (One API request per feature). Users should consider the potential cost implications when opting for individual evaluation.

# ABCDs Detector

The ABCDs Detector solution streamlines the assessment of your video ads against YouTube's ABCD framework. Powered by Google AI, this tool automates the evaluation process, providing detailed reports on how well your ads align with key attention-driving metrics. Simplify your YouTube ad analysis and gain valuable insights for optimization with the ABCDs Detector.

## The Approach

### Overview

The solution leverages:

**Video content annotation:** Google AI extracts features and identifies key moments within your video ads.

**Large Language Model (LLM) integration:** LLMs are used to assess features against YouTube's ABCD framework rubrics. This enables the detector to "ask questions" and determine if the ad adheres to each rubric.

By combining these techniques, ABCDs Detector automates the evaluation process and delivers comprehensive reports on how well your ads align with the ABCD framework. This empowers you to optimize your YouTube ad campaigns for maximum impact.

### Detailed approach

1. Video Intelligence API: To get annotations for the following features:
  - Label annotations
  - Face annotations
  - Text annotations
  - Object annotations
  - People annotations
  - Speech annotations
  - Shot annotations
  - Logo annotations


2. Gemini: To perform video Q&A about the features to evaluate if the video adheres to the ABCD rubrics. The colab will send a request to Gemini with tailored prompts to evaluate each rubric.

ABCDs Detector will perform 2 verifications, first with annotations and then with LLMs. Since the LLM approach is prone to hallucinations, False Positives or False Negatives will be expected. The solution will still require human QA if 100% accuracy is required for the evaluation.

ABCDs Detector MVP supports a single video evaluation for the following features/rubrics:
  - Quick Pacing
  - Quick Pacing (First 5 seconds)
  - Dynamic Start
  - Supers
  - Supers with Audio
  - Brand Visuals
  - Brand Visuals (First 5 seconds)
  - Brand Mention (Speech)
  - Brand Mention (Speech) (First 5 seconds)
  - Product Visuals
  - Product Visuals (First 5 seconds)
  - Product Mention (Text)
  - Product Mention (Text) (First 5 seconds)
  - Product Mention (Speech)
  - Product Mention (Speech) (First 5 seconds)
  - Visible Face (First 5 seconds)
  - Visible Face (Close Up)
  - Presence of People
  - Presence of People (First 5 seconds)
  - Overall Pacing
  - Audio Speech Early
  - Call To Action (Text)
  - Call To Action (Speech)

For a definition for each of these signals please take a look at the [long_form_abc_features.py](https://github.com/google-marketing-solutions/abcds-detector/blob/main/features_repository/long_form_abcd_features.py) and [shorts_features.py](https://github.com/google-marketing-solutions/abcds-detector/blob/main/features_repository/shorts_features.py) files.

The final result of the assessment (Excellent, Might Improve or Needs Review) is defined in the [generics_helpers.py](https://github.com/google-marketing-solutions/abcds-detector/blob/main/helpers/generic_helpers.py?plain=1#L186) and can be customized based on preferences.

### Google Cloud Cost breakdown

1. Video Intelligence API: Prices are per minute. Partial minutes are rounded up to the next full minute. Volume is per month. For more details please check the official [documentation](https://cloud.google.com/video-intelligence/pricing).

2. Gemini: With the Multimodal models in Vertex AI, you can input either text or media (images, video). Text input is charged by every 1,000 characters of input (prompt) and every 1,000 characters of output (response). Characters are counted by UTF-8 code points and white space is excluded from the count. Prediction requests that lead to filtered responses are charged for the input only. At the end of each billing cycle, fractions of one cent ($0.01) are rounded to one cent. Media input is charged per image or per second (video). For more details please check the official documentation: https://cloud.google.com/vertex-ai/generative-ai/pricing

For questions, please reach out to: abcds-detector@google.com

## Requirements
Please esure you have access to all of the following before starting:
* [Google Cloud Project](https://cloud.google.com) with enabled APIs:
    * [Video Intelligence API](https://console.cloud.google.com/marketplace/product/google/videointelligence.googleapis.com) - Optional if you are only using LLMs.
    * [Vertex AI API](https://console.cloud.google.com/marketplace/product/google/aiplatform.googleapis.com) - Optional if you are only using Annotations.
    * [Knowledge Graph API](https://console.cloud.google.com/marketplace/product/google/kgsearch.googleapis.com) - Optional if you are only using LLMs.
    * [Cloud Storage API](https://console.cloud.google.com/marketplace/product/google/storage.googleapis.com)
    * [BigQuery](https://cloud.google.com/bigquery/docs/reference/rest) - Optional if you don't want to store the results in BQ.
* [API Key](https://cloud.google.com/docs/authentication/api-keys) provisioned. - Optional if you are only using LLMs.
* [Project Billing](https://cloud.google.google.com/billing/) enabled.
* Python libraries:
    * `google-cloud-videointelligence`
    * `google-cloud-aiplatform`
* FFMPEG (not needed for colab)
  * Save the platform specific [FFMPEG Binary](https://evermeet.cx/ffmpeg/) locally.
  * Set the **IMAGEIO_FFMPEG_EXE** variable to the FFMPEG binary path.

You can see more on the ABCD methodology [here.](https://www.thinkwithgoogle.com/intl/en-emea/future-of-marketing/creativity/youtube-video-ad-best-practices/)

## Where to start?

1. Navigate to [colab.research.google.com](http://colab.research.google.com).
2. In the dialog, open a Notebook from GitHub.
3. Enter the url from this page.

**Note:** This repository provides python modules that can be executed on local machines for easier debugging and troubleshooting.

## Instructions
Please follow the steps below before executing the ABCDs Detector solution. Every **[VARIABLE]** is a parameter you can configure in the **Define ABCDs Detector Parameters** section.

1. Store your videos on [Google Cloud Storage](https://console.cloud.google.com/storage/browser) with the following folder structure:
  * **[BUCKET_NAME]** - name of bucket, ensure you have write permission. Same as paramter below.
    * **[brand_name]** - a folder, must be same as parameter below.
      * **videos** - a folder called videos, hard coded. Consider only **10-15 videos max** due to processing time limitations.
        * **some_video.mp4** - upload video to analyze, must be **mp4** and must be **[<= 50 MB](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models)**.
      * **annotations** - a folder created by this tool to store AI data. No need to create this.

1. Make sure the requirements are met:
  * Enable APIs:
    * [Video Intelligence API](https://console.cloud.google.com/marketplace/product/google/videointelligence.googleapis.com)
    * [Vertex AI API](https://console.cloud.google.com/marketplace/product/google/aiplatform.googleapis.com)
    * [Knowledge Graph API](https://console.cloud.google.com/marketplace/product/google/kgsearch.googleapis.com)
    * [Cloud Storage API](https://console.cloud.google.com/marketplace/product/google/storage.googleapis.com)
    * [BigQuery](https://console.cloud.google.com/marketplace/product/google/bigquery.googleapis.com)
  * Provision [An API Key](https://cloud.google.com/docs/authentication/api-keys):
    1. Visit [Credentials Page](https://cloud.console.google.com/apis/credentials).
    1. Create a **New API Key** and copy it into **[KNOWLEDGE_GRAPH_API_KEY]** below.
    1. We recommend editing and restricting the key to the above APIs.

1. Define all the parameters.
  * Required:
    * Google Cloud Project Details
    * Brand And Product Details
  * Optional
    * Solution Setup
    * ABCD Framework Details
    * LLM Configuration

1. Run all of the steps in sequence.
  * Some steps do not produce output, they only define functions.
  * If a step asks you to **Restart Runtime**, do so.
  * If a step displays an error, stop and debug it. Debug the following:
    * APIs are enabled.
    * Storage bucket is correctly configured.
    * The video is the correct size.
    * API Key has correct restrictions.
    * Previous colab sections completed.
    * Select _Runtime > Reset Session and Run All_ as a last resort.
  * The **Execute Bulk ABCD Assessment** produces the video analysis.

1. For questions, please reach out to: abcds-detector@google.com

**Note:** Please check the official [Gemini API documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini) to learn more about the LLM parameters (temperature, top_k, top_p, etc) that are used in this colab.

## Customization:

* Change the default parameters used for the ABCDs detection.
* Modify the ABCDs signals detection logic to fit yours.
* Add or remove ABCDs signals.
* Specify your own logic for calculating ABCDs score per video.
* ABCD features are dynamically added to a JSON list. If you want to add/remove features, please do that directly in the features_config/features.py file.
* To optimize LLM execution, features support grouping by 'full_video' and 'first_5_secs_video'. If you want to execute the features separately, please specify 'no_grouping' in the "group_by" field.

**Note:**

* This notebook is a starting point and can be further customized to fit your specific needs.

## Roadmap

1. Improvement: cut the video in shorter segments to improve LLM accuracy.
2. Improvement: leverage a [consensus approach](https://arxiv.org/pdf/2310.20151.pdf) to increase response confidence.

## Additional Resources:

* [Google Video Intelligence API](https://cloud.google.com/video-intelligence?hl=en)
* [Vertex AI](https://cloud.google.com/vertex-ai)
* [ABCD Framework best practices](https://www.thinkwithgoogle.com/intl/en-emea/future-of-marketing/creativity/youtube-video-ad-best-practices/)

---

## REST API

The ABCD Detector is deployed as a production REST API at:

```
https://creative-reviewer-939529436370.us-central1.run.app
```

### Authentication

All API requests require an API key passed as a header:

```
X-API-Key: acr_<your-key>
```

**Generating an API key** — sign in at the service URL, then run in the browser DevTools console:

```js
const r = await fetch('/auth/api-keys', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({name: 'my-integration'})
});
const d = await r.json();
console.log(d.key); // save this — shown once only
```

---

### POST /api/review

The primary endpoint. Submit an MP4 file or YouTube URL and receive the full ABCD report plus direct URLs for every asset in a single synchronous response.

**Request** (`multipart/form-data`):

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `file` | MP4 | one of `file`/`url` | Max 32 MB, max 60 s |
| `url` | string | one of `file`/`url` | YouTube URLs only |
| `use_abcd` | bool | no | Default `true` — ABCD framework scoring |
| `use_shorts` | bool | no | Default `false` — YouTube Shorts heuristics |
| `use_ci` | bool | no | Default `true` — Creative Intelligence features |

**Example — file upload:**

```bash
curl -X POST https://creative-reviewer-939529436370.us-central1.run.app/api/review \
  -H "X-API-Key: acr_<your-key>" \
  -F "file=@ad.mp4"
```

**Example — YouTube URL:**

```bash
curl -X POST https://creative-reviewer-939529436370.us-central1.run.app/api/review \
  -H "X-API-Key: acr_<your-key>" \
  -F "url=https://www.youtube.com/watch?v=VIDEO_ID"
```

**Response `200`:**

```json
{
  "report_id": "a1b2c3d4",
  "report_url": "https://creative-reviewer-.../report/a1b2c3d4",
  "pdf_url":    "https://creative-reviewer-.../api/report/a1b2c3d4/pdf",
  "video_url":  "https://creative-reviewer-.../api/video/a1b2c3d4",

  "abcd": {
    "score": 82,
    "result": "Excellent",
    "passed": 19,
    "total": 23,
    "features": [
      {
        "id": "abcd_attention",
        "name": "Attention",
        "detected": true,
        "confidence": 0.91,
        "rationale": "...",
        "recommendation": "...",
        "recommendation_priority": "high"
      }
    ]
  },

  "persuasion": { "density": 74, "features": [] },
  "accessibility": { "score": 68, "features": [] },
  "predictions": { "overall_score": 77 },

  "brand_intelligence": {
    "brand_name": "Acme",
    "product_service": "Consumer App",
    "target_audience": "18-34"
  },

  "scenes": [
    {
      "scene_number": 1,
      "start_time": "0:00",
      "end_time": "0:05",
      "keyframe_url": "https://creative-reviewer-.../api/keyframe/a1b2c3d4/0",
      "description": "Opening hook with product reveal",
      "transcript": "Introducing the new...",
      "emotion": "excited",
      "sentiment_score": 0.82
    }
  ],

  "action_plan": [
    {
      "priority": "high",
      "feature_name": "Brand Mention (First 5s)",
      "detected": false,
      "recommendation": "Show your brand name or logo in the first 5 seconds."
    }
  ],

  "duration_seconds": 30.0,
  "tokens_used": 300,
  "credits_remaining": 2700
}
```

> **Note:** `video_url` is only present for file uploads (not YouTube). Scene `keyframe_url` fields return `image/jpeg` — no base64 in the response.

---

### Other Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | None | Service health + DB status |
| `GET` | `/report/{report_id}` | None | Shareable HTML report |
| `GET` | `/api/report/{report_id}/pdf` | None | Download PDF |
| `GET` | `/api/keyframe/{report_id}/{scene_idx}` | None | Scene keyframe JPEG |
| `GET` | `/api/video/{report_id}` | Key | Stream source video |
| `GET` | `/api/results/{report_id}` | Key | Raw results JSON |
| `POST` | `/api/evaluate_file` | Key | Same as `/api/review` but includes raw base64 keyframes |
| `GET` | `/auth/api-keys` | Key | List your API keys |
| `POST` | `/auth/api-keys` | Key | Create an API key |
| `DELETE` | `/auth/api-keys/{key_id}` | Key | Revoke an API key |
| `GET` | `/billing/packs` | Key | Credit packs + balance |
| `GET` | `/auth/me` | Key | Current user info |

---

### Credits

| Parameter | Value |
|-----------|-------|
| Rate | 10 credits / second of video |
| Max video duration | 60 seconds (600 credits max) |
| Minimum balance to start | 100 credits |
| New account bonus | 3,000 credits |

Credits are deducted **after** a successful evaluation. Failed evaluations are not charged.

---

### Error Codes

| Status | Error | Description |
|--------|-------|-------------|
| `400` | `missing_input` | Neither `file` nor `url` provided |
| `400` | `ambiguous_input` | Both `file` and `url` provided |
| `401` | — | Missing or invalid API key |
| `402` | `insufficient_credits` | Credit balance too low |
| `413` | `file_too_large` | File exceeds 32 MB |
| `415` | `unsupported_format` | Not an MP4 file |
| `415` | `unsupported_url` | Non-YouTube URL |
| `429` | `concurrent_limit` | Evaluation already in progress |
| `429` | `rate_limited` | Too many requests |

---

## Testing

A test script is provided at `tests/test_review_api.py`. It uses only Python stdlib — no additional dependencies required.

### Run the fast tests (auth + validation, ~5 seconds)

```bash
python3 tests/test_review_api.py \
  --key acr_<your-key> \
  --skip-youtube \
  --skip-file
```

### Run the full test suite (includes a real YouTube evaluation, ~3-5 min)

```bash
python3 tests/test_review_api.py --key acr_<your-key>
```

### Test against a different deployment

```bash
python3 tests/test_review_api.py \
  --key acr_<your-key> \
  --url https://your-service-url.run.app
```

### What the tests cover

| # | Test | Notes |
|---|------|-------|
| 1 | Health check | Verifies service is up and database is connected |
| 2 | Auth — no key | Expects `401` |
| 3 | Auth — invalid key | Expects `401` |
| 4 | No input | Expects `400 missing_input` |
| 5 | Non-YouTube URL | Expects `415 unsupported_url` |
| 6 | Non-MP4 file | Expects `415 unsupported_format` |
| 7 | YouTube review | Full response structure, ABCD scoring, scenes |
| 8 | `report_url` | HTML report accessible without auth |
| 9 | `pdf_url` | Returns valid PDF bytes |
| 10 | `keyframe_url` | Returns JPEG image for scene 0 |
| 11 | File upload | Generates a synthetic MP4, verifies `video_url` in response |

### Example output

```
Testing: https://creative-reviewer-939529436370.us-central1.run.app
API key: acr_abc12345...
============================================================

[1] Health check
  ✓ GET /health → 200 (healthy, db=ok)

[2] Authentication
  ✓ No API key → 401
  ✓ Invalid API key → 401

[3] Input validation
  ✓ No input → 400 missing_input
  ✓ Non-YouTube URL → 415 unsupported_url
  ✓ Non-MP4 file → 415 unsupported_format

[4] YouTube URL review (this takes ~2-5 min)
  Submitting: https://www.youtube.com/watch?v=...
  ✓ POST /api/review → 200 (187s)
  ✓ All required top-level fields present
  ✓ abcd.score=78  result='Might Improve'  features=23
  ✓ Scenes have keyframe_url (no raw base64) — 8 scenes
  ✓ action_plan correctly ordered by priority (12 items)
  ✓ report_url accessible (no auth)
  ✓ pdf_url returns valid PDF (142 KB)
  ✓ scenes[0].keyframe_url returns image (18 KB)
  ✓ video_url absent for YouTube input (expected)

============================================================
Results: 11 passed  0 failed  1 skipped
```

---

## Admin Utilities

### create_api_key.py

Generate an API key for any existing user directly against the database:

```bash
python3 create_api_key.py kevin@example.com my-key-name
```

### Admin API key endpoint

Protected by `UPSCALE_REPORT_TOKEN`. Generates a key server-side:

```bash
curl -X POST https://creative-reviewer-939529436370.us-central1.run.app/admin/generate-api-key \
  -H "X-Admin-Token: <UPSCALE_REPORT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "name": "my-key"}'
