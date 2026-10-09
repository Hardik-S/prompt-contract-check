"""Offline validation of prompt-template manifests and placeholders."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_PLACEHOLDER = re.compile(r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}")
_MANIFEST_KEYS = {"version", "templates"}
_TEMPLATE_KEYS = {"id", "path", "variables"}


class InputError(ValueError):
    """Raised when a manifest does not have the required structural shape."""


def _require_shape(manifest: Any) -> list[Mapping[str, Any]]:
    if not isinstance(manifest, dict) or set(manifest) != _MANIFEST_KEYS:
        raise InputError("manifest must be an object with exactly version and templates")
    if type(manifest["version"]) is not int or manifest["version"] != 1:
        raise InputError("manifest version must be 1")
    entries = manifest["templates"]
    if not isinstance(entries, list):
        raise InputError("manifest templates must be a list")
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != _TEMPLATE_KEYS:
            raise InputError(f"template at index {index} must have exactly id, path, and variables")
        if not isinstance(entry["id"], str) or not isinstance(entry["path"], str):
            raise InputError(f"template at index {index} id and path must be strings")
        if not isinstance(entry["variables"], list) or any(
            not isinstance(variable, str) for variable in entry["variables"]
        ):
            raise InputError(f"template at index {index} variables must be a list of strings")
    return entries


def validate(manifest: Any, base_dir: str | Path) -> dict[str, Any]:
    """Validate manifest and template files without rendering or executing them."""
    entries = _require_shape(manifest)
    root = Path(base_dir).resolve()
    diagnostics: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    valid_count = 0

    def add(template_id: str, path: str, code: str, line: int | None, message: str) -> None:
        diagnostics.append({
            "template_id": template_id,
            "path": path,
            "code": code,
            "line": line,
            "message": message,
        })

    for entry in entries:
        template_id = entry["id"]
        relative_path = entry["path"]
        start = len(diagnostics)

        if not template_id:
            add(template_id, relative_path, "invalid_id", None, "template id must not be empty")
        elif template_id in seen_ids:
            add(template_id, relative_path, "duplicate_id", None, "template id is duplicated")
        else:
            seen_ids.add(template_id)

        if not relative_path:
            add(template_id, relative_path, "invalid_path", None, "template path must not be empty")
            target = None
        else:
            candidate = (root / relative_path).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                target = None
                add(template_id, relative_path, "path_outside_base", None,
                    "template path resolves outside the manifest directory")
            else:
                normalized = candidate.relative_to(root).as_posix()
                if normalized in seen_paths:
                    add(template_id, relative_path, "duplicate_path", None, "template path is duplicated")
                else:
                    seen_paths.add(normalized)
                target = candidate

        declared: set[str] = set()
        for variable in entry["variables"]:
            if not _IDENTIFIER.fullmatch(variable):
                add(template_id, relative_path, "invalid_variable", None,
                    "declared variable name is not a supported identifier")
            elif variable in declared:
                add(template_id, relative_path, "duplicate_variable", None,
                    "declared variable name is duplicated")
            else:
                declared.add(variable)

        body: str | None = None
        if target is not None:
            if not target.exists():
                add(template_id, relative_path, "missing_file", None, "template file does not exist")
            elif not target.is_file():
                add(template_id, relative_path, "not_file", None, "template path is not a file")
            else:
                try:
                    body = target.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    add(template_id, relative_path, "invalid_utf8", None,
                        "template file is not valid UTF-8")
                except OSError:
                    add(template_id, relative_path, "unreadable_file", None,
                        "template file could not be read")

        used: set[str] = set()
        if body is not None:
            for match in _PLACEHOLDER.finditer(body):
                name = match.group(1)
                used.add(name)
                line = body.count("\n", 0, match.start()) + 1
                if name not in declared:
                    add(template_id, relative_path, "undeclared_placeholder", line,
                        "placeholder has no matching variable declaration")
            for name in sorted(declared - used):
                add(template_id, relative_path, "unused_variable", None,
                    "declared variable is not used by the template")

        if len(diagnostics) == start:
            valid_count += 1

    return {
        "template_count": len(entries),
        "valid_count": valid_count,
        "diagnostics": diagnostics,
    }
