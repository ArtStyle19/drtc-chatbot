# Dirección de diseño: "Mesa de estudio"

## Para quién y para qué

**Quién:** una abogada de la OAJ o un especialista de SDT a media mañana, con un expediente abierto,
que necesita saber qué artículo sustenta una decisión.
**Qué debe lograr:** encontrar la regla, comprobarla en la fuente y copiar una cita correcta.
**Sensación:** la calma de una sala de lectura y la precisión del diario oficial. Seria, confiable,
sin adornos.

## Dominio y mundo de color

- **Conceptos:** diario oficial *El Peruano*, folio, sello, expediente, resaltador, artículo / numeral
  / literal, vigencia, concordancia.
- **Colores que existen en ese mundo:** tinta azul institucional (DRTC `#092475`), papel de diario
  (canvas `#f6f4ee`), blanco del folio, amarillo resaltador (`#ffe58a`) para pasajes citados,
  dorado del sello oficial (`#d3a62a`), sepia/ámbar de los textos no verificados, rojo de derogado.

## Firma (elemento propio de este producto)

1. **Sello de vigencia** (`ValiditySeal`): insignia con doble borde, como la impresión de un sello de
   goma, que dice con palabras el estado del texto: *Vigente verificado*, *No verificado*,
   *En revisión*, *Sustituido*, *Derogado*. Aparece en tarjetas de normas, citas y el visor.
2. **Citas como referencias jurídicas** (spec 005): chips legibles por sí solos
   ("Ley 27181 · art. 2 lit. e · p. 4") con **Copiar cita** en formato formal para informes.
3. **Folio** (spec 003, ✅): panel lateral con la página exacta del PDF y el pasaje resaltado como con
   un resaltador. Hoy se sincroniza con la disposición que se lee; con la spec 005 lo hará con la
   conversación.

## Defaults que rechazamos

| Default | Lo que hacemos en su lugar |
|---|---|
| Clon de ChatGPT (burbujas, columna centrada) | *Mesa de estudio*: conversación + Folio en vista dividida; respuestas como tarjeta de dictamen (Conclusión, Fundamento jurídico, Análisis, Excepciones, Fuentes) |
| Notas numéricas [1] [2] | Chips con la referencia jurídica completa |
| "Confianza: 87 %" inventada por el modelo | Estado de evidencia calculado por la validación ("3 disposiciones · 0 verificadas") |
| Paleta SaaS azul genérica, sans en todo | Tinta DRTC + papel + resaltador; serif (Libre Baskerville) para títulos y textos legales |

## Sistema

- **Tipografía:** Source Sans 3 (interfaz), Libre Baskerville (títulos y texto normativo),
  IBM Plex Mono (identificadores: "Decreto Supremo N.° 017-2009-MTC").
- **Profundidad:** solo bordes de baja opacidad (`--color-rule*`) y cambios sutiles de superficie;
  sin sombras dramáticas.
- **Espaciado:** base 4 px (escala de Tailwind). **Radios:** 4 / 6 / 10 px.
- **Contraste:** todos los pares texto/fondo verificados ≥ 4,5:1 (WCAG AA).
- **Movimiento:** transiciones de 120 ms con desaceleración; se respetan `prefers-reduced-motion`.
- **Estados:** carga (esqueletos), vacío, error con reintento; foco visible siempre.
- **Responsive:** escritorio primero para el personal; en móvil el Folio será una hoja inferior.

Tokens en `frontend/src/styles.css`; resumen para futuras sesiones en `.interface-design/system.md`.
