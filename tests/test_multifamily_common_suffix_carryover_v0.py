from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "multifamily_common_suffix_carryover_v0.py"
SPEC = importlib.util.spec_from_file_location(
    "multifamily_common_suffix_carryover_v0",
    SCRIPT,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@dataclass
class Tokenized:
    token_ids: list[int]
    tokens: list[str]


def _config() -> dict:
    return yaml.safe_load(
        (ROOT / "configs" / "multifamily_common_suffix_carryover_v0.yaml").read_text()
    )


def _panel() -> list[dict]:
    return MODULE._panel(ROOT, _config())


def _raw_rows(model_label: str) -> list[Tokenized]:
    panel = _panel()
    model = _config()["models"][model_label]
    contract = model["raw_tokenization_contract"]
    if contract["kind"] == "distinct_atomic_tokens":
        return [Tokenized([1000 + index], []) for index, _ in enumerate(panel)]
    return [
        Tokenized(
            [
                contract["shared_prefix_token_id"],
                contract["family_token_ids"][item["factors"]["family"]],
                contract["slot_token_ids"][
                    int(item["factors"]["matched_slot"].removeprefix("slot_"))
                ],
            ],
            [],
        )
        for item in panel
    ]


def _context_rows(model_label: str) -> dict[str, list[Tokenized]]:
    model = _config()["models"][model_label]
    raw = _raw_rows(model_label)
    return {
        context_id: [
            Tokenized(row.token_ids + [model["suffix_token_ids"][context_id]], [])
            for row in raw
        ]
        for context_id in _config()["input"]["context_order"]
    }


def test_config_fixes_two_common_suffix_contexts_and_one_omnibus() -> None:
    config = _config()
    assert config["protocol_id"] == MODULE.PROTOCOL_ID
    assert config["input"]["context_order"] == ["period", "newline"]
    assert config["input"]["contexts"]["period"]["suffix"] == "."
    assert config["input"]["contexts"]["newline"]["suffix"] == "\n"
    assert config["input"]["position"] == "last_nonpad"
    assert config["input"]["site"] == "resid_post"
    endpoint = config["primary_endpoint"]
    assert endpoint["id"] == (
        "all_context_all_depth_common_suffix_slot_fraction_after_family_centering"
    )
    assert endpoint["synchronized_across_contexts_and_depths"] is True
    assert endpoint["randomization_draws"] == 19999
    assert endpoint["seed"] == 20260829
    assert endpoint["hypothesis_family"] == list(MODULE.MODEL_ROLES)
    assert endpoint["multiplicity"] == "holm"
    assert endpoint["decision_scope"] == "model_level_all_context_all_depth_omnibus_only"


def test_panel_is_the_unchanged_ordered_five_by_ten_t3_panel() -> None:
    config = _config()
    panel = _panel()
    assert len(panel) == 50
    assert [item["id"] for item in panel] == [
        f"{family}_slot_{slot:02d}"
        for family in config["panel"]["family_order"]
        for slot in config["panel"]["slot_order"]
    ]


@pytest.mark.parametrize("model_label", MODULE.MODEL_ROLES)
def test_common_suffix_contract_accepts_exact_raw_prefix_plus_one_token(
    model_label: str,
) -> None:
    config = _config()
    raw = _raw_rows(model_label)
    receipt = MODULE.validate_context_tokenizations(
        raw,
        _context_rows(model_label),
        _panel(),
        config["models"][model_label],
        config["input"],
    )
    assert receipt["context_order"] == ["period", "newline"]
    for context_id in receipt["context_order"]:
        context = receipt["contexts"][context_id]
        assert context["raw_prefix_preserved_count"] == 50
        assert context["unique_combined_sequence_count"] == 50
        assert context["observed_combined_token_counts"] == [
            len(raw[0].token_ids) + 1
        ]
        assert context["suffix_token_id"] == config["models"][model_label][
            "suffix_token_ids"
        ][context_id]


@pytest.mark.parametrize("failure", ["wrong_suffix", "changed_prefix", "extra_token"])
def test_common_suffix_contract_rejects_near_misses(failure: str) -> None:
    config = _config()
    model_label = "olmo3_7b_bf16"
    rows = _context_rows(model_label)
    if failure == "wrong_suffix":
        rows["period"][7].token_ids[-1] += 1
    elif failure == "changed_prefix":
        rows["newline"][19].token_ids[1] += 1
    else:
        rows["period"][31].token_ids.insert(-1, 777)
    with pytest.raises(MODULE.base.ProtocolError, match="Raw-plus-suffix contract failed"):
        MODULE.validate_context_tokenizations(
            _raw_rows(model_label),
            rows,
            _panel(),
            config["models"][model_label],
            config["input"],
        )


def test_common_suffix_contract_checks_exact_roundtrip_when_decoder_is_available() -> None:
    config = _config()
    panel = _panel()
    model_label = "gemma2_2b_4bit"
    raw = _raw_rows(model_label)
    contexts = _context_rows(model_label)
    lookup = {
        tuple(row.token_ids): item["glyph"]
        for item, row in zip(panel, raw, strict=True)
    }
    for context_id in config["input"]["context_order"]:
        suffix = config["input"]["contexts"][context_id]["suffix"]
        lookup.update(
            {
                tuple(row.token_ids): item["glyph"] + suffix
                for item, row in zip(panel, contexts[context_id], strict=True)
            }
        )
    receipt = MODULE.validate_context_tokenizations(
        raw,
        contexts,
        panel,
        config["models"][model_label],
        config["input"],
        decoder=lambda ids: lookup[tuple(ids)],
    )
    assert receipt["contexts"]["period"]["roundtrip_exact_count"] == 50
    assert receipt["contexts"]["newline"]["roundtrip_exact_count"] == 50


def test_context_depth_randomization_is_deterministic_and_uses_all_ten_cells() -> None:
    rng = np.random.default_rng(61)
    family = rng.normal(size=(1, 5, 1, 1, 8))
    slot = rng.normal(size=(2, 1, 10, 5, 8))
    tensor = family + slot
    first = MODULE.synchronized_context_depth_randomization(tensor, draws=199, seed=83)
    second = MODULE.synchronized_context_depth_randomization(tensor, draws=199, seed=83)
    assert first == second
    assert first["profile_order"] == "context_major_then_depth"
    assert first["context_count"] == 2
    assert first["depth_count"] == 5
    assert len(first["overall"]["observed_depth_profile"]) == 10
    assert len(first["overall"]["per_depth_p_greater_equal"]) == 10
    assert len(first["by_context"]) == 2
    assert all(len(cell["observed_depth_profile"]) == 5 for cell in first["by_context"])
    assert first["overall"]["observed_omnibus"] == pytest.approx(
        np.mean(first["overall"]["observed_depth_profile"])
    )


def test_outcome_registry_is_total_for_predeclared_branches() -> None:
    registry = _config()["outcome_pattern_registry"]
    assert set(registry) == {
        "dual_model_common_suffix_recurrence_candidate",
        "gemma_only_common_suffix_heterogeneity",
        "olmo_only_common_suffix_carryover",
        "opposite_null_centered_direction",
        "no_common_suffix_slot_recurrence",
    }
    primary = {
        MODULE.MODEL_ROLES[0]: {"excess_over_null_mean": 0.1, "holm_reject": True},
        MODULE.MODEL_ROLES[1]: {"excess_over_null_mean": 0.2, "holm_reject": True},
    }
    assert MODULE._outcome_pattern(primary) == "dual_model_common_suffix_recurrence_candidate"
    primary[MODULE.MODEL_ROLES[1]]["holm_reject"] = False
    assert MODULE._outcome_pattern(primary) == "gemma_only_common_suffix_heterogeneity"
    primary[MODULE.MODEL_ROLES[0]]["holm_reject"] = False
    primary[MODULE.MODEL_ROLES[1]]["holm_reject"] = True
    assert MODULE._outcome_pattern(primary) == "olmo_only_common_suffix_carryover"
    primary[MODULE.MODEL_ROLES[0]]["excess_over_null_mean"] = -0.1
    assert MODULE._outcome_pattern(primary) == "opposite_null_centered_direction"
    primary[MODULE.MODEL_ROLES[1]]["excess_over_null_mean"] = -0.2
    assert MODULE._outcome_pattern(primary) == "no_common_suffix_slot_recurrence"


def test_t3_reference_is_bound_but_descriptive_and_not_pooled() -> None:
    config = _config()
    reference = MODULE._load_t3_reference(ROOT, config)
    assert reference["role"] == "frozen_descriptive_reference_only"
    assert reference["inferential_pooling"] is False
    assert reference["outcome_pattern"] == "olmo_only_token_structured_recurrence"
    assert set(reference["primary_results"]) == set(MODULE.MODEL_ROLES)
    assert reference["primary_results"]["olmo3_7b_bf16"]["statistic"] == pytest.approx(
        0.5003918689177909
    )


def test_protocol_forbids_intervention_generation_target_access_and_fishing() -> None:
    config = _config()
    assert set(config["forbidden_actions"]) == {
        "activation_intervention",
        "behavioral_generation",
        "protected_target_access",
        "post_outcome_context_layer_family_endpoint_or_seed_selection",
        "direct_cross_model_effect_magnitude_comparison",
        "inferential_reuse_of_t3_raw_glyph_outcomes",
    }
    source = SCRIPT.read_text()
    assert '"intervention_calls": 0' in source
    assert '"generation_calls": 0' in source
    assert '"protected_target_files_opened": 0' in source
    assert '"multiplicity_decision_authorized": False' in source


def test_fake_backend_runs_seal_and_joint_analysis_serializes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config()
    manifest = json.loads((ROOT / MODULE.MANIFEST_PATH).read_text())
    panel = _panel()
    glyph_index = {item["glyph"]: index for index, item in enumerate(panel)}

    class FakeTokenizer:
        def __init__(self, backend: "FakeBackend") -> None:
            self.backend = backend

        def decode(self, ids: list[int], **_: object) -> str:
            return self.backend.decoded[tuple(int(value) for value in ids)]

    class FakeBackend:
        def __init__(self, backend_config: object) -> None:
            locator = str(getattr(backend_config, "model"))
            self.role = next(role for role in MODULE.MODEL_ROLES if role in locator)
            self.spec = config["models"][self.role]
            self.num_layers = int(self.spec["expected_num_layers"])
            self.model_dim = int(self.spec["expected_model_dim"])
            self.resolved_dtype = str(self.spec["expected_resolved_dtype"])
            self.resolved_device = "gpu"
            self.model_config = {"model_type": self.spec["expected_model_type"]}
            if bool(self.spec["expected_quantized"]):
                self.model_config["quantization"] = {"bits": 4}
            self.decoded: dict[tuple[int, ...], str] = {}
            self.tokenizer = FakeTokenizer(self)
            self.closed = False

        def load(self) -> None:
            return None

        def _raw_ids(self, glyph: str) -> list[int]:
            index = glyph_index[glyph]
            contract = self.spec["raw_tokenization_contract"]
            if contract["kind"] == "distinct_atomic_tokens":
                return [1000 + index]
            item = panel[index]
            family = item["factors"]["family"]
            slot = int(item["factors"]["matched_slot"].removeprefix("slot_"))
            return [
                contract["shared_prefix_token_id"],
                contract["family_token_ids"][family],
                contract["slot_token_ids"][slot],
            ]

        def tokenize(self, text: str) -> Tokenized:
            glyph = text[0]
            ids = self._raw_ids(glyph)
            if len(text) == 2:
                context_id = "newline" if text[1] == "\n" else "period"
                ids = ids + [self.spec["suffix_token_ids"][context_id]]
            self.decoded[tuple(ids)] = text
            return Tokenized(ids, [str(value) for value in ids])

        def model_receipt(self) -> dict:
            return {
                "parameter_count": self.spec["expected_parameter_count"],
                "model_artifact": manifest["model_artifacts"][self.role],
                "resolved_device": self.resolved_device,
                "resolved_dtype": self.resolved_dtype,
            }

        def forward(
            self,
            text: str,
            *,
            capture_layers: list[int],
            **_: object,
        ) -> object:
            tokenized = self.tokenize(text)
            index = glyph_index[text[0]]
            family = index // 10
            slot = index % 10
            context = 1 if text[1] == "\n" else 0
            activations = {
                layer: np.full(
                    self.model_dim,
                    family * 0.7 + slot * (1.0 + layer / 100.0) + context * 0.2,
                    dtype=np.float32,
                )
                for layer in capture_layers
            }
            return MODULE.SimpleNamespace(
                token_ids=tokenized.token_ids,
                tokens=tokenized.tokens,
                logits=np.zeros(self.spec["expected_vocab_size"], dtype=np.float32),
                activations=activations,
                latency_ms=0.01,
                peak_memory_bytes=4096,
            )

        def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(MODULE.frozen, "MLXBackend", FakeBackend)
    monkeypatch.setattr(
        MODULE.base,
        "_model_runtime_check",
        lambda _: {"versions": {}, "test_double": True},
    )
    runs: dict[str, Path] = {}
    for role in MODULE.MODEL_ROLES:
        output = tmp_path / role
        receipt = MODULE.run_model(role, tmp_path / f"{role}.model", output)
        assert receipt["status"] == "pass"
        assert receipt["execution"]["model_forward_calls"] == 100
        assert receipt["capture"]["array_shape"] == [
            50,
            2,
            5,
            config["models"][role]["expected_model_dim"],
        ]
        assert MODULE.validate_run(output)["status"] == "pass"
        runs[role] = output

    analysis = tmp_path / "analysis"
    receipt = MODULE.analyze_runs(runs, analysis)
    assert receipt["status"] == "pass"
    assert receipt["context_layer_row_count"] == 20
    assert receipt["randomization_draws_per_model"] == 19999
    assert receipt["t3_raw_reference"]["inferential_pooling"] is False
    assert MODULE.validate_analysis(analysis) == {
        "status": "pass",
        "protocol_id": MODULE.PROTOCOL_ID,
        "outcome_pattern": receipt["outcome_pattern"],
        "context_layer_row_count": 20,
        "scientific_confirmation": False,
    }


def test_manifest_binds_protocol_assets_models_t3_and_static_counts() -> None:
    manifest_path = ROOT / MODULE.MANIFEST_PATH
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["protocol_id"] == MODULE.PROTOCOL_ID
    assert set(manifest["model_artifacts"]) == set(MODULE.MODEL_ROLES)
    assert manifest["static_counts"]["panel_items"] == 50
    assert manifest["static_counts"]["contexts"] == 2
    assert manifest["static_counts"]["fixed_context_depth_cells_per_model"] == 10
    assert manifest["static_counts"]["model_forward_calls_per_model"] == 100
    assert manifest["static_counts"]["randomization_draws_per_model"] == 19999
    assert "artifacts/multifamily_matched_slot_geometry_v0/analysis/analysis_receipt.json" in (
        manifest["frozen_assets"]
    )
    audit = MODULE.audit_freeze(ROOT)
    assert audit["status"] == "pass"
    assert audit["model_roles"] == list(MODULE.MODEL_ROLES)
