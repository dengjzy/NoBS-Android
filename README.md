# NoBS-Android (CleanYourPhone)

> No Bullshit Android: An Agent-Native, Zero-App, Fully-Reversible Android Purge & Debloat Skill via ADB.
> 跨平台 · 免装 App · 零 Root · 全量可逆 · 零网络损耗 · 多设备物理隔离

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![Python](https://img.shields.io/badge/python-3.8%2B%20(stdlib%20only)-blue.svg)]()

---

## 为什么需要 NoBS-Android？

市面上的手机去广告工具有两大顽疾：
1. 手机端常驻 App：依赖无障碍权限，耗电严重、常被国产系统杀后台、存在读取屏幕隐私隐患。
2. 重型桌面客户端 / 臃肿环境：动辄数百兆安装包，或强依赖大量第三方 pip 包，且在 Windows / macOS / Linux 之间兼容性脆弱。

NoBS-Android 专为大模型 Coding Agent（Claude Code, Antigravity, Cursor 等）打造：
* 全跨平台（Cross-Platform）：核心逻辑 100% 由 Python 3 标准库编写，无需 pip install 任何依赖。在 Windows (CMD/PowerShell)、macOS 和 Linux 上均可开箱即用。
* 多设备独立隔离（Multi-Device Ready）：以设备序列号为维度隔离快照目录（`snapshots/<device_id>/`），同时清理多台手机或平板绝不混淆。
* 三维本地纯物理根除（零网速损耗，不依赖网络层代理）：
  1. Tier 0 核心广告包：免 Root 停用系统广告引擎（MSAS / OPOS / vivo Ads）、锁屏画报、遥测打点。
  2. 第三方摇一摇广告终结：利用底层 AppOps 限制主流 App 动作传感器权限，彻底告别走路误触跳转。
  3. 快应用与推广偷跑治理：停用快应用框架，杜绝免安装网页广告静默唤醒。
* 关于网络层 Private DNS 的严正说明：
  系统广告与摇一摇广告已被上述本地手段彻底根除，完全不依赖网络过滤。公共 DoT（如 `dns.adguard-dns.com`）在国内存在跨境握手延迟（200ms+）以及导致国内大厂同城 CDN 调度失效的问题，因此本项目**默认不修改 Private DNS**，保持国内千兆带宽满血解析。进阶用户如需配置，可使用脚本自主指定内网或自建 DNS。
* 100% 可逆与安全快照：事前自动备份，遇到问题通过 `python scripts/rollback.py --device <id>` 一秒还原。

---

## 前置准备：开启手机调试（手机端唯一需要的手动步骤）

AI Agent 无法物理点击你的手机屏幕，因此连接前需要先手动开启系统的调试开关：

### 1. 通用开启方式（所有安卓品牌通用）
1. 打开手机【设置 → 关于手机】（或关于设备/系统信息）；
2. 连续快速点击【版本号】（或系统版本/软件版本）**7 次**，直到屏幕提示“您已处于开发者模式”；
3. 返回【设置】，进入【系统与更新】（或更多设置/其他设置）中的【开发者选项】；
4. 开启 **USB 调试**。

### 2. 连接方式选择
* 方式 A：有线 USB 连接（最推荐、最稳定）
  使用数据线将手机连接电脑，手机屏幕若弹出“允许 USB 调试吗？”，勾选“始终允许”并点击【确定】。
* 方式 B：无线调试（Android 11+，免数据线）
  1. 手机与电脑连接同一 Wi-Fi 网络；
  2. 在【开发者选项】中开启【无线调试】；
  3. 点击进入【无线调试】界面，查看 IP 地址与动态端口号（如 `192.168.1.50:37349`）；
  4. 电脑端执行配对与连接即可。

### 3. 主流品牌特殊注意事项
* 小米 / Redmi / HyperOS / MIUI：
  在【开发者选项】中，除开启【USB 调试】外，必须同时开启底部的 **【USB 调试 (安全设置)】**（允许通过 USB 模拟权限），否则系统会静默拒绝停用指令。
* vivo / iQOO / OriginOS：
  连接电脑后请解锁手机屏幕，若弹出权限确认框请务必点击允许。
* OPPO / 一加 / Realme / ColorOS：
  若开启后连接断开，请检查【开发者选项】中【禁止权限监控】是否需要开启，防止权限自动被系统回收。
* 华为 / 荣耀 (HarmonyOS / MagicOS)：
  部分机型在开发者选项中建议开启“仅充电模式下允许 ADB 调试”。

---

## 直接交给 AI Agent（无需手动 Clone）

完成上述前置开启后，如果你正在使用具备终端执行能力的 AI Agent（如 Claude Code, Antigravity, Cursor 等），你甚至不需要手动克隆仓库，直接将以下提示词发送给你的 Agent 即可：

```text
请帮我净化通过 ADB 连接的安卓手机（已开启 USB 或无线调试）。
参考开源项目 NoBS-Android 的规范：https://raw.githubusercontent.com/dengjzy/NoBS-Android/main/SKILL.md

请严格遵循 Andrej Karpathy Engineering Guidelines 执行：
1. 先运行探测命令（通过 ADB 读取设备品牌、型号与系统版本）；
2. 执行任何改动前，必须建立当前设备的状态快照并生成 rollback 记录；
3. 向我呈现拟停用的系统核心广告组件清单（Tier 0 纯广告）与摇一摇传感器拦截名单，等待我确认；
4. 确认后仅执行已批准项，绝不触碰核心通信与支付环境；
5. 注意：除非我明确要求，否则默认不要修改系统 Private DNS（避免境外 DoT 导致国内 CDN 减速）；
6. 执行后输出前后状态对比，并提供一键还原命令。
```

Agent 会自动通过网络读取最新规则并调用 ADB 闭环执行。

---

## 严格对齐 Andrej Karpathy Guidelines

本项目遵循 multica-ai/andrej-karpathy-skills 的四大工程铁律：
* Think Before Coding：遇厂商限制（如 OriginOS 的 USER_RESTRICTED）绝不猜测，降级为 AppOps 最小权限灭活；识别 DoT 延迟 Trade-off，坚决不无脑加塞境外网络依赖。
* Simplicity First：零第三方依赖，拒绝 Speculative Code 与过度封装。
* Surgical Changes：绝不破坏 /system 分区，不改动核心通信、指纹支付与安全组件。
* Goal-Driven Execution：每项动作均提供终端查询命令，完成闭环复验。

---

## 命令行手动操作（可选）

无论在 Windows、macOS 还是 Linux 终端下，均可直接运行：

```bash
# 1. 探测已连接设备
python scripts/probe.py

# 2. 建立安全快照
python scripts/snapshot.py

# 3. 广告包预检与应用 (纯本地操作，零网速影响)
python scripts/debloat.py dry-run rules/vivo_originos.json
python scripts/debloat.py apply rules/vivo_originos.json

# 4. 封杀第三方摇一摇广告 (哔哩哔哩/美团/淘宝/京东等，纯本地操作，零网速影响)
python scripts/shake.py scan
python scripts/shake.py apply

# 5. 私密 DNS 管理 (可选高阶项，默认保持系统原样)
python scripts/dns.py status

# 6. 一键回滚特定设备
python scripts/rollback.py --device <serial>
```

---

## 项目结构

```text
NoBS-Android/
├── CLAUDE.md                # Andrej Karpathy 工程规范指引
├── PROMPT.md                # 零安装、直接复制给 Agent 的提示词模版
├── SKILL.md                 # Agent 核心技能指引规范（Open Agent Skills 标准）
├── rules/                   # 规则库（纯结构化 JSON）
│   ├── vivo_originos.json   # vivo / iQOO (OriginOS) 规则
│   ├── xiaomi_hyperos.json  # 小米 / 红米 (HyperOS / MIUI) 规则
│   ├── oppo_coloros.json    # OPPO / 一加 / Realme (ColorOS) 规则
│   └── apps_antispam.json   # 主流第三方 App 摇一摇与流氓权限治理规则
├── scripts/                 # 跨平台纯 Python 3 (标准库无依赖)
│   ├── probe.py             # 设备与 ROM 探测
│   ├── snapshot.py          # 多设备隔离快照
│   ├── debloat.py           # 广告包停用与 AppOps 降级
│   ├── dns.py               # 系统级 DoT 加密私密 DNS 管理 (可选)
│   ├── shake.py             # 摇一摇传感器权限锁定
│   └── rollback.py          # 多设备一键还原工具
└── snapshots/               # 自动隔离保存各设备的历史快照（按 device_id 分目录）
```

---

## License
MIT License
