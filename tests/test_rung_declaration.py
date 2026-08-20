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


class TestStratifiedReportingIsALadderProperty:
    """Not a rung. The measurement that motivated one showed it was the
    wrong shape: a global number that inverts under stratification means
    stratification is the condition under which any rung means anything,
    not a step to take after the others."""

    def test_the_ladder_declares_how_it_reports(self):
        import yaml

        doc = yaml.safe_load(mod.DECLARATION.read_text())
        rep = doc["reporting"]
        assert rep["stratify"] == "required"
        assert rep["winner"] == "per_cell"
        assert "homology" in rep["axes"]

    def test_it_says_aggregates_are_forbidden_rather_than_discouraged(self):
        import yaml

        doc = yaml.safe_load(mod.DECLARATION.read_text())
        assert doc["reporting"]["forbidden"]

    def test_the_self_match_rule_is_written_down(self):
        # The band is meaningless without it: including the query's own
        # sequence moves the median identity from 41.2 to 100.0 and puts
        # 88 per cent of the corpus in the near-identical band.
        import yaml

        doc = yaml.safe_load(mod.DECLARATION.read_text())
        assert "sequence_id" in doc["reporting"]["self_match"]

    def test_no_rung_duplicates_the_reporting_rule(self):
        # Per-stratum policy was rung 6 and is now a property. If it comes
        # back as a rung, one of the two is wrong.
        import yaml

        doc = yaml.safe_load(mod.DECLARATION.read_text())
        titles = [r["title"].lower() for r in doc["rungs"]]
        assert not any("per-stratum policy" == t for t in titles)

    def test_length_is_named_as_not_a_substitute(self):
        # A table stratified by length looks like a stratified table.
        # Measured: homology spans a factor of 8.5 and length ties, and the
        # extremes inside each length band are the twilight cells.
        import yaml

        doc = yaml.safe_load(mod.DECLARATION.read_text())
        assert "length" in doc["reporting"]["length_is_not_a_substitute"]


class TestWhatCarriesTheHardBand:
    """The sharpest statement of what the method contributes, and it is
    neither of the two things the project is usually described by."""

    def test_the_finding_is_written_down(self):
        import yaml

        doc = yaml.safe_load(mod.DECLARATION.read_text())
        claim = doc["reporting"]["what_carries_the_hard_band"]
        assert "consensus" in claim
        # Named as NOT the two obvious candidates, because both are what a
        # reader would assume and both were measured weaker.
        assert "identity" in claim and "similarity" in claim

    def test_the_retriever_rung_asks_about_agreement_too(self):
        # If consensus carries twilight, a retriever whose top hit is right
        # and whose neighbourhood disagrees loses the band it was brought in
        # to win. Measuring only top-hit accuracy answers another question.
        import yaml

        doc = yaml.safe_load(mod.DECLARATION.read_text())
        rung = next(r for r in doc["rungs"] if r["title"] == "the retriever")
        assert "secondary_question" in rung
        assert "AGREES" in rung["secondary_question"]
