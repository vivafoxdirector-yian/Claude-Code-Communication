# Skill: Color Accessibility & Contrast Auditor (Review Loop)

## Description
CSS, Tailwind 클래스, 또는 HTML/React 컴포넌트 내의 색상 조합을 검사하여
W3C WCAG 2.1/2.2 AA 기준 준수 여부 및 색각 이상자 대응(어포던스)을 엄격히 검증합니다.

> 역할 분담: 이 파일은 **색상/대비/색각 전문 감사**다. 버튼-텍스트 구분, 포커스 링 유무,
> 레이아웃 affordance 등 **색상 외 사용성**은 [ux-affordance-audit.md](ux-affordance-audit.md)가 담당한다.
> (대비 관련 Blocker는 이 파일이 상세 기준의 단일 출처)

## Review Rules (3-Tier Classification)

1. [Blocker]
   - 일반 본문 텍스트(18pt 미만)의 텍스트-배경 명도 대비율이 **4.5:1 미만**인 경우 (예: 흰 배경에 밝은 회색 텍스트 #999999 등)
   - 대형 텍스트(18pt 이상/14pt 이상 굵게) 또는 인터랙티브 컴포넌트(입력창 보더, 버튼 포커스 링)의 명도 대비가 **3.0:1 미만**인 경우
   - 오류/성공 상태를 오직 '색상(빨강/초록)'으로만 구분하고 아이콘이나 보조 텍스트가 누락된 경우 (색각 이상자 배제)
   - 순수 블랙(#000000) 배경에 순수 화이트(#FFFFFF) 텍스트를 배치하여 할레이션/눈부심 피로를 유발하는 경우

2. [Follow-up]
   - 비활성화(Disabled) 상태 요소의 가독성 개선 여지
   - 다크 모드 전환 시 서피스(Surface) 간의 입체감 구분이 미흡한 경우
   - 호버(Hover)/포커스(Focus) 시 색상 변화 폭이 좁아 피드백이 약한 경우

3. [Non-actionable]
   - 기준(4.5:1)을 이미 충족한 상태에서 주관적인 채도 선호도 차이
   - 브랜드 아이덴티티에 따른 메인 컬러 선정 자체에 대한 취향 문제

## Exit Rule
- Blocker가 0건일 경우 즉시 합격(Pass) 판정한다.
- 지적 사항 발견 시 구체적인 수정 HEX 값 또는 대체 Tailwind 유틸리티 클래스를 즉시 제안한다.