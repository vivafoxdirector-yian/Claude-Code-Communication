#!/bin/bash

# 🚀 에이전트 간 메시지 전송 스크립트

# tmux의 base-index와 pane-base-index를 동적으로 취득
get_tmux_indices() {
    local session="$1"
    local window_index=$(tmux show-options -t "$session" -g base-index 2>/dev/null | awk '{print $2}')
    local pane_index=$(tmux show-options -t "$session" -g pane-base-index 2>/dev/null | awk '{print $2}')

    # 기본값
    window_index=${window_index:-0}
    pane_index=${pane_index:-0}

    echo "$window_index $pane_index"
}

# 에이전트→tmux 타겟 매핑
get_agent_target() {
    case "$1" in
        "president") echo "president" ;;
        "boss1"|"worker1"|"worker2"|"worker3")
            # multiagent 세션의 index를 동적으로 취득
            if tmux has-session -t multiagent 2>/dev/null; then
                local indices=($(get_tmux_indices multiagent))
                local window_index=${indices[0]}
                local pane_index=${indices[1]}

                # window명으로 취득 (base-index에 의존하지 않음)
                local window_name="agents"

                # pane 번호를 계산
                case "$1" in
                    "boss1") echo "multiagent:$window_name.$((pane_index))" ;;
                    "worker1") echo "multiagent:$window_name.$((pane_index + 1))" ;;
                    "worker2") echo "multiagent:$window_name.$((pane_index + 2))" ;;
                    "worker3") echo "multiagent:$window_name.$((pane_index + 3))" ;;
                esac
            else
                echo ""
            fi
            ;;
        *) echo "" ;;
    esac
}

show_usage() {
    cat << EOF
🤖 에이전트 간 메시지 전송

사용방법:
  $0 [에이전트명] [메시지]
  $0 --list

이용 가능한 에이전트:
  president - 프로젝트 총괄 책임자
  boss1     - 팀 리더
  worker1   - 실행 담당자A
  worker2   - 실행 담당자B
  worker3   - 실행 담당자C

사용 예시:
  $0 president "지시서에 따라주세요"
  $0 boss1 "Hello World 프로젝트 시작 지시"
  $0 worker1 "작업 완료했습니다"
EOF
}

# 에이전트 목록 표시
show_agents() {
    echo "📋 이용 가능한 에이전트:"
    echo "=========================="

    # president 세션 확인
    if tmux has-session -t president 2>/dev/null; then
        echo "  president → president       (프로젝트 총괄 책임자)"
    else
        echo "  president → [미기동]        (프로젝트 총괄 책임자)"
    fi

    # multiagent 세션 확인
    if tmux has-session -t multiagent 2>/dev/null; then
        local boss1_target=$(get_agent_target "boss1")
        local worker1_target=$(get_agent_target "worker1")
        local worker2_target=$(get_agent_target "worker2")
        local worker3_target=$(get_agent_target "worker3")

        echo "  boss1     → ${boss1_target:-[오류]}  (팀 리더)"
        echo "  worker1   → ${worker1_target:-[오류]}  (실행 담당자A)"
        echo "  worker2   → ${worker2_target:-[오류]}  (실행 담당자B)"
        echo "  worker3   → ${worker3_target:-[오류]}  (실행 담당자C)"
    else
        echo "  boss1     → [미기동]        (팀 리더)"
        echo "  worker1   → [미기동]        (실행 담당자A)"
        echo "  worker2   → [미기동]        (실행 담당자B)"
        echo "  worker3   → [미기동]        (실행 담당자C)"
    fi
}

# 로그 기록
log_send() {
    local agent="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    mkdir -p logs
    echo "[$timestamp] $agent: SENT - \"$message\"" >> logs/send_log.txt
}

# 메시지 전송
send_message() {
    local target="$1"
    local message="$2"

    echo "📤 전송 중: $target ← '$message'"

    # Claude Code의 프롬프트를 한 번 클리어
    tmux send-keys -t "$target" C-c
    sleep 0.3

    # 메시지 전송
    tmux send-keys -t "$target" "$message"
    sleep 0.1

    # 엔터 입력
    tmux send-keys -t "$target" C-m
    sleep 0.5
}

# 타겟 존재 확인
check_target() {
    local target="$1"
    local session_name="${target%%:*}"

    if ! tmux has-session -t "$session_name" 2>/dev/null; then
        echo "❌ 세션 '$session_name' 을(를) 찾을 수 없습니다"
        return 1
    fi

    return 0
}

# 메인 처리
main() {
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi

    # --list 옵션
    if [[ "$1" == "--list" ]]; then
        show_agents
        exit 0
    fi

    if [[ $# -lt 2 ]]; then
        show_usage
        exit 1
    fi

    local agent_name="$1"
    local message="$2"

    # 에이전트 타겟 취득
    local target
    target=$(get_agent_target "$agent_name")

    if [[ -z "$target" ]]; then
        echo "❌ 오류: 알 수 없는 에이전트 '$agent_name'"
        echo "이용 가능한 에이전트: $0 --list"
        exit 1
    fi

    # 타겟 확인
    if ! check_target "$target"; then
        exit 1
    fi

    # 메시지 전송
    send_message "$target" "$message"

    # 로그 기록
    log_send "$agent_name" "$message"

    echo "✅ 전송 완료: $agent_name 에 '$message'"

    return 0
}

main "$@"
