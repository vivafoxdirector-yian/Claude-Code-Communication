#!/bin/bash

# 🚀 Multi-Agent Communication Demo 환경 구축
# 참고: setup_full_environment.sh

set -e  # 오류 시 중지

# 색상 로그 함수
log_info() {
    echo -e "\033[1;32m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[1;34m[SUCCESS]\033[0m $1"
}

echo "🤖 Multi-Agent Communication Demo 환경 구축"
echo "==========================================="
echo ""

# STEP 1: 기존 세션 클린업
log_info "🧹 기존 세션 클린업 시작..."

tmux kill-session -t multiagent 2>/dev/null && log_info "multiagent 세션 삭제 완료" || log_info "multiagent 세션이 존재하지 않았습니다"
tmux kill-session -t president 2>/dev/null && log_info "president 세션 삭제 완료" || log_info "president 세션이 존재하지 않았습니다"

# 완료 파일 클리어
mkdir -p ./tmp
rm -f ./tmp/worker*_done.txt 2>/dev/null && log_info "기존 완료 파일을 클리어" || log_info "완료 파일이 존재하지 않았습니다"

log_success "✅ 클린업 완료"
echo ""

# STEP 2: multiagent 세션 작성 (4페인: boss1 + worker1,2,3)
log_info "📺 multiagent 세션 작성 시작 (4페인)..."

# 세션 작성
log_info "세션 작성 중..."
tmux new-session -d -s multiagent -n "agents"

# 세션 작성 확인
if ! tmux has-session -t multiagent 2>/dev/null; then
    echo "❌ 오류: multiagent 세션 작성에 실패했습니다"
    exit 1
fi

log_info "세션 작성 성공"

# 2x2 그리드 작성 (윈도우명 사용으로 base-index 비의존)
log_info "그리드 작성 중..."

# 수평 분할 (윈도우명으로 지정)
log_info "수평 분할 실행 중..."
tmux split-window -h -t "multiagent:agents"

# 좌상단 페인을 선택하여 수직 분할
log_info "좌측 수직 분할 실행 중..."
tmux select-pane -t "multiagent:agents" -L  # 왼쪽 페인을 선택
tmux split-window -v

# 우상단 페인을 선택하여 수직 분할
log_info "우측 수직 분할 실행 중..."
tmux select-pane -t "multiagent:agents" -R  # 오른쪽 페인을 선택
tmux split-window -v

# 페인 배치 확인
log_info "페인 배치 확인 중..."
PANE_COUNT=$(tmux list-panes -t "multiagent:agents" | wc -l)
log_info "작성된 페인 수: $PANE_COUNT"

if [ "$PANE_COUNT" -ne 4 ]; then
    echo "❌ 오류: 기대하는 페인 수(4)와 다릅니다: $PANE_COUNT"
    exit 1
fi

# 페인의 물리적 배치를 취득 (top-left부터 순서대로)
log_info "페인 번호 취득 중..."
# tmux의 페인 번호를 위치에 기반하여 취득
PANE_IDS=($(tmux list-panes -t "multiagent:agents" -F "#{pane_id}" | sort))

log_info "검출된 페인: ${PANE_IDS[*]}"

# 페인 타이틀 설정 및 셋업
log_info "페인 타이틀 설정 중..."
PANE_TITLES=("boss1" "worker1" "worker2" "worker3")

for i in {0..3}; do
    PANE_ID="${PANE_IDS[$i]}"
    TITLE="${PANE_TITLES[$i]}"

    log_info "설정 중: ${TITLE} (${PANE_ID})"

    # 페인 타이틀 설정
    tmux select-pane -t "$PANE_ID" -T "$TITLE"

    # 작업 디렉토리 설정
    tmux send-keys -t "$PANE_ID" "cd $(pwd)" C-m

    # 컬러 프롬프트 설정
    if [ $i -eq 0 ]; then
        # boss1: 빨간색
        tmux send-keys -t "$PANE_ID" "export PS1='(\[\033[1;31m\]${TITLE}\[\033[0m\]) \[\033[1;32m\]\w\[\033[0m\]\$ '" C-m
    else
        # workers: 파란색
        tmux send-keys -t "$PANE_ID" "export PS1='(\[\033[1;34m\]${TITLE}\[\033[0m\]) \[\033[1;32m\]\w\[\033[0m\]\$ '" C-m
    fi

    # 환영 메시지
    tmux send-keys -t "$PANE_ID" "echo '=== ${TITLE} 에이전트 ==='" C-m
done

log_success "✅ multiagent 세션 작성 완료"
echo ""

# STEP 3: president 세션 작성 (1페인)
log_info "👑 president 세션 작성 시작..."

tmux new-session -d -s president
tmux send-keys -t president "cd $(pwd)" C-m
tmux send-keys -t president "export PS1='(\[\033[1;35m\]PRESIDENT\[\033[0m\]) \[\033[1;32m\]\w\[\033[0m\]\$ '" C-m
tmux send-keys -t president "echo '=== PRESIDENT 세션 ==='" C-m
tmux send-keys -t president "echo '프로젝트 총괄 책임자'" C-m
tmux send-keys -t president "echo '========================'" C-m

log_success "✅ president 세션 작성 완료"
echo ""

# STEP 4: 환경 확인 및 표시
log_info "🔍 환경 확인 중..."

echo ""
echo "📊 셋업 결과:"
echo "==================="

# tmux 세션 확인
echo "📺 Tmux Sessions:"
tmux list-sessions
echo ""

# 페인 구성 표시
echo "📋 페인 구성:"
echo "  multiagent 세션 (4페인):"
tmux list-panes -t "multiagent:agents" -F "    Pane #{pane_id}: #{pane_title}"
echo ""
echo "  president 세션 (1페인):"
echo "    Pane: PRESIDENT (프로젝트 총괄)"

echo ""
log_success "🎉 Demo 환경 셋업 완료!"
echo ""
echo "📋 다음 단계:"
echo "  1. 🔗 세션 어태치:"
echo "     tmux attach-session -t multiagent   # 멀티에이전트 확인"
echo "     tmux attach-session -t president    # 프레지던트 확인"
echo ""
echo "  2. 🤖 Claude Code 기동:"
echo "     # 순서1: President 인증"
echo "     tmux send-keys -t president 'claude' C-m"
echo "     # 순서2: 인증 후, multiagent 일괄 기동"
echo "     # 각 페인의 ID를 사용하여 claude를 기동"
echo "     tmux list-panes -t multiagent:agents -F '#{pane_id}' | while read pane; do"
echo "         tmux send-keys -t \"\$pane\" 'claude' C-m"
echo "     done"
echo ""
echo "  3. 📜 지시서 확인:"
echo "     PRESIDENT: instructions/president.md"
echo "     boss1: instructions/boss.md"
echo "     worker1,2,3: instructions/worker.md"
echo "     시스템 구조: CLAUDE.md"
echo ""
echo "  4. 🎯 데모 실행: PRESIDENT에 \"당신은 president입니다. 지시서에 따라주세요\"라고 입력"
