<div align="center">

# CUA Desktop Operator Skill

**Codex、Claude Code、Cursor、OpenCode などの MCP 対応 AI Agent 向け Windows デスクトップ操作スキル。**

<p>
  <a href="./README.md"><img alt="English" src="https://img.shields.io/badge/English-111827?style=for-the-badge&labelColor=111827&color=2563EB"></a>
  <a href="./README.zh-CN.md"><img alt="简体中文" src="https://img.shields.io/badge/简体中文-111827?style=for-the-badge&labelColor=111827&color=16A34A"></a>
  <a href="./README.ja.md"><img alt="日本語" src="https://img.shields.io/badge/日本語-111827?style=for-the-badge&labelColor=111827&color=DC2626"></a>
</p>

</div>

## 概要

このリポジトリは**そのまま skill として配置できる構成**です。リポジトリのルート自体が skill ルートです。

提供するもの:

- ローカル MCP server
- Windows デスクトップ実行 runtime
- 共通 skill インターフェース
- 再利用可能な macro
- タスク単位の一時成果物管理と cleanup

## 主な用途

- 現在のデスクトップ観測
- アプリ起動とフォーカス
- クリック、入力、貼り付け、スクロール、ホットキー
- 安定した GUI フローの macro 実行
- 複数 Agent 間で同じデスクトップ操作能力を共有

## クイックスタート

1. skills ディレクトリへクローンします:

```powershell
git clone https://github.com/Marways7/cua_desktop_operator_skill "$HOME\\.codex\\skills\\cua_desktop_operator_skill"
```

2. 依存関係をインストールします:

```powershell
.\scripts\setup_runtime.ps1
```

3. MCP server を起動します:

```powershell
.\scripts\start_mcp_server.ps1
```

4. `references/mcp-client-setup.md` を参照して Agent 側で MCP を設定します。

## ディレクトリ構成

```text
cua_desktop_operator_skill/
├─ SKILL.md
├─ agents/
├─ references/
├─ scripts/
├─ desktop_operator_core/
└─ desktop_operator_mcp/
```

## 一時ファイル方針

- スクリーンショット、JSON 状態、実行ログは一時成果物として扱います
- 既定ではローカル OS のディレクトリに保存し、リポジトリには書き戻しません
- タスク完了後は Agent が `desktop_cleanup_artifacts` を呼び出します
- ユーザーが保持を明示した場合のみ成果物を残します

詳細は英語版 README を参照してください:

- [README.md](./README.md)

## ライセンス

本プロジェクトは [GNU AGPL v3.0](./LICENSE) で公開します。

修正版を配布する場合や、修正版をサービスとして提供する場合は、同じライセンスで対応するソースコードを公開する前提です。

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Marways7/cua_desktop_operator_skill&type=Date)](https://star-history.com/#Marways7/cua_desktop_operator_skill&Date)
