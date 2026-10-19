#!/usr/bin/env python3
"""Watch the unchanged timing protocol, then validate/run/validate its canary."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Callable
import uuid


SOURCE_FILES = {
    "scripts/t22_kv_cpu_canary_v0.py", "scripts/t22_kv_dissection_v0.py",
    "scripts/t21_glyph_context_path_pilot_v0.py", "tests/test_t22_kv_cpu_canary_v0.py",
    "src/glyphprobe/provenance.py", "configs/t21_glyph_context_path_pilot_v0.yaml",
    "validation/t21_glyph_context_path_pilot_v0/pilot_specification_v1.json",
    "validation/t21_glyph_context_path_confirmation_v0/canary_specification.json",
}
PROTOCOL = "glyphprobe-t22-cpu-after-timing-orchestration-v0"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected JSON object: {path.name}")
    return value


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def process_identity(pid: int) -> dict | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except FileNotFoundError:
        return None
    fields = raw[raw.rfind(")") + 2:].split()
    require(len(fields) >= 20, "Malformed process identity")
    return {"pid": pid, "start_ticks": int(fields[19]), "state": fields[0],
            "boot_id": boot_id()}


def atomic_status(path: Path, value: dict) -> None:
    temporary = path.with_name(f".{path.name}.partial-{uuid.uuid4().hex}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def check_sources(repo: Path, sources: dict[str, str]) -> None:
    for relative, expected in sources.items():
        require(sha(repo / relative) == expected, f"Bound source changed: {relative}")


def timing_alive(expected: dict) -> tuple[bool, dict | None]:
    require(boot_id() == expected["boot_id"], "Machine boot identity changed")
    current = process_identity(expected["pid"])
    if current is None or current["state"] in ("Z", "X"):
        return False, current
    require(current["start_ticks"] == expected["start_ticks"], "Timing PID was reused")
    return True, current


def validate_report(report_path: Path, run: Path, items: int) -> dict:
    report = read(report_path)
    require(report.get("status") == "pass" and report.get("target_items") == items,
            "Independent validation did not report the required pass/item count")
    require(report.get("acquisition_receipt_sha256") == sha(run / "acquisition_receipt.json")
            and report.get("specification_sha256") == sha(run / "specification.json"),
            "Independent validation report/run hash mismatch")
    return {"report": str(report_path), "report_sha256": sha(report_path),
            "acquisition_receipt_sha256": report["acquisition_receipt_sha256"],
            "specification_sha256": report["specification_sha256"], "target_items": items}


def run_child(command: list[str], *, stage: str, log: Path, repo: Path,
              sources: dict, status: dict, publish: Callable, poll_seconds: float) -> int:
    """Own/reap only our subprocess; never signal the pre-existing timing PID."""
    check_sources(repo, sources)
    with log.open("xb", buffering=0) as output:
        child = subprocess.Popen(command, cwd=repo, stdin=subprocess.DEVNULL,
                                 stdout=output, stderr=subprocess.STDOUT,
                                 close_fds=True, start_new_session=True)
        identity = process_identity(child.pid)
        status.update(stage=stage, active_child_pid=child.pid,
                      active_child_identity=identity, active_log=str(log), command=command)
        publish()
        try:
            while child.poll() is None:
                check_sources(repo, sources)
                publish()
                time.sleep(poll_seconds)
            check_sources(repo, sources)
            status["children"].append({"stage": stage, "pid": child.pid,
                                       "identity": identity, "returncode": child.returncode,
                                       "log": str(log), "finished_at_utc": now()})
            status.update(active_child_pid=None, active_child_identity=None)
            publish()
            require(child.returncode == 0, f"{stage} exited with code {child.returncode}")
            return child.returncode
        except BaseException:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=10)
            status["interrupted_child"] = {"pid": child.pid, "identity": identity,
                                           "returncode": child.returncode, "log": str(log)}
            status.update(active_child_pid=None, active_child_identity=None)
            raise


def commands(repo: Path, python: str, model: Path, timing: Path, canary: Path,
             state: Path, rehash_model: bool) -> dict[str, list[str]]:
    validator = [python, "-u", str(repo / "scripts/validate_t22_cpu_acquisition_v0.py"),
                 "--repo", str(repo)]
    extra = ["--model-path", str(model)] if rehash_model else []
    return {
        "validating_timing": validator + ["--run", str(timing), "--expected-items", "1",
                                           "--output", str(state / "timing_validation.json")] + extra,
        "running_canary": [python, "-u", str(repo / "scripts/t22_kv_cpu_canary_v0.py"),
                           "run", "--model-path", str(model), "--output", str(canary),
                           "--items", "8", "--threads", "4"],
        "validating_canary": validator + ["--run", str(canary), "--expected-items", "8",
                                           "--output", str(state / "canary_validation.json")] + extra,
    }


def orchestrate(*, repo: Path, python: str, model: Path, timing: Path, canary: Path,
                state: Path, timing_pid: int | None = None, timing_start_ticks: int | None = None,
                poll_seconds: float = 10, rehash_model: bool = False,
                print_plan: bool = False) -> dict:
    repo, model, timing, canary, state = (path.resolve() for path in
                                         (repo, model, timing, canary, state))
    require(0 < poll_seconds <= 30, "Polling interval must be between zero and 30 seconds")
    require((timing_pid is None) == (timing_start_ticks is None),
            "Supply both timing PID/start ticks or neither")
    if timing_pid is not None:
        require(timing_pid > 0 and timing_start_ticks > 0, "Positive timing PID/start ticks required")
    else:
        require((timing / "acquisition_receipt.json").is_file(),
                "A completed timing receipt is required when no live PID is supplied")
    require(len({model, timing, canary, state}) == 4, "Run/model/state paths must differ")
    for left, right in ((state, model), (state, timing), (state, canary),
                        (canary, model), (canary, timing)):
        require(not left.is_relative_to(right) and not right.is_relative_to(left),
                "Run/model/state paths must not contain each other")
    plan = commands(repo, python, model, timing, canary, state, rehash_model)
    if print_plan:
        return {"commands": plan, "timing_pid": timing_pid,
                "timing_start_ticks": timing_start_ticks, "state_dir": str(state)}
    specification_path = timing / "specification.json"
    specification = read(specification_path)
    require(set(specification["source_sha256"]) == SOURCE_FILES,
            "Timing source map differs from the exact allowed eight-file set")
    sources = dict(specification["source_sha256"])
    for path in (repo / "scripts/validate_t22_cpu_acquisition_v0.py", Path(__file__).resolve()):
        sources[path.relative_to(repo).as_posix()] = sha(path)
    sources[specification_path.relative_to(repo).as_posix()] = sha(specification_path)
    check_sources(repo, sources)
    require(not canary.exists(), "Canary output already exists; will not launch duplicate work")
    state.mkdir(parents=True, exist_ok=False)
    expected = ({"pid": timing_pid, "start_ticks": timing_start_ticks, "boot_id": boot_id()}
                if timing_pid is not None else None)
    status = {"protocol_id": PROTOCOL, "stage": "waiting_timing", "status": "running",
              "created_at_utc": now(), "orchestrator_pid": os.getpid(),
              "orchestrator_identity": process_identity(os.getpid()),
              "timing_process": expected, "timing_run": str(timing),
              "canary_run": str(canary), "model_path": str(model),
              "source_sha256": sources, "children": [], "active_child_pid": None,
              "logs": {stage: str(state / f"{stage}.log") for stage in plan},
              "reports": {}, "commands": plan, "scientific_result": False}
    status_path = state / "status.json"

    def publish() -> None:
        status["updated_at_utc"] = now()
        atomic_status(status_path, status)

    try:
        publish()
        while expected is not None:
            check_sources(repo, sources)
            alive, current = timing_alive(expected)
            status["last_timing_identity"] = current
            publish()
            if not alive:
                break
            time.sleep(poll_seconds)
        require((timing / "acquisition_receipt.json").is_file(),
                "Timing process ended without an acquisition receipt")
        for stage, run, items in (("validating_timing", timing, 1),
                                  ("running_canary", canary, None),
                                  ("validating_canary", canary, 8)):
            if stage == "running_canary":
                require(not canary.exists(), "Canary output appeared; will not launch duplicate work")
            run_child(plan[stage], stage=stage, log=Path(status["logs"][stage]),
                      repo=repo, sources=sources, status=status, publish=publish,
                      poll_seconds=poll_seconds)
            if items is not None:
                report_path = state / ("timing_validation.json" if items == 1 else "canary_validation.json")
                status["reports"][stage] = validate_report(report_path, run, items)
                publish()
        status.update(status="complete", stage="complete", completed_at_utc=now())
        publish()
        return status
    except BaseException as error:
        status.update(status="failed", failed_stage=status["stage"], stage="failed",
                      error_type=type(error).__name__, error=str(error), failed_at_utc=now())
        publish()
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--timing-run", type=Path, default=Path("runs/t22_cpu_timing_v0"))
    parser.add_argument("--canary-run", type=Path, default=Path("runs/t22_cpu_canary_v0"))
    parser.add_argument("--state-dir", type=Path, default=Path("runs/t22_cpu_orchestration_v0"))
    parser.add_argument("--timing-pid", type=int,
                        help="Required with start ticks only while timing is still running")
    parser.add_argument("--timing-start-ticks", type=int)
    parser.add_argument("--poll-seconds", type=float, default=10)
    parser.add_argument("--rehash-model", action="store_true")
    parser.add_argument("--print-plan", action="store_true")
    args = parser.parse_args()
    for name in ("timing_run", "canary_run", "state_dir"):
        value = getattr(args, name)
        if not value.is_absolute():
            setattr(args, name, args.repo / value)

    def terminate(_signum: int, _frame: object) -> None:
        raise KeyboardInterrupt("Orchestrator received SIGTERM")

    signal.signal(signal.SIGTERM, terminate)
    try:
        result = orchestrate(repo=args.repo, python=args.python, model=args.model_path,
                             timing=args.timing_run, canary=args.canary_run, state=args.state_dir,
                             timing_pid=args.timing_pid, timing_start_ticks=args.timing_start_ticks,
                             poll_seconds=args.poll_seconds, rehash_model=args.rehash_model,
                             print_plan=args.print_plan)
        print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    except (Exception, KeyboardInterrupt) as error:
        print(json.dumps({"status": "failed", "error_type": type(error).__name__,
                          "error": str(error)}), file=sys.stderr, flush=True)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
