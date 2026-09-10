# 출처 및 라이선스

이 스킬은 직접 작성한 것이 아니라 Anthropic 공식 저장소에서 가져온 것이다.

- **원본**: https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md
- **가져온 날짜**: 2026-07-09
- **라이선스**: © Anthropic PBC. All rights reserved. Anthropic Commercial Terms of Service 적용.
  - 원본 SKILL.md frontmatter는 `LICENSE.txt`를 참조하나, 원 저장소의 스킬 폴더/플러그인 루트에서 해당 파일을 찾지 못했다. 저장소 전체 라이선스는 Anthropic 독점(Commercial ToS)이다.
  - Claude Code 내 사용은 의도된 용도에 해당한다. 재배포/외부 공개 시 Anthropic Commercial ToS를 확인할 것.

## 변경 이력
- **2026-07-09**: 최초 도입. `SKILL.md` 원문 그대로(verbatim).
- **2026-09-10**: 프로젝트 확장. 원문 본문은 유지하되,
  - frontmatter `description`에 명명된-스타일 UI 파이프라인 관련 설명 추가(자동 트리거 확장 목적).
  - 본문 하단에 "## Project Workflow (named-style UI pipeline)" 섹션 추가 — 아래 참조 파일 3종을 3단계로 배선.
  - 프로젝트가 추가한 참조 파일(원저작자 Anthropic 아님, 프로젝트 자체 작성):
    - `references/design-style-spec.md` (사양·토큰 생성)
    - `references/ui-component-codegen.md` (스타일 준수 코드 생성)
    - `references/ux-affordance-audit.md` (UX/접근성 감사 루프)
  - 원문 원칙과 파이프라인 충돌 시 원문 원칙 우선으로 명시.
- **2026-09-10 (2차)**:
  - `design-style-spec.md`에 Typography(3-a) + Signature Element(4) 항목 추가 — 원문의 타이포·시그니처 강점을 파이프라인에 흡수.
  - 색상 전문 참조 파일 2종 추가(프로젝트 자체 작성): `references/color-token-system.md`(색상 토큰 생성), `references/color-contrast-audit.md`(색상 대비/색각 감사).
  - 감사 역할 분담 명시: `ux-affordance-audit`=일반 사용성, `color-contrast-audit`=색상 대비(임계값 단일 출처). 중복 제거.
  - `color-contrast-audit.md`의 붙여넣기 아티팩트 교정: 4.51→4.5:1, 3.01→3.0:1, WCAG 2.12.2→2.1/2.2, 빨강초록→빨강/초록, HTMLReact→HTML/React 등.
  - SKILL.md Project Workflow에 위 2종 배선.
- **2026-09-10 (3차, 스타일 카탈로그 최신화)**:
  - 활성 스타일 7종으로 개편: Bento Grid / Liquid Glass(=Glassmorphism 2.0) / Material 3 Expressive / Minimal·Swiss / Aurora·Mesh Gradient / Big Expressive Typography / Dark-first Developer UI.
  - Neubrutalism·Flat 2.0은 "참고(Reference)"로 강등(명시 요청 시에만). Claymorphism/Skeuomorphism도 참고로 기재.
  - `design-style-spec.md`에 Style Catalog(활성/참고) 표 추가, 선택지 갱신.
  - `ui-component-codegen.md` 스타일별 구현 가이드를 7종 기준으로 재작성.
  - SKILL.md frontmatter description·워크플로 스타일 목록 동기화.
- **2026-09-10 (4차, 데스크탑 시스템 스타일 추가)**:
  - 활성 카탈로그에 데스크탑 시스템용 2종 추가: **Fluent (Windows 11)**, **Desktop Density / Pro Tool**. (활성 총 9종)
  - `design-style-spec.md` 카탈로그·선택지, `ui-component-codegen.md` 구현 가이드, SKILL.md description 동기화.
