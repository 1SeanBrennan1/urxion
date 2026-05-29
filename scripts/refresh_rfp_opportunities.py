#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rfp_opportunity_cache import CACHE_PATH, refresh_opportunity_cache


def main() -> None:
    payload = refresh_opportunity_cache()
    print(f"Refreshed {payload.get('count', 0)} RFP opportunities")
    print(f"Cache: {CACHE_PATH}")
    print(f"Fetched at: {payload.get('fetched_at')}")


if __name__ == "__main__":
    main()
