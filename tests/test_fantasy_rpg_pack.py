from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK_ID = "fantasy-rpg-icons-vfx-v1"
SELECTION = ROOT / "specs" / "resource-packs" / f"{PACK_ID}.json"
PACK = ROOT / "resource-packs" / PACK_ID


class FantasyRpgPackContracts(unittest.TestCase):
    def load_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_selection_locks_approved_inventory(self) -> None:
        data = self.load_json(SELECTION)
        entries = data["entries"]
        self.assertEqual(95, len(entries))
        self.assertEqual(90, sum(entry.get("operation", "copy") == "copy" for entry in entries))
        self.assertEqual(5, sum(entry.get("operation") == "compose_2x2" for entry in entries))
        self.assertEqual(95, len({entry["destination"] for entry in entries}))

    def test_selection_rejects_project_only_and_failed_candidates(self) -> None:
        data = self.load_json(SELECTION)
        source_values: list[str] = []
        for entry in data["entries"]:
            source_values.extend(entry.get("sources", [entry.get("source", "")]))
        joined = "\n".join(source_values).replace("\\", "/").lower()
        for forbidden in ("_source", ".import", "assassin_v2", "unknown", "frontier"):
            self.assertNotIn(forbidden, joined)
        self.assertNotRegex(joined, r"(^|/)source(/|$)")
        self.assertNotRegex(joined, r"[a-z]:/")
        self.assertNotRegex(joined, r"(?:ranger_bow_10|windrunner_bow_15)")

    def test_pack_spec_has_exact_semantic_categories(self) -> None:
        spec = self.load_json(PACK / "pack-spec.json")
        entries = spec["entries"]
        counts: dict[str, int] = {}
        for entry in entries:
            counts[entry["kind"]] = counts.get(entry["kind"], 0) + 1
            self.assertRegex(entry["asset_id"], r"^[a-z0-9_]+$")
            self.assertFalse(re.search(r"unknown|frontier|(?:^|_)lv?\d+(?:_|$)", entry["asset_id"]))
        self.assertEqual(
            {"skill_icon": 23, "item_icon": 36, "vfx_single": 31, "vfx_sheet": 5},
            counts,
        )
        assassin = [entry for entry in entries if entry["category"] == "vfx_assassin"]
        self.assertEqual(7, len(assassin))

    def test_manifest_contains_95_validated_entries(self) -> None:
        manifest = self.load_json(PACK / "manifest.json")
        entries = manifest["entries"]
        self.assertEqual(95, len(entries))
        self.assertEqual(23, sum(entry["kind"] == "skill_icon" for entry in entries))
        self.assertEqual(36, sum(entry["kind"] == "item_icon" for entry in entries))
        self.assertTrue(all(entry["color_mode"] == "RGBA" for entry in entries))
        self.assertTrue(all((PACK / entry["path"]).is_file() for entry in entries))

    def test_required_pack_documents_exist(self) -> None:
        for name in ("README.md", "LICENSE-ASSETS.md", "CATALOG.md", "SHA256SUMS"):
            self.assertTrue((PACK / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
