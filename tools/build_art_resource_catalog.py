#!/usr/bin/env python3
"""Build the reusable art-pack manifest, checksums and Markdown catalogue."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "resource-packs" / "ink-wuxia-icons-vfx-v1"

TITLE_ZH = {
    "icon_skill_basic_blade_v1": "基础刀击",
    "icon_skill_basic_staff_v1": "基础棍击",
    "icon_skill_basic_sword_v1": "基础剑击",
    "icon_skill_basic_unarmed_v1": "基础拳击",
    "icon_skill_blade_crescent_v1": "弧月刀势",
    "icon_skill_blade_heavy_v1": "重刀劈斩",
    "icon_skill_footwork_v1": "轻功步法",
    "icon_skill_frost_needles_v1": "寒霜针雨",
    "icon_skill_guard_v1": "护体守御",
    "icon_skill_healing_v1": "回生治疗",
    "icon_skill_inner_breath_v1": "吐纳内功",
    "icon_skill_palm_wave_v1": "掌劲气浪",
    "icon_skill_poison_needles_v1": "淬毒飞针",
    "icon_skill_redirect_v1": "移劲卸力",
    "icon_skill_shadow_dagger_v1": "暗影短刃",
    "icon_skill_staff_sweep_v1": "长棍横扫",
    "icon_skill_sword_cross_v1": "交错剑光",
    "icon_skill_sword_slash_v1": "剑气斩击",
    "icon_skill_sword_star_v1": "星落剑芒",
    "icon_skill_sword_yinyang_v1": "阴阳剑势",
    "item_broken_mask": "破损面具",
    "item_cold_incense_pouch": "冷香囊",
    "item_confession_scroll": "供词卷轴",
    "item_evidence_statement": "证物陈词",
    "item_faction_token": "门派令牌",
    "item_false_note": "可疑字条",
    "item_herb_bundle": "药草束",
    "item_herbal_ledger": "药材账册",
    "item_iron_ore": "铁矿石",
    "item_jade_fragment": "玉石碎片",
    "item_luminous_silk": "流光丝料",
    "item_sealed_letter": "封缄书信",
    "item_spirit_stone": "灵性矿石",
    "item_testimony": "证言文书",
    "item_village_map": "村落地图",
    "item_white_jade_pendant": "白玉佩",
    "vfx_melee_basic_impact_01": "基础近战命中",
    "vfx_palm_ocean_shockwave_01": "沧浪掌劲冲击",
    "vfx_movement_dragon_turn_01": "游龙折转轨迹",
    "vfx_guard_blue_shield_01": "青蓝护体屏障",
    "vfx_staff_wind_sweep_01": "棍风横扫",
    "vfx_blade_tiger_impact_01": "虎形刀势冲击",
    "vfx_guard_golden_bell_01": "金钟护罩",
    "vfx_inner_gold_aura_01": "金色内劲聚气",
    "vfx_blade_vertical_cleave_01": "纵向重刀劈斩",
    "vfx_blade_earth_split_01": "裂地刀势",
    "vfx_sword_falling_star_01": "流星剑芒",
    "vfx_blade_heavy_cleave_01": "厚重刀光",
    "vfx_sword_mountain_arc_01": "千山剑弧",
    "vfx_sword_cloud_pierce_01": "破云穿刺剑光",
    "vfx_sword_straight_slash_01": "直线剑斩",
    "vfx_guard_violet_crystal_01": "紫晶罡罩",
    "vfx_inner_violet_cloud_01": "紫云内息",
    "vfx_redirect_water_swirl_01": "回澜卸力水旋",
    "vfx_inner_meridian_gold_01": "金色经脉淬炼",
    "vfx_needle_frost_storm_01": "寒霜针暴",
    "vfx_needle_frost_burst_01": "寒针冰爆",
    "vfx_needle_silver_point_01": "银针点刺",
    "vfx_movement_moon_water_step_01": "月下踏水步",
    "vfx_inner_moon_aura_01": "月华内息",
    "vfx_sword_blue_arc_01": "青蓝剑弧一",
    "vfx_sword_blue_arc_02": "青蓝剑弧二",
    "vfx_inner_breath_green_01": "青绿色吐纳气息",
    "vfx_movement_shadow_step_01": "暗影疾步",
    "vfx_dagger_wind_slash_01": "短刃风切",
    "vfx_dagger_mist_combo_01": "雾影连斩",
    "vfx_dagger_shadow_execution_01": "暗影绝杀",
    "vfx_inner_shadow_aura_01": "暗影内息",
    "vfx_palm_crimson_impact_01": "赤色掌劲冲击",
    "vfx_guard_wood_leaf_01": "青木叶阵护罩",
    "vfx_healing_emerald_breath_01": "翠绿回生灵息",
    "vfx_sword_swallow_arc_01": "燕返剑弧",
    "vfx_staff_breaker_impact_01": "破阵棍击",
    "vfx_staff_leaf_sweep_01": "扫叶棍风",
    "vfx_needle_poison_volley_01": "毒针齐射",
    "vfx_sword_counter_lines_01": "破招剑线",
    "vfx_taiji_opening_01": "太极起势",
    "vfx_taiji_dual_orbit_01": "两仪环流",
    "vfx_taiji_four_symbol_01": "四象气旋",
    "vfx_guard_tortoise_shell_01": "玄甲护罩",
    "vfx_inner_taiji_aura_01": "太极内息",
    "vfx_blade_black_wind_01": "黑风刀卷",
    "vfx_blade_gate_break_01": "破门刀击",
}

CATEGORY_ZH = {
    "icons/skills/basic": "图标 · 基础攻击",
    "icons/skills/blade": "图标 · 刀法",
    "icons/skills/dagger": "图标 · 短刃",
    "icons/skills/movement": "图标 · 身法",
    "icons/skills/needle": "图标 · 飞针",
    "icons/skills/palm": "图标 · 掌法",
    "icons/skills/staff": "图标 · 棍法",
    "icons/skills/support": "图标 · 辅助与内功",
    "icons/skills/sword": "图标 · 剑法",
    "icons/items/clues": "图标 · 线索与文书",
    "icons/items/materials": "图标 · 材料",
    "icons/items/tokens": "图标 · 信物",
    "vfx/attack/blade": "特效 · 刀法攻击",
    "vfx/attack/dagger": "特效 · 短刃攻击",
    "vfx/attack/misc": "特效 · 通用命中",
    "vfx/attack/needle": "特效 · 飞针攻击",
    "vfx/attack/palm": "特效 · 掌法攻击",
    "vfx/attack/staff": "特效 · 棍法攻击",
    "vfx/attack/sword": "特效 · 剑法攻击",
    "vfx/attack/taiji": "特效 · 太极气劲",
    "vfx/movement": "特效 · 身法轨迹",
    "vfx/support/guard": "特效 · 护体",
    "vfx/support/healing": "特效 · 治疗",
    "vfx/support/inner": "特效 · 内功",
    "vfx/support/redirect": "特效 · 卸力与转化",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asset_id(path: Path) -> str:
    stem = path.stem
    return stem.removesuffix("_4frame_v1") if "/vfx/" in f"/{path.as_posix()}" else stem


def description(kind: str, title: str) -> str:
    if kind == "skill_icon":
        return f"表达“{title}”语义的无字透明技能图标，适合技能列表、快捷栏和战斗 HUD。"
    if kind == "item_icon":
        return f"表达“{title}”物件语义的无字透明图标，适合背包、掉落、线索和任务界面。"
    return f"“{title}”四阶段透明特效，按起势、增强、命中峰值、消散的顺序播放。"


def build_entry(path: Path) -> dict[str, object]:
    relative = path.relative_to(PACK).as_posix()
    category = path.parent.relative_to(PACK).as_posix()
    entry_id = asset_id(path)
    if entry_id not in TITLE_ZH:
        raise KeyError(f"missing Chinese title for {entry_id}")
    with Image.open(path) as image:
        width, height = image.size
        mode = image.mode
        pixel_sha256 = hashlib.sha256(image.convert("RGBA").tobytes()).hexdigest()
    if relative.startswith("icons/skills/"):
        kind = "skill_icon"
    elif relative.startswith("icons/items/"):
        kind = "item_icon"
    else:
        kind = "vfx_sheet"
    entry: dict[str, object] = {
        "asset_id": entry_id,
        "title_zh": TITLE_ZH[entry_id],
        "kind": kind,
        "category": category,
        "category_zh": CATEGORY_ZH[category],
        "path": relative,
        "description_zh": description(kind, TITLE_ZH[entry_id]),
        "format": "PNG",
        "width": width,
        "height": height,
        "color_mode": mode,
        "has_alpha": "A" in mode,
        "sha256": sha256(path),
        "pixel_sha256_rgba": pixel_sha256,
        "status": "validated_runtime",
        "version": "1.0.0",
        "rights": "see LICENSE-ASSETS.md",
        "license_status": "NOASSERTION_owner_project_reuse_only",
        "tags": [part for part in category.split("/")[1:] if part] + [
            part for part in entry_id.split("_") if part not in {"icon", "skill", "item", "vfx", "v1", "01"}
        ],
    }
    if kind.endswith("icon"):
        entry.update(
            {
                "layout": "single",
                "recommended_display_size": [64, 128],
                "transparent_background": True,
                "textless": True,
                "framed": False,
                "provenance": {
                    "kind": "ai_generated_and_locally_processed",
                    "backend": "codex_builtin",
                    "model": "codex-imagegen-built-in",
                },
            }
        )
    else:
        preview = Path("previews") / category / f"{entry_id}.webp"
        entry.update(
            {
                "preview_path": preview.as_posix(),
                "layout": "2x2",
                "frame_count": 4,
                "frame_order": ["top_left", "top_right", "bottom_left", "bottom_right"],
                "frame_width": width // 2,
                "frame_height": height // 2,
                "recommended_frame_ms": [90, 105],
                "recommended_display_size": 460 if width > 1024 else 380,
                "anchor": "cell_center",
                "blend_mode": "alpha",
                "transparent_background": True,
                "provenance": {
                    "kind": "project_generated_ai_runtime",
                    "backend": "mixed_project_pipeline",
                    "note": "Provider metadata completeness varies across the adopted source batch.",
                },
            }
        )
    return entry


def markdown(entries: list[dict[str, object]]) -> str:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for entry in entries:
        grouped[str(entry["category"])].append(entry)
    lines = [
        "# 水墨武侠图标与招式特效资源目录",
        "",
        "> 本文档由 `python tools/build_art_resource_catalog.py` 从发布资源和规格自动生成，请勿手工改表格。",
        "",
        f"当前包含 **{sum(e['kind'].endswith('icon') for e in entries)} 个图标**、**{sum(e['kind'] == 'vfx_sheet' for e in entries)} 套四阶段特效**。",
        "",
        "所有文件使用稳定的英文语义 ID，不包含具体游戏角色名、剧情名、绝对路径或 Godot `.import` 文件。",
        "",
    ]
    for category in sorted(grouped):
        rows = grouped[category]
        lines.extend(
            [
                f"## {CATEGORY_ZH[category]}",
                "",
                "| 预览 | 资源 ID | 内容描述 | 规格 | 文件 |",
                "|---|---|---|---|---|",
            ]
        )
        for entry in rows:
            preview = str(entry.get("preview_path", entry["path"]))
            spec = f"{entry['width']}×{entry['height']} {entry['color_mode']}"
            if entry["kind"] == "vfx_sheet":
                spec += f"；2×2 / 4 帧；单帧 {entry['frame_width']}×{entry['frame_height']}"
            else:
                spec += "；无字透明底"
            lines.append(
                f"| ![{entry['title_zh']}]({preview}) | `{entry['asset_id']}` · {entry['title_zh']} | "
                f"{entry['description_zh']} | {spec} | [`{entry['path']}`]({entry['path']}) |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    png_files = sorted((PACK / "icons").rglob("*.png")) + sorted((PACK / "vfx").rglob("*.png"))
    entries = [build_entry(path) for path in png_files]
    ids = [str(entry["asset_id"]) for entry in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate asset IDs detected")
    manifest = {
        "schema_version": 1,
        "pack_id": "ink_wuxia_icons_vfx_v1",
        "version": "1.0.0",
        "generated_at": "2026-08-18",
        "sharing_scope": "repository_owner_projects; third-party use requires permission",
        "entries": entries,
    }
    (PACK / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (PACK / "CATALOG.md").write_text(markdown(entries).rstrip() + "\n", encoding="utf-8")
    checksums = []
    for path in sorted((PACK / "icons").rglob("*.png")) + sorted((PACK / "vfx").rglob("*.png")) + sorted((PACK / "previews").rglob("*.webp")):
        checksums.append(f"{sha256(path)}  {path.relative_to(PACK).as_posix()}")
    (PACK / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print(f"Built art catalogue: {len(entries)} entries, {len(checksums)} hashed files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
