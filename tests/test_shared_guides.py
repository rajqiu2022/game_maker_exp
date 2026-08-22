from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

GUIDES = (
    "multiplayer-authority.md",
    "runtime-performance.md",
    "equipment-progression.md",
    "cross-platform-release.md",
    "audio-feedback.md",
    "resource-pack-governance.md",
)
TEMPLATES = (
    "network-state-envelope.template.json",
    "performance-budget.template.json",
    "equipment-route.template.json",
    "release-profile.template.json",
    "audio-presentation.template.json",
    "resource-pack.template.json",
)
CHECKLISTS = (
    "multiplayer-release.md",
    "performance-release.md",
    "equipment-progression.md",
    "cross-platform-release.md",
    "audio-release.md",
)
REQUIRED_GUIDE_HEADINGS = (
    "## 问题",
    "## 适用边界",
    "## 常见失败",
    "## 自动检查",
    "## 人工检查",
    "## 验收标准",
    "### 最低验收",
    "### 正式验收",
)
FORBIDDEN_PUBLIC_PATTERNS = (
    re.compile(r"[A-Za-z]:[/\\\\]"),
    re.compile(r"Users[/\\\\]", re.IGNORECASE),
    re.compile(r"codex/[-\w]+", re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|access[_-]?token|secret)\s*[:=]", re.IGNORECASE),
)


class SharedGuideContracts(unittest.TestCase):
    def test_all_guides_templates_and_checklists_exist(self) -> None:
        expected = (
            *(ROOT / "docs" / name for name in GUIDES),
            *(ROOT / "templates" / name for name in TEMPLATES),
            *(ROOT / "checklists" / name for name in CHECKLISTS),
        )
        missing = [path.relative_to(ROOT).as_posix() for path in expected if not path.is_file()]
        self.assertEqual([], missing)

    def test_templates_are_versioned_json_objects(self) -> None:
        for name in TEMPLATES:
            with self.subTest(template=name):
                data = json.loads((ROOT / "templates" / name).read_text(encoding="utf-8"))
                self.assertIsInstance(data, dict)
                self.assertIsInstance(data.get("schema_version"), int)

    def test_guides_have_operational_acceptance_sections(self) -> None:
        for name in GUIDES:
            with self.subTest(guide=name):
                text = (ROOT / "docs" / name).read_text(encoding="utf-8")
                for heading in REQUIRED_GUIDE_HEADINGS:
                    self.assertIn(heading, text)

    def test_public_guides_do_not_leak_local_or_project_only_values(self) -> None:
        for name in GUIDES:
            with self.subTest(guide=name):
                text = (ROOT / "docs" / name).read_text(encoding="utf-8")
                for pattern in FORBIDDEN_PUBLIC_PATTERNS:
                    self.assertIsNone(pattern.search(text), pattern.pattern)

    def test_readme_links_every_new_guide(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for name in GUIDES:
            self.assertIn(f"docs/{name}", readme)

    def test_case_study_keeps_project_values_out_of_public_rules(self) -> None:
        text = (ROOT / "case-studies" / "rpg-map-production-lessons.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("项目参数不是通用规则", text)
        self.assertIn("权威状态", text)
        self.assertIn("过渡装备", text)
        self.assertIn("发布闭包", text)


if __name__ == "__main__":
    unittest.main()
