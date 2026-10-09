"""Acceptance coverage for the manifest and placeholder contract."""

import json
from pathlib import Path

import pytest

from prompt_contract_check.engine import InputError, validate

ROOT = Path(__file__).resolve().parents[1]


def write_manifest(tmp_path, templates, version=1):
    (tmp_path / "prompt.txt").write_text("Use {{known}}.", encoding="utf-8")
    return {"version": version, "templates": templates}


def test_example_pack_is_valid():
    manifest = json.loads((ROOT / "examples/valid-pack/manifest.json").read_text(encoding="utf-8"))
    result = validate(manifest, ROOT / "examples/valid-pack")
    assert result["template_count"] == 2
    assert result["valid_count"] == 2
    assert result["diagnostics"] == []


@pytest.mark.parametrize(
    "prompt,variables,expected_code",
    [
        ("First line.\nUnknown {{missing}}.", ["known"], "undeclared_placeholder"),
        ("Unused declaration {{known}}.", ["known", "unused"], "unused_variable"),
        ("Only {{known}} is a placeholder; {{not-valid}} is literal.", ["known"], None),
    ],
)
def test_placeholder_contract_reports_unknown_and_unused(tmp_path, prompt, variables, expected_code):
    (tmp_path / "prompt.txt").write_text(prompt, encoding="utf-8")
    manifest = {"version": 1, "templates": [{"id": "one", "path": "prompt.txt", "variables": variables}]}
    result = validate(manifest, tmp_path)
    if expected_code is None:
        assert result["diagnostics"] == []
    else:
        assert any(d["code"] == expected_code for d in result["diagnostics"])
        if expected_code == "undeclared_placeholder":
            assert any(d["line"] == 2 for d in result["diagnostics"])


def test_duplicate_ids_paths_and_variable_declarations_are_diagnosed(tmp_path):
    (tmp_path / "prompt.txt").write_text("Use {{known}}.", encoding="utf-8")
    manifest = {"version": 1, "templates": [
        {"id": "same", "path": "prompt.txt", "variables": ["known", "known"]},
        {"id": "same", "path": "prompt.txt", "variables": ["known"]},
    ]}
    result = validate(manifest, tmp_path)
    codes = " ".join(d["code"].lower() for d in result["diagnostics"])
    assert "id" in codes and "path" in codes and ("variable" in codes or "declar" in codes)


@pytest.mark.parametrize("path", ["../outside.txt", "missing.txt"])
def test_unsafe_or_missing_paths_are_diagnosed(tmp_path, path):
    result = validate({"version": 1, "templates": [{"id": "x", "path": path, "variables": []}]}, tmp_path)
    assert result["valid_count"] == 0
    assert result["diagnostics"]


def test_invalid_utf8_is_diagnosed(tmp_path):
    (tmp_path / "bad.txt").write_bytes(b"hello \xff")
    result = validate({"version": 1, "templates": [{"id": "x", "path": "bad.txt", "variables": []}]}, tmp_path)
    assert result["valid_count"] == 0
    assert result["diagnostics"]


@pytest.mark.parametrize("manifest", [
    None, [], {}, {"version": "1", "templates": []},
    {"version": True, "templates": []}, {"version": 1.0, "templates": []},
    {"version": 1, "templates": [None]},
    {"version": 1, "templates": [{"id": 1, "path": "prompt.txt", "variables": []}]},
])
def test_malformed_manifest_shapes_raise_input_error(tmp_path, manifest):
    with pytest.raises(InputError):
        validate(manifest, tmp_path)


def test_diagnostic_order_and_line_numbers_are_stable(tmp_path):
    (tmp_path / "prompt.txt").write_text("{{first}}\n{{second}}\n{{first}}", encoding="utf-8")
    manifest = {"version": 1, "templates": [{"id": "x", "path": "prompt.txt", "variables": []}]}
    first = validate(manifest, tmp_path)
    second = validate(manifest, tmp_path)
    assert first == second
    assert [d["line"] for d in first["diagnostics"]] == [1, 2, 3]
