"""Las fases del universo: lo que el driver tiene que no confundir.

El universo se construye desde los 75 GAF antes de cargar una sola anotacion, y
las secuencias llegan al final, en una sola pasada. Las cosas que fallarian EN
SILENCIO en ese modo cuestan la serie entera, asi que se fijan aqui.
"""

from __future__ import annotations

import importlib.util
import pathlib
from unittest.mock import patch

REPO = pathlib.Path(__file__).resolve().parents[1]
DRIVER = REPO / "plans" / "clean-campaign" / "goa_campaign_driver.py"
PLAN = REPO / "plans" / "GOA-ONTOLOGY-PAIRING.md"


def _driver():
    """The driver module, with ``log`` NEUTRALISED.

    ``log`` appends to ``goa-campaign.log`` next to the script, which on this
    machine is the LIVE campaign log. Without this patch every ``pytest`` run
    wrote nine invented lines into it -- "phase 3: job abc submitted", "FAILURE
    (failed) err=502 de UniProt" -- and four runs left 36. That is not noise: it
    is the record the run's figures are read from, and a test line there is
    indistinguishable from a real failure at that hour.

    Patched in the factory rather than per test, because the defect appeared with
    the FIRST test that called a function that logs, and the next one to do so has
    no reason to remember.
    """
    spec = importlib.util.spec_from_file_location("goa_driver", DRIVER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.log = lambda _msg: None
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
        assert "extract_goa_universe" in sql
        assert "SUCCEEDED" in sql
        assert "dry_run" in sql, "sin este filtro un dry run marca la release como hecha"

    def test_extrae_la_release_de_la_url_del_gaf(self):
        """La release sale de la url y no de un campo. El payload lleva ahora un
        ``release``, pero el que decide si una pasada vieja cuenta es el fichero
        que se leyo, y eso es la url. Si el patron cambia, el resume no reconoce
        nada y repite las 75."""
        d = _driver()
        tiers = '["truth", "curated_inference", "swissprot_of_release"]'

        class _Out:
            returncode = 0
            stdout = (
                f"http://100.64.0.1:8790/goa_uniprot_all.gaf.156.gz\t{tiers}\n"
                f"http://100.64.0.1:8790/goa_uniprot_all.gaf.235.gz\t{tiers}\n"
            )
            stderr = ""

        with patch.object(d.subprocess, "run", lambda *a, **k: _Out()):
            assert d.universe_done(object()) == {156, 235}


class TestHechaSignificaHechaBajoEsteCriterio:
    """El defecto del 2026-10-06, una vuelta mas.

    Al cambiar el criterio se vacio ``protein`` pero NO la tabla ``job``, y el
    resume siguio contando como hechas 13 releases cuyas proteinas ya no
    existian: el arranque dijo "62 releases to go" en vez de 75 y el universo
    habria salido sin nada de lo que solo aportan las releases 222-235.
    """

    def _done_con(self, admit_json):
        d = _driver()

        class _Out:
            returncode = 0
            stdout = f"http://x/goa_uniprot_all.gaf.156.gz\t{admit_json}\n"
            stderr = ""

        with patch.object(d.subprocess, "run", lambda *a, **k: _Out()):
            return d.universe_done(object())

    def test_los_mismos_niveles_en_otro_orden_son_el_mismo_criterio(self):
        """La comparacion es de CONJUNTOS y se hace en Python a proposito:
        ``payload->'admit' = '[...]'::jsonb`` es igualdad ORDENADA de arrays, y
        diria que estos dos payloads son criterios distintos. Decir "no hecha"
        de algo que si se hizo cuesta releer 24 GB."""
        assert self._done_con(
            '["swissprot_of_release", "truth", "curated_inference"]'
        ) == {156}

    def test_un_criterio_mas_estrecho_no_cuenta(self):
        """Una pasada que admitio solo la verdad no construyo el universo que este
        driver va a usar. Decir "hecha" de eso cuesta un agujero en el corpus."""
        assert self._done_con('["truth"]') == set()

    def test_una_pasada_sin_niveles_no_cuenta(self):
        """Las pasadas anteriores al corte llevaban una PALABRA de alcance, no
        niveles, y corrieron bajo ``reliable``, que admitia IBA y ND. Ningun
        conjunto de niveles equivale a eso."""
        assert self._done_con("[]") == set()


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
                    {"event": "extract_goa_universe.done",
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


class TestLaFase3PreguntaALaBase:
    """La fase 3 pide las secuencias UNA vez, al final, y su poblacion no es un
    payload: es "toda fila sin ``sequence_id``" leida en el momento de ejecutar.
    Una lista construida aqui seria una foto de la base tomada antes de encolar
    el job.
    """

    def test_no_encola_nada_si_no_falta_ninguna_secuencia(self):
        """Y no es un fallo: es el estado de una fase 3 que ya corrio."""
        d = _driver()

        class _Api:
            def call(self, *a, **k):
                raise AssertionError("no deberia encolar nada")

        with patch.object(d, "_sin_secuencia", lambda: 0):
            assert d.run_phase3(_Api()) == 0

    def test_el_payload_no_lleva_accesiones(self):
        d = _driver()
        enviado = {}

        class _Api:
            def call(self, verb, path, body=None):
                if verb == "POST":
                    enviado.update(body)
                    return {"id": "abc"}
                return []

            def wait_job(self, job_id, timeout_s):
                return {"status": "succeeded"}

        with patch.object(d, "_sin_secuencia", lambda: 1234):
            assert d.run_phase3(_Api()) == 0
        assert enviado["operation"] == "resolve_protein_sequences"
        assert "accessions" not in enviado["payload"]
        assert "max_accessions" not in enviado["payload"], "una corrida real no se acota"

    def test_un_fallo_del_job_devuelve_error(self):
        d = _driver()

        class _Api:
            def call(self, verb, path, body=None):
                return {"id": "abc"} if verb == "POST" else []

            def wait_job(self, job_id, timeout_s):
                return {"status": "failed", "error_message": "502 de UniProt"}

        with patch.object(d, "_sin_secuencia", lambda: 5):
            assert d.run_phase3(_Api()) == 1

    def test_hay_tres_fases_y_la_cuarta_se_rechaza(self):
        """Un ``--phase 4`` por error no debe caer en la rama por defecto y
        arrancar la fase 2 sobre un universo a medio construir."""
        d = _driver()
        import sys

        with patch.object(sys, "argv", ["driver", "--phase", "4"]):
            try:
                d.main()
            except SystemExit as exc:
                assert "1, 2 or 3" in str(exc)
            else:
                raise AssertionError("un --phase 4 tiene que abortar")


class TestTheSuiteDoesNotWriteToTheCampaignLog:
    """The regression this file left behind, pinned so it cannot return.

    Any test calling a driver function that logs would write into the live log if
    ``_driver`` ever stopped neutralising ``log``.
    """

    def test_the_factory_neutralises_the_log(self):
        d = _driver()
        assert d.log("this must not reach any file") is None

    def test_running_a_phase_does_not_touch_the_file(self):
        d = _driver()
        log_path = pathlib.Path(d.LOG)
        before = log_path.stat().st_mtime_ns if log_path.exists() else None
        size = log_path.stat().st_size if log_path.exists() else None

        class _Api:
            def call(self, *a, **k):
                raise AssertionError("must not enqueue anything")

        with patch.object(d, "_sin_secuencia", lambda: 0):
            d.run_phase3(_Api())

        if before is not None:
            assert log_path.stat().st_size == size, "the test wrote into the live log"
            assert log_path.stat().st_mtime_ns == before


class TestTheGafIsKeptWhileTheDiskAllows:
    """Downloading the 802 GB series twice costs 23 of the 47 hours the whole run
    takes, measured at the real 9.6 MB/s. Both phases walk the series ascending, so
    the prefix phase 1 sees first is the one phase 2 asks for first.

    What must NOT happen is keeping files until the disk fills: Postgres lives on
    the same filesystem, so that is not a clean stop, it is a WAL PANIC in the
    campaign's own database.
    """

    def test_above_the_floor_the_file_is_kept(self):
        d = _driver()
        removed = []
        with (
            patch.object(d, "free_gb", lambda: d.DISK_FLOOR_GB_TO_KEEP + 1),
            patch.object(d.os, "remove", lambda p: removed.append(p)),
        ):
            d._drop_or_keep(156)
        assert removed == [], "it was kept, so phase 2 does not re-download it"

    def test_below_the_floor_the_file_goes(self):
        d = _driver()
        removed = []
        with (
            patch.object(d, "free_gb", lambda: d.DISK_FLOOR_GB_TO_KEEP - 1),
            patch.object(d.os, "remove", lambda p: removed.append(p)),
        ):
            d._drop_or_keep(156)
        assert len(removed) == 1
        assert removed[0].endswith("goa_uniprot_all.gaf.156.gz")

    def test_exactly_at_the_floor_the_file_goes(self):
        """The comparison is strict, so the floor is a floor and not a maybe."""
        d = _driver()
        removed = []
        with (
            patch.object(d, "free_gb", lambda: d.DISK_FLOOR_GB_TO_KEEP),
            patch.object(d.os, "remove", lambda p: removed.append(p)),
        ):
            d._drop_or_keep(156)
        assert len(removed) == 1

    def test_the_floor_leaves_room_for_the_database(self):
        """120 GB measured for the previous campaign's database over a corpus of
        comparable size, plus the largest single release at 24 GB. A floor under
        that would trade a download for a PANIC."""
        d = _driver()
        assert d.DISK_FLOOR_GB_TO_KEEP >= 120 + 24

    def test_a_missing_file_is_not_an_error(self):
        """A failed pass may have left nothing to remove, and that must not end the
        run."""
        d = _driver()

        def boom(_p):
            raise OSError("no such file")

        with (
            patch.object(d, "free_gb", lambda: 0),
            patch.object(d.os, "remove", boom),
        ):
            d._drop_or_keep(156)
