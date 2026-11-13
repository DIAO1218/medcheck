"""Keep the two required locations of the architecture blueprint in sync.

The requirement sheet puts the artefact in `./docs/architecture/` (D2) and the
required repository structure puts it at the root (Section 5). We satisfy both by
mirroring, and this script makes drift impossible rather than unlikely.

    python scripts/sync_blueprint.py            # copy root -> docs/architecture/
    python scripts/sync_blueprint.py --check    # fail if they differ
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "architecture-blueprint.md"
MIRROR = ROOT / "docs" / "architecture" / "architecture-blueprint.md"


def in_sync() -> bool:
    return SOURCE.is_file() and MIRROR.is_file() and SOURCE.read_bytes() == MIRROR.read_bytes()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.check:
        if in_sync():
            print("PASS: architecture blueprint is identical in both required locations")
            return 0
        print(
            "FAIL: architecture-blueprint.md and docs/architecture/architecture-blueprint.md differ; "
            "run scripts/sync_blueprint.py",
            file=sys.stderr,
        )
        return 1

    MIRROR.write_bytes(SOURCE.read_bytes())
    print(f"copied {SOURCE.name} -> {MIRROR.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
