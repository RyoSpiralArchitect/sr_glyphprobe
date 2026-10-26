"""Synthetic-only server/journal tests: never load production stimuli or keys."""
from __future__ import annotations

import copy
import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1] / "scripts/serve_contextual_emoji_author_pilot_v0.py"
spec = importlib.util.spec_from_file_location("author_pilot_server_tests", SOURCE)
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


def packet():
    return {"protocol_id": "synthetic-author-pilot", "package_id": "pkg_" + "1" * 32,
            "language": "en", "total_items": 2,
            "items": [{"id": "item_" + digit * 32, "prompt": "Synthetic prompt " + digit,
                       "responses": ["Synthetic first", "Synthetic second"]} for digit in ("2", "3")]}


def binding():
    return {"package_id": "pkg_" + "1" * 32, "manifest_sha256": "a" * 64, "participant_sha256": "b" * 64}


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="glyphprobe-server-synthetic-")
        self.base = Path(self.temp.name)
        self.package = self.base / "package"
        self.package.mkdir()
        self.assets = self.base / "assets"; self.assets.mkdir()
        for name, value in (("index.html", "<!doctype html><p>Synthetic UI</p>"), ("app.js", "void 0;"), ("style.css", "body {}")):
            (self.assets / name).write_text(value)
        (self.base / "docs").mkdir()
        for name in ("CONTEXTUAL_EMOJI_AUTHOR_PILOT_V0.md", "CONTEXTUAL_EMOJI_AUTHOR_PILOT_V0.ja.md"):
            (self.base / "docs" / name).write_text("Synthetic instructions only")
        self.interface = server.interface_identity(self.assets, self.base)
        self.path = self.base / "records" / "responses.jsonl"
        self.journal = server.Journal(self.path, self.package, packet(), binding(), self.interface)
        self.counter = 0

    def tearDown(self):
        self.journal.close()
        self.temp.cleanup()

    def body(self, **fields):
        self.counter += 1
        return {"request_id": f"request_{self.counter:08d}", "revision": self.journal.snapshot()["revision"], "instruction_language": "ja", **fields}

    def start(self):
        self.journal.mutate("setup", self.body(setup={"english_confidence": "comfortable", "prior_exposure": "yes"}))
        return self.journal.mutate("start", self.body())

    def answer(self, **response):
        return self.body(item_id=packet()["items"][0]["id"],
                         response={"choice": "first", "recognition": "unsure", **response})


class JournalTests(Base):
    def test_read_only_snapshots_and_export_never_append(self):
        initial = self.path.read_bytes()
        self.journal.snapshot(); self.journal.export()
        self.assertEqual(initial, self.path.read_bytes())
        self.assertEqual(self.journal.snapshot()["revision"], 0)
        self.assertFalse(self.journal.export()["state"]["started"])
        self.assertNotIn("answer_key", json.dumps(self.journal.export()))

    def test_setup_then_start_required(self):
        with self.assertRaises(server.APIError): self.journal.mutate("start", self.body())
        with self.assertRaises(server.APIError): self.journal.mutate("response", self.answer())
        self.start()
        with self.assertRaises(server.APIError):
            self.journal.mutate("setup", self.body(setup={"english_confidence": "difficult", "prior_exposure": "no"}))
        with self.assertRaises(server.APIError): self.journal.mutate("start", self.body())

    def test_revision_conflict_does_not_append(self):
        self.start()
        payload = self.answer()
        self.journal.mutate("response", payload)
        before = self.path.read_bytes()
        payload["request_id"] = "another_request"
        with self.assertRaises(server.APIError) as caught: self.journal.mutate("response", payload)
        self.assertEqual(caught.exception.code, "revision_conflict")
        self.assertEqual(before, self.path.read_bytes())

    def test_idempotency_returns_saved_result_without_append(self):
        self.start()
        payload = self.answer()
        result = self.journal.mutate("response", payload)
        size = self.path.stat().st_size
        self.assertEqual(self.journal.mutate("response", payload), result)
        self.assertEqual(size, self.path.stat().st_size)
        changed = copy.deepcopy(payload); changed["response"]["choice"] = "second"
        with self.assertRaises(server.APIError) as caught: self.journal.mutate("response", changed)
        self.assertEqual(caught.exception.code, "idempotency_conflict")

    def test_old_retry_returns_current_finalized_state_without_event(self):
        self.start()
        request = self.answer()
        self.journal.mutate("response", request)
        self.journal.mutate("response", self.answer(choice="second"))
        final = self.journal.mutate("finalize", self.body(confirm=True, remaining_reason="Synthetic partial finish"))
        raw = self.path.read_bytes()
        self.assertEqual(self.journal.mutate("response", request), final)
        self.assertTrue(final["locked"])
        self.assertEqual(self.path.read_bytes(), raw)
        self.journal.close()
        self.journal = server.Journal(self.path, self.package, packet(), binding(), self.interface)
        self.assertEqual(self.journal.mutate("response", request), final)

    def test_known_author_exposure_separate_from_self_report(self):
        self.journal.mutate("setup", self.body(setup={"english_confidence": "comfortable", "prior_exposure": "no"}))
        exported = self.journal.export()
        self.assertEqual(exported["state"]["setup"]["prior_exposure"], "no")
        self.assertEqual(exported["participant_identity"], {"pseudonym": "author-01", "role": "author", "prior_model_outcome_exposure_known": True})
        header = server.parse_json(self.path.read_bytes().splitlines()[0])
        self.assertEqual(header["participant_identity"], exported["participant_identity"])

    def test_response_revisions_preserved_and_replay(self):
        self.start()
        self.journal.mutate("response", self.answer(note="First revision"))
        self.journal.mutate("response", self.answer(choice="both", naturalness={"first": "awkward"}, note="Second revision"))
        expected = self.journal.snapshot()
        raw = self.path.read_text()
        self.assertIn("First revision", raw); self.assertIn("Second revision", raw)
        self.journal.close()
        self.journal = server.Journal(self.path, self.package, packet(), binding(), self.interface)
        self.assertEqual(self.journal.snapshot(), expected)
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o600)

    def test_partial_finalize_reason_and_explicit_confirmation(self):
        self.start()
        self.journal.mutate("response", self.answer(choice="abstain"))
        for confirm, reason in [(False, "Time ran out"), (True, "   ")]:
            with self.assertRaises(server.APIError):
                self.journal.mutate("finalize", self.body(confirm=confirm, remaining_reason=reason))
        request = self.body(confirm=True, remaining_reason="Time ran out")
        result = self.journal.mutate("finalize", request)
        self.assertTrue(result["locked"])
        self.assertEqual(self.journal.mutate("finalize", request), result)
        with self.assertRaises(server.APIError): self.journal.mutate("response", self.answer(choice="second"))
        exported = self.journal.export()
        self.assertEqual(exported["missing_item_ids"], [packet()["items"][1]["id"]])
        self.assertEqual(exported["finalization"]["remaining_reason"], "Time ran out")
        self.journal.close()
        self.journal = server.Journal(self.path, self.package, packet(), binding(), self.interface)
        self.assertEqual(self.journal.export(), exported)

    def test_complete_finalize_allows_empty_reason(self):
        self.start()
        for item in packet()["items"]:
            body = self.answer(); body["item_id"] = item["id"]
            self.journal.mutate("response", body)
        self.assertTrue(self.journal.mutate("finalize", self.body(confirm=True, remaining_reason=""))["locked"])

    def test_invalid_response_fields_and_values_do_not_append(self):
        self.start()
        before = self.path.read_bytes()
        bad = [{"choice": "correct"}, {"recognition": "definitely"}, {"note": "x" * 4001},
               {"naturalness": {"first": "bad"}}, {"answer_key": "invented"}, {"choice": []}]
        for value in bad:
            with self.subTest(value=list(value)):
                with self.assertRaises(server.APIError): self.journal.mutate("response", self.answer(**value))
        unknown = self.answer(); unknown["item_id"] = []
        with self.assertRaises(server.APIError): self.journal.mutate("response", unknown)
        self.assertEqual(before, self.path.read_bytes())

    def test_invalid_setup_and_request_fields(self):
        for setup in ({"english_confidence": [], "prior_exposure": "yes"},
                      {"english_confidence": "comfortable", "prior_exposure": "yes", "label": "x"}):
            with self.assertRaises(server.APIError): self.journal.mutate("setup", self.body(setup=setup))
        body = self.body(setup={"english_confidence": "comfortable", "prior_exposure": "yes"}); body["revision"] = False
        with self.assertRaises(server.APIError): self.journal.mutate("setup", body)
        with self.assertRaises(server.APIError): self.journal.mutate("start", {"request_id": "short", "revision": 0})

    def test_optional_recognition_retains_null_and_declined_confidence(self):
        self.journal.mutate("setup", self.body(setup={"english_confidence": "prefer_not_to_say", "prior_exposure": "unsure"}))
        self.journal.mutate("start", self.body(instruction_language="en"))
        request = self.answer(); del request["response"]["recognition"]
        result = self.journal.mutate("response", request)
        self.assertIsNone(result["responses"][request["item_id"]]["recognition"])
        request = self.answer(recognition=None)
        self.assertIsNone(self.journal.mutate("response", request)["responses"][request["item_id"]]["recognition"])
        events = [server.parse_json(line) for line in self.path.read_bytes().splitlines()]
        self.assertEqual(events[2]["body"]["instruction_language"], "en")

    def test_instruction_language_required_and_validated(self):
        self.start()
        body = self.answer(); del body["instruction_language"]
        with self.assertRaises(server.APIError): self.journal.mutate("response", body)
        body = self.answer(instruction_language="unknown")
        with self.assertRaises(server.APIError): self.journal.mutate("response", body)

    def test_interface_binding_refuses_changed_instructions_on_resume(self):
        self.journal.close()
        revised = {**self.interface, "protocol_ja": "f" * 64}
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "interface"):
            server.Journal(self.path, self.package, packet(), binding(), revised)
        self.assertEqual(before, self.path.read_bytes())

    def test_package_binding_rejected_on_resume(self):
        self.journal.close()
        different = {**binding(), "manifest_sha256": "c" * 64}
        with self.assertRaisesRegex(ValueError, "another package"):
            server.Journal(self.path, self.package, packet(), different, self.interface)

    def test_truncated_and_tampered_journals_fail_closed(self):
        self.start(); self.journal.close()
        raw = self.path.read_bytes()
        self.path.write_bytes(raw[:-1])
        with self.assertRaisesRegex(ValueError, "Partial journal"):
            server.Journal(self.path, self.package, packet(), binding(), self.interface)
        self.assertEqual(self.path.read_bytes(), raw[:-1])
        self.path.write_bytes(raw.replace(b"comfortable", b"difficult"))
        with self.assertRaisesRegex(ValueError, "hash chain"):
            server.Journal(self.path, self.package, packet(), binding(), self.interface)

    def test_journal_lock_and_private_paths(self):
        with self.assertRaises(BlockingIOError): server.Journal(self.path, self.package, packet(), binding(), self.interface)
        with self.assertRaisesRegex(ValueError, "separate"):
            server.private_journal_path(self.package / "state.jsonl", self.package)
        gitroot = self.base / "gitroot"; gitroot.mkdir(); (gitroot / ".git").mkdir()
        with self.assertRaisesRegex(ValueError, "Git"):
            server.private_journal_path(gitroot / "state.jsonl", self.package)
        public = self.base / "public"; public.mkdir(mode=0o755)
        with self.assertRaisesRegex(ValueError, "private directory"):
            server.private_journal_path(public / "state.jsonl", self.package)
        link = self.base / "link.jsonl"; link.symlink_to(self.path)
        with self.assertRaisesRegex(ValueError, "symlink"):
            server.private_journal_path(link, self.package)

    def test_failed_append_disables_further_saves(self):
        self.start()
        with mock.patch.object(server.os, "fsync", side_effect=OSError("synthetic fsync failure")):
            with self.assertRaises(OSError): self.journal.mutate("response", self.answer())
        self.assertNotIn(packet()["items"][0]["id"], self.journal.snapshot()["responses"])
        with self.assertRaises(server.APIError) as caught: self.journal.mutate("response", self.answer())
        self.assertEqual(caught.exception.code, "journal_unavailable")

    def test_concurrent_revisions_have_one_winner(self):
        self.start()
        first, second = self.answer(choice="first"), self.answer(choice="second")
        outcomes = []
        def save(body):
            try: outcomes.append(self.journal.mutate("response", body)["revision"])
            except server.APIError as error: outcomes.append(error.code)
        threads = [threading.Thread(target=save, args=(body,)) for body in (first, second)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertCountEqual(outcomes, [3, "revision_conflict"])


class HTTPTests(Base):
    def setUp(self):
        super().setUp()
        self.http = server.PilotServer(self.journal, self.assets, 0, protocol_root=self.base)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.cookie = None

    def tearDown(self):
        self.http.shutdown(); self.http.server_close(); self.thread.join()
        super().tearDown()

    def request(self, method, path, value=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.http.server_port, timeout=3)
        chosen = {"Host": f"127.0.0.1:{self.http.server_port}"}
        if self.cookie: chosen["Cookie"] = self.cookie
        data = None
        if value is not None:
            data = value if isinstance(value, bytes) else server.canonical(value)
            chosen.update({"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{self.http.server_port}"})
        chosen.update(headers or {})
        connection.request(method, path, body=data, headers=chosen)
        response = connection.getresponse()
        status, returned, body = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return status, returned, body

    def open_start(self):
        status, headers, _ = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("HttpOnly", headers["Set-Cookie"]); self.assertIn("SameSite=Strict", headers["Set-Cookie"])
        self.cookie = headers["Set-Cookie"].split(";", 1)[0]

    def test_public_gets_do_not_write_and_no_private_routing(self):
        before = self.path.read_bytes()
        self.open_start()
        for path in ("/api/packet", "/api/state", "/api/export", "/app.js", "/style.css"):
            status, _, body = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertNotIn(b"answer_key", body); self.assertNotIn(b"assignment_key", body)
        for path in ("/private/answer_key.json", "/manifest.json", "/../private/answer_key.json", "/%2e%2e/private", "/api/reveal", "/api/reset"):
            self.assertEqual(self.request("GET", path)[0], 404)
        self.assertEqual(before, self.path.read_bytes())

    def test_auth_origin_host_and_fetch_site(self):
        self.assertEqual(self.request("GET", "/api/state")[0], 401)
        self.assertEqual(self.request("GET", "/", headers={"Host": "attacker.example"})[0], 403)
        self.open_start()
        payload = self.body(setup={"english_confidence": "comfortable", "prior_exposure": "yes"})
        self.assertEqual(self.request("POST", "/api/setup", payload, {"Origin": "http://attacker.example"})[0], 403)
        self.assertEqual(self.request("POST", "/api/setup", payload, {"Origin": "null"})[0], 403)
        self.assertEqual(self.request("GET", "/api/state", headers={"Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertEqual(self.request("POST", "/api/setup", payload, {"Cookie": self.http.cookie_name + "=wrong"})[0], 401)
        self.assertEqual(self.journal.snapshot()["revision"], 0)

    def test_http_response_revision_and_export(self):
        self.open_start()
        for action, payload in (("setup", self.body(setup={"english_confidence": "comfortable", "prior_exposure": "yes"})),):
            self.assertEqual(self.request("POST", "/api/" + action, payload)[0], 200)
        self.assertEqual(self.request("POST", "/api/start", self.body())[0], 200)
        response = self.answer(note="Synthetic note")
        status, _, data = self.request("POST", "/api/response", response)
        self.assertEqual(status, 200); self.assertEqual(json.loads(data)["revision"], 3)
        stale = self.answer(); stale["revision"] = 2
        status, _, data = self.request("POST", "/api/response", stale)
        self.assertEqual(status, 409); self.assertEqual(json.loads(data)["state"]["revision"], 3)
        self.assertEqual(self.request("POST", "/api/finalize", self.body(confirm=True, remaining_reason="Synthetic stop"))[0], 200)
        status, headers, data = self.request("GET", "/api/export")
        self.assertEqual(status, 200); self.assertIn("attachment", headers["Content-Disposition"])
        self.assertTrue(json.loads(data)["state"]["locked"])

    def test_invalid_json_and_fields_never_write(self):
        self.open_start(); before = self.path.read_bytes()
        for value in (b'{"request_id":"request_1","request_id":"request_2","revision":0}', b'{"revision":NaN}'):
            self.assertEqual(self.request("POST", "/api/setup", value)[0], 400)
        self.assertEqual(self.request("POST", "/api/setup", {}, {"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.request("POST", "/api/reset", {})[0], 404)
        self.assertEqual(before, self.path.read_bytes())

    def test_cached_assets_and_startup_interface_check(self):
        self.open_start()
        (self.assets / "app.js").write_text("Changed after startup")
        self.assertEqual(self.request("GET", "/app.js")[2], b"void 0;")
        with self.assertRaisesRegex(ValueError, "Interface or instructions"):
            server.PilotServer(self.journal, self.assets, 0, protocol_root=self.base)

    def test_cookie_namespace_separates_ports(self):
        other = server.PilotServer(self.journal, self.assets, 0, protocol_root=self.base)
        try:
            self.assertNotEqual(other.cookie_name, self.http.cookie_name)
            self.assertIn(str(self.http.server_port), self.http.cookie_name)
            self.assertIn(packet()["package_id"][4:20], self.http.cookie_name)
        finally:
            other.server_close()


class PackageTests(unittest.TestCase):
    def test_generator_verification_precedes_public_packet_load(self):
        with tempfile.TemporaryDirectory(prefix="glyphprobe-loader-synthetic-") as directory:
            base = Path(directory); (base / "participant").mkdir()
            data = server.canonical(packet()); (base / "participant/participant.json").write_bytes(data)
            summary = {"status": "verified", "package_id": packet()["package_id"],
                       "participant_sha256": hashlib.sha256(data).hexdigest(), "manifest_sha256": "c" * 64}
            generator = mock.Mock(); generator.verify.return_value = summary
            with mock.patch.object(server, "_generator", return_value=generator):
                public, bound = server.load_package(base)
                self.assertEqual(public, packet()); self.assertEqual(bound["manifest_sha256"], "c" * 64)
                generator.validate_participant.assert_called_once_with(packet())
                generator.verify.assert_called_once()
                summary["participant_sha256"] = "0" * 64
                with self.assertRaisesRegex(ValueError, "changed after verification"): server.load_package(base)


if __name__ == "__main__":
    unittest.main()
