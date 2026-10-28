---
name: nobs-android
description: "Agent-native Android cleanser and debloater via ADB. Removes system ads, bloatware, telemetry, and third-party shake ads safely, reversibly, and cross-platform without installing any app on the phone."
---

# NoBS-Android: AI Agent 操作指南

本 Skill 用于指导 AI Coding Agent（如 Antigravity, Claude Code, Cursor 等）通过电脑端 ADB 调试接口，对连接的安卓手机执行无损、可逆、跨平台、零常驻 App 的手机净化与广告清理。

## 绝对安全红线（基于 Andrej Karpathy Guidelines）
1. Think Before Coding（事前思辨）：执行任何变更前，必须探测设备特性。遇到厂商权限限制（如 OriginOS 的 USER_RESTRICTED）绝不猜测，采用最小权限降级（AppOps）。
2. Surgical Changes（最小侵入与隔离）：严禁执行 `pm uninstall`（删除），仅允许使用 `pm disable-user` 或 `pm suspend`。多设备快照与回滚必须按设备序列号分目录严格物理隔离。
3. Simplicity First（零冗余依赖）：全套脚本基于 Python 3 标准库构建，无需安装任何第三方库（无 pip 依赖），在 Windows / macOS / Linux 均能原生直接运行。
4. Goal-Driven Execution（目标驱动与闭环验证）：每执行一项改动，必须有对应的终端查询命令进行真实验证。

---

## 跨平台执行指令规范 (Windows / macOS / Linux)

所有核心脚本均采用纯 Python 3 实现，AI Agent 可以直接使用通用 `python` 或 `python3` 调用：

| 功能 | 跨平台通用执行命令 | 作用与网络影响 |
| :--- | :--- | :--- |
| 设备探测 | `python scripts/probe.py [--device <serial>]` | 读取机型、系统版本与当前状态 |
| 创建基准快照 | `python scripts/snapshot.py [--device <serial>]` | 隔离记录当前包状态与设置 |
| 广告包停用 (Tier 0) | `python scripts/debloat.py <dry-run\|apply> rules/<brand>.json [--tier tier0_pure_ads] [--device <serial>]` | 本地停用广告服务（零网速损耗） |
| 摇一摇传感器治理 | `python scripts/shake.py <scan\|apply\|reset> [--device <serial>]` | 本地锁死动作传感器（零网速损耗） |
| 私密 DNS (可选) | `python scripts/dns.py <status\|enable\|disable> [--device <serial>]` | 网络层过滤（国内网络需谨慎） |
| 全量/单机一键回滚 | `python scripts/rollback.py [--device <serial>] [--list] [--all]` | 恢复指定设备至初始状态 |

---

## 标准执行工作流

### 步骤 1：连接握手与设备探测
```bash
python scripts/probe.py
```
向用户汇报探测结果：手机品牌、型号、Android 版本、ROM 家族（如 OriginOS / HyperOS / ColorOS），以及已匹配的规则文件。

### 步骤 2：创建设备隔离快照
```bash
python scripts/snapshot.py
```
告知用户快照已生成，快照自动保存在 `snapshots/<device_id>/` 下，确保多台设备互相隔离不冲突。

### 步骤 3：诊断与交互式方案呈现（提问并等待确认）

1. 核心阶段 1：系统核心广告与遥测服务 (Tier 0 - 强力推荐，零网速影响)
   以 `dry-run` 预览匹配结果：
   ```bash
   python scripts/debloat.py dry-run rules/<brand>.json
   ```
   向用户展示匹配的系统广告清单，询问是否确认停用。

2. 核心阶段 2：第三方 App“摇一摇”开屏广告治理 (强力推荐，零网速影响)
   扫描手机上已安装的第三方高频广告应用：
   ```bash
   python scripts/shake.py scan
   ```
   向用户展示扫描到的应用，询问是否锁定动作传感器权限以阻断“走路晃动开屏误跳广告”。

3. 进阶阶段 3：系统级私密 DNS (DoT 协议过滤 - 默认不推荐，可选)
   说明其原理与网络取舍（Trade-off）：
   - 境外公共 DoT（如 `dns.adguard-dns.com`）在国内存在跨境握手延迟（200ms+）以及导致国内大厂 CDN 调度劣化的问题；
   - 核心系统广告和摇一摇广告已被阶段 1 和 2 本地彻底解决，无需强依赖此功能；
   - 询问用户是否确需开启（或告知其可在局域网自建 AdGuard Home / MosDNS 获取最佳效果）。

### 步骤 4：分阶段应用与闭环验证
收到用户确认后依次执行：
- 停用系统广告包：`python scripts/debloat.py apply rules/<brand>.json`
- 封杀摇一摇传感器：`python scripts/shake.py apply`
- 若用户明确要求开启 DNS：`python scripts/dns.py enable`

### 步骤 5：成果复核与提供回滚指南
- 重新运行 `python scripts/probe.py` 验证已停用数量。
- 告知用户若需要还原该设备，只需运行：`python scripts/rollback.py --device <serial>`。
