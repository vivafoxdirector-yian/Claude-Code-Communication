# Python Code Review Guidelines

## Table of Contents
- [Naming Conventions](#naming-conventions)
- [Code Structure](#code-structure)
- [Pythonic Code](#pythonic-code)
- [Type Hints](#type-hints)
- [Error Handling](#error-handling)
- [Design Patterns & Anti-patterns](#design-patterns--anti-patterns)
- [Severity Levels](#severity-levels)

## Naming Conventions

### PEP 8 (기본 적용)
- 클래스: `PascalCase` (e.g., `UserService`, `OrderRepository`)
- 함수/변수: `snake_case` (e.g., `get_user_by_id`, `total_count`)
- 상수: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`)
- 모듈: `snake_case` 소문자 (e.g., `user_service.py`, `order_utils.py`)
- 비공개 멤버: `_single_leading_underscore` (e.g., `_internal_method`)
- 이름 충돌 회피: `trailing_underscore_` (e.g., `class_`, `type_`)
- 매직 메서드: `__double_leading_trailing__` (e.g., `__init__`, `__str__`)

### 의미 있는 네이밍 체크리스트
- boolean 변수/함수: `is_`, `has_`, `can_`, `should_` 접두사 사용
- 컬렉션 변수: 복수형 사용 (e.g., `users`, `order_items`)
- 함수명은 동사로 시작 (e.g., `calculate_total`, `send_notification`)
- 축약어 지양: `usr` → `user`, `msg` → `message`
- 루프 변수가 단순 인덱스인 경우 `i`, `j` 허용, 단 의미 있는 이름 권장

## Code Structure

### 함수 길이 & 복잡도
- 함수: 30줄 이하 권장
- 순환 복잡도(Cyclomatic Complexity): 10 이하 권장
- 파라미터: 4개 이하 권장 (초과 시 dataclass나 dict로 래핑)
- 중첩 깊이: 3단계 이하 (early return 활용)
- 한 줄 최대 79자 (PEP 8 기준), 실용적으로 99자까지 허용

### 클래스 설계
- 단일 책임 원칙(SRP) 준수 여부
- `__init__`에서 너무 많은 로직 수행 여부
- 불변 객체 선호 (`@dataclass(frozen=True)`, `NamedTuple`)
- 상속보다 조합(composition) 선호
- 추상 기반 클래스(`ABC`) 적절한 활용

### 임포트 순서 (PEP 8)
1. 표준 라이브러리
2. 서드파티 라이브러리
3. 로컬 패키지/모듈
각 그룹은 빈 줄로 구분

### 코드 중복
- 동일 로직 3회 이상 반복 시 추출 고려
- 유틸리티 함수의 적절한 위치
- DRY 원칙 준수 여부

## Pythonic Code

### 리스트/딕셔너리/셋 컴프리헨션
```python
# Non-Pythonic
result = []
for x in range(10):
    if x % 2 == 0:
        result.append(x * 2)

# Pythonic
result = [x * 2 for x in range(10) if x % 2 == 0]
```

### 제너레이터 표현식 (메모리 효율)
```python
# 대용량 데이터 처리 시 리스트 대신 제너레이터 권장
total = sum(x * 2 for x in range(1_000_000))
```

### 컨텍스트 매니저
```python
# Non-Pythonic
f = open('file.txt')
data = f.read()
f.close()

# Pythonic
with open('file.txt') as f:
    data = f.read()
```

### 언패킹
```python
# Non-Pythonic
first = items[0]
rest = items[1:]

# Pythonic
first, *rest = items

# 스왑
a, b = b, a
```

### enumerate / zip 활용
```python
# Non-Pythonic
for i in range(len(items)):
    print(i, items[i])

# Pythonic
for i, item in enumerate(items):
    print(i, item)
```

### 딕셔너리 메서드 활용
```python
# Non-Pythonic
if key in d:
    value = d[key]
else:
    value = default

# Pythonic
value = d.get(key, default)
```

### f-string 사용 (Python 3.6+)
```python
# Non-Pythonic
message = "Hello, %s! You are %d years old." % (name, age)

# Pythonic
message = f"Hello, {name}! You are {age} years old."
```

### 조건 표현식
```python
# Non-Pythonic
if x is not None:
    result = x
else:
    result = default

# Pythonic
result = x if x is not None else default
```

## Type Hints

### 타입 어노테이션 (Python 3.5+)
- 함수 파라미터와 반환 타입에 타입 힌트 사용 권장
- `Optional[T]` 대신 `T | None` (Python 3.10+)
- 컬렉션 타입: `list[int]`, `dict[str, Any]`, `tuple[int, ...]`

```python
# 권장
def get_user(user_id: int) -> User | None:
    ...

def process_items(items: list[str]) -> dict[str, int]:
    ...
```

### 타입 힌트 체크리스트
- Public API(공개 함수/메서드)에는 타입 힌트 필수 권장
- `Any` 타입 남용 지양
- `TypeVar`를 활용한 제네릭 함수 적절한 사용
- `Protocol`을 활용한 구조적 서브타이핑 고려

## Error Handling

### 예외 처리
- 빈 `except` 블록 금지 (최소 `pass`에 이유 주석 또는 로깅)
- 너무 넓은 예외 타입 캐치 지양 (e.g., `except Exception:`, `except:`)
- 구체적인 예외 타입 사용 (e.g., `except ValueError:`, `except FileNotFoundError:`)
- 커스텀 예외 클래스 적절한 활용 (`class DomainError(Exception): ...`)
- `finally` 블록 vs 컨텍스트 매니저 선택

```python
# Bad
try:
    result = risky_operation()
except:
    pass

# Bad
try:
    result = risky_operation()
except Exception as e:
    print(e)

# Good
try:
    result = risky_operation()
except ValueError as e:
    logger.error("Invalid value: %s", e)
    raise
```

### None 처리
- 함수 반환 시 `None` 대신 빈 컬렉션, `Optional` 타입, 또는 예외를 고려
- `None` 체크는 `is None` / `is not None` 사용 (절대 `== None` 사용 금지)

## Design Patterns & Anti-patterns

### 확인할 Anti-patterns

**Mutable Default Argument (Python 특유의 함정)**
```python
# Bad - 리스트가 모든 호출에서 공유됨
def append_item(item, lst=[]):
    lst.append(item)
    return lst

# Good
def append_item(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

**God Class**: 하나의 클래스가 너무 많은 책임

**Magic Numbers**: 의미 불명의 리터럴 값
```python
# Bad
if status == 3:
    ...

# Good
STATUS_ACTIVE = 3
if status == STATUS_ACTIVE:
    ...
```

**Bare `except`**: 예외 타입 없이 모든 예외를 잡음

**`import *`**: 네임스페이스 오염, 명시적 임포트 권장

**Global 변수 남용**: 함수 외부 상태 의존

**과도한 `isinstance` 체크**: 다형성 또는 덕 타이핑 활용 권장

### SOLID 원칙

| 원칙 | 확인 포인트 | 심각도 |
|------|-----------|--------|
| SRP | 클래스/함수가 하나의 책임만 갖는가 | MAJOR |
| OCP | 새 기능 추가 시 기존 코드 수정 없이 확장 가능한가 | MAJOR |
| LSP | 하위 클래스가 상위 클래스를 안전하게 대체할 수 있는가 | CRITICAL |
| ISP | 인터페이스(ABC)가 적절히 분리되어 있는가 | MINOR |
| DIP | 추상화에 의존하고 DI를 활용하는가 | MAJOR |

### 권장 패턴
- `dataclass`: 데이터 보관 클래스에 활용
- `@property`: getter/setter 대신 프로퍼티 사용
- Context Manager (`__enter__`/`__exit__` 또는 `contextlib.contextmanager`)
- `functools.lru_cache` / `functools.cache`: 순수 함수 메모이제이션
- Strategy 패턴: 조건 분기가 많은 경우

## Severity Levels

| 레벨 | 설명 | 예시 |
|------|------|------|
| CRITICAL | 반드시 수정 필요 | 버그, 데이터 손실, 보안 취약점, Mutable Default Argument |
| MAJOR | 수정 강력 권고 | SRP 위반, 높은 복잡도, 빈 except 블록, bare except |
| MINOR | 수정 권장 | 네이밍 개선, 매직 넘버, 타입 힌트 누락, import 순서 |
| SUGGESTION | 참고 사항 | 더 Pythonic한 대안, 리팩토링 아이디어, 성능 개선 |
