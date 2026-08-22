#!/usr/bin/env python3
"""Import approved runtime art without ever overwriting different content."""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

from PIL import Image


FORBIDDEN_PARTS = {"source", "build", "exports", ".godot", "__pycache__"}


def safe_relative(value: str) -> Path:
    normalized = value.replace("\\", "/")
    path = Path(normalized)
    if not value or path.is_absolute() or path.drive or path.root or any(part == ".." for part in path.parts):
        raise ValueError(f"path must be repository-relative: {value}")
    if any(part in {"", "."} for part in path.parts):
        raise ValueError(f"path contains an unstable segment: {value}")
    return path


def _write_no_clobber(data: bytes, destination: Path) -> str:
    if destination.exists():
        if not destination.is_file() or destination.read_bytes() != data:
            raise FileExistsError(f"destination has different content: {destination}")
        return "identical"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as handle:
        handle.write(data)
    return "created"


def copy_no_clobber(source: Path, destination: Path) -> str:
    if not source.is_file():
        raise FileNotFoundError(source)
    return _write_no_clobber(source.read_bytes(), destination)


def compose_2x2_no_clobber(sources: list[Path], destination: Path) -> str:
    if len(sources) != 4:
        raise ValueError("compose_2x2 requires exactly four source frames")
    frames: list[Image.Image] = []
    try:
        for source in sources:
            with Image.open(source) as image:
                image.load()
                if image.mode != "RGBA":
                    raise ValueError(f"compose_2x2 source must be RGBA: {source}")
                frames.append(image.copy())
        size = frames[0].size
        if any(frame.size != size for frame in frames):
            raise ValueError("compose_2x2 source frames must have equal dimensions")
        sheet = Image.new("RGBA", (size[0] * 2, size[1] * 2), (0, 0, 0, 0))
        for index, frame in enumerate(frames):
            sheet.paste(frame, ((index % 2) * size[0], (index // 2) * size[1]))
        output = io.BytesIO()
        sheet.save(output, format="PNG")
        return _write_no_clobber(output.getvalue(), destination)
    finally:
        for frame in frames:
            frame.close()


def _validated_source(value: str) -> Path:
    relative = safe_relative(value)
    if FORBIDDEN_PARTS.intersection(part.casefold() for part in relative.parts):
        raise ValueError(f"forbidden source path: {value}")
    if relative.suffix.casefold() != ".png":
        raise ValueError(f"only runtime PNG sources are accepted: {value}")
    return relative


def import_selection(source_root: Path, repository_root: Path, selection_path: Path) -> dict[str, int]:
    data = json.loads(selection_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("selection schema_version must be 1")
    pack_id = str(data.get("pack_id", ""))
    if not pack_id or not all(character.islower() or character.isdigit() or character in "-_" for character in pack_id):
        raise ValueError(f"invalid pack_id: {pack_id}")
    pack_root = repository_root / "resource-packs" / pack_id
    summary = {"created": 0, "identical": 0, "rejected": 0}
    for entry in data.get("entries", []):
        destination_relative = safe_relative(str(entry.get("destination", "")))
        if FORBIDDEN_PARTS.intersection(part.casefold() for part in destination_relative.parts):
            raise ValueError(f"forbidden destination path: {destination_relative}")
        destination = pack_root / destination_relative
        operation = entry.get("operation", "copy")
        try:
            if operation == "copy":
                source = source_root / _validated_source(str(entry.get("source", "")))
                result = copy_no_clobber(source, destination)
            elif operation == "compose_2x2":
                sources = [source_root / _validated_source(str(value)) for value in entry.get("sources", [])]
                result = compose_2x2_no_clobber(sources, destination)
            else:
                raise ValueError(f"unsupported import operation: {operation}")
        except Exception:
            summary["rejected"] += 1
            raise
        summary[result] += 1
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--selection", required=True, type=Path)
    args = parser.parse_args()
    repository_root = Path(__file__).resolve().parents[1]
    summary = import_selection(args.source_root.resolve(), repository_root, args.selection.resolve())
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
