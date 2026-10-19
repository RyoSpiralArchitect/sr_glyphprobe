"""Range transport and resume checks with synthetic bytes; no network or model."""

import hashlib
import http.client
import io
from pathlib import Path
import re
import ssl
import sys
import threading
import urllib.error

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_t22_pinned_model_ranges_v0 as fetch


URL = "https://huggingface.co/pinned/model.safetensors"
BODY = b"abcdefghijklmnopqrstuvwxyz012345"
CHUNK_BYTES = 8


@pytest.fixture(autouse=True)
def retry_sleeps(monkeypatch):
    delays = []
    monkeypatch.setattr(fetch.time, "sleep", delays.append)
    return delays


def metadata(body):
    return {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}


class Response(io.BytesIO):
    def __init__(self, body, start, end, total, *, status=206, final_url=URL):
        super().__init__(body)
        self.status = status
        self.headers = {
            "Content-Range": f"bytes {start}-{end}/{total}",
            "Content-Length": str(len(body)),
        }
        self.final_url = final_url

    def geturl(self):
        return self.final_url

    def getcode(self):
        return self.status


class RangeOpener:
    def __init__(self, body=BODY, transform=None):
        self.body = body
        self.transform = transform
        self.calls = []
        self.lock = threading.Lock()

    def __call__(self, request, *, timeout):
        assert timeout > 0
        assert request.full_url.startswith("https://")
        match = re.fullmatch(r"bytes=(\d+)-(\d+)", request.get_header("Range"))
        assert match, "Every request must bound its byte range explicitly"
        start, end = map(int, match.groups())
        assert 0 <= start <= end < len(self.body)
        with self.lock:
            self.calls.append((start, end))
        result = Response(self.body[start : end + 1], start, end, len(self.body))
        return self.transform(result, start, end) if self.transform else result


def paths(tmp_path):
    destination = tmp_path / "model" / "model.safetensors"
    destination.parent.mkdir()
    return destination, tmp_path / "external-range-cache"


def download(destination, cache, opener, *, expected=None, prefix_file=None, workers=1):
    fetch.fetch_range_file(
        destination,
        URL,
        expected or metadata(BODY),
        cache_root=cache,
        workers=workers,
        chunk_bytes=CHUNK_BYTES,
        prefix_file=prefix_file,
        timeout=5,
        opener=opener,
    )


def snapshot(path):
    stat = path.stat()
    return path.read_bytes(), stat.st_mtime_ns, stat.st_ino


def test_parallel_out_of_order_ranges_publish_verified_artifact(tmp_path):
    destination, cache = paths(tmp_path)
    later_finished = threading.Event()
    completion_order = []
    lock = threading.Lock()

    def out_of_order(response, start, end):
        if start == 0:
            assert later_finished.wait(5), "Range requests did not run concurrently"
        else:
            with lock:
                completion_order.append(start)
            later_finished.set()
        return response

    opener = RangeOpener(transform=out_of_order)
    download(destination, cache, opener, workers=4)
    assert destination.read_bytes() == BODY
    assert sorted(opener.calls) == [(0, 7), (8, 15), (16, 23), (24, 31)]
    assert completion_order and completion_order[0] != 0
    download(destination, cache, lambda *a, **kw: pytest.fail("Verified artifact fetched again"))


@pytest.mark.parametrize(
    "failure",
    ["status", "missing_range", "wrong_start", "wrong_end", "wrong_total", "malformed_range", "content_length", "missing_length"],
)
def test_invalid_range_metadata_never_publishes(tmp_path, failure):
    destination, cache = paths(tmp_path)

    def invalidate(response, start, end):
        if failure == "status":
            response.status = 200
        elif failure == "missing_range":
            del response.headers["Content-Range"]
        elif failure == "wrong_start":
            response.headers["Content-Range"] = f"bytes {start + 1}-{end}/{len(BODY)}"
        elif failure == "wrong_end":
            response.headers["Content-Range"] = f"bytes {start}-{end + 1}/{len(BODY)}"
        elif failure == "wrong_total":
            response.headers["Content-Range"] = f"bytes {start}-{end}/{len(BODY) + 1}"
        elif failure == "malformed_range":
            response.headers["Content-Range"] = "bytes */32"
        elif failure == "missing_length":
            del response.headers["Content-Length"]
        else:
            response.headers["Content-Length"] = str(end - start + 2)
        return response

    with pytest.raises(ValueError):
        download(destination, cache, RangeOpener(transform=invalidate))
    assert not destination.exists()


@pytest.mark.parametrize("body_delta", [-1, 1])
def test_short_or_long_response_body_never_publishes(tmp_path, body_delta):
    destination, cache = paths(tmp_path)

    def invalidate(response, start, end):
        replacement = BODY[start:end] if body_delta < 0 else BODY[start : end + 1] + b"!"
        result = Response(replacement, start, end, len(BODY))
        # Keep the promised length correct; the actual body must be checked too.
        result.headers["Content-Length"] = str(end - start + 1)
        return result

    with pytest.raises(ValueError):
        download(destination, cache, RangeOpener(transform=invalidate))
    assert not destination.exists()


def test_complete_file_hash_mismatch_never_publishes(tmp_path):
    destination, cache = paths(tmp_path)
    wrong_body = b"!" + BODY[1:]
    with pytest.raises(ValueError):
        download(destination, cache, RangeOpener(wrong_body))
    assert not destination.exists()


def test_prefix_is_read_only_and_ranges_resume_at_its_exact_length(tmp_path):
    destination, cache = paths(tmp_path)
    prefix = tmp_path / "original.partial"
    prefix.write_bytes(BODY[:5])
    before = snapshot(prefix)
    opener = RangeOpener()
    download(destination, cache, opener, prefix_file=prefix)
    assert destination.read_bytes() == BODY
    assert snapshot(prefix) == before
    assert sorted(opener.calls) == [(5, 12), (13, 20), (21, 28), (29, 31)]


def test_failed_transfer_preserves_prefix(tmp_path):
    destination, cache = paths(tmp_path)
    prefix = tmp_path / "original.partial"
    prefix.write_bytes(BODY[:5])
    before = snapshot(prefix)

    def fail(*args, **kwargs):
        raise OSError("synthetic interruption")

    with pytest.raises(OSError, match="synthetic interruption"):
        download(destination, cache, fail, prefix_file=prefix)
    assert snapshot(prefix) == before
    assert not destination.exists()


def interrupted_cache(destination, cache, prefix_file=None):
    start = prefix_file.stat().st_size if prefix_file else 0

    def interrupt_after_first(response, request_start, end):
        if request_start > start:
            raise OSError("synthetic interruption")
        return response

    opener = RangeOpener(transform=interrupt_after_first)
    with pytest.raises(OSError, match="synthetic interruption"):
        download(destination, cache, opener, prefix_file=prefix_file)
    assert not destination.exists()
    cached = list(cache.rglob("*.bin"))
    assert len(cached) == 1
    return start, cached[0]


@pytest.mark.parametrize("prefix_bytes", [0, 5])
def test_resume_reuses_verified_cached_chunk(tmp_path, prefix_bytes):
    destination, cache = paths(tmp_path)
    prefix = None
    if prefix_bytes:
        prefix = tmp_path / "original.partial"
        prefix.write_bytes(BODY[:prefix_bytes])
    start, cached = interrupted_cache(destination, cache, prefix)
    before = snapshot(cached)
    prefix_before = snapshot(prefix) if prefix else None
    opener = RangeOpener()
    download(destination, cache, opener, prefix_file=prefix)
    assert destination.read_bytes() == BODY
    assert all(request_start >= start + CHUNK_BYTES for request_start, _ in opener.calls)
    assert snapshot(cached) == before
    if prefix:
        assert snapshot(prefix) == prefix_before


def test_cached_chunk_is_rehashed_and_corruption_is_preserved(tmp_path):
    destination, cache = paths(tmp_path)
    _, cached = interrupted_cache(destination, cache)
    cached.write_bytes(b"!" + cached.read_bytes()[1:])
    before = snapshot(cached)
    with pytest.raises(ValueError):
        download(destination, cache, lambda *a, **kw: pytest.fail("Corrupt cache used for a download"))
    assert not destination.exists()
    assert snapshot(cached) == before


def test_non_https_redirect_never_publishes(tmp_path):
    destination, cache = paths(tmp_path)

    def redirect(response, start, end):
        response.final_url = "http://mirror.invalid/model"
        return response

    with pytest.raises(ValueError):
        download(destination, cache, RangeOpener(transform=redirect))
    assert not destination.exists()


def test_non_https_source_rejected_without_request(tmp_path):
    destination, cache = paths(tmp_path)
    with pytest.raises(ValueError):
        fetch.fetch_range_file(
            destination,
            "http://mirror.invalid/model",
            metadata(BODY),
            cache_root=cache,
            opener=lambda *a, **kw: pytest.fail("Insecure source was requested"),
        )
    assert not destination.exists()


def test_existing_unknown_destination_is_preserved_without_request(tmp_path):
    destination, cache = paths(tmp_path)
    destination.write_bytes(b"original user file")
    before = snapshot(destination)
    with pytest.raises(ValueError):
        download(destination, cache, lambda *a, **kw: pytest.fail("Unknown destination was replaced"))
    assert snapshot(destination) == before


def download_single_range(destination, cache, opener):
    fetch.fetch_range_file(
        destination,
        URL,
        metadata(BODY),
        cache_root=cache,
        workers=1,
        chunk_bytes=len(BODY),
        timeout=5,
        opener=opener,
    )


def test_two_incomplete_bodies_retry_exact_range_then_publish(tmp_path, retry_sleeps):
    destination, cache = paths(tmp_path)
    attempts = 0

    def short_twice(response, start, end):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            result = Response(BODY[:-1], start, end, len(BODY))
            result.headers["Content-Length"] = str(len(BODY))
            return result
        return response

    opener = RangeOpener(transform=short_twice)
    download_single_range(destination, cache, opener)
    assert opener.calls == [(0, len(BODY) - 1)] * 3
    assert retry_sleeps == [1, 3]
    assert destination.read_bytes() == BODY


def test_three_incomplete_bodies_exhaust_bounded_attempts(tmp_path, retry_sleeps):
    destination, cache = paths(tmp_path)

    def always_short(response, start, end):
        result = Response(BODY[:-1], start, end, len(BODY))
        result.headers["Content-Length"] = str(len(BODY))
        return result

    opener = RangeOpener(transform=always_short)
    with pytest.raises(ValueError):
        download_single_range(destination, cache, opener)
    assert opener.calls == [(0, len(BODY) - 1)] * 3
    assert retry_sleeps == [1, 3]
    assert not destination.exists()


@pytest.mark.parametrize(
    "failure",
    ["status", "range", "length", "too_long", "artifact_hash"],
)
def test_validation_failures_are_not_retried(tmp_path, retry_sleeps, failure):
    destination, cache = paths(tmp_path)

    def invalidate(response, start, end):
        if failure == "status":
            response.status = 200
        elif failure == "range":
            response.headers["Content-Range"] = "bytes */32"
        elif failure == "length":
            response.headers["Content-Length"] = str(len(BODY) - 1)
        elif failure == "too_long":
            response = Response(BODY + b"!", start, end, len(BODY))
            response.headers["Content-Length"] = str(len(BODY))
        else:
            response = Response(b"!" + BODY[1:], start, end, len(BODY))
        return response

    opener = RangeOpener(transform=invalidate)
    with pytest.raises(ValueError):
        download_single_range(destination, cache, opener)
    assert opener.calls == [(0, len(BODY) - 1)]
    assert retry_sleeps == []
    assert not destination.exists()


@pytest.mark.parametrize(
    "error_factory",
    [
        pytest.param(lambda: TimeoutError("synthetic timeout"), id="timeout"),
        pytest.param(lambda: ConnectionResetError("synthetic reset"), id="reset"),
        pytest.param(lambda: http.client.IncompleteRead(b"abc", 29), id="incomplete_read"),
        pytest.param(lambda: urllib.error.URLError(TimeoutError("synthetic timeout")), id="url_timeout"),
        pytest.param(lambda: urllib.error.URLError(ConnectionResetError("synthetic reset")), id="url_reset"),
        pytest.param(lambda: urllib.error.URLError(http.client.IncompleteRead(b"abc", 29)), id="url_incomplete_read"),
    ],
)
def test_transient_transport_error_retries_same_range(tmp_path, retry_sleeps, error_factory):
    destination, cache = paths(tmp_path)
    attempts = []
    good_opener = RangeOpener()

    def interrupted_once(request, *, timeout):
        attempts.append(request.get_header("Range"))
        if len(attempts) == 1:
            raise error_factory()
        return good_opener(request, timeout=timeout)

    download_single_range(destination, cache, interrupted_once)
    assert attempts == [f"bytes=0-{len(BODY) - 1}"] * 2
    assert retry_sleeps == [1]
    assert destination.read_bytes() == BODY


@pytest.mark.parametrize("wrapped", [False, True])
def test_tls_certificate_verification_failure_is_not_retried(tmp_path, retry_sleeps, wrapped):
    destination, cache = paths(tmp_path)
    attempts = []

    def certificate_failure(request, *, timeout):
        attempts.append(request.get_header("Range"))
        error = ssl.SSLCertVerificationError("synthetic certificate verification failure")
        raise urllib.error.URLError(error) if wrapped else error

    expected_error = urllib.error.URLError if wrapped else ssl.SSLCertVerificationError
    with pytest.raises(expected_error):
        download_single_range(destination, cache, certificate_failure)
    assert attempts == [f"bytes=0-{len(BODY) - 1}"]
    assert retry_sleeps == []
    assert not destination.exists()
