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
- `Folio` (`features/reader/ui/folio`): white page panel — toolbar (page, zoom, "Abrir PDF"), passage line
  (marker-yellow "PASAJE" badge + server citation + pages), page chips for multi-page passages, then the
  canvas on the paper tone. The marker is `--color-marker` with `mix-blend-mode: multiply` so the text
  stays readable; a replaced text is dashed red ("Texto anterior · no vigente"), never yellow.
- Reading column: breadcrumb + seal on one row, serif heading ("Artículo 2" + muted title), provision nodes
  with mono locator + page; the focused node gets an ink left rule and a pale ink wash. Actions ("Ver en el
  PDF", "Copiar cita", "Cita breve") are quiet until hover/focus and always visible on touch.
- Replaced text lives in a `<details>` ("Texto anterior, no vigente") with a dashed red border and a solid
  red "NO VIGENTE" tag; review warnings are amber `role="note"` boxes; editorial notes are a collapsed list.
- `ReferenceSearch` (header combobox): mono "/" hint, results in a bordered popover; ink outline on the
  active option; each result shows the server citation, page, a two-line serif snippet and
  "edición no verificada".
- `ReferenceSearch` also ends its list with a quiet, ruled option «🔍 Buscar "…" en el texto» (ink text,
  always last; reached with ↓ or a click): the way out to the content search.
- `ResultCard` (`features/search/ui`): mono norm name → serif server citation → muted title → serif snippet
  with the matched words on a pale ink wash and bold (**not** the yellow marker, which stays reserved for
  cited passages in the reader) → foot (seal + edition + mono page + «Por palabras / Por significado /
  Referencia exacta» tags written out, never colour alone) → ink «Leer en la norma» button. Other matching
  passages live in a `<details>`. A reference the person typed gets an ink left rule: it is first on
  purpose. Diagnostics (dev builds only) are a dashed `<details>` of mono key/values.
- «Buscar en el texto» page: one column (≤ 56rem) — eyebrow, h1, one sentence («no son una respuesta ni una
  opinión legal»), a labelled field + «Buscar», the privacy line, norm chips (pill, ink when pressed),
  a `role="status"` count, an amber `role="note"` when the meaning search is unavailable, then the cards.
  The first card must start close to the fold on a phone, so the intro stays one sentence.
- Planned: dictamen-style answer card (Conclusión / Fundamento / Análisis / Excepciones / Fuentes).

## Responsive
- ≥ 1024 px: three columns — index (17rem, sticky) · reading (≤ 46rem) · Folio (22–34rem, sticky).
- Below: one pane at a time — "Índice" disclosure + segmented Texto | PDF; "Ver en el PDF" switches to PDF.
- Mobile trims chrome (compact corpus notice, one-row Folio toolbar) so the text starts above the fold.

## States
- Loading: pulse skeleton cards with `aria-busy`. Error: `role="alert"` + "Reintentar". Empty: dashed
  rule box. Global corpus notice (amber) while any edition is unverified.
