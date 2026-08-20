"""The checks that make the ladder refusable, tested on what they must catch.

Each of these is a thing that actually happened or nearly did, not a
hypothetical: a rung holding a constant with nobody named as having
decided it, a dependency pointing at a rung above it, and an axis with no
field, which is how an axis becomes a wish nothing can verify.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "check_rung_declaration",
    Path(__file__).resolve().parents[1] / "scripts" / "check_rung_declaration.py",
)
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)


def _rung(**over):
    base = {
        "number": 1,
        "title": "t",
        "question": "q",
        "axes": [{"name": "a", "field": "payload.x"}],
        "held": [{"what": "w", "value": "v", "decided_by": "campaign"}],
        "gate": "g",
        "winner": "per_cell",
        "status": "declared",
    }
    base.update(over)
    return base


class TestTheRealDeclarationPasses:
    def test_the_shipped_ladder_is_clean(self):
        import yaml

        doc = yaml.safe_load(mod.DECLARATION.read_text())
        assert mod._offences(doc) == []

    def test_every_rung_declares_at_least_one_axis(self):
        import yaml

        doc = yaml.safe_load(mod.DECLARATION.read_text())
        for rung in doc["rungs"]:
            assert rung["axes"], f"rung {rung['number']} varies nothing"


class TestDependenciesPointBackwards:
    def test_a_rung_may_not_stand_on_one_above_it(self):
        # A ladder standing on its own shoulders: an answer that later
        # changes would not propagate to what held it.
        doc = {"rungs": [_rung(number=1, held=[{"what": "w", "decided_by": "rung 2"}])]}
        assert any("not below it" in o for o in mod._offences(doc))

    def test_a_rung_may_not_stand_on_one_that_does_not_exist(self):
        doc = {"rungs": [_rung(number=3, held=[{"what": "w", "decided_by": "rung 2"}])]}
        assert any("not declared" in o for o in mod._offences(doc))

    def test_standing_on_a_lower_rung_is_fine(self):
        doc = {"rungs": [_rung(number=1), _rung(number=2, held=[{"what": "w", "decided_by": "rung 1"}])]}
        assert mod._offences(doc) == []


class TestNothingIsHeldAnonymously:
    def test_a_held_constant_must_name_who_decided_it(self):
        # This is the whole point of the ladder: rung N's constants are
        # rung N-1's answers. A constant nobody decided is a constant
        # nobody can invalidate.
        doc = {"rungs": [_rung(held=[{"what": "the retriever", "value": "knn"}])]}
        assert any("without saying who decided it" in o for o in mod._offences(doc))


class TestAnAxisMustBeCheckable:
    def test_an_axis_with_no_field_at_all_is_an_offence(self):
        doc = {"rungs": [_rung(axes=[{"name": "vibes"}])]}
        assert any("declares no field" in o for o in mod._offences(doc))

    def test_a_null_field_is_allowed_only_with_a_reason(self):
        doc = {"rungs": [_rung(axes=[{"name": "routing", "field": None}])]}
        assert any("no note saying why" in o for o in mod._offences(doc))

        ok = {"rungs": [_rung(axes=[{"name": "routing", "field": None, "note": "a route, not a sweep"}])]}
        assert mod._offences(ok) == []


class TestShape:
    @pytest.mark.parametrize("field", ["number", "title", "question", "axes", "held", "gate", "winner", "status"])
    def test_every_required_field_is_required(self, field):
        rung = _rung()
        del rung[field]
        assert any(f"missing {field}" in o for o in mod._offences({"rungs": [rung]}))

    def test_an_unknown_status_is_refused(self):
        doc = {"rungs": [_rung(status="probably fine")]}
        assert any("is not one of" in o for o in mod._offences(doc))

    def test_duplicate_rung_numbers_are_refused(self):
        doc = {"rungs": [_rung(number=1), _rung(number=1)]}
        assert any("duplicate" in o for o in mod._offences(doc))

    def test_an_empty_ladder_is_refused(self):
        assert mod._offences({"rungs": []}) == ["no rungs declared"]


class TestParkedIsADecision:
    def test_parked_without_a_reason_is_refused(self):
        # The distinction this file exists for: a rung nobody got to and a
        # rung someone decided against look identical unless the reason is
        # written down.
        doc = {"rungs": [_rung(status="parked")]}
        assert any("indistinguishable from forgotten" in o for o in mod._offences(doc))

    def test_parked_with_a_reason_is_fine(self):
        doc = {"rungs": [_rung(status="parked", parked={"reason": "its own chapter, another day"})]}
        assert mod._offences(doc) == []

    def test_the_parked_rung_in_the_real_ladder_carries_its_cost(self):
        import yaml

        doc = yaml.safe_load(mod.DECLARATION.read_text())
        parked = [r for r in doc["rungs"] if r["status"] == "parked"]
        assert parked, "expected at least one parked rung"
        for rung in parked:
            # Resuming should not require rediscovering what it costs.
            assert rung["parked"]["reason"]
            assert rung["parked"]["cost_when_resumed"]
