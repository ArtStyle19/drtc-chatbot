# Lenguaje ubicuo (glosario ES ↔ código)

La interfaz y la conversación con los especialistas usan el término en español; el código usa el
identificador en inglés. Si un término nuevo aparece en una spec, se agrega aquí en el mismo PR.

## Corpus normativo (`legal_corpus`)

| Término (ES) | Código (EN) | Definición |
|---|---|---|
| Norma, instrumento jurídico | `LegalInstrument` | Ley, decreto, reglamento, TUO u ordenanza. Raíz de agregado. |
| Tipo de norma | `InstrumentType` | `ley`, `decreto_supremo`, `texto_unico_ordenado`, … |
| Versión, edición, texto consolidado | `InstrumentVersion` | Un texto concreto de la norma en un momento dado, tomado de un documento fuente. |
| Documento fuente | `SourceDocument` / `SourceDocumentRef` | El PDF original, inmutable, identificado por su SHA-256. |
| Disposición | `Provision` | Unidad jurídica identificable: artículo, numeral, literal, inciso, párrafo, disposición complementaria, anexo. *(spec 002)* |
| Texto de una disposición en una versión | `ProvisionVersion` | El texto exacto de una disposición en una versión; nunca se sobrescribe. *(spec 002)* |
| Ruta estructural | `StructuralPath` | Ubicación de una disposición: `titulo:I/articulo:2/literal:e`. *(spec 002)* |
| Evento normativo (modificación, sustitución, incorporación, derogación) | `LegalEvent` | Cambio que una norma produce en otra. *(spec 002)* |
| Nota de modificación "(*)" | `AmendmentNote` | Nota editorial que indica qué norma modificó un texto. *(spec 002)* |
| Concordancia, remisión | `ProvisionRelation` | Relación entre disposiciones (referencia, excepción, dependencia). |
| Estado de verificación (vigencia) | `VerificationStatus` | `verified_current`, `unverified`, `pending_review`, `superseded`, `repealed`, `unknown`. |
| Vigente verificado | `VERIFIED_CURRENT` | Único estado que se puede presentar como vigente. |
| Fecha de consolidación ("actualizado al") | `consolidated_as_of` | Fecha hasta la que el texto incorpora modificaciones. |
| Revisión de una disposición | `ProvisionRevision` | Un texto de la disposición en una edición; la sustitución crea una revisión nueva y deja la anterior `superseded`. |
| Aprobación | `Approval` / `ApprovalMode` | La edición puede usarse para consultas (`human` o `auto_dev` solo en desarrollo). **No es verificación.** |
| Anomalía | `Anomaly` | Caso que el analizador no pudo interpretar con certeza; se reporta al revisor. |
| Rol de una página | `PageRole` | `normative`, `explanatory`, `front_matter`, `index`, `back_matter`. |
| Material explicativo | `PageRole.EXPLANATORY` | Manuales y comentarios: no son norma (p. ej. Manual del TUO). |
| Página física / página impresa | `pdf_page` / `printed_page_label` | Número de página del PDF vs. número impreso en el documento. |
| Sello de vigencia | `ValiditySeal` (UI) | Elemento visual que dice, con palabras, el estado de verificación. |

## Lectura (spec 003)

| Término (ES) | Código (EN) | Definición |
|---|---|---|
| Índice de una norma | `Outline` | Lista plana y ordenada de contenedores, artículos, disposiciones y anexos de una edición, con su ruta, padre y página. |
| Unidad de lectura | `ReadingUnit` | Lo que el lector muestra completo para una ruta: el artículo, la disposición, el anexo o el contenedor que la contiene. La decide el backend. |
| Contenedor | `container` (`section`/`title`/`chapter`) | Sección, título o capítulo: no tiene texto propio; se lee como la lista de lo que contiene. |
| Cita breve / cita formal | `short_citation` / `format_citation` | "Ley N.° 27181, art. 2, lit. e)" / la cita completa con edición, estado de verificación y página. **La redacta el servidor**; un texto sustituido se cita como "no vigente". |
| Historial (texto sustituido) | `history` | Textos anteriores de una disposición, siempre rotulados **no vigente**, con la norma que los sustituyó. |
| Advertencia de revisión | `ReviewFlag` | Marca por revisión que pide a una persona mirar el texto (p. ej. párrafo sustituido sin aplicar, anexo sin estructura de tabla). |
| Caja de texto | `PageBox` / `TextBox` | Rectángulo de una línea del PDF en puntos (origen abajo-izquierda), guardado por la ingesta para resaltar. |
| *Folio* | `Folio` (UI) | Panel con la página del PDF original y el pasaje resaltado como con un marcador. |
| Edición mostrada | `?v=` / `version_id` | Edición aprobada que se lee; por defecto la más reciente. |

## Recuperación (`retrieval`)

| Término (ES) | Código (EN) | Definición |
|---|---|---|
| Fragmento | `Chunk` | Unidad indexable (artículo = padre, numeral/literal = hijo). |
| Búsqueda exacta (por referencia) | `LookupReference` | Por identificador: "art. 218.2 del TUO". Determinista; si hay varias coincidencias las lista y no elige. *(spec 003)* |
| Referencia legal | `LegalReference` | Lo que la persona escribió, analizado en norma + unidad (artículo, numeral, literal, anexo, disposición, título…). |
| Alias de una norma | `aliases` | Nombres y siglas con que el personal nombra una norma (`LGTTT`, `RENAT`, `LPAG`, `TUO`); vienen del manifiesto. |
| Pasaje | `Passage` | Texto vigente de un artículo, numeral, literal, disposición o anexo de una edición aprobada: lo que se indexa y lo que la búsqueda devuelve. *(spec 004)* |
| Miga de pan y encabezado | `breadcrumb` / `lead` | Ruta legible del pasaje («Ley 27181 › Título I › Art. 2 › lit. e)») y el comienzo (≤ 300 caracteres) del texto del padre; se indexan junto al pasaje para que un literal suelto tenga contexto. |
| Brazo de búsqueda | `arm` (`reference` / `lexical` / `vector`) | Cada método que aporta resultados: referencia exacta, palabras o significado. La respuesta dice con cuál(es) se halló cada uno (`via`). |
| Búsqueda por palabras | `LexicalSearch` | PostgreSQL full-text con la configuración `spanish`; la consulta se amplía con las tildes que usa el corpus. *(spec 004)* |
| Búsqueda por significado | `VectorSearch` | Embeddings (OpenAI) en pgvector, comparados por coseno exacto (sin índice aproximado). *(spec 004)* |
| Fusión de rankings (RRF) | `reciprocal_rank_fusion` | *Reciprocal Rank Fusion*: cada pasaje suma `1/(k+posición)` por cada lista en que aparece; no mezcla puntajes de escalas distintas. |
| Búsqueda degradada | `degraded` (`vector_unavailable` / `vector_not_indexed`) | La búsqueda por significado no pudo usarse (sin clave, error, demora o vectores sin calcular): se responde igual con palabras y se avisa por qué. |
| Golden set | `golden-v1.jsonl` | Preguntas reales de trabajo con la disposición, la página y el texto de respaldo esperados, y su estado de revisión (`draft` hasta que lo apruebe el revisor jurídico). |
| Línea base de evaluación | `evaluation/baseline.json` | Métricas aceptadas de los brazos determinísticos; ninguna mejora se funde si las empeora más de la tolerancia (0,02). Cambiarla exige `--reason` y una entrada en `evaluation/CHANGELOG.md`. |
| Acierto@K / MRR | `hit@K` / `MRR` | Proporción de preguntas con la respuesta esperada entre los K primeros / media del inverso de la posición de la primera. Se miden por **disposición** (la ruta es la esperada o está debajo de ella) y por **unidad de lectura**. |
| Expansión de contexto | `ContextExpansion` | Agregar artículo padre, numerales hermanos, definiciones, excepciones. *(spec 005)* |

## Consultas (`consultation`)

| Término (ES) | Código (EN) | Definición |
|---|---|---|
| Conversación | `Conversation` | Secuencia de consultas de un actor. Raíz de agregado. |
| Consulta (pregunta + respuesta) | `Consultation` / `Turn` | Un intercambio. |
| Intención de la consulta | `QueryIntent` | Disposición exacta, concepto, requisitos, excepciones, comparación, caso práctico, fuera de alcance. |
| Paquete de evidencias | `EvidencePack` | Pasajes aprobados que recibe el modelo, con IDs generados por el backend. |
| Respuesta | `Answer` | Conclusión, fundamento jurídico, análisis, excepciones y límites, fuentes. |
| Afirmación | `Claim` | Frase verificable de la respuesta; tipo: regla directa, interpretación o recomendación práctica. |
| Cita | `Citation` | Vínculo entre una afirmación y un pasaje de evidencia validado. |
| Validación de citas | `CitationValidator` | Servicio de dominio que comprueba cada cita. |
| Abstención | `Abstention` | Respuesta explícita de que no hay respaldo suficiente. |
| Perfil de audiencia | `AudienceProfile` | Personal (técnico) o ciudadanía (lenguaje llano). |

## Identidad y organización

| Término (ES) | Código (EN) | Definición |
|---|---|---|
| Actor | `Actor` | Quién ejecuta un caso de uso (anónimo en el MVP). |
| Credenciales | `Credentials` | Token o identificador de sesión del navegador. |
| Proveedor de identidad | `IdentityProvider` | Puerto que convierte credenciales en un `Actor`. |
| OAJ, SDT, DCT, Mesa de Partes | roles (spec 007) | Oficinas de la DRTC Puno (roles del sistema existente). |
| Administrado | `citizen` | Persona que realiza un trámite ante la DRTC. |
| Expediente | `case_file` | Conjunto de documentos de un trámite (fuera del alcance del asistente). |
