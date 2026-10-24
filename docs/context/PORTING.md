# GINKA Android 移植计划

## 目标与边界

用户要求：先在 GitHub 查找并下载相关项目，规划移植方式，再将已下载的 GINKA PC 包制作成 Android APK。

本计划负责引擎判断、候选方案、验证顺序及方案待核实项；当前进展以 [NOW.md](NOW.md#当前工作) 为准，输入与工具位置以 [MAP.md](MAP.md#移植工作文件) 为准。

## 输入检查

输入清点日期：2026-10-20。范围：已完成下载的 LZ4、内层 ZIP 解包及四份 XP3 的静态索引；后续静态恢复和运行验证以 [当前状态](NOW.md#当前工作) 为准。

- 已将 LZ4 解码为工作副本 ZIP，原始下载文件保留。
- ZIP 共 85 个条目，展开总量 3,559,181,070 字节；78 个非空文件具有 ZIP 加密标记，另外有 4 个目录和 3 个未加密空文件。没有 ZIP 注释提供密码。
- 目录内包含 `data.xp3`、`bgimage.xp3`、`cr_data.xp3` 等 7 份 XP3，以及 `KAGParserEx.dll`、`kagexopt.dll`、`textrender.dll`、`AlphaMovie.dll`、`GINKA.dll` 等 Windows 插件。
- 已确认采用 KiriKiri/KAGEX 框架。原始 XP3 含 `Hxv4` 保护；现通过静态工具恢复资源，保留原始包并在独立目录适配。索引证据见 [xp3-index.json](../../work/ginka/xp3-index.json)，具体恢复范围及验证结果见 [NOW.md](NOW.md#静态资源恢复与原型适配)。
- 包含 Windows 可执行文件及带 `crack` 字样的文件名；本次没有运行这些文件。Android 路线需要兼容运行时与可用资源，不能把 Windows EXE 改扩展名作为移植。
- 目录证据见 [archive-index.json](../../work/ginka/archive-index.json)；仅记录文件元数据，不保存密码或账号凭证。

## GitHub 候选方案

### 首选验证：KrKr2 Emulator

- 仓库：[2468785842/krkr2](https://github.com/2468785842/krkr2)。本次固定使用 [v1.4.4 官方发行资产](https://github.com/2468785842/krkr2/releases/tag/v1.4.4)，摘要与位置见 [MAP.md](MAP.md#移植工作文件)。该 APK 的最低系统为 Android 10，包含两个 ARM ABI。
- [v1.4.4 插件清单](https://github.com/2468785842/krkr2/blob/v1.4.4/krkr2_plugins.md)为调查依据；实际发现该版本缺少本包需要的 `Scripts.loadDataPack` 接口，现通过保留类型的资源转换适配。
- v1.4.4 标签主要保存 Android 包装层与预编译库；当前 main 已有不同的原生源码布局，不能将其能力直接等同于发行资产。专用 APK 复用已核验的运行时库，另编译 Java 入口和双 ABI JNI 桥接，不宣称重编译了完整引擎。

### 备选：Kirikiroid2-Yuri

- 仓库：[YuriSizuku/Kirikiroid2Yuri](https://github.com/YuriSizuku/Kirikiroid2Yuri)。
- [作者说明](https://github.com/YuriSizuku/Kirikiroid2Yuri/blob/yuri/readme.md)明确区分推荐发行版与仍有兼容问题的源码构建测试版；若首选失败，再按具体错误比较该方案，不同时铺开多套改造。
- 原版 [zeas2/Kirikiroid2](https://github.com/zeas2/Kirikiroid2)作为上游参考；[Android 14 安装问题](https://github.com/zeas2/Kirikiroid2/issues/164)等反馈说明必须按目标系统验证，不能仅凭生成 APK 判定可用。

## 暂定移植路线

用户已确认采用“APK＋独立资源目录”，决定来源见 [DECISIONS.md](DECISIONS.md#d-002采用-apk独立资源目录交付)。目标手机型号与版本未知，实施目标为 Android 10 及以上、`arm64-v8a` 与 `armeabi-v7a`；模拟器结果不作为真机保证。

1. **静态恢复与依赖适配**：使用已固定提交的工具恢复 XP3；将 PBD 数据转为等价 TJS 表达式，根据脚本与 PSB 字符串池核对名称别名。保留源包，不执行输入包中的 Windows 程序。
2. **兼容性验证**：先验证标题、新游戏及中文对话，再检查存读档与更多音画路径。采用运行时已有的 OpenGL 渲染配置，软件渲染曾导致标题绘制崩溃；缺失接口不能用空实现掩盖。
3. **游戏专用 APK**：复用固定运行时，编译独立包名、资源选择入口与启动桥接，保留两个 ARM ABI；使用本地独立签名，不复用其他项目的证书。
4. **资源封装**：输出七个未加密 XP3 与必要配置；同一硬链接对应的多名称共享归档数据段，并记录散列。通过资源目录完成首次启动，不把通用解释器 APK 当作包含游戏的成品。
5. **交付验证**：分别记录构建、签名、安装、启动、上述功能检查及真机验收证据。最终提供 APK、必要资源及简明使用说明；没有通过的环节写“待核实”。

## 当前待核实项

- 文件名映射及延后调用的资源是否覆盖所有游戏路径；静态恢复完成不等于整部游戏通关验证。
- 历史调查入口：[GINKA-IND](https://github.com/Walkedharmony/GINKA-IND) 是 Windows 翻译工具说明；[GARbro HxCrypt 实现](https://github.com/crskycode/GARbro/blob/master/ArcFormats/KiriKiri/HxCrypt.cs)未在本任务执行验证。实际采用的静态恢复工具见 [MAP.md](MAP.md#移植工作文件)。
- 目标手机型号、Android 版本与 CPU ABI。
- 本包是否依赖 Android 运行时未实现的 Windows 原生插件，以及是否需要额外资源适配。
- 更高 Android 版本、16 KB 内存页设备、物理 ARM 设备及完整剧情、视频与存读档的验证范围，以当前证据为准；不从系统最低版本推导全部设备兼容。

## 完成判据

只有实际生成可安装的游戏专用 APK，并说明哪些运行环节经过验证，才可报告移植产物完成。下载通用模拟器、解开压缩包或生成空壳 APK 都不能替代此判据。
