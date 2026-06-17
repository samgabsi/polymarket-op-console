from __future__ import annotations

import argparse
import json
from pathlib import Path

ROUTES = [
    "/v3", "/v3/command-center", "/v3/search", "/v3/graph", "/v3/workflows",
    "/v3/pre-trade-packet", "/v3/market-brief", "/v3/thesis-health", "/v3/portfolio-brief",
    "/v3/operator-review", "/v3/analytics", "/v3/analytics/decisions", "/v3/analytics/theses", "/v3/analytics/evidence", "/v3/analytics/alerts", "/v3/analytics/governance", "/v3/analytics/calibration", "/v3/analytics/learning-report", "/v3/settings", "/v3/docs", "/v2-live", "/v2-live/strategy", "/v2-live/research",
    "/v2-live/monitoring", "/v2-live/portfolio", "/v2-live/governance", "/v2-live/data",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture or plan v3 screenshot QA routes. Dry-run is safe and dependency-free.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--out", default="runtime_screenshots/v3.3.0-real")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    out = Path(args.out)
    plan = {"version": "3.3.0-real", "base_url": args.base_url.rstrip("/"), "out": str(out), "routes": ROUTES, "screenshots_include_secrets": False, "order_submitted": False, "order_cancelled": False, "live_trading_armed": False}
    if args.dry_run:
        print(json.dumps({"dry_run": True, **plan}, indent=2, sort_keys=True))
        return 0
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        print(json.dumps({"ok": False, "reason": "playwright_not_available", "hint": "Run with --dry-run or install browser automation dependencies locally.", **plan}, indent=2, sort_keys=True))
        return 2
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
        for route in ROUTES:
            url = args.base_url.rstrip("/") + route
            safe_name = route.strip("/").replace("/", "_") or "v3"
            page.goto(url, wait_until="networkidle")
            page.screenshot(path=str(out / f"{safe_name}.png"), full_page=True)
        browser.close()
    print(json.dumps({"ok": True, **plan}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
