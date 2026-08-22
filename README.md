# Game Maker Experience

面向多个游戏项目共同维护的制作经验库。这里沉淀地图场景、交互建筑、技能表现、角色与怪物精灵、跨平台 UI、AI 美术生产和质量门禁，并提供可以直接复制的配置模板与发布检查表。

本仓库不保存某个游戏的业务代码，也不把一次项目实现当成唯一答案。核心文档描述可迁移的规则，真实项目差异放在案例中。

## 快速入口

| 你正在做什么 | 先读 | 直接使用 |
|---|---|---|
| 新建或重做地图 | [地图场景生成管线](docs/map-scene-pipeline.md) | [地图规格模板](templates/map-authoring-spec.template.json)、[地图发布检查表](checklists/map-release.md) |
| 建筑遮挡角色，需要自动半透明 | [交互建筑与半透明遮挡](docs/building-occlusion.md) | [建筑遮挡模板](templates/building-occlusion.template.json)、[建筑检查表](checklists/building-interaction.md) |
| 制作技能图标、动作、特效和音效 | [可配置技能表现系统](docs/skill-presentation.md) | [技能数值模板](templates/skill-definition.template.json)、[技能表现模板](templates/skill-presentation.template.json) |
| 制作角色或怪物动画 | [角色与怪物精灵管线](docs/character-monster-sprites.md) | [动画清单模板](templates/sprite-animation-manifest.template.json)、[精灵发布检查表](checklists/sprite-release.md) |
| 同时支持 PC 和手机 | [跨平台 UI 与触控](docs/ui-cross-platform.md) | [UI 布局模板](templates/ui-layout-profile.template.json)、[手机 UI 检查表](checklists/ui-mobile-release.md) |
| 使用 AI 生成美术资源 | [AI 美术生产管线](docs/art-production.md) | [美术资产清单模板](templates/art-asset-manifest.template.json)、[美术发布检查表](checklists/art-release.md) |
| 打通远程玩家状态与交互 | [多人联机权威状态](docs/multiplayer-authority.md) | [网络状态信封模板](templates/network-state-envelope.template.json)、[多人联机检查表](checklists/multiplayer-release.md) |
| 解决刷怪、寻路和高攻速卡顿 | [游戏运行时性能预算](docs/runtime-performance.md) | [性能预算模板](templates/performance-budget.template.json)、[性能检查表](checklists/performance-release.md) |
| 设计职业装备和前期成长 | [装备成长与推荐路线](docs/equipment-progression.md) | [装备路线模板](templates/equipment-route.template.json)、[装备成长检查表](checklists/equipment-progression.md) |
| 导出桌面与移动正式包 | [跨平台构建与发布闭包](docs/cross-platform-release.md) | [发布配置模板](templates/release-profile.template.json)、[跨平台发布检查表](checklists/cross-platform-release.md) |
| 丰富技能、拾取和 UI 音效 | [游戏音效反馈系统](docs/audio-feedback.md) | [音频表现模板](templates/audio-presentation.template.json)、[音效检查表](checklists/audio-release.md) |
| 建立跨项目资源共享 | [可复用资源包治理](docs/resource-pack-governance.md) | [资源包模板](templates/resource-pack.template.json)、[资源包目录](resource-packs/README.md) |
| 复用已整理的图标与招式特效 | [可复用美术资源包](resource-packs/README.md) | [水墨武侠图标与招式特效 v1](resource-packs/ink-wuxia-icons-vfx-v1/README.md) |
| 建立自动化验收 | [质量门禁](docs/quality-gates.md) | `python tools/validate_repository.py` |
| 把经验接入新项目 | [采用指南](docs/adoption-guide.md) | [贡献规范](CONTRIBUTING.md) |

Godot 4 参考代码：

- [分层建筑遮挡组件](examples/godot/layered_building_occluder.gd)
- [只负责表现的技能控制器](examples/godot/skill_presentation_controller.gd)

## 核心原则

1. **规格是源，运行文件是产物。** 地图、技能和动画都从可审阅的规格构建，不手改生成文件。
2. **逻辑与表现解耦。** 数值结算不依赖图标、特效或音效；表现资源缺失也不能破坏玩法。
3. **视觉、碰撞、交互分离。** 一张建筑图不等于一个碰撞体，也不等于一个触控区域。
4. **资产必须有契约。** 尺寸、方向、动作、锚点、透明通道和命名都可机器检查。
5. **平台语义一致，布局按平台适配。** PC 和手机使用同一技能与道具身份，但不强求同一排版。
6. **先自动检查，再人工看效果。** 结构测试发现缺文件，视觉验收判断构图、动作和手感。
7. **案例不能污染规范。** 项目专属 ID、路径和数值放在 `case-studies/`，模板保持中立。

## 推荐采用顺序

```mermaid
flowchart LR
    A[选择专题] --> B[复制模板]
    B --> C[替换项目命名与路径]
    C --> D[建立自动检查]
    D --> E[接入运行时]
    E --> F[人工视觉与手感验收]
    F --> G[记录项目案例]
    G --> H[反哺公共规范]
```

详细步骤见[采用指南](docs/adoption-guide.md)。

## 仓库结构

```text
docs/          稳定、跨项目的制作手册
templates/     可复制的 JSON 配置模板
checklists/    制作和发布检查表
case-studies/  项目问题、决策、结果与迁移结论
examples/      小型、项目无关的引擎参考实现
tools/         本仓库内容校验工具
resource-packs/ 经所有者批准、独立声明授权的跨项目运行时美术包
```

## 当前案例

- [俯视角 RPG 地图制作经验](case-studies/rpg-map-production-lessons.md)：从地图生成、建筑遮挡、技能表现、动态怪物到 PC/手机联机 UI 的集中复盘。
- [RPG 地图项目资源采用建议](adoption/rpg-map-resource-fit.md)：把共享资源语义映射到刺客、战士、辅助、材料和跨平台 UI，不自动修改游戏运行时。

## 当前资源包

- [水墨武侠图标与招式特效 v1](resource-packs/ink-wuxia-icons-vfx-v1/README.md)
- [幻想 RPG 图标与战斗特效 v1](resource-packs/fantasy-rpg-icons-vfx-v1/README.md)
- [跨平台 RPG UI Kit v1](resource-packs/rpg-ui-kit-v1/README.md)

## 维护方式

其他项目可以直接提交专题补充、模板演进或新案例。修改公共规则时，请同时写清适用边界和迁移影响；完整要求见[贡献规范](CONTRIBUTING.md)。

仓库中的文档、模板、工具和示例代码统一采用 [MIT License](LICENSE)，便于不同项目复制、修改和回馈改进。`resource-packs/` 下的 PNG/WebP 使用各资源包自己的 `LICENSE-ASSETS.md`，不自动继承根 MIT。
