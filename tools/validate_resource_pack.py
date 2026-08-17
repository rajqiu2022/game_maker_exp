#!/usr/bin/env python3
"""Validate the published reusable icon/VFX pack."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - installation failure path
    raise SystemExit("Pillow is required: python -m pip install -r requirements-art.txt") from exc


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "resource-packs" / "ink-wuxia-icons-vfx-v1"
MANIFEST = PACK / "manifest.json"
NAME_RE = re.compile(r"^[a-z0-9_]+$")
FORBIDDEN_NAME_PARTS = {"copy", "final", "new", "test", "tmp", "candidate", "rejected"}
SENSITIVE_PATTERNS = (
    re.compile(r"[A-Za-z]:\\(?:Users|Code)\\", re.IGNORECASE),
    re.compile(r"\b(?:sk|ghp)_[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?:api[_-]?key|access[_-]?token)\s*[:=]", re.IGNORECASE),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_image_contract(entry: dict[str, object], path: Path, errors: list[str]) -> None:
    try:
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            mode = image.mode
            rgba = image.convert("RGBA")
    except Exception as exc:  # Pillow gives format-specific exceptions
        fail(errors, f"cannot decode {path.relative_to(ROOT)}: {exc}")
        return
    if [width, height] != [int(entry["width"]), int(entry["height"])]:
        fail(errors, f"dimension mismatch for {entry['asset_id']}: {width}x{height}")
    if mode != entry["color_mode"]:
        fail(errors, f"color mode mismatch for {entry['asset_id']}: {mode}")
    alpha = rgba.getchannel("A")
    pixel_sha = hashlib.sha256(rgba.tobytes()).hexdigest()
    if pixel_sha != entry.get("pixel_sha256_rgba"):
        fail(errors, f"normalized RGBA pixel hash mismatch: {entry['asset_id']}")
    alpha_min, alpha_max = alpha.getextrema()
    if alpha_min != 0 or alpha_max == 0:
        fail(errors, f"transparent asset lacks useful alpha range: {entry['asset_id']}")
    kind = str(entry["kind"])
    if kind.endswith("icon"):
        if (width, height, mode) != (256, 256, "RGBA"):
            fail(errors, f"icon must be 256x256 RGBA: {entry['asset_id']}")
    elif kind == "vfx_sheet":
        if width != height or width % 2 or height % 2 or width not in {768, 1024, 1254}:
            fail(errors, f"VFX sheet violates 2x2 size contract: {entry['asset_id']} {width}x{height}")
        cell_width, cell_height = width // 2, height // 2
        for frame in range(4):
            x = (frame % 2) * cell_width
            y = (frame // 2) * cell_height
            cell_alpha = alpha.crop((x, y, x + cell_width, y + cell_height))
            if cell_alpha.getbbox() is None:
                fail(errors, f"empty VFX frame {frame + 1}: {entry['asset_id']}")
        key_residue = 0
        pixel_bytes = rgba.tobytes()
        for offset in range(0, len(pixel_bytes), 4):
            red, green, blue, pixel_alpha = pixel_bytes[offset : offset + 4]
            if pixel_alpha > 8 and red >= 253 and green <= 2 and blue >= 253:
                key_residue += 1
        if key_residue > 8:
            fail(errors, f"possible #FF00FF key residue ({key_residue} pixels): {entry['asset_id']}")


def validate_sensitive_text(errors: list[str]) -> None:
    for path in sorted(PACK.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".json", ""}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(text):
                fail(errors, f"sensitive or machine-local text in {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    if not MANIFEST.is_file():
        print(f"ERROR: missing {MANIFEST.relative_to(ROOT)}")
        return 1
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        print("ERROR: manifest entries must be an array")
        return 1
    ids: set[str] = set()
    paths: set[str] = set()
    preview_paths: set[str] = set()
    hashes: dict[str, list[str]] = defaultdict(list)
    counts = defaultdict(int)
    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            fail(errors, "manifest entry is not an object")
            continue
        entry = raw_entry
        entry_id = str(entry.get("asset_id", ""))
        relative = str(entry.get("path", ""))
        if not NAME_RE.fullmatch(entry_id):
            fail(errors, f"unstable asset ID: {entry_id}")
        if set(entry_id.split("_")) & FORBIDDEN_NAME_PARTS:
            fail(errors, f"forbidden lifecycle word in asset ID: {entry_id}")
        if entry_id in ids:
            fail(errors, f"duplicate asset ID: {entry_id}")
        ids.add(entry_id)
        if relative in paths:
            fail(errors, f"duplicate manifest path: {relative}")
        paths.add(relative)
        path = PACK / relative
        if not path.is_file():
            fail(errors, f"missing published file: {relative}")
            continue
        actual_hash = sha256(path)
        if actual_hash != entry.get("sha256"):
            fail(errors, f"SHA-256 mismatch: {entry_id}")
        hashes[actual_hash].append(entry_id)
        if path.stat().st_size >= 50 * 1024 * 1024:
            fail(errors, f"file is too large for the direct-Git pack: {relative}")
        validate_image_contract(entry, path, errors)
        counts[str(entry.get("kind", "unknown"))] += 1
        if entry.get("kind") == "vfx_sheet":
            preview = str(entry.get("preview_path", ""))
            preview_paths.add(preview)
            if not preview or not (PACK / preview).is_file():
                fail(errors, f"missing VFX preview: {entry_id}")
    for digest, duplicate_ids in hashes.items():
        if len(duplicate_ids) > 1:
            fail(errors, f"duplicate physical content {digest[:12]}: {', '.join(duplicate_ids)}")
    published_png = {path.relative_to(PACK).as_posix() for path in PACK.rglob("*.png")}
    published_webp = {path.relative_to(PACK).as_posix() for path in PACK.rglob("*.webp")}
    orphan_png = sorted(published_png - paths)
    orphan_webp = sorted(published_webp - preview_paths)
    if orphan_png:
        fail(errors, f"orphan PNG files: {', '.join(orphan_png)}")
    if orphan_webp:
        fail(errors, f"orphan WebP files: {', '.join(orphan_webp)}")
    if counts != {"skill_icon": 20, "item_icon": 16, "vfx_sheet": 47}:
        fail(errors, f"unexpected pack counts: {dict(counts)}")
    checksum_lines = (PACK / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    if len(checksum_lines) != 130:
        fail(errors, f"SHA256SUMS must cover 130 binary files, found {len(checksum_lines)}")
    validate_sensitive_text(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Resource-pack validation failed with {len(errors)} error(s).")
        return 1
    print(
        "Resource-pack validation passed: "
        f"entries={len(entries)} icons={counts['skill_icon'] + counts['item_icon']} "
        f"vfx={counts['vfx_sheet']} previews={len(preview_paths)} duplicate_hashes=0 orphan_files=0"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
