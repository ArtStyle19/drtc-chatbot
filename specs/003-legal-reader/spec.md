# Feature Specification: Lector normativo (árbol, búsqueda exacta y Folio con la fuente)

**Feature Branch**: `003-legal-reader`

**Created**: 2026-11-18

**Status**: ✅ Implementada en el Sprint 2 (ver `tasks.md` y *Resultados*)

**Input**: "Que el personal pueda abrir una norma, navegar su estructura, leer un artículo con su estado de
vigencia, ver la página exacta del PDF con el pasaje resaltado, encontrar una disposición escribiendo
una referencia ('art. 5 Ley 27181') y copiar la cita en formato formal."

## Contexto

La spec 002 dejó las tres normas como disposiciones con página exacta y cajas de texto. Esta spec es el
primer producto que el personal puede **usar**: leer y ubicar partes concretas de las normas con la
fuente a un clic (objetivo 2 de la [visión](../../docs/product/vision.md)). No hay IA ni búsqueda por
significado todavía (specs 004-005).

## Clarifications

Sin sesión de aclaración con la DRTC todavía. Decisiones tomadas por defecto (cualquiera se puede
revertir sin rehacer lo demás); están marcadas en *Assumptions*. Respuestas del líder del proyecto
(2026-11-17/18) que acotan esta spec: personal primero y ciudadanía después, sin login por ahora
(ADR-0007), documentación en español y código en inglés, y "debe quedar perfecto" (se prioriza la
exactitud del resaltado y de las citas sobre la cantidad de funciones).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Navegar y leer una norma con su estado de vigencia (Priority: P1)

Como personal de la OAJ, quiero abrir una norma, recorrer su índice (títulos, capítulos, artículos,
disposiciones, anexos) y leer un artículo con sus numerales y literales, para ubicar rápido lo que dice la
norma y saber en qué medida puedo confiar en ese texto.

**Why this priority**: es el valor central de la Biblioteca; sin esto la ingesta no se puede usar.

**Independent Test**: abrir la Ley 27181, ir al art. 2 desde el índice y leerlo: se ve el texto vigente, el
sello "No verificado", la edición, y que fue sustituido por el DU 019-2020.

**Acceptance Scenarios**:

1. **Given** una norma con edición aprobada, **When** la abro desde la Biblioteca ("Leer norma"), **Then** veo su índice
   completo y colapsable y la edición con su sello de vigencia en el encabezado; el sello se repite junto
   al texto que se lee, de modo que nunca queda lejos de lo que se está leyendo.
2. **Given** el índice, **When** elijo un artículo, **Then** veo su título, su texto y sus numerales y
   literales anidados, con el número de página del PDF de cada uno, y la dirección del navegador cambia a
   un enlace que, al abrirlo, lleva exactamente a ese artículo.
3. **Given** un artículo cuyo texto fue sustituido por una norma posterior, **When** lo leo, **Then** veo
   solo el texto vigente, con la indicación "Texto sustituido por «…» (fecha)", y puedo desplegar el texto
   anterior, claramente rotulado como **no vigente**.
4. **Given** una edición no verificada, **When** leo cualquier disposición, **Then** nunca se describe como
   vigente: el sello dice con palabras "No verificado" y el aviso de la edición lo explica.
5. **Given** una disposición con un párrafo sustituido que el sistema no pudo aplicar (spec 002), **When**
   la leo, **Then** veo una advertencia visible "Este texto puede contener un párrafo ya sustituido" con la
   nota editorial que lo explica.
6. **Given** una disposición con notas editoriales (concordancias, notas `(*)`, notas al pie), **When** la
   leo, **Then** puedo desplegarlas; no se mezclan con el texto de la norma.
7. **Given** una norma sin edición aprobada, o un enlace a una disposición inexistente, **Then** veo un
   mensaje claro (no una pantalla en blanco) y un camino para volver.

---

### User Story 2 - Ver la fuente: la página del PDF con el pasaje resaltado (Priority: P1)

Como abogada, quiero ver la página original del PDF con el pasaje marcado como con un resaltador, para
comprobar que el texto que leo es el que dice el documento.

**Why this priority**: la confianza en un asistente jurídico depende de poder verificar en la fuente
(principio I.3 de la constitución).

**Independent Test**: seleccionar el art. 2 de la Ley 27181: el panel Folio muestra la página 3 con el
texto del artículo resaltado y encima del mismo texto (verificable midiendo las cajas).

**Acceptance Scenarios**:

1. **Given** una disposición seleccionada, **When** se abre el Folio, **Then** muestra la página del PDF
   donde empieza, con el pasaje resaltado, y se puede pasar a las páginas siguiente y anterior y ajustar el
   zoom; si el pasaje abarca varias páginas se indica ("pp. 4-5") y se resalta en cada una.
2. **Given** un literal dentro de un artículo, **When** lo elijo en el texto, **Then** el Folio resalta solo
   ese literal; si elijo el artículo, resalta todo el artículo.
3. **Given** el texto anterior (sustituido) de una disposición, **When** elijo "Ver en el PDF", **Then** el
   Folio resalta ese texto anterior en su página original.
4. **Given** que el PDF no se puede cargar, **Then** el texto sigue legible y el Folio muestra un error con
   "Reintentar" y un enlace para abrir el PDF en una pestaña.
5. **Given** un PDF de 14 MB, **When** abro el Folio, **Then** solo se descargan las partes necesarias para
   mostrar la página (carga por rangos), y el visor no pesa en la carga inicial de la aplicación.
6. **Given** que el PDF original está registrado con un SHA-256, **When** el servidor lo entrega, **Then**
   solo entrega archivos de ediciones aprobadas y cuyo contenido coincide con su huella.

---

### User Story 3 - Encontrar una disposición escribiendo su referencia (Priority: P1)

Como especialista de SDT, quiero escribir "art. 5 Ley 27181" o "218.2 TUO" y llegar a esa disposición, para
no recorrer el índice cuando ya sé lo que busco.

**Why this priority**: es el patrón de uso más frecuente del personal jurídico y la base de la búsqueda
exacta que usarán después las respuestas citadas (principio I.6).

**Independent Test**: escribir `art. 2 lit. e ley 27181` abre ese literal; escribir `art. 5` (sin norma)
muestra las normas que tienen artículo 5 para elegir.

**Acceptance Scenarios**:

1. **Given** referencias equivalentes (`art. 5 Ley 27181`, `artículo 5 de la LGTTT`, `Ley 27181 art 5`),
   **Then** todas resuelven a la misma disposición; se aceptan `art.`, `artículo`, `arts.`, `num.`,
   `numeral`, `lit.`, `inciso`, `inc.`, números como `4-A` y `218.2`, y siglas (`LGTTT`, `RENAT`, `LPAG`, `TUO`).
2. **Given** una referencia sin norma (`art. 11`), **Then** se muestran los resultados de cada norma que
   la tiene, con el nombre de la norma y el comienzo del texto, para elegir (nunca se elige una por el usuario).
3. **Given** una referencia bien escrita a algo que no existe (`art. 999 ley 27181`), **Then** se dice qué se
   entendió y que esa norma no tiene tal disposición en la edición cargada.
4. **Given** texto que no es una referencia (`transporte de mercancías`), **Then** se explica que no se reconoce una
   referencia pero que puede buscarse por su contenido y se dan ejemplos de referencias (la búsqueda por contenido es la
   [spec 004](../004-hybrid-search/spec.md): el buscador del encabezado ofrece «Buscar … en el texto»).
5. **Given** disposiciones, anexos, títulos y capítulos (`primera disposición complementaria final RENAT`,
   `anexo 2 RENAT`, `título IV TUO`), **Then** también se resuelven.
6. **Given** la búsqueda en el encabezado de cualquier pantalla, **Then** se puede usar con teclado
   (enfoque, flechas entre resultados, Enter, Escape) y los resultados se anuncian a lectores de pantalla.

---

### User Story 4 - Copiar la cita en formato formal (Priority: P2)

Como abogada de la OAJ, quiero copiar la cita de lo que estoy leyendo ya redactada, para pegarla en un
informe sin errores de transcripción.

**Why this priority**: ahorra tiempo y evita errores; prepara el formato de las citas de las respuestas.

**Independent Test**: en el art. 2 lit. e) de la Ley 27181, "Copiar cita" deja en el portapapeles una cita con
norma, artículo, literal, edición, estado de verificación y página.

**Acceptance Scenarios**:

1. **Given** una disposición, **When** pulso "Copiar cita", **Then** se copia la cita formal y aparece una
   confirmación visible y anunciada ("Cita copiada").
2. **Given** una edición no verificada, **Then** la cita formal lo dice (`Edición no verificada`); nunca
   afirma vigencia.
3. **Given** que existe una forma corta, **Then** también se puede copiar la cita breve (`Ley N.° 27181, art. 2, lit. e)`).
4. **Given** un texto sustituido, **Then** su cita lo indica (`texto sustituido por …; no vigente`).
5. La cita **la genera el backend** (no el navegador) a partir de los datos de la norma y de la disposición.

---

### User Story 5 - Usable en cualquier pantalla y con teclado (Priority: P3)

Como personal con distintos equipos, quiero usar el lector en pantalla grande y en el celular, y sin ratón.

**Acceptance Scenarios**:

1. **Given** pantalla ancha, **Then** índice, texto y Folio se ven a la vez; en pantalla estrecha el índice es
   un panel desplegable y Texto/Fuente se alternan con pestañas.
2. Todo es operable con teclado, con foco visible; no hay violaciones serias de accesibilidad (axe, WCAG 2.2 AA).
3. Estados de carga (esqueletos), vacío y error con reintento en el índice, el texto y el Folio.

### Edge Cases

- Artículos sin texto propio (solo numerales): se muestra el título y los numerales.
- Anexos: son una sola disposición con texto de tabla; se muestran como texto preformateado.
- Dos ediciones de la misma norma: el lector abre la más reciente aprobada y se puede fijar otra
  (`?v=`); el enlace conserva la edición. (Aún no hay un selector en la interfaz: hoy hay una edición por norma.)
- Referencias con espacios y signos irregulares (`ART.  5°  Ley N° 27181`), mayúsculas y acentos.
- Un literal que existe en varios numerales (`art. 4-A lit. a`): se listan todos, no se elige uno.
- Un PDF con la huella alterada: el servidor se niega a entregarlo (error explicado, sin detalles internos).
- Enlaces antiguos a rutas que cambian al re-ingerir: se muestra "no encontrada" con el índice.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La API DEBE entregar el **índice** de una edición aprobada: contenedores (sección, título,
  capítulo), artículos, disposiciones y anexos, con tipo, etiqueta, título, ruta, página y padre.
- **FR-002**: La API DEBE entregar la **unidad de lectura** (`GET /instruments/{id}/reading-unit?path=`): la
  disposición y su subárbol vigente (numerales y literales, en orden de documento) con texto, páginas,
  cajas, notas, advertencias, historial y cita de cada nivel; para cualquier ruta devuelve la unidad que la
  contiene (artículo, disposición, anexo o contenedor). Un contenedor devuelve además lo que contiene.
- **FR-003**: Cada disposición DEBE incluir la **cita** (breve y formal) generada por el backend; la formal
  incluye norma, ubicación, edición, estado de verificación y página, y jamás afirma vigencia sin
  `verified_current`.
- **FR-004**: Las revisiones sustituidas DEBEN estar disponibles solo como historial rotulado como no vigente
  (en la unidad de lectura, `history` de cada nivel), con su evento legal y su propia cita ("texto sustituido
  por …; no vigente").
- **FR-005**: El analizador DEBE conservar, por disposición, las **advertencias de revisión** (p. ej.
  `paragraph_replacement_unapplied`); la API las expone y el lector las muestra.
- **FR-006**: La API DEBE entregar el **PDF original** de una edición aprobada (`GET /versions/{id}/source`) con
  soporte de `Range`, tipo `application/pdf`, `ETag` y caché; DEBE verificar que el archivo coincide con
  su SHA-256 registrado y NO DEBE aceptar rutas de archivo del cliente.
- **FR-007**: La API DEBE resolver **referencias** (`GET /lookup?q=`) a disposiciones, reconociendo normas por
  número, sigla y nombre; devuelve la interpretación, el estado (`resolved`, `ambiguous`, `not_found`,
  `unrecognized`) y los resultados con su cita; nunca elige entre normas ambiguas por el usuario.
- **FR-008**: El lector DEBE mostrar índice, texto y Folio; la URL DEBE reflejar la norma, la ruta y la
  edición para poder compartirla (`/biblioteca/{norma}?p={ruta}&v={edición}`).
- **FR-009**: El Folio DEBE resaltar con las cajas guardadas el pasaje seleccionado (artículo completo o
  numeral/literal concreto), página por página, con zoom y navegación de páginas; el visor DEBE cargarse
  bajo demanda y descargar el PDF por rangos.
- **FR-010**: El lector DEBE mostrar siempre el sello de vigencia y el estado de aprobación de la edición;
  una edición no verificada nunca se presenta como vigente.
- **FR-011**: El lector DEBE mostrar las notas editoriales (desplegables) y las advertencias de revisión sin
  mezclarlas con el texto de la norma.
- **FR-012**: La interfaz DEBE cumplir WCAG 2.2 AA, ser operable con teclado y funcionar en escritorio y móvil.
- **FR-013**: Los PDF solo se entregan para ediciones **aprobadas**; las pendientes siguen invisibles (spec 002).

### Key Entities

- **Unidad de lectura** (`ReadingUnit`): la disposición que se muestra completa (artículo, disposición,
  anexo, contenedor) y que contiene la ruta pedida.
- **Esquema/Índice** (`Outline`): lista plana ordenada de contenedores, artículos, disposiciones y anexos.
- **Cita** (`Citation`): forma breve y forma formal de una disposición, generadas por el backend.
- **Referencia legal** (`LegalReference`): lo que el usuario escribió, analizado en norma + unidad.
- **Advertencia de revisión** (`review_flag`): código por revisión que señala algo que una persona debe mirar.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Desde el listado, una persona llega al texto de un artículo concreto y a su página resaltada en
  menos de 15 segundos sin ayuda, con el índice o con la búsqueda por referencia.
- **SC-002**: En una prueba con los PDF reales, el resaltado cubre el texto de la disposición: ≥ 95 % del
  área de cada caja resaltada coincide con texto de la página (medido en el navegador).
- **SC-003**: Las 10 preguntas del golden set se resuelven con la búsqueda por referencia cuando traen una
  referencia explícita, y el Folio muestra su página citada.
- **SC-004**: El visor de PDF no aumenta el paquete inicial de la aplicación (carga diferida) y abrir una página
  del TUO (14 MB) descarga menos del 15 % del archivo.
- **SC-005**: Cero violaciones serias o críticas de accesibilidad (axe) en el índice, la lectura, la búsqueda
  y el Folio; todo operable con teclado.
- **SC-006**: Ninguna pantalla presenta como vigente una edición `unverified` (verificado por pruebas).

## Assumptions

- **No hay enlaces automáticos entre disposiciones** (p. ej. "véase el artículo 38"): una referencia sin
  norma explícita puede apuntar a otra norma ("artículo 5 de la Ley 26842") y enlazarla a la nuestra sería un
  error jurídico. Queda en el backlog hasta tener un resolvedor de referencias entre normas con revisión.
- Las notas editoriales (spec 002, FR-007) ahora se muestran, desplegadas bajo demanda.
- Sin login (ADR-0007): cualquier persona con acceso a la aplicación lee todo lo aprobado.
- La búsqueda es solo por referencia exacta; la búsqueda por texto/significado es la spec 004.
- La edición mostrada por defecto es la aprobada más reciente de la norma.
- Fuera de alcance: edición de textos, anotaciones personales, impresión/exportación a PDF, comparar ediciones.
- **Limitaciones conocidas** (decididas, no olvidadas):
  - El historial de una disposición que ya no existe en el texto vigente (derogada del todo) no aparece en
    la lectura: la unidad de lectura muestra solo disposiciones con texto vigente.
  - En un **anexo** el texto se muestra como bloque plano con advertencia y el Folio resalta solo su
    encabezado, porque la ingesta no estructura tablas (spec 002; sin OCR ni extractor de tablas sin spec).
  - Los títulos en mayúsculas se muestran en minúscula de oración, pero **sin añadir tildes** que el PDF no
    traiga ("Ambito de aplicacion"): la fidelidad a la fuente va antes que la ortografía.
  - Las referencias del tipo "artículo 5 del Título II" se resuelven pasando por el título que contiene al
    artículo; las que cruzan normas no se enlazan.

## Resultados (Sprint 2)

| Criterio | Resultado | Cómo se midió |
|---|---|---|
| SC-001 (< 15 s) | **Pendiente de prueba con personas** | Requiere a quien use la herramienta; el flujo existe (índice o búsqueda → texto + página resaltada) |
| SC-002 (resaltado sobre el texto) | ✅ | Playwright contra la API real: bajo cada caja del literal e) del art. 2 hay tinta y no más que bajo la misma caja desplazada ±0,7 líneas (4 de 5 líneas con desplazamiento óptimo 0-1 px) |
| SC-003 (golden set) | ✅ 100 % de las citas con referencia | `test_every_golden_citation_with_a_reference_is_resolved_to_its_cited_page` |
| SC-004 (carga diferida y < 15 %) | ✅ paquete inicial 94,8 kB (sin pdf.js, que son 112 kB aparte); abrir el art. 229 del TUO recibe ≈ 2,4 % del PDF | Playwright con CDP (`Network.dataReceived`) |
| SC-005 (axe y teclado) | ✅ 0 violaciones serias o críticas | Playwright + axe (WCAG 2.2 AA) en lectura, historial, título, portada, búsqueda abierta y móvil (ambos paneles) |
| SC-006 (nunca "vigente") | ✅ | Pruebas de unidad y e2e: el sello dice "No verificado" junto al texto, en la cita y en la búsqueda |

Pruebas: 375 backend (96 % de cobertura), 146 de unidad del frontend, 27 e2e con API simulada y 26 contra la
API real. Hallazgos corregidos durante la verificación: ver [ADR-0013](../../docs/architecture/adr/0013-reader-pdfjs-folio-and-reference-lookup.md#hallazgos-de-la-implementación-para-no-repetirlos).
