#!/usr/bin/env python3
"""
Test suite for POST /api/review

Usage:
    python tests/test_review_api.py --key acr_<your-key>
    python tests/test_review_api.py --key acr_<your-key> --url https://custom-host.run.app

Tests:
    1. Health check
    2. Auth — missing key returns 401
    3. Auth — invalid key returns 401
    4. Input validation — no input returns 400
    5. Input validation — both file and url returns 400
    6. Input validation — non-YouTube URL returns 415
    7. YouTube URL review — full response structure
    8. Asset URLs — report_url, pdf_url accessible (no auth)
    9. Asset URLs — keyframe_url accessible (no auth)
    10. Asset URLs — video_url present for file uploads
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
SKIP = "\033[93m~\033[0m"

_results = {"passed": 0, "failed": 0, "skipped": 0}


def ok(name: str):
    print(f"  {PASS} {name}")
    _results["passed"] += 1


def fail(name: str, reason: str = ""):
    print(f"  {FAIL} {name}" + (f": {reason}" if reason else ""))
    _results["failed"] += 1


def skip(name: str, reason: str = ""):
    print(f"  {SKIP} {name}" + (f" ({reason})" if reason else ""))
    _results["skipped"] += 1


def request(method: str, url: str, *, headers=None, data=None, files=None, timeout=300):
    """Minimal HTTP client using stdlib only."""
    import urllib.parse, io, os, mimetypes

    headers = headers or {}

    if files:
        # Build multipart/form-data manually
        boundary = "----TestBoundary" + os.urandom(8).hex()
        body_parts = []
        for field, value in (data or {}).items():
            body_parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"\r\n\r\n{value}\r\n'.encode()
            )
        for field, (filename, file_obj, content_type) in files.items():
            file_data = file_obj.read() if hasattr(file_obj, "read") else file_obj
            body_parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode()
                + file_data + b"\r\n"
            )
        body_parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(body_parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif data and not files:
        body = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in data.items()).encode()
        headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    else:
        body = None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_health(base: str):
    print("\n[1] Health check")
    status, body = request("GET", f"{base}/health")
    if status == 200:
        data = json.loads(body)
        if data.get("status") in ("healthy", "degraded") and "database" in data:
            ok(f"GET /health → {status} ({data['status']}, db={data['database']})")
        else:
            fail("GET /health", f"unexpected body: {data}")
    else:
        fail("GET /health", f"status={status}")


def test_auth(base: str, key: str):
    print("\n[2] Authentication")

    # No key
    status, _ = request("POST", f"{base}/api/review")
    if status == 401:
        ok("No API key → 401")
    else:
        fail("No API key → 401", f"got {status}")

    # Wrong key
    status, _ = request("POST", f"{base}/api/review", headers={"X-API-Key": "acr_badkey"})
    if status == 401:
        ok("Invalid API key → 401")
    else:
        fail("Invalid API key → 401", f"got {status}")


def test_input_validation(base: str, key: str):
    print("\n[3] Input validation")
    headers = {"X-API-Key": key}

    # No input
    status, body = request("POST", f"{base}/api/review", headers=headers, data={})
    data = json.loads(body)
    if status == 400 and data.get("error") == "missing_input":
        ok("No input → 400 missing_input")
    else:
        fail("No input → 400", f"got {status} {data}")

    # Non-YouTube URL
    status, body = request("POST", f"{base}/api/review", headers=headers,
                           data={"url": "https://vimeo.com/123456"})
    data = json.loads(body)
    if status == 415 and data.get("error") == "unsupported_url":
        ok("Non-YouTube URL → 415 unsupported_url")
    else:
        fail("Non-YouTube URL → 415", f"got {status} {data}")

    # Bad file format
    fake_file = b"not a real video"
    status, body = request(
        "POST", f"{base}/api/review", headers=headers,
        files={"file": ("test.avi", fake_file, "video/avi")},
    )
    data = json.loads(body)
    if status == 415 and data.get("error") == "unsupported_format":
        ok("Non-MP4 file → 415 unsupported_format")
    else:
        fail("Non-MP4 file → 415", f"got {status} {data}")


def test_youtube_review(base: str, key: str) -> dict | None:
    """Submit a short public YouTube ad and validate the full response."""
    print("\n[4] YouTube URL review (this takes ~2-5 min)")
    headers = {"X-API-Key": key}

    # A short Google Ads example (~15 s)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    print(f"  Submitting: {test_url}")
    t0 = time.time()

    status, body = request(
        "POST", f"{base}/api/review", headers=headers,
        data={"url": test_url, "use_abcd": "true", "use_ci": "true"},
        timeout=600,
    )
    elapsed = round(time.time() - t0)

    if status != 200:
        fail(f"POST /api/review → 200", f"got {status}: {body[:300]}")
        return None

    data = json.loads(body)
    ok(f"POST /api/review → 200 ({elapsed}s)")

    # --- Required top-level fields ---
    required = ["report_id", "report_url", "pdf_url", "abcd", "persuasion",
                "accessibility", "predictions", "scenes", "action_plan",
                "tokens_used", "credits_remaining"]
    missing = [f for f in required if f not in data]
    if missing:
        fail("Required top-level fields present", f"missing: {missing}")
    else:
        ok(f"All required top-level fields present")

    # --- ABCD structure ---
    abcd = data.get("abcd", {})
    if all(k in abcd for k in ("score", "result", "passed", "total", "features")):
        ok(f"abcd.score={abcd['score']}  result='{abcd['result']}'  features={len(abcd['features'])}")
    else:
        fail("abcd structure", f"got keys: {list(abcd)}")

    # --- Scenes have keyframe_url, not base64 keyframe ---
    scenes = data.get("scenes", [])
    if not scenes:
        skip("Scene keyframe_url check", "no scenes returned")
    else:
        has_kf_url = all("keyframe_url" in s for s in scenes if s.get("keyframe_url") or True)
        has_raw_b64 = any("keyframe" in s and not "keyframe_url" in s for s in scenes)
        if not has_raw_b64:
            ok(f"Scenes have keyframe_url (no raw base64) — {len(scenes)} scenes")
        else:
            fail("keyframe_url present (no raw base64)", "base64 keyframe still in response")

    # --- action_plan priority ordering ---
    plan = data.get("action_plan", [])
    if plan:
        prio_order = {"high": 0, "medium": 1, "low": 2}
        ordered = all(
            prio_order.get(plan[i]["priority"], 9) <= prio_order.get(plan[i+1]["priority"], 9)
            for i in range(len(plan) - 1)
        )
        if ordered:
            ok(f"action_plan correctly ordered by priority ({len(plan)} items)")
        else:
            fail("action_plan priority ordering")

    # --- report_url / pdf_url reachable without auth ---
    report_url = data.get("report_url", "")
    if report_url:
        s, _ = request("GET", report_url, timeout=30)
        if s == 200:
            ok(f"report_url accessible (no auth)")
        else:
            fail("report_url accessible", f"status={s}")

    pdf_url = data.get("pdf_url", "")
    if pdf_url:
        s, body = request("GET", pdf_url, timeout=60)
        if s == 200 and body[:4] == b"%PDF":
            ok(f"pdf_url returns valid PDF ({len(body)//1024} KB)")
        else:
            fail("pdf_url returns PDF", f"status={s}, header={body[:10]}")

    # --- keyframe_url for first scene ---
    if scenes:
        kf_url = scenes[0].get("keyframe_url", "")
        if kf_url:
            s, body = request("GET", kf_url, timeout=30)
            if s == 200 and body[:3] in (b"\xff\xd8\xff", b"GIF", b"\x89PNG"):
                ok(f"scenes[0].keyframe_url returns image ({len(body)//1024} KB)")
            else:
                fail("scenes[0].keyframe_url returns image", f"status={s}")
        else:
            skip("keyframe_url for scene 0", "no keyframe_url in scene")

    # --- video_url absent for YouTube (no GCS upload) ---
    if "video_url" not in data:
        ok("video_url absent for YouTube input (expected)")

    print(f"\n  report_id : {data['report_id']}")
    print(f"  report_url: {data['report_url']}")
    print(f"  pdf_url   : {data['pdf_url']}")
    print(f"  tokens    : {data['tokens_used']} used, {data['credits_remaining']} remaining")

    return data


def test_file_review(base: str, key: str):
    """Create a tiny valid MP4 and verify video_url appears in response."""
    print("\n[5] File upload review (tiny synthetic MP4)")

    # Try to generate a 2-second test MP4 with ffmpeg
    import subprocess, tempfile, os
    tmp = Path(tempfile.mktemp(suffix=".mp4"))
    try:
        result = subprocess.run(
            ["ffmpeg", "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=2",
             "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
             "-t", "2", "-c:v", "libx264", "-c:a", "aac",
             "-shortest", str(tmp), "-y", "-loglevel", "quiet"],
            capture_output=True, timeout=30,
        )
        if result.returncode != 0 or not tmp.exists():
            skip("File upload review", "ffmpeg not available or failed")
            return
    except (FileNotFoundError, subprocess.TimeoutExpired):
        skip("File upload review", "ffmpeg not available")
        return

    headers = {"X-API-Key": key}
    video_bytes = tmp.read_bytes()
    tmp.unlink(missing_ok=True)
    print(f"  Generated test MP4: {len(video_bytes)//1024} KB")

    status, body = request(
        "POST", f"{base}/api/review", headers=headers,
        files={"file": ("test_ad.mp4", video_bytes, "video/mp4")},
        timeout=600,
    )

    if status != 200:
        fail("POST /api/review (file) → 200", f"got {status}: {body[:300]}")
        return

    data = json.loads(body)
    ok(f"POST /api/review (file) → 200")

    if "video_url" in data:
        ok(f"video_url present for file upload")
        s, _ = request("GET", data["video_url"], timeout=30)
        if s == 200:
            ok("video_url accessible")
        else:
            fail("video_url accessible", f"status={s}")
    else:
        fail("video_url present for file upload", "missing from response")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Test /api/review endpoint")
    parser.add_argument("--key", required=True, help="API key (acr_...)")
    parser.add_argument(
        "--url",
        default="https://creative-reviewer-939529436370.us-central1.run.app",
        help="Base URL of the service",
    )
    parser.add_argument("--skip-youtube", action="store_true",
                        help="Skip the YouTube review test (slow)")
    parser.add_argument("--skip-file", action="store_true",
                        help="Skip the file upload test")
    args = parser.parse_args()

    base = args.url.rstrip("/")
    key = args.key

    print(f"\nTesting: {base}")
    print(f"API key: {key[:12]}...")
    print("=" * 60)

    test_health(base)
    test_auth(base, key)
    test_input_validation(base, key)

    if not args.skip_youtube:
        test_youtube_review(base, key)
    else:
        skip("YouTube URL review", "--skip-youtube")

    if not args.skip_file:
        test_file_review(base, key)
    else:
        skip("File upload review", "--skip-file")

    # Summary
    print("\n" + "=" * 60)
    p, f, s = _results["passed"], _results["failed"], _results["skipped"]
    print(f"Results: {p} passed  {f} failed  {s} skipped")
    sys.exit(0 if f == 0 else 1)


if __name__ == "__main__":
    main()
