# URXION Website

Flask website and public demo flows for URXION.

## Python version

This repo is validated on **Python 3.10**. Use the checked-in `.python-version` with pyenv/asdf, or create a 3.10 virtual environment manually.

```bash
python3.10 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install ".[dev]"
```

## Project metadata

Runtime and development dependencies live in `pyproject.toml`. `requirements.txt` is kept as a pinned compatibility export for simple hosts that still install from requirements files.

## Run tests

```bash
.venv/bin/python -m compileall -q flask_app.py agent_resources.py blog_generator.py rfp_opportunity_cache.py scripts tests
.venv/bin/python -m pytest
```

Current expected baseline:

```text
128 passed
```

## Run locally

```bash
.venv/bin/python flask_app.py
```

## Site wording export

To export visible rendered page copy into `articles/site_wording_export.md`:

```bash
.venv/bin/python scripts/export_site_wording.py
```

The exporter excludes script/style/svg content and is useful for reviewing marketing copy, SEO text, and active public page wording.

## Maintenance scripts

Older one-off helper scripts are documented in `docs/maintenance-scripts.md`. Treat them as maintenance utilities, not request-time application code.
