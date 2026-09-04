# 파이썬에서의 디자인 패턴 — 주의점과 관용적 대안

출처: Mariano Anaya, *Clean Code in Python* Ch.9 *Common Design Patterns* (assets/reference 의 PDF).

## 큰 원칙

- GoF 패턴은 **정적 타입 언어(C++/Java)** 를 전제로 고안된 것이 많다. 파이썬의 **동적 타이핑·일급 함수·덕 타이핑**은 일부 패턴을 **불필요(invisible)** 하게 만든다.
- 패턴을 **직역(literal translation)** 하면 오히려 **비-Pythonic**해진다. "패턴이 맞는 자리에만, 파이썬다운 방식으로" 적용한다.
- 패턴은 미리 적용하지 말고(YAGNI), 리팩토링 과정에서 **떠오르게(emerge)** 한다 — 객체지향 설계는 bottom-up.

---

## 파이썬에서 사라지거나 단순해지는 패턴

| GoF 패턴 | 파이썬 관용 대안 |
|----------|------------------|
| **Strategy** | 전략 클래스 계층 대신 **함수를 인자로 전달**(일급 함수). `key=func` 처럼. |
| **Command** | **클로저 / `functools.partial` / 호출 가능 객체**로 작업 캡슐화. |
| **Iterator** | **언어 내장** — `__iter__`/`__next__`, 제너레이터(`yield`). 직접 구현 거의 불필요. |
| **Template Method** | 상속 대신 **부분 적용(partial)** 또는 고차 함수로 가변 단계 주입. |
| **Singleton** | **모듈 자체가 싱글톤**. 공유 상태가 필요하면 **Borg/monostate**(`__dict__` 공유). |
| **Prototype** | `copy.copy` / `copy.deepcopy`. |
| **Builder** | **키워드 인자 / `@dataclass` / `__post_init__`** 로 대체되는 경우 多. |
| **Decorator (구조 패턴)** | 함수/클래스 래핑은 자연스러우나, **`@` 데코레이터 문법과는 별개 개념**임에 유의. |
| **Adapter** | **다중 상속·믹스인·컴포지션**으로 표현. 데코레이터를 어댑터로 쓰기도. |
| **Flyweight** | `__slots__`, 객체 인터닝, 캐싱(`functools.lru_cache`)이 먼저. |
| **Null Object** | `None` 대신 기본 동작 객체를 반환해 다형성 유지 — 파이썬에서도 매우 유용. |

> ⚠️ **혼동 주의**: 파이썬의 `@decorator`(함수/클래스 데코레이터)는 GoF의 **Decorator 패턴과 이름만 같고 다른 것**이다. (Clean Code in Python도 명시적으로 경고)

---

## Ch.9가 실제로 다루는 패턴 (파이썬 구현 관점)

- **Factory** (생성을 파이썬식으로 — 함수·`__call__`)
- **Singleton & shared state (monostate / Borg)**
- **Builder**
- **Adapter**
- **Composite**
- **Facade**
- **Chain of Responsibility**
- **Template Method**
- **Null Object**

각 패턴을 "문제 해결 도구"가 아니라 **"이 구현이 다른 선택지보다 왜 더 깨끗하고 유지보수 좋은가"** 의 관점으로 분석한다.

---

## 파이썬에서 패턴 적용 시 체크리스트

- [ ] 이 문제, **언어 기본 기능(일급 함수·제너레이터·컨텍스트 매니저·dataclass)** 으로 더 단순히 풀리지 않는가?
- [ ] GoF 구조를 **직역**해서 불필요한 클래스 계층을 만들고 있지 않은가?
- [ ] 지금 **정말 필요한가**, 아니면 미래를 위한 과한 추상화(YAGNI 위반)인가?
- [ ] 패턴 이름(특히 Decorator)을 파이썬 기능과 혼동하고 있지 않은가?
- [ ] 패턴 적용 후 **테스트가 더 쉬워졌는가** (어려워졌다면 잘못된 신호)?
