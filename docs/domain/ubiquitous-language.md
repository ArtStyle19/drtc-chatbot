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

## Recuperación (`retrieval`)

| Término (ES) | Código (EN) | Definición |
|---|---|---|
| Fragmento | `Chunk` | Unidad indexable (artículo = padre, numeral/literal = hijo). |
| Búsqueda exacta | `ExactLookup` | Por identificador: "art. 218.2 del TUO". |
| Búsqueda textual | `LexicalSearch` | `tsvector` en español con `unaccent`. |
| Búsqueda semántica | `VectorSearch` | Embeddings en pgvector. |
| Fusión de rankings | `reciprocal_rank_fusion` | RRF: combina las listas de candidatos. |
| Expansión de contexto | `ContextExpansion` | Agregar artículo padre, numerales hermanos, definiciones, excepciones. |

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
