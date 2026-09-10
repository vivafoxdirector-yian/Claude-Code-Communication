# Skill: Style-Compliant UI Component Generator

## Role
정의된 사양서에 맞춰 실제 프로덕션 레벨의 UI 코드를 작성합니다.

## Implementation Guidelines by Style (2026)

### 활성 스타일 (Active)

- **Bento Grid**: CSS Grid(`grid-cols-1 md:grid-cols-3 lg:grid-cols-4` 또는 12칼럼) 기반, 카드의 시각적 가중치에 따라 `col-span`/`row-span` 조절. 일관된 `gap`(16–24px), 통일 radius(16–24px), 카드마다 초점 1개(지표/비주얼). 콘텐츠가 높이를 정하게.
- **Liquid Glass** (Glassmorphism 2.0): `backdrop-filter: blur(20–30px) saturate(150%)` + 낮은 불투명 채움(`bg-white/8~12`) + 상단 스펙큘러 하이라이트(`inset 0 1px 0 rgba(255,255,255,.2)` 및 엣지 그라데이션) + radius 20–28px. **필수: 텍스트는 반드시 scrim 위에** 올려 AA 대비 확보(블러만으론 대비 미달). 생동감 있는/메시 배경 위에서 가장 좋음.
- **Material 3 Expressive**: 다이내믹 컬러 롤(primary/secondary/tertiary + container 톤) + 톤 서피스(surface, surface-container-low/high) + **상태 레이어**(hover 8% / press 12% 오버레이) + 표현적 셰이프 스케일(크고 다양한 corner radius). Elevation은 그림자보다 톤 색으로. 버튼: filled/tonal/outlined.
- **Minimal / Swiss**: 절제된 뉴트럴 팔레트 + 단일 액센트, 8px 스페이싱 그리드, 강한 타이포 위계, 헤어라인 보더(1px, 저대비), 그림자 최소, 작은 radius(6–10px), 넉넉한 여백. 장식 없음 — 콘텐츠·타이포가 전부.
- **Aurora / Mesh Gradient**: 블러된 다색 radial/mesh 블롭을 배경 레이어로(느린 drift 애니메이션, `prefers-reduced-motion`에서 정지). 전경 콘텐츠는 **불투명 서피스 카드** 위에 올려 대비 확보. 액센트 글로우는 절제.
- **Big / Expressive Typography**: 가변폰트 디스플레이를 히어로로 초대형 사용, 타이트한 leading, 극적인 스케일 대비(거대 H1 ↔ 작은 body). `text-wrap: balance`, 디스플레이에 음수 letter-spacing. 색은 최소, 타이포가 레이아웃을 주도.
- **Dark-first Developer UI**: 다크 뉴트럴 베이스(#0d0d10~#16161a, 순수 블랙 지양) + 고대비 크리스프 텍스트 + 미세 1px 보더(`rgba(255,255,255,.06~.10)`) + 작은 글로우/액센트. 정보 밀도 높게, 코드·수치엔 모노스페이스, 키보드 우선 어포던스, 작은 radius, 정교한 마이크로 인터랙션. 시맨틱 색은 채도 낮게.

### 데스크탑 시스템 프로그램 (Desktop system)

- **Fluent (Windows 11)**: WinUI 룩. **머티리얼** — Mica(창 배경, 데스크탑 색이 은은히 비침 → 웹/Electron에선 미묘한 레이어 틴트로 근사) + Acrylic(플라이아웃·패널에 반투명 `backdrop-filter: blur`). **레이어드 서피스**(창 base → layer → card)와 부드러운 elevation. **시스템 액센트 단일**(기본 Windows 블루 `#0067c0` 라이트 / `#4cc2ff` 다크). radius 8px(작은 요소 4px). 컨트롤: 좌측 NavigationView(확장형), 상단 CommandBar, 토글 스위치, 리스트/트리뷰의 선택 하이라이트(액센트 좌측 바 또는 채움), InfoBar. 타이포: `"Segoe UI Variable", "Segoe UI", system-ui`. 라이트/다크 양쪽. **connected/implicit 애니메이션**은 절제하고 `prefers-reduced-motion` 준수.
- **Desktop Density / Pro Tool**: 극고밀도. 작은 타이포(12–13px)·타이트한 행, **멀티패널 + 리사이즈 스플리터 + 도킹 패널**(트리/테이블/인스펙터), 메뉴바+툴바(아이콘 버튼)+상태바, 문서 탭. 저채도 뉴트럴 팔레트(장시간 작업엔 다크 선호), 선택/활성용 액센트 1개. **수치·좌표·값은 모노 + tabular-nums**. 장식 최소, 작은 radius(2–6px), 헤어라인 구분선. 키보드 우선(가시 포커스·단축키 힌트·컨텍스트 메뉴). 플랫폼 무관(Electron/Qt/web). 모션 최소.

### 참고 스타일 (Reference — 명시 요청 시에만)

- **Neubrutalism**: 하드 섀도우(`box-shadow: 4px 4px 0 #000`), 두꺼운 외곽선(`border-2 border-black`), 고대비 원색. (정점 지남 — 개성 강한 브랜드에만)
- **Flat 2.0**: 부드러운 elevation 섀도우 + 명확한 hover/focus 링. (현재는 기본값에 가까움 → Minimal/Swiss 권장)

## Quality Standards
- 순수 CSS/Tailwind 클래스만으로 상태(hover, focus-visible, active, disabled)를 완전히 구현할 것.
- 시각적 화려함 때문에 텍스트 가독성을 해치지 않을 것.