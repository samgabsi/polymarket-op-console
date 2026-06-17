from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.live_v3 import create_demo_data  # noqa: E402


def main() -> int:
    result = create_demo_data()
    print(json.dumps({"ok": result.get("ok"), "path": result.get("path"), "secret_values_returned": result.get("secret_values_returned"), "order_submitted": result.get("order_submitted"), "order_cancelled": result.get("order_cancelled"), "live_trading_armed": result.get("live_trading_armed")}, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
