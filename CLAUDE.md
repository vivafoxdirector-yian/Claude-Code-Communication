# Agent Communication System

## 에이전트 구성
- **PRESIDENT** (별도 세션): 총괄 책임자
- **boss1** (multiagent:agents): 팀 리더
- **worker1,2,3** (multiagent:agents): 실행 담당

## 당신의 역할
- **PRESIDENT**: @instructions/president.md
- **boss1**: @instructions/boss.md
- **worker1,2,3**: @instructions/worker.md

## 메시지 전송
```bash
./agent-send.sh [상대] "[메시지]"
```

## 기본 흐름
PRESIDENT → boss1 → workers → boss1 → PRESIDENT
