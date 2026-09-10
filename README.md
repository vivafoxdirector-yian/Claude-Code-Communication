# 🏢 aiorg — AI 조직 프레임워크

조직도를 YAML 로 선언하면, 각 구성원을 독립 Claude Code 세션(tmux)으로 세우고
그들 사이의 지시·보고·태스크를 파일 큐로 관리한다.

**구성원은 전부 Claude 세션이고, 사람은 대표하고만 이야기한다.**
대표에게 목표를 말하면 부서장에게 쪼개 내려가고, 실무자가 만들고, 결과가 거꾸로 올라온다.

```
👑 ceo       대표  [exec]
   |- 🎯 dev-lead  개발팀장  [dev]
   |  |- 🔧 dev-1     백엔드 개발자  [dev]
   |  `- 🔧 dev-2     프론트엔드 개발자  [dev]
   |- 📋 po        제품 책임자  [product]
   |- 📣 presales  프리세일즈  [biz]
   `- 🎯 qa-lead   품질팀장  [qa]
      `- 🔍 qa-1      코드 리뷰어  [qa]
```

대괄호 안은 tmux 세션(부서)이다. `./aiorg chart product-team` 이 그린 것이다.

## 빠른 시작

tmux 가 필요하다. Windows 라면 WSL 안에서 한다.

```bash
./aiorg doctor                    # 환경 점검 (tmux, python3, PyYAML, claude, 스킬)
./aiorg skills --link             # 스킬을 어디서든 보이게 (한 번만)
```

**조직이 일할 곳은 이 저장소가 아니다.** 제품 저장소를 따로 두고 조직도에 적는다.

```bash
mkdir -p ~/myproduct && cd ~/myproduct && git init && cd -
./aiorg new product-team mycorp   # org/mycorp.yaml 로 복사
#   org/mycorp.yaml 의 org.workdir 을 "/home/사용자/myproduct" 로 고친다
```

```bash
./aiorg up --org mycorp           # tmux 세션 구성 + 알림 지킴이
./aiorg scaffold                  # 산출물 자리와 구성원 권한을 제품 저장소에
./aiorg launch                    # 각 자리에서 claude 기동
./aiorg status                    # 전원이 '대기' 가 될 때까지
./aiorg brief                     # 각자에게 역할 안내  <- 빼먹으면 조직이 안 생긴다
./aiorg attach ceo                # 대표에게 목표를 말한다. Ctrl-b d 로 나온다
```

지켜보는 것은 조직 밖에서 한다 — 붙을 필요가 없다.

```bash
./aiorg status                    # 누가 무엇을 하고, 어디가 막혔나
./aiorg task tree                 # 태스크 갈래
./aiorg peek dev-1                # 그 자리 화면만 (입력은 안 들어간다)
./aiorg layout                    # 누가 어느 세션·창·pane 에 있나
```

## 문서

| | |
|---|---|
| [docs/CHEATSHEET.md](docs/CHEATSHEET.md) | **명령만** 빠르게 찾을 때 |
| [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) | 빈 저장소에서 처음부터 끝까지 |
| [docs/EXISTING-PRODUCT.md](docs/EXISTING-PRODUCT.md) | **이미 있는 제품**에 붙이기 (areas·워킹트리·저장소 여럿) |
| [docs/AIORG.md](docs/AIORG.md) | 설계 배경과 전체 설정 |
| `./aiorg help` | 명령 요약 |

## 조직 템플릿 10종

```bash
./aiorg templates                 # 목록
./aiorg chart enterprise          # 조직도를 그림으로
```

`solo`(2) · `minimal`(4) · `startup`(5) · `research`(5) · `product-team`(8) ·
`two-po`(8) · `quality-first`(8) · `existing-product`(8) · `research-build`(10) ·
`enterprise`(14). 그림은 [org/templates/README.md](org/templates/README.md) 에 있다.

**조직을 바꾸려면 조직도 YAML 만 고친다.** 스크립트는 손대지 않는다.
역할 지시서는 [org/roles/](org/roles/) 에 있고, 그 문서가 곧 그 역할의 행동이다.

## 사람이 조직에 넣는 것 — 경로는 둘이다

| | 대표에게 말하기 | `docs/voc/raw/` 에 파일 넣기 |
|---|---|---|
| 무엇인가 | 주인의 뜻 | 고객이 한 말 |
| 무게 | **결정.** 근거를 묻지 않는다 | **근거.** 채택은 PO 와 대표가 판단 |

**구성원에게는 고객 접점이 없다.** 그대로 "VOC 를 가져와라" 하면 그럴듯하게
지어낸다. 그래서 원천을 사람으로 못 박았다 — `raw/` 에 없으면 VOC 가 아니다.

**비용도 같다.** 청구 시스템 접점이 없으므로 숫자는 사람이 `docs/finops/raw/` 에
넣은 것에서만 나온다. 비어 있으면 PO 는 "비용 자료가 없습니다" 라고 보고한다.

## 규약이 아니라 코드가 지킨다

문서로만 정해둔 것은 지켜지지 않는다는 것을 여러 번 확인했고, 그럴 때마다
기계가 막게 바꿨다.

- **커밋 가드** — 구성원이 이 프레임워크 저장소에 커밋하면 훅이 거부한다
- **운영자 명령 차단** — 구성원이 `up`·`down`·`clean` 을 쓰면 `aiorg` 가 거부한다
- **워킹트리** — 여러 명이 같은 저장소에서 일하면 서로의 브랜치를 갈아치운다
- **세션 주인 표시** — 저장소를 복사해 둘을 돌려도 남의 조직을 죽이지 않는다
- **경고** — 담당 없는 코드 영역, 지시서 안내를 못 받은 멤버, 꺼진 알림 지킴이,
  신뢰 확인이 안 된 작업 디렉터리

## 요구 사항

`tmux` · `git` · `python3` + `PyYAML` · `claude`. `./aiorg doctor` 가 확인해 준다.
Windows 의 WSL 에서 쓰는 경우, WSL 의 `claude` 는 Windows 쪽과 **별개 설치이고
로그인도 따로**다.

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