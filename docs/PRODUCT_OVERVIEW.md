# AI Creative Review — Product Overview

**What it is · How it works · Who it's for**

_This document is written for non-technical team members. For API and system documentation, see [API.md](API.md) and [TRD.md](TRD.md)._

---

## What Is AI Creative Review?

AI Creative Review is an automated tool that watches your video ads and tells you — in minutes — whether they're built to perform.

It scores every ad against **YouTube's ABCD framework**: a research-backed set of 23 creative principles that Google has validated drive higher view-through rates, brand recall, and conversions. On top of that, it detects persuasion tactics, predicts campaign performance, and generates a full shareable report with specific, actionable feedback for every element it evaluates.

Think of it as a senior creative strategist who watches every ad you produce, scores it against a proven checklist, and hands you back a written report in about 5 minutes — instead of 45.

---

## The Problem It Solves

Manual creative QA doesn't scale. A human reviewer evaluating a single video against the ABCD framework takes 30–60 minutes, results vary between reviewers, and at any meaningful production volume it becomes a bottleneck. Teams either skip the process entirely or limit it to hero assets.

AI Creative Review makes it practical to review every asset before it goes live — not just the ones that seem worth the time.

---

## Who It's For

| Team | How they use it |
|---|---|
| **Creative** | Validate work before handoff. Catch gaps early, while edits are still cheap. |
| **Media Buying** | QA creative before campaign launch. Predict CPA risk and ROAS tier. |
| **Brand** | Audit video libraries for consistency. Train new creators against a standard. |
| **Account Management** | Share polished reports with clients as proof of creative diligence. |

---

## The ABCD Framework — Plain English

Every video ad is evaluated across four dimensions:

**A — Attract**
Does the ad grab attention immediately? The first 5 seconds are everything. This section checks for fast editing, early movement, on-screen text, and voiceover that starts right away.

**B — Brand**
Is it obvious who's behind the ad? The tool checks whether the logo and brand name appear on screen and are spoken aloud — ideally within the first 5 seconds, not buried at the end.

**C — Connect**
Does the ad make the viewer feel something? This covers whether real people and faces appear, whether the product is clearly shown, and whether the product name is communicated both visually and verbally.

**D — Direct**
Does the ad tell the viewer what to do? A clear call to action — spoken and on screen — is required for any ad designed to drive a response.

**The score:** Each ad gets a percentage based on how many of the 23 principles it meets.
- **80%+** — Excellent
- **65–79%** — Might Improve
- **Below 65%** — Needs Review

---

## How It Works, Step by Step

### 1. Provide your video
There are two ways to submit an ad for review — pick whichever fits your workflow:

- **Upload an MP4** — Drag and drop a file (up to 60 seconds, 32 MB) onto the platform or send it via API.
- **Paste a YouTube URL** — Drop a public `youtube.com` or `youtu.be` link into the URL field. No download or file handling needed.

No other configuration is required.

### 2. The AI reads the ad
Google's Gemini AI watches the video and simultaneously:
- Identifies the brand, products, and calls to action on its own
- Detects scene changes, transcribes speech, and reads on-screen text
- Maps the emotional arc of the ad scene by scene

### 3. Every principle is evaluated
Each of the 23 ABCD features is assessed — plus 7 persuasion tactics, creative structure, and accessibility checks. For each one, the AI returns:
- **Pass or fail**
- **Why** (specific reasoning)
- **Evidence** (exact timestamps and observations)
- **What to fix** (a prioritized recommendation if it failed)

### 4. Performance is predicted
Using the feature results, the tool calculates four forward-looking predictions:

| Prediction | What it means |
|---|---|
| **CPA Risk** | Low / Medium / High cost-per-acquisition risk |
| **ROAS Tier** | Expected return on ad spend: High / Moderate / Low |
| **Creative Fatigue Risk** | How quickly the ad is likely to wear out with the audience |
| **Funnel Stage Fit** | Whether the ad is best suited for awareness, consideration, or conversion |

### 5. You receive the report
A full report is generated and available in three forms:
- **Web view** — An interactive page with scene-by-scene thumbnails, score cards, and expandable feature results
- **PDF** — A formatted document ready to share with clients or stakeholders
- **JSON** — Raw data for teams who want to pipe results into their own dashboards or tools

---

## What the Report Contains

| Section | What it tells you |
|---|---|
| **ABCD Score** | Overall pass rate and result tier (Excellent / Might Improve / Needs Review) |
| **Persuasion Density** | What percentage of 7 persuasion tactics are present (social proof, scarcity, urgency, etc.) |
| **Performance Predictions** | CPA risk, ROAS tier, fatigue risk, funnel fit |
| **Scene Timeline** | Every scene with a thumbnail, transcript, detected emotion, and audio level |
| **Feature Breakdown** | Pass/fail + rationale for all 23 ABCD features |
| **Action Plan** | Prioritized list of the most impactful things to fix |
| **Platform Fit** | Scores and tips for YouTube, Meta Feed, Meta Reels, TikTok, and CTV |
| **Brand Intelligence** | Auto-generated brand brief: positioning, target audience, messaging themes |
| **Benchmarks** | How this ad compares to others evaluated on the platform |
| **Reference Ads** | Similar high-scoring ads from the library for creative inspiration |
| **Accessibility** | Captions, text contrast, speech rate, sound-off usability |

---

## Pricing

The platform runs on a credit system — you buy credits and spend them per video.

| What | Cost |
|---|---|
| Cost per second of video | 10 credits |
| 30-second ad | 300 credits |
| 60-second ad | 600 credits |
| 1,000 credit pack | $10 |
| 3,000 credit pack | $25 |
| New account bonus | 3,000 free credits (~5 full reviews) |

There are no subscriptions or seat fees. You pay for what you use.

---

## How to Access It

### Web App
Visit [app.aicreativereview.com](https://app.aicreativereview.com), sign in with Google or email, and upload a video. Results are ready in 2–5 minutes depending on video length.

### API (for automation or integrations)
Generate an API key from your account settings, then submit videos programmatically and receive the full report as structured data. Useful for connecting to internal dashboards, triggering reviews on upload, or batch processing an entire creative library.

The same endpoint accepts either an MP4 file or a YouTube URL — both return the identical JSON response:

```
# Option A — MP4 file upload
POST https://app.aicreativereview.com/api/evaluate_file
Header: X-API-Key: acr_yourkey
Body:   file=ad.mp4, use_abcd=true, use_ci=true

# Option B — YouTube URL
POST https://app.aicreativereview.com/api/evaluate_file
Header: X-API-Key: acr_yourkey
Body:   url=https://www.youtube.com/watch?v=..., use_abcd=true, use_ci=true
```

Full API documentation is in [API.md](API.md).

---

## Accuracy & Limitations

The AI is accurate **90–95% of the time** against human expert reviewers. A few things to keep in mind:

- **It's a screening tool, not a final judgment.** It can occasionally miss something a human would catch, or flag something that isn't there. Use it to identify what needs a closer look, not as the last word.
- **YouTube URLs and MP4 uploads are both fully supported.** YouTube-sourced reviews run the same AI analysis; the only difference is that a small number of annotation-based checks (which require a locally hosted file) are skipped. All ABCD scoring, persuasion detection, and performance predictions are included.
- **Videos must be 60 seconds or under.** Longer cuts should be trimmed to the ad version before submission.
- **Processing time:** ~2 minutes for a 30-second ad, ~5 minutes for a 60-second ad.

---

## Glossary

| Term | Meaning |
|---|---|
| **ABCD Framework** | YouTube's 23-point creative best practice checklist (Attract, Brand, Connect, Direct) |
| **Persuasion Density** | The percentage of 7 psychological persuasion tactics detected in the ad |
| **Creative Intelligence** | The broader analysis layer: persuasion tactics, narrative structure, and accessibility checks |
| **CPA Risk** | Predicted cost-per-acquisition risk based on creative signals (Low / Medium / High) |
| **ROAS Tier** | Predicted return on ad spend tier (High / Moderate / Low) |
| **Fatigue Risk** | How likely the ad is to wear out quickly with repeated exposure |
| **Scene** | A continuous visual segment of the ad detected by the AI |
| **Keyframe** | A representative still image captured from each scene |
| **Credits** | The platform's usage currency — 10 credits per second of video evaluated |
| **Report ID** | A unique identifier for each evaluation — use it to share or retrieve a report |
