# 项目映射

## 目录关系

所有位置相对于项目根目录。

| 位置 | 用途 |
| --- | --- |
| `AGENTS.md` | 项目协作规则 |
| `PROJECT_INDEX.md` | 条件路由入口 |
| `README.md` | 项目用途与基本使用方式 |
| `docs/context/` | 当前状态、映射、操作、决策和风险专题；具体入口见 [项目索引](../../PROJECT_INDEX.md) |
| `docs/context/history/` | 必要历史归档；从 [历史索引](history/README.md) 定位 |

## 下载工具与文件位置

核验日期：2026-10-19；范围为本次下载工具、验证依赖及文件位置，不代表项目产品技术选型。

| 对象 | 项目内位置或来源 |
| --- | --- |
| GeZi v2.2.0 官方发行包 | `tools/GeZi-v2.2.0-win64.zip`；来源为 [GitHub 官方发行页](https://github.com/huaotem-bot/gezi-quark-downloader/releases/tag/v2.2.0) |
| GeZi 启动程序 | `tools/gezi-v2.2.0/鸽子下载/GeZi.exe`；已解压并启动 |
| GeZi 本地配置 | 启动程序同目录的 `GeZi.config.xml`；可能保存登录信息，不读取或提交其内容 |
| 已完成的目标文件 | `downloads/retry-20261019/【PC】GINKA.zip.lz4`；完成及校验证据见 [NOW.md](NOW.md#gezi-验证) |
| GeZi 当前保存目录 | `downloads/retry-20261019/`；设置页已确认。本次使用共写同一文件模式、单文件并发 256 路 |
| 首轮未完成文件 | `downloads/【PC】GINKA.zip.lz4` 及同名 `.qmeta`；保留的约 80% 残件，不能当作完成文件 |
| 本地校验依赖 | `tools/verification-python/`；PyPI 的 `lz4` 4.4.5，仅安装到此目录，用于只读压缩流校验 |

`tools/` 与 `downloads/` 通过根目录 `.gitignore` 排除，避免将外部程序、登录配置和下载内容纳入后续 Git 提交。

## 待核实映射

与 GINKA 移植相关的引擎和待确认环境见 [PORTING.md](PORTING.md)，不将下载工具的运行环境当作游戏引擎环境。

| 对象 | 状态 |
| --- | --- |
| 源码、资源、测试与构建目录 | 已定位的 GINKA 工作入口见下方“移植工作文件” |
| 技术栈、运行时、依赖与版本 | 当前实施路线见 [PORTING.md](PORTING.md)；不推断其他产品用途 |
| 配置文件与环境变量名称 | 运行时资源配置与构建参数见下方及 [RUNBOOK.md](RUNBOOK.md)；不记录密钥值 |
| 版本管理、远程仓库与分支约定 | 本地 Git `main` 已初始化；远端与发行的实际状态见 [NOW.md](NOW.md#github-上传) |
| 构建产物、安装与部署位置 | 开发产物见下方；最终交付与安装状态以 [NOW.md](NOW.md#当前工作) 为准 |

仅在相关任务需要且取得证据后修订对应条目；不从目录名推断环境。

## 移植工作文件

位置更新日期：2026-10-25；范围为本任务的本地移植源码、工具与产物。以下位置相对于项目根目录；原始完成下载仍以本文件的“下载工具与文件位置”为准。

| 对象 | 位置与用途 |
| --- | --- |
| 内层 ZIP 工作副本 | `work/ginka/source.zip`；由 LZ4 解码生成，保留原始下载文件 |
| ZIP 目录检查结果 | `work/ginka/archive-index.json`；保存条目和引擎相关文件元数据 |
| 已解包 PC 资源 | `work/ginka/unpacked/【PC】GINKA/`；原始下载与 ZIP 保留，未运行其中 Windows 程序 |
| Hx 静态分析工具 | `tools/porting/cxdec-static/`，上游 `hktkqj/cxdec-hxv4-static-analysis`，提交 `3c6dee001df011fa7ed557c7463635c6f67698f6`；静态探测输出 `work/ginka/static-probe/` |
| 资源恢复工具 | `tools/porting/cxdec-tools/`，上游 `1F1E33-float32/Cxdec_Tools`，提交 `c25804340610bdfb9e971e3b6bd23b8abd52797a`；本地改动保存在 [cxdec-ginka.patch](../../porting/patches/cxdec-ginka.patch) |
| 静态导出资源 | `work/ginka/cxdec-recovered/`、`work/ginka/cxdec-recovered-v2/`；后者用于复核工具修正，未覆盖首轮输出 |
| PBD 数据适配 | [转换器 Cargo 项目](../../porting/pbd-adapter/Cargo.toml)及 [源码](../../porting/pbd-adapter/src/main.rs)；按文件格式识别；完整转换输出 `work/ginka/pbd-complete/`、当前命名补充 `work/ginka/pbd-aliases-v3/` |
| 资源名恢复辅助 | [collect_resource_names.py](../../porting/collect_resource_names.py)从指定脚本和 PSB 字符串表采集线索；[restore_aliases.py](../../porting/restore_aliases.py)只增加哈希明确命中的别名；输出 `work/ginka/all-aliases/` |
| Android 专用入口 | [GameActivity.java](../../porting/android/java/org/ginka/launcher/GameActivity.java)负责权限与资源选择；[launcher.rs](../../porting/android/native/launcher.rs)连接固定版本的原生启动 API；`compile-stubs/`、`link_stubs.rs` 仅供编译，不打入 APK |
| 启动与渲染配置 | [startup.tjs](../../porting/android/startup.tjs)、[Kirikiroid2Preference.xml](../../porting/android/Kirikiroid2Preference.xml)；前者处理接口与资源路由，后者选择运行时已有的 OpenGL 渲染 |
| APK 构建 | [build_apk.py](../../porting/build_apk.py)；SDK、JDK、Rust 工具链由参数指定，不保存个人设备私有路径；开发记录为 `work/ginka/apk-build-*/` |
| 资源封装 | [prepare_resources.py](../../porting/prepare_resources.py)组装独立源树；[build_resources.py](../../porting/build_resources.py)、[pack_xp3.py](../../porting/pack_xp3.py)生成归档与散列清单；准备源树 `work/ginka/resources-src-05/`，交付包 `dist/GINKA-Android-0.1.0/GINKA/` |
| 交付入口 | `dist/GINKA-Android-0.1.0/`，APK、资源、使用说明和源码快照；体积、校验及验证范围统一见 [NOW.md](NOW.md#交付检查) |
| 独立资源校验 | [verify_resources.py](../../porting/verify_resources.py)检查 XP3 索引、长度、Adler-32 和清单 SHA-256；结果 `work/ginka/resource-verification.json`，只代表报告对应的文件版本 |
| 本地构建依赖 | `tools/porting/rust/`、`tools/porting/w64devkit/`、`tools/porting/apktool.jar`；诊断用 Python 库 `tools/porting/python-deps/` 不作为游戏依赖 |
| Android 兼容性原型 | `work/ginka/android-prototype/`；含验证用启动脚本及定时诊断，未作为成品交付 |
| 解包与 XP3 静态检查 | `work/ginka/extraction-result.json`、`work/ginka/extraction.log`、`work/ginka/xp3-index.json` |
| 密码恢复工具与证据 | `tools/recovery/hashcat-7.1.2/`、`tools/recovery/john/JtR/run/zip2john.exe`；非敏感结果为 `work/recovery/dictionary-result.json`、`work/recovery/verified-result.json`；操作依据见 [RUNBOOK.md](RUNBOOK.md#本地-zip-密码恢复) |
| 安卓运行时首屏证据 | `work/ginka/runtime-smoke.png`；核验对象与范围见 [NOW.md](NOW.md#安卓运行时准备验证) |
| 候选 Android 运行时 | `tools/porting/krkr2-1.4.4-all.apk`；从 [GitHub 发行页](https://github.com/2468785842/krkr2/releases/tag/v1.4.4)下载，72,226,012 字节；仅作为兼容性验证依赖，不能当作游戏专用 APK 成品 |
| 候选运行时完整性 | SHA-256：`443be0d4d76c5026c7980eb625bef482c7c43275b3176bc2b6b7399c5755f497`；与 GitHub 发行资产 digest 一致，APK ZIP CRC 检查通过 |

`work/` 与 `dist/` 分别用于临时资源与后续交付产物，并从 Git 排除；APK 是否已生成与验证以 [NOW.md](NOW.md#当前工作) 为准。
