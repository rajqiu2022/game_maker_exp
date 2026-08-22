#!/usr/bin/env python3
"""Validate every generic reusable resource pack and the unchanged legacy pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

try:
    from tools.build_resource_pack import discover_pack_ids, sha256
except ModuleNotFoundError:  # Direct script execution adds tools/ rather than the repository root.
    from build_resource_pack import discover_pack_ids, sha256


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = {
    "source",
    "reference",
    "references",
    "raw",
    "private",
    "cache",
    "candidate",
    "candidates",
    "build",
    "exports",
    ".godot",
    "__pycache__",
}
FORBIDDEN_SUFFIXES = {".import", ".pyc", ".pck", ".apk", ".exe"}
SENSITIVE_PATTERNS = (
    re.compile(r"[A-Za-z]:\\(?:Users|Code)\\", re.IGNORECASE),
    re.compile(r"\b(?:sk|ghp)_[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?:api[_-]?key|access[_-]?token)\s*[:=]", re.IGNORECASE),
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _validate_sensitive_and_forbidden(pack: Path, errors: list[str]) -> None:
    for path in sorted(pack.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(pack)
        if FORBIDDEN_PARTS.intersection(part.casefold() for part in relative.parts) or any(
            path.name.casefold().endswith(suffix) for suffix in FORBIDDEN_SUFFIXES
        ):
            _fail(errors, f"forbidden file in pack: {relative.as_posix()}")
        if path.suffix.casefold() not in {".md", ".json", ""}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(text) for pattern in SENSITIVE_PATTERNS):
            _fail(errors, f"sensitive or machine-local text: {relative.as_posix()}")


def validate_pack(repository_root: Path, pack_id: str) -> list[str]:
    errors: list[str] = []
    pack = repository_root / "resource-packs" / pack_id
    for required in ("README.md", "LICENSE-ASSETS.md", "pack-spec.json", "manifest.json", "CATALOG.md", "SHA256SUMS"):
        if not (pack / required).is_file():
            _fail(errors, f"missing required pack file: {required}")
    if errors:
        return errors
    try:
        spec = json.loads((pack / "pack-spec.json").read_text(encoding="utf-8"))
        manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"cannot parse pack JSON: {exc}"]
    if manifest.get("pack_id") != pack_id or spec.get("pack_id") != pack_id:
        _fail(errors, "pack identity mismatch")
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        return errors + ["manifest entries must be an array"]
    ids: set[str] = set()
    paths: set[str] = set()
    previews: set[str] = set()
    hashes: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        entry_id = str(entry.get("asset_id", ""))
        relative = str(entry.get("path", ""))
        if entry_id in ids:
            _fail(errors, f"duplicate asset ID: {entry_id}")
        if relative in paths:
            _fail(errors, f"duplicate manifest path: {relative}")
        ids.add(entry_id)
        paths.add(relative)
        path = pack / relative
        if not path.is_file():
            _fail(errors, f"missing published file: {relative}")
            continue
        actual_hash = sha256(path)
        if actual_hash != entry.get("sha256"):
            _fail(errors, f"SHA-256 mismatch: {entry_id}")
        hashes[actual_hash].append(entry_id)
        try:
            with Image.open(path) as image:
                image.load()
                if list(image.size) != [entry.get("width"), entry.get("height")]:
                    _fail(errors, f"dimension mismatch: {entry_id}")
                if image.mode != entry.get("color_mode"):
                    _fail(errors, f"color mode mismatch: {entry_id}")
                pixel_hash = hashlib.sha256(image.convert("RGBA").tobytes()).hexdigest()
                if pixel_hash != entry.get("pixel_sha256_rgba"):
                    _fail(errors, f"pixel hash mismatch: {entry_id}")
        except Exception as exc:
            _fail(errors, f"cannot decode {relative}: {exc}")
        if not isinstance(entry.get("provenance"), dict) or not entry["provenance"].get("kind"):
            _fail(errors, f"missing provenance: {entry_id}")
        if entry.get("rights") != "see LICENSE-ASSETS.md":
            _fail(errors, f"missing pack rights reference: {entry_id}")
        preview = entry.get("preview_path")
        if preview:
            previews.add(str(preview))
            if not (pack / str(preview)).is_file():
                _fail(errors, f"missing preview: {entry_id}")
        if entry.get("kind") == "ui_component":
            margins = entry.get("content_safe_margin")
            stretch = entry.get("stretch_mode")
            if not isinstance(margins, list) or len(margins) != 4 or stretch not in {"none", "scale", "tile", "nine_patch"}:
                _fail(errors, f"invalid UI layout metadata: {entry_id}")
            interactive = entry.get("interactive")
            touch = entry.get("recommended_touch_target")
            if not isinstance(interactive, bool):
                _fail(errors, f"missing UI interactive contract: {entry_id}")
            elif interactive and (not isinstance(touch, list) or len(touch) != 2 or min(touch) <= 0):
                _fail(errors, f"invalid UI touch target: {entry_id}")
            elif interactive and "mobile" in entry.get("platforms", []) and min(touch) < 72:
                _fail(errors, f"mobile UI touch target below 72x72: {entry_id}")
    for digest, duplicate_ids in hashes.items():
        if len(duplicate_ids) > 1:
            _fail(errors, f"duplicate physical content {digest[:12]}: {', '.join(duplicate_ids)}")
    published_png = {path.relative_to(pack).as_posix() for path in pack.rglob("*.png")}
    published_webp = {path.relative_to(pack).as_posix() for path in pack.rglob("*.webp")}
    orphan_png = sorted(published_png - paths)
    orphan_webp = sorted(published_webp - previews)
    if orphan_png:
        _fail(errors, f"orphan PNG files: {', '.join(orphan_png)}")
    if orphan_webp:
        _fail(errors, f"orphan WebP files: {', '.join(orphan_webp)}")
    expected_checksums = [
        f"{sha256(path)}  {path.relative_to(pack).as_posix()}"
        for path in sorted(pack.rglob("*.png")) + sorted(pack.rglob("*.webp"))
    ]
    actual_checksums = (pack / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    if expected_checksums != actual_checksums:
        _fail(errors, "SHA256SUMS does not match published binaries")
    _validate_sensitive_and_forbidden(pack, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack")
    args = parser.parse_args()
    pack_ids = [args.pack] if args.pack else discover_pack_ids(ROOT)
    errors: list[str] = []
    for pack_id in pack_ids:
        pack_errors = validate_pack(ROOT, pack_id)
        errors.extend(f"{pack_id}: {message}" for message in pack_errors)
    if not args.pack:
        legacy = subprocess.run([sys.executable, str(ROOT / "tools" / "validate_resource_pack.py")], cwd=ROOT, check=False)
        if legacy.returncode:
            errors.append("legacy wuxia pack validation failed")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Validated reusable resource packs: {len(pack_ids)} generic pack(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
