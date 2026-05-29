# Maintenance scripts

These files are operational helpers or legacy content-generation utilities. They are not request-time Flask application code.

## Active / useful

- `scripts/export_site_wording.py` — renders public pages through the Flask test client and exports visible copy to `articles/site_wording_export.md`.
- `scripts/refresh_rfp_opportunities.py` — refreshes cached RFP opportunities.
- `scripts/wrap_templates.py` — template migration/maintenance helper.

## Legacy / use with care

- `blog_generator.py` — legacy Groq-assisted article generator. It now reads `GROQ_API_KEY` from the environment and should not contain hardcoded secrets.
- `miniblogpost.py`, `miniblogpost1.py`, `miniblogpostredo.py` — older blog generation experiments.
- `code_copy.py` — local code export helper that writes into a generated `code_copy/` directory.
- `scrub_all.py`, `scrub_keys.py` — local scrub utilities for old generated exports.

If these legacy utilities are used again, run them in a clean branch and review generated files before committing.
