"""Export selected runtime images and their reuse receipt into a new directory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile


def export(pack: Path, destination: Path, ids: list[str]) -> None:
    pack = pack.resolve(strict=True)
    source = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    entries = {item["asset_id"]: item for item in source["entries"]}
    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    selected = []
    for asset_id in dict.fromkeys(ids):
        if asset_id not in entries:
            raise ValueError(f"unknown asset ID: {asset_id}")
        entry = entries[asset_id]
        path = Path(entry["path"])
        if path.is_absolute() or path.drive or ".." in path.parts:
            raise ValueError(f"invalid asset path: {asset_id}")
        if not (pack / path).resolve(strict=True).is_relative_to(pack):
            raise ValueError(f"asset outside pack: {asset_id}")
        selected.append(entry)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        output = Path(temporary) / "selection"
        output.mkdir()
        for entry in selected:
            target = output / entry["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(pack / entry["path"], target)
            if hashlib.sha256(target.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError(f"checksum mismatch: {entry['asset_id']}")
        shutil.copyfile(pack / "LICENSE-ASSETS.md", output / "LICENSE-ASSETS.md")
        receipt = {key: source[key] for key in ("schema_version", "pack_id", "version", "sharing_scope")}
        receipt["entries"] = [
            {k: v for k, v in entry.items() if not k.startswith("preview")}
            for entry in selected
        ]
        (output / "selection.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        output.rename(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("asset_ids", nargs="+")
    args = parser.parse_args()
    try:
        export(args.pack, args.destination, args.asset_ids)
    except (KeyError, OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
