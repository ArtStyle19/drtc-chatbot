# Feature Specification: Búsqueda por contenido (híbrida), con la evaluación primero

**Feature Branch**: `004-hybrid-search`

**Created**: 2026-11-18

**Status**: Implementada y medida con Gemini (SC-003 y SC-004 cumplidos); falta comparar con OpenAI cuando haya clave válida (SC-010) y la prueba con personas (SC-011)

**Input**: "Que el personal encuentre disposiciones escribiendo lo que busca en lenguaje natural ('¿se puede
cobrar por el servicio de mototaxi?') y no solo por referencia. Combina la búsqueda exacta por
referencia (que tiene prioridad), la búsqueda por palabras y la búsqueda por significado. Antes de construir la búsqueda se
construye la evaluación: un golden set ampliado, métricas, una línea base y una compuerta de calidad.
Interfaz: página «Buscar en el texto». Sin respuestas generadas (spec 005)."

## Contexto

La spec 003 permite leer una norma y llegar a una disposición **si ya se sabe cuál es** ("art. 5 Ley
27181"). Cuando alguien tiene un caso y no sabe qué artículo aplica, hoy no tiene cómo buscar. Esta
spec agrega la búsqueda por **contenido** y, antes, la forma de **medir** si funciona bien. Es el cimiento
del asistente con respuestas citadas (spec 005): un asistente solo puede citar bien lo que la búsqueda le
trae, y la constitución (principio IV) exige que ningún cambio de recuperación se integre si empeora las
métricas del golden set. Por eso el orden del trabajo es: **evaluación → búsqueda exacta (línea base) →
por palabras → por significado → combinada**, midiendo cada paso.

Esta spec **no** genera respuestas: muestra *coincidencias* con lo buscado, con su cita y su fuente.

## Clarifications

### Session 2026-11-18 (líder del proyecto)

- Q: ¿Se usan embeddings de OpenAI y de quién es la clave? → A: Sí; la clave de API es **del líder del proyecto**
  y vive en el archivo `.env` local (nunca en el código ni en el repositorio). Cada corrida que envía texto
  a OpenAI muestra antes una estimación de tokens y costo y espera confirmación.
- Q: ¿Quién redacta las ~50 preguntas del golden set? → A: El asistente de desarrollo las redacta como
  **borradores** (lenguaje del personal, de las tres normas, todos los tipos, ~8 fuera de alcance); el líder del
  proyecto, como revisor jurídico, las aprueba después. Los borradores y las aprobadas se reportan por separado.
- Q: ¿Hay pantalla para probarlo? → A: Sí, una página **«Buscar en el texto»**, a la que llega el buscador del
  encabezado cuando el texto no es una referencia. Sin respuestas generadas.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir la calidad de la búsqueda con preguntas revisadas (Priority: P1)

Como líder del proyecto y revisor jurídico, quiero un conjunto de preguntas con su respuesta esperada y un
informe de métricas, para saber con números —no con impresiones— si un cambio en la búsqueda la mejora o
la empeora.

**Why this priority**: sin esto no se puede elegir entre variantes ni evitar regresiones (principio IV); se
construye **antes** que la búsqueda, para tener una línea base.

**Independent Test**: ejecutar la evaluación sobre el corpus cargado: produce un informe con, para cada
método, el porcentaje de preguntas cuya disposición esperada aparece entre los primeros 1, 3, 5 y 10
resultados y el rango recíproco medio, separando preguntas aprobadas y borrador; y falla si las métricas
de los métodos deterministas empeoran más que la tolerancia respecto de la línea base guardada.

**Acceptance Scenarios**:

1. **Given** el golden set, **When** reviso su contenido, **Then** hay al menos 50 preguntas de las tres normas y
   de todos los tipos (disposición exacta, concepto, requisitos, excepciones, comparación, caso práctico, fuera de
   alcance), al menos 8 de ellas **sin respuesta** en el corpus, redactadas en lenguaje del personal.
2. **Given** cada pregunta con respuesta, **Then** señala la ubicación exacta de la disposición esperada y un
   texto de respaldo que **realmente aparece** en la página citada del PDF y en esa disposición (verificado
   automáticamente); toda pregunta nueva entra como borrador.
3. **Given** el método de búsqueda exacta (que ya existe), **When** ejecuto la evaluación, **Then** obtengo su línea
   base **antes** de que exista cualquier búsqueda por contenido.
4. **Given** una línea base guardada, **When** un cambio hace que los métodos deterministas den peores resultados
   que la línea base menos la tolerancia, **Then** la verificación automática falla y dice qué preguntas
   empeoraron; cambiar la línea base exige dejar registrada la decisión.
5. **Given** que una evaluación enviaría texto a un proveedor externo, **When** la inicio, **Then** muestra la
   cantidad estimada de tokens y el costo, y **no continúa sin mi confirmación**; el costo real queda anotado.

---

### User Story 2 - Encontrar una disposición escribiendo lo que busco (Priority: P1)

Como especialista de la OAJ, quiero escribir lo que busco con mis propias palabras ("plazo para apelar una
resolución", "silencio positivo") y ver las disposiciones que mejor coinciden, para llegar al artículo que
aplica sin recorrer toda la norma.

**Why this priority**: es el valor visible del sprint y el primer paso hacia las respuestas citadas.

**Independent Test**: en la página «Buscar en el texto», escribir "plazo para interponer recurso
administrativo": el primer resultado es el numeral del TUO que fija 15 días, con su cita, página y fragmento resaltado.

**Acceptance Scenarios**:

1. **Given** un texto que no es una referencia, **When** lo escribo en el buscador del encabezado y pulso Enter,
   **Then** llego a la página «Buscar en el texto» con ese texto y sus resultados; una referencia sigue
   llevándome directo a la disposición, como en la spec 003.
2. **Given** una búsqueda, **Then** da igual si uso mayúsculas, tildes, plurales o formas del verbo
   ("sancionan", "sancionar", "sanción"), si incluyo signos de interrogación o palabras vacías, o si solo escribo
   algunas palabras de la frase.
3. **Given** resultados, **Then** cada uno muestra: la **cita breve** de la disposición, la página, el nombre de
   la norma y su edición con el **sello de vigencia**, un **fragmento resaltado** con las palabras que
   coincidieron y un enlace que abre el lector **en ese lugar exacto**.
4. **Given** que coinciden varios numerales o literales de un mismo artículo, **Then** se muestran juntos bajo ese
   artículo, indicando cuáles coincidieron, en vez de repetir el artículo muchas veces.
5. **Given** que el texto contiene una referencia además de otras palabras ("art. 5 Ley 27181 plazo"), **Then** la
   disposición referida aparece **primero**, marcada como referencia exacta, y después las coincidencias por contenido.
6. **Given** resultados de más de una norma, **Then** puedo filtrar por norma sin volver a buscar.
7. **Given** una búsqueda sin coincidencias, **Then** veo un mensaje claro con sugerencias (probar otras
   palabras, buscar por referencia) y no una pantalla en blanco.
8. **Given** cualquier resultado, **Then** la pantalla aclara que son **coincidencias con lo buscado, no una
   respuesta** ni una opinión legal; y una edición no verificada nunca se describe como vigente.

---

### User Story 3 - Encontrar por significado aunque no use las mismas palabras (Priority: P1)

Como funcionario que atiende al público, quiero que la búsqueda entienda lo que quiero decir aunque no use las
palabras de la norma ("mototaxi", "multa", "papeles del carro"), para no depender de conocer el vocabulario jurídico.

**Why this priority**: la mayoría de las preguntas reales no repiten el texto de la norma; sin esto la búsqueda
por palabras falla justo donde más hace falta.

**Independent Test**: con el golden set, la búsqueda combinada encuentra la disposición esperada en más preguntas
que la búsqueda por palabras sola, y nunca en menos preguntas que la mejor de las dos.

**Acceptance Scenarios**:

1. **Given** una pregunta cuyas palabras no aparecen en la disposición esperada, **When** busco, **Then** esa
   disposición aparece entre los primeros resultados (medido con el golden set).
2. **Given** una disposición encontrada por palabras **y** por significado, **Then** aparece mejor ubicada que
   si la hubiera encontrado solo uno de los dos métodos, y **sin duplicados**.
3. **Given** el golden set, **Then** el informe compara por separado "solo palabras", "solo significado" y
   "combinada", y compara los dos modelos de significado candidatos para elegir uno con datos.

---

### User Story 4 - La búsqueda sigue sirviendo si falla la parte de significado (Priority: P2)

Como persona que usa la herramienta, quiero que la búsqueda no se rompa si el servicio externo no responde o
aún no está configurado, para poder seguir trabajando.

**Why this priority**: la búsqueda por significado depende de un tercero; la herramienta no puede quedar inutilizable por eso.

**Independent Test**: quitar la clave de OpenAI (o simular un fallo): la búsqueda devuelve los resultados por palabras con un aviso visible.

**Acceptance Scenarios**:

1. **Given** que el servicio de significado no está disponible (sin clave, error o demora excesiva), **When**
   busco, **Then** obtengo los resultados por palabras y un aviso "La búsqueda por significado no está
   disponible; se muestran coincidencias de palabras", sin pantalla de error.
2. **Given** que escribo una búsqueda, **Then** veo un aviso de que el texto se envía a un servicio externo para
   interpretarlo y que no debo incluir datos personales; el texto de las búsquedas no se guarda ni se registra.
3. **Given** que el servicio vuelve a estar disponible, **Then** la siguiente búsqueda usa de nuevo ambos métodos
   sin intervención.

---

### User Story 5 - Entender por qué apareció un resultado (Priority: P3)

Como miembro del equipo, quiero ver, para cada resultado, qué método lo encontró y en qué posición, para
depurar la búsqueda y explicar sus resultados al revisor.

**Why this priority**: es una herramienta para el equipo; no bloquea el uso diario.

**Acceptance Scenarios**:

1. **Given** el modo de diagnóstico (apagado por defecto, disponible solo en entornos de desarrollo y prueba),
   **When** busco, **Then** cada resultado indica si lo halló la referencia exacta, las palabras o el significado,
   con su posición en cada lista y su posición final.
2. **Given** un entorno de producción, **Then** el diagnóstico no está disponible.

### Edge Cases

- Texto vacío, de solo espacios o de más de 300 caracteres: se rechaza con un mensaje claro (no se envía a ningún servicio externo).
- Un texto con datos personales (nombre, DNI, placa): la búsqueda funciona, pero nada de ese texto se guarda ni se
  escribe en registros; solo se advierte antes.
- Búsqueda en la que lo mejor es un numeral o literal: el resultado principal es su artículo, con el fragmento del
  numeral o literal que coincidió.
- Anexos de texto muy largo: se pueden encontrar, y el fragmento resaltado es el pedazo que coincidió.
- Textos **sustituidos** (historial), notas editoriales y el material explicativo del Manual del TUO: **no se
  buscan**; solo el texto vigente de ediciones aprobadas.
- Una edición aprobada que cambia (nueva ingesta): la búsqueda refleja el texto nuevo; volver a preparar el índice es seguro y
  solo recalcula lo que cambió (para no gastar de más).
- Una pregunta fuera de alcance ("impuesto a la renta"): se muestran las mejores coincidencias disponibles con el aviso de que
  son coincidencias y no una respuesta; decidir cuándo abstenerse es de la spec 005.
- Dos ediciones de una misma norma: los resultados dicen de qué edición viene cada uno.
- Resultados idénticos entre métodos: aparecen una sola vez.
- Más de una norma con la misma referencia ("art. 11"): se listan todas (como en la spec 003).

## Requirements *(mandatory)*

### Functional Requirements

**Evaluación**

- **FR-001**: El golden set DEBE tener al menos 50 preguntas de las tres normas y de todos los tipos de intención, con al menos
  8 sin respuesta en el corpus; cada una con `review_status`; las nuevas entran como `draft`.
- **FR-002**: Cada pregunta con respuesta DEBE indicar la ubicación estructural exacta de la(s) disposición(es)
  esperada(s) y un texto de respaldo; la suite DEBE verificar que ese texto aparece en la página citada del PDF y en la
  disposición ingerida de esa ubicación.
- **FR-003**: DEBE existir un comando de evaluación que, por método (exacta, palabras, significado, combinada), informe el
  porcentaje de preguntas con la disposición esperada entre los K primeros resultados (K = 1, 3, 5, 10) y el rango recíproco
  medio, a nivel de disposición exacta y de artículo, separando aprobadas y borrador, y que liste las preguntas peor resueltas.
- **FR-004**: DEBE guardarse en el repositorio una línea base de las métricas de los métodos deterministas (exacta y
  palabras); una verificación automática DEBE fallar si empeoran más que la tolerancia, y cambiar la línea base DEBE
  exigir una entrada fechada en el registro de decisiones de evaluación.
- **FR-005**: Toda corrida que envíe texto a un proveedor externo DEBE mostrar antes la cantidad estimada de tokens y el
  costo, DEBE pedir confirmación explícita y DEBE registrar proveedor, modelo, tokens y costo estimado.

**Búsqueda**

- **FR-006**: La búsqueda por palabras DEBE ignorar mayúsculas y tildes, reconocer variantes de una palabra (plural, género, forma verbal),
  ignorar palabras vacías y signos, y aceptar cualquier subconjunto de las palabras de la frase.
- **FR-007**: La búsqueda por significado DEBE encontrar disposiciones relevantes aunque la pregunta no comparta sus palabras;
  su calidad se mide con el golden set (SC-003, SC-004).
- **FR-008**: Los resultados de los métodos DEBEN fusionarse en una sola lista ordenada, sin duplicados, en la que lo hallado por
  más de un método quede mejor ubicado que lo hallado por uno solo.
- **FR-009**: Si el texto identifica una disposición por referencia, esa disposición DEBE aparecer primero y marcada como
  referencia exacta (principio I.6); una referencia ambigua lista todas las candidatas.
- **FR-010**: Las coincidencias de numerales, literales o párrafos DEBEN agruparse bajo su artículo o unidad de lectura, indicando cuáles coincidieron.
- **FR-011**: Cada resultado DEBE incluir la cita breve generada por el servidor, la página, la norma y su edición, el estado de
  verificación (con el sello), un fragmento con las palabras coincidentes resaltadas y un enlace al lector en el lugar exacto (spec 003).
- **FR-012**: Solo se DEBEN buscar los textos **vigentes** de ediciones **aprobadas**; el historial sustituido, las notas editoriales y el material
  explicativo NO se buscan.
- **FR-013**: Si el método de significado no está disponible (sin clave, error, demora excesiva), la búsqueda DEBE devolver los
  resultados por palabras e indicarlo con un aviso en la respuesta y en la pantalla.
- **FR-014**: El texto de una búsqueda DEBE limitarse (1-300 caracteres); no DEBE guardarse ni escribirse en registros; solo ese
  texto y el texto público de las normas pueden enviarse al proveedor externo; la clave NO DEBE estar en el código, las pruebas,
  los registros ni el repositorio.
- **FR-015**: La búsqueda NO DEBE generar respuestas ni afirmar que una disposición responde a la pregunta; DEBE presentar los
  resultados como coincidencias y nunca presentar como vigente una edición no verificada.
- **FR-016**: Preparar el índice DEBE ser repetible sin efectos (idempotente), solo recalcular lo que cambió y reflejar siempre las
  ediciones aprobadas.
- **FR-017**: Un modo de diagnóstico (apagado por defecto y solo en entornos de desarrollo y prueba) DEBE mostrar, por resultado,
  qué métodos lo hallaron y su posición.

**Interfaz**

- **FR-018**: El buscador del encabezado DEBE seguir resolviendo referencias como hoy y, cuando el texto no es una referencia, DEBE
  ofrecer «Buscar "…" en el texto» (Enter lleva a la página de resultados). El texto que se teclea en el encabezado se limita a 300 caracteres, igual que la búsqueda, y **no** se envía a la búsqueda por contenido ni a ningún servicio externo hasta que la persona lo confirma (Enter u opción).
- **FR-019**: La página «Buscar en el texto» DEBE tener la dirección `/buscar?q=…` (compartible), la caja de búsqueda con el texto,
  el número de resultados anunciado a lectores de pantalla, filtro por norma y estados de carga, vacío, error y "sin significado".
- **FR-020**: La interfaz DEBE cumplir WCAG 2.2 AA, ser operable con teclado y funcionar en escritorio y móvil.

### Key Entities

- **Pregunta de evaluación** (`GoldenQuestion`): pregunta, intención, si tiene respuesta, disposiciones esperadas (ubicación exacta, versión, páginas,
  texto de respaldo), estado de revisión.
- **Pasaje indexado** (`IndexedPassage`): el texto vigente de una disposición de una edición aprobada, con su ubicación, su contexto (norma,
  títulos, artículo) y la huella de su contenido; es un dato **derivado y reconstruible** del corpus.
- **Coincidencia** (`SearchHit`): una unidad de lectura (artículo, disposición, anexo) con su mejor pasaje, los pasajes que coincidieron, su
  cita, su edición y su estado de verificación, y cómo fue hallada.
- **Corrida de evaluación** (`EvaluationRun`) e **informe**: métricas por método, por tipo de pregunta y por estado de revisión; **línea base**: las
  métricas aceptadas contra las que se compara.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El golden set tiene ≥ 50 preguntas (≥ 8 sin respuesta) y el 100 % pasa las verificaciones de integridad (ubicación existente,
  texto de respaldo presente en la página y en la disposición).
- **SC-002**: La búsqueda exacta ubica la disposición esperada en el 1.er lugar en el 100 % de las preguntas cuyo texto trae una referencia explícita.
- **SC-003**: La búsqueda combinada encuentra el artículo esperado entre los 10 primeros resultados en ≥ 85 % de las preguntas con respuesta y su
  rango recíproco medio es ≥ 0,60 (umbrales provisionales: se confirman o ajustan tras la primera medición y se registra la decisión).
- **SC-004**: La búsqueda combinada nunca es peor que la mejor de las búsquedas por separado (por palabras o por significado) en el porcentaje de acierto entre los 10 primeros.
- **SC-005**: El 95 % de las búsquedas muestra resultados en menos de 2 segundos; sin el método de significado, en menos de 0,5 s.
- **SC-006**: Sin clave o con el proveedor caído, el 100 % de las búsquedas sigue devolviendo resultados por palabras con el aviso.
- **SC-007**: Una degradación deliberada de la búsqueda por palabras hace fallar la verificación automática (comprobado una vez); una ejecución normal pasa.
- **SC-008**: Cero violaciones serias o críticas de accesibilidad (axe) en la página de resultados y en los estados vacío, error y aviso; operable con teclado.
- **SC-009**: Ninguna pantalla ni respuesta de la búsqueda presenta como vigente una edición `unverified` (verificado por pruebas).
- **SC-010**: Preparar los vectores de las tres normas y evaluar los dos modelos candidatos cuesta menos de 0,50 USD en total (estimado antes y registrado después).
- **SC-011**: Una persona llega, con una pregunta en sus propias palabras, a un artículo pertinente en menos de 20 segundos sin ayuda
  (**pendiente de prueba con personas**; no la puede medir el equipo de desarrollo).

### Resultados medidos (2026-11-19)

| Criterio | Estado | Evidencia |
|---|---|---|
| SC-001 | ✅ | `golden-v1.jsonl`: 61 preguntas (52 con respuesta, 9 sin respuesta), todas `draft` hasta que las apruebe el revisor; `tests/integration/corpus/test_golden_set.py` y `tests/e2e/test_golden_set_corpus.py` verifican ruta, páginas y texto de respaldo contra el PDF y el corpus ingerido |
| SC-002 | ✅ | Brazo exacto: 6 de 6 preguntas con referencia explícita en el 1.er lugar y ninguna sin respuesta devuelve resultados (`evaluation/baseline.json`) |
| SC-003 | ✅ | `gemini-embedding-2` (2026-11-19): combinada acierto@10 por unidad **100 %**, MRR **0,907** (umbrales provisionales ≥ 85 % y ≥ 0,60: superados con holgura; **no se suben** porque el golden set es un borrador del asistente y puede favorecer al significado). Palabras solas: 67 % / 0,445 · significado solo: 100 % / 0,907. Informe `evaluation/reports/2026-11-19-lexical+vector+hybrid.md` |
| SC-004 | ✅ | Con pesos iguales **fallaba** (combinada 98 % < significado 100 %, MRR 0,792 < 0,907; informe `…-equal-weights`). Tras el ajuste de la fusión (k = 5, el significado pesa 6 veces, [informe de ajuste](../../evaluation/reports/2026-11-19-fusion-tuning.md)) la combinada **iguala** al significado en las cifras por unidad (100 % = 100 %, MRR 0,907 = 0,907), orden idéntico en las 61 preguntas |
| SC-005 | ✅ | Palabras: p50 16 ms · p95 39 ms (< 0,5 s). Con significado la llamada a Google domina: p50 531 ms · p95 933 ms (< 2 s) y el tiempo límite de la consulta interactiva es 3 s; si Google no responde, se degrada a palabras |
| SC-006 | ✅ | `test_without_a_meaning_provider_the_api_still_answers_with_words_and_says_why`, pruebas de degradación (sin clave, error, demora, vectores sin calcular) |
| SC-007 | ✅ | Comprobado una vez: degradar a propósito el brazo de palabras hace fallar `test_retrieval_baseline.py`; ejecución normal pasa |
| SC-008 | ✅ | Playwright + axe (WCAG 2.2 AA): resultados, degradado, vacío, error, sin texto, panel del encabezado y diagnóstico, escritorio y móvil; operable con teclado |
| SC-009 | ✅ | `test_nothing_is_ever_presented_as_current_while_the_editions_are_unverified` (API) y `result-card.spec.ts` (el sello solo puede volverse más cauteloso) |
| SC-010 | ◐ | Corpus completo (2.896 ventanas) y las 61 preguntas vectorizados con `gemini-embedding-2`: **US$ 0 en el plan gratuito** (cota superior de pago ≈ US$ 0,11; Google no informa los tokens, la cifra de tokens es estimada). **Falta** comparar con OpenAI (`text-embedding-3-small`/`large`): su clave fue rechazada (401); ver ADR-0014 |
| SC-011 | ⏳ | Pendiente de prueba con personas |

**Hallazgos del Sprint 3 al medir el significado** (2026-11-19): (1) el significado solo supera con claridad a las palabras en este golden set (acierto@10 100 % frente a 67 %); (2) los dos métodos son complementarios pero con **pesos iguales la combinada empeora** al método bueno, por eso el significado pesa 6 veces y k = 5; (3) con esa configuración las palabras no cambian el orden por unidad: su valor es la robustez, el resaltado y funcionar sin proveedor; (4) las 9 preguntas **sin respuesta** devuelven resultados igualmente (la búsqueda siempre devuelve algo): la **abstención** se calibra en la spec 005 con el coseno del significado (0,62-0,74 en esas preguntas), no con el puntaje fusionado; (5) Gemini, plan gratuito: 100 solicitudes/minuto y 1.000/día, una por texto: el corpus completo no cabe en un día.

**Hallazgos que cambiaron el diseño** (detalle en [research](research.md) y en los informes de `evaluation/reports/`):
`unaccent` + `spanish_stem` rompía el singular/plural de «-ción» (366 de 6.403 palabras) → configuración `spanish` +
ampliación de la consulta con las tildes del corpus; la normalización por longitud casi duplicó el MRR de palabras
(0,226 → 0,445); el analizador del corpus leía referencias cruzadas como numerales (RENAT 108.1.8 fantasma, art. 20.1 con
todo el texto sustituido) y se corrigió con pruebas contra el PDF; la comprobación de privacidad con el stack real
encontró tres fugas del texto de la búsqueda (respuestas 422, registro de acceso de `uvicorn` y de `nginx`) y se cerraron.

## Assumptions

- Hay un solo proveedor de significado (OpenAI) y dos modelos candidatos (`text-embedding-3-small` y `text-embedding-3-large`); los identificadores salen de
  la configuración y se verifican contra la lista vigente del proveedor al usar la clave por primera vez. Se elige uno con el golden set.
- El corpus sigue **sin verificar** (SPIKE-01): los resultados muestran "No verificado"; las expectativas del golden set están ligadas a una
  `version_id` y deberán revisarse cuando se carguen los textos oficiales vigentes.
- Las preguntas del golden set las redacta el asistente de desarrollo a partir de los textos reales: pueden estar sesgadas hacia el vocabulario de la norma;
  se mitiga con redacción coloquial, preguntas sin respuesta y la plantilla para que el revisor aporte preguntas reales del personal.
- El criterio de acierto es la disposición (o su artículo) **esperada**; una disposición distinta pero también pertinente cuenta como fallo, por lo que las
  métricas son conservadoras.
- Un reordenador de resultados (*reranker*) **no** se incluye; se evalúa solo si las métricas muestran una brecha que lo justifique.
- Con ~2.600 pasajes no hace falta un índice aproximado de vectores; se reevalúa cuando el corpus crezca por órdenes de magnitud.
- Sin login (ADR-0007): la búsqueda es pública dentro de la aplicación; sin historial de búsquedas.
- Solo español; sin diccionario de sinónimos propio (se evaluará con el golden set si hace falta).
- **Fuera de alcance**: respuestas generadas y abstención (spec 005), conversaciones, filtros por fecha o tipo de norma, ordenamiento por vigencia, búsqueda en el historial
  sustituido, subida de nuevos documentos.

## Dependencias

Corpus ingerido y aprobado (spec 002), lector y búsqueda por referencia (spec 003), constitución (principios I.6, IV, VI).
