# shellcheck shell=bash
# aiorg tmux 계층.
#
# 설계 요지 — 기존 agent-send.sh 가 물렸던 세 곳을 여기서 끊는다:
#   1) pane 인덱스(0,1,2,3) 대신 tmux pane ID(%12)를 쓴다.
#      base-index / pane-base-index 설정에 아예 의존하지 않는다.
#   2) send-keys 에 -l(리터럴)을 붙인다. 메시지에 'Enter' 나 'C-c' 같은
#      키 이름 문자열이 들어가도 키로 해석되지 않는다.
#   3) C-c 를 보내지 않는다. 대신 상대가 대기(idle) 상태일 때만 벨을 울리고,
#      작업 중이면 벨을 보류한다. 남의 작업을 끊어먹지 않는다.
#
# 메시지 본문은 절대 pane 으로 흘려보내지 않는다. 본문은 파일 큐에 있고,
# pane 으로 가는 것은 "새 메시지가 있다"는 한 줄 벨뿐이다.
# 따라서 벨이 실패해도 메시지는 유실되지 않는다.

# ---------------------------------------------------------------- 세션 이름

aiorg_session_name() {
  local prefix dept
  prefix="$(aiorg_org_field session_prefix)"
  dept="$1"
  printf '%s-%s' "$prefix" "$dept"
}

aiorg_org_field() {
  "$AIORG_PY" - "$1" <<'PY'
import json, os, sys
p = os.path.join(os.environ["AIORG_HOME"], "runtime", "org.resolved.json")
try:
    with open(p, encoding="utf-8") as f:
        print(json.load(f)["org"][sys.argv[1]])
except Exception:
    print("")
PY
}

# ---------------------------------------------------------------- pane 대장

aiorg_panes_file() { printf '%s/runtime/panes.tsv' "$AIORG_HOME"; }

# id -> pane ID. 없으면 빈 문자열.
aiorg_pane_of() {
  local id="$1" f
  f="$(aiorg_panes_file)"
  [[ -f $f ]] || return 0
  awk -F'\t' -v want="$id" '$1 == want { print $3; exit }' "$f"
}

aiorg_session_of() {
  local id="$1" f
  f="$(aiorg_panes_file)"
  [[ -f $f ]] || return 0
  awk -F'\t' -v want="$id" '$1 == want { print $2; exit }' "$f"
}

aiorg_pane_record() {
  # id, 세션명, pane ID
  printf '%s\t%s\t%s\n' "$1" "$2" "$3" >>"$(aiorg_panes_file)"
}

# ---------------------------------------------------------------- 상태 판정

# pane 이 살아 있는지.
aiorg_pane_alive() {
  local pane="$1"
  [[ -n $pane ]] || return 1
  tmux list-panes -a -F '#{pane_id}' 2>/dev/null | grep -qxF "$pane"
}

# ---------------------------------------------------------------- 화면 표지
#
# Claude Code TUI 화면을 읽어 상태를 판정한다. UI 문구는 버전마다 바뀌므로
# 표지를 여기 한곳에 모아 둔다. 감지가 어긋나면 이 네 줄만 고치면 된다.
#
# 확인된 변화 (참고):
#   ~2.1.237  입력 상자가 ╭─ ╰─ 테두리, 하단에 "? for shortcuts"
#    2.1.260  테두리가 사라지고 가로줄 + "⏵⏵ auto mode on (shift+tab to cycle)"
# 그래서 양쪽 표지를 모두 남겨 둔다. 버전이 섞여 있어도 동작한다.

# 작업 중: 실행 중에만 뜨는 인터럽트 힌트.
AIORG_PAT_BUSY='esc to interrupt|to interrupt\)'

# 사람이 답해야 하는 대화상자: 폴더 신뢰, 권한 승인, 선택 목록.
AIORG_PAT_PROMPT='trust (the|this) folder|Do you trust|Enter to confirm|Do you want to (proceed|allow)|❯ *[0-9]+\. '

# 인증 끊김. idle 화면과 겹쳐 보이므로 idle 보다 먼저 검사해야 한다.
AIORG_PAT_LOGIN='Not logged in|Run /login|Login expired|Invalid API key|/login to'

# 기동 중.
AIORG_PAT_STARTING='Loading|Starting|Welcome to Claude Code'

# 입력 대기: 하단 모드 표시줄(신형) 또는 입력 상자 테두리(구형).
AIORG_PAT_IDLE='\? for shortcuts|shift\+tab to cycle|for agents|auto mode on|accept edits on|plan mode on|[Bb]ypass(ing)? [Pp]ermissions|╭─|╰─'

# 멤버 상태를 표준출력으로: down | starting | login | prompt | busy | idle
#
#   down     — pane 이 없거나 claude 가 아직 안 떠 있음
#   starting — claude 부팅 중 (벨 보류)
#   prompt   — 사람의 응답을 기다리는 대화상자가 떠 있음 (벨 보류)
#              폴더 신뢰 확인, 권한 승인 등. 운영자가 직접 붙어서 답해야 한다.
#   busy     — claude 가 작업 중 (벨 보류)
#   idle     — 입력 대기 (벨 전송 가능)
#
# Claude Code TUI 화면을 읽어 판정하므로 UI 문구가 바뀌면 여기만 고치면 된다.
# 오판해도 메시지는 큐에 남으므로 유실은 없다 — 알림만 늦어진다.
# 판정 순서가 중요하다: 대화상자 화면에도 입력 상자 테두리가 있어서,
# idle 검사를 먼저 하면 대화상자에 벨을 쏘게 된다.
aiorg_member_state() {
  local pane="$1" cap cmd
  aiorg_pane_alive "$pane" || { printf 'down\n'; return; }

  # 화면 글자를 읽기 전에 프로세스를 먼저 본다.
  # claude 가 종료되고 셸로 돌아왔는데 스크롤백에 옛 대화상자 문구가 남아 있으면
  # 화면만 보고는 '응답대기' 로 오판한다. 실제로 겪은 일이다.
  cmd="$(tmux display-message -p -t "$pane" '#{pane_current_command}' 2>/dev/null)"
  case "$cmd" in
    sh|bash|zsh|fish|dash|tcsh|ksh) printf 'down\n'; return ;;
  esac

  cap="$(tmux capture-pane -p -t "$pane" -S -40 2>/dev/null)" || { printf 'down\n'; return; }

  # 검사 순서가 중요하다. 대화상자·로그인 안내 화면에도 입력 대기 표지가 함께
  # 뜨기 때문에, idle 을 먼저 검사하면 아무도 응답하지 않는 화면에 벨을 쏘게 된다.
  if grep -qE "$AIORG_PAT_BUSY" <<<"$cap"; then printf 'busy\n'; return; fi
  if grep -qE "$AIORG_PAT_PROMPT" <<<"$cap"; then printf 'prompt\n'; return; fi
  if grep -qE "$AIORG_PAT_LOGIN" <<<"$cap"; then printf 'login\n'; return; fi
  if grep -qE "$AIORG_PAT_STARTING" <<<"$cap"; then printf 'starting\n'; return; fi
  if grep -qE "$AIORG_PAT_IDLE" <<<"$cap"; then printf 'idle\n'; return; fi
  printf 'down\n'
}

# 감지가 어긋났을 때 원인을 보기 위한 진단.
# 어떤 표지가 걸렸는지/안 걸렸는지 한눈에 보여준다.
aiorg_explain_state() {
  local pane="$1" cap name pat
  if ! aiorg_pane_alive "$pane"; then
    printf 'pane 이 없습니다: %s\n' "$pane"; return
  fi
  cap="$(tmux capture-pane -p -t "$pane" -S -40 2>/dev/null)"
  printf '판정: %s\n' "$(aiorg_member_state "$pane")"
  for name in BUSY PROMPT LOGIN STARTING IDLE; do
    eval "pat=\$AIORG_PAT_$name"
    if grep -qE "$pat" <<<"$cap"; then
      printf '  %-9s 일치: %s\n' "$name" "$(grep -oE "$pat" <<<"$cap" | head -1)"
    else
      printf '  %-9s -\n' "$name"
    fi
  done
}

# 전 멤버의 상태를 runtime/live.json 으로 떨어뜨린다 (status 렌더용).
aiorg_write_live() {
  local out="$AIORG_HOME/runtime/live.json" tmp id sess pane state first=1
  tmp="$out.tmp"
  printf '{\n' >"$tmp"
  while IFS=$'\t' read -r id sess pane; do
    [[ -n $id ]] || continue
    state="$(aiorg_member_state "$pane")"
    [[ $first -eq 1 ]] || printf ',\n' >>"$tmp"
    first=0
    printf '  "%s": {"session": "%s", "pane": "%s", "state": "%s"}' \
      "$id" "$sess" "$pane" "$state" >>"$tmp"
  done <"$(aiorg_panes_file)"
  printf '\n}\n' >>"$tmp"
  mv -f "$tmp" "$out"
  printf '%s\n' "$out"
}

# ---------------------------------------------------------------- 벨

# 한 줄 알림을 pane 에 넣고 Enter. 성공 시 0.
aiorg_ring() {
  local pane="$1" text="$2"
  aiorg_pane_alive "$pane" || return 1

  # 입력창에 남은 글자를 먼저 지운다. 앞선 벨이 제출에 실패했거나 사람이 뭔가
  # 치다 만 경우, 그 뒤에 이어붙어 메시지가 깨진다.
  #
  # C-c 가 아니라 C-u 를 쓴다. C-c 는 상대가 작업 중일 때 그 작업을 끊어버리지만
  # (전신 데모가 바로 이걸로 남의 일을 망쳤다), C-u 는 입력 줄만 비운다.
  # 게다가 벨은 idle 일 때만 울리므로 끊을 작업 자체가 없다.
  tmux send-keys -t "$pane" C-u 2>/dev/null || true
  sleep 0.15

  # -l 로 리터럴 전송. 'Enter' 나 'C-c' 같은 문자열이 키로 해석될 여지를 없앤다.
  tmux send-keys -t "$pane" -l "$text" || return 1
  # TUI 가 입력을 반영할 짧은 틈을 준다.
  sleep 0.35
  tmux send-keys -t "$pane" Enter || return 1
  return 0
}

# ---------------------------------------------------------------- git 워킹트리
#
# 여러 멤버가 같은 디렉터리에서 일하면 git 이 서로를 짓밟는다.
# 실제로 이렇게 된다:
#   dev-be:  git checkout -b feature/backend   (좋아, 내 브랜치)
#   dev-fe:  git checkout -b feature/frontend  (워킹트리 전체가 옮겨감)
#   dev-be:  git branch --show-current -> feature/frontend  (!!)
# dev-be 는 자기가 옮겨진 줄도 모르고 백엔드 작업을 프론트 브랜치에 커밋한다.
# 편집 중인 파일도 서로 덮어쓴다.
#
# git worktree 가 정확히 이 문제를 위한 기능이다. 멤버마다 독립 워킹트리를
# 주면 브랜치도 작업 파일도 완전히 갈린다. 저장소(.git)는 하나를 공유하므로
# 서로의 커밋은 그대로 보인다.

# 워킹트리는 runtime/ 밖에 둔다.
#
# runtime/ 은 조직 상태(메시지 큐, 태스크, 로그)이고 통째로 지워도 되는 것으로
# 안내한다. 그런데 워킹트리에는 **커밋 안 된 코드**가 들어 있다.
# 같은 곳에 두면 "runtime 을 지우면 처음부터 다시 시작" 이라는 안내를 따른 사람이
# 자기 작업을 날린다. 성격이 다른 것을 같은 통에 담지 않는다.
aiorg_worktree_root() { printf '%s/worktrees' "$AIORG_HOME"; }

# 멤버 하나의 워킹트리를 보장한다. 경로를 표준출력으로.
# 사용법: aiorg_ensure_worktree <제품저장소> <멤버id>
aiorg_ensure_worktree() {
  local repo="$1" id="$2" wt branch
  wt="$(aiorg_worktree_root)/$id"
  branch="aiorg/$id"

  if [[ -d $wt/.git || -f $wt/.git ]]; then
    printf '%s\n' "$wt"; return 0
  fi

  mkdir -p "$(aiorg_worktree_root)"
  # 이미 그 이름의 브랜치가 있으면 새로 만들지 않고 붙인다 (up 재실행 대비).
  if git -C "$repo" show-ref --verify --quiet "refs/heads/$branch"; then
    git -C "$repo" worktree add "$wt" "$branch" >/dev/null 2>&1 || return 1
  else
    git -C "$repo" worktree add -b "$branch" "$wt" >/dev/null 2>&1 || return 1
  fi

  # 워킹트리는 이 저장소 아래(/mnt/c, Windows 파일시스템)에 만들어지는데
  # 제품 저장소는 다른 파일시스템(ext4)일 수 있다. drvfs 는 모든 파일을 755 로
  # 보고하므로 git 이 전 파일을 "mode 100644 -> 100755" 로 변경된 것처럼 본다.
  # 그러면 개발자가 자기 변경만 골라 커밋해도 mode 변경이 딸려 들어가고,
  # 리뷰어가 볼 diff 가 무의미하게 커진다.
  git -C "$wt" config core.fileMode false 2>/dev/null || true
  printf '%s\n' "$wt"
}

# 워킹트리를 쓰는 멤버인지 (조직도의 members[].worktree).
aiorg_wants_worktree() {
  [[ "$(aiorg_member_field "$1" worktree)" == "True" ]]
}

# 멤버가 어디서 시작하는가. 우선순위:
#   1. 자기 git 워킹트리 (worktree: true 인 경우)
#   2. members[].workdir
#   3. 조직 workdir
# 사용법: aiorg_member_start_dir <멤버id> <조직 workdir>
aiorg_member_start_dir() {
  local id="$1" fallback="$2" wt
  if aiorg_wants_worktree "$id"; then
    wt="$(aiorg_worktree_root)/$id"
    if [[ -d $wt ]]; then printf '%s
' "$wt"; return; fi
  fi
  wt="$(aiorg_member_field "$id" workdir_resolved)"
  printf '%s
' "${wt:-$fallback}"
}

# ---------------------------------------------------------------- 세션 구성

# 세션(= 부서) 하나를 만들고 멤버마다 자리를 준다.
# 사용법: aiorg_build_session <부서> <작업디렉터리> <배치> <멤버 id...>
#
# 배치 두 가지:
#   windows — 멤버당 tmux 창 하나. 각자 터미널 전체 폭을 쓴다. (기본)
#             Claude Code TUI 는 좁은 폭에서 심하게 줄바꿈되므로 실사용에는 이쪽이다.
#             창 사이 이동은 Ctrl-b n / p, 목록은 Ctrl-b w.
#   panes   — 한 창을 격자로 쪼갠다. 부서 전체가 한눈에 보이지만 멤버당 폭이 좁다.
#             4명이면 한 명당 ~40칸으로, 읽기는 되지만 작업하기는 답답하다.
aiorg_build_session() {
  local dept="$1" workdir="$2" layout="$3"; shift 3
  local ids=("$@") sess pane i n wd
  sess="$(aiorg_session_name "$dept")"
  n=${#ids[@]}

  wd="$(aiorg_member_start_dir "${ids[0]}" "$workdir")"

  tmux kill-session -t "$sess" 2>/dev/null || true

  # 첫 자리. -P -F 로 생성된 pane ID 를 그 자리에서 받는다.
  # pane ID(%12)는 창·pane 번호가 어떻게 바뀌어도 그 pane 을 계속 가리킨다.
  pane="$(tmux new-session -d -s "$sess" -n "${ids[0]}" -c "$wd" -P -F '#{pane_id}')"
  # 스크롤백을 넉넉히 잡는다. tmux 기본값 2000 줄로는 구성원이 무엇을 했는지
  # 나중에 되짚을 수 없다 — 실제로 조사 결과의 출처를 확인하려다 이력이
  # 이미 잘려나가 확인하지 못한 적이 있다.
  tmux set-option -t "$sess" history-limit 50000 >/dev/null 2>&1 || true
  aiorg_pane_record "${ids[0]}" "$sess" "$pane"
  aiorg_prepare_pane "$pane" "${ids[0]}" "$wd"

  for ((i = 1; i < n; i++)); do
    wd="$(aiorg_member_start_dir "${ids[i]}" "$workdir")"
    if [[ $layout == panes ]]; then
      # 매번 tiled 로 재배치해 "no space for new pane" 을 피한다.
      pane="$(tmux split-window -t "$sess:${ids[0]}" -c "$wd" -P -F '#{pane_id}')"
      tmux select-layout -t "$sess:${ids[0]}" tiled >/dev/null
    else
      pane="$(tmux new-window -t "$sess" -n "${ids[i]}" -c "$wd" -P -F '#{pane_id}')"
    fi
    aiorg_pane_record "${ids[i]}" "$sess" "$pane"
    aiorg_prepare_pane "$pane" "${ids[i]}" "$wd"
  done

  if [[ $layout == panes ]]; then
    # 격자 배치에서는 테두리에 직함을 띄운다. 셸 프롬프트에 색을 넣는 것보다
    # 셸 종류(zsh/bash)에 의존하지 않고 잘 보인다.
    tmux select-layout -t "$sess:${ids[0]}" tiled >/dev/null
    tmux set-option -t "$sess" pane-border-status top >/dev/null 2>&1 || true
    tmux set-option -t "$sess" pane-border-format ' #{pane_title} ' >/dev/null 2>&1 || true
  fi
  tmux select-window -t "$sess:${ids[0]}" >/dev/null 2>&1 || true
  printf '%s\n' "$sess"
}

# pane 에 신원을 심는다. claude 는 이 셸에서 뜨므로 환경변수를 물려받고,
# claude 의 Bash 도구가 도는 자식 셸까지 그대로 내려간다.
#
# 프롬프트에는 셸 이스케이프를 쓰지 않는다. 사용자의 로그인 셸이 zsh 일 수도
# bash 일 수도 있고, 둘의 PS1 문법이 달라서 한쪽에서는 제어문자가 그대로
# 화면에 찍힌다. 신원 표시는 pane 테두리(pane-border-format)가 담당한다.
aiorg_prepare_pane() {
  local pane="$1" id="$2" workdir="$3" role title
  role="$(aiorg_member_field "$id" role)"
  title="$(aiorg_member_field "$id" title)"

  tmux select-pane -t "$pane" -T "$id — $title ($role)" 2>/dev/null || true

  # PATH 에 AIORG_HOME 을 넣어 어느 디렉터리에서든 `aiorg` 를 부를 수 있게 한다.
  # 이게 없으면 제품 저장소를 workdir 로 잡는 순간(기존 제품에 조직을 붙이는 경우)
  # 멤버가 `./aiorg` 를 찾지 못해 조직 전체가 통신 불능이 된다.
  tmux send-keys -t "$pane" -l "export AIORG_HOME='$AIORG_HOME' AIORG_ME='$id' AIORG_ROLE='$role' PATH='$AIORG_HOME':\$PATH"
  tmux send-keys -t "$pane" Enter
  tmux send-keys -t "$pane" -l "cd '$workdir'"
  tmux send-keys -t "$pane" Enter
  tmux send-keys -t "$pane" -l "export PS1='[$id] \$ '"
  tmux send-keys -t "$pane" Enter
  tmux send-keys -t "$pane" -l "clear; echo \"[aiorg] $id ($role) 준비 완료 — 'claude' 로 세션을 시작하세요\""
  tmux send-keys -t "$pane" Enter
}

# 해석된 조직도에서 멤버 필드 하나를 꺼낸다.
aiorg_member_field() {
  "$AIORG_PY" - "$1" "$2" <<'PY'
import json, os, sys
p = os.path.join(os.environ["AIORG_HOME"], "runtime", "org.resolved.json")
mid, field = sys.argv[1], sys.argv[2]
with open(p, encoding="utf-8") as f:
    org = json.load(f)
for m in org["members"]:
    if m["id"] == mid:
        v = m.get(field, "")
        print(" ".join(v) if isinstance(v, list) else v)
        break
else:
    print("")
PY
}
