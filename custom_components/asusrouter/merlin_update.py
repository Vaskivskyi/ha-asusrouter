"""Asuswrt-Merlin firmware update helpers."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import hashlib
import logging
from pathlib import Path
import re
import tempfile
from typing import Any
from zipfile import BadZipFile, ZipFile

import aiohttp
from asusrouter.connection_config import ARConnectionConfigKey as ARCCKey

_LOGGER = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024
DOWNLOAD_PAGE = "https://www.asuswrt-merlin.net/download"
FWUPDATE_MANIFEST_URL = "https://fwupdate.asuswrt-merlin.net/manifest2.txt"
HTTP_OK = 200
MANIFEST_MIN_PARTS = 3
SOURCEFORGE_RELEASE_URL = (
    "https://sourceforge.net/projects/asuswrt-merlin/files/"
    "{model}/Release/{zip_name}/download"
)
MERLIN_VERSION = re.compile(
    r"^3\.0\.0\.(?P<branch>[46])\.(?P<tail>\d+\.\d+_\d+(?:_rog)?)$"
)
FIRMWARE_EXTENSIONS = {".pkgtb", ".trx", ".w"}

ProgressCallback = Callable[[int], None]


class MerlinUpdateError(Exception):
    """Raised when a Merlin update cannot be prepared or uploaded."""


def is_merlin_firmware(version: str | None) -> bool:
    """Return true when the firmware version looks like Asuswrt-Merlin."""

    if not version:
        return False

    return bool(MERLIN_VERSION.match(version))


def _filename_token(version: str) -> str:
    match = MERLIN_VERSION.match(version)
    if not match:
        raise MerlinUpdateError(
            f"`{version}` is not a supported Merlin version"
        )

    return f"300{match.group('branch')}_{match.group('tail')}"


def _sourceforge_url(model: str, version: str) -> tuple[str, str]:
    token = _filename_token(version)
    zip_name = f"{model}_{token}.zip"

    return zip_name, SOURCEFORGE_RELEASE_URL.format(
        model=model,
        zip_name=zip_name,
    )


def _manifest_version(firmware: str, extension: str) -> str:
    match = re.fullmatch(r"(?P<base>300[46])\.(?P<tail>\d+\.\d+)", firmware)
    if not match or not extension.isdigit():
        raise MerlinUpdateError(
            "Merlin update manifest contains an unsupported version format"
        )

    base = match.group("base")
    return (
        f"3.0.0.{base[-1]}."
        f"{match.group('tail')}_{extension}"
    )


async def _confirmed_manifest_version(
    session: aiohttp.ClientSession,
    model: str,
    version: str,
) -> None:
    headers = {"User-Agent": "Home Assistant AsusRouter Merlin updater"}

    try:
        async with session.get(
            FWUPDATE_MANIFEST_URL,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=60),
        ) as response:
            if response.status != HTTP_OK:
                raise MerlinUpdateError(
                    "Merlin update manifest failed with "
                    f"HTTP {response.status}"
                )
            manifest = await response.text()
    except aiohttp.ClientError as ex:
        raise MerlinUpdateError(
            "Could not fetch Merlin update manifest"
        ) from ex

    for line in manifest.splitlines():
        parts = line.strip().split("#")
        if len(parts) < MANIFEST_MIN_PARTS or parts[0] != model:
            continue

        values = {}
        for part in parts[1:]:
            if part.startswith("FW"):
                values["FW"] = part[2:]
            elif part.startswith("EXT"):
                values["EXT"] = part[3:]

        manifest_firmware = values.get("FW")
        manifest_extension = values.get("EXT")
        if not manifest_firmware or manifest_extension is None:
            raise MerlinUpdateError(
                f"Merlin update manifest entry for `{model}` is incomplete"
            )

        manifest_version = _manifest_version(
            manifest_firmware,
            manifest_extension,
        )
        if manifest_version != version:
            raise MerlinUpdateError(
                "Merlin update manifest reports "
                f"`{manifest_version}` for `{model}`, not `{version}`"
            )

        return

    raise MerlinUpdateError(
        f"Merlin update manifest does not contain `{model}`"
    )


async def _download_file(
    session: aiohttp.ClientSession,
    url: str,
    destination: Path,
) -> None:
    headers = {"User-Agent": "Home Assistant AsusRouter Merlin updater"}

    async with session.get(
        url,
        headers=headers,
        allow_redirects=True,
        timeout=aiohttp.ClientTimeout(total=900),
    ) as response:
        if response.status != HTTP_OK:
            raise MerlinUpdateError(
                f"Merlin download failed with HTTP {response.status}"
            )

        with destination.open("wb") as file:
            async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                file.write(chunk)


def _extract_firmware(
    zip_path: Path,
    extract_dir: Path,
    model: str,
    version: str,
) -> Path:
    expected_prefix = f"{model}_{_filename_token(version)}"

    try:
        with ZipFile(zip_path) as archive:
            members = [
                member
                for member in archive.infolist()
                if not member.is_dir()
                and Path(member.filename).suffix.lower()
                in FIRMWARE_EXTENSIONS
            ]

            matches = [
                member
                for member in members
                if Path(member.filename).name.startswith(expected_prefix)
            ]

            if len(matches) != 1:
                raise MerlinUpdateError(
                    "Merlin zip did not contain exactly one firmware image "
                    f"matching `{expected_prefix}`"
                )

            member = matches[0]
            firmware_name = Path(member.filename).name
            firmware_path = extract_dir / firmware_name

            with (
                archive.open(member) as source,
                firmware_path.open("wb") as destination,
            ):
                while chunk := source.read(CHUNK_SIZE):
                    destination.write(chunk)

    except BadZipFile as ex:
        raise MerlinUpdateError(
            "Downloaded Merlin file is not a valid zip"
        ) from ex

    return firmware_path


async def _published_sha256(
    session: aiohttp.ClientSession,
    firmware_name: str,
) -> str | None:
    try:
        async with session.get(
            DOWNLOAD_PAGE,
            headers={"User-Agent": "Home Assistant AsusRouter Merlin updater"},
            timeout=aiohttp.ClientTimeout(total=60),
        ) as response:
            if response.status != HTTP_OK:
                return None
            text = await response.text()
    except (TimeoutError, aiohttp.ClientError):
        return None

    pattern = re.compile(
        rf"\b([a-fA-F0-9]{{64}})\s+{re.escape(firmware_name)}\b"
    )
    match = pattern.search(text)

    return match.group(1).lower() if match else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


async def _upload_firmware(
    api: Any,
    firmware_path: Path,
) -> None:
    if not await api.async_connect():
        raise MerlinUpdateError(
            "Could not connect to the router before upload"
        )

    connection = getattr(api, "_connection", None)
    if connection is None:
        raise MerlinUpdateError("Router connection is not available")

    session = getattr(connection, "_session", None)
    headers = getattr(connection, "_header", None)
    if session is None or session.closed or not headers:
        raise MerlinUpdateError(
            "Authenticated router session is not available"
        )

    url = f"{connection.webpanel}/upgrade.cgi"
    verify_ssl = connection.config.get(ARCCKey.VERIFY_SSL)

    form = aiohttp.FormData()
    form.add_field("current_page", "Advanced_FirmwareUpgrade_Content.asp")
    form.add_field("next_page", "")
    form.add_field("action_mode", "")
    form.add_field("action_script", "")
    form.add_field("action_wait", "")
    form.add_field(
        "file",
        await asyncio.to_thread(firmware_path.read_bytes),
        filename=firmware_path.name,
        content_type="application/octet-stream",
    )

    try:
        async with session.post(
            url,
            data=form,
            headers=headers,
            ssl=verify_ssl,
            timeout=aiohttp.ClientTimeout(total=900),
        ) as response:
            if response.status != HTTP_OK:
                raise MerlinUpdateError(
                    "Router firmware upload failed with HTTP "
                    f"{response.status}"
                )

            text = await response.text(errors="ignore")
            if "UpdateError" in text:
                raise MerlinUpdateError(
                    "The router rejected the uploaded firmware image"
                )

    except aiohttp.ServerDisconnectedError:
        _LOGGER.debug("Router disconnected during firmware upload")
    except aiohttp.ClientError as ex:
        raise MerlinUpdateError("Router firmware upload failed") from ex


async def install_merlin_update(
    api: Any,
    model: str,
    latest_version: str,
    progress: ProgressCallback | None = None,
) -> None:
    """Download, validate, and upload a Merlin firmware update."""

    if progress is None:
        def _ignore_progress(_: int) -> None:
            return None

        progress = _ignore_progress

    zip_name, download_url = _sourceforge_url(model, latest_version)

    async with aiohttp.ClientSession() as session:
        with tempfile.TemporaryDirectory(prefix="asusrouter-merlin-") as temp:
            temp_dir = Path(temp)
            zip_path = temp_dir / zip_name

            progress(5)
            await _confirmed_manifest_version(session, model, latest_version)
            progress(10)

            _LOGGER.info(
                "Downloading Merlin firmware `%s` from SourceForge",
                zip_name,
            )
            await _download_file(session, download_url, zip_path)
            progress(35)

            firmware_path = _extract_firmware(
                zip_path,
                temp_dir,
                model,
                latest_version,
            )
            progress(45)

            expected_sha = await _published_sha256(session, firmware_path.name)
            if expected_sha is None:
                raise MerlinUpdateError(
                    "No published SHA256 found for "
                    f"`{firmware_path.name}`; refusing to upload firmware"
                )

            actual_sha = await asyncio.to_thread(_sha256, firmware_path)
            if actual_sha != expected_sha:
                raise MerlinUpdateError(
                    "Downloaded Merlin firmware failed SHA256 validation"
                )
            _LOGGER.info("Validated Merlin firmware SHA256")

            progress(55)
            await _upload_firmware(api, firmware_path)
            progress(90)
