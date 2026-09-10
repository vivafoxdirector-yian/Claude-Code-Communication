# Skill: Color Token System Generator

## Description
입력된 브랜드 메인 컬러를 기반으로 UI 가독성, Semantic 표준(Success, Error, Warning, Info), 
60-30-10 배분 원칙을 충족하는 색상 토큰(Tailwind CSS 규격)을 설계합니다.

## Scope & Constraints (Scope Lock)
- 임의의 원색(Pure saturated color) 남발을 금지하며, 배경은 중립 무채색을 기본으로 한다.
- 메인 액션(Primary CTA) 컬러는 서비스 전반에서 일관된 1종만 정의한다.
- 다크 모드 토큰 생성 시 순수 블랙(#000000)을 지양하고 서피스 계층(#121212 등)을 사용한다.

## Input Format
- 브랜드 대표 색상 (Primary HEX 또는 컨셉 키워드):
- 다크 모드 지원 여부: (Yes / No)
- 타겟 서비스 분위기: (예: 신뢰감 있는 핀테크, 차분한 대시보드, 키치한 이커머스 등)

## Execution Checklist & Output
1. **60-30-10 Color Budgeting**:
   - 60% Dominant: Background & Main Canvas
   - 30% Secondary: Card surfaces, borders, secondary text
   - 10% Accent: Primary CTA, active badges, highlights
2. **Semantic Color Scale (Tailwind config)**:
   - Primary (50 ~ 900)
   - Neutral/Surface (50 ~ 900)
   - Status (Success, Destructive/Error, Warning, Info)
3. **Dark Mode Surface Hierarchy**:
   - Level 0 (Base Canvas) -> Level 1 (Card) -> Level 2 (Dialog/Dropdown)