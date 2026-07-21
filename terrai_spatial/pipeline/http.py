"""One HTTP path for every pipeline script.

A single User-Agent naming the repository, one default timeout, and retry with
backoff on transient network errors — generalized from the only script that
had retries before this module existed. Non-network failures (size caps,
malformed JSON) are raised immediately rather than retried.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path
from typing import Any


USER_AGENT = "TerrAI-Spatial-Intelligence/0.3 (+https://github.com/TsumiNa/terrai-spatial-intelligence)"
DEFAULT_TIMEOUT = 30
RETRIES = 3
BACKOFF_SECONDS = 0.5
_CHUNK_BYTES = 1024 * 1024


class ResponseRejectedError(RuntimeError):
    """A response was received but refused; retrying cannot help."""


def _request(url: str, *, headers: dict[str, str] | None = None, data: bytes | None = None) -> urllib.request.Request:
    return urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})})


def _with_retries(url: str, operation: Any) -> Any:
    last_error: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            return operation()
        except ResponseRejectedError:
            raise
        except (OSError, TimeoutError) as error:
            last_error = error
            if attempt < RETRIES:
                time.sleep(BACKOFF_SECONDS * attempt)
    raise RuntimeError(f"failed to download {url}: {last_error}") from last_error


def response_provenance(response: Any) -> dict[str, str | None]:
    return {
        "resolved_url": response.geturl(),
        "http_last_modified": response.headers.get("Last-Modified"),
        "http_etag": response.headers.get("ETag"),
        "http_content_type": response.headers.get("Content-Type"),
    }


def download_bytes(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int | None = None,
    headers: dict[str, str] | None = None,
) -> bytes:
    def attempt() -> bytes:
        with urllib.request.urlopen(_request(url, headers=headers), timeout=timeout) as response:
            payload = bytearray()
            while chunk := response.read(_CHUNK_BYTES):
                payload.extend(chunk)
                if max_bytes is not None and len(payload) > max_bytes:
                    raise ResponseRejectedError(f"response from {url} exceeds {max_bytes} bytes")
            return bytes(payload)

    return _with_retries(url, attempt)


def download_file(
    url: str,
    target: Path,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, str | None]:
    """Stream a response into ``target`` and return provenance plus its sha256.

    ``target`` is removed on failure so a partial download never looks like a
    completed one.
    """

    def attempt() -> dict[str, str | None]:
        try:
            digest = hashlib.sha256()
            total = 0
            with urllib.request.urlopen(_request(url, headers=headers), timeout=timeout) as response, target.open(
                "wb"
            ) as output:
                while chunk := response.read(_CHUNK_BYTES):
                    total += len(chunk)
                    if max_bytes is not None and total > max_bytes:
                        raise ResponseRejectedError(f"response from {url} exceeds {max_bytes} bytes")
                    digest.update(chunk)
                    output.write(chunk)
                return {**response_provenance(response), "sha256": digest.hexdigest()}
        except BaseException:
            target.unlink(missing_ok=True)
            raise

    return _with_retries(url, attempt)


def download_json(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
) -> tuple[Any, dict[str, str | None]]:
    """GET (or POST, when ``data`` is given) a JSON document with provenance."""

    def attempt() -> tuple[Any, dict[str, str | None]]:
        with urllib.request.urlopen(_request(url, headers=headers, data=data), timeout=timeout) as response:
            provenance = response_provenance(response)
            try:
                value = json.load(response)
            except json.JSONDecodeError as error:
                raise ResponseRejectedError(f"response from {url} is not JSON") from error
        return value, provenance

    return _with_retries(url, attempt)
