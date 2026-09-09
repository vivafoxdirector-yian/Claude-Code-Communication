# aiorg 치트시트

자주 쓰는 명령과 옵션만 모았다. 왜 그런지는 [AIORG.md](AIORG.md),
처음 돌리는 절차는 [GETTING-STARTED.md](GETTING-STARTED.md) 를 본다.

**운영자**(사람)와 **구성원**(각 Claude 세션)이 쓰는 명령이 다르다.
`whoami` 가 id 를 뱉으면 구성원, 비어 있으면 운영자다.

---

## 처음부터 끝까지 (운영자)

```bash
./aiorg doctor                       # 실행 환경 점검 (tmux, python3, PyYAML, claude, 스킬)
./aiorg skills --link                # 스킬을 ~/.claude/skills/ 로 연결 (한 번만)
./aiorg templates                    # 조직 템플릿 목록 10종
./aiorg new product-team mycorp      # org/mycorp.yaml 로 복사 -> workdir 을 고친다
./aiorg up --org mycorp              # 조직도대로 tmux 세션 구성 + 알림 지킴이
./aiorg scaffold                     # 산출물 디렉터리 + 구성원 권한 설정을 제품 저장소에
./aiorg launch                       # 각 자리에서 claude 기동
./aiorg status                       # 전원 '대기' 확인
./aiorg brief                        # 각자에게 역할·지시서 안내  <- 빼먹으면 조직이 안 생긴다
./aiorg attach ceo                   # 대표에게 목표 지시. Ctrl-b d 로 나옴
```

## 조직 세우기·내리기

```bash
./aiorg up                           # 조직도 자동 선택 (아래 '조직도 고르는 순서')
./aiorg up --org mycorp              # org/mycorp.yaml 로
./aiorg up --org /경로/조직도.yaml     # 경로로 직접
./aiorg up --launch                  # 세우고 바로 claude 까지
./aiorg down                         # 세션 종료. 태스크·수신함·산출물은 남는다
./aiorg clean                        # runtime/ 정리 — 무엇을 잃는지 먼저 보여준다
./aiorg clean --force                # 확인했으면 실제로 지운다
```

```bash
# 완전히 처음부터
./aiorg down && ./aiorg clean --force && ./aiorg up && ./aiorg launch && ./aiorg brief
```

**조직도 고르는 순서** — `--org` 를 붙였으면 그것이 언제나 이긴다.

```
1. AIORG_ORG 환경변수      2. org/default.yaml      3. 지금 떠 있는 조직
4. org/ 에 조직도가 딱 하나면 그것                    5. 표준 템플릿
```

둘 이상인데 `--org` 를 안 붙이면 `up` 이 목록을 보여주고 거부한다.

## 한 자리만 되살리기

```bash
./aiorg up                           # 없어진 부서만 다시 세움. 살아 있는 세션은 그대로
./aiorg launch                       # 셸로 떨어진 자리만 띄움. 일하는 사람은 안 건드림
./aiorg brief ceo                    # 그 자리에만 안내
./aiorg brief ceo po dev-1           # 여러 명 지정도 가능
```

## 지켜보기 (붙지 않고)

```bash
./aiorg status                       # 조직도 + 각자 상태 + 미확인/진행
./aiorg task tree                    # 태스크 갈래
./aiorg progress                     # 진행 중인 일과 각자의 최신 작업 기록
./aiorg progress --assignee dev-1    # 한 사람만
./aiorg layout                       # 누가 어느 세션·창·자리에 있나 + 지킴이 상태
./aiorg peek dev-1                   # 그 자리 화면 (기본 30줄). 입력은 안 들어간다
./aiorg peek dev-1 -n 60             # 줄 수 지정
./aiorg log                          # 이벤트 로그
./aiorg log --limit 50               # 줄 수
./aiorg log --type msg.sent          # 종류로 거르기
./aiorg log --grep 인증               # 내용으로 거르기
./aiorg areas                        # 코드 영역과 담당자
./aiorg artifacts                    # 산출물 자리 (설계·ADR·테스트계획)
./aiorg members                      # 전원의 담당/역량
./aiorg members --ids                # id 만
./aiorg members --skill python       # 해당 역량을 가진 사람만 (부분 일치)
```

```bash
AIORG_ASCII=1 ./aiorg status         # 이모지가 물음표로 보일 때
```

## 붙기

```bash
./aiorg attach                       # 붙을 수 있는 세션 목록
./aiorg attach ceo                   # 그 멤버 화면으로
./aiorg explain dev-1                # 상태 판정이 어긋날 때 원인 진단
```

| 키 | |
|---|---|
| `Ctrl-b` `d` | **나오기.** Ctrl 을 떼고 d 를 누른다 (`Ctrl-b` `Ctrl-d` 는 아무 일도 안 남) |
| `Ctrl-b` `n` / `p` | 같은 세션의 다음/이전 창 |
| `Ctrl-b` `w` | 창 목록에서 고르기 |
| `Ctrl-b` `[` | 스크롤 모드 (`q` 로 빠져나옴) |
| `Esc` | claude 진행 중단 / 종료 대화상자 취소 |

**`Ctrl-D` 와 `exit` 은 치지 않는다** — pane 이 닫히고, 창이 하나뿐인 부서는 세션째 사라진다.

## tmux 를 직접 보기

`layout` 으로 안 보이는 것을 볼 때. 조직을 안 건드린다.

```bash
tmux ls                                          # 세션 목록. (attached) 가 지금 붙어 있는 것
tmux list-panes -a -F '#{session_name} #{window_index}:#{window_name} #{pane_id} #{pane_current_command}' | sort
tmux list-windows -t aiorg-dev                   # 한 부서의 창만
tmux capture-pane -p -t %3 | tail -30            # pane 화면 (aiorg peek 이 하는 일)
tmux display-message -p -t %3 '#{pane_current_path}'   # 그 자리가 어느 디렉터리인가
```

```
tx-biz: 1 windows (created Mon Sep  7 12:03:49 2026)
tx-dev: 3 windows (created Mon Sep  7 12:03:49 2026)
tx-exec: 1 windows (created Mon Sep  7 12:03:48 2026)
tx-notify: 1 windows (created Mon Sep  7 12:03:49 2026)
```

```
tx-dev 0:dev-lead %1 zsh        <- pane_current_command 가 claude 가 아니면 그 자리는 죽은 것
tx-dev 1:dev-1    %2 claude
tx-exec 0:ceo     %0 claude
```

창 이름이 곧 멤버 id 다. `<prefix>-notify` 는 알림 지킴이이고 구성원이 아니다.

```bash
# 멤버 id 로 pane 찾기
awk -F'\t' '$1=="dev-1"{print $3}' runtime/panes.tsv

# 밖에서 강제로 떼기 (붙은 채 Ctrl-b d 가 안 될 때)
tmux detach-client -s aiorg-exec

# 조직 밖에서 만든 세션까지 전부 (aiorg down 은 조직 세션만 내린다)
tmux kill-server
```

`tmux kill-server` 는 **조직과 무관한 당신의 다른 tmux 세션까지 죽인다.** 확인하고 쓴다.

## 알림

```bash
./aiorg notify                       # 보류된 벨을 지금 한 번 재시도
./aiorg notify --watch               # 계속 재시도 (up 이 이미 띄워 둔다)
./aiorg notify --interval 10         # 재시도 간격 (기본 20초)
```

전원 `대기` 인데 **미확인이 줄지 않으면** 지킴이를 의심한다. `status` 가 먼저 알려준다.

## 스킬

```bash
./aiorg skills                       # 연결 상태
./aiorg skills --link                # ~/.claude/skills/ 로 심링크 (사본 아님)
./aiorg skills --unlink              # 링크만 제거. 원본은 그대로
```

## 조직도 만들기

```bash
./aiorg templates                    # 목록 (existing-product 는 경로를 고쳐야 뜬다)
./aiorg new product-team mycorp      # org/mycorp.yaml
./aiorg new existing-product mycorp  # 기존 제품용 (areas + 워킹트리)
./aiorg chart product-team           # 조직도를 그림으로 (터미널)
./aiorg chart mycorp --mermaid       # 문서에 붙일 형태
```

---

# 구성원이 쓰는 명령

각 Claude 세션 안에서 쓴다. 여기 없는 명령(`up`, `down`, `launch`, `brief`,
`attach`, `layout`, `peek`, `clean`, `scaffold`, `skills`)은 운영자의 것이다.

## 나와 수신함

```bash
aiorg whoami                         # 내 id
aiorg inbox                          # 수신함 확인 (읽으면 확인 처리)
aiorg inbox --peek                   # 확인 처리 없이 엿보기
aiorg inbox --all                    # 이미 읽은 것까지
```

## 보내기

```bash
aiorg send dev-1 "본문"                          # 정보 전달
aiorg send dev-1 -s "제목" "본문"                 # 제목 붙여서
aiorg send dev-1 -t question "물어볼 것"          # 종류 지정 (info question answer ...)
aiorg reply msg_ab12cd34 "답신"                  # 받은 메시지에 답
aiorg report "결과 요약"                          # 직속 상급자에게 보고
aiorg report --task t_xxxx "결과 요약"            # 태스크에 묶어서
```

**받는 사람 선택자**

```
dev-1            멤버 한 명            @all             전원
@reports         내 직속 부하 전원      @boss            내 직속 상급자
@role:engineer   해당 역할 전원         @dept:dev        해당 부서(세션) 전원
```

**여러 줄 본문** — `-` 를 주면 표준입력에서 읽는다.

```bash
aiorg report --task t_xxxx - <<'EOT'
첫째 줄
둘째 줄
EOT
```

```bash
aiorg send dev-1 --file /경로/본문.md
```

## 태스크 (관리자)

```bash
aiorg assign dev-1 "제목"                         # 배정 + 지시가 함께 나간다
aiorg assign dev-1 "제목" -d "상세 지시"           # 상세
aiorg assign dev-1 "제목" -p t_상위태스크          # 상위 태스크 아래로
aiorg assign dev-1 "제목" -b feature/login        # 브랜치 지정
```

## 태스크 (실무자)

```bash
aiorg task list                                  # 전체
aiorg task list --mine --open                    # 내 것 중 안 끝난 것
aiorg task show t_xxxx                           # 상세 + 이력
aiorg task tree                                  # 갈래

aiorg task start t_xxxx                          # 착수
aiorg task done t_xxxx --note "무엇을 했는지"      # 완료
aiorg task block t_xxxx --note "무엇에 막혔는지"   # 막힘 <- 남을 기다릴 때도 이것
aiorg task review t_xxxx --note "리뷰 요청"       # 리뷰 대기
aiorg task cancel t_xxxx --note "취소 이유"       # 취소

aiorg task set --id t_xxxx --note "중간 기록"                  # 진행 중 기록
aiorg task set --id t_xxxx --artifact backend/main.py         # 산출물 경로
aiorg task set --id t_xxxx --branch aiorg/dev-1               # 브랜치
```

**상태 표시**

```
[o] open      [>] in_progress   [!] blocked
[?] review    [x] done          [-] cancelled
```

## 내가 볼 것

```bash
aiorg members                        # 누구에게 배정할지 고를 때
aiorg areas                          # 내가 건드려도 되는 코드 영역
aiorg artifacts                      # 문서를 어디에 남기는가
aiorg status                         # 조직 전체 현황
```

---

# 상태값

```
대기        일을 받을 수 있다        작업중      응답 생성 중
부팅중      claude 가 뜨는 중        응답대기    대화상자가 떠서 멈춤 -> attach 해서 답한다
로그인필요  인증 끊김 -> /login      미가동      claude 가 없다 -> launch
```

# 환경변수

```bash
AIORG_ORG=org/mycorp.yaml            # 기본 조직도
AIORG_ASCII=1                        # 이모지 대신 ASCII 기호
AIORG_ME=dev-1                       # 내 신원 (보통 pane 에서 자동)
AIORG_CLAUDE_CMD="claude --model x"  # launch 가 쓸 명령 (지정하면 --add-dir 을 안 붙인다)
AIORG_HOME=/경로                      # 프레임워크 위치
```

# 자주 겪는 것

```bash
# 전원 '응답대기' — 신뢰 확인 대화상자
./aiorg attach <멤버>                 # ↓ 로 'Yes, I trust this folder' 로 옮기고 Enter, Ctrl-b d
cd <작업 디렉터리> && claude           # 미리 한 번 신뢰해 두면 다음부터 안 뜬다

# brief 가 "0 명에게 전달" — 아무에게도 안 갔다는 뜻
./aiorg status                       # '대기' 가 아닌 사람은 건너뛴다. 건너뜀 줄에 이유가 있다
./aiorg attach dev-lead              # (prompt) 면 붙어서 답한다. Ctrl-b n 으로 같은 부서의 다음 창
./aiorg brief                        # 전원 '대기' 가 된 뒤 다시

# 신뢰 대화상자를 아예 안 겪기 (launch 가 띄우기 전에 알려준다)
cd <작업 디렉터리> && claude           # 한 번만 답해 두면 이후 조용히 뜬다

# 전원 '대기' 인데 미확인이 안 줄어듦
./aiorg notify

# 한 자리가 죽음
./aiorg up && ./aiorg launch && ./aiorg brief <멤버>

# 조직도의 기호가 물음표
AIORG_ASCII=1 ./aiorg status
```

---

## 더 볼 것

- [GETTING-STARTED.md](GETTING-STARTED.md) — 빈 저장소에서 처음부터
- [EXISTING-PRODUCT.md](EXISTING-PRODUCT.md) — 이미 있는 제품에 붙이기
- [AIORG.md](AIORG.md) — 설계 배경과 전체 설정
- `./aiorg help` — 이 문서의 요약판
