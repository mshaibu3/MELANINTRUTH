# API CI Runbook

This runbook is the required Phase 3.10 path for proving the dependency-enabled backend before starting Phase 4 mobile work.

## Current Phase 3.10 status

* Workflow: `.github/workflows/api-integration.yml` (`api-integration`).
* Local run status on 2026-07-09 UTC: **not executed in GitHub Actions from this container**.
* Reason: this container has no `gh` CLI, no configured git remote, package installation is blocked by a `403 Forbidden` tunnel error for `/simple/fastapi/`, and Docker is not installed.
* Phase 4 mobile status: **blocked** until the API integration workflow passes with FastAPI tests running without skips.

Do not mark the backend as dependency-enabled verified unless the workflow run has a successful GitHub Actions run ID or an equivalent Docker/PostgreSQL log bundle.

## GitHub Actions workflow proof

Run these commands from an authenticated workstation with repository access:

```bash
git checkout <branch>
git pull
gh workflow run api-integration.yml
gh run list --workflow api-integration.yml
gh run view <run-id> --log
```

Record all of the following in `docs/deployment/README.md`, `docs/ROADMAP.md`, and `docs/ACCEPTANCE-CRITERIA.md` after the run passes:

* workflow name
* run ID or URL
* run status
* UTC date/time of successful run
* commit SHA tested
* commands passed
* confirmation that FastAPI tests ran without skips under `REQUIRE_FASTAPI_TESTS=1`
* confirmation that Alembic migrations and migration verification passed against PostgreSQL
* confirmation that OpenAPI generation, `make openapi-check`, and `git diff --exit-code docs/api/openapi.json` passed
* confirmation that `make test-postgres-real` passed
* whether Phase 4 mobile is unlocked

## Commands the workflow must run

The workflow must use a PostgreSQL service and must run:

```bash
make api-install
make api-migrate
make migration-verify
REQUIRE_FASTAPI_TESTS=1 make api-test
make api-openapi
make openapi-check
git diff --exit-code docs/api/openapi.json
make test-postgres-real
```

`REQUIRE_FASTAPI_TESTS=1` is mandatory: missing FastAPI dependencies or unexpected FastAPI skips must fail the job.

## Local Docker fallback

If GitHub Actions cannot be triggered, run the same proof on a Docker-enabled machine:

```bash
make api-docker-build
make postgres-up
make api-migrate
make migration-verify
REQUIRE_FASTAPI_TESTS=1 make api-test
make api-openapi
make openapi-check
git diff --exit-code docs/api/openapi.json
make test-postgres-real
make postgres-down
```

If any command fails, fix the root cause and rerun the failed command. Do not bypass failures, weaken assertions, or convert required dependency-enabled tests into skips.

## Backend proof checklist

Phase 4 mobile remains blocked until all are true:

* `make api-install` passes in CI.
* `make api-migrate` passes against PostgreSQL.
* `make migration-verify` passes.
* `REQUIRE_FASTAPI_TESTS=1 make api-test` passes without FastAPI skips.
* `make api-openapi` passes.
* `make openapi-check` passes.
* `git diff --exit-code docs/api/openapi.json` passes.
* `make test-postgres-real` passes.
* Protected endpoints reject missing and invalid auth.
* Admin endpoints reject normal users.
* Consent-gated upload, cloud-consent analysis, privacy deletion, governance audit, render safety gate, and the exact scientific limitation wording are covered by passing tests.
