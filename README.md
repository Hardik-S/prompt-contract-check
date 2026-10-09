# Prompt Contract Check

Prompt Contract Check statically checks that a small text-template pack declares every `{{identifier}}` placeholder exactly once and that every declared variable is used. It performs no rendering or model calls.

```console
python -m pip install -e ".[dev]"
prompt-contract-check validate examples/manifest.json --format text
```

Examples are synthetic. The validator checks file paths and placeholder contracts only; it does not assess prompt quality.
