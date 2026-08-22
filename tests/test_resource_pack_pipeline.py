from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.build_resource_pack import build_pack
from tools.validate_resource_packs import validate_pack


class ResourcePackPipelineTests(unittest.TestCase):
    def make_png(self, path: Path, size: tuple[int, int], color: tuple[int, int, int, int]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", size, color)
        image.putpixel((0, 0), (color[0], color[1], color[2], 0))
        image.save(path)

    def make_repository(self) -> tuple[tempfile.TemporaryDirectory, Path, str]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        pack_id = "demo-pack-v1"
        pack = root / "resource-packs" / pack_id
        pack.mkdir(parents=True)
        (pack / "README.md").write_text("# Demo\n", encoding="utf-8")
        (pack / "LICENSE-ASSETS.md").write_text("owner project reuse only\n", encoding="utf-8")
        self.make_png(pack / "icons" / "icon_test.png", (256, 256), (180, 40, 60, 220))
        self.make_png(pack / "vfx" / "vfx_single.png", (64, 64), (20, 80, 220, 180))
        sheet = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        for index, color in enumerate(((255, 0, 0, 200), (0, 255, 0, 200), (0, 0, 255, 200), (255, 255, 0, 200))):
            frame = Image.new("RGBA", (32, 32), color)
            frame.putpixel((0, 0), (color[0], color[1], color[2], 0))
            sheet.paste(frame, ((index % 2) * 32, (index // 2) * 32))
        (pack / "vfx").mkdir(exist_ok=True)
        sheet.save(pack / "vfx" / "vfx_sheet.png")
        self.make_png(pack / "ui" / "button.png", (80, 40), (15, 25, 35, 230))
        entries = [
            {
                "asset_id": "icon_test",
                "title_zh": "测试图标",
                "kind": "skill_icon",
                "category": "icons",
                "path": "icons/icon_test.png",
                "description_zh": "无字透明测试图标。",
                "tags": ["test"],
                "recommended_display_size": [64, 128],
                "provenance": {"kind": "project_generated", "backend": "test"},
            },
            {
                "asset_id": "vfx_single",
                "title_zh": "单帧特效",
                "kind": "vfx_single",
                "category": "vfx",
                "path": "vfx/vfx_single.png",
                "description_zh": "单阶段透明特效。",
                "tags": ["test"],
                "anchor": "center",
                "blend_mode": "alpha",
                "recommended_display_size": 96,
                "provenance": {"kind": "project_generated", "backend": "test"},
            },
            {
                "asset_id": "vfx_sheet",
                "title_zh": "四帧特效",
                "kind": "vfx_sheet",
                "category": "vfx",
                "path": "vfx/vfx_sheet.png",
                "description_zh": "四阶段透明特效。",
                "tags": ["test"],
                "anchor": "cell_center",
                "blend_mode": "alpha",
                "recommended_frame_ms": [90, 105],
                "recommended_display_size": 96,
                "provenance": {"kind": "project_generated", "backend": "test"},
            },
            {
                "asset_id": "ui_button",
                "title_zh": "按钮",
                "kind": "ui_component",
                "category": "ui",
                "path": "ui/button.png",
                "description_zh": "通用无字按钮。",
                "tags": ["ui"],
                "platforms": ["desktop", "mobile"],
                "stretch_mode": "nine_patch",
                "content_safe_margin": [8, 8, 8, 8],
                "recommended_visible_size": [160, 80],
                "recommended_touch_target": [160, 80],
                "interactive": True,
                "provenance": {"kind": "project_generated", "backend": "test"},
            },
        ]
        spec = {
            "schema_version": 1,
            "pack_id": pack_id,
            "title_zh": "测试资源包",
            "version": "1.0.0",
            "generated_at": "2026-08-22",
            "sharing_scope": "repository owner projects",
            "categories": {"icons": "图标", "vfx": "特效", "ui": "界面"},
            "entries": entries,
        }
        (pack / "pack-spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        return temporary, root, pack_id

    def test_builder_generates_manifest_catalog_checksums_and_previews(self) -> None:
        temporary, root, pack_id = self.make_repository()
        self.addCleanup(temporary.cleanup)

        summary = build_pack(root, pack_id)

        pack = root / "resource-packs" / pack_id
        self.assertEqual(4, summary["entries"])
        for relative in ("manifest.json", "CATALOG.md", "SHA256SUMS"):
            self.assertTrue((pack / relative).is_file(), relative)
        self.assertTrue((pack / "previews" / "vfx" / "vfx_single.webp").is_file())
        self.assertTrue((pack / "previews" / "vfx" / "vfx_sheet.webp").is_file())
        self.assertEqual([], validate_pack(root, pack_id))

    def test_builder_supports_icon_single_vfx_sheet_and_ui_component(self) -> None:
        temporary, root, pack_id = self.make_repository()
        self.addCleanup(temporary.cleanup)
        build_pack(root, pack_id)

        entries = json.loads((root / "resource-packs" / pack_id / "manifest.json").read_text(encoding="utf-8"))["entries"]
        by_id = {entry["asset_id"]: entry for entry in entries}
        self.assertEqual("single", by_id["icon_test"]["layout"])
        self.assertEqual("single", by_id["vfx_single"]["layout"])
        self.assertEqual(4, by_id["vfx_sheet"]["frame_count"])
        self.assertEqual([8, 8, 8, 8], by_id["ui_button"]["content_safe_margin"])

    def test_validator_rejects_orphan_binary(self) -> None:
        temporary, root, pack_id = self.make_repository()
        self.addCleanup(temporary.cleanup)
        build_pack(root, pack_id)
        self.make_png(root / "resource-packs" / pack_id / "icons" / "orphan.png", (256, 256), (1, 2, 3, 255))

        self.assertTrue(any("orphan PNG" in error for error in validate_pack(root, pack_id)))

    def test_builder_rejects_duplicate_id_path_or_hash(self) -> None:
        for field in ("asset_id", "path", "hash"):
            temporary, root, pack_id = self.make_repository()
            try:
                spec_path = root / "resource-packs" / pack_id / "pack-spec.json"
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                duplicate = dict(spec["entries"][0])
                duplicate["asset_id"] = "icon_duplicate"
                duplicate["path"] = "icons/icon_duplicate.png"
                self.make_png(root / "resource-packs" / pack_id / duplicate["path"], (256, 256), (11, 22, 33, 255))
                if field == "asset_id":
                    duplicate["asset_id"] = spec["entries"][0]["asset_id"]
                elif field == "path":
                    duplicate["path"] = spec["entries"][0]["path"]
                else:
                    (root / "resource-packs" / pack_id / duplicate["path"]).write_bytes(
                        (root / "resource-packs" / pack_id / spec["entries"][0]["path"]).read_bytes()
                    )
                spec["entries"].append(duplicate)
                spec_path.write_text(json.dumps(spec), encoding="utf-8")

                with self.subTest(field=field), self.assertRaises(ValueError):
                    build_pack(root, pack_id)
            finally:
                temporary.cleanup()

    def test_validator_rejects_import_source_build_and_sensitive_paths(self) -> None:
        temporary, root, pack_id = self.make_repository()
        self.addCleanup(temporary.cleanup)
        build_pack(root, pack_id)
        pack = root / "resource-packs" / pack_id
        (pack / "notes.md").write_text("D:\\code\\private and ghp_1234567890123456", encoding="utf-8")
        (pack / "bad.png.import").write_text("cache", encoding="utf-8")

        errors = validate_pack(root, pack_id)
        self.assertTrue(any("forbidden file" in error for error in errors))
        self.assertTrue(any("sensitive" in error for error in errors))

    def test_validator_rejects_missing_license_or_provenance(self) -> None:
        temporary, root, pack_id = self.make_repository()
        self.addCleanup(temporary.cleanup)
        pack = root / "resource-packs" / pack_id
        spec_path = pack / "pack-spec.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        spec["entries"][0].pop("provenance")
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        (pack / "LICENSE-ASSETS.md").unlink()

        with self.assertRaises(ValueError):
            build_pack(root, pack_id)

    def test_validator_checks_ui_safe_area_and_stretch_contract(self) -> None:
        temporary, root, pack_id = self.make_repository()
        self.addCleanup(temporary.cleanup)
        spec_path = root / "resource-packs" / pack_id / "pack-spec.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        ui = next(entry for entry in spec["entries"] if entry["kind"] == "ui_component")
        ui["content_safe_margin"] = [50, 8, 50, 8]
        ui["stretch_mode"] = "unknown"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")

        with self.assertRaises(ValueError):
            build_pack(root, pack_id)

    def test_existing_wuxia_pack_matches_base_branch_hashes(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        diff = subprocess.run(
            ["git", "diff", "--quiet", "origin/codex/shared-art-resource-catalog", "--", "resource-packs/ink-wuxia-icons-vfx-v1"],
            cwd=repository,
            check=False,
        )
        self.assertEqual(0, diff.returncode)

    def test_validator_cli_runs_from_repository_root(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["python", "tools/validate_resource_packs.py"],
            cwd=repository,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
