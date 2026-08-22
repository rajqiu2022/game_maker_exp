# 幻想 RPG 图标与战斗特效 v1

面向获授权游戏项目复用的无文字运行时 PNG 包，包含技能图标、通用物品图标、单段战斗特效、四阶段特效和暗影刀光特效。

## 内容

- 23 个 256×256 RGBA 技能图标。
- 36 个 64/128 方形通用物品图标。
- 24 个通用单段战斗 VFX。
- 5 个按左上、右上、左下、右下排列的四阶段 VFX 图集。
- 7 个正式暗影近战 VFX。

资源使用跨项目语义 ID，不保留地图名、装备等级或内部业务标识。完整规格见 `manifest.json`，可视目录见 `CATALOG.md`，文件摘要见 `SHA256SUMS`。

## 使用方式

1. 根据 `asset_id` 选择语义匹配项，不依赖源文件名。
2. 图标按 `recommended_display_size` 接入统一槽位。
3. 单段 VFX 以中心锚点播放；四阶段图集按 manifest 的 `frame_order` 切分。
4. 先复制到采用项目自己的资源目录，再在项目适配层绑定引擎路径。
5. 导入时禁止用不同内容覆盖已有目标文件。

## 授权

根仓库 MIT 不覆盖本包 PNG/WebP。使用前阅读 [LICENSE-ASSETS.md](LICENSE-ASSETS.md)。

## 生成与校验

```powershell
python tools/build_resource_pack.py --pack fantasy-rpg-icons-vfx-v1
python tools/validate_resource_packs.py --pack fantasy-rpg-icons-vfx-v1
```

`manifest.json`、`CATALOG.md`、`SHA256SUMS` 和 `previews/` 为确定性生成物，请勿手工修改。
