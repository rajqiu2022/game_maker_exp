from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.import_selected_assets import (
    compose_2x2_no_clobber,
    copy_no_clobber,
    import_selection,
    safe_relative,
)


class SafeResourceImportTests(unittest.TestCase):
    def make_png(
        self,
        path: Path,
        color: tuple[int, int, int, int],
        size: tuple[int, int] = (8, 8),
        mode: str = "RGBA",
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new(mode, size, color if mode == "RGBA" else color[:3])
        image.save(path)

    def test_import_copies_missing_file_and_preserves_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "source" / "game" / "art" / "icon.png"
            destination = root / "repository" / "resource-packs" / "demo" / "icons" / "icon.png"
            self.make_png(source, (200, 30, 40, 255))
            expected = source.read_bytes()

            result = copy_no_clobber(source, destination)

            self.assertEqual("created", result)
            self.assertEqual(expected, destination.read_bytes())
            self.assertEqual(expected, source.read_bytes())

    def test_import_accepts_identical_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "source.png"
            destination = root / "destination.png"
            self.make_png(source, (20, 100, 220, 255))
            destination.write_bytes(source.read_bytes())

            self.assertEqual("identical", copy_no_clobber(source, destination))

    def test_import_rejects_different_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "source.png"
            destination = root / "destination.png"
            self.make_png(source, (255, 0, 0, 255))
            self.make_png(destination, (0, 0, 255, 255))
            original = destination.read_bytes()

            with self.assertRaisesRegex(FileExistsError, "different content"):
                copy_no_clobber(source, destination)

            self.assertEqual(original, destination.read_bytes())

    def test_import_rejects_absolute_or_parent_traversal_paths(self) -> None:
        invalid = ["../secret.png", "icons/../../secret.png", "C:/Users/me/secret.png", "/tmp/secret.png"]
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    safe_relative(value)

    def test_import_rejects_forbidden_source_parts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source_root = root / "source"
            repository_root = root / "repository"
            selection = root / "selection.json"
            self.make_png(source_root / "game" / "art" / "source" / "icon.png", (10, 20, 30, 255))
            selection.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "pack_id": "demo",
                        "entries": [
                            {
                                "asset_id": "icon_test",
                                "kind": "skill_icon",
                                "source": "game/art/source/icon.png",
                                "destination": "icons/skills/icon_test.png",
                                "operation": "copy",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "forbidden source path"):
                import_selection(source_root, repository_root, selection)

    def test_import_rejects_unpublished_source_and_private_paths(self) -> None:
        forbidden = [
            "game/art/reference/icon.png",
            "game/art/references/icon.png",
            "game/art/raw/icon.png",
            "game/art/private/icon.png",
            "game/art/cache/icon.png",
            "game/art/candidates/icon.png",
            "game/art/icons/icon_source.png",
            "game/art/icons/icon_reference.png",
        ]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source_root = root / "source"
            repository_root = root / "repository"
            selection = root / "selection.json"
            for index, source_path in enumerate(forbidden):
                with self.subTest(source_path=source_path):
                    self.make_png(source_root / source_path, (10 + index, 20, 30, 255))
                    selection.write_text(
                        json.dumps(
                            {
                                "schema_version": 1,
                                "pack_id": "demo",
                                "entries": [
                                    {
                                        "asset_id": f"icon_test_{index}",
                                        "kind": "skill_icon",
                                        "source": source_path,
                                        "destination": f"icons/skills/icon_test_{index}.png",
                                        "operation": "copy",
                                    }
                                ],
                            }
                        ),
                        encoding="utf-8",
                    )

                    with self.assertRaisesRegex(ValueError, "forbidden source path"):
                        import_selection(source_root, repository_root, selection)

    def test_compose_2x2_requires_four_equal_rgba_frames(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            frames = []
            for index in range(3):
                frame = root / f"frame_{index}.png"
                self.make_png(frame, (index * 30, 40, 50, 255))
                frames.append(frame)

            with self.assertRaisesRegex(ValueError, "exactly four"):
                compose_2x2_no_clobber(frames, root / "sheet.png")

            fourth = root / "frame_3.png"
            self.make_png(fourth, (90, 40, 50, 255), mode="RGB")
            with self.assertRaisesRegex(ValueError, "RGBA"):
                compose_2x2_no_clobber(frames + [fourth], root / "sheet.png")

    def test_compose_2x2_uses_row_major_order_without_touching_sources(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            colors = [
                (255, 0, 0, 255),
                (0, 255, 0, 255),
                (0, 0, 255, 255),
                (255, 255, 0, 255),
            ]
            frames = []
            hashes = []
            for index, color in enumerate(colors):
                frame = root / f"frame_{index}.png"
                self.make_png(frame, color)
                frames.append(frame)
                hashes.append(hashlib.sha256(frame.read_bytes()).hexdigest())

            result = compose_2x2_no_clobber(frames, root / "sheet.png")

            self.assertEqual("created", result)
            with Image.open(root / "sheet.png") as sheet:
                self.assertEqual((16, 16), sheet.size)
                self.assertEqual(colors[0], sheet.getpixel((4, 4)))
                self.assertEqual(colors[1], sheet.getpixel((12, 4)))
                self.assertEqual(colors[2], sheet.getpixel((4, 12)))
                self.assertEqual(colors[3], sheet.getpixel((12, 12)))
            self.assertEqual(hashes, [hashlib.sha256(path.read_bytes()).hexdigest() for path in frames])


if __name__ == "__main__":
    unittest.main()
