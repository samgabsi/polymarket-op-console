# Startup and Install Hardening — v2.3.0-real

## Minimal local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open `/v2-live` after launch.

## Smoke checks

```bash
python scripts/check_versions.py
python scripts/smoke_startup.py
python scripts/check_release_package.py .
```

These scripts do not require secrets and do not place or cancel orders.

## Port conflicts

Set `PORT` or `APP_PORT` to a free port if 8000 is occupied:

```bash
APP_PORT=8010 python run.py
```

## Optional live dependencies

Install `requirements-live-optional.txt` only when intentionally preparing read-only/live integration. Live submit remains gated by environment, risk, approval, confirmation, read-only state, and kill switch.
