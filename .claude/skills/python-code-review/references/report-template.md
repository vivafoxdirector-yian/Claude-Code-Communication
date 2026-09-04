# Code Review Report Template

아래 마크다운 템플릿을 사용하여 리뷰 결과를 출력한다.

```markdown
# Python Code Review Report

**리뷰 일시**: {date}
**리뷰 대상**: {target} (파일 경로 또는 PR 정보)
**리뷰어**: Claude Python Code Review Skill

---

## 요약

| 항목 | 수 |
|------|-----|
| CRITICAL | {n} |
| MAJOR | {n} |
| MINOR | {n} |
| SUGGESTION | {n} |

### 총평
{1-3문장으로 전체적인 코드 품질 평가}

---

## 상세 리뷰

### CRITICAL

#### [{순번}] {이슈 제목}
- **파일**: `{파일경로}:{라인번호}`
- **설명**: {이슈 설명}
- **현재 코드**:
  ```python
  {문제 코드}
  ```
- **개선안**:
  ```python
  {개선 코드}
  ```

### MAJOR
(동일 형식)

### MINOR
(동일 형식)

### SUGGESTION
(동일 형식)

---

## 잘한 점
{코드에서 좋았던 부분 1-3가지 간단히 언급}
```
