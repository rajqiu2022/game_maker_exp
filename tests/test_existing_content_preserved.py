from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "origin/codex/shared-art-resource-catalog"
LEGACY_PACK = "resource-packs/ink-wuxia-icons-vfx-v1"
NEW_PACKS = ("fantasy-rpg-icons-vfx-v1", "rpg-ui-kit-v1")
FORBIDDEN_SUFFIXES = {".import", ".pyc", ".pck", ".apk", ".exe", ".zip"}
FORBIDDEN_PARTS = {
    "source",
    "reference",
    "references",
    "raw",
    "private",
    "cache",
    "candidate",
    "candidates",
    "build",
    "exports",
    ".godot",
    "__pycache__",
}
MACHINE_PATH = re.compile(r"[A-Za-z]:[/\\\\](?:Users|code)[/\\\\]", re.IGNORECASE)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, capture_output=True, encoding="utf-8"
    )


def tree_blobs(revision: str, prefix: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in git("ls-tree", "-r", revision, "--", prefix).stdout.splitlines():
        metadata, path = line.split("\t", 1)
        result[path] = metadata.split()[2]
    return result


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ExistingContentPreservedContracts(unittest.TestCase):
    def test_existing_wuxia_pack_matches_base_branch_blob_hashes(self) -> None:
        self.assertEqual(tree_blobs(BASE, LEGACY_PACK), tree_blobs("HEAD", LEGACY_PACK))
        diff = git("diff", "--name-only", BASE, "--", LEGACY_PACK).stdout.strip()
        self.assertEqual("", diff)

    def test_new_pack_paths_do_not_collide_with_existing_pack(self) -> None:
        legacy = {path.relative_to(ROOT).as_posix() for path in (ROOT / LEGACY_PACK).rglob("*") if path.is_file()}
        new_paths: set[str] = set()
        for pack_id in NEW_PACKS:
            pack = ROOT / "resource-packs" / pack_id
            self.assertTrue(pack.is_dir())
            current = {path.relative_to(ROOT).as_posix() for path in pack.rglob("*") if path.is_file()}
            self.assertFalse(legacy & current)
            self.assertFalse(new_paths & current)
            new_paths.update(current)

    def test_no_forbidden_extensions_machine_paths_or_private_dirs_in_packs(self) -> None:
        for path in sorted((ROOT / "resource-packs").rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT / "resource-packs")
            self.assertFalse(FORBIDDEN_PARTS.intersection(part.casefold() for part in relative.parts), relative)
            self.assertNotIn(path.suffix.casefold(), FORBIDDEN_SUFFIXES, relative)
            if path.suffix.casefold() in {".md", ".json", ""}:
                self.assertIsNone(MACHINE_PATH.search(path.read_text(encoding="utf-8")), relative)

    def test_generated_files_are_reproducible(self) -> None:
        generated = []
        for pack_id in NEW_PACKS:
            pack = ROOT / "resource-packs" / pack_id
            generated.extend([pack / "manifest.json", pack / "CATALOG.md", pack / "SHA256SUMS"])
            generated.extend(sorted((pack / "previews").rglob("*.webp")))
        before = {path: file_hash(path) for path in generated}
        subprocess.run(
            [sys.executable, "tools/build_resource_pack.py", "--all"], cwd=ROOT, check=True
        )
        after = {path: file_hash(path) for path in generated}
        self.assertEqual(before, after)

    def test_base_content_is_not_deleted_or_renamed(self) -> None:
        changed = git("diff", "--name-status", f"{BASE}...HEAD").stdout.splitlines()
        destructive = [line for line in changed if line.startswith(("D\t", "R"))]
        self.assertEqual([], destructive)

    def test_contribution_rules_document_non_destructive_asset_publishing(self) -> None:
        text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        for phrase in ("no-clobber", "LICENSE-ASSETS.md", "禁止静默覆盖", "`.import`"):
            self.assertIn(phrase, text)

    def test_ci_fetches_the_preservation_test_baseline(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn(
            "codex/shared-art-resource-catalog:refs/remotes/origin/codex/shared-art-resource-catalog",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
