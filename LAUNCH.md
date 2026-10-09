# Prompt Contract Check v0.1.0 launch note

**Problem:** prompt files and their declared variables drift over time. An undeclared placeholder may reach runtime, while a stale declaration can hide a missing input.

**Reproduce:** in a fresh Python 3.10+ environment, install the package and check the passing synthetic pack:

```console
python -m pip install .
prompt-contract-check validate examples/valid-pack/manifest.json --format json
```

Then validate `examples/invalid-pack/manifest.json`; it exits 2 and identifies the undeclared `recipient` placeholder in `welcome.txt` without printing the prompt body.

**Scope:** the tool checks manifest shape, unique IDs/paths, path containment, UTF-8 files, and exact `{{identifier}}` declaration/use parity. Results include deterministic file/line diagnostics.

**Limits:** examples are synthetic. This does not render templates, call models, run evaluations, inspect prompt quality, or parse Jinja/Handlebars syntax. It makes no novelty claim.
