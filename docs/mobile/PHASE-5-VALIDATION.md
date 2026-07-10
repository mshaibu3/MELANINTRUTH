# Phase 5 Validation Plan

The pull request must pass:

1. `ci` for Python installation, linting, backend tests, and AI safety tests.
2. `api-integration` for PostgreSQL migrations, no-skip FastAPI tests, OpenAPI drift protection, and repository verification.
3. `mobile-ci` for dependency resolution, strict Dart formatting, Flutter analysis, all controller/widget/gateway tests, and coverage upload.

Canonical Dart formatting and the gateway-test analyzer repair have been committed. The Phase 5 branch is not accepted until all three workflows are green on the same owner-authored head commit.
