"""Run the farm-api service via `python -m farm_api`.

Defaults to port 8801 unless `FARM_API_PORT` overrides. Host is
127.0.0.1 by default; set `FARM_API_HOST=0.0.0.0` if the operator wants
to expose the sidecar through the existing PROTEA ngrok tunnel.
"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.environ.get("FARM_API_HOST", "127.0.0.1")
    port = int(os.environ.get("FARM_API_PORT", "8801"))
    uvicorn.run("farm_api:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
