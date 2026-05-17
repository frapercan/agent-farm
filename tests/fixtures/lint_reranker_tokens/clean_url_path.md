# URL path carve-out fixture

This fixture contains URL versioning references that must NOT be flagged.

The canonical API prefix is /v1/jobs (T4.1, ADR-D4).
External clients POST to /v1/datasets and /v1/reranker-models/import.

Inside an inline code span: ``/v1/jobs`` resolves to the canonical
handler. Nested path segments such as /api/v1/jobs and
/api/v2/predictions are also covered by Q3.

Sphinx HTTP directive form:

.. http:get:: /v1/jobs

.. http:post:: /v1/datasets

A future major bump would mount under /v2/ alongside /v1/ for the
deprecation window.
