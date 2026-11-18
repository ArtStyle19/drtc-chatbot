# Inventario del corpus inicial

Fase 1 de la arquitectura de referencia ("inventario y validación jurídica"). Datos obtenidos al
inspeccionar los PDF el 17-11-2026; la fuente de verdad estructurada es
[`corpus/manifest.yaml`](../../corpus/manifest.yaml).

## Resumen

| | Ley 27181 | DS 017-2009-MTC (RENAT) | TUO Ley 27444 |
|---|---|---|---|
| Archivo | `ley-27181-lgttt-texto-2020-06.pdf` | `ds-017-2009-mtc-renat-actualizado-2017-01-04.pdf` | `tuo-ley-27444-ds-004-2019-jus-minjus-2021.pdf` |
| Páginas | 36 | 181 | 292 |
| Capa de texto | Sí (Word 2016) | Sí (Word 2010) | Sí (InDesign) |
| ¿Requiere OCR? | No | No | No |
| Origen | Compilación no oficial formato SPIJ | Edición del MTC (DGTT) | Edición oficial MINJUSDH (2.ª, jul-2021) |
| Texto incluye cambios hasta | 31-05-2020 (inferido) | 04-01-2017 (+ nota del 12-01-2017) | julio de 2021 |
| Números de página impresos | No | No | Coinciden con la página del PDF |
| Estado | `unverified` | `unverified` | `unverified` (posiblemente sustituido) |

## Estructura encontrada

**Ley 27181:** Título I (p. 2) · Título II (p. 8) · Título III (p. 15) · Título IV (p. 18) ·
Título V (p. 26) · Títulos VI-VII (pp. 32-33) · Disposiciones complementarias, transitorias y finales
(pp. 33-36). Notas "(*)" de prórrogas COVID-19 al inicio. El art. 2 aparece en su redacción original
y en la sustituida por el DU 019-2020 (p. 2-3).

**RENAT (DS 017-2009-MTC):** DS aprobatorio (pp. 1-2) · Sección Primera (p. 2) · Segunda (p. 20) ·
Cuarta (p. 86) · Quinta (p. 97) · Sexta y DCF (p. 139) · DCT (p. 145) · DCD (p. 163) · Anexo 1
(p. 166) · Anexo 2 (pp. 170-181). 138 artículos según el DS aprobatorio. Notas "(*)" con textos
sustituidos e incorporados.

**TUO Ley 27444:** preliminares (pp. 1-22: presentación, guía del lector, abreviaturas, normas
concordadas) · **Primera Parte: Manual explicativo (pp. 23-68) — no normativo** · Segunda Parte
(p. 69) · DS 004-2019-JUS (pp. 71-77) · texto del TUO desde el Título Preliminar (p. 78; art. I en
p. 79) hasta p. 284 · índice (pp. 285-289) · colofón (pp. 290-292). Las notas al pie indican el
origen de cada texto ("Texto según el artículo … de la Ley N.° 27444, modificado por …").

## Vigencia: hallazgos (pendientes de verificación oficial)

1. **TUO de la Ley 27444.** El **DS 006-2026-JUS** (publicado el 30-04-2026) aprobó un nuevo TUO y
   derogó el aprobado por el DS 004-2019-JUS, base del PDF cargado. Según comentaristas, el nuevo TUO
   sigue la numeración de la propia Ley 27444 modificada, por lo que **los números de artículo
   pueden no coincidir** con los del PDF. Hay fuentes con fechas de vigencia distintas (1-05-2026 o
   seis meses después): verificar en El Peruano.
2. **Ley 27181.** Modificada después de 2020, entre otras por el DL 1707 (ene-2026, Sistema
   Integrado de Transporte), la Ley 32598 (may-2026) y la Ley 32616 (arts. 25 y 28).
3. **RENAT.** Modificado muchas veces desde 2017; p. ej. el DS 006-2025-MTC modificó el art. 11 y
   los numerales 25.2 y 90.2. También hay regímenes de pago de multas (DS 016-2025-MTC,
   DS 017-2026-MTC) que remiten al RENAT.

**Consecuencia:** el corpus actual sirve para construir y probar el sistema, nunca para responder
como si fuera la norma vigente. SPIKE-01 cargará los textos oficiales como nuevas versiones.

Fuentes consultadas (secundarias, para orientar la verificación):
[CMS – nuevo TUO LPAG](https://cms.law/es/per/publication/aprueban-el-nuevo-texto-unico-ordenado-de-la-ley-del-procedimiento-administrativo-general) ·
[MINJUSDH – nota de prensa](https://www.gob.pe/institucion/minjus/noticias/1386239-minjusdh-simplifica-tramites-y-publica-nuevo-texto-unico-de-la-ley-del-procedimiento-administrativo-general) ·
[SUNAT – control de cambios](https://www.sunat.gob.pe/legislacion/procedim/normasadua/gja-01/ctrlCambios/cc-gja-01-006-TUO-30-04-2026.htm) ·
[LP – DL 1707](https://img.lpderecho.pe/wp-content/uploads/2026/01/Decreto-Legislativo-1707-LPDerecho.pdf) ·
[LP – Ley 32616](https://img.lpderecho.pe/wp-content/uploads/2026/05/Ley-32616-LPDerecho-1.pdf) ·
[MTC – DS 006-2025-MTC](https://www.gob.pe/institucion/mtc/normas-legales/6679488-006-2025-mtc).

## Fuentes oficiales para SPIKE-01

- **SPIJ** (MINJUSDH): legislación sistematizada y concordada.
- **El Peruano – Normas Legales Actualizadas**: textos consolidados con fecha de actualización.
- **Portales del MTC y del MINJUSDH**: ediciones oficiales y TUO.

No reemplace los PDF actuales: agregue los nuevos como documentos fuente y versiones adicionales, y
registre cuál está verificada como vigente.

## Resultado de la ingesta (Sprint 1, 2026-11-18)

Medido con `drtc-ingest run --all` sobre los tres PDF (≈ 5 s en total). Los artículos coinciden con los
oficiales: **36** (Ley 27181, más `4-A`, `9-A`, `16-A`, `26-A`), **138** (RENAT, más `12-A`) y **265** (TUO,
más los 9 del Título Preliminar), sin saltos de numeración.

| | Ley 27181 | RENAT | TUO Ley 27444 |
|---|---|---|---|
| Disposiciones vigentes | 259 | 1 431 | 1 247 |
| Textos sustituidos (revisiones anteriores) | 98 | 235 | 0 |
| Notas editoriales guardadas | 74 | 445 | ≈ 540 |
| Casos marcados para revisión | 5 | 65 | 1 |

**Casos marcados** (nada se descarta ni se adivina; salen en el reporte de la ingesta):

- `paragraph_replacement_unapplied` (Ley 5, RENAT 52): una nota dice "*Párrafo* modificado por… cuyo
  texto es el siguiente" y cita **solo el párrafo** nuevo. El parser no puede saber con certeza qué
  párrafo reemplaza; guarda el párrafo nuevo como nota editorial y deja el texto vigente de la
  disposición con el párrafo original. **El revisor debe decidir cada caso.**
- `continuation_after_quote` (RENAT 5, TUO 0-1): texto que continúa después de un bloque citado y se
  adjuntó a la disposición anterior; confirmar que pertenece ahí.
- `duplicate_unquoted_unit` (RENAT 8, TUO 1): mayormente tablas o referencias numeradas dentro de una
  disposición; se conserva la primera aparición.

Ejemplos de lo que sí quedó exacto: Ley 27181 art. 2 (r1 sustituido, r2 vigente por el DU 019-2020, con
el literal e) incorporado por la Ley 29937), art. 15 (modificado por la Ley 28172; literal g)
incorporado por el DL 1451), art. 26 (4 revisiones), art. 7 numeral 7.3 (Ley 30936).

Para revisar: `uv run drtc-ingest sample <versión> -n 20 --seed 1` imprime disposiciones al azar con su
página para comprobarlas contra el PDF.
