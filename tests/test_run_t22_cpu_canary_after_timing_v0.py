"""Exercise fail-closed acquisition scheduling without model execution."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_t22_cpu_canary_after_timing_v0.py"
spec = importlib.util.spec_from_file_location("t22_orchestration_test_module", SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    for name in runner.SOURCE_FILES:
        destination = repo / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(name)
    for name in ("scripts/validate_t22_cpu_acquisition_v0.py", SCRIPT.name):
        destination = repo / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(name)
    monkeypatch.setattr(runner, "__file__", str(repo / SCRIPT.name))
    timing = repo / "runs/timing"
    timing.mkdir(parents=True)
    (timing / "specification.json").write_text(json.dumps({
        "source_sha256": {name: runner.sha(repo / name) for name in runner.SOURCE_FILES}}))
    (timing / "acquisition_receipt.json").write_text("{}")
    arguments = dict(repo=repo, python=sys.executable, model=tmp_path / "model",
                     timing=timing, canary=repo / "runs/canary", state=repo / "runs/state")
    stages = []

    def child(command, *, stage, **kwargs):
        stages.append(stage)
        if stage == "running_canary":
            arguments["canary"].mkdir()
            for filename in ("specification.json", "acquisition_receipt.json"):
                (arguments["canary"] / filename).write_text("{}")
        else:
            items = 1 if stage == "validating_timing" else 8
            root = arguments["timing"] if items == 1 else arguments["canary"]
            output = Path(command[command.index("--output") + 1])
            output.write_text(json.dumps({
                "status": "pass", "target_items": items,
                "acquisition_receipt_sha256": runner.sha(root / "acquisition_receipt.json"),
                "specification_sha256": runner.sha(root / "specification.json")}))
        return 0

    monkeypatch.setattr(runner, "run_child", child)
    return arguments, stages, child


def test_completed_timing_can_schedule_without_invented_pid(setup):
    arguments, stages, _ = setup
    status = runner.orchestrate(**arguments)
    assert stages == ["validating_timing", "running_canary", "validating_canary"]
    assert status["status"] == "complete"
    assert status["timing_process"] is None
    assert status["reports"]["validating_canary"]["target_items"] == 8
    assert json.loads((arguments["state"] / "status.json").read_text())["status"] == "complete"


def test_validator_report_failure_prevents_canary_even_with_exit_zero(setup, monkeypatch):
    arguments, stages, original = setup

    def invalid_report(command, **kwargs):
        original(command, **kwargs)
        output = Path(command[command.index("--output") + 1])
        report = json.loads(output.read_text())
        report["status"] = "fail"
        output.write_text(json.dumps(report))
        return 0

    monkeypatch.setattr(runner, "run_child", invalid_report)
    with pytest.raises(ValueError, match="required pass"):
        runner.orchestrate(**arguments)
    assert stages == ["validating_timing"]
    assert not arguments["canary"].exists()
    assert json.loads((arguments["state"] / "status.json").read_text())["status"] == "failed"


def test_changed_acquisition_source_prevents_any_subprocess(setup):
    arguments, stages, _ = setup
    (arguments["repo"] / "scripts/t22_kv_cpu_canary_v0.py").write_text("changed")
    with pytest.raises(ValueError, match="Bound source changed"):
        runner.orchestrate(**arguments)
    assert stages == []


def test_existing_canary_is_preserved(setup):
    arguments, stages, _ = setup
    arguments["canary"].mkdir()
    marker = arguments["canary"] / "keep"
    marker.write_text("original")
    with pytest.raises(ValueError, match="already exists"):
        runner.orchestrate(**arguments)
    assert marker.read_text() == "original"
    assert stages == []


def test_missing_completion_receipt_requires_real_process_identity(setup):
    arguments, stages, _ = setup
    (arguments["timing"] / "acquisition_receipt.json").unlink()
    with pytest.raises(ValueError, match="completed timing receipt"):
        runner.orchestrate(**arguments)
    assert stages == []


def test_partial_process_identity_is_rejected(setup):
    arguments, stages, _ = setup
    with pytest.raises(ValueError, match="both timing PID"):
        runner.orchestrate(**arguments, timing_pid=123)
    assert stages == []


def test_real_child_nonzero_is_not_a_pass(tmp_path):
    status = {"children": []}
    with pytest.raises(ValueError, match="exited with code 7"):
        runner.run_child([sys.executable, "-c", "print('failed child'); raise SystemExit(7)"],
                         stage="probe", log=tmp_path / "child.log", repo=tmp_path,
                         sources={}, status=status, publish=lambda: None, poll_seconds=0.01)
    assert status["children"][0]["returncode"] == 7
    assert "failed child" in (tmp_path / "child.log").read_text()
