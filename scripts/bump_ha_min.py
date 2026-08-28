"""Bump the minimum Home Assistant version in `hacs.json`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
HACS_FILE = ROOT / "hacs.json"
PYPROJECT_FILE = ROOT / "pyproject.toml"

HA_PIN_PATTERN = re.compile(r'"homeassistant==(?P<version>[^"]+)"')
HA_VERSION_PATTERN = re.compile(r"^\d{4}\.\d{1,2}\.\d+$")


def read_pinned_version() -> str | None:
    """Read the HA version pinned for testing in `pyproject.toml`."""

    match = HA_PIN_PATTERN.search(PYPROJECT_FILE.read_text(encoding="utf-8"))
    return match.group("version") if match else None


def read_min_version() -> str:
    """Read the current minimum Home Assistant version from `hacs.json`."""

    data = json.loads(HACS_FILE.read_text(encoding="utf-8"))
    return str(data["homeassistant"])


def write_min_version(version: str) -> None:
    """Write the minimum Home Assistant version into `hacs.json`."""

    data = json.loads(HACS_FILE.read_text(encoding="utf-8"))
    data["homeassistant"] = version
    HACS_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def version_parts(version: str) -> tuple[int, ...]:
    """Split a version into integer parts for ordering."""

    return tuple(int(part) for part in version.split("."))


def main() -> int:
    """Run the script."""

    parser = argparse.ArgumentParser(
        description=(
            "Set the minimum Home Assistant version supported by the "
            "integration. This is the feature floor - the oldest release "
            "providing every API the integration uses - not the version "
            "pinned for testing in pyproject.toml."
        )
    )
    parser.add_argument(
        "version",
        nargs="?",
        help="target version, e.g. 2026.7.0",
    )
    args = parser.parse_args()

    current = read_min_version()
    pinned = read_pinned_version()

    if not args.version:
        print(f"hacs.json minimum:  {current}")
        print(f"pyproject test pin: {pinned or 'not found'}")
        print("\nPass a version to update, e.g. bump_ha_min.py 2026.7.0")
        return 0

    version = args.version.strip()
    if not HA_VERSION_PATTERN.match(version):
        print(
            f"'{version}' is not a Home Assistant version (YYYY.M.P)",
            file=sys.stderr,
        )
        return 1

    if version == current:
        print(f"hacs.json already requires {current}")
        return 0

    write_min_version(version)
    print(f"hacs.json minimum: {current} -> {version}")

    # A pre-release pin (2026.9.0b1) has no integer parts to compare
    if (
        pinned
        and HA_VERSION_PATTERN.match(pinned)
        and version_parts(version) > version_parts(pinned)
    ):
        print(
            f"warning: minimum {version} is above the tested pin {pinned}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
