from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "multifamily_carrier_distance_v0.py"
SPEC = importlib.util.spec_from_file_location("multifamily_carrier_distance_v0", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@dataclass
class Tokenized:
    token_ids: list[int]
    tokens: list[str]


def _config() -> dict:
    return yaml.safe_load(
        (ROOT / "configs" / "multifamily_carrier_distance_v0.yaml").read_text()
    )


def _panel() -> list[dict]:
    return MODULE._panel(ROOT, _config())


def _raw_ids(model_label: str, index: int) -> list[int]:
    config = _config()
    panel = _panel()
    item = panel[index]
    contract = config["models"][model_label]["raw_tokenization_contract"]
    if contract["kind"] == "distinct_atomic_tokens":
        return [1000 + index]
    family = item["factors"]["family"]
    slot = int(item["factors"]["matched_slot"].removeprefix("slot_"))
    if contract["kind"] == "exact_prefix_family_slot_factorization":
        return [
            contract["shared_prefix_token_id"],
            contract["family_token_ids"][family],
            contract["slot_token_ids"][slot],
        ]
    exceptions = {
        "sky_slot_01": [9468, 102032],
        "sky_slot_02": [9468, 107569],
        "social_slot_00": [9468, 100701],
    }
    if item["id"] in exceptions:
        return exceptions[item["id"]]
    family_ids = {"sky": 234, "food": 235, "animals": 238, "transport": 248, "social": 97}
    return [9468, family_ids[family], 239 + slot]


def _raw_rows(model_label: str) -> list[Tokenized]:
    return [Tokenized(_raw_ids(model_label, index), []) for index in range(50)]


def _carrier_rows(model_label: str) -> dict[str, list[Tokenized]]:
    config = _config()
    model = config["models"][model_label]
    return {
        carrier_id: [
            Tokenized(
                _raw_ids(model_label, index)
                + [model["carrier_token_ids"][carrier_id]]
                * config["input"]["carriers"][carrier_id]["repeats"],
                [],
            )
            for index in range(50)
        ]
        for carrier_id in config["input"]["carrier_order"]
    }


def test_config_fixes_carriers_distances_three_models_and_iut() -> None:
    config = _config()
    assert config["protocol_id"] == MODULE.PROTOCOL_ID
    assert config["input"]["carrier_order"] == ["article_a", "pipe"]
    assert config["input"]["distance_order"] == [1, 2, 4, 8]
    assert config["input"]["carriers"]["article_a"] == {"unit": " a", "repeats": 8}
    assert config["input"]["carriers"]["pipe"] == {"unit": " |", "repeats": 8}
    assert config["models"]["order"] == list(MODULE.MODEL_ROLES)
    endpoint = config["primary_endpoint"]
    assert endpoint["id"] == "distance1_recurrence_intersection_logdistance_attenuation"
    assert endpoint["distance_contrast_weights"] == [0.375, 0.125, -0.125, -0.375]
    assert endpoint["intersection_union_p_value"] == (
        "max_distance1_and_attenuation_component_p_values"
    )
    assert endpoint["randomization_draws"] == 19999
    assert endpoint["seed"] == 20260830
    assert endpoint["hypothesis_family"] == list(MODULE.MODEL_ROLES)


def test_panel_is_unchanged_five_by_ten() -> None:
    config = _config()
    panel = _panel()
    assert len(panel) == 50
    assert [item["id"] for item in panel] == [
        f"{family}_slot_{slot:02d}"
        for family in config["panel"]["family_order"]
        for slot in config["panel"]["slot_order"]
    ]


@pytest.mark.parametrize("model_label", MODULE.MODEL_ROLES)
def test_carrier_contract_accepts_exact_raw_plus_eight_identical_tokens(
    model_label: str,
) -> None:
    config = _config()
    receipt = MODULE.validate_carrier_tokenizations(
        _raw_rows(model_label),
        _carrier_rows(model_label),
        _panel(),
        config["models"][model_label],
        config["input"],
    )
    assert receipt["carrier_order"] == ["article_a", "pipe"]
    assert receipt["distance_order"] == [1, 2, 4, 8]
    for carrier_id in receipt["carrier_order"]:
        carrier = receipt["carriers"][carrier_id]
        assert carrier["repeats"] == 8
        assert carrier["raw_prefix_preserved_count"] == 50
        assert carrier["unique_combined_sequence_count"] == 50
        assert all(len(row) == 4 for row in carrier["readout_positions_by_item"])


def test_llama_fixed_roster_has_three_merge_exceptions_and_is_hash_bound() -> None:
    config = _config()
    receipt = MODULE.validate_raw_tokenizations(
        _raw_rows("llama32_3b_bf16"),
        _panel(),
        config["models"]["llama32_3b_bf16"],
    )
    assert receipt["observed_item_token_count_histogram"] == {"2": 3, "3": 47}
    assert receipt["ordered_sequence_sha256"] == (
        "5373ea1d1180ffaa8b40139e048e2a1b960952fd945a520eaf0dbb5ffe9efb7b"
    )
    changed = _raw_rows("llama32_3b_bf16")
    changed[1].token_ids[-1] += 1
    with pytest.raises(MODULE.base.ProtocolError, match="ordered-sequence SHA-256"):
        MODULE.validate_raw_tokenizations(
            changed,
            _panel(),
            config["models"]["llama32_3b_bf16"],
        )


@pytest.mark.parametrize("failure", ["wrong_token", "short_carrier", "changed_prefix"])
def test_carrier_contract_rejects_near_misses(failure: str) -> None:
    config = _config()
    model_label = "olmo3_7b_bf16"
    rows = _carrier_rows(model_label)
    if failure == "wrong_token":
        rows["article_a"][7].token_ids[-1] += 1
    elif failure == "short_carrier":
        rows["pipe"][19].token_ids.pop()
    else:
        rows["article_a"][31].token_ids[1] += 1
    with pytest.raises(MODULE.base.ProtocolError, match="Raw-plus-carrier contract failed"):
        MODULE.validate_carrier_tokenizations(
            _raw_rows(model_label),
            rows,
            _panel(),
            config["models"][model_label],
            config["input"],
        )


def test_distance_randomization_is_deterministic_and_iut_uses_larger_p() -> None:
    rng = np.random.default_rng(77)
    family = rng.normal(size=(5, 1, 1, 12))
    slot = rng.normal(size=(1, 10, 1, 12))
    interaction = 0.4 * rng.normal(size=(5, 10, 1, 12))
    distances = np.asarray([1.0, 0.75, 0.45, 0.2])
    profiles = []
    for carrier in range(2):
        for distance_value in distances:
            for depth in range(5):
                profiles.append(
                    family[:, :, 0, :]
                    + distance_value * slot[:, :, 0, :]
                    + interaction[:, :, 0, :]
                    + carrier * 0.01
                    + depth * 0.001
                )
    tensor = np.stack(profiles, axis=2)
    kwargs = {
        "carrier_count": 2,
        "distance_count": 4,
        "depth_count": 5,
        "weights": [0.375, 0.125, -0.125, -0.375],
        "draws": 199,
        "seed": 101,
    }
    first = MODULE.distance_randomization(tensor, **kwargs)
    second = MODULE.distance_randomization(tensor, **kwargs)
    assert first["distance1_component"] == second["distance1_component"]
    assert first["attenuation_component"] == second["attenuation_component"]
    assert first["distance_profile"].tolist() == pytest.approx(second["distance_profile"].tolist())
    assert first["intersection_union_raw_p"] == max(
        first["distance1_component"]["raw_p"],
        first["attenuation_component"]["raw_p"],
    )
    assert first["attenuation_component"]["statistic"] > 0
    assert first["observed_profile"].shape == (2, 4, 5)


def test_outcome_registry_covers_named_and_mixed_rejection_sets() -> None:
    def cells(rejected: set[str]) -> dict[str, dict[str, bool]]:
        return {role: {"holm_reject": role in rejected} for role in MODULE.MODEL_ROLES}

    assert MODULE._outcome_pattern(cells(set(MODULE.MODEL_ROLES))) == (
        "all_three_distance_attenuation_candidate"
    )
    assert MODULE._outcome_pattern(cells({"llama32_3b_bf16", "olmo3_7b_bf16"})) == (
        "structured_tokenizer_pair_distance_attenuation"
    )
    assert MODULE._outcome_pattern(cells({"olmo3_7b_bf16"})) == (
        "olmo_only_distance_attenuation"
    )
    assert MODULE._outcome_pattern(cells({"gemma2_2b_4bit", "olmo3_7b_bf16"})) == (
        "mixed_model_distance_attenuation"
    )
    assert MODULE._outcome_pattern(cells(set())) == "no_model_distance_attenuation"


def test_protocol_forbids_intervention_generation_target_access_and_overclaim() -> None:
    config = _config()
    assert set(config["forbidden_actions"]) == {
        "activation_intervention",
        "behavioral_generation",
        "protected_target_access",
        "post_outcome_carrier_distance_layer_family_endpoint_or_seed_selection",
        "direct_cross_model_effect_magnitude_comparison",
        "monotonic_decay_or_disappearance_claim_from_fixed_contrast",
        "inferential_reuse_of_t4_outcomes",
    }
    source = SCRIPT.read_text()
    assert '"intervention_calls": 0' in source
    assert '"generation_calls": 0' in source
    assert '"protected_target_files_opened": 0' in source
    assert '"multiplicity_decision_authorized": False' in source


def test_fake_backend_seals_three_runs_and_joint_analysis(
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
            self.logits = np.zeros(self.spec["expected_vocab_size"], dtype=np.float32)

        def load(self) -> None:
            return None

        def tokenize(self, text: str) -> Tokenized:
            index = glyph_index[text[0]]
            ids = _raw_ids(self.role, index)
            if len(text) > 1:
                carrier_id = "pipe" if "|" in text[1:] else "article_a"
                ids = ids + [self.spec["carrier_token_ids"][carrier_id]] * 8
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
            position: int,
            **_: object,
        ) -> object:
            tokenized = self.tokenize(text)
            index = glyph_index[text[0]]
            family = index // 10
            slot = index % 10
            raw_count = len(_raw_ids(self.role, index))
            distance = position - raw_count + 1
            carrier = 1 if "|" in text[1:] else 0
            basis = np.linspace(-0.2, 0.2, self.model_dim, dtype=np.float32)
            activations = {
                layer: basis
                + np.float32(family * 0.35)
                + np.float32(slot * (1.0 / distance) * (1.0 + layer / 100.0))
                + np.float32(carrier * 0.03)
                for layer in capture_layers
            }
            return MODULE.SimpleNamespace(
                token_ids=tokenized.token_ids,
                tokens=tokenized.tokens,
                logits=self.logits,
                activations=activations,
                latency_ms=0.01,
                peak_memory_bytes=4096,
            )

        def close(self) -> None:
            return None

    monkeypatch.setattr(MODULE.frozen, "MLXBackend", FakeBackend)
    monkeypatch.setattr(
        MODULE.base,
        "_model_runtime_check",
        lambda _: {"versions": {}, "test_double": True},
    )
    original_distance = MODULE.distance_randomization

    def quick_distance(tensor: np.ndarray, **kwargs: object) -> dict:
        kwargs["draws"] = 199
        return original_distance(tensor, **kwargs)

    monkeypatch.setattr(MODULE, "distance_randomization", quick_distance)
    runs: dict[str, Path] = {}
    for role in MODULE.MODEL_ROLES:
        path = tmp_path / role
        MODULE.run_model(role, tmp_path / role, path)
        validated = MODULE.validate_run(path)
        assert validated["status"] == "pass"
        assert validated["activations"].shape[:4] == (50, 2, 4, 5)
        assert validated["receipt"]["execution"]["model_forward_calls"] == 400
        runs[role] = path

    analysis_path = tmp_path / "analysis"
    receipt = MODULE.analyze_runs(runs, analysis_path)
    assert receipt["status"] == "pass"
    assert set(receipt["primary_results"]) == set(MODULE.MODEL_ROLES)
    assert receipt["carrier_distance_layer_row_count"] == 120
    assert receipt["intervention_calls"] == 0
    assert receipt["generation_calls"] == 0
    assert MODULE.validate_analysis(analysis_path)["status"] == "pass"
