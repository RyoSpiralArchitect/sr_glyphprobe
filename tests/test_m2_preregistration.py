from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "audit_m2_preregistration.py"
SPEC = importlib.util.spec_from_file_location("audit_m2_preregistration", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_config(*, panel: str, source: str) -> dict:
    return {
        "schema_version": 1,
        "mode": "internal",
        "backend": {
            "kind": "mlx",
            "model": AUDIT.EXPECTED_MODEL_ID,
            "revision": AUDIT.EXPECTED_MODEL_REVISION,
            "device": "gpu",
            "dtype": "float32",
            "local_files_only": True,
            "validation_receipt": AUDIT.EXPECTED_VALIDATION_RECEIPT,
            "validation_receipt_sha256": AUDIT.EXPECTED_VALIDATION_RECEIPT_SHA256,
        },
        "run": {
            "seeds": [101, 211, 307],
            "replicate_mode": "wrapper_subsample",
            "wrapper_subsample_fraction": 0.75,
        },
        "panel": {"file": panel, "neutral_glyph": "🟰", "centroid_mode": "panel"},
        "source": {"wrappers_file": source, "max_wrappers": 16},
        "targets": {
            "cases_file": AUDIT.EXPECTED_P2_TARGETS,
            "max_cases": 48,
            "calibration_cases": 12,
        },
        "capture": {"site": "resid_post", "layers": [2, 4]},
        "intervention": {
            "normalization": "rms",
            "strengths": [0.05],
            "clip": {"mode": "global_rms", "max_ratio": 0.25},
            "iso_kl": {"enabled": False},
        },
        "controls": {
            "random_directions_per_layer": 0,
            "zero_direction": True,
            "sign_flip": False,
            "sign_flip_strengths": [],
            "label_shuffle_permutations": 0,
            "include_neutral_direction": False,
        },
        "metrics": {
            "fingerprint_dim": 96,
            "fingerprint_seed": 8_675_309,
            "split_half_repeats": 1,
        },
        "surface": {"emoji_template": "{emoji}\n{prompt}", "neutral_template": "{prompt}"},
    }


def test_required_surface_is_exact_and_includes_audit_itself() -> None:
    assert len(AUDIT.REQUIRED_FROZEN_PATHS) == 35
    assert len(set(AUDIT.REQUIRED_FROZEN_PATHS)) == 35
    assert set(AUDIT.P2_CONFIG_CONTRACTS) == {
        path
        for path in AUDIT.REQUIRED_FROZEN_PATHS
        if path.startswith("configs/m2_p2_")
    }
    assert "scripts/audit_m2_preregistration.py" in AUDIT.REQUIRED_FROZEN_PATHS
    assert "data/targets/c1_causal_holdout_targets_v1.jsonl" in AUDIT.REQUIRED_FROZEN_PATHS
    assert "data/targets/prestage_targets.jsonl" in AUDIT.REQUIRED_FROZEN_PATHS
    assert "data/wrappers/source_wrappers.jsonl" in AUDIT.REQUIRED_FROZEN_PATHS
    assert "data/emoji_panels/colored_shapes.yaml" in AUDIT.REQUIRED_FROZEN_PATHS
    assert "validation/mlx_gpt2_parity/receipt.json" in AUDIT.REQUIRED_FROZEN_PATHS


@pytest.mark.parametrize(
    "unsafe",
    ["/absolute/file", "../escape", "a/../escape", "a//b", "./a", "a\\b"],
)
def test_manifest_paths_fail_closed_when_not_canonical(unsafe: str) -> None:
    with pytest.raises(AUDIT.PreregistrationAuditError):
        AUDIT._safe_repo_relative_path(unsafe)


def test_manifest_file_table_verifies_exact_set_and_hashes(tmp_path: Path) -> None:
    paths = ("frozen/a.txt", "frozen/b.txt")
    for relative, payload in zip(paths, (b"alpha\n", b"beta\n")):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    manifest = {
        "files": [
            {"path": path, "sha256": _sha256(tmp_path / path)}
            for path in reversed(paths)
        ]
    }

    verified = AUDIT.validate_manifest_file_table(
        tmp_path,
        manifest,
        required_paths=paths,
    )

    assert [row["path"] for row in verified] == sorted(paths)
    assert all(row["actual_sha256"] == row["expected_sha256"] for row in verified)


def test_manifest_file_table_rejects_duplicate_missing_extra_and_tampering(
    tmp_path: Path,
) -> None:
    path = tmp_path / "frozen.txt"
    path.write_text("sealed\n", encoding="utf-8")
    record = {"path": "frozen.txt", "sha256": _sha256(path)}

    with pytest.raises(AUDIT.PreregistrationAuditError, match="duplicate"):
        AUDIT.validate_manifest_file_table(
            tmp_path,
            {"files": [record, record]},
            required_paths=("frozen.txt",),
        )
    with pytest.raises(AUDIT.PreregistrationAuditError, match="path set mismatch"):
        AUDIT.validate_manifest_file_table(
            tmp_path,
            {"files": [record]},
            required_paths=("frozen.txt", "missing.txt"),
        )
    extra = tmp_path / "extra.txt"
    extra.write_text("extra\n", encoding="utf-8")
    with pytest.raises(AUDIT.PreregistrationAuditError, match="path set mismatch"):
        AUDIT.validate_manifest_file_table(
            tmp_path,
            {
                "files": [
                    record,
                    {"path": "extra.txt", "sha256": _sha256(extra)},
                ]
            },
            required_paths=("frozen.txt",),
        )
    path.write_text("changed\n", encoding="utf-8")
    with pytest.raises(AUDIT.PreregistrationAuditError, match="SHA-256 mismatch"):
        AUDIT.validate_manifest_file_table(
            tmp_path,
            {"files": [record]},
            required_paths=("frozen.txt",),
        )


@pytest.mark.parametrize(
    ("relative_path", "contract"),
    sorted(AUDIT.P2_CONFIG_CONTRACTS.items()),
)
def test_synthetic_p2_contract_accepts_each_frozen_mapping(
    relative_path: str,
    contract: dict[str, str],
) -> None:
    config = _canonical_config(panel=contract["panel"], source=contract["source"])

    report = AUDIT.validate_p2_config_document(
        config,
        "synthetic config with no holdout reference",
        contract,
        label=relative_path,
    )

    assert report["arm"] == contract["arm"]
    assert report["layers"] == [2, 4]
    assert report["strengths"] == [0.05]
    assert report["seeds"] == [101, 211, 307]


@pytest.mark.parametrize(
    ("field_path", "bad_value", "message"),
    [
        (("backend", "kind"), "torch", "backend.kind"),
        (("backend", "dtype"), "float16", "backend.dtype"),
        (("backend", "local_files_only"), False, "local_files_only"),
        (("run", "seeds"), [101, 211], "run.seeds"),
        (("targets", "max_cases"), 47, "targets.max_cases"),
        (("capture", "layers"), [2, 4, 7], "capture.layers"),
        (("intervention", "strengths"), [0.1], "intervention.strengths"),
        (("controls", "random_directions_per_layer"), 1, "random_directions"),
        (("controls", "zero_direction"), False, "zero_direction"),
        (("controls", "sign_flip"), True, "sign_flip"),
        (("controls", "include_neutral_direction"), True, "neutral_direction"),
        (("metrics", "fingerprint_dim"), 48, "fingerprint_dim"),
        (("metrics", "fingerprint_seed"), 123, "fingerprint_seed"),
    ],
)
def test_synthetic_p2_contract_rejects_execution_drift(
    field_path: tuple[str, str],
    bad_value: object,
    message: str,
) -> None:
    contract = AUDIT.P2_CONFIG_CONTRACTS["configs/m2_p2_primary_mlx.yaml"]
    config = _canonical_config(panel=contract["panel"], source=contract["source"])
    config[field_path[0]][field_path[1]] = bad_value

    with pytest.raises(AUDIT.PreregistrationAuditError, match=message):
        AUDIT.validate_p2_config_document(
            config,
            "synthetic config",
            contract,
            label="synthetic.yaml",
        )


def test_synthetic_p2_contract_rejects_wrong_mapping_and_any_c1_reference() -> None:
    contract = AUDIT.P2_CONFIG_CONTRACTS["configs/m2_p2_primary_mlx.yaml"]
    config = _canonical_config(panel=contract["panel"], source=contract["source"])
    wrong_source = copy.deepcopy(config)
    wrong_source["source"]["wrappers_file"] = AUDIT.INDEPENDENT_SOURCE_WRAPPERS
    with pytest.raises(AUDIT.PreregistrationAuditError, match="source.wrappers_file"):
        AUDIT.validate_p2_config_document(
            wrong_source,
            "synthetic config",
            contract,
            label="synthetic.yaml",
        )

    with pytest.raises(AUDIT.PreregistrationAuditError, match="C1 reference"):
        AUDIT.validate_p2_config_document(
            config,
            "# Do not accidentally use ../data/targets/c1_causal_holdout_targets_v1.jsonl",
            contract,
            label="synthetic.yaml",
        )


def test_unique_yaml_loader_rejects_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.yaml"
    path.write_text("backend:\n  kind: mlx\n  kind: torch\n", encoding="utf-8")
    with pytest.raises(AUDIT.PreregistrationAuditError, match="duplicate YAML key"):
        AUDIT._load_unique_yaml(path)


def test_script_never_imports_or_loads_a_model_or_tokenizer() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "AutoModel" not in source
    assert "AutoTokenizer" not in source
    assert "from_pretrained" not in source
