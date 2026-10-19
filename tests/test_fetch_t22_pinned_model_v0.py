"""Trusted transport and artifact checks using byte streams, no network/model."""

from contextlib import contextmanager
import hashlib
import io
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_t22_pinned_model_v0 as fetch


@contextmanager
def response(body, final_url="https://huggingface.co/pinned"):
    stream = io.BytesIO(body)
    stream.geturl = lambda: final_url
    yield stream


def metadata(body):
    return {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}


def test_download_is_verified_then_published_and_idempotent(tmp_path):
    body = b"verified model bytes"
    target = tmp_path / "model.safetensors"
    fetch.fetch_file(target, "https://huggingface.co/pinned", metadata(body),
                     opener=lambda *a, **kw: response(body))
    assert target.read_bytes() == body
    assert not target.with_suffix(".safetensors.partial").exists()
    fetch.fetch_file(target, "https://huggingface.co/pinned", metadata(body),
                     opener=lambda *a, **kw: pytest.fail("Verified file was fetched again"))


@pytest.mark.parametrize("body", [b"short", b"too many bytes", b"12345678"])
def test_mismatch_never_publishes_artifact(tmp_path, body):
    target = tmp_path / "model.safetensors"
    with pytest.raises(ValueError):
        fetch.fetch_file(target, "https://huggingface.co/pinned", metadata(b"abcdefgh"),
                         opener=lambda *a, **kw: response(body))
    assert not target.exists()
    assert not target.with_suffix(".safetensors.partial").exists()


def test_existing_unknown_file_is_preserved(tmp_path):
    target = tmp_path / "model.safetensors"
    target.write_bytes(b"user file")
    with pytest.raises(ValueError, match="Existing file"):
        fetch.fetch_file(target, "https://huggingface.co/pinned", metadata(b"expected"))
    assert target.read_bytes() == b"user file"


def test_insecure_redirect_and_preexisting_partial_are_rejected(tmp_path):
    target = tmp_path / "model.safetensors"
    with pytest.raises(ValueError, match="non-HTTPS"):
        fetch.fetch_file(target, "https://huggingface.co/pinned", metadata(b"abc"),
                         opener=lambda *a, **kw: response(b"abc", "http://mirror.invalid/file"))
    partial = tmp_path / "model.safetensors.partial"
    partial.write_bytes(b"existing partial")
    with pytest.raises(FileExistsError):
        fetch.fetch_file(target, "https://huggingface.co/pinned", metadata(b"abc"),
                         opener=lambda *a, **kw: response(b"abc"))
    assert partial.read_bytes() == b"existing partial"


def test_stream_interruption_never_leaves_usable_artifact(tmp_path):
    class Interrupted(io.BytesIO):
        def geturl(self):
            return "https://huggingface.co/pinned"

        def read(self, *args):
            raise OSError("interrupted transport")

    target = tmp_path / "model.safetensors"
    with pytest.raises(OSError, match="interrupted"):
        fetch.fetch_file(target, "https://huggingface.co/pinned", metadata(b"abc"),
                         opener=lambda *a, **kw: Interrupted(b"abc"))
    assert not target.exists()
    assert not (tmp_path / "model.safetensors.partial").exists()
