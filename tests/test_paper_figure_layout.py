"""Regression checks for labels in the manuscript's boxed diagrams."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("matplotlib")

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "paper_figures", ROOT / "paper" / "scripts" / "build_figures.py"
)
assert SPEC is not None and SPEC.loader is not None
FIGURES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURES)


@pytest.mark.parametrize(
    "builder_name", ["build_design", "build_lineage", "build_t21_path_summary"]
)
@pytest.mark.parametrize("dpi", [72, 100, 220])
def test_boxed_diagrams_keep_readable_padding(monkeypatch, builder_name, dpi):
    def inspect_without_export(fig, stem):
        try:
            assert stem in {"t19_design", "t19_lineage", "t21_path_summary"}
            fig.set_dpi(dpi)
            labels = []
            for ax in fig.axes:
                for patch in ax.patches:
                    if not isinstance(patch, FIGURES.FancyBboxPatch):
                        continue
                    center = (
                        patch.get_x() + patch.get_width() / 2,
                        patch.get_y() + patch.get_height() / 2,
                    )
                    matching = [
                        text
                        for text in ax.texts
                        if text.get_position() == pytest.approx(center)
                    ]
                    assert len(matching) == 1
                    labels.append((patch, matching[0]))
            assert (
                len(labels)
                == {"t19_design": 11, "t19_lineage": 5, "t21_path_summary": 3}[stem]
            )
            FIGURES.validate_box_labels(fig, labels)
            return []
        finally:
            FIGURES.plt.close(fig)

    monkeypatch.setattr(FIGURES, "save_figure", inspect_without_export)
    getattr(FIGURES, builder_name)()


@pytest.mark.parametrize(
    "label",
    ["A label far too wide for its box", "one\ntwo\nthree\nfour\nfive\nsix"],
)
def test_overflow_fails_before_export(label):
    fig, ax = FIGURES.plt.subplots(figsize=(2, 2))
    try:
        patch = FIGURES.FancyBboxPatch((0.25, 0.4), 0.5, 0.2, boxstyle="square,pad=0")
        ax.add_patch(patch)
        text = ax.text(0.5, 0.5, label, ha="center", va="center")
        with pytest.raises(ValueError, match="Diagram label"):
            FIGURES.validate_box_labels(fig, [(patch, text)])
    finally:
        FIGURES.plt.close(fig)


@pytest.mark.parametrize(
    "builder_name,source,validator,expected_intervals",
    [
        ("build_model_effects", "MODEL_SOURCE", "validate_models", 18),
        ("build_causal_sites", "CAUSAL_SOURCE", "validate_causal", 12),
        ("build_t20_ceilings", "T20_SOURCE", "validate_t20", 18),
    ],
)
def test_all_reported_intervals_fit_the_axes(
    monkeypatch, builder_name, source, validator, expected_intervals
):
    def inspect_without_export(fig, _stem):
        try:
            FIGURES.validate_interval_bounds(fig)
            count = sum(
                len(collection.get_segments())
                for ax in fig.axes
                for container in ax.containers
                if getattr(container, "has_xerr", False)
                for collection in container.lines[2]
            )
            assert count == expected_intervals
            return []
        finally:
            FIGURES.plt.close(fig)

    monkeypatch.setattr(FIGURES, "save_figure", inspect_without_export)
    payload = FIGURES.load_json(getattr(FIGURES, source))
    rows = getattr(FIGURES, validator)(payload)
    getattr(FIGURES, builder_name)(rows)


def test_clipped_interval_fails_before_export():
    fig, ax = FIGURES.plt.subplots()
    try:
        ax.errorbar([0.25], [0], xerr=[[0.08], [0.10]])
        ax.set_xlim(-0.01, 0.315)
        with pytest.raises(ValueError, match="Confidence interval"):
            FIGURES.validate_interval_bounds(fig)
    finally:
        FIGURES.plt.close(fig)


def test_t21_bounds_are_one_sided_and_unclipped(monkeypatch):
    def inspect(fig, stem):
        try:
            assert stem == "t21_path_summary"
            FIGURES.validate_interval_bounds(fig)
            segments = [
                segment
                for ax in fig.axes
                for container in ax.containers
                if getattr(container, "has_xerr", False)
                for collection in container.lines[2]
                for segment in collection.get_segments()
            ]
            assert len(segments) == 5
            for segment in segments:
                assert 0 < segment[0, 0] < segment[1, 0]
            return []
        finally:
            FIGURES.plt.close(fig)

    monkeypatch.setattr(FIGURES, "save_figure", inspect)
    FIGURES.build_t21_path_summary()
