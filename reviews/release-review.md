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

## Follow-up review for issue #6

**Recommendation: PASS for the bounded absolute/rooted/drive-qualified path repair.** The original issue #4 BLOCK report and reproduction above are retained unchanged as historical review evidence. This follow-up verifies that the identified defect is fixed on commit `803544a25ef553db8174904d3398dbdf16dd1a25` (`Reject absolute prompt template paths`), which matched `HEAD` and `origin/main` during review.

### Checks completed

- Fresh environment: `python --version` reported Python 3.13.1. `python -m venv C:\Users\hshre\AppData\Local\Temp\pcc-review-31aedd9ca703495a8185a24a6988ce3b\venv`; `C:\Users\hshre\AppData\Local\Temp\pcc-review-31aedd9ca703495a8185a24a6988ce3b\venv\Scripts\python.exe -m pip install .` built and installed `prompt-contract-check 0.1.0`; `C:\Users\hshre\AppData\Local\Temp\pcc-review-31aedd9ca703495a8185a24a6988ce3b\venv\Scripts\python.exe -m pip install 'pytest>=8,<9'` installed pytest 8.4.2.
- Full tests: `C:\Users\hshre\AppData\Local\Temp\pcc-review-31aedd9ca703495a8185a24a6988ce3b\venv\Scripts\python.exe -m pytest` — **21 passed**.
- README valid quickstart: `C:\Users\hshre\AppData\Local\Temp\pcc-review-31aedd9ca703495a8185a24a6988ce3b\venv\Scripts\prompt-contract-check.exe validate examples/valid-pack/manifest.json --format text` — exit 0, 2 templates valid.
- README invalid example: `C:\Users\hshre\AppData\Local\Temp\pcc-review-31aedd9ca703495a8185a24a6988ce3b\venv\Scripts\prompt-contract-check.exe validate examples/invalid-pack/manifest.json --format json` — exit 2, undeclared and unused variable diagnostics; no prompt body printed.
- Absolute existing in-root file: `C:\Users\hshre\AppData\Local\Temp\pcc-review-31aedd9ca703495a8185a24a6988ce3b\venv\Scripts\prompt-contract-check.exe validate <temp>\manifest.json --format json`, with manifest path set to the existing `C:\Users\hshre\AppData\Local\Temp\pcc-review-31aedd9ca703495a8185a24a6988ce3b\safe.txt` — exit 2, `absolute_path`.
- Rooted existing in-root file: same command with `path` set to `\Users\hshre\AppData\Local\Temp\pcc-review-31aedd9ca703495a8185a24a6988ce3b\safe.txt` — confirmed the target exists on the current drive; exit 2, `absolute_path`. POSIX-rooted spelling of the same existing file also exited 2 with `absolute_path`.
- Drive-qualified `C:safe.txt` — exit 2, `absolute_path`.
- Additional adversarial cases: `../outside.txt` exited 2 with `path_outside_base`; a symlink `escape.txt` to a file outside the manifest directory exited 2 with `path_outside_base`.
- Valid relative `safe.txt` pointing to the existing in-root file — exit 0, 1/1 valid.
- GitHub Actions run [37957328376](https://github.com/Hardik-S/prompt-contract-check/actions/runs/37957328376) — completed successfully on exact SHA `803544a25ef553db8174904d3398dbdf16dd1a25`; all four Ubuntu/Windows × Python 3.10/3.13 jobs passed install, tests, and installed CLI quickstart.

### Finding and release review

The validator now detects `Path.is_absolute()`, `PureWindowsPath.is_absolute()`, Windows drive, and Windows root before joining or resolving the supplied path. The regression test covers an absolute path to an existing in-root file. The independent checks confirm absolute, rooted, and drive-qualified paths are rejected before target-file validation, while relative in-root paths remain accepted and traversal/symlink containment remains enforced. No blocker found for the bounded repair. **Issue #4's original BLOCK record remains above, unchanged; this follow-up verifies its path-specific repair.**

No files outside `reviews/release-review.md` were edited. No commit or push was made.
