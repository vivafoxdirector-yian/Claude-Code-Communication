# 이미 있는 제품에 조직 붙이기

빈 저장소에서 시작하는 것은 [GETTING-STARTED.md](GETTING-STARTED.md) 를 본다.
여기서는 **이미 코드가 있는 제품**에 조직을 붙인다. 다른 점은 셋이다.

| | 새로 만들 때 | 기존 제품 |
|---|---|---|
| 코드 위치 | 조직이 정한다 | **`areas` 로 내가 선언한다** |
| 작업 공간 | 전원이 한 디렉터리 | **각자 git 워킹트리** |
| 결과 수확 | 그냥 커밋되어 있다 | **브랜치를 병합해야 한다** |

셋 중 둘째가 가장 중요하다. 이유는 5 장에 있다.

---

## 0. 준비

[GETTING-STARTED 0 장](GETTING-STARTED.md#0-준비--한-번만)과 같다.
`./aiorg doctor`, `./aiorg skills --link`, 그리고 **제품 저장소를 한 번 신뢰해 둔다.**

```bash
cd /경로/내제품 && claude     # ↓ 로 'Yes, I trust this folder' 로 옮기고 Enter, Ctrl-D
```

안 해두면 구성원 전원이 신뢰 확인 대화상자 앞에서 멈춘다.

## 1. 제품 저장소를 확인한다

**git 저장소여야 한다.** 워킹트리를 쓰려면 필수다.

```bash
cd /경로/내제품
git status              # 깨끗한 상태에서 시작하는 편이 낫다
ls                      # 프론트/백엔드가 각각 어느 디렉터리인지 확인
```

커밋 안 된 변경이 남아 있으면 워킹트리를 만들 때 헷갈린다. 먼저 정리하거나
커밋해 둔다.

## 2. 조직도 만들기

```bash
./aiorg new existing-product mycorp
```

`existing-product` 는 8명이다 — 대표, PO, 개발팀장 + 개발자 3(백엔드·프론트·인프라),
품질팀장 + 리뷰어. 규모가 안 맞으면 멤버를 지우거나 더하면 된다.

## 3. 고칠 곳은 셋뿐이다

### 3-1. 제품 저장소를 가리킨다

```yaml
org:
  workdir: "/mnt/c/git/myproduct"
```

Windows 경로는 WSL 형식으로 쓴다 — `C:\git\myproduct` 는 `/mnt/c/git/myproduct`.
경로가 틀리면 `up` 이 **거부**하므로 오타는 바로 드러난다.

### 3-2. 코드가 어디 있는지 선언한다

`path` 는 `workdir` 기준 상대경로다. 실제 구조에 맞게 이름도 개수도 바꾼다.

```yaml
  areas:
    backend:
      path: api/           # 실제로 api/ 에 있다면
      desc: "API 서버"
    frontend:
      path: web/
      desc: "웹 UI"
    infra:
      path: deploy/
      desc: "배포 설정, CI"
```

`admin/`, `mobile/`, `batch/` 처럼 제품에 맞는 이름을 쓰면 된다.
모노레포가 아니라 저장소가 여러 개라면 — 조직도 하나는 저장소 하나에 붙는다.
저장소마다 조직도를 따로 만들고 `session_prefix` 를 다르게 둔다.

### 3-3. 누가 어느 영역을 맡는지

```yaml
  - id: dev-be
    areas: [backend]
    worktree: true

  - id: dev-fe
    areas: [frontend]
    worktree: true

  - id: dev-ops
    areas: [infra, backend]     # 둘 이상 겸해도 된다
    worktree: true
```

**`areas` 는 "이 사람이 건드리는 코드"다.** 팀장이 배정할 때 이걸 보고 고르고,
태스크의 파일 범위도 여기서 나온다. 같은 파일을 둘이 고치는 사고를 줄이는 장치다.

## 4. 세우고, 검증 결과를 읽는다

```bash
./aiorg up --org mycorp
```

```
조직도 해석 완료: /경로/org/mycorp.yaml
  조직명 : AI Org (기존 제품)
  멤버   : 8명   배치: windows
  세션 exec      : ceo, po
  세션 dev       : dev-lead, dev-be, dev-fe, dev-ops
  세션 qa        : qa-lead, qa-1

git 워킹트리 준비 중...
  dev-be -> /경로/worktrees/dev-be  (브랜치 aiorg/dev-be)
  dev-fe -> /경로/worktrees/dev-fe  (브랜치 aiorg/dev-fe)
  dev-ops -> /경로/worktrees/dev-ops  (브랜치 aiorg/dev-ops)
  qa-1 -> /경로/worktrees/qa-1  (브랜치 aiorg/qa-1)

tmux 세션 구성 중 (배치: windows)...
  demo-exec ← ceo po
  demo-dev ← dev-lead dev-be dev-fe dev-ops
  demo-qa ← qa-lead qa-1

알림 지킴이 기동 (demo-notify) — 보류된 벨을 계속 재시도합니다
```

### 경고가 나오면 반드시 읽는다

**경로 오타**를 잡아준다:

```
경고: 작업 디렉터리(/경로/내제품) 아래에 없는 영역 경로가 있습니다:
      frontend -> frontnend/
      경로를 고치거나, 아직 만들지 않은 영역이라면 그대로 두어도 됩니다.
```

**아무도 못 건드리는 코드**도 잡아준다:

```
경고: 담당자가 없는 영역: infra
      그 코드를 건드릴 사람이 조직에 없습니다. 멤버의 areas 에 넣거나 영역에서 빼세요.
```

영역과 담당자가 맞는지 눈으로 확인한다:

```bash
./aiorg areas
```

```
작업 디렉터리: /경로/내제품

영역      경로     담당             설명
backend   api/     dev-be, dev-ops  API 서버
frontend  web/     dev-fe           웹 UI
infra     deploy/  dev-ops          배포 설정, CI
```

## 4-2. 저장소가 여럿일 때

프론트와 백엔드가 **각각 다른 git 저장소**에 있는 경우다. `workdir` 은 하나뿐이므로
그대로는 안 맞는다. 두 가지 배치가 가능하다.

### 배치 A — 공통 부모를 기준점으로 (저장소들이 한 폴더 아래 있을 때)

```yaml
org:
  workdir: "/mnt/c/git/innogrid"        # 두 저장소를 담고 있는 부모
  areas:
    backend:  { path: tabcloudit-v2/, desc: "API 서버" }
    frontend: { path: cmp-frontend/, desc: "웹 UI" }
  artifacts:
    design: { path: docs/design/, desc: "기술 설계" }
    ...

members:
  - id: dev-be
    areas: [backend]
    workdir: "/mnt/c/git/innogrid/tabcloudit-v2"     # 자기 저장소 안에 앉힌다
  - id: dev-fe
    areas: [frontend]
    workdir: "/mnt/c/git/innogrid/cmp-frontend"
```

**`worktree: true` 는 끈다.** 워킹트리는 여러 명이 *같은* 저장소에서 `git checkout`
으로 서로의 브랜치를 갈아치우는 것을 막는 장치다. 저장소가 다르면 충돌하지 않는다.
게다가 워킹트리는 `org.workdir` 을 저장소로 보므로, 부모가 git 저장소가 아니면
`up` 이 이렇게 거부한다.

```
aiorg: 워킹트리를 쓰려면 작업 디렉터리가 git 저장소여야 합니다: /mnt/c/git/innogrid
```

`workdir` 을 안 준 멤버(대표, PO, 팀장, 리뷰어)는 부모에 앉는다. 두 저장소가 그 아래
있으므로 읽기는 문제없다. 다만 **부모가 git 저장소가 아니면 그들이 만드는 문서가
커밋되지 않는다.** 부모를 문서 전용 저장소로 만들면 해결된다.

```bash
cd /mnt/c/git/innogrid && git init
cat > .gitignore <<'EOF'
# 문서만 추적한다. 이 아래의 다른 저장소·작업 폴더는 건드리지 않는다.
/*
!/.gitignore
!/docs/
EOF
git add -A && git commit -m "docs: 조직 산출물 저장소 시작"
```

`git status` 에 문서만 잡히고, 아래 저장소들은 영향을 받지 않는다.

### 배치 B — 산출물 전용 디렉터리를 기준점으로

소스와 무관한 곳을 기준점으로 두고 `areas` 를 절대경로로 가리킨다.
제품 저장소를 건드리지 않고 조직의 산출물만 따로 모으고 싶을 때 쓴다.

```yaml
org:
  workdir: "/mnt/c/git/yian/tabcloudit"      # 산출물만 모으는 저장소
  areas:
    backend:  { path: /mnt/c/git/innogrid/tabcloudit-v2/, desc: "API 서버" }
    frontend: { path: /mnt/c/git/innogrid/cmp-frontend/, desc: "웹 UI" }

members:
  - id: dev-be
    workdir: "/mnt/c/git/innogrid/tabcloudit-v2"
  - id: dev-fe
    workdir: "/mnt/c/git/innogrid/cmp-frontend"
```

기준점을 `git init` 해두면 문서가 거기 쌓이고 커밋된다. `areas` 가 절대경로라
소스는 원래 자리에 그대로 둔다.

**소스가 작업 디렉터리 밖이면 읽기 권한이 필요하다.** Claude Code 는 시작한
디렉터리 밖을 읽으려 할 때 사람에게 묻기 때문이다. `launch` 가 이것을 알아서
열어 준다 — `areas` 중 그 멤버의 작업 디렉터리 밖에 있는 것을 `--add-dir` 로 붙인다.

```
dev-lead  claude --add-dir "<프레임워크>" --add-dir "/mnt/c/git/innogrid/tabcloudit-v2" --add-dir "/mnt/c/git/innogrid/cmp-frontend"
dev-be    claude --add-dir "<프레임워크>" --add-dir "/mnt/c/git/innogrid/cmp-frontend"
```

`dev-be` 에게 프론트가 붙는 것은 자기 저장소 밖이기 때문이다.

**주의 — `--add-dir` 은 작업 디렉터리를 하나 더 붙이는 것이라 읽기와 쓰기가 모두
열린다.** 즉 `dev-be` 가 기술적으로는 프론트 저장소를 고칠 수 있다. 막는 것은
도구가 아니라 `areas` 와 지시서다.

> **내 코드 영역 밖을 건드리지 않는다.** 조직도가 영역을 정해 두었다면 그게 경계다.
> 다른 영역을 손대야 하는 변경이면 팀장에게 알린다.

경계가 규칙으로만 지켜진다는 뜻이다. 프레임워크 저장소에 커밋하는 것은 훅으로
막지만(5 장 아래), 영역 경계는 그런 장치가 없다. 실측으로는 잘 지켰지만
기계가 보장하는 것은 아니다.

### 어느 쪽을 고를까

| | 배치 A (공통 부모) | 배치 B (산출물 전용) |
|---|---|---|
| 소스가 한 폴더 아래 있다 | ✅ 자연스럽다 | 굳이 |
| 소스가 흩어져 있다 | 안 된다 | ✅ |
| 제품 저장소에 문서를 안 남기고 싶다 | 부모에 남는다 | ✅ 완전히 분리 |
| 팀장·리뷰어가 코드를 읽는다 | cwd 안이라 바로 | `--add-dir` 로 열림 |

## 5. 워킹트리 — 왜 필수인가

기존 제품에서는 `worktree: true` 가 사실상 필수다. 안 쓰면 이렇게 된다.

전원이 같은 디렉터리에서 일하는데, 프론트 담당이 `git checkout -b feature/frontend`
를 한다. 그 순간 **백엔드 담당의 발밑에서도 브랜치가 바뀐다.** 백엔드 담당은
자기가 어느 브랜치에 있는지 모른 채 계속 커밋한다. 실제로 겪은 일이다 —
겉으로는 아무 오류도 안 난다.

`worktree: true` 를 켜면 각자 자기 작업 트리를 받는다.

```bash
git -C /경로/내제품 worktree list
```

```
/경로/내제품                     8d14cca [master]
/경로/aiorg/worktrees/dev-be     8d14cca [aiorg/dev-be]
/경로/aiorg/worktrees/dev-fe     8d14cca [aiorg/dev-fe]
/경로/aiorg/worktrees/dev-ops    8d14cca [aiorg/dev-ops]
/경로/aiorg/worktrees/qa-1       8d14cca [aiorg/qa-1]
```

브랜치 이름은 `aiorg/<멤버id>` 로 고정이다. 워킹트리는 **프레임워크 저장소의
`worktrees/`** 아래에 만들어진다 — 제품 저장소를 어지럽히지 않기 위해서다.
`runtime/` 과 분리되어 있어서 `./aiorg clean` 으로도 안 지워진다.

> 워킹트리 안에서는 이 프레임워크 저장소의 스킬이 안 보인다.
> 워킹트리는 자기 `.git` 을 가진 별개 프로젝트이기 때문이다.
> `./aiorg skills --link` 를 해두면 해결된다 ([AIORG.md](AIORG.md) 참고).

## 6. 기동과 안내

```bash
./aiorg launch
./aiorg status        # 전원 '대기' 확인
./aiorg brief
```

`brief` 를 빼먹으면 조직이 생기지 않는다. 빼먹었으면 `status` 가 경고한다.

## 7. 목표를 준다 — 기존 제품이라 다른 점

```bash
./aiorg attach ceo
```

새로 만들 때와 지시 방법이 다르다. **지금 있는 것을 존중하라고 말해야 한다.**

```
결제 화면에 쿠폰 적용 기능을 넣으려고 합니다.

지금 코드는 api/ 와 web/ 에 있습니다. 기존 구조와 코딩 규약을 먼저 읽고,
거기에 맞춰 더하는 방향으로 해주세요. 기존 API 의 응답 형식은 바꾸지 않습니다.
DB 스키마 변경이 필요하면 만들기 전에 저에게 먼저 알려주세요.
```

- **무엇을 건드리지 말아야 하는지**를 함께 준다 (기존 API 형식, 스키마, 공개 인터페이스)
- **먼저 물어봐야 할 것**을 정해준다 (스키마 변경, 의존성 추가, 대규모 리팩터링)

안 적으면 조직이 알아서 범위를 넓힌다. 새 제품이면 그래도 되지만
기존 제품에서는 그게 사고가 된다.

## 8. 지켜보기

```bash
./aiorg status          # 누가 무엇을 하고, 어디가 막혔나
./aiorg task tree       # 태스크 갈래
./aiorg layout          # 누가 어느 세션·창에 앉아 있나
./aiorg peek dev-be     # 붙지 않고 그 자리 화면만
./aiorg areas           # 영역과 담당자
```

각자가 자기 브랜치에 커밋하고 있는지도 본다.

```bash
git -C /경로/내제품 log --oneline --all --graph -20
```

## 9. 결과 수확 — 여기가 가장 다르다

새 제품이면 커밋이 그냥 `master` 에 쌓인다. 기존 제품은 **각자 자기 브랜치에**
쌓이므로 사람이 병합해야 한다.

먼저 무엇이 들어왔는지 본다.

```bash
cd /경로/내제품
git log --oneline master..aiorg/dev-be
git diff master...aiorg/dev-be --stat
```

확인했으면 병합한다.

```bash
git merge --no-ff aiorg/dev-be
```

> **병합은 사람이 한다.** 조직에게 시키지 않는다. 팀장이 여러 브랜치를 통합하는
> 흐름도 만들 수는 있지만, 이 문서를 쓰는 시점에 그것까지 실제로 돌려 확인하지는
> 않았다. 브랜치가 갈라지고 충돌이 나기 시작하면 사람이 보는 편이 안전하다.
> 영역을 겹치지 않게 나눠 두면 충돌 자체가 잘 안 난다 — `areas` 가 그 장치다.

병합이 끝나면 워킹트리를 정리한다.

```bash
git worktree remove /경로/aiorg/worktrees/dev-be
git branch -d aiorg/dev-be
```

**정리는 서두르지 않아도 된다.** 조직을 내려도 워킹트리와 브랜치는 남는다.

## 10. 내리기

```bash
./aiorg down
```

세션과 대화 맥락만 사라진다. 태스크·수신함(`runtime/`), 워킹트리와 브랜치,
그리고 제품 저장소의 커밋은 전부 남는다.

다시 올릴 때는 `up` → `launch` → **`brief`** 다.

---

## 여러 제품을 동시에 돌릴 때

`session_prefix` 를 제품마다 다르게 둔다. 안 그러면 tmux 세션 이름이 겹친다.

```yaml
org:
  session_prefix: shop      # -> shop-exec, shop-dev, shop-qa, shop-notify
```

같은 프레임워크 저장소를 복사해 두 벌로 돌리는 경우, `up` 이 세션 주인을
확인해서 **남의 조직을 죽이지 않는다.** 겹치면 이렇게 거부한다.

```
aiorg: tmux 세션 'aiorg-dev' 은 다른 저장소가 쓰고 있습니다.
```

---

## 자주 겪는 것

**영역 경로가 없다고 나온다**
`path` 는 `workdir` 기준 상대경로다. 절대경로를 쓰지 않았는지, 오타가 없는지 본다.
아직 만들지 않은 영역(앞으로 만들 `mobile/` 같은 것)이면 경고를 무시해도 된다.

**둘이 같은 파일을 고쳤다**
`areas` 가 겹치거나, 팀장이 태스크에 파일 범위를 안 적은 것이다.
`./aiorg areas` 로 경계를 다시 보고, 겹치는 영역을 나눈다.

**워킹트리에 커밋 안 된 것이 남았다**
`./aiorg clean` 은 이것을 먼저 경고한다. `runtime/` 만 지우고 `worktrees/` 는
건드리지 않으므로 코드가 사라지지는 않는다.

```bash
git -C /경로/aiorg/worktrees/dev-be status --short
```

**기존 코딩 규약을 안 지킨다**
제품 저장소에 `CLAUDE.md` 가 있으면 구성원이 읽는다. 규약을 거기에 적어 두는 것이
가장 확실하다. 지시서(`org/roles/*.md`)는 프레임워크의 것이므로 제품별 규약을
넣지 않는다.

**스킬이 안 보인다 (워킹트리)**
```bash
./aiorg skills --link
```
