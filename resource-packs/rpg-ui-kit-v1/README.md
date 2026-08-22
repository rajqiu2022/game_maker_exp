# 跨平台 RPG UI Kit v1

一套无文字、可适配桌面和移动端的 RPG 运行时 PNG 组件。包内保留视觉尺寸、触控目标与内容安全区的分离契约，避免把贴图大小直接当成按钮命中范围。

## 内容

- 42 个核心按钮、复选框、面板、槽位、列表和进度条组件。
- 12 个移动端摇杆、攻击、交互、药水和功能控件。
- 8 个角色、队友、目标、资源与基地状态 HUD 组件。

## 接入规则

1. 根据 manifest 的语义 `asset_id` 绑定控件，不依赖源项目节点名。
2. `nine_patch` 组件必须使用 `content_safe_margin`，文字和图标放在安全区内。
3. `recommended_visible_size` 控制视觉大小；交互控件用独立的 `recommended_touch_target`。
4. 移动控件建议命中目标不小于 72×72 逻辑像素，并按设备安全区布局。
5. HUD 图片只负责外观，玩家状态、队伍状态和本地面板状态仍由项目逻辑分层管理。

详细属性见 `manifest.json`，组件预览见 `CATALOG.md` 与 `previews/`。

## 授权

根仓库 MIT 不覆盖本包 PNG/WebP。使用前阅读 [LICENSE-ASSETS.md](LICENSE-ASSETS.md)。

## 生成与校验

```powershell
python tools/build_resource_pack.py --pack rpg-ui-kit-v1
python tools/validate_resource_packs.py --pack rpg-ui-kit-v1
```

清单、目录、摘要和 WebP 预览由工具确定性生成，请勿手工维护。
