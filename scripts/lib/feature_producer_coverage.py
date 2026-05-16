#!/usr/bin/env python3
"""ALL_FEATURES producer-coverage guard (FARM-1.10).

Background
==========

`protea_contracts.ALL_FEATURES` is the canonical column list for the
re-ranker dump and inference parquets. The dump pipeline enforces a
`shard.columns superset_of ALL_FEATURES` invariant at write time
(`protea/core/parquet_export.py:_assert_canonical_columns`). When a new
column is added to `ALL_FEATURES` without an unconditional producer in
the dump path, the invariant fails AFTER multi-hour KNN compute. The
2026-05-13 incident (4 `lineage_*` columns shipped by T-RES.1b, LB.1 v226
failed after ~5h with `missing=['lineage_is_ancestor_of_known', ...]`)
is the canonical example. See
`context/memory/project_canonical_feature_producer_consumer.md`.

This module ships a generic harness that lets caller repos
(`protea-contracts`, `protea-reranker-lab`, PROTEA itself) wire a 1-sec
CI check that exercises every payload feature-flag combination and asserts
the producer DAG covers every column in `ALL_FEATURES`.

Wiring contract
===============

The caller provides:

1. ``--features-module`` — fully-qualified module attribute that resolves
   to an iterable of column-name strings (e.g.
   ``protea_contracts.feature_schema.ALL_FEATURES``).
2. ``--simulator-module`` — fully-qualified module attribute that
   resolves to a callable ``(flags: dict[str, bool]) -> Iterable[str]``.
   The callable simulates one dry-run of the dump producer DAG under the
   given flag set and returns the produced column names. The harness
   only relies on the return value; the simulator is free to mock IO.
3. ``--payload-module`` (optional) — fully-qualified attribute that
   resolves to a Pydantic ``BaseModel`` subclass; the harness introspects
   its ``bool`` fields to discover the flag set. If omitted, the caller
   must pass ``--flags`` directly.
4. ``--flags`` (optional) — explicit space-separated list of bool flag
   names, used when no payload model is available (lab side, scripts).

The harness then iterates ``itertools.product([False, True], repeat=N)``
over those N flags and asserts that for every combo, the simulator's
output is a superset of ``ALL_FEATURES``. Missing columns are reported
per combo on stderr; exit code is 1 on any failure, 0 otherwise.

Idempotency / dependencies
==========================

The harness imports nothing from PROTEA or its dependency tree by
itself. The `--simulator-module` import is what pulls heavy deps in;
callers that cannot afford an editable install in CI can stub the
simulator with synthetic data (as the unit tests in this repo do).

CLI usage
=========

.. code-block:: bash

   python3 scripts/lib/feature_producer_coverage.py \\
       --features-module protea_contracts.feature_schema.ALL_FEATURES \\
       --payload-module protea.core.operations.export_research_dataset.ExportResearchDatasetPayload \\
       --simulator-module my_pkg.coverage_sim.simulate

Exit codes
==========

* 0 — every combination produces a superset of ALL_FEATURES.
* 1 — at least one combination is missing one or more columns.
* 2 — invocation error (bad import, missing required arg, type
       mismatch on the resolved object).
"""

from __future__ import annotations

import argparse
import importlib
import itertools
import sys
from collections.abc import Callable, Iterable, Sequence
from typing import Any


class CoverageError(RuntimeError):
    """Raised when the producer DAG fails to cover ALL_FEATURES for a combo."""


def resolve_attr(dotted: str) -> Any:
    """Resolve a dotted ``module.path.attr`` string to a Python object.

    Walks the module path left-to-right, importing the longest valid
    prefix, then traverses attribute access. Raises ``ImportError`` (with
    a wrapped explanation) if no prefix resolves; ``AttributeError`` if
    the prefix imports but the attribute is missing.
    """
    if not dotted or "." not in dotted:
        raise ValueError(
            f"expected dotted module.attr path, got: {dotted!r}"
        )
    parts = dotted.split(".")
    # find the longest importable prefix
    module = None
    split_at = 0
    for idx in range(len(parts), 0, -1):
        candidate = ".".join(parts[:idx])
        try:
            module = importlib.import_module(candidate)
            split_at = idx
            break
        except ImportError:
            continue
    if module is None:
        raise ImportError(
            f"could not import any prefix of {dotted!r} as a module"
        )
    obj: Any = module
    for attr in parts[split_at:]:
        obj = getattr(obj, attr)
    return obj


def discover_bool_flags(payload_model: Any) -> list[str]:
    """Return the alphabetised list of bool-typed field names on a model.

    Supports two model shapes:

    * Pydantic v2 ``BaseModel`` (``model_fields`` dict).
    * Pydantic v1 ``BaseModel`` (``__fields__`` dict).

    Fields whose annotation is exactly ``bool`` are considered flags.
    Optional / Union / list-of-bool fields are skipped because they are
    not on/off knobs the dump path branches on.
    """
    fields = getattr(payload_model, "model_fields", None)
    if fields is None:
        fields = getattr(payload_model, "__fields__", None)
    if fields is None:
        raise TypeError(
            f"{payload_model!r} has neither model_fields nor __fields__; "
            "expected a Pydantic BaseModel subclass."
        )
    bool_flags: list[str] = []
    for name, field in fields.items():
        annotation = getattr(field, "annotation", None)
        # pydantic v1 stores type on .outer_type_ as a fallback
        if annotation is None:
            annotation = getattr(field, "outer_type_", None)
        if annotation is bool:
            bool_flags.append(name)
    return sorted(bool_flags)


def run_coverage_scan(
    *,
    all_features: Sequence[str],
    flags: Sequence[str],
    simulator: Callable[[dict[str, bool]], Iterable[str]],
) -> list[tuple[dict[str, bool], list[str]]]:
    """Run the cartesian-product coverage scan.

    Returns a list of ``(flag_combo, missing_columns)`` pairs for every
    combination where ``simulator(combo)`` failed to produce a superset
    of ``all_features``. The list is empty when every combination passes.

    A vacuous ``all_features`` (empty list) trivially passes for every
    combo and returns ``[]``.
    """
    canonical = list(all_features)
    failures: list[tuple[dict[str, bool], list[str]]] = []
    # Even with zero flags, exercise the simulator once with an empty dict.
    if not flags:
        produced = set(simulator({}))
        missing = sorted(c for c in canonical if c not in produced)
        if missing:
            failures.append(({}, missing))
        return failures
    for combo_values in itertools.product([False, True], repeat=len(flags)):
        combo = dict(zip(flags, combo_values, strict=True))
        produced = set(simulator(dict(combo)))
        missing = sorted(c for c in canonical if c not in produced)
        # We don't fail on extras (the dump can legitimately carry
        # reserved/metadata columns beyond ALL_FEATURES); only on missing.
        if missing:
            failures.append((combo, missing))
    return failures


def format_failures(
    failures: Sequence[tuple[dict[str, bool], list[str]]],
) -> str:
    """Render a human-readable summary of coverage failures."""
    if not failures:
        return ""
    lines = [
        f"feature-producer coverage FAILED: {len(failures)} combo(s) "
        "missing columns from ALL_FEATURES.",
        "",
    ]
    for combo, missing in failures:
        if combo:
            combo_str = ", ".join(
                f"{k}={v}" for k, v in sorted(combo.items())
            )
        else:
            combo_str = "(no flags)"
        lines.append(f"  combo: {combo_str}")
        lines.append(f"    missing: {missing!r}")
    lines.append("")
    lines.append(
        "Fix: wire an unconditional producer for the missing columns in "
        "the dump path. See "
        "context/memory/project_canonical_feature_producer_consumer.md."
    )
    return "\n".join(lines)


def _coerce_features(obj: Any, label: str) -> list[str]:
    """Validate that the resolved features object is an iterable of str."""
    if isinstance(obj, str):
        raise TypeError(
            f"{label} resolved to a string, expected iterable of strings"
        )
    try:
        items = list(obj)
    except TypeError as exc:
        raise TypeError(
            f"{label} is not iterable: {obj!r}"
        ) from exc
    bad = [x for x in items if not isinstance(x, str)]
    if bad:
        raise TypeError(
            f"{label} contains non-string entries: {bad[:5]!r}"
        )
    return items


def _coerce_simulator(obj: Any, label: str) -> Callable[[dict[str, bool]], Iterable[str]]:
    """Validate that the resolved simulator is callable."""
    if not callable(obj):
        raise TypeError(f"{label} is not callable: {obj!r}")
    return obj  # type: ignore[return-value]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="feature_producer_coverage.py",
        description=(
            "FARM-1.10 guard: verify every payload-flag combination "
            "produces a superset of ALL_FEATURES on the dump path."
        ),
    )
    parser.add_argument(
        "--features-module",
        required=True,
        metavar="MODULE.ATTR",
        help=(
            "Dotted path to the ALL_FEATURES iterable, e.g. "
            "protea_contracts.feature_schema.ALL_FEATURES."
        ),
    )
    parser.add_argument(
        "--simulator-module",
        required=True,
        metavar="MODULE.ATTR",
        help=(
            "Dotted path to a callable "
            "simulate(flags: dict[str, bool]) -> Iterable[str] that "
            "walks the dump producer DAG and returns the produced "
            "column names."
        ),
    )
    parser.add_argument(
        "--payload-module",
        default=None,
        metavar="MODULE.ATTR",
        help=(
            "Dotted path to a Pydantic BaseModel whose bool fields are "
            "the dump-path feature flags. When given, --flags is "
            "ignored. When omitted, --flags is required."
        ),
    )
    parser.add_argument(
        "--flags",
        nargs="*",
        default=None,
        metavar="FLAG",
        help=(
            "Explicit list of bool flag names to iterate over (used "
            "when no payload model is available). Empty list is "
            "allowed and triggers a single dry run."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the success banner. Failures always print.",
    )
    args = parser.parse_args(argv)

    try:
        features_raw = resolve_attr(args.features_module)
        all_features = _coerce_features(
            features_raw, args.features_module
        )
        simulator_raw = resolve_attr(args.simulator_module)
        simulator = _coerce_simulator(
            simulator_raw, args.simulator_module
        )
        if args.payload_module is not None:
            payload_model = resolve_attr(args.payload_module)
            flags = discover_bool_flags(payload_model)
        elif args.flags is not None:
            flags = sorted(args.flags)
        else:
            print(
                "error: either --payload-module or --flags is required",
                file=sys.stderr,
            )
            return 2
    except (ImportError, AttributeError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    failures = run_coverage_scan(
        all_features=all_features,
        flags=flags,
        simulator=simulator,
    )

    if failures:
        print(format_failures(failures), file=sys.stderr)
        return 1

    if not args.quiet:
        n_combos = max(1, 2 ** len(flags))
        print(
            f"feature-producer coverage OK: "
            f"{n_combos} flag combo(s), "
            f"{len(all_features)} canonical column(s).",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
