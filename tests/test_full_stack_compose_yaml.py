"""Tests for infra/compose/docker-compose.full-stack.yml.

Validates structural invariants of the full-stack compose file without
running any containers:

  - Every service declares a ``healthcheck`` block.
  - All expected named volumes exist in the top-level ``volumes`` map.
  - Profile split is correct: infra services carry only the ``infra``
    profile, monitoring services carry only the ``monitoring`` profile,
    and no monitoring service accidentally ends up in the default profile
    (i.e., without any profile).
  - At least one service exists in each of the two profiles.

Skips gracefully when PyYAML is not importable so the test suite can run
in minimal environments (the CI image always has it; this guard is for
local tox -e lint-only runs).
"""

from __future__ import annotations

from pathlib import Path

import pytest

COMPOSE_FILE = (
    Path(__file__).parent.parent / "infra" / "compose" / "docker-compose.full-stack.yml"
)

# ---------------------------------------------------------------------------
# Skip entire module when pyyaml is absent
# ---------------------------------------------------------------------------

try:
    import yaml  # noqa: F401
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _YAML_AVAILABLE,
    reason="pyyaml not importable — install it to run compose-structure tests",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def compose() -> dict:
    """Load and parse the full-stack compose YAML once per test session."""
    import yaml  # local import: guaranteed available because of skipif guard above

    assert COMPOSE_FILE.exists(), (
        f"Compose file not found at {COMPOSE_FILE}. "
        "Run from the repository root or check the path."
    )
    raw = COMPOSE_FILE.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    assert isinstance(data, dict), "Compose YAML must parse to a mapping."
    return data


@pytest.fixture(scope="module")
def services(compose: dict) -> dict:
    assert "services" in compose, "Compose file must have a top-level 'services' key."
    svcs = compose["services"]
    assert isinstance(svcs, dict) and svcs, "services map must be non-empty."
    return svcs


@pytest.fixture(scope="module")
def volumes(compose: dict) -> dict:
    assert "volumes" in compose, "Compose file must have a top-level 'volumes' key."
    vols = compose["volumes"]
    assert isinstance(vols, dict) and vols, "volumes map must be non-empty."
    return vols


# ---------------------------------------------------------------------------
# Healthcheck assertions
# ---------------------------------------------------------------------------


class TestHealthchecks:
    """Every service must declare a healthcheck block."""

    def test_all_services_have_healthcheck(self, services: dict) -> None:
        missing = [name for name, cfg in services.items() if "healthcheck" not in (cfg or {})]
        assert not missing, (
            f"The following services are missing a 'healthcheck': {missing}. "
            "Add a healthcheck so that dependent services can use "
            "condition: service_healthy."
        )

    def test_healthcheck_has_test_key(self, services: dict) -> None:
        bad = [
            name
            for name, cfg in services.items()
            if "healthcheck" in (cfg or {}) and "test" not in (cfg["healthcheck"] or {})
        ]
        assert not bad, (
            f"Services with healthcheck missing 'test' key: {bad}"
        )


# ---------------------------------------------------------------------------
# Volume assertions
# ---------------------------------------------------------------------------

EXPECTED_VOLUMES = {
    "protea_postgres_data",
    "protea_minio_data",
    "protea_grafana_data",
    "protea_prometheus_data",
    "protea_loki_data",
}


class TestVolumes:
    """Named volumes must cover all expected persistence paths."""

    def test_expected_volumes_present(self, volumes: dict) -> None:
        declared = set(volumes.keys())
        missing = EXPECTED_VOLUMES - declared
        assert not missing, (
            f"Expected named volumes not declared: {missing}. "
            "Add them to the top-level 'volumes' map."
        )

    def test_no_external_volumes(self, volumes: dict) -> None:
        """All volumes should be managed by this compose project, not external."""
        external = [
            name
            for name, cfg in volumes.items()
            if isinstance(cfg, dict) and cfg.get("external") is True
        ]
        assert not external, (
            f"Volumes declared as external (should be managed here): {external}"
        )


# ---------------------------------------------------------------------------
# Profile assertions
# ---------------------------------------------------------------------------

INFRA_SERVICES = {"postgres", "rabbitmq", "minio"}
MONITORING_SERVICES = {"prometheus", "grafana", "loki", "promtail", "postgres-exporter"}


class TestProfiles:
    """Profile split must be clean: every service belongs to exactly one profile."""

    def _get_profiles(self, service_cfg: dict | None) -> list[str]:
        if not service_cfg:
            return []
        return list(service_cfg.get("profiles") or [])

    def test_infra_services_have_infra_profile(self, services: dict) -> None:
        for svc in INFRA_SERVICES:
            assert svc in services, f"Expected infra service '{svc}' not found in compose."
            profiles = self._get_profiles(services[svc])
            assert "infra" in profiles, (
                f"Service '{svc}' must carry the 'infra' profile; got: {profiles}"
            )

    def test_monitoring_services_have_monitoring_profile(self, services: dict) -> None:
        for svc in MONITORING_SERVICES:
            assert svc in services, (
                f"Expected monitoring service '{svc}' not found in compose."
            )
            profiles = self._get_profiles(services[svc])
            assert "monitoring" in profiles, (
                f"Service '{svc}' must carry the 'monitoring' profile; got: {profiles}"
            )

    def test_no_service_in_default_profile(self, services: dict) -> None:
        """No service should appear in the default profile (i.e., without any profile).

        All services here are infrastructure or observability helpers; the app
        process stack is intentionally external. A service with no 'profiles'
        key would start on every plain `docker compose up`, which is wrong.
        """
        in_default = [
            name
            for name, cfg in services.items()
            if not self._get_profiles(cfg)
        ]
        assert not in_default, (
            f"Services with no profile (would start in default profile): {in_default}. "
            "Every service must declare either 'infra' or 'monitoring'."
        )

    def test_infra_services_not_in_monitoring_profile(self, services: dict) -> None:
        for svc in INFRA_SERVICES:
            if svc not in services:
                continue
            profiles = self._get_profiles(services[svc])
            assert "monitoring" not in profiles, (
                f"Infra service '{svc}' must not carry the 'monitoring' profile."
            )

    def test_monitoring_services_not_in_infra_profile(self, services: dict) -> None:
        for svc in MONITORING_SERVICES:
            if svc not in services:
                continue
            profiles = self._get_profiles(services[svc])
            assert "infra" not in profiles, (
                f"Monitoring service '{svc}' must not carry the 'infra' profile. "
                "Exception: postgres-exporter joins both networks, but still "
                "belongs only to the 'monitoring' profile."
            )

    def test_both_profiles_have_at_least_one_service(self, services: dict) -> None:
        infra_count = sum(
            1 for cfg in services.values()
            if "infra" in self._get_profiles(cfg)
        )
        monitoring_count = sum(
            1 for cfg in services.values()
            if "monitoring" in self._get_profiles(cfg)
        )
        assert infra_count >= 1, "The 'infra' profile must contain at least one service."
        assert monitoring_count >= 1, (
            "The 'monitoring' profile must contain at least one service."
        )


# ---------------------------------------------------------------------------
# Sanity: compose file is parse-valid and non-trivial
# ---------------------------------------------------------------------------


class TestSanity:
    """Basic sanity checks on the parsed compose structure."""

    def test_compose_has_name(self, compose: dict) -> None:
        assert "name" in compose, (
            "Compose file should declare a 'name' to ensure predictable "
            "container and volume names."
        )

    def test_compose_name_value(self, compose: dict) -> None:
        assert compose.get("name") == "protea-full-stack", (
            f"Compose name should be 'protea-full-stack', got '{compose.get('name')}'."
        )

    def test_total_service_count(self, services: dict) -> None:
        expected_total = len(INFRA_SERVICES) + len(MONITORING_SERVICES)
        actual = len(services)
        assert actual == expected_total, (
            f"Expected {expected_total} services "
            f"({len(INFRA_SERVICES)} infra + {len(MONITORING_SERVICES)} monitoring), "
            f"got {actual}: {list(services.keys())}"
        )
