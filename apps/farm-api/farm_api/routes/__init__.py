"""Route modules for farm-api. Each module exposes an APIRouter named
`router` that app.py mounts. Splitting by domain keeps the OpenAPI tags
clean and lets test files import a single router for narrow coverage.
"""
