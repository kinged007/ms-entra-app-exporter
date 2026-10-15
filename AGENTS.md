# AGENTS.md

## Purpose

Microsoft Entra ID exporter for tenant-to-tenant migration. Connects to Microsoft Graph via MSAL (app or delegated auth), exports app registrations / service principals with `$search`/`$filter`, sanitizes exports (redacts `appId`), and writes JSON for re-import. Do not publish tenant-specific data, tokens, or customer identifiers.

## How to work in this repo

- Default branch: `master`.
- Do not push directly to `master`. Open a PR from a feature branch.
- Commit identity: `kinged007 <599286+kinged007@users.noreply.github.com>`.
- `.mailmap` is committed — do not reintroduce `you@example.com` authors.
- Never commit `tenants/`, `files/`, `queries/`, `*.pem`, `*.crt`, or `.env`; they are gitignored.
- Do not commit secrets (API keys, tokens, .env). Only `.env.example` belongs in the repo.

## Checks

```bash
pip install -r requirements.txt
pip install pytest ruff mypy
pytest -v
ruff check tests/
mypy --ignore-missing-imports --explicit-package-bases tests/
```

CI (`.github/workflows/ci.yml`) runs the same on push/PR to `master`. Keep it green.

## Skills

Use the repo's skills catalog where applicable; keep changes minimal and reversible. Prefer extending existing modules in `utils/`, `schema/`, and `src/` over duplicating logic.
