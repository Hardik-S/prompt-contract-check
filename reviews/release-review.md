# Independent release review

**Recommendation: BLOCK**

Reviewed commit `e688d922b057cb27953ce591df1f42ab7fadd3a7` (`Validate static prompt variable contracts`), matching local `HEAD` and `origin/main`, against the frozen goal packet and [issue #4](https://github.com/Hardik-S/prompt-contract-check/issues/4).

## Blocking finding

The implementation accepts absolute template paths when they resolve inside the manifest directory. The contract requires every path to be relative. Reproduction on Windows, using the fresh-installed CLI:

```json
{"version": 1, "templates": [{"id": "x", "path": "C:\\Users\\hshre\\AppData\\Local\\Temp\\pcc-absolute-repro-y5yw16n3\\safe.txt", "variables": ["name"]}]}
```

The manifest was `C:\Users\hshre\AppData\Local\Temp\pcc-absolute-repro-y5yw16n3\manifest.json`; `safe.txt` was beside it and contained `Hello {{name}}`. Command:

```powershell
prompt-contract-check validate C:\Users\hshre\AppData\Local\Temp\pcc-absolute-repro-y5yw16n3\manifest.json --format json
```

Result: exit 0, `template_count: 1`, `valid_count: 1`, and no diagnostics. The smallest repair is to reject absolute paths before resolution and add an absolute-in-root regression case.

## Checks completed

- Fresh install in a new virtual environment: `python -m pip install .` succeeded on Python 3.13.1; the wheel was built and installed.
- README quickstart against `examples/valid-pack/manifest.json --format json`: exit 0, 2/2 valid, no diagnostics.
- README invalid synthetic pack against `examples/invalid-pack/manifest.json --format json`: exit 2; reported undeclared placeholder and unused declaration without printing template contents.
- `python -m pip install -e ".[dev]"`: succeeded. `python -m pytest`: **20 passed**.
- Adversarial CLI checks: in-root absolute path was incorrectly accepted (blocker); directory, missing file, invalid UTF-8 template, and symlink escape were rejected with exit 2. Symlink escape produced `path_outside_base`.
- Strict JSON checks: duplicate object key, `Infinity`, `NaN`, and invalid UTF-8 manifest were rejected with exit 2. A diagnostic case containing prompt and variable sentinels did not echo either sentinel.
- Source review: exact integer version is enforced with `type(version) is int`; top-level/template keys and field types are exact; duplicate IDs, paths, and variable names are diagnosed; placeholder matching is limited to the specified ASCII identifier pattern; undeclared uses carry stable line numbers and unused declarations are detected. Diagnostics contain no template body or variable values. Runtime dependencies are empty and inspected implementation uses local parsing/filesystem checks only; no rendering, provider/network calls, evaluation, or code execution found. README and launch copy make no prompt-quality or novelty claim.
- CI run [37956760173](https://github.com/Hardik-S/prompt-contract-check/actions/runs/37956760173) is for this exact SHA and completed successfully. Ubuntu and Windows jobs each passed for Python 3.10 and 3.13, including install, tests, and installed CLI quickstart.

**Release gate:** keep blocked until absolute in-root paths are rejected and the focused regression test plus required checks pass on the repaired commit. No files other than this review were changed; no commit or push was made.
