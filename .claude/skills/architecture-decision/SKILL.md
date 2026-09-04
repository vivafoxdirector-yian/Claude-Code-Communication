---
name: architecture-decision
description: "아키텍처 의사결정 스킬. Srinath Perera의 Software Architecture and Decision Making을 기준으로 기술 선택의 트레이드오프를 분석하고 불확실성을 관리하며 의사결정을 기록한다. '5가지 질문'과 '7가지 원칙'으로 결정을 구조화하고 ADR(Architecture Decision Record)을 작성한다. 다음 상황에서 사용: (1) 기술 스택/아키텍처 스타일/패턴을 선택할 때(모놀리스 vs 마이크로서비스, 동기 vs 비동기, SQL vs NoSQL 등), (2) 트레이드오프를 비교·평가할 때, (3) 결정을 ADR로 문서화할 때, (4) HA·확장성·일관성·보안 등 macro 아키텍처 결정을 내릴 때, (5) '의사결정', '기술 선택', '트레이드오프', 'ADR', '아키텍처 결정' 키워드가 포함된 요청."
---

# Architecture Decision Making

Srinath Perera의 *Software Architecture and Decision Making* 프레임워크로 기술 결정을 구조화한다.
핵심 명제: **"깊게 생각하되, 천천히 구현하라(Think deeply, implement slowly)."** 대부분의 설계 실수는 지식 부족이 아니라 **판단(judgment) 부족**에서 온다.

## Workflow

### 1. 결정의 맥락 파악
무엇을 결정해야 하는가, 그리고 그 결정이 **바꾸기 어려운가(hard to change)** 아닌가를 먼저 가른다.
- 바꾸기 어려운 결정 → 깊게 분석(설계는 깊게).
- 바꾸기 쉬운 결정 → 빠르게 결정하고 증거로 학습(구현은 천천히/반복적으로).

### 2. 5가지 질문 (5 Questions)
모든 아키텍처 결정 전에 던진다. 상세는 [references/principles.md](references/principles.md).
1. **Time to market** — 시장 출시 적기는 언제인가?
2. **Team skill** — 팀의 기술 수준은 어떤가?
3. **Performance sensitivity** — 시스템의 성능 민감도는 어느 정도인가?
4. **Rewrite window** — 언제 시스템을 다시 쓸 수 있는가?
5. **Hard problems** — 가장 어려운 문제는 무엇인가? (조기에·병렬로 공략)

### 3. 7가지 원칙 (7 Principles) 적용
1. 모든 것을 **사용자 여정(user journey)** 에서 출발시킨다.
2. **반복적 thin-slice** 전략을 쓴다.
3. 매 반복마다 **최소 노력으로 최대 가치**를 더해 더 많은 사용자를 지원한다.
4. **결정을 내리고 리스크를 감수**한다(불확실성을 부하에게 떠넘기지 않는다).
5. **바꾸기 어려운 것은 깊게 설계**하되 **천천히 구현**한다.
6. **미지(unknown)를 제거**하고 증거로 학습한다 — 어려운 문제를 조기에·병렬로.
7. **응집(coherence) vs 유연성(flexibility)** 의 트레이드오프를 이해한다.

### 4. 트레이드오프 분석
선택지별로 장단점을 표로 비교한다. macro 아키텍처 결정 영역(상세는 references):
- **Coordination**: 클라이언트 주도 / 별도 서비스 / 중앙 미들웨어 / 코레오그래피
- **State 일관성**: 트랜잭션 / Saga / 이벤트소싱 등 "트랜잭션을 넘어서"
- **HA & Scale**: 가용성 추가, 확장 도구(캐시·샤딩·복제·큐)
- **Microservices 여부**: 공유 DB·보안·조정·의존성 지옥 회피 vs 느슨결합 모놀리스
기본값(default)이 통하는 경우를 먼저 제시하고, 복잡한 대안은 필요할 때만 권한다. 안티패턴도 함께 짚는다.

### 5. ADR 작성
결정은 [references/adr-template.md](references/adr-template.md) 형식의 ADR로 기록한다.
- 컨텍스트 → 고려한 선택지 → 결정 → 근거(5질문/7원칙 연결) → 결과/리스크.
- 한국어로 작성. 원천 자료: `assets/reference/software-architecture-and-decision-making-...pdf`
