"""Tests for scripts/lib/feature_producer_coverage.py.

Covers: attribute resolution, bool-flag discovery, coverage-scan
semantics (missing / extras / vacuous), CLI exit codes, and the
caller-injected simulator contract.

Slice: FARM-1.10 (farm-platform loop).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import types
from collections.abc import Iterable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "lib" / "feature_producer_coverage.py"


def _load_module():
    """Import the harness as ``cov`` for in-process unit tests."""
    spec = importlib.util.spec_from_file_location(
        "feature_producer_coverage", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cov = _load_module()


# ---------------------------------------------------------------------------
# Module registration helpers
# ---------------------------------------------------------------------------


def _install_synthetic_module(
    name: str,
    attrs: dict[str, object],
) -> None:
    """Register an ephemeral module in ``sys.modules`` for the duration
    of one test. Cleanup is the test's responsibility (use the
    ``synthetic_module`` fixture below).
    """
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod


@pytest.fixture
def synthetic_module():
    """Provide a registrar + auto-cleaning sys.modules patch."""
    registered: list[str] = []

    def _register(name: str, attrs: dict[str, object]) -> str:
        _install_synthetic_module(name, attrs)
        registered.append(name)
        return name

    yield _register
    for name in registered:
        sys.modules.pop(name, None)


# ---------------------------------------------------------------------------
# resolve_attr
# ---------------------------------------------------------------------------


class TestResolveAttr:
    def test_resolves_module_then_attr(self, synthetic_module) -> None:
        synthetic_module(
            "_fpc_test_resolve_a",
            {"ALL_FEATURES": ["a", "b"]},
        )
        out = cov.resolve_attr("_fpc_test_resolve_a.ALL_FEATURES")
        assert out == ["a", "b"]

    def test_resolves_nested_attr(self, synthetic_module) -> None:
        class Container:
            cols = ("x", "y", "z")

        synthetic_module("_fpc_test_resolve_b", {"Container": Container})
        out = cov.resolve_attr("_fpc_test_resolve_b.Container.cols")
        assert out == ("x", "y", "z")

    def test_raises_on_missing_module(self) -> None:
        with pytest.raises(ImportError):
            cov.resolve_attr("definitely_no_such_module_xyz.attr")

    def test_raises_on_missing_attr(self, synthetic_module) -> None:
        synthetic_module("_fpc_test_resolve_c", {"present": 1})
        with pytest.raises(AttributeError):
            cov.resolve_attr("_fpc_test_resolve_c.absent")

    def test_rejects_bare_name(self) -> None:
        with pytest.raises(ValueError):
            cov.resolve_attr("no_dots")


# ---------------------------------------------------------------------------
# discover_bool_flags
# ---------------------------------------------------------------------------


class _FakeField:
    """Minimal stand-in for a Pydantic FieldInfo (v2) or ModelField (v1).

    Only the ``annotation`` attribute is consulted by
    :func:`feature_producer_coverage.discover_bool_flags`.
    """

    def __init__(self, annotation: object) -> None:
        self.annotation = annotation


class _FakePydanticV2:
    """Stub matching ``BaseModel.model_fields`` (pydantic v2)."""

    def __init__(self, fields: dict[str, object]) -> None:
        self.model_fields = {
            name: _FakeField(ann) for name, ann in fields.items()
        }


class _FakePydanticV1:
    """Stub matching ``BaseModel.__fields__`` (pydantic v1)."""

    def __init__(self, fields: dict[str, object]) -> None:
        self.__fields__ = {
            name: _FakeField(ann) for name, ann in fields.items()
        }


class TestDiscoverBoolFlags:
    """The harness must work with pydantic v1 *and* v2 model shapes.

    We use lightweight stubs instead of importing pydantic so the tests
    run in any CI image (agent-farm itself does not depend on pydantic).
    """

    def test_pydantic_v2_bool_fields_only(self) -> None:
        m = _FakePydanticV2({
            "name": str,
            "compute_a": bool,
            "compute_b": bool,
            "count": int,
            "ratio": float,
        })
        assert cov.discover_bool_flags(m) == ["compute_a", "compute_b"]

    def test_pydantic_v1_bool_fields_only(self) -> None:
        m = _FakePydanticV1({
            "name": str,
            "flag_a": bool,
            "flag_b": bool,
        })
        assert cov.discover_bool_flags(m) == ["flag_a", "flag_b"]

    def test_returns_sorted_alphabetised(self) -> None:
        m = _FakePydanticV2({
            "zeta": bool,
            "alpha": bool,
            "mid": bool,
        })
        assert cov.discover_bool_flags(m) == ["alpha", "mid", "zeta"]

    def test_empty_payload_is_ok(self) -> None:
        m = _FakePydanticV2({})
        assert cov.discover_bool_flags(m) == []

    def test_non_bool_annotations_excluded(self) -> None:
        """``bool | None``, ``Optional[bool]`` and similar are not the
        strict ``bool`` annotation; they are deliberately ignored so the
        harness only iterates on/off knobs.
        """
        m = _FakePydanticV2({
            "strict_flag": bool,
            "maybe_flag": bool | None,  # type: ignore[arg-type]
            "int_field": int,
        })
        assert cov.discover_bool_flags(m) == ["strict_flag"]

    def test_rejects_non_model(self) -> None:
        with pytest.raises(TypeError):
            cov.discover_bool_flags(object())


# ---------------------------------------------------------------------------
# run_coverage_scan
# ---------------------------------------------------------------------------


class TestRunCoverageScan:
    def test_all_columns_produced_returns_empty(self) -> None:
        def simulate(_flags: dict[str, bool]) -> Iterable[str]:
            return ["a", "b", "c"]

        failures = cov.run_coverage_scan(
            all_features=["a", "b", "c"],
            flags=["flag1", "flag2"],
            simulator=simulate,
        )
        assert failures == []

    def test_missing_column_flagged_per_combo(self) -> None:
        def simulate(flags: dict[str, bool]) -> Iterable[str]:
            cols = {"a", "b"}
            if flags.get("emit_c"):
                cols.add("c")
            return cols

        failures = cov.run_coverage_scan(
            all_features=["a", "b", "c"],
            flags=["emit_c"],
            simulator=simulate,
        )
        # Only the emit_c=False combo should fail.
        assert len(failures) == 1
        combo, missing = failures[0]
        assert combo == {"emit_c": False}
        assert missing == ["c"]

    def test_vacuous_all_features_passes(self) -> None:
        def simulate(_flags: dict[str, bool]) -> Iterable[str]:
            return []

        failures = cov.run_coverage_scan(
            all_features=[],
            flags=["x", "y"],
            simulator=simulate,
        )
        assert failures == []

    def test_no_flags_runs_simulator_once(self) -> None:
        calls: list[dict[str, bool]] = []

        def simulate(flags: dict[str, bool]) -> Iterable[str]:
            calls.append(dict(flags))
            return ["a"]

        failures = cov.run_coverage_scan(
            all_features=["a"],
            flags=[],
            simulator=simulate,
        )
        assert failures == []
        assert calls == [{}]

    def test_extras_in_simulator_output_do_not_fail(self) -> None:
        """The dump shard legitimately carries reserved/meta columns
        (``protein_accession``, ``label``, ...). The harness only
        cares about missing ALL_FEATURES columns.
        """
        def simulate(_flags: dict[str, bool]) -> Iterable[str]:
            return ["a", "b", "c", "label", "protein_accession"]

        failures = cov.run_coverage_scan(
            all_features=["a", "b", "c"],
            flags=["flag1"],
            simulator=simulate,
        )
        assert failures == []

    def test_cartesian_product_size(self) -> None:
        """With N flags, every one of the 2**N combos is exercised."""
        seen: set[tuple[tuple[str, bool], ...]] = set()

        def simulate(flags: dict[str, bool]) -> Iterable[str]:
            seen.add(tuple(sorted(flags.items())))
            return ["a"]

        cov.run_coverage_scan(
            all_features=["a"],
            flags=["f1", "f2", "f3"],
            simulator=simulate,
        )
        assert len(seen) == 8  # 2**3

    def test_missing_columns_alphabetised(self) -> None:
        def simulate(_flags: dict[str, bool]) -> Iterable[str]:
            return ["b"]

        failures = cov.run_coverage_scan(
            all_features=["zeta", "alpha", "mid"],
            flags=[],
            simulator=simulate,
        )
        assert failures and failures[0][1] == ["alpha", "mid", "zeta"]


# ---------------------------------------------------------------------------
# format_failures
# ---------------------------------------------------------------------------


class TestFormatFailures:
    def test_empty_failures_returns_empty(self) -> None:
        assert cov.format_failures([]) == ""

    def test_renders_combo_and_missing(self) -> None:
        out = cov.format_failures([
            ({"compute_lineage": False, "compute_v6": False},
             ["lineage_is_ancestor_of_known"]),
        ])
        assert "compute_lineage=False" in out
        assert "compute_v6=False" in out
        assert "lineage_is_ancestor_of_known" in out

    def test_renders_no_flags_marker(self) -> None:
        out = cov.format_failures([({}, ["a"])])
        assert "(no flags)" in out


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


class TestCoercion:
    def test_features_must_be_iterable_of_str(self) -> None:
        with pytest.raises(TypeError):
            cov._coerce_features(123, "label")
        with pytest.raises(TypeError):
            cov._coerce_features(["a", 1, "b"], "label")

    def test_features_rejects_bare_string(self) -> None:
        # A bare string is iterable but would yield single chars.
        with pytest.raises(TypeError):
            cov._coerce_features("abc", "label")

    def test_simulator_must_be_callable(self) -> None:
        with pytest.raises(TypeError):
            cov._coerce_simulator(42, "label")


# ---------------------------------------------------------------------------
# main() — CLI exit codes
# ---------------------------------------------------------------------------


class TestMain:
    def test_exit_0_on_full_coverage(
        self, capsys: pytest.CaptureFixture, synthetic_module
    ) -> None:
        mod = synthetic_module("_fpc_main_a", {
            "ALL_FEATURES": ["a", "b"],
            "simulate": lambda _flags: ["a", "b", "extra"],
        })
        rc = cov.main([
            "--features-module", f"{mod}.ALL_FEATURES",
            "--simulator-module", f"{mod}.simulate",
            "--flags", "f1", "f2",
        ])
        assert rc == 0
        captured = capsys.readouterr()
        assert "coverage OK" in captured.out
        # 2**2 == 4 combos
        assert "4 flag combo(s)" in captured.out

    def test_exit_1_on_missing_column(
        self, capsys: pytest.CaptureFixture, synthetic_module
    ) -> None:
        mod = synthetic_module("_fpc_main_b", {
            "ALL_FEATURES": ["a", "b", "c"],
            "simulate": lambda flags: (
                ["a", "b", "c"] if flags.get("compute_c") else ["a", "b"]
            ),
        })
        rc = cov.main([
            "--features-module", f"{mod}.ALL_FEATURES",
            "--simulator-module", f"{mod}.simulate",
            "--flags", "compute_c",
        ])
        assert rc == 1
        captured = capsys.readouterr()
        assert "FAILED" in captured.err
        assert "'c'" in captured.err
        assert "compute_c=False" in captured.err

    def test_exit_2_on_bad_module(
        self, capsys: pytest.CaptureFixture, synthetic_module
    ) -> None:
        mod = synthetic_module("_fpc_main_c", {
            "ALL_FEATURES": ["a"],
            "simulate": lambda _flags: ["a"],
        })
        rc = cov.main([
            "--features-module", "no_such_mod_xyz.X",
            "--simulator-module", f"{mod}.simulate",
            "--flags",
        ])
        assert rc == 2
        captured = capsys.readouterr()
        assert "error:" in captured.err

    def test_exit_2_when_neither_payload_nor_flags(
        self, capsys: pytest.CaptureFixture, synthetic_module
    ) -> None:
        mod = synthetic_module("_fpc_main_d", {
            "ALL_FEATURES": ["a"],
            "simulate": lambda _flags: ["a"],
        })
        rc = cov.main([
            "--features-module", f"{mod}.ALL_FEATURES",
            "--simulator-module", f"{mod}.simulate",
        ])
        assert rc == 2
        captured = capsys.readouterr()
        assert "--payload-module or --flags" in captured.err

    def test_payload_module_discovers_flags(
        self, capsys: pytest.CaptureFixture, synthetic_module
    ) -> None:
        # Use the same lightweight pydantic-v2 stub as TestDiscoverBoolFlags
        # so this test runs without pydantic installed.
        fake_payload = _FakePydanticV2({
            "output_name": str,
            "compute_alignments": bool,
            "compute_taxonomy": bool,
        })

        mod = synthetic_module("_fpc_main_e", {
            "ALL_FEATURES": ["a"],
            "FakePayload": fake_payload,
            # The simulator emits "a" only when both flags are True;
            # this forces 3 of 4 combos to fail and proves the harness
            # discovered the two boolean fields.
            "simulate": lambda flags: (
                ["a"]
                if flags.get("compute_alignments") and flags.get("compute_taxonomy")
                else []
            ),
        })
        rc = cov.main([
            "--features-module", f"{mod}.ALL_FEATURES",
            "--simulator-module", f"{mod}.simulate",
            "--payload-module", f"{mod}.FakePayload",
        ])
        assert rc == 1
        captured = capsys.readouterr()
        # Three failing combos (the all-True combo passes).
        assert captured.err.count("missing:") == 3

    def test_quiet_suppresses_success_banner(
        self, capsys: pytest.CaptureFixture, synthetic_module
    ) -> None:
        mod = synthetic_module("_fpc_main_f", {
            "ALL_FEATURES": ["a"],
            "simulate": lambda _flags: ["a"],
        })
        rc = cov.main([
            "--features-module", f"{mod}.ALL_FEATURES",
            "--simulator-module", f"{mod}.simulate",
            "--flags",
            "--quiet",
        ])
        assert rc == 0
        captured = capsys.readouterr()
        assert captured.out == ""


# ---------------------------------------------------------------------------
# Regression: the canonical-feature incident
# ---------------------------------------------------------------------------


class TestCanonicalIncidentRegression:
    """Mirrors the 2026-05-13 incident: 4 lineage_* columns added to
    ALL_FEATURES, lineage producer only fires when ``compute_lineage_features``
    is True. The harness must flag every combo where the flag is False
    (eight combos out of sixteen for a four-flag payload).
    """

    def test_lineage_columns_uncovered_unless_flag_on(self) -> None:
        all_features = [
            "distance",
            "lineage_is_ancestor_of_known",
            "lineage_is_descendant_of_known",
            "lineage_ancestor_of_count",
            "lineage_descendant_of_count",
        ]
        flags = [
            "compute_alignments",
            "compute_lineage_features",
            "compute_taxonomy",
            "compute_v6_features",
        ]

        def simulate(combo: dict[str, bool]) -> Iterable[str]:
            cols = {"distance"}
            if combo.get("compute_lineage_features"):
                cols.update({
                    "lineage_is_ancestor_of_known",
                    "lineage_is_descendant_of_known",
                    "lineage_ancestor_of_count",
                    "lineage_descendant_of_count",
                })
            return cols

        failures = cov.run_coverage_scan(
            all_features=all_features,
            flags=flags,
            simulator=simulate,
        )
        # 16 combos; 8 have compute_lineage_features=False and fail.
        assert len(failures) == 8
        for combo, missing in failures:
            assert combo["compute_lineage_features"] is False
            assert "lineage_is_ancestor_of_known" in missing

    def test_lineage_fix_with_unconditional_default(self) -> None:
        """Post-fix simulator (PR #364 style): zero-fill defaults so
        every record carries the 4 columns regardless of flag.
        """
        all_features = [
            "distance",
            "lineage_is_ancestor_of_known",
            "lineage_is_descendant_of_known",
            "lineage_ancestor_of_count",
            "lineage_descendant_of_count",
        ]
        flags = ["compute_lineage_features"]

        def simulate(combo: dict[str, bool]) -> Iterable[str]:
            # Unconditional skeleton (the dump fix).
            cols = {
                "distance",
                "lineage_is_ancestor_of_known",
                "lineage_is_descendant_of_known",
                "lineage_ancestor_of_count",
                "lineage_descendant_of_count",
            }
            return cols

        failures = cov.run_coverage_scan(
            all_features=all_features,
            flags=flags,
            simulator=simulate,
        )
        assert failures == []


# ---------------------------------------------------------------------------
# Subprocess smoke (covers shebang + permissions)
# ---------------------------------------------------------------------------


class TestSubprocess:
    def test_cli_help(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "FARM-1.10" in result.stdout
