<div align="center">

# CUA Desktop Operator Skill

**面向 Codex、Claude Code、Cursor、OpenCode 等 MCP Agent 的 Windows 桌面操作技能。**

<p>
  <a href="./README.md"><img alt="English" src="https://img.shields.io/badge/English-111827?style=for-the-badge&labelColor=111827&color=2563EB"></a>
  <a href="./README.zh-CN.md"><img alt="简体中文" src="https://img.shields.io/badge/简体中文-111827?style=for-the-badge&labelColor=111827&color=16A34A"></a>
  <a href="./README.ja.md"><img alt="日本語" src="https://img.shields.io/badge/日本語-111827?style=for-the-badge&labelColor=111827&color=DC2626"></a>
</p>

</div>

## 项目定位

这是一个**可直接作为 skill 克隆使用**的仓库。仓库根目录就是 skill 根目录。

它提供：

- 本地 MCP server
- Windows 桌面执行 runtime
- 通用 skill 接口
- 可复用宏动作
- 任务级临时产物管理与清理

## 适用场景

- 观察当前桌面
- 打开或聚焦应用
- 点击、输入、粘贴、滚动、热键
- 通过宏完成稳定的 GUI 流程
- 让不同 AI Agent 共享同一套桌面执行能力

## 快速开始

1. 把仓库克隆到某个 skills 目录，例如：

```powershell
git clone <your-repo-url> "$HOME\\.codex\\skills\\cua_desktop_operator_skill"
```

2. 安装依赖：

```powershell
.\scripts\setup_runtime.ps1
```

3. 启动 MCP server：

```powershell
.\scripts\start_mcp_server.ps1
```

4. 按 `references/mcp-client-setup.md` 给你的 Agent 配置 MCP。

## 目录结构

```text
cua_desktop_operator_skill/
├─ SKILL.md
├─ agents/
├─ references/
├─ scripts/
├─ desktop_operator_core/
└─ desktop_operator_mcp/
```

## 临时文件策略

- 默认把截图、状态 JSON、执行日志当作临时产物
- 默认存到本地系统目录，不写回仓库
- 任务完成后，Agent 应调用 `desktop_cleanup_artifacts`
- 如果用户明确要求保留调试证据，再保留这些产物

更多细节请查看英文主 README：

- [README.md](./README.md)

## 许可证

本项目使用 [GNU AGPL v3.0](./LICENSE)。

这意味着分发修改版，或以服务形式提供修改版时，应继续以相同许可证公开对应源码。

## Star History

发布到 GitHub 后，把下面的 `OWNER/REPO` 替换成真实仓库名：

[![Star History Chart](https://api.star-history.com/svg?repos=OWNER/REPO&type=Date)](https://star-history.com/#OWNER/REPO&Date)
