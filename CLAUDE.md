# AI 조직 프레임워크 (aiorg)

조직도를 YAML 로 선언하면, 각 구성원을 독립 Claude Code 세션(tmux)으로 세우고
그들 사이의 지시·보고·태스크를 파일 큐로 관리하는 프레임워크다.

## 이 저장소는 프레임워크다 — 산출물을 여기 만들지 않는다

**여기서 만드는 것은 aiorg 자체이고, aiorg 로 만든 결과물이 아니다.**

조직이 일할 곳은 `org.workdir` 로 지정하는 **제품 저장소**다. 코드도, 요구사항
정의서도, 설계도, VOC 도 그쪽에 쌓인다. 이 저장소에는 프레임워크와 그 문서만 둔다.

- `workdir` 을 안 바꾸고 조직을 돌리면 `up` 이 경고한다. 한 번 시험하는 것이라면
  괜찮지만, 끝나고 `git status` 로 남은 것을 확인하고 지운다
- `docs/` 에는 규약을 설명하는 README 만 있다. `specs/`, `raw/` 같은 산출물 자리는
  제품 저장소에 만든다 — `./aiorg scaffold` 가 만들어 준다
- `runtime/`(조직 상태)과 `worktrees/`(작업 트리)는 git 에서 제외된다

## 이 세션에서 당신이 누구인지 먼저 확인한다

```bash
./aiorg whoami
```

- **id 가 출력되면** 당신은 그 조직의 구성원이다. 아래 두 문서를 읽고 그대로 따른다.
  1. `org/roles/_protocol.md` — 전원 공통 통신 규칙 (필독)
  2. 자기 역할 지시서 — `./aiorg members` 의 마지막 열에 경로가 있다
     (`ceo.md`, `manager.md`, `engineer.md`, `reviewer.md`, `po.md`, `presales.md`)

  구성원으로서 지켜야 할 핵심:
  - 다른 멤버의 tmux pane 을 직접 조작하지 않는다. 통신은 `./aiorg` 명령으로만 한다.
  - 조직도를 지킨다. 지시는 상급자에게 받고, 보고는 직속 상급자에게 한다.
  - 태스크 상태를 반드시 갱신한다 (`task start` / `done` / `block`).
  - `./aiorg up`, `launch`, `brief`, `down` 은 운영자용이다. 구성원은 쓰지 않는다.

- **아무것도 출력되지 않으면** 당신은 운영자 쪽 세션이다. 조직을 세우고 관찰하는 입장이다.

## 운영 명령

```bash
./aiorg doctor                  # 실행 환경 점검 (tmux, python3, PyYAML, claude)
./aiorg templates               # 조직 템플릿 목록 (10종)
./aiorg new <템플릿> [이름]      # 템플릿을 org/<이름>.yaml 로 복사
./aiorg up [--org 이름]         # 조직도대로 tmux 세션 구성
./aiorg launch                  # 각 자리에서 claude 기동
./aiorg brief                   # 각자에게 역할·지시서 안내 전달
./aiorg status                  # 조직도 + 각자 상태 + 미확인/진행 현황
./aiorg areas                   # 코드 영역과 담당자 (기존 제품에 붙였을 때)
./aiorg skills [--link]         # 프레임워크 스킬을 어디서든 보이게 연결
./aiorg attach [멤버]            # 특정 멤버 화면에 붙기
./aiorg layout                  # tmux 배치 (세션·창·자리·상태) 한 표로
./aiorg peek <멤버> [-n N]      # 붙지 않고 그 자리 화면만 보기
./aiorg notify [--watch]        # 보류된 알림 재시도 (up 이 지킴이를 띄워둔다)
./aiorg down                    # 세션 종료 (기록은 runtime/ 에 남음)
./aiorg clean [--force]         # runtime/ 정리 (무엇을 잃는지 먼저 보여준다)
./aiorg log                     # 이벤트 로그
```

명령만 빠르게 찾으려면 [docs/CHEATSHEET.md](docs/CHEATSHEET.md).
처음 돌려본다면 [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) 를 따라간다.
이미 있는 제품에 붙이려면 [docs/EXISTING-PRODUCT.md](docs/EXISTING-PRODUCT.md).
전체 사용법은 `./aiorg help`, 설계 배경과 상세는 [docs/AIORG.md](docs/AIORG.md).

## 사람이 조직에 넣는 것 — 경로는 둘이다

| | 대표에게 말하기 | `docs/voc/raw/` 에 파일 넣기 |
|---|---|---|
| 무엇인가 | 주인의 뜻 | 고객이 한 말 |
| 다루는 법 | 지시. 근거를 묻지 않는다 | 자료. 원문이 증거로 남는다 |
| 무게 | **결정** | 입력일 뿐. 채택은 PO·대표가 판단 |

주인의 말은 결정이고, 고객의 말은 근거다.
**대표에게 구두로 한 고객 이야기는 VOC 가 아니라 주인의 판단으로 처리된다** —
고객 근거로 둔갑시키면 PO 가 확인할 원문이 없기 때문이다.
근거로 남기려면 `docs/voc/raw/` 를 거쳐야 한다. 안내는 [docs/voc/README.md](docs/voc/README.md).

**비용도 같다.** 구성원에게는 청구 시스템 접점이 없으므로, 숫자는 사람이
`docs/finops/raw/` 에 넣은 것에서만 나온다. 비어 있으면 PO 는 "비용 자료가 없습니다"
라고 보고한다. 안내는 [docs/finops/README.md](docs/finops/README.md).

## 실행 환경

tmux 가 필요하다. Windows 에서는 WSL 안에서 실행한다.

```bash
wsl
cd /mnt/c/git/yian/Claude-Code-Communication
./aiorg doctor
```

## 구조

| 경로 | 역할 |
|---|---|
| `aiorg` | CLI 진입점 (bash) |
| `lib/orgstate.py` | 조직도 해석, 메시지 큐, 태스크, 이벤트 로그 |
| `lib/tmuxlib.sh` | tmux 세션 구성, 상태 감지, 알림 전달 |
| `org/templates/*.yaml` | 조직 템플릿 10종. 직접 고치지 말고 `new` 로 복사해 쓴다 |
| `org/*.yaml` | 내 조직도 — 이 파일만 고치면 조직이 바뀐다. git 추적 안 함 |
| `org/roles/*.md` | 역할별 지시서 |
| `runtime/` | 조직 상태 (메시지 큐, 태스크, 로그). 저절로 안 사라진다 — `./aiorg clean` |
| `worktrees/` | git 워킹트리. **커밋 안 된 코드가 있을 수 있어 runtime/ 과 분리** |
| `docs/voc/raw/` | 고객 발언 원문. **사람만 쓴다** — 구성원은 읽기 전용 |
| `docs/finops/` | 청구·사용 자료 규약. `raw/` 는 **사람만 쓴다**. PO 가 분석 |
| `docs/sales/` | 영업 자료 (프리세일즈 작성 → PO 사실확인 → 대표 승인) |
| `docs/product/` | 조사 결과, 요구사항 정의서 (PO 작성) |

## 이전 데모 (참고용)

`setup.sh`, `agent-send.sh`, `instructions/` 는 이 프레임워크의 전신인
tmux 통신 데모다. aiorg 로 대체되었으며 유지되지 않는다.
`dictionaries/common_business_terms.yaml` 은 Whisper 사전용 파일로 이 시스템과 무관하다.
