# Microsoft Entra ID Migration Helper

[![CI](https://github.com/kinged007/ms-entra-app-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/kinged007/ms-entra-app-exporter/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](requirements.txt)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Export and sanitize Microsoft Entra ID app registrations and service principals for tenant-to-tenant migration. Built as consulting evidence for a tenant-migration engagement: connects via OAuth (MSAL), queries Microsoft Graph with `$search` / `$filter`, and writes redacted JSON ready for re-import.

Permissions required: `Application.Read.All` (application or delegated).

## Features

- **Tenant connections** — app or delegated (user) auth, certificate or client secret, stored as JSON in `tenants/`.
- **Export** — search/filter against Graph or select from CSV; optionally fetches associated service principals in batches.
- **Explorer** — interactive browser for any Graph endpoint with saved queries (`queries/`).
- **Sanitization** — redacts `appId` occurrences and validates output against Pydantic schemas for applications and service principals.
- **Proxy support** — reads `PROXY_ADDRESS` from `.env` or `--proxy` flag.

## Install

```bash
git clone https://github.com/kinged007/ms-entra-app-exporter.git
cd ms-entra-app-exporter

# option A: helper script (creates venv and installs)
sh run.sh          # Windows: run.bat

# option B: manual
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Requires Python 3.10+ and an app registration in Microsoft Entra.

1. Create an App Registration in Microsoft Entra.
2. Under **Authentication** → **Add a platform** → **Mobile and desktop applications** → enable **MSAL only** → **Configure** (for delegated/user auth). For app-only auth, add a certificate or secret under **Certificates & secrets**.
3. Grant **Application.Read.All** (application or delegated, matching your connection type) and grant admin consent.

Proxy (optional): create `.env` with `PROXY_ADDRESS="http://proxy:port"`.

## Usage

```bash
# via helper script (handles venv)
sh run.sh

# or directly
python app.py
python app.py --proxy http://proxy:port
```

Menu: **Manage Tenants** (create/edit/delete), **API Explorer** (browse Graph endpoints), **Export App Metadata** (search/filter → sanitize → review → save to `files/`), **Clean up**.

Saved tenants: `tenants/<name>.json`. Exports: `files/<clientId>_<type>_<timestamp>.json`. Never commit `tenants/`, `files/`, or `.env` — they are gitignored.

## How it is tested

```bash
pip install -r requirements.txt
pytest -v
ruff check tests/
mypy --ignore-missing-imports tests/
```

CI runs the same checks on every push and pull request to `master`.

## Project layout

```
app.py              # CLI entry + main menu
src/tenant.py       # tenant CRUD and token acquisition (MSAL)
src/apps.py         # Graph search/filter and batch fetch
src/explorer.py     # interactive Graph explorer
schema/             # Pydantic models for tenant, application, service principal
utils/              # Graph requests, sanitization/redaction, dict helpers
files/ tenants/ queries/  # gitignored runtime data
```

## Security notes

- Tokens are held in memory only (`access_token` is never written to `tenants/*.json`).
- Exports redact `appId` values to `__APPID_REDACTED__` via `utils/validate.py`.
- Do not commit `tenants/`, `files/`, `queries/`, or `.env`.
