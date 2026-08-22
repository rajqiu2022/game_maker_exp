from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "adoption" / "rpg-map-resource-fit.md"
PACK_IDS = ("ink-wuxia-icons-vfx-v1", "fantasy-rpg-icons-vfx-v1", "rpg-ui-kit-v1")
REQUIRED_ASSETS = {
    "icon_skill_shadow_dagger_v1",
    "vfx_dagger_shadow_execution_01",
    "vfx_dagger_mist_combo_01",
    "vfx_dagger_wind_slash_01",
    "vfx_movement_shadow_step_01",
    "icon_skill_basic_sword_v1",
    "vfx_blade_heavy_cleave_01",
    "vfx_blade_earth_split_01",
    "vfx_melee_basic_impact_01",
    "vfx_guard_blue_shield_01",
    "vfx_healing_emerald_breath_01",
    "vfx_inner_gold_aura_01",
    "vfx_redirect_water_swirl_01",
    "item_iron_ore",
    "item_spirit_stone",
    "item_jade_fragment",
    "item_herb_bundle",
}


class AdoptionMappingContracts(unittest.TestCase):
    def manifest_ids(self) -> set[str]:
        result: set[str] = set()
        for pack_id in PACK_IDS:
            path = ROOT / "resource-packs" / pack_id / "manifest.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            result.update(entry["asset_id"] for entry in data["entries"])
        return result

    def test_report_references_required_existing_assets(self) -> None:
        text = REPORT.read_text(encoding="utf-8")
        referenced = set(re.findall(r"`((?:icon|item|vfx|ui)_[a-z0-9_]+)`", text))
        self.assertTrue(REQUIRED_ASSETS.issubset(referenced))
        self.assertEqual(set(), referenced - self.manifest_ids())

    def test_report_is_recommendation_only_and_does_not_change_runtime(self) -> None:
        text = REPORT.read_text(encoding="utf-8")
        self.assertIn("推荐映射，不是自动替换", text)
        self.assertIn("不修改 `rpg_map` 任何运行时文件", text)
        for heading in ("当前用途", "共享资源 ID", "语义匹配", "适配工作", "风险"):
            self.assertIn(heading, text)

    def test_navigation_links_all_three_packs_and_report(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        pack_readme = (ROOT / "resource-packs" / "README.md").read_text(encoding="utf-8")
        for pack_id in PACK_IDS:
            self.assertIn(pack_id, root_readme)
            self.assertIn(pack_id, pack_readme)
        self.assertIn("adoption/rpg-map-resource-fit.md", root_readme)


if __name__ == "__main__":
    unittest.main()
