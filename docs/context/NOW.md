# 当前状态

## 当前工作

- 目标：交付 GINKA Android 测试版，并按用户新增要求上传当前版本至 GitHub、整理可复用移植提示词。
- 进展：源文件下载、ZIP 密码恢复与解包已完成。专用 APK `0.1.0` 已生成，包含两个 ARM ABI，签名校验通过；在独立 Android 12 模拟器中，两种 ABI 均已显示标题并进入中文剧情。采用 OpenGL 后越过原先的软件绘制崩溃，补全动态界面名称后，32 位版本已创建带缩略图的存档。七个独立资源包已封装。方案见 [移植计划](PORTING.md)，位置见 [MAP.md](MAP.md#移植工作文件)。
- 当前验证：32 位保存与读取通过，读取后继续显示后续海上鸟居场景；64 位在冷启动后成功读取该存档并恢复中文对话，也成功创建第二槽存档。完整剧情、视频及 ARM 真机尚未验证。用户不清楚手机型号和系统版本，模拟器结果不作为真机保证。
- 交付：本地测试版 `0.1.0` 的 APK、完整配套资源、安装说明、许可及源码快照已整理，整包 ZIP 校验通过；入口与检查见本文件“交付检查”。未运行输入包中的 Windows 可执行文件，不宣称整部游戏通关或用户验收完成。
- 下一步：完成 [GitHub 上传](#github-上传)所需授权并核实远端结果；在用户实际手机上按 [安装说明](RUNBOOK.md#手机安装与使用)验证。若出现兼容性问题，依据具体系统版本、错误页面与日志接续；真机及完整流程仍待核实。

## 静态资源恢复与原型适配

记录更新日期：2026-10-25；范围：本地资源恢复、兼容层构建及独立模拟器的阶段验证。本节不代表真机验证。

- 使用 `cxdec-hxv4-static-analysis` 成功静态恢复 EXE 内的启动脚本和 BOOTSTRAP 配置，未启动游戏 EXE。
- `Cxdec_Tools` 经本地适配支持本包的 salt 定位及未加密 PBD，最初导出 11,261 个文件，其中 8,269 个保留哈希叶名。后续依据脚本、PBD 和 PSB 字符串表恢复了数千个名称别名，不改原始资源；导出和名称匹配不等于全游戏经过校验。
- 工具适配的 19 项单元测试通过；修改转换范围后的 PBD 类型与字符串转义测试再次通过。已按格式标记转换 146 个源数据对象，并补充 61 份已恢复名称的数据表达式，保留类型，不用空对象替代界面数据。
- 原始 XP3 的 `startup.tjs` 静态反编译后确认直接显示 `startup failed: corrupted execution file`；这条提示本身不能证明归档损坏。原型改用已恢复的 `system/initialize.tjs` 作为验证入口。
- 显式载入内置 `KAGParserEx.dll` 后越过早期黑屏；软件渲染的标题绘制曾使两种 ABI 崩溃，改用运行时已有 OpenGL 配置后，两种 ABI 均通过标题与中文剧情检查。证据为 `work/ginka/title-arm64-opengl.png`、`work/ginka/title-arm32-opengl.png`、`work/ginka/play-arm64-opening.png`、`work/ginka/play-arm32-opening.png`。
- 动态生成的 `file_save_en.pbd` 等名称最初未恢复，存档页出现缺少 `item` 定义；补全扩展名替换与语言后缀后，32 位存读档通过。截图为 `work/ginka/save-ui-arm32.png`、`work/ginka/save-slot-arm32.png`、`work/ginka/load-arm32.png`、`work/ginka/dialogue-arm32-progress.png`。2026-10-25 复核了 64 位冷启动后的跨 ABI 读取，截图及日志为 `work/ginka/load-arm64-cold.png`、`work/ginka/load-arm64-cold.log`。
- 原输入 11,261 个文件保留；当前别名目录有 6,790 个明确匹配的文件别名。七个输出归档合计 3,572,341,390 字节、18,281 个逻辑文件条目，包含新增兼容脚本与数据表达式；这些数字不表示新增了同等数量的原始游戏文件。索引、长度、数据段 Adler-32 和清单 SHA-256 已独立检查；变更的 `data.xp3` 已定点复核。
- APK 包名为 `org.ginka.launcher`，最低 API 29、目标 API 33；含 Java 启动入口、双 ABI JNI 桥接及固定运行时，编译声明与链接占位库未打入 APK。构建证据为 `work/ginka/apk-build-04/build-report.json` 与同目录签名日志。资源体积和散列以 [资源清单](../../dist/GINKA-Android-0.1.0/GINKA/resource-manifest.json)为准，校验证据为 `work/ginka/resource-verification.json`。
- 64 位第二槽缩略图及中文摘要见 `work/ginka/save-slot-arm64.png`，相应数据文件为模拟器资源目录的 `savedata/data_0001_02.bmp`。清除本测试应用数据后，已验证首次资源访问提示、跳转到本应用权限设置页，以及授权返回后自动识别 `Download/GINKA/` 并进入标题；截图为 `work/ginka/first-launch-permission.png`、`work/ginka/permission-settings.png`、`work/ginka/first-launch-auto-resource.png`。该结果仅覆盖本次 Android 12 模拟器。

## 交付检查

交付日期：2026-10-25。范围：本任务的 APK、七个资源归档、安装说明、源码快照及直接关联文档；不包含真机验收、发布或完整游戏通关。

- [专用 APK](../../dist/GINKA-Android-0.1.0/GINKA-0.1.0.apk)：72,354,356 字节，SHA-256 为 `14a8d3ec5edf8a158aabccbab4c062c4c12c531d822db414455281035d01cda2`；签名验证与两种 ABI 的模拟器安装通过。
- [配套资源清单](../../dist/GINKA-Android-0.1.0/GINKA/resource-manifest.json)：保留七个 XP3、OpenGL 配置及空的可选追加包列表，不包含测试存档。原始下载、解包输入、恢复密码与本地签名材料未放入交付包。
- [使用说明](../../dist/GINKA-Android-0.1.0/使用说明.txt)是 [操作手册](RUNBOOK.md#手机安装与使用)的交付快照；`porting-source.zip` 为本次源码与上下文文档快照，项目内文件仍是后续修改的权威来源。
- 新建了 `porting/` 下的启动器、资源适配及构建校验源码；修改 `.gitignore`、README、PROJECT_INDEX、NOW、MAP、PORTING、RUNBOOK、RISKS；沿用 AGENTS、DECISIONS 与历史索引，没有覆盖原始输入或新增无独立职责的记录文件。
- [完整交付 ZIP](../../dist/GINKA-Android-0.1.zip)：3,082,750,195 字节，16 个文件条目；全部条目的 ZIP CRC 检查通过。整包 SHA-256 见 [校验文件](../../dist/GINKA-Android-0.1.zip.sha256)，包内各文件的散列见 [SHA256SUMS.txt](../../dist/GINKA-Android-0.1.0/SHA256SUMS.txt)，打包证据为 `work/ginka/delivery-report.json`。
- 本次 7 份变更 Markdown 的 89 个本地链接及标题锚点检查通过；交付清单未发现测试存档，源码快照未包含工具、原始下载或签名材料。检查仅覆盖本次改动及其直接入口，未扩展为全项目审计。
- 适配源码及补丁见 [MAP.md](MAP.md#移植工作文件)。工作目录中有含资源派生参数的临时文件，不将这些值复制到项目文档。

## GitHub 上传

核验日期：2026-10-25；范围：本次 `0.1.0` 版本的上传准备与可复用提示词，不重新扩大游戏运行验证。

- 来源：用户明确要求将当前版本上传至 GitHub，并把同类软件移植提示词放到桌面。
- GitHub 账号为 `Lyz30919235`；用户完成所需授权后，已建立独立[私有仓库 ginka-android](https://github.com/Lyz30919235/ginka-android)，本地分支为 `main`。当前正在准备首次源码推送与 `v0.1.0` 测试版附件，尚未报告 Release 发布完成。
- 完整 ZIP 已分成两个小于 2 GiB 的发行附件，见 `dist/github-v0.1.0/`；[分卷清单](../../dist/github-v0.1.0/release-parts.json)是分卷顺序、长度与散列的权威来源。已用 [合并脚本](../../porting/release/merge_package.ps1)实际合并，结果与原完整 ZIP 的长度及 SHA-256 一致。下载与合并步骤见 [RUNBOOK.md](RUNBOOK.md#github-分卷下载与合并)。
- [可复用提示词](PORTING_PROMPT.md)已创建并导出为桌面 TXT；项目文件是后续修改的权威来源。桌面文件内容与模板一致，未写入密码、令牌或个人设备路径。
- 待核实：远端仓库、commit、tag、Release 状态及每个发行附件的长度和散列；授权尚未完成时不得把本地准备报告为上传成功。

## 密码恢复与资源载入验证

核验日期：2026-10-20。范围：本地 ZIP 密码恢复、解包完整性，以及单个模拟设备对原始 `data.xp3` 的首次载入；不包含游戏可玩性、真机或用户验收。

- 953 个上下文及常见候选未命中。随后使用 Hashcat 7.1.2、模式 17220 和 RX 7900 XT OpenCL，按 1 至 8 位数字逐长度搜索；在 4 位数字阶段命中并正常退出，未继续搜索更长密码。保留默认自检与 90°C 温度中止保护。
- Hashcat 发行包的错误 include 已按上游修复更正，操作依据见 [RUNBOOK.md](RUNBOOK.md#本地-zip-密码恢复)。Python 独立读取 5 个加密条目并通过 CRC 检查，排除单凭哈希命中判断成功。
- Bandizip 完整解包退出码为 0；81 个文件（含 3 个空文件）的实际长度均与 ZIP 目录一致，共 3,559,181,070 字节。原始下载及 ZIP 工作副本保留。密码不写入项目文档。
- 静态检查了 `data.xp3`、`cr_data.xp3`、`steam.xp3`、`fgimage.xp3` 的索引，均含 `Hxv4`。这只证明目录结构可读，不代表脚本或资源正文已经解密。
- 向模拟设备的独立测试目录仅复制原始 `data.xp3`，运行时读取后显示启动错误；[截图](../../work/ginka/runtime-hxv4-error.png)、[应用日志](../../work/ginka/runtime-launch.log)。没有进入标题或新游戏，未测试音画与存读档。

## 安卓运行时准备验证

核验日期：2026-10-20。范围：MuMu 单个模拟设备上的候选运行时安装、冷启动与首屏；不包含 GINKA 游戏运行或真机验证。

- ADB 识别到 MuMu Android 12；设备声明 ABI 包含 `x86_64`、`arm64-v8a`、`x86`、`armeabi-v7a` 等。这不证明目标手机架构或 ARM 真机兼容。
- 候选 APK 安装返回 `Success`；`org.github.krkr2/.MainActivity` 冷启动返回 `Status: ok`，随后该 Activity 仍位于前台，进程存在。
- 首屏为运行时的文件浏览界面；[截图证据](../../work/ginka/runtime-smoke.png)。没有载入游戏资源，不能据此报告 GINKA 可玩。

## GeZi 验证

核验日期：2026-10-19。范围：本次完成副本的任务最终状态、文件长度、SHA-256 及完整 LZ4 压缩流校验；不包含安装、运行或用户验收。

- 分享地址：`https://pan.quark.cn/s/9ca65ebc3b86`；解析到 `【PC】GINKA.zip.lz4`，GeZi 显示 3.47 GB。
- 工具安装时（2026-10-18）发行包 SHA-256 为 `65d1dae68ca1cbc240d3f479e18c812e41199a9a25406dc4b4dab822cb73f0db`，与 GitHub 发行资产 digest 及发行说明公布值一致；该结果不代表目标下载文件的哈希。
- 首轮下载在中断前实测至约 80.4%；重新打开软件后，自动续传返回 401。重新解析同一分享后在独立目录从头下载，旧文件及续传元数据保留，未覆盖或删除。
- 完成副本：GeZi 日志显示“全部完成：1 个文件已下载完成”，任务进度 100.0%；本次用时 277.2 秒，平均 12.54 MB/s。
- 文件实际长度为 3,474,930,441 字节；SHA-256 为 `d99614ecfccfe0cca8ae44453df81e748c80688a79e55c61ead9b666b8cee036`。该哈希为本地指纹，未与来源方原始哈希比较。
- 只读流式解码到帧末尾成功，无尾随数据；LZ4 内置内容校验通过。解码数据总长 3,474,927,110 字节，起始签名为 ZIP（`504b0304`）；未将内层 ZIP 写入磁盘，未验证 ZIP 内部各文件或运行其内容。方法见 [RUNBOOK.md](RUNBOOK.md#gezi-免转存下载)。
- 未读取或导出 Cookie，未读取续传元数据内容，未支付；未暂停或取消原有夸克任务。

## 核验证据

核验日期：2026-10-18。对象与范围：基础文档建立时的 9 个 Markdown 文档及其直接关联的相对链接、标题锚点与职责分配。以下为建档时证据，不代表后续下载工具的状态。

- 建立前：确认当前工作目录为项目根目录；根目录包含隐藏项在内共 0 个条目，项目根目录和上级目录均未发现 `AGENTS.md`。本次用户提供的中文规则及读写要求适用。
- 建立后：9 个文件存在，37 个本地链接（含 11 个标题锚点）检查通过；两组各 7 条读写规则齐全，未发现设备绝对路径；人工核对文件职责已覆盖本次要求。
- 既有成果：建立前目录为空，无既有文件被覆盖；未新建无独立用途的 `PROJECT_NOTES.md`。
- 检查方法见 [RUNBOOK.md：文档检查](RUNBOOK.md#文档检查)。未运行构建、应用测试、安装、部署或发布；未作用户验收结论。

以上结果只代表本次文档检查，不作为后续代码或环境验证的当前证据。
