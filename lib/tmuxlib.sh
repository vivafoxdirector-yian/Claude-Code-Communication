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
# 프레임워크 저장소가 구성원의 커밋을 거부하게 만든다.
#
# 왜 필요한가: 구성원은 지시서를 읽으려고 이 저장소를 열어 보게 되는데, 거기서
# 방향을 잃고 산출물까지 이쪽에 만들어 커밋한 적이 있다. 지시서 문구로도
# 막지만(brief, _protocol.md 0 절), 텍스트는 어기면 그만이다. 커밋만은
# 기계가 막는다.
#
# 판정: TMUX_PANE 이 조직의 pane 목록에 있고, 커밋 대상이 이 저장소 자신일 때.
# 워킹트리(worktrees/<id>)는 최상위가 다르므로 걸리지 않는다 — 구성원은
# 자기 워킹트리에는 정상적으로 커밋해야 한다.
aiorg_install_commit_guard() {
  local hook="$AIORG_HOME/.git/hooks/pre-commit"
  local sig="# aiorg-commit-guard"
  [[ -d "$AIORG_HOME/.git/hooks" ]] || return 0
  if [[ -f $hook ]] && ! grep -q "$sig" "$hook" 2>/dev/null; then
    return 0   # 사람이 만든 훅이 있다. 덮지 않는다.
  fi
  cat >"$hook" <<GUARD
#!/bin/sh
$sig — ./aiorg up 이 설치했습니다. 지우면 보호가 없어집니다.
GUARD_HOME='$AIORG_HOME'
top=\$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
[ "\$top" = "\$GUARD_HOME" ] || exit 0   # 워킹트리는 통과
panes="\$GUARD_HOME/runtime/panes.tsv"
[ -n "\$TMUX_PANE" ] && [ -f "\$panes" ] || exit 0
who=\$(awk -F'	' -v p="\$TMUX_PANE" '\$3==p{print \$1}' "\$panes")
[ -n "\$who" ] || exit 0
echo "aiorg: 여기는 aiorg 프레임워크 저장소입니다. 구성원(\$who)은 여기에 커밋하지 않습니다." >&2
echo "       산출물은 당신의 작업 디렉터리에 만드세요. pwd 로 확인하세요." >&2
exit 1
GUARD
  chmod +x "$hook"
}

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
# 이 부서 세션이 온전한가. 세션이 살아 있고, 기대하는 멤버 전원이
# panes.tsv 에 기록된 살아 있는 pane 을 가지고 있어야 한다.
# 첫 인자는 이전 pane 기록(스냅샷). up 이 panes.tsv 를 비우기 전에 떠 둔 것이다.
aiorg_session_intact() {
  local prev="$1" sess="$2"; shift 2
  local id pane
  [[ -f $prev ]] || return 1
  tmux has-session -t "$sess" 2>/dev/null || return 1
  for id in "$@"; do
    pane="$(awk -F'\t' -v w="$id" '$1 == w { print $3; exit }' "$prev")"
    [[ -n $pane ]] || return 1
    aiorg_pane_alive "$pane" || return 1
    # 그 pane 이 정말 이 세션 것인지도 본다 (예전 조직의 잔재일 수 있다)
    [[ "$(tmux display-message -p -t "$pane" '#{session_name}' 2>/dev/null)" == "$sess" ]] || return 1
  done
  return 0
}
# 알림 지킴이. 상대가 작업 중일 때 보낸 메시지는 벨이 보류되고, 이것이
# 재시도해 준다. 사람이 별도 터미널에서 켜 두는 것으로 되어 있었는데
# 잊으면 조직이 조용히 멈춘다 — 전원 '대기' 인데 미확인이 줄지 않는 모습이다.
# 실제로 그렇게 멈춘 것을 봤으므로 up 이 직접 띄운다.
aiorg_notify_session() { aiorg_session_name notify; }

aiorg_notify_running() {
  tmux has-session -t "$(aiorg_notify_session)" 2>/dev/null
}

aiorg_notify_start() {
  local sess
  sess="$(aiorg_notify_session)"
  aiorg_notify_running && return 0
  tmux new-session -d -s "$sess" -c "$AIORG_HOME" "'$AIORG_HOME/aiorg' notify --watch" 2>/dev/null || return 1
  tmux set-environment -t "$sess" AIORG_OWNER "$AIORG_HOME" >/dev/null 2>&1 || true
  return 0
}

aiorg_notify_stop() {
  tmux kill-session -t "$(aiorg_notify_session)" 2>/dev/null
}


aiorg_build_session() {
  local dept="$1" workdir="$2" layout="$3"; shift 3
  local ids=("$@") sess pane i n wd
  sess="$(aiorg_session_name "$dept")"
  n=${#ids[@]}

  wd="$(aiorg_member_start_dir "${ids[0]}" "$workdir")"

  # 이 저장소를 복사해 여러 프로젝트를 동시에 돌리는 경우, session_prefix 가 같으면
  # 세션 이름이 겹친다. 그대로 두면 나중에 뜬 쪽이 먼저 돌던 조직을 죽이고
  # 이름을 가져간다 — 먼저 쪽은 이유도 모르고 전원 '미가동' 이 된다.
  # 그래서 세션마다 주인(AIORG_HOME)을 적어두고, 남의 것이면 손대지 않는다.
  if tmux has-session -t "$sess" 2>/dev/null; then
    local owner
    owner="$(tmux show-environment -t "$sess" AIORG_OWNER 2>/dev/null | sed 's/^AIORG_OWNER=//')"
    if [[ -n $owner && $owner != "$AIORG_HOME" ]]; then
      printf 'CONFLICT\t%s\t%s\n' "$sess" "$owner"
      return 2
    fi
    # 우리 것이고 이 부서의 자리가 전부 살아 있으면 손대지 않는다.
    #
    # 왜 이렇게 하는가: 창이 하나뿐인 부서는 셸이 끝나면 세션째로 사라진다.
    # 되살리려면 up 을 다시 해야 하는데, 예전에는 살아 있는 세션까지 전부 죽이고
    # 새로 만들었다. 한 자리를 잃으면 일하던 조직 전체의 대화 맥락을 잃는 것이다.
    # 이제 없어진 부서만 다시 세운다.
    if aiorg_session_intact "${AIORG_PANES_PREV:-/nonexistent}" "$sess" "${ids[@]}"; then
      printf 'REUSE\t%s\n' "$sess"
      return 0
    fi
  fi
  tmux kill-session -t "$sess" 2>/dev/null || true

  # 첫 자리. -P -F 로 생성된 pane ID 를 그 자리에서 받는다.
  # pane ID(%12)는 창·pane 번호가 어떻게 바뀌어도 그 pane 을 계속 가리킨다.
  pane="$(tmux new-session -d -s "$sess" -n "${ids[0]}" -c "$wd" -P -F '#{pane_id}')"
  # 스크롤백을 넉넉히 잡는다. tmux 기본값 2000 줄로는 구성원이 무엇을 했는지
  # 나중에 되짚을 수 없다 — 실제로 조사 결과의 출처를 확인하려다 이력이
  # 이미 잘려나가 확인하지 못한 적이 있다.
  tmux set-option -t "$sess" history-limit 50000 >/dev/null 2>&1 || true
  # 이 세션이 어느 저장소 것인지 적어둔다. 복사본이 남의 세션을 죽이지 않게 하는 표식이다.
  tmux set-environment -t "$sess" AIORG_OWNER "$AIORG_HOME" >/dev/null 2>&1 || true
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
  # 여기서 'claude' 를 직접 치라고 안내하면 안 된다. launch 는 --add-dir 로
  # 프레임워크 저장소를 함께 열어 주는데, 손으로 띄운 자리는 그것이 빠져서
  # 역할 지시서를 읽지 못한다 — 겉보기엔 정상이라 알아채기 어렵다.
  tmux send-keys -t "$pane" -l "clear; echo \"[aiorg] $id ($role) 자리 준비됨 — 운영자 터미널에서 ./aiorg launch 를 실행하세요 (여기서 claude 를 직접 치지 마세요)\""
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
