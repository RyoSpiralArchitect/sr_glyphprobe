#!/usr/bin/env python3
"""Loopback-only author-pilot UI with concealed keys and an append-only journal.

GET requests never create human-response records. The opaque cookie authenticates
this running session only; it contains no item identity or answer information.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import fcntl
import hashlib
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import stat
import threading
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts/contextual_emoji_author_pilot_v0.py"
COOKIE = "glyphprobe_author_pilot_session"
JOURNAL_PROTOCOL = "glyphprobe-author-pilot-journal-v0"
PARTICIPANT_IDENTITY = {"pseudonym": "author-01", "role": "author", "prior_model_outcome_exposure_known": True}
CHOICES = {"first", "second", "both", "neither", "ambiguous", "unclear", "abstain"}
RECOGNITION = {"yes", "no", "unsure"}
NATURALNESS = {"good", "awkward", "unclear"}
STATIC = {"/": ("index.html", "text/html; charset=utf-8"),
          "/index.html": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/style.css": ("style.css", "text/css; charset=utf-8")}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def parse_json(data):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    def constant(value):
        raise ValueError("Nonfinite JSON value")
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class APIError(Exception):
    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _generator():
    spec = importlib.util.spec_from_file_location("author_pilot_generator_for_server", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_package(package, root=ROOT):
    """Return only a verified public packet and non-secret package binding."""
    package, root = Path(package).resolve(), Path(root).resolve()
    generator = _generator()
    summary = generator.verify(package, root=root)
    require(summary.get("status") == "verified", "Package verification did not pass")
    path = package / "participant/participant.json"
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == summary["participant_sha256"], "Participant packet changed after verification")
    participant = parse_json(data)
    generator.validate_participant(participant)
    require(participant["package_id"] == summary["package_id"], "Package identity differs")
    require(re.fullmatch(r"[a-f0-9]{64}", summary["manifest_sha256"]) is not None, "Invalid package digest")
    return participant, {"package_id": summary["package_id"], "manifest_sha256": summary["manifest_sha256"],
                         "participant_sha256": summary["participant_sha256"]}


def validate_public_packet(packet):
    """Small local safety boundary, independent of generator's stronger verifier."""
    require(set(packet) == {"protocol_id", "package_id", "language", "total_items", "items"}, "Unexpected public packet field")
    require(isinstance(packet["protocol_id"], str) and packet["language"] == "en", "Invalid packet protocol/language")
    require(re.fullmatch(r"pkg_[a-f0-9]{32}", packet["package_id"]) is not None, "Invalid public package ID")
    require(type(packet["total_items"]) is int and 0 < packet["total_items"] <= 10000 and
            len(packet["items"]) == packet["total_items"], "Invalid packet count")
    identities = set()
    for item in packet["items"]:
        require(set(item) == {"id", "prompt", "responses"} and
                re.fullmatch(r"item_[a-f0-9]{32}", item["id"]) is not None and item["id"] not in identities,
                "Invalid or duplicate public item")
        require(isinstance(item["prompt"], str) and item["prompt"] and isinstance(item["responses"], list) and
                len(item["responses"]) == 2 and all(isinstance(v, str) and v for v in item["responses"]),
                "Invalid public stimulus")
        identities.add(item["id"])


def interface_identity(assets, root=ROOT):
    assets, root = Path(assets).resolve(), Path(root).resolve()
    files = {"server": Path(__file__).resolve(), "index.html": assets / "index.html",
             "app.js": assets / "app.js", "style.css": assets / "style.css",
             "protocol_en": root / "docs/CONTEXTUAL_EMOJI_AUTHOR_PILOT_V0.md",
             "protocol_ja": root / "docs/CONTEXTUAL_EMOJI_AUTHOR_PILOT_V0.ja.md"}
    for path in files.values():
        require(path.is_file() and not path.is_symlink(), "Missing or symlinked interface/protocol file")
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}


def private_journal_path(path, package):
    """No journal in Git, package artifacts, or a symlink; never chmod existing folders."""
    path = Path(path).expanduser()
    require(not path.is_symlink(), "Journal cannot be a symlink")
    path = path.resolve()
    package = Path(package).resolve()
    require(not path.is_relative_to(package), "Journal must be separate from the package")
    require(not path.is_relative_to(ROOT), "Journal must be outside this repository")
    for parent in [path.parent, *path.parent.parents]:
        require(not (parent / ".git").exists(), "Journal must be outside Git checkouts")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    require(stat.S_IMODE(path.parent.stat().st_mode) & 0o077 == 0, "Journal parent must be a private directory (mode 700)")
    return path


class Journal:
    """A single locked append-only file. Existing records must replay exactly."""
    def __init__(self, path, package, packet, binding, interface_binding=None):
        validate_public_packet(packet)
        self.path = private_journal_path(path, package)
        self.packet, self.binding = copy.deepcopy(packet), dict(binding)
        self.interface_binding = dict(interface_binding or interface_identity(ROOT / "web/author-pilot"))
        require(set(self.interface_binding) == {"server", "index.html", "app.js", "style.css", "protocol_en", "protocol_ja"} and
                all(re.fullmatch(r"[a-f0-9]{64}", h) for h in self.interface_binding.values()), "Invalid interface digest binding")
        self.items = {item["id"] for item in packet["items"]}
        require(binding["package_id"] == packet["package_id"] and
                all(re.fullmatch(r"[a-f0-9]{64}", binding[k]) for k in ("manifest_sha256", "participant_sha256")),
                "Invalid journal package binding")
        self.lock = threading.RLock()
        self.state = {"revision": 0, "locked": False, "started": False, "setup": None, "responses": {}}
        self.requests, self.last_hash, self.finalization = {}, "0" * 64, None
        self.failed = False
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        created = False
        try:
            self.fd = os.open(self.path, os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_EXCL | nofollow, 0o600)
            created = True
        except FileExistsError:
            self.fd = os.open(self.path, os.O_RDWR | os.O_APPEND | nofollow)
        try:
            require(stat.S_ISREG(os.fstat(self.fd).st_mode) and stat.S_IMODE(os.fstat(self.fd).st_mode) & 0o077 == 0,
                    "Journal must be a private regular file")
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if created:
                self._append({"kind": "header", "protocol_id": JOURNAL_PROTOCOL,
                              "binding": self.binding, "interface_binding": self.interface_binding,
                              "participant_identity": PARTICIPANT_IDENTITY, "created_at_utc": utc_now()})
            else:
                self._replay()
        except BaseException:
            os.close(self.fd)
            self.fd = None
            raise

    def close(self):
        with self.lock:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None

    def _append(self, record):
        envelope = {**record, "previous_sha256": self.last_hash}
        digest = hashlib.sha256(canonical(envelope)).hexdigest()
        line = canonical({**envelope, "sha256": digest}) + b"\n"
        offset = 0
        try:
            while offset < len(line):
                written = os.write(self.fd, line[offset:])
                if written <= 0:
                    raise OSError("Journal write made no progress")
                offset += written
            os.fsync(self.fd)
        except BaseException:
            self.failed = True
            raise
        self.last_hash = digest

    def _replay(self):
        os.lseek(self.fd, 0, os.SEEK_SET)
        pieces = []
        while True:
            piece = os.read(self.fd, 65536)
            if not piece:
                break
            pieces.append(piece)
        raw = b"".join(pieces)
        require(raw and raw.endswith(b"\n"), "Partial journal: preserve it; automatic truncation is forbidden")
        for index, line in enumerate(raw.splitlines()):
            record = parse_json(line)
            digest = record.pop("sha256")
            require(record["previous_sha256"] == self.last_hash and hashlib.sha256(canonical(record)).hexdigest() == digest,
                    "Journal hash chain differs")
            self.last_hash = digest
            record.pop("previous_sha256")
            if index == 0:
                require(set(record) == {"kind", "protocol_id", "binding", "interface_binding", "participant_identity", "created_at_utc"} and
                        record["kind"] == "header" and record["protocol_id"] == JOURNAL_PROTOCOL and
                        record["binding"] == self.binding and record["interface_binding"] == self.interface_binding and
                        record["participant_identity"] == PARTICIPANT_IDENTITY,
                        "Journal belongs to another package, interface, or protocol")
            else:
                require(set(record) == {"kind", "request_id", "request_sha256", "action", "body", "recorded_at_utc", "state"} and
                        record["kind"] == "mutation", "Invalid journal event")
                request_id, request_sha = self._request(record["action"], record["body"])
                require(request_id == record["request_id"] and request_sha == record["request_sha256"] and request_id not in self.requests,
                        "Journal request identity differs")
                future = self._transition(record["action"], record["body"], record["recorded_at_utc"])
                require(future == record["state"], "Journal state does not replay")
                self.state = future
                self.requests[request_id] = (request_sha, copy.deepcopy(future))
                if record["action"] == "finalize":
                    self.finalization = {"recorded_at_utc": record["recorded_at_utc"],
                                         "remaining_reason": record["body"]["remaining_reason"]}

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.state)

    def _request(self, action, body):
        if not isinstance(body, dict) or not isinstance(body.get("request_id"), str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", body["request_id"]):
            raise APIError("invalid_request_id", "Use an opaque 8–128 character request ID.")
        return body["request_id"], hashlib.sha256(canonical({"action": action, "body": body})).hexdigest()

    def _transition(self, action, body, timestamp):
        allowed = {"setup": {"setup"}, "start": set(), "response": {"item_id", "response"},
                   "finalize": {"confirm", "remaining_reason"}}
        if action not in allowed or set(body) != {"request_id", "revision", "instruction_language"} | allowed[action]:
            raise APIError("invalid_fields", "Request fields do not match this action.")
        if not isinstance(body["instruction_language"], str) or body["instruction_language"] not in {"ja", "en"}:
            raise APIError("invalid_instruction_language", "Record the displayed instruction language, ja or en.")
        if type(body["revision"]) is not int or body["revision"] != self.state["revision"]:
            raise APIError("revision_conflict", "The record changed; reload the current state before saving.", 409)
        if self.state["locked"]:
            raise APIError("locked", "This batch is finalized. Its responses cannot be changed.", 409)
        state = copy.deepcopy(self.state)
        if action == "setup":
            value = body["setup"]
            if state["started"]:
                raise APIError("already_started", "Setup is fixed once this batch starts.", 409)
            if (not isinstance(value, dict) or set(value) != {"english_confidence", "prior_exposure"} or
                    not isinstance(value["english_confidence"], str) or
                    value["english_confidence"] not in {"comfortable", "sometimes_difficult", "difficult", "prefer_not_to_say"} or
                    not isinstance(value["prior_exposure"], str) or value["prior_exposure"] not in RECOGNITION):
                raise APIError("invalid_setup", "Complete both setup questions using the offered choices.")
            state["setup"] = copy.deepcopy(value)
        elif action == "start":
            if state["setup"] is None:
                raise APIError("setup_required", "Complete setup before starting.", 409)
            if state["started"]:
                raise APIError("already_started", "This batch has already started.", 409)
            state["started"] = True
        elif action == "response":
            if not state["started"]:
                raise APIError("start_required", "Start the batch before saving a response.", 409)
            if not isinstance(body["item_id"], str) or body["item_id"] not in self.items:
                raise APIError("unknown_item", "The item is not in this batch.")
            response = self._response(body["response"])
            state["responses"][body["item_id"]] = {**response, "saved_at_utc": timestamp}
        else:
            if not state["started"]:
                raise APIError("start_required", "Start the batch before finalizing.", 409)
            if body["confirm"] is not True:
                raise APIError("confirmation_required", "Finalization needs explicit confirmation.")
            reason = body["remaining_reason"]
            if not isinstance(reason, str) or len(reason) > 4000:
                raise APIError("invalid_reason", "Keep the remaining-item reason within 4,000 characters.")
            if self.items - set(state["responses"]) and not reason.strip():
                raise APIError("remaining_reason_required", "Explain the remaining unanswered items, or answer them before finalizing.")
            state["locked"] = True
        state["revision"] += 1
        return state

    @staticmethod
    def _response(value):
        if not isinstance(value, dict) or not {"choice"} <= set(value) <= {"choice", "recognition", "naturalness", "note"}:
            raise APIError("invalid_response", "A response needs a choice, with optional recognition, naturalness and note.")
        recognition = value.get("recognition")
        if (not isinstance(value["choice"], str) or value["choice"] not in CHOICES or
                (recognition is not None and (not isinstance(recognition, str) or recognition not in RECOGNITION))):
            raise APIError("invalid_response", "Use the offered choice and optional recognition options.")
        natural = value.get("naturalness", {})
        if not isinstance(natural, dict) or not set(natural) <= {"prompt", "first", "second"} or any(not isinstance(v, str) or v not in NATURALNESS for v in natural.values()):
            raise APIError("invalid_naturalness", "Use good, awkward, or unclear for any optional naturalness ratings.")
        note = value.get("note", "")
        if not isinstance(note, str) or len(note) > 4000:
            raise APIError("invalid_note", "Keep the note within 4,000 characters.")
        return {"choice": value["choice"], "recognition": recognition, "naturalness": copy.deepcopy(natural), "note": note}

    def mutate(self, action, body):
        with self.lock:
            if self.failed:
                raise APIError("journal_unavailable", "A journal write failed; further saves are disabled. Preserve the file for inspection.", 503)
            request_id, request_sha = self._request(action, body)
            if request_id in self.requests:
                saved_sha, _original_result = self.requests[request_id]
                if request_sha != saved_sha:
                    raise APIError("idempotency_conflict", "This request ID was already bound to different content.", 409)
                # Keep the original receipt in the journal, but never regress a
                # client to an older revision after another tab has advanced.
                return copy.deepcopy(self.state)
            timestamp = utc_now()
            future = self._transition(action, body, timestamp)
            self._append({"kind": "mutation", "request_id": request_id, "request_sha256": request_sha,
                          "action": action, "body": body, "recorded_at_utc": timestamp, "state": future})
            self.state = future
            self.requests[request_id] = (request_sha, copy.deepcopy(future))
            if action == "finalize":
                self.finalization = {"recorded_at_utc": timestamp, "remaining_reason": body["remaining_reason"]}
            return copy.deepcopy(future)

    def export(self):
        with self.lock:
            return {"record_type": "author_pilot_not_independent_human_validation", "participant": copy.deepcopy(self.packet),
                    "participant_identity": dict(PARTICIPANT_IDENTITY),
                    "state": copy.deepcopy(self.state), "package_binding": dict(self.binding),
                    "interface_binding": dict(self.interface_binding), "journal_sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(),
                    "finalization": copy.deepcopy(self.finalization),
                    "missing_item_ids": sorted(self.items - set(self.state["responses"])),
                    "exposure_note": "started records batch start, not proof that each item was viewed"}


class PilotServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, journal, assets, port=8877, protocol_root=ROOT):
        self.journal, self.assets = journal, Path(assets).resolve()
        self.auth_token = secrets.token_urlsafe(32)
        self.static_bytes = {}
        for filename, _ in STATIC.values():
            path = self.assets / filename
            require(path.is_file() and not path.is_symlink(), "Missing or symlinked static asset")
            self.static_bytes[filename] = path.read_bytes()
        current_binding = interface_identity(self.assets, protocol_root)
        require(current_binding == journal.interface_binding and
                all(hashlib.sha256(self.static_bytes[name]).hexdigest() == current_binding[name]
                    for name in ("index.html", "app.js", "style.css")), "Interface or instructions changed since journal creation")
        super().__init__(("127.0.0.1", port), PilotHandler)
        self.cookie_name = f"{COOKIE}_{self.server_port}_{journal.packet['package_id'][4:20]}"


class PilotHandler(BaseHTTPRequestHandler):
    server_version = "GlyphProbeAuthorPilot"
    sys_version = ""

    def log_message(self, format, *args):
        # No request path, note, stimulus, cookie, or answer information in logs.
        pass

    def _guard(self, mutate=False, auth=True):
        port = self.server.server_port
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = self.headers.get("Host", "")
        if len(self.headers.get_all("Host", [])) != 1 or host not in hosts:
            raise APIError("invalid_host", "Use this server's loopback address.", 403)
        origin = self.headers.get("Origin")
        if len(self.headers.get_all("Origin", [])) > 1 or (mutate and origin is None) or (origin is not None and origin != "http://" + host):
            raise APIError("invalid_origin", "Only same-origin browser requests are accepted.", 403)
        if self.headers.get("Sec-Fetch-Site") in {"cross-site", "same-site"}:
            raise APIError("cross_site_request", "Cross-site access is disabled.", 403)
        if auth:
            cookie = SimpleCookie()
            try:
                cookie.load(self.headers.get("Cookie", ""))
            except Exception:
                raise APIError("unauthorized", "Open the start page in this browser first.", 401)
            name = self.server.cookie_name
            value = cookie[name].value if name in cookie else ""
            if not secrets.compare_digest(value, self.server.auth_token):
                raise APIError("unauthorized", "Open the start page in this browser first.", 401)

    def _reply(self, status, data, content_type="application/json; charset=utf-8", *, cookie=False, download=False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        if cookie:
            self.send_header("Set-Cookie", f"{self.server.cookie_name}={self.server.auth_token}; Path=/; HttpOnly; SameSite=Strict")
        if download:
            self.send_header("Content-Disposition", 'attachment; filename="author-pilot-responses.json"')
        self.end_headers()
        self.wfile.write(data)

    def _error(self, error):
        payload = {"error": error.code, "message": error.message}
        if error.status == 409:
            payload["state"] = self.server.journal.snapshot()
        self._reply(error.status, canonical(payload))

    def do_GET(self):
        try:
            path = urlsplit(self.path).path
            self._guard(auth=path not in {"/", "/index.html"})
            if path in STATIC:
                filename, mime = STATIC[path]
                self._reply(200, self.server.static_bytes[filename], mime, cookie=path in {"/", "/index.html"})
            elif path == "/api/packet":
                self._reply(200, canonical(self.server.journal.packet))
            elif path == "/api/state":
                self._reply(200, canonical(self.server.journal.snapshot()))
            elif path == "/api/export":
                self._reply(200, canonical(self.server.journal.export()), download=True)
            else:
                raise APIError("not_found", "No such public resource.", 404)
        except APIError as error:
            self._error(error)
        except Exception:
            self._error(APIError("internal_error", "Request could not be completed; existing records were retained.", 500))

    def do_POST(self):
        try:
            self._guard(mutate=True)
            actions = {"/api/setup": "setup", "/api/start": "start", "/api/response": "response", "/api/finalize": "finalize"}
            path = urlsplit(self.path).path
            if path not in actions:
                raise APIError("not_found", "No such mutation.", 404)
            if self.headers.get_content_type() != "application/json" or self.headers.get("Transfer-Encoding"):
                raise APIError("invalid_content_type", "Send a bounded application/json body.", 415)
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) != 1 or not lengths[0].isdigit() or not 0 < int(lengths[0]) <= 65536:
                raise APIError("invalid_length", "A JSON body of at most 65,536 bytes is required.", 413)
            self.connection.settimeout(10)
            data = self.rfile.read(int(lengths[0]))
            if len(data) != int(lengths[0]):
                raise APIError("invalid_length", "The request body was incomplete.")
            try:
                body = parse_json(data)
            except (ValueError, UnicodeError):
                raise APIError("invalid_json", "JSON must be finite and have unique keys.")
            self._reply(200, canonical(self.server.journal.mutate(actions[path], body)))
        except APIError as error:
            self._error(error)
        except Exception:
            self._error(APIError("internal_error", "Save failed; reload the record before trying again.", 500))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--port", type=int, default=8877)
    args = parser.parse_args()
    require(1024 <= args.port <= 65535, "Choose an unprivileged local port")
    packet, binding = load_package(args.package, args.root)
    journal = Journal(args.journal, args.package, packet, binding,
                      interface_identity(ROOT / "web/author-pilot", ROOT))
    try:
        server = PilotServer(journal, ROOT / "web/author-pilot", args.port)
        print(f"http://127.0.0.1:{server.server_port}/  ({packet['total_items']} items)", flush=True)
        try:
            server.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    finally:
        journal.close()


if __name__ == "__main__":
    main()
