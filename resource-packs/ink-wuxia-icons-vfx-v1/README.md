# 水墨武侠图标与招式特效 v1

面向 2D、2.5D 与固定视角 RPG 的可复用水墨武侠美术包。资源已经改为跨项目语义 ID，不包含具体游戏角色、门派、剧情名、中文烘焙文字或引擎 `.import` 文件。

## 内容

- 技能语义图标：20 个。
- 物品与线索图标：16 个。
- 四阶段透明招式特效：47 套。
- 由发布图集生成的动态 WebP 预览：47 个。

完整逐项说明、规格与预览见 [资源目录](CATALOG.md)，机器可读数据见 [manifest.json](manifest.json)，文件校验值见 [SHA256SUMS](SHA256SUMS)。

## 目录

```text
icons/
├── skills/{basic,blade,dagger,movement,needle,palm,staff,support,sword}/
└── items/{clues,materials,tokens}/
vfx/
├── attack/{blade,dagger,misc,needle,palm,staff,sword,taiji}/
├── movement/
└── support/{guard,healing,inner,redirect}/
previews/vfx/              与 vfx 目录同构的动态 WebP
manifest.json              规格、内容描述、来源类型与 SHA-256
CATALOG.md                 自动生成的可视化资源目录
SHA256SUMS                 所有 130 个二进制文件校验值
LICENSE-ASSETS.md          美术资源使用边界
```

## 图标规格

- PNG，256×256，RGBA 透明背景。
- 无文字、无 UI 边框；项目自行叠加品质框、冷却遮罩、数量和快捷键。
- 推荐显示尺寸 64–128 px。低于 64 px 时应单独检查刀刃、飞针和书信轮廓是否仍能分辨。
- 四种基础攻击图标按当前武器动态选择；命名招式按剑、刀、棍、掌、针、短刃、身法和辅助语义选择。

## 特效规格

- PNG，RGBA 透明背景，2×2 四帧图集。
- 帧序固定为行优先：左上 → 右上 → 左下 → 右下。
- 生命周期语义：起势/聚气 → 成形/推进 → 命中峰值 → 消散。
- 当前包含三档画布：768×768、1024×1024、1254×1254；对应单帧 384、512、627 px。接入时读取 manifest，不写死统一尺寸。
- 推荐 90–105 ms/帧，中心锚定；默认 Alpha 混合。角色突进、穿身和回位不包含在图集中，应由角色动作系统独立处理。

Godot 4 切片示例：

```gdscript
var frame_size := Vector2(sheet.get_width() / 2.0, sheet.get_height() / 2.0)
for frame_index in range(4):
    var frame := AtlasTexture.new()
    frame.atlas = sheet
    frame.region = Rect2(
        (frame_index % 2) * frame_size.x,
        floor(frame_index / 2.0) * frame_size.y,
        frame_size.x,
        frame_size.y
    )
    sprite.texture = frame
    await get_tree().create_timer(0.095).timeout
```

Unity 或自研引擎使用同一行优先帧序即可；manifest 中的 `frame_width`、`frame_height`、`anchor` 和 `blend_mode` 是跨引擎合同。

## 来源与边界

- 技能与物品图标来自无参考图输入的项目内 AI 生成批次，并经过本地去底、切片和运行时验证。
- 特效来自项目内多批 AI 生成与本地后处理，历史批次的服务商元数据完整度不一致，因此不宣称全部具有相同的公开再许可状态。
- 本包只复制正式运行时 PNG 与其派生预览；不包含 raw 生成图、参考图、角色立绘、候选、淘汰资源、绝对路径、成本或账号信息。
- 授权规则见 [LICENSE-ASSETS.md](LICENSE-ASSETS.md)。仓库根 MIT 只覆盖代码和文档，不自动覆盖本包 PNG/WebP。

## 重建与验证

```powershell
python -m pip install -r requirements-art.txt
python tools/build_art_resource_catalog.py
python tools/validate_resource_pack.py
python tools/validate_repository.py
```

构建器会重算图片尺寸、模式、SHA-256、目录表和全部二进制校验值。验证器同时检查缺失/孤儿文件、重复哈希、命名、透明通道、图标尺寸、2×2 四格非空、洋红键色残留、预览和敏感路径。
