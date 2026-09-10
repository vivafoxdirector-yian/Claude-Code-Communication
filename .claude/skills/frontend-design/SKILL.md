---
name: frontend-design
description: Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, typography, and making choices that don't read as templated defaults. Also drives a project workflow for building UI from a named design style — web/product (Bento Grid, Liquid Glass / Glassmorphism, Material 3 Expressive, Minimal / Swiss, Aurora / Mesh Gradient, Big Expressive Typography, Dark-first Developer UI) and desktop system programs (Fluent / Windows 11, Desktop Density / Pro Tool); Neubrutalism and Flat 2.0 kept as reference) — producing a scope-locked style spec with design tokens, generating style-compliant component code (HTML/CSS/Tailwind/React), and auditing UX affordance & WCAG contrast in a review loop. Use for UI/component design, design tokens/design systems, landing pages, or UX/accessibility review.
license: Complete terms in LICENSE.txt
---

# Frontend Design

Approach this as the design lead at a small studio known for giving every client a visual identity that could not be mistaken for anyone else's. This client has already rejected proposals that felt templated, and is paying for a distinctive point of view: make deliberate, opinionated choices about palette, typography, and layout that are specific to this brief, and take one real aesthetic risk you can justify.

## Ground it in the subject

If the brief does not pin down what the product or subject is, pin it yourself before designing: name one concrete subject, its audience, and the page's single job, and state your choice. If there's any information in your memory about the human's preferences, context about what they're building, or designs you've made before – use that as a hint. The subject's own world, its materials, instruments, artifacts, and vernacular, is where distinctive choices come from. Build with the brief's real content and subject matter throughout.

## Design principles

For web designs, the hero is a thesis. Open with the most characteristic thing in the subject's world, in whatever form makes sense for it: a headline, an image, an animation, a live demo, an interactive moment. Be deliberate with your choice: a big number with a small label, supporting stats, and a gradient accent is the template answer, only use if that's truly the best option.

Typography carries the personality of the page. Pair the display and body faces deliberately, not the same families you would reach for on any other project, and set a clear type scale with intentional weights, widths, and spacing. Make the type treatment itself a memorable part of the design, not a neutral delivery vehicle for the content.

Structure is information. Structural devices, numbering, eyebrows, dividers, labels, should encode something true about the content, not decorate it. Many generic designs use numbered markers (01 / 02 / 03), but that's only appropriate if the content actually is a sequence - like a real process or a typed timeline where order carries information the reader needs. Question if choices like numbered markers actually make sense before incorporating them.

Leverage motion deliberately. Think about where and if animation can serve the subject: a page-load sequence, a scroll-triggered reveal, hover micro-interactions, ambient atmosphere. An orchestrated moment usually lands harder than scattered effects; choose what the direction calls for. However, sometimes less is more, and extra animation contributes to the feeling that the design is AI-generated.

Match complexity to the vision. Maximalist directions need elaborate execution; minimal directions need precision in spacing, type, and detail. Elegance is executing the chosen vision well.

Consider written content carefully. Often a design brief may not contain real content, and it's up to you to come up with copy. Copy can make a design feel as templated as the design itself. See the below section on writing for more guidance.

## Process: brainstorm, explore, plan, critique, build, critique again

For calibration: AI-generated design right now clusters around three looks: (1) a warm cream background (near #F4F1EA) with a high-contrast serif display and a terracotta accent; (2) a near-black background with a single bright acid-green or vermilion accent; (3) a broadsheet-style layout with hairline rules, zero border-radius, and dense newspaper-like columns. All three are legitimate for some briefs, but they are defaults rather than choices, and they appear regardless of subject. Where the brief pins down a visual direction, follow it exactly — the brief's own words always win, including when it asks for one of these looks. Where it leaves an axis free, don't spend that freedom on one of these defaults. Just like a human designer who's hired, there's often a careful balance between doing what you're good at and taking each project as a chance to experiment and learn.

Work in two passes. First, brainstorm a short design plan based on the human's design brief: create a compact token system with color, type, layout, and signature. Color: describe the palette as 4–6 named hex values. Type: the typefaces for 2+ roles (a characterful display face that's used with restraint, a complementary body face, and a utility face for captions or data if needed). Layout: a layout concept, using one-sentence prose descriptions and ASCII wireframes to ideate and compare. Signature: the single unique element this page will be remembered by that embodies the brief in an appropriate way.

Then review that plan against the brief before building: if any part of it reads like the generic default you would produce for any similar page (work through a similar prompt to see if you arrive somewhere similar) rather than a choice made for this specific brief — revise that part, say what you changed and why. Only after you've confirmed the relative uniqueness of your design plan should you start to write the code, following the revised plan exactly and deriving every color and type decision from it.

When writing the code, be careful of structuring your CSS selector specificities. It's easy to generate CSS classes that cancel each other out (especially with a type-based selector like .section and a element-based selector like .cta). This can happen often with paddings/margins between sections.

Try to do a lot of this planning and iteration in your thinking, and only show ideas to the user when you have higher confidence it'll delight them.

## Restraint and self-critique

Spend your boldness in one place. Let the signature element be the one memorable thing, keep everything around it quiet and disciplined, and cut any decoration that does not serve the brief. Not taking a risk can be a risk itself! Build to a quality floor without announcing it: responsive down to mobile, visible keyboard focus, reduced motion respected. Critique your own work as you build, taking screenshots if your environment supports it – a picture is worth 1000 tokens. Consider Chanel's advice: before leaving the house, take a look in the mirror and remove one accessory. Human creators have memory and always try to do something new, so if you have a space to quickly jot down notes about what you've tried, it can help you in future passes.

## More on writing in design

Words appear in a design for one reason: to make it easier to understand, and therefore easier to use. They are design material, not decoration. Bring the same intentionality to copy that you would bring to spacing and color. Before writing anything, ask what the design needs to say, and how it can best be said to help the person navigate the experience.

Write from the end user's side of the screen. Name things by what people control and recognize, never by how the system is built. A person manages notifications, not webhook config. Describe what something does in plain terms rather than selling it. Being specific is always better than being clever.

Use active voice as default. A control should say exactly what happens when it's used: "Save changes," not "Submit." An action keeps the same name through the whole flow, so the button that says "Publish" produces a toast that says "Published." The vocabulary of an interface is the signposting for someone navigating the product. Cohesion and consistency are how people learn their way around.

Treat failure and emptiness as moments for direction, not mood. Explain what went wrong and how to fix it, in the interface's voice rather than a person's. Errors don't apologize, and they are never vague about what happened. An empty screen is an invitation to act.

Keep the register conversational and tuned: plain verbs, sentence case, no filler, with tone matched to the brand and the audience. Let each element do exactly one job. A label labels, an example demonstrates, and nothing quietly does double duty.

---

## Project Workflow (named-style UI pipeline)

> 이 섹션은 원문(Anthropic)에 프로젝트가 추가한 부분이다. 위 원칙(독창성·절제·AI 클리셰 회피)을 **상위 가이드**로 유지한 채, 아래 3단계로 실제 UI를 산출한다. 상세 지침은 각 참조 파일에 있다.

명명된 디자인 스타일로 UI를 만들 때 다음 순서로 진행한다. 스타일 카탈로그(활성 7종 + 참고)는 [references/design-style-spec.md](references/design-style-spec.md)의 Style Catalog 참조:

1. **사양 (Spec)** — [references/design-style-spec.md](references/design-style-spec.md)
   스타일을 택해 **Scope Lock(목표/제외/인수조건)** + 디자인 토큰(색/**타이포**/그림자/반경) + 레이아웃 + **시그니처 요소**까지 사양서를 작성한다. 코드 작성 전에 반드시 이 단계를 먼저.
   - 색상 토큰 심화 — [references/color-token-system.md](references/color-token-system.md): 브랜드색 기반 시맨틱 스케일(Primary/Neutral/Status 50~900), 60-30-10 배분, 다크모드 서피스 계층을 설계할 때 사용.
2. **구현 (Codegen)** — [references/ui-component-codegen.md](references/ui-component-codegen.md)
   사양서에 맞춰 프로덕션 UI 코드를 생성한다. 스타일별 Tailwind/CSS 가이드와 상태(hover/focus-visible/active/disabled) 완전 구현을 따른다.
3. **검증 (Audit)** — 두 감사를 함께 돌린다. 지적은 [Blocker]/[Follow-up]/[Non-actionable]로 분류, **Blocker 0건이면 통과**, 2회차부터 diff만 검토.
   - 일반 사용성 — [references/ux-affordance-audit.md](references/ux-affordance-audit.md): affordance·시인성·포커스·반응형 (HIG/Material/NN·g).
   - 색상 접근성 — [references/color-contrast-audit.md](references/color-contrast-audit.md): WCAG 2.1/2.2 AA 대비(본문 4.5:1 / 대형·UI 3.0:1), 색각 이상 대응. **대비 임계값의 단일 출처.**

주의: 위 원문 원칙과 이 파이프라인이 충돌하면(예: 명명된 스타일이 "AI 클리셰 3종"으로 수렴) **원문 원칙이 우선**한다 — 스타일은 골라도 그 안에서 독창성과 절제를 지킨다.
