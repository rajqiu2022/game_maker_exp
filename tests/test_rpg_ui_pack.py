from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK_ID = "rpg-ui-kit-v1"
SELECTION = ROOT / "specs" / "resource-packs" / f"{PACK_ID}.json"
PACK = ROOT / "resource-packs" / PACK_ID
REQUIRED_METADATA = {
    "asset_id",
    "category",
    "platforms",
    "stretch_mode",
    "content_safe_margin",
    "recommended_visible_size",
    "interactive",
}


class RpgUiPackContracts(unittest.TestCase):
    def load_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_selection_locks_42_core_12_mobile_8_hud(self) -> None:
        entries = self.load_json(SELECTION)["entries"]
        self.assertEqual(62, len(entries))
        sources = [entry["source"].replace("\\", "/") for entry in entries]
        self.assertEqual(42, sum("/ui/kit/" in source for source in sources))
        self.assertEqual(12, sum("/ui/mobile/" in source for source in sources))
        self.assertEqual(8, sum("/ui/hud/" in source for source in sources))
        self.assertFalse(any("/source/" in source or source.endswith(".import") for source in sources))
        self.assertEqual(62, len({entry["destination"] for entry in entries}))

    def test_pack_spec_has_responsive_and_touch_metadata(self) -> None:
        entries = self.load_json(PACK / "pack-spec.json")["entries"]
        self.assertEqual(62, len(entries))
        counts = {
            "core": sum(entry["category"].startswith("ui_core_") for entry in entries),
            "mobile": sum(entry["category"] == "ui_mobile_controls" for entry in entries),
            "hud": sum(entry["category"] == "ui_hud_status" for entry in entries),
        }
        self.assertEqual({"core": 42, "mobile": 12, "hud": 8}, counts)
        for entry in entries:
            self.assertTrue(REQUIRED_METADATA.issubset(entry))
            self.assertEqual(4, len(entry["content_safe_margin"]))
            self.assertEqual(2, len(entry["recommended_visible_size"]))
            if entry["interactive"]:
                self.assertIn("recommended_touch_target", entry)
        for entry in entries:
            if entry["category"] == "ui_mobile_controls":
                self.assertGreaterEqual(min(entry["recommended_touch_target"]), 72)
                self.assertNotEqual(entry["recommended_visible_size"], entry["recommended_touch_target"])

    def test_manifest_preserves_ui_contract(self) -> None:
        entries = self.load_json(PACK / "manifest.json")["entries"]
        self.assertEqual(62, len(entries))
        for entry in entries:
            self.assertEqual("ui_component", entry["kind"])
            self.assertEqual("RGBA", entry["color_mode"])
            self.assertIn("interactive", entry)
            self.assertTrue((PACK / entry["path"]).is_file())
            self.assertTrue((PACK / entry["preview_path"]).is_file())

    def test_required_pack_documents_exist(self) -> None:
        for name in ("README.md", "LICENSE-ASSETS.md", "CATALOG.md", "SHA256SUMS"):
            self.assertTrue((PACK / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
