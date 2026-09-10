# Skill: UX & Affordance Gatekeeper (Review Loop)

## Description
제시된 HTML/CSS/React 컴포넌트의 사용성(Affordance, 시인성, 조작성)을 
Apple HIG, Google Material Design, NN/g 원칙에 입각하여 엄격히 검증합니다.

> 역할 분담: 이 파일은 **일반 사용성/affordance 감사**(버튼-텍스트 구분, 포커스 링 유무, 입력 영역 인지, 인터랙션, 반응형)를 담당한다.
> **색상 대비/색각 이상**의 상세 기준은 [color-contrast-audit.md](color-contrast-audit.md)가 단일 출처다 — 아래 대비 항목은 요약이며, 정확한 임계값은 그 파일을 따른다.

## Review Rules (3-Tier Classification)
모든 지적 사항은 반드시 다음 3가지 레이블 중 하나로만 분류합니다:
1. [Blocker] : 
   - 클릭 가능한 버튼과 일반 텍스트/카드가 시각적으로 구분되지 않는 경우 (Flat의 한계)
   - 텍스트-배경 대비율 4.5:1 미달 (WCAG AA 위반, Soft UI/뉴모피즘의 대표적 결함)
   - 폼 입력창(Input)의 테두리나 포커스 링이 없어 입력 영역을 알 수 없는 경우
2. [Follow-up] :
   - 미세한 인터랙션 애니메이션(Hover/Active transition) 미흡
   - 모바일 반응형 여백 최적화 여지
3. [Non-actionable] :
   - 순수 취향 차이(폰트 패밀리 선호, 브랜드 색상 채도 등)

## Exit Rule
- Blocker가 0건이면 리뷰를 즉시 통과(Approve) 처리한다.
- 2회차 리뷰부터는 수정된 변경점(Diff)만 검토한다.