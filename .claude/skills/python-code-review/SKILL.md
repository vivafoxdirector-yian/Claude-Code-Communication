---
name: python-code-review
description: "Python 코드 리뷰 스킬. 코드 품질, 가독성, 네이밍, 구조, 중복, 복잡도를 중점적으로 리뷰하며 PEP 8 및 Pythonic 코드 원칙을 기준으로 한다. 다음 상황에서 사용: (1) 사용자가 Python 코드 리뷰를 요청할 때, (2) PR이나 git diff의 Python 변경사항을 리뷰할 때, (3) 특정 .py 파일이나 디렉토리의 코드 품질을 점검할 때, (4) 리뷰, review, 코드 점검, 코드 체크 등의 키워드가 포함된 Python 관련 요청"
---

# Python Code Review

Python 코드를 품질/가독성 관점에서 리뷰하고 마크다운 리포트를 생성한다.

## Workflow

### 1. 리뷰 대상 파악

사용자 요청에 따라 리뷰 대상을 결정한다:

**Git diff/PR 기반:**
```bash
# 스테이징된 변경사항
git diff --cached

# 특정 브랜치 대비 변경사항
git diff main...HEAD

# GitHub PR
gh pr diff {PR번호}
```

**파일/디렉토리 기반:**
- 사용자가 지정한 파일이나 디렉토리의 `.py` 파일을 대상으로 한다
- Glob 패턴 `**/*.py`로 대상 파일을 탐색한다

### 2. 코드 분석

리뷰 가이드라인은 [references/python-guidelines.md](references/python-guidelines.md) 참조.
심화 리뷰 기준(Design by Contract, 데코레이터/디스크립터, 제너레이터/async, SOLID, 테스트 가능성 등)은 *Clean Code in Python* 기반 [references/clean-code-python.md](references/clean-code-python.md) 참조.

핵심 체크포인트:
- **네이밍**: PEP 8 준수, 의미 있는 이름, snake_case/PascalCase/UPPER_SNAKE_CASE
- **함수 길이/복잡도**: 30줄 이하, 순환 복잡도 10 이하
- **클래스 설계**: SRP, 불변성 선호, 조합 우선
- **Pythonic 코드**: 리스트 컴프리헨션, 제너레이터, 컨텍스트 매니저, 언패킹
- **타입 힌트**: 함수 시그니처의 타입 어노테이션 사용 여부
- **에러 처리**: 빈 except, 넓은 예외 타입, 적절한 예외 계층
- **코드 중복**: 3회 이상 반복 로직
- **Anti-patterns**: God Class, Magic Numbers, Mutable Default Arguments 등

### 3. 리포트 출력

[references/report-template.md](references/report-template.md)의 마크다운 템플릿에 따라 결과를 출력한다.

심각도 기준:
- **CRITICAL**: 버그, 데이터 손실 가능성, 보안 취약점
- **MAJOR**: SRP 위반, 높은 복잡도, 빈 except 블록, Mutable Default Argument
- **MINOR**: 네이밍 개선, 매직 넘버, 타입 힌트 누락
- **SUGGESTION**: 더 Pythonic한 대안 제안, 리팩토링 아이디어

리포트는 한국어로 작성하며, 코드 예시와 개선안을 함께 제시한다. 마지막에 잘한 점도 1-3가지 언급한다.

### 4. 결과 파일 저장

리뷰가 완료되면 `result/` 디렉토리 하위에 결과 파일을 마크다운으로 저장한다.

- **파일명 규칙**: `result_YYYYMMDD.md` (예: `result_20260601.md`)
- **경로**: `result/result_YYYYMMDD.md`
- 동일 날짜에 여러 번 리뷰 시 suffix를 추가한다: `result_YYYYMMDD_2.md`
- 결과 파일에는 리포트 템플릿에 따른 전체 리뷰 내용을 포함한다
