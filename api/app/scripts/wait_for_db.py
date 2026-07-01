"""Block until Postgres accepts connections (used by container entrypoint)."""

from __future__ import annotations

import sys
import time

from sqlalchemy import text

from app.database import engine


def main() -> int:
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[wait_for_db] database is ready")
            return 0
        except Exception as exc:  # noqa: BLE001
            print(f"[wait_for_db] not ready yet: {exc}")
            time.sleep(2)
    print("[wait_for_db] timed out waiting for database", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
