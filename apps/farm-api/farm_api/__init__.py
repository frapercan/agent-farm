"""farm-api — FastAPI sidecar exposing read-only views over agent-farm state.

The package-level export is the FastAPI `app` instance so `uvicorn
farm_api:app` works without further configuration.
"""

from farm_api.app import create_app

# Module-level singleton constructed at import time so uvicorn's
# `farm_api:app` target resolves immediately. Tests prefer create_app()
# (which builds a fresh instance per fixture).
app = create_app()

__all__ = ["app", "create_app"]
