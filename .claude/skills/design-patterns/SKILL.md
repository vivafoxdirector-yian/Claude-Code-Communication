---
name: design-patterns
description: "디자인 패턴(GoF) 스킬. Gang of Four의 23개 객체지향 디자인 패턴(생성/구조/행위)을 목적·적용 시점·트레이드오프·안티패턴 관점으로 다룬다. Clean Code in Python의 'Python식 패턴 적용' 관점을 반영해 언어 무관 카탈로그 + 파이썬 주의점을 함께 제공한다. 다음 상황에서 사용: (1) 특정 문제에 어떤 패턴이 맞는지 고를 때, (2) 코드에서 패턴 적용/리팩토링을 제안할 때, (3) 패턴의 의도·구조·예시를 설명할 때, (4) 패턴 오용(과용)을 진단할 때, (5) '디자인 패턴', '패턴', 'GoF', '팩토리', '싱글톤', '전략 패턴', '옵저버' 등 패턴명이 포함된 요청."
---

# Design Patterns (GoF)

Gang of Four의 23개 디자인 패턴을 **"문제 해결 도구"가 아니라 "더 유지보수 좋은 구조를 만드는 수단"** 으로 다룬다. (Clean Code in Python의 관점)

## 핵심 전제

> 패턴은 **목적이 아니라 결과**다. 처음부터 패턴을 끼워 맞추지 말 것(YAGNI 위반).
> "지금 필요한 것만 단순하게 쓰다가, 요구가 쌓이면 자연스럽게 패턴이 *떠오른다*(bottom-up)."
> 동적 언어(파이썬)에선 일급 함수·덕타이핑·내장 프로토콜 때문에 **일부 패턴이 불필요하거나 더 단순**해진다.

## Workflow

### 1. 문제/맥락 파악
- 무엇이 문제인가: 생성의 복잡성 / 구조·결합 / 행위·알고리즘 변동 중 어디인가?
- **패턴이 정말 필요한가?** 단순 함수·다형성·기존 언어 기능으로 풀리면 패턴은 과하다.

### 2. 패턴 후보 선정
카탈로그는 [references/gof-catalog.md](references/gof-catalog.md) 참조. 분류:
- **생성(Creational)**: 객체 생성 방식 — Factory Method, Abstract Factory, Builder, Prototype, Singleton
- **구조(Structural)**: 객체 조합/관계 — Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy
- **행위(Behavioral)**: 책임/알고리즘 분배 — Chain of Responsibility, Command, Iterator, Mediator, Memento, Observer, State, Strategy, Template Method, Visitor, Interpreter
- **GoF 외 실무 패턴(Beyond GoF)**: SPI/Plugin, Dependency Injection, Repository, Unit of Work, Null Object, DTO — GoF 조합 + 아키텍처 원칙(DIP)의 실무적 형태. 구조/경계 차원은 `clean-architecture-design`과 연계.

각 패턴은 **의도 / 적용 시점 / 협력 구조 / 트레이드오프·오용 신호**로 정리되어 있다.

### 3. 파이썬 적용 시 주의
[references/python-notes.md](references/python-notes.md) 참조 — 파이썬에서 "사라지거나 단순해지는" 패턴, 관용적 대안.
예: Strategy → 그냥 함수 전달, Singleton → 모듈/Borg, Iterator → 내장 프로토콜, Command → 일급 함수/클로저, Template Method → 부분 적용(partial).

### 4. 제안 / 진단
- **선택 제안**: 후보 1~2개를 트레이드오프와 함께 제시(과한 패턴은 배제 이유도 명시).
- **코드 진단**: 적용·오용을 짚는다.
  - **과용(over-engineering)**: 인터페이스 한 개뿐인데 Abstract Factory, 분기 2개에 Strategy 클래스 남발 등.
  - **잘못된 적용**: LSP 깨는 상속, 파이썬에서 비-관용적인 GoF 직역.
- 결과는 한국어로, 코드 예시·대안과 함께 제시한다.

원천 자료: GoF *Design Patterns* / `assets/reference/clean_code_in_python_...pdf` Ch.9.
