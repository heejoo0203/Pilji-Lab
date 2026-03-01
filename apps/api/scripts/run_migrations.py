from __future__ import annotations

import subprocess
from pathlib import Path
import sys


def main() -> int:
    api_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from alembic.config import main; main(argv=['upgrade', 'head'])",
        ],
        cwd=api_root,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
