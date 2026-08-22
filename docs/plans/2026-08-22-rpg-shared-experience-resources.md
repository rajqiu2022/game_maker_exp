# RPG Shared Experience And Resource Packs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Preserve the existing playbook and wuxia pack while adding reusable RPG production guides, a fantasy icon/VFX pack, and a cross-platform UI pack with collision-safe imports and reproducible validation.

**Architecture:** Work on `codex/rpg-shared-resources-v1`, based on `origin/codex/shared-art-resource-catalog`. A committed selection spec maps project-relative source files to cross-project semantic destinations; a no-clobber importer copies only approved runtime files and composes staged VFX sheets; generic pack tooling generates manifests, catalogues, previews, and checksums. Existing resource-pack files remain byte-for-byte unchanged.

**Tech Stack:** Python 3.9+, Pillow, `unittest`, JSON, Markdown, Git, GitHub Actions.

---

## Global constraints

- Read source assets from `D:/code/rpg_map` but never modify that working tree.
- Do not publish `.import`, `source/`, build output, audio, fonts, character/monster/map art, absolute paths, secrets, or rejected assets.
- Do not change any file under `resource-packs/ink-wuxia-icons-vfx-v1/`.
- Every destination write must be no-clobber: missing is allowed, identical is idempotent, different content is an error.
- Run the focused test before implementation, after implementation, and before each commit.
- Push normally to `origin/codex/rpg-shared-resources-v1`; never force push.

### Task 1: Add a collision-safe selected-asset importer

**Files:**

- Create: `tests/test_safe_resource_import.py`
- Create: `tools/import_selected_assets.py`

**Step 1: Write the failing importer tests**

Cover these contracts with temporary directories:

```python
def test_import_copies_missing_file_and_preserves_bytes(): ...
def test_import_accepts_identical_existing_file(): ...
def test_import_rejects_different_existing_file(): ...
def test_import_rejects_absolute_or_parent_traversal_paths(): ...
def test_import_rejects_forbidden_source_parts(): ...
def test_compose_2x2_requires_four_equal_rgba_frames(): ...
def test_compose_2x2_uses_row_major_order_without_touching_sources(): ...
```

Use a minimal selection document:

```json
{
  "schema_version": 1,
  "pack_id": "test_pack",
  "entries": [
    {
      "asset_id": "icon_test",
      "kind": "skill_icon",
      "source": "game/art/icon.png",
      "destination": "icons/skills/icon_test.png",
      "operation": "copy"
    }
  ]
}
```

**Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m unittest tests.test_safe_resource_import -v
```

Expected: import failure because `tools.import_selected_assets` does not exist.

**Step 3: Implement the minimal importer**

Implement:

```python
FORBIDDEN_PARTS = {"source", "build", "exports", ".godot", "__pycache__"}

def safe_relative(value: str) -> Path: ...
def copy_no_clobber(source: Path, destination: Path) -> str: ...
def compose_2x2_no_clobber(sources: list[Path], destination: Path) -> str: ...
def import_selection(source_root: Path, repository_root: Path, selection_path: Path) -> dict: ...
```

CLI:

```powershell
python tools/import_selected_assets.py --source-root D:/code/rpg_map --selection specs/resource-packs/example.json
```

The summary must report `created`, `identical`, and `rejected`; no overwrite flag is provided.

**Step 4: Run tests and repository validation**

Run:

```powershell
python -m unittest tests.test_safe_resource_import -v
python tools/validate_repository.py
```

Expected: all tests pass and the existing repository remains valid.

**Step 5: Commit**

```powershell
git add tests/test_safe_resource_import.py tools/import_selected_assets.py
git commit -m "tool: add collision-safe resource importer"
```

### Task 2: Generalize resource-pack build and validation tooling

**Files:**

- Create: `tests/test_resource_pack_pipeline.py`
- Create: `tools/build_resource_pack.py`
- Create: `tools/validate_resource_packs.py`
- Modify: `.github/workflows/validate.yml`

**Step 1: Write failing pack-pipeline tests**

Create temporary packs and assert:

```python
def test_builder_generates_manifest_catalog_checksums_and_previews(): ...
def test_builder_supports_icon_single_vfx_sheet_and_ui_component(): ...
def test_validator_rejects_orphan_binary(): ...
def test_validator_rejects_duplicate_id_path_or_hash(): ...
def test_validator_rejects_import_source_build_and_sensitive_paths(): ...
def test_validator_rejects_missing_license_or_provenance(): ...
def test_validator_checks_ui_safe_area_and_stretch_contract(): ...
def test_existing_wuxia_pack_is_unchanged_and_still_valid(): ...
```

The pack source of truth is `pack-spec.json`; generated files are `manifest.json`, `CATALOG.md`, `SHA256SUMS`, and `previews/`.

**Step 2: Run and verify RED**

```powershell
python -m unittest tests.test_resource_pack_pipeline -v
```

Expected: missing generic builder and validator modules.

**Step 3: Implement generic build contracts**

`tools/build_resource_pack.py` must:

- load `resource-packs/<pack-id>/pack-spec.json`;
- inspect real image dimensions/mode/alpha and compute file/pixel SHA-256;
- support `skill_icon`, `item_icon`, `vfx_single`, `vfx_sheet`, and `ui_component`;
- generate static WebP previews and animated WebP for 2×2 sheets;
- create deterministic Markdown and checksum output;
- reject unlisted binaries before writing generated files.

`tools/validate_resource_packs.py` must discover packs containing `pack-spec.json`, validate all generated output, and invoke the legacy validator for the unchanged wuxia pack.

**Step 4: Update CI and run tests**

Add:

```yaml
- run: python -m unittest discover -s tests -v
- run: python tools/validate_resource_packs.py
```

Run:

```powershell
python -m unittest tests.test_resource_pack_pipeline -v
python tools/validate_resource_pack.py
python tools/validate_resource_packs.py
python tools/validate_repository.py
```

Expected: all commands return zero and the original pack hashes remain unchanged.

**Step 5: Commit**

```powershell
git add tests/test_resource_pack_pipeline.py tools/build_resource_pack.py tools/validate_resource_packs.py .github/workflows/validate.yml
git commit -m "tool: generalize reusable resource pack validation"
```

### Task 3: Add missing reusable production guides

**Files:**

- Create: `docs/multiplayer-authority.md`
- Create: `docs/runtime-performance.md`
- Create: `docs/equipment-progression.md`
- Create: `docs/cross-platform-release.md`
- Create: `docs/audio-feedback.md`
- Create: `docs/resource-pack-governance.md`
- Create: `templates/network-state-envelope.template.json`
- Create: `templates/performance-budget.template.json`
- Create: `templates/equipment-route.template.json`
- Create: `templates/release-profile.template.json`
- Create: `templates/audio-presentation.template.json`
- Create: `templates/resource-pack.template.json`
- Create: `checklists/multiplayer-release.md`
- Create: `checklists/performance-release.md`
- Create: `checklists/equipment-progression.md`
- Create: `checklists/cross-platform-release.md`
- Create: `checklists/audio-release.md`
- Create: `tests/test_shared_guides.py`
- Modify: `README.md`
- Modify: `docs/adoption-guide.md`
- Modify: `docs/quality-gates.md`
- Modify: `case-studies/rpg-map-production-lessons.md`

**Step 1: Write failing documentation contracts**

Tests must require:

- every new guide, template, and checklist exists;
- every JSON template parses and has integer `schema_version`;
- README links resolve;
- every guide includes problem, boundaries, failure modes, automated checks, manual checks, and minimum/formal acceptance;
- public guides contain no `D:/`, user profile, internal branch, token, or project-only resource ID;
- the RPG case study records concrete lessons without presenting project values as universal rules.

**Step 2: Run and verify RED**

```powershell
python -m unittest tests.test_shared_guides -v
```

Expected: missing documents and templates.

**Step 3: Write the six guides and neutral templates**

Required content:

- Multiplayer: command/request/result/state/presentation/local-UI boundaries, revisions, dedupe, reconnect limits.
- Performance: frame budgets, spawn batching, interest activation, path budgets, cache ownership, profiling evidence.
- Equipment: class compatibility, non-destructive pickup rejection, transition tiers, recommendation routes, authoritative inventory.
- Release: platform manifests, map-scoped compatibility, resource closure, package audit, device smoke tests.
- Audio: semantic events, cast/hit split, overlap throttles, priority, fallback, remote playback dedupe.
- Governance: semantic IDs, provenance, rights, no-clobber imports, generated catalogues, versioning, adoption reports.

**Step 4: Run link, JSON, and repository checks**

```powershell
python -m unittest tests.test_shared_guides -v
python tools/validate_repository.py
```

Expected: all documents and links pass.

**Step 5: Commit**

```powershell
git add README.md docs templates checklists case-studies tests/test_shared_guides.py
git commit -m "docs: add multiplayer performance progression and release guides"
```

### Task 4: Build the fantasy RPG icon and VFX pack

**Files:**

- Create: `specs/resource-packs/fantasy-rpg-icons-vfx-v1.json`
- Create: `resource-packs/fantasy-rpg-icons-vfx-v1/pack-spec.json`
- Create: `resource-packs/fantasy-rpg-icons-vfx-v1/README.md`
- Create: `resource-packs/fantasy-rpg-icons-vfx-v1/LICENSE-ASSETS.md`
- Generate: `resource-packs/fantasy-rpg-icons-vfx-v1/icons/**`
- Generate: `resource-packs/fantasy-rpg-icons-vfx-v1/vfx/**`
- Generate: `resource-packs/fantasy-rpg-icons-vfx-v1/previews/**`
- Generate: `resource-packs/fantasy-rpg-icons-vfx-v1/manifest.json`
- Generate: `resource-packs/fantasy-rpg-icons-vfx-v1/CATALOG.md`
- Generate: `resource-packs/fantasy-rpg-icons-vfx-v1/SHA256SUMS`
- Create: `tests/test_fantasy_rpg_pack.py`

**Step 1: Write failing pack-selection tests**

Lock the approved inventory:

- 23 `256x256 RGBA` skill icons;
- 36 generic item icons;
- 24 single-stage VFX;
- five composed 2×2 staged VFX sheets;
- seven formal assassin VFX;
- total 95 manifest entries.

Tests must reject `_source`, `.import`, RGB-only icons, 96x96 icons, assassin V2, duplicate base phase images, `unknown`, `frontier`, class-tier IDs, and absolute source paths.

**Step 2: Run and verify RED**

```powershell
python -m unittest tests.test_fantasy_rpg_pack -v
```

Expected: selection spec and pack do not exist.

**Step 3: Create the exact selection and metadata specs**

Use cross-project destinations such as:

```text
icons/skills/elemental/icon_arcane_missile.png
icons/items/consumables/item_health_potion_small.png
vfx/elemental/vfx_frost_nova_single.png
vfx/marks/vfx_hunter_mark_4frame_v1.png
vfx/assassin/vfx_shadow_arc_single.png
```

Map the four phase files in row-major order for each staged VFX. Do not store `D:/code/rpg_map` in the spec.

**Step 4: Import and generate the pack**

```powershell
python tools/import_selected_assets.py --source-root D:/code/rpg_map --selection specs/resource-packs/fantasy-rpg-icons-vfx-v1.json
python tools/build_resource_pack.py --pack fantasy-rpg-icons-vfx-v1
```

Expected: only missing files are created; source files remain unchanged.

**Step 5: Validate focused and full contracts**

```powershell
python -m unittest tests.test_fantasy_rpg_pack -v
python tools/validate_resource_packs.py --pack fantasy-rpg-icons-vfx-v1
python tools/validate_repository.py
```

Expected: 95 entries, no orphan/duplicate/forbidden files, zero errors.

**Step 6: Commit**

```powershell
git add specs/resource-packs/fantasy-rpg-icons-vfx-v1.json resource-packs/fantasy-rpg-icons-vfx-v1 tests/test_fantasy_rpg_pack.py
git commit -m "assets: add reusable fantasy RPG icon and VFX pack"
```

### Task 5: Build the cross-platform RPG UI Kit pack

**Files:**

- Create: `specs/resource-packs/rpg-ui-kit-v1.json`
- Create: `resource-packs/rpg-ui-kit-v1/pack-spec.json`
- Create: `resource-packs/rpg-ui-kit-v1/README.md`
- Create: `resource-packs/rpg-ui-kit-v1/LICENSE-ASSETS.md`
- Generate: `resource-packs/rpg-ui-kit-v1/ui/**`
- Generate: `resource-packs/rpg-ui-kit-v1/previews/**`
- Generate: `resource-packs/rpg-ui-kit-v1/manifest.json`
- Generate: `resource-packs/rpg-ui-kit-v1/CATALOG.md`
- Generate: `resource-packs/rpg-ui-kit-v1/SHA256SUMS`
- Create: `tests/test_rpg_ui_pack.py`

**Step 1: Write failing UI-pack contracts**

Require exactly:

- 42 core UI Kit components;
- 12 mobile controls;
- eight HUD components;
- total 62 manifest entries.

Each entry must provide semantic ID, category, source dimensions, platform list, stretch mode, content-safe margins, recommended visible size, and recommended touch target when interactive.

**Step 2: Run and verify RED**

```powershell
python -m unittest tests.test_rpg_ui_pack -v
```

Expected: UI selection and pack are absent.

**Step 3: Create specs and import without overwrite**

Use categories:

```text
ui/core/buttons/
ui/core/panels/
ui/core/slots/
ui/core/meters/
ui/mobile/controls/
ui/hud/status/
```

Run:

```powershell
python tools/import_selected_assets.py --source-root D:/code/rpg_map --selection specs/resource-packs/rpg-ui-kit-v1.json
python tools/build_resource_pack.py --pack rpg-ui-kit-v1
```

**Step 4: Validate responsive and touch metadata**

```powershell
python -m unittest tests.test_rpg_ui_pack -v
python tools/validate_resource_packs.py --pack rpg-ui-kit-v1
python tools/validate_repository.py
```

Expected: 62 validated entries; interactive mobile controls recommend at least 72x72 logical pixels and visual/touch bounds remain separate.

**Step 5: Commit**

```powershell
git add specs/resource-packs/rpg-ui-kit-v1.json resource-packs/rpg-ui-kit-v1 tests/test_rpg_ui_pack.py
git commit -m "assets: add reusable cross-platform RPG UI kit"
```

### Task 6: Publish adoption mappings without changing game runtime

**Files:**

- Create: `adoption/rpg-map-resource-fit.md`
- Modify: `resource-packs/README.md`
- Modify: `README.md`
- Create: `tests/test_adoption_mapping.py`

**Step 1: Write failing mapping tests**

Require the report to reference existing manifest IDs for:

- assassin dagger, execution, mist combo, wind slash, and shadow step;
- warrior sword, heavy cleave, earth split, and impact;
- guard, healing, inner aura, and redirect;
- iron ore, spirit stone, jade fragment, and herb bundle.

The report must state that no `rpg_map` runtime file is modified and that mappings are recommendations, not automatic replacements.

**Step 2: Run and verify RED**

```powershell
python -m unittest tests.test_adoption_mapping -v
```

Expected: adoption report missing.

**Step 3: Write the mapping and update navigation**

For each recommendation include current use, shared asset ID, semantic fit, adaptation needed, and risk. Link all three packs from `resource-packs/README.md` and the root README.

**Step 4: Validate and commit**

```powershell
python -m unittest tests.test_adoption_mapping -v
python tools/validate_repository.py
git add adoption/rpg-map-resource-fit.md resource-packs/README.md README.md tests/test_adoption_mapping.py
git commit -m "docs: map reusable art packs to RPG use cases"
```

### Task 7: Run full quality gates and protect existing content

**Files:**

- Create: `tests/test_existing_content_preserved.py`
- Modify: `CONTRIBUTING.md`
- Modify: `.github/workflows/validate.yml` only if review finds a missing final command.

**Step 1: Write preservation tests**

Lock the existing pack tree and base commit:

```python
def test_existing_wuxia_pack_matches_base_branch_hashes(): ...
def test_new_pack_paths_do_not_collide_with_existing_pack(): ...
def test_no_forbidden_extensions_or_machine_paths_anywhere_in_packs(): ...
def test_generated_files_are_reproducible(): ...
```

Compare `resource-packs/ink-wuxia-icons-vfx-v1/` against `origin/codex/shared-art-resource-catalog` via Git blob hashes, not timestamps.

**Step 2: Run complete validation**

```powershell
python -m unittest discover -s tests -v
python tools/build_art_resource_catalog.py
python tools/validate_resource_pack.py
python tools/build_resource_pack.py --all
python tools/validate_resource_packs.py
python tools/validate_repository.py
git diff --check
```

Expected: all commands return zero; rebuilding produces no tracked diff.

**Step 3: Audit repository content**

Run:

```powershell
git status --short
git diff --stat origin/codex/shared-art-resource-catalog...HEAD
git diff --name-status origin/codex/shared-art-resource-catalog...HEAD
git diff -- resource-packs/ink-wuxia-icons-vfx-v1
```

Expected: no modifications under the existing pack and no task working files staged.

**Step 4: Update contribution rules and commit**

Document the no-clobber import and pack-specific rights rules in `CONTRIBUTING.md`, then run the full checks again.

```powershell
git add CONTRIBUTING.md tests/test_existing_content_preserved.py .github/workflows/validate.yml
git commit -m "test: enforce non-destructive shared resource publishing"
```

### Task 8: Review, synchronize, and push safely

**Files:**

- Modify: none unless review finds an approved task-scoped issue.

**Step 1: Run completion review**

Use `requesting-code-review` and verify:

- design and implementation plan are satisfied;
- binary selections match approved counts;
- no source/reference/private files were included;
- rights statements are consistent;
- no existing file was overwritten;
- tests validate behavior rather than only source strings.

**Step 2: Re-run final gates after review fixes**

```powershell
python -m unittest discover -s tests -v
python tools/validate_resource_pack.py
python tools/validate_resource_packs.py
python tools/validate_repository.py
git diff --check
git status --short
```

Expected: zero failures and only intentional task working logs remain untracked/ignored.

**Step 3: Synchronize remote without force**

```powershell
git fetch origin
git rev-list --left-right --count origin/codex/shared-art-resource-catalog...HEAD
git push -u origin codex/rpg-shared-resources-v1
```

If the remote base advanced, rebase only when conflict-free. On any content conflict, stop and report instead of choosing or overwriting.

**Step 4: Verify remote branch**

```powershell
git ls-remote --heads origin codex/rpg-shared-resources-v1
git log --oneline --decorate origin/codex/shared-art-resource-catalog..HEAD
```

Expected: the remote branch points at local HEAD and retains the original resource branch history.

**Step 5: Report**

Provide:

- GitHub branch URL;
- commit list;
- pack entry/file counts and sizes;
- test and validation totals;
- reusable mappings;
- excluded-resource reasons;
- confirmation that `rpg_map` and the existing wuxia pack were not modified.

