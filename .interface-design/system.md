# Interface design system — DRTC Puno legal assistant

Direction: "Mesa de estudio" — calm reading room + official-gazette precision. Full rationale in
`docs/ux/design-direction.md`. Tokens live in `frontend/src/styles.css` (`@theme`).

## Intent
- Who: legal/technical staff of DRTC Puno with a case file open; later, citizens on mobile.
- Task: find the rule, verify it in the source page, copy a correct citation.
- Feel: serious, trustworthy, documentary. Never playful, never generic SaaS.

## Palette (and why)
- Ink (DRTC navy) `--color-ink-600 #092475` — institutional identity, primary actions, references.
- Paper `--color-paper #f6f4ee` canvas; Folio `--color-folio #fff` for documents/cards.
- Marker `--color-marker #ffe58a` — only for cited passages (highlighter metaphor).
- Seal tones — verified (gold rim `#d3a62a`), unverified/pending (amber), superseded/unknown (slate),
  repealed (red). Text/soft pairs all ≥ 4.5:1.
- One accent (ink). Color always carries meaning; never decoration.

## Depth & surfaces
- Borders-only: `--color-rule-soft` (0.07) / `--color-rule` (0.12) / `--color-rule-strong` (0.24).
- No dramatic shadows. Same hue family across surfaces; header/footer = folio white + rule.

## Typography
- UI: Source Sans 3 (400/600/700). Titles & legal text: Libre Baskerville (serif).
- Identifiers ("Ley N.° 27181", eyebrows): IBM Plex Mono 400/500.
- Eyebrow pattern: mono, xs, uppercase, `tracking-widest`, tertiary text.

## Spacing & radius
- 4px base (Tailwind scale). Page padding `px-6`, section `py-10`, card padding `1.25rem 1.5rem`.
- Radius: 4 (seal, small), 6 (buttons, nav), 10 (cards, alerts).

## Signature components
- `ValiditySeal` (`shared/ui/validity-seal`): double-rim stamp, uppercase label + icon + sr-only
  description; tones via `data-tone`. Must appear wherever a norm/provision is shown.
- `InstrumentCard` (`features/library/ui`): mono reference → serif title → meta → edition block
  pinned to bottom (seal + edition label + "Actualizado al … · N páginas") → `<details>` alerts.
- Planned: citation chip with "Copiar cita"; Folio side panel with marker highlight; dictamen-style
  answer card (Conclusión / Fundamento / Análisis / Excepciones / Fuentes).

## States
- Loading: pulse skeleton cards with `aria-busy`. Error: `role="alert"` + "Reintentar". Empty: dashed
  rule box. Global corpus notice (amber) while any edition is unverified.
