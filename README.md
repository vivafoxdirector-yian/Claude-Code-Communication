# 🤖 Tmux Multi-Agent Communication Demo

Agent 간 통신을 위한 tmux 환경 데모 시스템

**📖 Read this in other languages:** [English](README-en.md)

## 🎯 데모 개요

PRESIDENT → BOSS → Workers 의 계층형 지시 시스템을 체험할 수 있습니다

### 👥 에이전트 구성

```
📊 PRESIDENT 세션 (1페인)
└── PRESIDENT: 프로젝트 총괄 책임자

📊 multiagent 세션 (4페인)
├── boss1: 팀 리더
├── worker1: 실행 담당자A
├── worker2: 실행 담당자B
└── worker3: 실행 담당자C
```

## 🚀 퀵 스타트

### 0. 리포지토리 클론

```bash
git clone https://github.com/nishimoto265/Claude-Code-Communication.git
cd Claude-Code-Communication
```

### 1. tmux 환경 구축

⚠️ **주의**: 기존의 `multiagent` 와 `president` 세션이 있는 경우 자동으로 삭제됩니다.

```bash
./setup.sh
```

### 2. 세션 어태치

```bash
# 멀티에이전트 확인
tmux attach-session -t multiagent

# 프레지던트 확인 (별도 터미널에서)
tmux attach-session -t president
```

### 3. Claude Code 기동

**순서1: President 인증**
```bash
# 먼저 PRESIDENT에서 인증을 실시
tmux send-keys -t president 'claude' C-m
```
인증 프롬프트에 따라 허가를 부여해 주세요.

**순서2: Multiagent 일괄 기동**
```bash
# 인증 완료 후, multiagent 세션을 일괄 기동
for i in {0..3}; do tmux send-keys -t multiagent:0.$i 'claude' C-m; done
```

### 4. 데모 실행

PRESIDENT 세션에서 직접 입력:
```
당신은 president입니다. 지시서에 따라주세요
```

## 📜 지시서에 대하여

각 에이전트의 역할별 지시서:
- **PRESIDENT**: `instructions/president.md`
- **boss1**: `instructions/boss.md`
- **worker1,2,3**: `instructions/worker.md`

**Claude Code 참조**: `CLAUDE.md` 에서 시스템 구조를 확인

**요점:**
- **PRESIDENT**: "당신은 president입니다. 지시서에 따라주세요" → boss1에 지시 전송
- **boss1**: PRESIDENT 지시 수신 → workers 전원에게 지시 → 완료 보고
- **workers**: Hello World 실행 → 완료 파일 작성 → 마지막 사람이 보고

## 🎬 기대되는 동작 흐름

```
1. PRESIDENT → boss1: "당신은 boss1입니다. Hello World 프로젝트 시작 지시"
2. boss1 → workers: "당신은 worker[1-3]입니다. Hello World 작업 시작"
3. workers → ./tmp/파일 작성 → 마지막 worker → boss1: "전원 작업 완료했습니다"
4. boss1 → PRESIDENT: "전원 완료했습니다"
```

## 🔧 수동 조작

### agent-send.sh를 사용한 전송

```bash
# 기본 전송
./agent-send.sh [에이전트명] [메시지]

# 예시
./agent-send.sh boss1 "긴급 태스크입니다"
./agent-send.sh worker1 "작업 완료했습니다"
./agent-send.sh president "최종 보고입니다"

# 에이전트 목록 확인
./agent-send.sh --list
```

## 🧪 확인 및 디버그

### 로그 확인

```bash
# 전송 로그 확인
cat logs/send_log.txt

# 특정 에이전트의 로그
grep "boss1" logs/send_log.txt

# 완료 파일 확인
ls -la ./tmp/worker*_done.txt
```

### 세션 상태 확인

```bash
# 세션 목록
tmux list-sessions

# 페인 목록
tmux list-panes -t multiagent
tmux list-panes -t president
```

## 🔄 환경 리셋

```bash
# 세션 삭제
tmux kill-session -t multiagent
tmux kill-session -t president

# 완료 파일 삭제
rm -f ./tmp/worker*_done.txt

# 재구축 (자동 클리어 포함)
./setup.sh
```

---

## 📄 라이선스

이 프로젝트는 [MIT License](LICENSE) 하에 공개되어 있습니다.

## 🤝 컨트리뷰션

풀 리퀘스트나 Issue를 통한 컨트리뷰션을 환영합니다!

---

🚀 **Agent Communication 을 체험해 보세요!** 🤖✨
