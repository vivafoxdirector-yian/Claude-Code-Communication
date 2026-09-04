# Clean Code in Python — 심화 리뷰 기준

출처: Mariano Anaya, *Clean Code in Python (2nd Edition)* (assets/reference 의 PDF가 원천 자료).
기본 PEP 8/Pythonic 기준은 [python-guidelines.md](python-guidelines.md) 참조. 이 문서는 **심화 관점**을 다룬다.

---

## 1. Pythonic Code (관용구)
- **인덱스/슬라이스**: 직접 인덱싱 대신 슬라이싱·`__getitem__` 활용. 음수 인덱스/슬라이스 객체 이해.
- **컨텍스트 매니저**: 리소스 정리는 `with` + `__enter__`/`__exit__` 또는 `contextlib.contextmanager`. (try/finally 반복 금지)
- **컴프리헨션/할당식**: 가독성 높은 list/dict/set comprehension. 복잡하면 제너레이터나 함수로.
- **프로퍼티**: getter/setter 대신 `@property`. 단, 명령-조회 분리(CQS) 지킬 것.
- **이터러블·시퀀스 프로토콜**: `__iter__`, `__len__`, `__getitem__`을 구현해 파이썬다운 객체로.
- **매직 메서드/덕 타이핑**: 인터페이스보다 프로토콜. `__repr__`, `__eq__`, `__hash__` 일관성.

## 2. General Traits of Good Code (좋은 코드의 일반 특성)
- **Design by Contract**: 사전조건(precondition)/사후조건(postcondition)을 명확히. 호출자/피호출자 책임 경계를 정한다.
- **방어적 프로그래밍**: 예상 가능한 에러는 처리, 예상 못한 것은 빠르게 실패(fail fast). assert는 "절대 일어나면 안 되는" 조건에만.
- **예외 처리**:
  - 빈 `except:` / `except Exception` 남용 금지.
  - 예외를 흐름 제어로 쓰지 않기. 적절한 추상화 수준에서 처리.
  - 원본 예외 컨텍스트 보존(`raise ... from e`). 민감정보 노출 금지.
- **관심사 분리(SoC)** & **응집도↑ 결합도↓**.
- **DRY / OAOO**: 지식의 중복 제거(단순 코드 중복이 아니라 "지식"의 중복).
- **YAGNI / KIS**: 필요해질 때까지 만들지 말고, 단순하게.
- **EAFP > LBYL**: "허락보다 용서" — try/except가 파이썬다움. (단, 남용 주의)

## 3. SOLID in Python
- **SRP**: 클래스/모듈의 변경 이유 하나. 거대 클래스(God Class) 분리.
- **OCP**: 다형성·전략으로 확장. `if isinstance(...)` 연쇄는 신호.
- **LSP**: 하위 클래스가 계약을 깨지 않음(시그니처·반환·예외).
- **ISP**: 작은 인터페이스(ABC/Protocol)로 분리.
- **DIP**: 구체 구현이 아니라 추상(Protocol/ABC)에 의존. 의존성 주입.

## 4. Decorators (데코레이터)
- 함수/클래스/코루틴 데코레이터로 **횡단 관심사(로깅·검증·재시도·캐싱)** 분리 → DRY.
- `functools.wraps`로 메타데이터 보존(누락 시 디버깅·introspection 깨짐).
- **부작용(side effect) 주의**: import 시점에 실행되는 부작용을 데코레이터 본문에 두지 말 것.
- 인자 받는 데코레이터는 중첩 함수 / 데코레이터 객체(`__call__`)로.
- 좋은 데코레이터: 재사용성·관심사 분리·캡슐화가 명확.

## 5. Descriptors (디스크립터)
- `__get__`/`__set__`/`__delete__`로 속성 접근 제어. data vs non-data descriptor 구분.
- `@property`, `@classmethod`, ORM 필드 등 내부 동작의 기반. 반복되는 프로퍼티 로직을 디스크립터로 추출.
- 과용 주의 — 단순 케이스는 property로 충분.

## 6. Generators / Iterators / Async
- **제너레이터**로 메모리 효율적 지연 평가. 대용량 데이터는 list 대신 generator/`yield`.
- 제너레이터 표현식 `(x for x in ...)`로 파이프라인 구성.
- `itertools` 활용(체이닝·그룹핑·슬라이싱).
- **async**: `async def`/`await`, async 컨텍스트 매니저(`__aenter__`), async 이터레이션(`__aiter__`/`__anext__`), async 제너레이터. IO 바운드에 적합, CPU 바운드엔 부적합.

## 7. Unit Testing & Refactoring
- **테스트 가능한 설계가 먼저**: 좋은 테스트의 비결은 테스트 자체가 아니라 테스트 가능한 코드.
- `unittest`/`pytest`, 경계/예외/엣지 케이스 커버. fixture·parametrize 활용.
- mock은 외부 의존(IO/네트워크/시간)에만. 과도한 mock은 설계 결함 신호.
- 리팩토링은 테스트라는 안전망 위에서. 코드 진화의 전제.

## 8. Common Design Patterns (Python식)
- GoF 패턴을 그대로 옮기지 말 것 — 파이썬에선 일급 함수·덕타이핑으로 더 간단해지는 패턴이 많다(Strategy=함수, Singleton=모듈, Borg 등).
- 패턴은 "문제 해결"이 아니라 "더 유지보수 좋은 구조"의 관점에서 적용.

---

## 리뷰 시 추가 심각도 가이드 (기본 SKILL.md 기준 보완)
- **CRITICAL**: 데코레이터/디스크립터의 부작용으로 인한 버그, mutable default, 리소스 누수(컨텍스트 매니저 미사용).
- **MAJOR**: SOLID 위반, Design by Contract 부재로 인한 모호한 책임, 광범위 예외 포착, 테스트 불가능한 강결합.
- **MINOR**: 비-Pythonic 관용구(수동 인덱싱·불필요한 LBYL), `functools.wraps` 누락.
- **SUGGESTION**: 제너레이터로 메모리 개선, 패턴을 파이썬식으로 단순화, 디스크립터로 중복 프로퍼티 추출.
