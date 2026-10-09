"""Command line interface for offline prompt contract validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, NoReturn

from . import engine


def _reject_constant(value: str) -> NoReturn:
    """Reject JavaScript-style non-finite numeric values accepted by json.loads."""
    raise ValueError(f"non-standard JSON constant {value!r}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object while rejecting ambiguous duplicate keys."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _load_manifest(path: Path) -> Any:
    raw = path.read_bytes()
    source = raw.decode("utf-8", errors="strict")
    return json.loads(
        source,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )


def _diagnostic_key(item: dict[str, Any]) -> tuple[str, str, str, int, str]:
    line = item.get("line")
    return (
        str(item.get("template_id", "")),
        str(item.get("path", "")),
        str(item.get("code", "")),
        line if isinstance(line, int) and not isinstance(line, bool) else -1,
        str(item.get("message", "")),
    )


def _summary(result: dict[str, Any]) -> dict[str, Any]:
    diagnostics = sorted(result["diagnostics"], key=_diagnostic_key)
    return {
        "template_count": result["template_count"],
        "valid_count": result["valid_count"],
        "diagnostics": [
            {
                "template_id": item["template_id"],
                "path": item["path"],
                "code": item["code"],
                "line": item["line"],
                "message": item["message"],
            }
            for item in diagnostics
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prompt-contract-check")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate a prompt pack manifest")
    validate.add_argument("manifest", type=Path, metavar="MANIFEST.json")
    validate.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    manifest_path = args.manifest
    try:
        manifest = _load_manifest(manifest_path)
    except json.JSONDecodeError as exc:
        # JSONDecodeError reports position only; it never includes source text.
        print(f"input error: invalid JSON at line {exc.lineno}, column {exc.colno}", file=sys.stderr)
        return 2
    except ValueError as exc:
        # Do not include duplicate keys or non-finite values from the source.
        detail = "invalid UTF-8" if isinstance(exc, UnicodeDecodeError) else "strict JSON violation"
        print(f"input error: {detail}", file=sys.stderr)
        return 2
    except OSError:
        print("input error: unable to read manifest", file=sys.stderr)
        return 2

    try:
        result = engine.validate(manifest, manifest_path.resolve().parent)
        summary = _summary(result)
    except engine.InputError as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    except Exception:
        # Avoid exposing exception text that could contain manifest or prompt data.
        print("validation error: unable to validate manifest", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
    else:
        print(f"Templates: {summary['template_count']}")
        print(f"Valid: {summary['valid_count']}")
        for item in summary["diagnostics"]:
            line = "" if item["line"] is None else f":{item['line']}"
            print(
                f"{item['template_id']} {item['path']}{line} "
                f"[{item['code']}] {item['message']}"
            )
    return 0 if not summary["diagnostics"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
