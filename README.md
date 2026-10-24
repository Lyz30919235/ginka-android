# galgame

## 项目用途

当前目录用于静态恢复本地 GINKA PC 资源、适配 KAGEX 接口，并制作 Android APK 与独立资源目录。实现路线见 [移植计划](docs/context/PORTING.md)，当前验证范围见 [NOW.md](docs/context/NOW.md#当前工作)。

## 基本使用方式

手机使用需同时安装专用 APK 并复制整个配套资源目录，再按应用提示授权和选择资源。详细步骤见 [手机安装与使用](docs/context/RUNBOOK.md#手机安装与使用)，开发重建流程见 [构建手册](docs/context/RUNBOOK.md#ginka-资源与-apk-构建)。

交付位置与当前验证结果从 [NOW.md](docs/context/NOW.md#当前工作) 定位。真机兼容性、完整剧情与视频播放仍待实测；生成 APK 或完成局部模拟器检查不等于整部游戏验收。

GitHub 提供 [v0.1.0 测试版附件](https://github.com/Lyz30919235/ginka-android/releases/tag/v0.1.0)，仓库保持私有；版本与附件的核验范围见 [上传记录](docs/context/NOW.md#github-上传)，分卷下载见 [合并说明](docs/context/RUNBOOK.md#github-分卷下载与合并)。同类任务可复用 [移植提示词](docs/context/PORTING_PROMPT.md)；第三方来源与许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 文档入口

需要定位资料时使用 [PROJECT_INDEX.md](PROJECT_INDEX.md)。参与项目工作前确认 [AGENTS.md](AGENTS.md) 中的适用规则；接续工作按索引定位当前状态。
