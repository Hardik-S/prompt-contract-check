# Prompt Contract Check

Prompt Contract Check catches a small class of prompt-pack mistakes before a prompt reaches an application: missing files, paths that escape the pack directory, duplicate IDs, undeclared `{{variables}}`, and declarations that templates never use.

It performs a static check only. It does not render prompts, call a provider, run evaluations, execute code, or assess prompt quality. Output reports file/line diagnostics without printing prompt bodies or variable values.

## Quickstart

Requires Python 3.10 or newer. Install the package into a fresh environment and validate the synthetic pack:

```console
python -m pip install .
prompt-contract-check validate examples/valid-pack/manifest.json --format text
```

The same command is available as `python -m prompt_contract_check`. For a JSON result, use `--format json`.

Try the deliberately broken synthetic pack:

```console
prompt-contract-check validate examples/invalid-pack/manifest.json --format json
```

It exits with status 2 and reports the undeclared `{{recipient}}` placeholder at its file and line. All examples use synthetic text.

## Manifest v1

The manifest contains exactly `version` and `templates`. Each entry contains exactly a unique `id`, a unique relative `path`, and a list of distinct variable identifiers. Template paths resolve relative to the manifest and must remain inside its directory. Files must be readable UTF-8 text.

Only `{{identifier}}` is recognized, where an identifier starts with an ASCII letter or underscore and continues with ASCII letters, digits, or underscores. Every recognized placeholder must be declared, and every declared variable must appear in that template. Other brace text is treated literally; this does not parse Jinja, Handlebars, or other template languages.

The JSON output contains `template_count`, `valid_count`, and deterministic `diagnostics` with `template_id`, `path`, `code`, `line`, and `message`. Valid packs exit 0; diagnosed contract failures exit 2. Input errors also exit 2 with a short message.

## Tests

```console
python -m pip install -e ".[dev]"
python -m pytest
```
