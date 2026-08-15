#!/usr/bin/env python3
"""Validate links, JSON syntax, and cross-template contracts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
EXCLUDED_ROOT_FILES = {"task_plan.md", "findings.md", "progress.md"}
EXCLUDED_DIR_PARTS = {".git", "__pycache__", "build"}
REQUIRED_PATHS = (
    "LICENSE",
    "README.md",
    "CONTRIBUTING.md",
    "docs/map-scene-pipeline.md",
    "docs/building-occlusion.md",
    "docs/skill-presentation.md",
    "docs/character-monster-sprites.md",
    "docs/ui-cross-platform.md",
    "docs/art-production.md",
    "docs/quality-gates.md",
    "templates/art-asset-manifest.template.json",
    "templates/map-authoring-spec.template.json",
    "templates/building-occlusion.template.json",
    "templates/skill-definition.template.json",
    "templates/skill-presentation.template.json",
    "templates/sprite-animation-manifest.template.json",
    "templates/ui-layout-profile.template.json",
)


def iter_published_files(pattern: str) -> Iterable[Path]:
    for path in sorted(ROOT.rglob(pattern)):
        relative = path.relative_to(ROOT)
        if relative.as_posix() in EXCLUDED_ROOT_FILES:
            continue
        if relative.parts[:2] == ("docs", "plans"):
            continue
        if any(part in EXCLUDED_DIR_PARTS for part in relative.parts):
            continue
        yield path


def markdown_without_fenced_code(text: str) -> str:
    sections = text.split("```")
    return "".join(section for index, section in enumerate(sections) if index % 2 == 0)


def validate_required_paths(errors: list[str]) -> None:
    for relative_path in REQUIRED_PATHS:
        if not (ROOT / relative_path).is_file():
            errors.append(f"missing required file: {relative_path}")


def require_keys(
    errors: list[str], data: Any, keys: set[str], context: str
) -> bool:
    if not isinstance(data, dict):
        errors.append(f"{context} must be an object")
        return False
    missing = sorted(keys - data.keys())
    if missing:
        errors.append(f"{context} missing keys: {', '.join(missing)}")
        return False
    return True


def load_json_templates(errors: list[str]) -> dict[str, dict[str, Any]]:
    templates: dict[str, dict[str, Any]] = {}
    for path in iter_published_files("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
            continue
        if path.parent.name != "templates":
            continue
        relative = path.relative_to(ROOT).as_posix()
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            errors.append(f"unsupported or missing schema_version in {relative}")
            continue
        templates[path.name] = data
    return templates


def validate_map_template(errors: list[str], data: dict[str, Any]) -> None:
    require_keys(
        errors,
        data,
        {"metadata", "coordinate_system", "regions", "spawn_points", "route", "visual_profiles"},
        "map template",
    )
    coordinate = data.get("coordinate_system", {})
    if require_keys(
        errors,
        coordinate,
        {"grid_size", "tile_world_size", "bounds_grid_format", "terrain_chunk_size_unit"},
        "map coordinate_system",
    ):
        if coordinate["bounds_grid_format"] != ["x", "y", "width", "height"]:
            errors.append("map bounds_grid_format must be [x, y, width, height]")
    grid_size = coordinate.get("grid_size", []) if isinstance(coordinate, dict) else []
    if not (
        isinstance(grid_size, list)
        and len(grid_size) == 2
        and all(isinstance(value, int) and value > 0 for value in grid_size)
    ):
        errors.append("map grid_size must contain two positive integers")
        return
    grid_width, grid_height = grid_size
    regions = data.get("regions", [])
    if not isinstance(regions, list):
        errors.append("map regions must be an array")
        return
    for index, region in enumerate(regions):
        bounds = region.get("bounds_grid", []) if isinstance(region, dict) else []
        region_id = region.get("id", index) if isinstance(region, dict) else index
        if not (
            isinstance(bounds, list)
            and len(bounds) == 4
            and all(isinstance(value, int) for value in bounds)
        ):
            errors.append(f"map region {region_id} requires integer [x, y, width, height]")
            continue
        x, y, width, height = bounds
        if x < 0 or y < 0 or width <= 0 or height <= 0:
            errors.append(f"map region {region_id} has invalid bounds {bounds}")
        elif x + width > grid_width or y + height > grid_height:
            errors.append(f"map region {region_id} exceeds grid_size {grid_size}")


def validate_building_template(errors: list[str], data: dict[str, Any]) -> None:
    profiles = data.get("profiles", {})
    if not isinstance(profiles, dict) or not profiles:
        errors.append("building template requires at least one profile")
        return
    for profile_id, profile in profiles.items():
        require_keys(
            errors,
            profile,
            {"visual", "footprint", "interaction", "occlusion"},
            f"building profile {profile_id}",
        )


def validate_sprite_template(errors: list[str], data: dict[str, Any]) -> None:
    required_actions = {"idle", "walk", "attack", "hit", "death"}
    actions = data.get("actions", {})
    if not isinstance(actions, dict):
        errors.append("sprite actions must be an object")
        return
    missing_actions = sorted(required_actions - actions.keys())
    if missing_actions:
        errors.append(f"sprite template missing actions: {', '.join(missing_actions)}")
    for action_id, action in actions.items():
        if "event_frame" in action and action.get("event_frame_index_base") not in (0, 1):
            errors.append(f"sprite action {action_id} must declare event_frame_index_base")
    aliases = data.get("action_aliases", {})
    if not isinstance(aliases, dict):
        errors.append("sprite action_aliases must be an object")
        return
    for alias, target in aliases.items():
        if target not in actions:
            errors.append(f"sprite action alias {alias} targets missing action {target}")


def validate_skill_templates(
    errors: list[str], definition: dict[str, Any], presentation: dict[str, Any], sprite: dict[str, Any]
) -> None:
    skills = definition.get("skills", {})
    profiles = presentation.get("profiles", {})
    if not isinstance(skills, dict) or not skills:
        errors.append("skill definition template requires skills")
        return
    if not isinstance(profiles, dict) or not profiles:
        errors.append("skill presentation template requires profiles")
        return
    for skill_id, skill in skills.items():
        presentation_id = skill.get("presentation_id") if isinstance(skill, dict) else None
        if presentation_id not in profiles:
            errors.append(f"skill {skill_id} references missing presentation {presentation_id}")
    for profile_id, profile in profiles.items():
        fallback_id = profile.get("fallback_profile") if isinstance(profile, dict) else None
        if fallback_id and fallback_id not in profiles:
            errors.append(f"presentation {profile_id} references missing fallback {fallback_id}")
    for start_id in profiles:
        visited: set[str] = set()
        current_id = start_id
        while current_id in profiles:
            if current_id in visited:
                errors.append(f"presentation fallback cycle starts at {start_id}")
                break
            visited.add(current_id)
            current_profile = profiles[current_id]
            current_id = str(current_profile.get("fallback_profile", ""))
            if not current_id:
                break
    actions = sprite.get("actions", {})
    aliases = sprite.get("action_aliases", {})
    supported_actions = set(actions) | set(aliases)
    for profile_id, profile in profiles.items():
        action = profile.get("action") if isinstance(profile, dict) else None
        if action and action not in supported_actions:
            errors.append(f"presentation {profile_id} uses unsupported action {action}")
    event_contract = presentation.get("event_contract", {})
    required_event_fields = {"event_id", "event_seq", "cast_instance_id", "phase"}
    configured_fields = set(event_contract.get("required_fields", []))
    if not required_event_fields.issubset(configured_fields):
        errors.append("skill event contract is missing identity or ordering fields")
    if event_contract.get("deduplicate_by") != "event_id":
        errors.append("skill event contract must deduplicate by event_id")


def validate_ui_template(errors: list[str], data: dict[str, Any]) -> None:
    semantic_values = set(data.get("semantic_controls", {}).values())
    profiles = data.get("profiles", {})
    if not semantic_values or not isinstance(profiles, dict):
        errors.append("UI template requires semantic_controls and profiles")
        return
    for profile_id, profile in profiles.items():
        controls = profile.get("controls", {}) if isinstance(profile, dict) else {}
        missing_controls = sorted(semantic_values - controls.keys())
        if missing_controls:
            errors.append(f"UI profile {profile_id} missing controls: {', '.join(missing_controls)}")
        for control_id, geometry in controls.items():
            if geometry.get("visible", True) is False:
                continue
            require_keys(
                errors,
                geometry,
                {"anchor", "offset", "visual_size", "hit_size", "z_order"},
                f"UI control {profile_id}.{control_id}",
            )


def validate_art_template(errors: list[str], data: dict[str, Any]) -> None:
    require_keys(
        errors,
        data,
        {"asset_id", "category", "status", "version", "source", "files", "processing", "integrity", "acceptance"},
        "art asset template",
    )


def validate_template_contracts(
    errors: list[str], templates: dict[str, dict[str, Any]]
) -> None:
    try:
        map_data = templates["map-authoring-spec.template.json"]
        building_data = templates["building-occlusion.template.json"]
        definition_data = templates["skill-definition.template.json"]
        presentation_data = templates["skill-presentation.template.json"]
        sprite_data = templates["sprite-animation-manifest.template.json"]
        ui_data = templates["ui-layout-profile.template.json"]
        art_data = templates["art-asset-manifest.template.json"]
    except KeyError:
        return
    validate_map_template(errors, map_data)
    validate_building_template(errors, building_data)
    validate_sprite_template(errors, sprite_data)
    validate_skill_templates(errors, definition_data, presentation_data, sprite_data)
    validate_ui_template(errors, ui_data)
    validate_art_template(errors, art_data)


def validate_markdown_links(errors: list[str]) -> None:
    for path in iter_published_files("*.md"):
        text = markdown_without_fenced_code(path.read_text(encoding="utf-8"))
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            file_part = unquote(target.split("#", 1)[0])
            if not file_part:
                continue
            resolved = (path.parent / file_part).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(f"link escapes repository: {path.relative_to(ROOT)} -> {target}")
                continue
            if not resolved.exists():
                errors.append(f"broken link: {path.relative_to(ROOT)} -> {target}")


def main() -> int:
    errors: list[str] = []
    validate_required_paths(errors)
    templates = load_json_templates(errors)
    validate_template_contracts(errors, templates)
    validate_markdown_links(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Validation failed with {len(errors)} error(s).")
        return 1
    markdown_count = sum(1 for _ in iter_published_files("*.md"))
    json_count = sum(1 for _ in iter_published_files("*.json"))
    print(
        f"Validation passed: {markdown_count} published Markdown files, "
        f"{json_count} JSON files, cross-template contracts valid."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
