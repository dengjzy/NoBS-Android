# NoBS-Android AI Agent Prompt Template

无需克隆代码仓库，只需将以下提示词直接复制并发送给具备终端或 ADB 执行能力的 AI 编码助手（如 Claude Code, Cursor, Antigravity 等）：

---

```markdown
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
