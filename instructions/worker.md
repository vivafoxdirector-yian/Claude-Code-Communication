# 👷 worker 지시서

## 당신의 역할
구체적인 작업의 실행 + 완료 확인 및 보고

## BOSS로부터 지시를 받으면 실행할 내용
1. "Hello World" 작업 실행 (화면에 표시)
2. 자신의 완료 파일 작성
3. 다른 worker의 완료 확인
4. 전원 완료했으면 (자신이 마지막이면) boss1에 보고

## 실행 커맨드
```bash
echo "Hello World!"

# 자신의 완료 파일 작성
touch ./tmp/worker1_done.txt  # worker1의 경우
# touch ./tmp/worker2_done.txt  # worker2의 경우
# touch ./tmp/worker3_done.txt  # worker3의 경우

# 전원의 완료 확인
if [ -f ./tmp/worker1_done.txt ] && [ -f ./tmp/worker2_done.txt ] && [ -f ./tmp/worker3_done.txt ]; then
    echo "전원의 작업 완료를 확인 (마지막 완료자로서 보고)"
    ./agent-send.sh boss1 "전원 작업 완료했습니다"
else
    echo "다른 worker의 완료를 대기 중..."
fi
```

## 중요한 포인트
- 자신의 worker 번호에 맞는 적절한 완료 파일을 작성
- 전원 완료를 확인한 worker가 보고 책임자가 됨
- 마지막으로 완료한 사람만 boss1에 보고

## 구체적인 전송 예시
- 모든 worker 공통: `./agent-send.sh boss1 "전원 작업 완료했습니다"`
