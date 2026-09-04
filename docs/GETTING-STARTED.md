# 처음부터 조직 만들어 돌리기

`product-team`(8명) 을 예로 처음부터 끝까지 따라간다.
전체 15분쯤 걸리고, 대부분은 조직이 일하는 것을 지켜보는 시간이다.

설계 배경과 각 설정의 자세한 뜻은 [AIORG.md](AIORG.md) 를 본다.
여기서는 **손으로 무엇을 하는지**만 순서대로 적는다.

---

## 0. 준비 — 한 번만

tmux 가 필요하므로 Windows 라면 WSL 안에서 한다.

```bash
wsl
cd /mnt/c/git/yian/Claude-Code-Communication
./aiorg doctor
```

```
환경 점검
  AIORG_HOME : /mnt/c/git/yian/Claude-Code-Communication
  나          :
  tmux       : /usr/bin/tmux
  git        : /usr/bin/git
  python3    : Python 3.12.3
  PyYAML     : 설치됨
  claude     : 2.1.260 (Claude Code)

이상 없습니다.
```

`나 :` 가 비어 있는 게 정상이다. 당신은 조직 밖의 운영자다.

**여기서 한 번 더 확인할 것이 있다.** WSL 의 `claude` 는 Windows 쪽 설치와
별개이고 로그인도 따로다. 안 되어 있으면 구성원 전원이 `로그인필요` 로 멈춘다.

```bash
claude          # 뜨면 로그인 상태 확인. 필요하면 /login. 확인했으면 Ctrl-D
```

---

## 1. 내 조직도 만들기

템플릿을 직접 고치지 않는다. 복사해서 쓴다.

```bash
./aiorg templates          # 어떤 템플릿이 있는지
./aiorg new product-team mycorp
```

```
만들었습니다: org/mycorp.yaml  (템플릿: product-team)
  띄우기: ./aiorg up --org mycorp
```

`org/mycorp.yaml` 이 이제 **당신 조직도**다. 프레임워크를 갱신해도 덮이지 않는다.
지금은 고칠 것이 없다 — `workdir` 이 `"."` 이라 이 저장소에서 일한다.

> 이미 있는 제품에 붙이려면 `product-team` 대신 `existing-product` 를 복사하고
> `org.workdir` 을 제품 저장소 경로로 바꾼다. [AIORG.md](AIORG.md) 참고.

---

## 2. 조직 세우기

```bash
./aiorg up --org mycorp
```

```
조직도 해석 완료: /mnt/c/git/yian/Claude-Code-Communication/org/mycorp.yaml
  조직명 : AI Dev Corp
  멤버   : 8명   배치: windows
  세션 exec      : ceo
  세션 dev       : dev-lead, dev-1, dev-2
  세션 product   : po
  세션 biz       : presales
  세션 qa        : qa-lead, qa-1

tmux 세션 구성 중 (배치: windows)...
  aiorg-exec ← ceo
  aiorg-dev ← dev-lead dev-1 dev-2
  aiorg-product ← po
  aiorg-biz ← presales
  aiorg-qa ← qa-lead qa-1

다음 순서:
  ./aiorg launch          각 자리에서 claude 기동
  ./aiorg status          전원이 '대기' 가 될 때까지 확인
  ./aiorg brief           각자에게 역할·지시서 안내
  ./aiorg attach ceo      대표 화면에 붙어 목표를 지시
```

tmux 세션 5개(부서 5개)에 자리 8개가 생겼다. 아직 claude 는 안 떴다.

여기서 **경고가 나오면 읽는다.** 조직도에 문제가 있으면 알려준다
(담당 없는 코드 영역, 이전 조직에서 남은 태스크, 스킬이 안 보이는 멤버 등).

---

## 3. claude 기동

```bash
./aiorg launch
```

```
claude 기동 중 (명령: claude)...
  ceo 기동
  dev-lead 기동
  ...
8 명 기동. 첫 실행이라면 각 pane 에서 인증을 마쳐야 합니다.
```

**첫 실행이면 각 자리에서 폴더 신뢰 확인 대화상자가 뜬다.** 사람이 답해야 한다
(권한 승인이라 자동으로 눌러주지 않는다). 20~30초 뒤 확인한다.

```bash
./aiorg status
```

`응답대기` 인 멤버가 있으면 붙어서 답한다.

```bash
./aiorg attach dev-1      # 1 을 고르고 Enter, 그다음 Ctrl-b d 로 빠져나온다
```

전원이 `대기` 가 되면 다음으로 간다.

```
👑 ceo          대표             [대기]
|- 🎯 dev-lead     개발팀장         [대기]
|  |- 🔧 dev-1        백엔드 개발자    [대기]
|  `- 🔧 dev-2        프론트엔드 개발자 [대기]
|- 📋 po           제품 책임자      [대기]
|- 📣 presales     프리세일즈       [대기]
`- 🎯 qa-lead      품질팀장         [대기]
   `- 🔍 qa-1         코드 리뷰어      [대기]
```

---

## 4. 각자에게 역할 알리기

```bash
./aiorg brief
```

```
  ceo 지시서 안내 전달
  dev-lead 지시서 안내 전달
  ...
8 명에게 전달.
이제 대표에게 목표를 지시하세요:  ./aiorg attach ceo
```

각자 자기 역할 지시서(`org/roles/*.md`)와 공통 프로토콜을 읽는다.
40초쯤 걸린다. **이걸 건너뛰면 구성원이 벨을 받고도 무엇을 할지 모른다.**

---

## 5. 알림 지킴이 띄우기 (권장)

**별도 터미널**에서 띄워두고 조직이 도는 내내 켜 둔다.

```bash
wsl
cd /mnt/c/git/yian/Claude-Code-Communication
./aiorg notify --watch
```

상대가 작업 중일 때 보낸 메시지는 벨이 보류된다. 이게 재시도해 준다.
**안 켜면 보류된 메시지가 계속 안 간다.**

---

## 6. 대표에게 목표를 말한다

여기서부터가 본론이다. 사람이 상대하는 것은 **대표 하나뿐**이다.

```bash
./aiorg attach ceo
```

프롬프트에 평소 Claude Code 쓰듯 사람 말로 말한다.

```
사내에서 쓸 URL 단축기를 만들려고 합니다.
긴 URL 을 짧은 코드로 바꾸고, 그 코드로 접속하면 원래 주소로 보내주는 것입니다.
통계나 사용자 계정은 이번 범위에서 제외합니다. 진행해 주세요.
```

`Ctrl-b d` 로 빠져나온다. 세션은 계속 산다.

**목적·범위·제외 범위를 함께 주는 것이 좋다.** 제외 범위를 안 적으면
조직이 알아서 범위를 넓힌다.

---

## 7. 지켜보기

운영자 터미널에서 본다. 조직 안에 들어갈 필요 없다.

```bash
./aiorg status
```

```
 멤버   : 8명    태스크 : 전체 4건 / 진행중 3건
--------------------------------------------------------------
👑 ceo          대표             [대기]   미확인 1
|- 🎯 dev-lead     개발팀장         [대기]   진행 1
|  |- 🔧 dev-1        백엔드 개발자    [대기]
|  `- 🔧 dev-2        프론트엔드 개발자 [대기]
|- 📋 po           제품 책임자      [대기]   미확인 1
|- 📣 presales     프리세일즈       [대기]
`- 🎯 qa-lead      품질팀장         [대기]   진행 1
   `- 🔍 qa-1         코드 리뷰어      [대기]   진행 1
```

```bash
./aiorg task tree
```

```
[>] t_6f631890  URL 단축기 구현  (dev-lead)
[x] t_i15j267d  URL 단축기 요구사항 정의서 작성  (po)
[!] t_zmroexhb  URL 단축기 품질 검증  (qa-lead)
`- [>] t_1ntr7st8  URL 단축기 검증 시나리오 준비  (qa-1)
```

대표가 목표를 셋으로 쪼갰다 — 기획(po), 구현(dev-lead), 품질(qa-lead).
`[x]` 는 완료, `[>]` 는 진행 중, `[!]` 는 **막힘**이다.

여기서 `qa-lead` 가 `[!]` 인 것은 정상이다. 구현이 끝나야 검증할 수 있으니
선행 대기를 `blocked` 로 표시한 것이다. 조용히 기다리지 않고 표시했기 때문에
**당신 눈에 보인다.**

무슨 일이 있었는지 순서대로 보려면:

```bash
./aiorg log --limit 20
```

### 읽어야 할 신호

| 보이는 것 | 뜻 | 할 일 |
|---|---|---|
| **미확인**이 줄지 않음 | 벨이 안 갔거나 무시 중 | `./aiorg notify` |
| `[!]` **blocked** | 지금 조직의 병목 | `./aiorg task show <id>` 로 이유 확인 |
| 전원 `대기`인데 태스크가 남음 | 관리자가 배정을 안 함 | 대표에게 물어본다 |
| `응답대기` | 대화상자가 떠서 멈춤 | `./aiorg attach <멤버>` |
| `로그인필요` | 인증 끊김 | 붙어서 `/login` |

---

## 8. 결과 확인

대표에게 물어보는 게 가장 쉽다.

```bash
./aiorg attach ceo
```

```
지금까지 뭐가 됐고 뭐가 남았나요?
```

대표는 조직 내부 사정(태스크 id 나열)이 아니라 **무엇이 완성됐고, 무엇이 남았고,
무엇을 결정해야 하는지**를 사람 말로 정리해 답하도록 되어 있다.

파일로 직접 볼 수도 있다.

```bash
./aiorg task show <태스크id>     # 산출물 경로, 브랜치, 상태 이력
git log --oneline -20
git status --short               # 조직이 새로 만든 파일
```

위 예시(URL 단축기)를 실제로 돌렸을 때 나온 것:

```
docs/product/specs/url-shortener.md        149줄   PO — 요구사항 정의서
docs/adr/ADR-0001-url-shortener-stack.md    58줄   개발팀장 — 기술 선택 기록
docs/qa/url-shortener-checklist.md         175줄   품질팀 — 검증 시나리오
```

`docs/adr/` 는 시키지 않은 것이다. 개발팀장 역할에
`use_skills: [architecture-decision]` 이 걸려 있어서, 기술 스택을 정할 때
그 스킬을 불러 결정 기록을 남긴 것이다. 조직도에 스킬을 걸어두면
이렇게 각자 자기 일에 맞는 스킬을 쓴다.

---

## 9. 중간에 끼어들기

**대표에게 말하면 된다.** 범위를 바꾸거나, 우선순위를 조정하거나, 멈추라고 할 때
전부 대표 프롬프트에 사람 말로 말한다.

```bash
./aiorg attach ceo
```

```
QA 검증은 이번엔 건너뛰고 구현부터 끝내 주세요.
```

**부하에게 직접 말하지 않는다.** 조직도를 무너뜨리고, 대표가 무슨 일이
벌어지는지 모르게 된다.

고객이 한 말을 **근거로 남기려면** 대표에게 말하는 게 아니라
`docs/voc/raw/` 에 원문 파일로 넣는다. 이유는 [voc/README.md](voc/README.md) 에 있다.

---

## 10. 조직 내리기

```bash
./aiorg down
```

```
aiorg-exec 종료
aiorg-dev 종료
...
조직 세션을 내렸습니다. 메시지·태스크 기록은 runtime/ 에 남아 있습니다.
```

**태스크·수신함·산출물은 지워지지 않는다.** 사라지는 것은 tmux 세션과
구성원의 Claude 대화 맥락뿐이다.

### 다시 올릴 때

```bash
./aiorg up --org mycorp
./aiorg launch
./aiorg brief          # <- 반드시. 자기가 누구인지 다시 알려줘야 한다
```

`brief` 를 빼먹으면 구성원이 벨을 받고도 `aiorg inbox` 를 모른다.
읽지 않은 메시지와 진행 중이던 태스크는 그대로 있으므로, `brief` 후
각자 자기 일을 되찾는다.

### 완전히 처음부터 하려면

```bash
./aiorg down
rm -rf runtime          # 메시지·태스크·로그가 전부 사라진다. 되돌릴 수 없다
```

`docs/` 의 산출물은 지워지지 않는다.

---

## 자주 겪는 것

**전원이 `미가동` 이다**
`./aiorg launch` 를 안 했거나 claude 가 뜨다 실패했다. `./aiorg attach <멤버>` 로
직접 보면 화면에 이유가 있다.

**한 명만 이상하다**
```bash
./aiorg explain <멤버>
```
어떤 화면 표지가 걸려서 그렇게 판정됐는지 보여준다. Claude Code 판올림으로
화면이 바뀌면 `lib/tmuxlib.sh` 상단의 `AIORG_PAT_*` 를 고친다.

**메시지를 보냈는데 `대기(수신자 작업중...)` 라고 나온다**
정상이다. 메시지는 이미 수신함 파일에 안전하게 들어갔다.
`./aiorg notify` 를 돌리거나 `--watch` 를 켜두면 상대가 한가해질 때 간다.

**조직이 엉뚱한 것을 만들고 있다**
대표에게 준 목표에 **제외 범위**가 없었을 가능성이 높다.
대표에게 말해 범위를 좁힌다.

**같은 일을 두 명이 하고 있다**
관리자가 태스크에 파일 범위를 안 적었다.
기존 제품이라면 조직도의 `areas` 로 코드 영역을 나눠 준다.

---

## 다음 단계

- **다른 조직 모양** — `./aiorg templates` (10종). 기획만 하는 `research`,
  리뷰를 두 배로 두는 `quality-first`, 기존 제품용 `existing-product` 등
- **조직도를 내 손으로 고치기** — `org/mycorp.yaml` 하나가 조직의 전부다.
  각 설정의 뜻은 [AIORG.md](AIORG.md)
- **역할을 고치거나 새로 만들기** — `org/roles/*.md`. 지시서가 곧 그 역할의 행동이다
