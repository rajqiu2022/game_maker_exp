#!/usr/bin/env python3
"""Build deterministic manifests, catalogues, previews and checksums for reusable packs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^[a-z0-9_]+$")
PACK_RE = re.compile(r"^[a-z0-9][a-z0-9_-]+$")
KINDS = {"skill_icon", "item_icon", "vfx_single", "vfx_sheet", "ui_component"}
STRETCH_MODES = {"none", "scale", "tile", "nine_patch"}
FORBIDDEN_PARTS = {"source", "build", "exports", ".godot", "__pycache__"}
PASSTHROUGH_FIELDS = (
    "interactive",
    "recommended_display_size",
    "anchor",
    "blend_mode",
    "recommended_frame_ms",
    "platforms",
    "stretch_mode",
    "content_safe_margin",
    "recommended_visible_size",
    "recommended_touch_target",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(value: str) -> Path:
    path = Path(value.replace("\\", "/"))
    if not value or path.is_absolute() or path.drive or path.root or ".." in path.parts:
        raise ValueError(f"pack path must be relative: {value}")
    if FORBIDDEN_PARTS.intersection(part.casefold() for part in path.parts):
        raise ValueError(f"forbidden pack path: {value}")
    return path


def _load_spec(repository_root: Path, pack_id: str) -> tuple[Path, dict]:
    if not PACK_RE.fullmatch(pack_id):
        raise ValueError(f"invalid pack ID: {pack_id}")
    pack = repository_root / "resource-packs" / pack_id
    for required in ("README.md", "LICENSE-ASSETS.md", "pack-spec.json"):
        if not (pack / required).is_file():
            raise ValueError(f"missing required pack file: {pack_id}/{required}")
    spec = json.loads((pack / "pack-spec.json").read_text(encoding="utf-8"))
    if spec.get("schema_version") != 1 or spec.get("pack_id") != pack_id:
        raise ValueError(f"invalid pack spec identity: {pack_id}")
    if not spec.get("sharing_scope") or not spec.get("version") or not spec.get("title_zh"):
        raise ValueError(f"incomplete pack metadata: {pack_id}")
    if not isinstance(spec.get("entries"), list):
        raise ValueError(f"pack entries must be an array: {pack_id}")
    return pack, spec


def _validate_ui_metadata(entry: dict, width: int, height: int) -> None:
    stretch = entry.get("stretch_mode")
    margins = entry.get("content_safe_margin")
    platforms = entry.get("platforms")
    visible = entry.get("recommended_visible_size")
    if stretch not in STRETCH_MODES:
        raise ValueError(f"invalid UI stretch_mode: {entry.get('asset_id')}")
    if not isinstance(margins, list) or len(margins) != 4 or any(not isinstance(value, int) or value < 0 for value in margins):
        raise ValueError(f"invalid UI content_safe_margin: {entry.get('asset_id')}")
    if margins[0] + margins[2] >= width or margins[1] + margins[3] >= height:
        raise ValueError(f"UI safe margins consume the source image: {entry.get('asset_id')}")
    if not isinstance(platforms, list) or not platforms:
        raise ValueError(f"UI platforms are required: {entry.get('asset_id')}")
    if not isinstance(visible, list) or len(visible) != 2 or min(visible) <= 0:
        raise ValueError(f"UI recommended_visible_size is required: {entry.get('asset_id')}")
    interactive = entry.get("interactive")
    if not isinstance(interactive, bool):
        raise ValueError(f"UI interactive flag is required: {entry.get('asset_id')}")
    if interactive:
        touch = entry.get("recommended_touch_target")
        if not isinstance(touch, list) or len(touch) != 2 or min(touch) <= 0:
            raise ValueError(f"interactive UI touch target is required: {entry.get('asset_id')}")
        if "mobile" in platforms and min(touch) < 72:
            raise ValueError(f"mobile UI touch target must be at least 72x72: {entry.get('asset_id')}")


def _preview_path(entry: dict) -> str:
    return (Path("previews") / str(entry["category"]) / f"{entry['asset_id']}.webp").as_posix()


def _write_preview(image: Image.Image, kind: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if kind == "vfx_sheet":
        frame_width, frame_height = image.width // 2, image.height // 2
        frames = [
            image.crop(
                (
                    (index % 2) * frame_width,
                    (index // 2) * frame_height,
                    (index % 2 + 1) * frame_width,
                    (index // 2 + 1) * frame_height,
                )
            )
            for index in range(4)
        ]
        frames[0].save(
            destination,
            format="WEBP",
            save_all=True,
            append_images=frames[1:],
            duration=95,
            loop=0,
            lossless=True,
            method=6,
        )
        for frame in frames:
            frame.close()
    else:
        image.save(destination, format="WEBP", lossless=True, method=6)


def _build_entry(pack: Path, raw: dict) -> dict:
    required = {"asset_id", "title_zh", "kind", "category", "path", "description_zh", "tags", "provenance"}
    missing = sorted(required - raw.keys())
    if missing:
        raise ValueError(f"entry missing {', '.join(missing)}: {raw.get('asset_id', '<unknown>')}")
    entry_id = str(raw["asset_id"])
    kind = str(raw["kind"])
    if not ID_RE.fullmatch(entry_id) or kind not in KINDS:
        raise ValueError(f"invalid resource entry: {entry_id}")
    if not isinstance(raw["provenance"], dict) or not raw["provenance"].get("kind"):
        raise ValueError(f"missing provenance: {entry_id}")
    relative = _safe_relative(str(raw["path"]))
    if relative.suffix.casefold() != ".png":
        raise ValueError(f"published resource must be PNG: {entry_id}")
    path = pack / relative
    if not path.is_file():
        raise ValueError(f"missing published resource: {relative.as_posix()}")
    with Image.open(path) as image:
        image.load()
        width, height = image.size
        mode = image.mode
        rgba = image.convert("RGBA")
        alpha_min, alpha_max = rgba.getchannel("A").getextrema()
        pixel_hash = hashlib.sha256(rgba.tobytes()).hexdigest()
        if mode != "RGBA":
            raise ValueError(f"published image must be RGBA: {entry_id}")
        if kind in {"skill_icon", "item_icon", "vfx_single", "vfx_sheet"} and (alpha_min != 0 or alpha_max == 0):
            raise ValueError(f"transparent resource lacks useful alpha: {entry_id}")
        if kind == "skill_icon" and (width, height) != (256, 256):
            raise ValueError(f"skill icon must be 256x256: {entry_id}")
        if kind == "item_icon" and (width != height or width not in {64, 128, 256}):
            raise ValueError(f"item icon must be 64, 128 or 256 square: {entry_id}")
        if kind == "vfx_sheet" and (width != height or width % 2 or height % 2):
            raise ValueError(f"VFX sheet must be an even square: {entry_id}")
        if kind == "ui_component":
            _validate_ui_metadata(raw, width, height)
        preview = None
        if kind in {"vfx_single", "vfx_sheet", "ui_component"}:
            preview = _preview_path(raw)
            _write_preview(rgba, kind, pack / preview)
    entry = {
        "asset_id": entry_id,
        "title_zh": raw["title_zh"],
        "kind": kind,
        "category": raw["category"],
        "category_zh": raw.get("category_zh", raw["category"]),
        "path": relative.as_posix(),
        "description_zh": raw["description_zh"],
        "format": "PNG",
        "width": width,
        "height": height,
        "color_mode": mode,
        "has_alpha": True,
        "sha256": sha256(path),
        "pixel_sha256_rgba": pixel_hash,
        "status": "validated_runtime",
        "version": raw.get("version", "1.0.0"),
        "rights": "see LICENSE-ASSETS.md",
        "license_status": "NOASSERTION_owner_project_reuse_only",
        "tags": raw["tags"],
        "layout": "2x2" if kind == "vfx_sheet" else "single",
        "provenance": raw["provenance"],
    }
    for field in PASSTHROUGH_FIELDS:
        if field in raw:
            entry[field] = raw[field]
    if kind == "vfx_sheet":
        entry.update(
            {
                "frame_count": 4,
                "frame_order": ["top_left", "top_right", "bottom_left", "bottom_right"],
                "frame_width": width // 2,
                "frame_height": height // 2,
            }
        )
    if preview:
        entry["preview_path"] = preview
    return entry


def _catalogue(spec: dict, entries: list[dict]) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        grouped[entry["category"]].append(entry)
    lines = [
        f"# {spec['title_zh']}资源目录",
        "",
        "> 本文档由 `python tools/build_resource_pack.py` 自动生成，请勿手工修改。",
        "",
        f"当前包含 **{len(entries)} 个资源条目**。",
        "",
    ]
    categories = spec.get("categories", {})
    for category in sorted(grouped):
        lines.extend([f"## {categories.get(category, category)}", "", "| 预览 | 资源 ID | 描述 | 规格 |", "|---|---|---|---|"])
        for entry in grouped[category]:
            preview = entry.get("preview_path", entry["path"])
            spec_text = f"{entry['width']}×{entry['height']} {entry['color_mode']} · {entry['layout']}"
            lines.append(
                f"| ![{entry['title_zh']}]({preview}) | `{entry['asset_id']}` | {entry['description_zh']} | {spec_text} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_pack(repository_root: Path, pack_id: str) -> dict[str, int]:
    pack, spec = _load_spec(repository_root, pack_id)
    raw_entries = spec["entries"]
    ids = [str(entry.get("asset_id", "")) for entry in raw_entries]
    paths = [str(entry.get("path", "")) for entry in raw_entries]
    if len(ids) != len(set(ids)) or len(paths) != len(set(paths)):
        raise ValueError(f"duplicate resource ID or path in {pack_id}")
    listed_paths = {_safe_relative(path).as_posix() for path in paths}
    published_png = {path.relative_to(pack).as_posix() for path in pack.rglob("*.png") if "previews" not in path.parts}
    orphan_png = sorted(published_png - listed_paths)
    if orphan_png:
        raise ValueError(f"orphan PNG files before build: {', '.join(orphan_png)}")
    entries = [_build_entry(pack, raw) for raw in raw_entries]
    hashes = [entry["sha256"] for entry in entries]
    if len(hashes) != len(set(hashes)):
        raise ValueError(f"duplicate physical resource content in {pack_id}")
    manifest = {
        "schema_version": 1,
        "pack_id": pack_id,
        "version": spec["version"],
        "generated_at": spec["generated_at"],
        "sharing_scope": spec["sharing_scope"],
        "entries": entries,
    }
    (pack / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (pack / "CATALOG.md").write_text(_catalogue(spec, entries), encoding="utf-8")
    binaries = sorted(pack.rglob("*.png")) + sorted(pack.rglob("*.webp"))
    checksums = [f"{sha256(path)}  {path.relative_to(pack).as_posix()}" for path in binaries]
    (pack / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    return {"entries": len(entries), "hashed_files": len(binaries)}


def discover_pack_ids(repository_root: Path) -> list[str]:
    resource_root = repository_root / "resource-packs"
    return sorted(path.parent.name for path in resource_root.glob("*/pack-spec.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pack")
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()
    pack_ids = discover_pack_ids(ROOT) if args.all else [args.pack]
    for pack_id in pack_ids:
        summary = build_pack(ROOT, pack_id)
        print(f"Built {pack_id}: {summary['entries']} entries, {summary['hashed_files']} hashed files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
