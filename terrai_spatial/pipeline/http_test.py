from __future__ import annotations

import hashlib
import json
import urllib.error
from pathlib import Path

import pytest

from terrai_spatial.pipeline import http


class FakeResponse:
    def __init__(self, payload: bytes, url: str = "https://example.test/final") -> None:
        self._payload = payload
        self._offset = 0
        self._url = url
        self.headers = {"Last-Modified": "Mon, 20 Jul 2026 00:00:00 GMT", "ETag": '"tag"', "Content-Type": "application/json"}

    def read(self, size: int | None = None) -> bytes:
        if size is None:
            size = len(self._payload)
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += size
        return chunk

    def geturl(self) -> str:
        return self._url

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def install(monkeypatch: pytest.MonkeyPatch, responses: list[object]) -> list[object]:
    requests: list[object] = []

    def fake_urlopen(request: object, timeout: float) -> object:
        requests.append(request)
        outcome = responses.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(http.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(http.time, "sleep", lambda seconds: None)
    return requests


def test_download_bytes_retries_transient_failures_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    requests = install(
        monkeypatch,
        [
            urllib.error.URLError("connection reset"),
            TimeoutError("timed out"),
            FakeResponse(b"payload"),
        ],
    )

    assert http.download_bytes("https://example.test/data") == b"payload"
    assert len(requests) == 3
    assert all(request.get_header("User-agent") == http.USER_AGENT for request in requests)


def test_download_bytes_gives_up_after_the_last_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    requests = install(monkeypatch, [urllib.error.URLError("down")] * http.RETRIES)

    with pytest.raises(RuntimeError, match="failed to download"):
        http.download_bytes("https://example.test/data")
    assert len(requests) == http.RETRIES


def test_size_cap_rejection_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    requests = install(monkeypatch, [FakeResponse(b"x" * 100)] * http.RETRIES)

    with pytest.raises(http.ResponseRejectedError, match="exceeds 10 bytes"):
        http.download_bytes("https://example.test/data", max_bytes=10)
    assert len(requests) == 1


def test_download_file_removes_the_partial_file_on_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install(monkeypatch, [FakeResponse(b"x" * 100)] * http.RETRIES)
    target = tmp_path / "archive.zip"

    with pytest.raises(http.ResponseRejectedError):
        http.download_file("https://example.test/archive.zip", target, max_bytes=10)
    assert not target.exists()


def test_download_file_records_provenance_and_payload_hash(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"archive bytes")
    target = tmp_path / "target.bin"

    result = http.download_file(source.as_uri(), target)

    assert target.read_bytes() == b"archive bytes"
    assert result["resolved_url"] == source.as_uri()
    assert result["sha256"] == hashlib.sha256(b"archive bytes").hexdigest()


def test_download_json_posts_data_and_rejects_non_json_without_retry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    requests = install(monkeypatch, [FakeResponse(b"{\"ok\": true}")])
    value, provenance = http.download_json("https://example.test/api", data=b"data=query")
    assert value == {"ok": True}
    assert provenance["resolved_url"] == "https://example.test/final"
    assert requests[0].data == b"data=query"

    requests = install(monkeypatch, [FakeResponse(b"<html>")] * http.RETRIES)
    with pytest.raises(http.ResponseRejectedError, match="is not JSON"):
        http.download_json("https://example.test/api")
    assert len(requests) == 1


def test_file_urls_work_for_local_fixture_downloads(tmp_path: Path) -> None:
    source = tmp_path / "fixture.json"
    source.write_text(json.dumps({"fixture": True}), encoding="utf-8")

    assert json.loads(http.download_bytes(source.as_uri())) == {"fixture": True}
