"""CLI acceptance checks, including strict JSON parsing and exit status."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cli(tmp_path, manifest_text, *args):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(manifest_text, encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "prompt_contract_check", "validate", str(manifest), *args],
        cwd=ROOT, env=env, text=True, capture_output=True, check=False,
    )


def test_cli_valid_and_invalid_exit_codes_and_json_output(tmp_path):
    (tmp_path / "prompt.txt").write_text("Use {{name}}.", encoding="utf-8")
    good = run_cli(tmp_path, '{"version":1,"templates":[{"id":"g","path":"prompt.txt","variables":["name"]}]}', "--format", "json")
    assert good.returncode == 0
    assert json.loads(good.stdout)["valid_count"] == 1
    bad = run_cli(tmp_path, '{"version":1,"templates":[{"id":"b","path":"prompt.txt","variables":[]}]}', "--format", "json")
    assert bad.returncode == 2
    assert json.loads(bad.stdout)["diagnostics"]


def test_cli_rejects_duplicate_json_keys_and_nonfinite_constants(tmp_path):
    duplicate = run_cli(tmp_path, '{"version":1,"version":1,"templates":[]}')
    nonfinite = run_cli(tmp_path, '{"version":NaN,"templates":[]}')
    assert duplicate.returncode == 2 and "input error" in duplicate.stderr.lower()
    assert nonfinite.returncode == 2 and "input error" in nonfinite.stderr.lower()


def test_cli_json_output_is_repeatable(tmp_path):
    (tmp_path / "prompt.txt").write_text("{{missing}} on line one.\n{{other}} on line two.", encoding="utf-8")
    text = '{"version":1,"templates":[{"id":"x","path":"prompt.txt","variables":[]}]}'
    first = run_cli(tmp_path, text, "--format", "json")
    second = run_cli(tmp_path, text, "--format", "json")
    assert first.returncode == second.returncode == 2
    assert first.stdout == second.stdout
    payload = json.loads(first.stdout)
    assert [item["line"] for item in payload["diagnostics"]] == [1, 2]
