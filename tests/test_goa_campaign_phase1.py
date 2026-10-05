"""La fase 1 del universo: lo que el driver tiene que no confundir.

El universo se construye desde los 75 GAF antes de cargar una sola anotacion.
Dos cosas de ese modo fallarian en silencio y cuestan la serie entera, asi que se
fijan aqui.
"""

from __future__ import annotations

import importlib.util
import pathlib
from unittest.mock import patch

REPO = pathlib.Path(__file__).resolve().parents[1]
DRIVER = REPO / "plans" / "clean-campaign" / "goa_campaign_driver.py"
PLAN = REPO / "plans" / "GOA-ONTOLOGY-PAIRING.md"


def _driver():
    spec = importlib.util.spec_from_file_location("goa_driver", DRIVER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestLaSerieTiene75:
    def test_el_plan_cubre_156_a_235(self):
        """Eran 71 (160..235) mientras se creyo que la serie empezaba en la 160.
        El archivo de EBI tiene cuatro mas antes, y parse_plan ABORTA si la cuenta
        no cuadra, asi que un plan desactualizado no arranca la campana: la para.
        """
        d = _driver()
        plan = d.parse_plan(str(PLAN))
        assert len(plan) == 75
        assert plan[0][0] == 156
        assert plan[-1][0] == 235

    def test_las_206_a_210_no_existen(self):
        """235-156+1 son 80, no 75. Las cinco que faltan no estan en el archivo,
        y si alguien las anade 'para completar' el driver pedira ficheros que no
        hay."""
        d = _driver()
        releases = {r for r, _ in d.parse_plan(str(PLAN))}
        assert not (releases & {206, 207, 208, 209, 210})
        assert len(releases) == 75

    def test_expected_releases_concuerda_con_el_plan(self):
        """La constante y la tabla se desincronizan por separado."""
        d = _driver()
        assert d.EXPECTED_RELEASES == len(d.parse_plan(str(PLAN)))


class TestUnDryRunNoCuentaComoHecho:
    """Un dry_run termina en SUCCEEDED sin escribir nada. Si contara como hecho,
    el resume saltaria precisamente la release cuyo universo no se construyo, y
    la serie quedaria con un agujero que nada senala: las cargas de la fase 2
    para esa release descartarian sus proteinas en silencio, que es el defecto
    original de toda la campana."""

    def test_la_consulta_excluye_los_dry_run(self):
        d = _driver()
        captured = {}

        class _Out:
            returncode = 0
            stdout = ""
            stderr = ""

        def fake_run(cmd, **kw):
            captured["sql"] = cmd[-1]
            return _Out()

        with patch.object(d.subprocess, "run", fake_run):
            d.universe_done(object())

        sql = captured["sql"]
        assert "ensure_goa_universe" in sql
        assert "SUCCEEDED" in sql
        assert "dry_run" in sql, "sin este filtro un dry run marca la release como hecha"

    def test_extrae_la_release_de_la_url_del_gaf(self):
        """El payload de ensure_goa_universe no lleva source_version (el modelo lo
        prohibe), asi que la release sale de la url. Si el patron cambia, el
        resume no reconoce nada y repite las 75."""
        d = _driver()

        class _Out:
            returncode = 0
            stdout = (
                "http://100.64.0.1:8790/goa_uniprot_all.gaf.156.gz\n"
                "http://100.64.0.1:8790/goa_uniprot_all.gaf.235.gz\n"
            )
            stderr = ""

        with patch.object(d.subprocess, "run", lambda *a, **k: _Out()):
            assert d.universe_done(object()) == {156, 235}


class TestElResultadoSeRegistra:
    """La tabla job NO tiene columna result y la API no la expone; el resultado
    vive solo en el evento. Leer job['result'] registra null para una pasada que
    funciono, y entonces las cifras que justifican la corrida no estan en el log.
    """

    def test_lo_saca_del_evento_done(self):
        d = _driver()

        class _Api:
            def call(self, verb, path, body=None):
                return [
                    {"event": "job.started", "fields": {}},
                    {"event": "ensure_goa_universe.done",
                     "fields": {"proteins_inserted": 106345, "not_retrievable": 10791}},
                ]

        got = d.job_result(_Api(), "abc")
        assert got["proteins_inserted"] == 106345
        assert got["not_retrievable"] == 10791

    def test_cae_al_job_succeeded_si_no_hay_done(self):
        d = _driver()

        class _Api:
            def call(self, verb, path, body=None):
                return [{"event": "job.succeeded", "fields": {"result": {"proteins_inserted": 7}}}]

        assert d.job_result(_Api(), "abc") == {"proteins_inserted": 7}

    def test_un_fallo_al_leer_eventos_no_tumba_la_release(self):
        """El log es log: si los eventos no se pueden leer, la release sigue."""
        d = _driver()

        class _Api:
            def call(self, verb, path, body=None):
                raise RuntimeError("red caida")

        assert d.job_result(_Api(), "abc") == {}
