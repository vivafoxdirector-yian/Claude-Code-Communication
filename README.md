# 🏢 aiorg — AI 조직 프레임워크

조직도를 YAML 로 선언하면, 각 구성원을 독립 Claude Code 세션(tmux)으로 세우고
그들 사이의 지시·보고·태스크를 파일 큐로 관리한다.

구성원은 전부 Claude 세션이다. **사람은 대표하고만 이야기한다.**

```bash
wsl                                    # Windows 라면 WSL 안에서
cd /mnt/c/git/yian/Claude-Code-Communication
./aiorg doctor                         # 환경 점검
./aiorg templates                      # 조직 템플릿 목록 (10종)
./aiorg up --org product-team          # 조직 구성
./aiorg launch                         # 각 자리에서 claude 기동
./aiorg status                         # 전원이 '대기' 가 될 때까지 확인
./aiorg brief                          # 각자에게 역할 안내
./aiorg attach ceo                     # 대표에게 목표를 지시
```

대표에게 목표를 말하면 부서장에게 쪼개 내려가고, 실무자가 만들고, 결과가 거꾸로 올라온다.
진행 상황은 다른 터미널에서 `./aiorg status`, `./aiorg task tree` 로 본다.

- **처음 시작한다면**: [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) — product-team 으로 처음부터 끝까지
- **사용법 전체**: `./aiorg help`
- **설계와 상세 문서**: [docs/AIORG.md](docs/AIORG.md)
- **조직 템플릿 10종**: [org/templates/](org/templates/) — solo(2) / minimal(4) / startup(5) / product-team(8) / two-po(8) / quality-first(8) / research(5) / research-build(10) / enterprise(14) / **existing-product(8, 기존 제품용)**
- **역할 지시서**: [org/roles/](org/roles/)

조직을 바꾸려면 조직도 YAML 만 고친다. 스크립트는 손대지 않는다.

---

## 이 아래는 전신(前身) 데모 문서

`setup.sh` / `agent-send.sh` / `instructions/` 로 동작하는 tmux 통신 데모다.
aiorg 로 대체되었으며 유지되지 않는다. 원본 프로젝트 문서를 그대로 남겨 둔다.

# 🤖 Tmux Multi-Agent Communication Demo

Agent同士がやり取りするtmux環境のデモシステム

**📖 Read this in other languages:** [English](README-en.md)

## 🎯 デモ概要

PRESIDENT → BOSS → Workers の階層型指示システムを体感できます

### 👥 エージェント構成

```
📊 PRESIDENT セッション (1ペイン)
└── PRESIDENT: プロジェクト統括責任者

📊 multiagent セッション (4ペイン)  
├── boss1: チームリーダー
├── worker1: 実行担当者A
├── worker2: 実行担当者B
└── worker3: 実行担当者C
```

## 🚀 クイックスタート

### 0. リポジトリのクローン

```bash
git clone https://github.com/nishimoto265/Claude-Code-Communication.git
cd Claude-Code-Communication
```

### 1. tmux環境構築

⚠️ **注意**: 既存の `multiagent` と `president` セッションがある場合は自動的に削除されます。

```bash
./setup.sh
```

### 2. セッションアタッチ

```bash
# マルチエージェント確認
tmux attach-session -t multiagent

# プレジデント確認（別ターミナルで）
tmux attach-session -t president
```

### 3. Claude Code起動

**手順1: President認証**
```bash
# まずPRESIDENTで認証を実施
tmux send-keys -t president 'claude' C-m
```
認証プロンプトに従って許可を与えてください。

**手順2: Multiagent一括起動**
```bash
# 認証完了後、multiagentセッションを一括起動
for i in {0..3}; do tmux send-keys -t multiagent:0.$i 'claude' C-m; done
```

### 4. デモ実行

PRESIDENTセッションで直接入力：
```
あなたはpresidentです。指示書に従って
```

## 📜 指示書について

各エージェントの役割別指示書：
- **PRESIDENT**: `instructions/president.md`
- **boss1**: `instructions/boss.md` 
- **worker1,2,3**: `instructions/worker.md`

**Claude Code参照**: `CLAUDE.md` でシステム構造を確認

**要点:**
- **PRESIDENT**: 「あなたはpresidentです。指示書に従って」→ boss1に指示送信
- **boss1**: PRESIDENT指示受信 → workers全員に指示 → 完了報告
- **workers**: Hello World実行 → 完了ファイル作成 → 最後の人が報告

## 🎬 期待される動作フロー

```
1. PRESIDENT → boss1: "あなたはboss1です。Hello World プロジェクト開始指示"
2. boss1 → workers: "あなたはworker[1-3]です。Hello World 作業開始"  
3. workers → ./tmp/ファイル作成 → 最後のworker → boss1: "全員作業完了しました"
4. boss1 → PRESIDENT: "全員完了しました"
```

## 🔧 手動操作

### agent-send.shを使った送信

```bash
# 基本送信
./agent-send.sh [エージェント名] [メッセージ]

# 例
./agent-send.sh boss1 "緊急タスクです"
./agent-send.sh worker1 "作業完了しました"
./agent-send.sh president "最終報告です"

# エージェント一覧確認
./agent-send.sh --list
```

## 🧪 確認・デバッグ

### ログ確認

```bash
# 送信ログ確認
cat logs/send_log.txt

# 特定エージェントのログ
grep "boss1" logs/send_log.txt

# 完了ファイル確認
ls -la ./tmp/worker*_done.txt
```

### セッション状態確認

```bash
# セッション一覧
tmux list-sessions

# ペイン一覧
tmux list-panes -t multiagent
tmux list-panes -t president
```

## 🔄 環境リセット

```bash
# セッション削除
tmux kill-session -t multiagent
tmux kill-session -t president

# 完了ファイル削除
rm -f ./tmp/worker*_done.txt

# 再構築（自動クリア付き）
./setup.sh
```

---

## 📄 ライセンス

このプロジェクトは[MIT License](LICENSE)の下で公開されています。

## 🤝 コントリビューション

プルリクエストやIssueでのコントリビューションを歓迎いたします！

---

🚀 **Agent Communication を体感してください！** 🤖✨ 