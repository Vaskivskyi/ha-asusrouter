"""Build README.md from the modular sources in `readme/`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).parent.parent
README_DIR = ROOT / "readme"
SHARED_DIR = README_DIR / "shared"
TEMPLATE = README_DIR / "README.template.md"
DEVICES = SHARED_DIR / "devices.json"
OUTPUT = ROOT / "README.md"

BANNER = (
    "<!-- This file is generated from `readme/` by "
    "`scripts/build_readme.py`. Do not edit it directly. -->\n"
)

INCLUDE_RE = re.compile(r"^<!-- include:\s*(?P<path>.+?)\s*-->$", re.MULTILINE)
DEVICES_MARKER = "<!-- devices -->"


def device_page(base: str, slug: str) -> str:
    """Build the device page markdown link target, escaping parentheses."""

    url = f"{base}{slug}.md"
    # Markdown needs angle brackets around URLs containing parentheses
    if "(" in slug or ")" in slug:
        return f"<{url}>"
    return url


def device_entry(base: str, device: dict[str, Any]) -> str:
    """Render one device as `[Name](page) ([find it](amazon))`."""

    page = device_page(base, device["slug"])
    entry = f"[{device['name']}]({page})"
    amazon = device.get("amazon")
    if amazon:
        entry += f" ([find it]({amazon}))"
    return entry


def validate(data: dict[str, Any]) -> None:
    """Fail loud on a malformed devices.json before rendering."""

    gen_ids = {g["id"] for g in data["wifi_generations"]}
    status_ids = set(data["statuses"])
    seen_slugs: set[str] = set()

    for device in data["devices"]:
        name = device.get("name", "<unnamed>")
        for key in ("name", "slug", "wifi", "status"):
            if not device.get(key):
                raise ValueError(f"Device {name!r} is missing '{key}'")
        if device["wifi"] not in gen_ids:
            raise ValueError(
                f"Device {name!r} has unknown wifi {device['wifi']!r}"
            )
        if device["status"] not in status_ids:
            raise ValueError(
                f"Device {name!r} has unknown status {device['status']!r}"
            )
        if device["slug"] in seen_slugs:
            raise ValueError(f"Duplicate slug {device['slug']!r}")
        seen_slugs.add(device["slug"])


def render_devices(data: dict[str, Any]) -> str:
    """Render every WiFi generation as a collapsible status-grouped list."""

    base = data["device_page_base"]
    statuses = data["statuses"]
    devices = data["devices"]

    # Confirmed before expected, following the order in the statuses map
    status_order = list(statuses)

    blocks = []
    for generation in data["wifi_generations"]:
        gen_id = generation["id"]
        rows = [d for d in devices if d["wifi"] == gen_id]
        if not rows:
            continue

        groups = []
        for status_key in status_order:
            group = [d for d in rows if d["status"] == status_key]
            if not group:
                continue
            status = statuses[status_key]
            entries = ", ".join(device_entry(base, d) for d in group)
            groups.append(
                f"**{status['emoji']} {status['label']}:** {entries}"
            )

        summary = f"<b>{generation['label']}</b> — {len(rows)} devices"
        body = "\n\n".join(groups)
        blocks.append(
            f"<details>\n<summary>{summary}</summary>\n\n{body}\n\n</details>"
        )

    return "\n\n".join(blocks)


def build() -> str:
    """Render the full README content."""

    template = TEMPLATE.read_text(encoding="utf-8")
    data = json.loads(DEVICES.read_text(encoding="utf-8"))
    validate(data)

    def replace_include(match: re.Match[str]) -> str:
        path = (README_DIR / match.group("path")).resolve()
        return path.read_text(encoding="utf-8").strip()

    content = INCLUDE_RE.sub(replace_include, template)
    content = content.replace(DEVICES_MARKER, render_devices(data))

    return BANNER + "\n" + content.strip() + "\n"


def main() -> None:
    """Build the README or check that it is up to date."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if README.md is out of date instead of writing it",
    )
    args = parser.parse_args()

    content = build()

    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != content:
            print(
                "README.md is out of date. "
                "Run `python scripts/build_readme.py`.",
                file=sys.stderr,
            )
            sys.exit(1)
        print("README.md is up to date.")
        return

    OUTPUT.write_text(content, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
