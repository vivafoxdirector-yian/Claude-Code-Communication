# Skill: UI/UX Style Spec & Token Generator

## Description
사용자가 선택한 디자인 스타일에 맞춰 UI 정보 구조, 레이아웃, 컬러/타이포/섀도우 토큰 사양서를 작성합니다.
스타일 트렌드는 갱신되므로 아래 카탈로그(활성/참고)를 기준으로 하되, 상위 원칙(SKILL.md의 반클리셰·독창성·절제)이 항상 우선한다.

## Style Catalog (2026 기준)

### 활성 (Active — 최신·현역, 기본 선택지)
| 스타일 | 한 줄 정체성 | 대표 사례 |
|--------|--------------|-----------|
| **Bento Grid** | 크기 다른 카드를 격자에 배치, 가중치로 span 조절 | Apple, SaaS 대시보드 |
| **Liquid Glass** (Glassmorphism 2.0) | 반투명+강한 블러+스펙큘러 하이라이트, 굴절감 | Apple Liquid Glass (2025) |
| **Material 3 Expressive** | 다이내믹 컬러·톤 서피스·상태 레이어·표현적 셰이프 | Google (2025) |
| **Minimal / Swiss** | 절제된 뉴트럴+단일 액센트, 정밀 여백·타이포 위계 | Linear, Vercel, Stripe |
| **Aurora / Mesh Gradient** | 부드러운 메시·오로라 그라데이션 배경/액센트 | Stripe, Linear, AI 제품 |
| **Big / Expressive Typography** | 거대 가변폰트 디스플레이가 레이아웃을 주도 | 에이전시·포트폴리오 |
| **Dark-first Developer UI** | 다크 뉴트럴 베이스+고대비 크리스프+미세 글로우 | Linear, Railway, Supabase |

#### 데스크탑 시스템 프로그램 (Desktop system — 관리 콘솔·네이티브 앱·툴)
| 스타일 | 한 줄 정체성 | 대표 사례 |
|--------|--------------|-----------|
| **Fluent (Windows 11)** | Mica/Acrylic 머티리얼 + WinUI 컨트롤 + 시스템 액센트 | Windows 11 앱, Visual Studio, Terminal |
| **Desktop Density / Pro Tool** | 극고밀도 멀티패널 + 도킹 + 모노 수치 + 단축키 우선 (플랫폼 무관) | VS Code, JetBrains, DAW/CAD, 모니터링 콘솔 |

### 참고 (Reference — 정점 지남, 필요 시에만)
| 스타일 | 상태 |
|--------|------|
| **Neubrutalism** | 2022–24 정점, 지금 식는 중. 개성 강한 브랜드에만. |
| **Flat 2.0** | 용어 자체가 오래됨(2017). 사실상 현재의 기본값 → Minimal/Swiss로 대체 권장. |
| Claymorphism / Skeuomorphism | 니치·복고 맥락에서만. |

## Constraints (Scope Lock)
- 사양서 상단에 반드시 [목표 / 제외 항목 / 인수 조건]을 명시하여 기능을 임의 확장하지 않는다.
- 장식적 요소보다 사용자 조작 가능성(Affordance)과 명도 대비(접근성)를 우선한다.

## Input Format
- 서비스명 및 대상 화면:
- 목표 사용자:
- 선택 스타일: (활성 9종 중 택1)
  - 웹/제품: Bento Grid | Liquid Glass | Material 3 Expressive | Minimal/Swiss | Aurora/Mesh Gradient | Big Expressive Typography | Dark-first Developer UI
  - 데스크탑 시스템: Fluent (Windows 11) | Desktop Density / Pro Tool
  - (참고 스타일은 명시 요청 시에만)
- 브랜드 톤/무드: (예: 신뢰감·전문 / 발랄·에너지 / 미니멀·차분 — signature와 타이포 선정 근거로 사용)
- 핵심 컴포넌트:

## Output Specification
1. **Scope Lock**:
   - In-Scope (이번 화면에 반드시 들어갈 필수 컴포넌트 3~5개)
   - Out-of-Scope (차후 개선으로 미룰 항목)
   - Acceptance Criteria (완료 판정 기준)
2. **Design Tokens (Tailwind/CSS)**:
   - Color Palette (Primary, Surface, Text-contrast, Border)
   - **Typography** (아래 3-a 참조)
   - Elevation & Shadow (스타일별 그림자/블러 설정)
   - Border Radius & Line Thickness
3. **Layout & Grid Pattern**:
   - Bento Grid / Card hierarchy 배치도 (ASCII 또는 Markdown Table)

### 3-a. Typography (필수)
> 타이포그래피는 페이지의 "성격"을 전달하는 핵심이다. 어느 프로젝트에나 쓰는 무난한 폰트로 도망가지 말고, 이 브리프에 맞게 **의도적으로** 고른다.
- **Type Roles (2개 이상)**:
  - `Display` — 개성 있는 헤드라인용. **절제해서** 사용(남발 금지).
  - `Body` — Display와 어울리는 가독성 좋은 본문용.
  - `Utility` (선택) — 캡션·수치·라벨용 (모노스페이스 등).
- **Type Scale**: 명확한 스케일과 의도적 weight/width/letter-spacing 지정 (예: `text-4xl/tight/700`, `text-base/relaxed/400`).
- **Pairing 근거**: 왜 이 조합이 브랜드 톤/무드에 맞는지 1줄. (fallback 스택 포함: `"Font", system-ui, sans-serif`)
- **접근성**: 본문 최소 크기·행간이 가독성을 해치지 않는지 확인.

### 4. Signature Element (필수)
> 이 화면을 **기억하게 만드는 단 하나의 요소**. 브리프의 본질을 담되, 이것 하나에만 대담함을 쓰고 나머지는 절제한다.
- **무엇인가**: 이 페이지의 시그니처 1개를 지정 (예: 히어로의 인터랙티브 모먼트, 특징적 그리드 파괴, 데이터 시각화, 모션 시퀀스 등).
- **왜 이것인가**: 서비스/주제의 세계와 어떻게 연결되는지 1~2줄.
- **표현 방식**: 어떤 컴포넌트/토큰으로 구현할지 (선택 스타일과 정합).
- **절제 원칙**: 시그니처 외 요소는 조용하게 유지 — "집을 나서기 전 액세서리 하나를 뺀다"(Chanel).

> ⚠️ 상위 원칙 정합: 명명된 스타일(Bento/Glassmorphism 등)을 골랐더라도, 타이포·시그니처는 **템플릿 기본값이 아니라 이 브리프만의 선택**이어야 한다. (frontend-design SKILL.md의 반(反)클리셰·독창성 원칙이 우선)