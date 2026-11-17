# Arquitectura de producción: plataforma de consultoría legal peruana

## 1. Decisiones del proyecto

Las decisiones definidas establecen esta base:

-   **Despliegue:** plataforma interna para un equipo, no un SaaS
    público multiempresa.
-   **Alcance legal:** normativa vigente. Se conservarán internamente
    versiones anteriores para trazabilidad y auditoría, pero las
    consultas históricas estarán fuera del alcance inicial.
-   **Modelos de IA:** proveedores externos mediante API. La integración
    estará abstraída para poder cambiar de proveedor sin rediseñar la
    aplicación.
-   **Corpus documental:** tres archivos PDF, incluido el tercer
    documento confirmado.

La recomendación es construir un **monolito modular con trabajadores
asíncronos**, PostgreSQL como base de datos principal, búsqueda híbrida
y un pipeline RAG con validación de citas.

Es una arquitectura preparada para producción sin introducir
microservicios ni una base de datos vectorial independiente antes de que
exista una necesidad real.

El sistema debe asistir al equipo en la investigación jurídica y
elaboración de documentos, pero no presentar interpretaciones generadas
como si fueran pronunciamientos jurídicos oficiales. Toda afirmación
legal relevante debe poder rastrearse hasta su fuente.

## 2. Arquitectura general

``` mermaid
flowchart TD
    U[Usuarios del equipo] --> FE[Next.js + TypeScript]
    FE --> API[FastAPI - Monolito modular]
    API --> PG[(PostgreSQL + pgvector + FTS)]
    API --> R[Redis]
    R --> W[Celery workers]
    W --> S3[(Almacenamiento compatible con S3)]
    W --> AI[APIs externas de IA]
    API --> AI
    API --> OBS[OpenTelemetry / Prometheus / Grafana]
    W --> OBS
```

### Tecnologías recomendadas

  -----------------------------------------------------------------------
  Capa                    Tecnología              Justificación
  ----------------------- ----------------------- -----------------------
  Frontend                Next.js + TypeScript    Ecosistema maduro y
                                                  buena experiencia de
                                                  usuario

  Backend                 FastAPI + Pydantic      Tipado, API y
                                                  ecosistema de
                                                  IA/documentos en Python

  Base de datos           PostgreSQL 17+          Integridad relacional,
                                                  búsqueda textual y
                                                  datos jurídicos

  Búsqueda vectorial      pgvector                Evita infraestructura
                                                  adicional inicialmente

  Tareas asíncronas       Celery + Redis          Reintentos y
                                                  procesamiento en
                                                  segundo plano

  Extracción PDF          PyMuPDF + Docling       Texto, estructura,
                                                  tablas y páginas

  OCR                     OCRmyPDF + Tesseract    Documentos escaneados

  Almacenamiento          S3 compatible           Archivos originales y
                                                  artefactos

  Despliegue              Docker Compose o Podman Operación sencilla
                          Compose

  Proxy inverso           Nginx                   TLS y enrutamiento

  Monitoreo               Prometheus + Grafana +  Métricas, trazas y
                          OpenTelemetry           operación
  -----------------------------------------------------------------------

**No empezaría con Kubernetes, microservicios ni una base vectorial
independiente.** Tres documentos y un equipo interno no justifican esa
complejidad operativa. La arquitectura debe tener interfaces bien
definidas para incorporar esos componentes posteriormente si el
crecimiento lo exige.

## 3. Estrategia de fuentes jurídicas

Esta es la decisión más importante desde el punto de vista del dominio
legal.

El sistema debe distinguir entre:

1.  **Documento fuente:** archivo PDF original, sin modificaciones.
2.  **Instrumento jurídico:** ley, decreto, reglamento o norma técnica
    representada por el documento.
3.  **Disposición normativa:** artículo, numeral, párrafo, anexo, tabla
    u otra unidad jurídica identificable.
4.  **Texto consolidado vigente:** redacción cuya aplicabilidad actual
    ha sido verificada.
5.  **Material explicativo:** manuales, comentarios y otros documentos
    que no tienen carácter normativo.

### Consideraciones sobre los documentos iniciales

-   El PDF del TUO de la Ley 27444 corresponde a una edición de 2021.
    Contiene un manual explicativo y el texto normativo del TUO. El
    manual no debe tratarse como texto legal. El propio documento
    explica que un TUO compila y ordena disposiciones, sin crear nuevas
    normas.
-   El PDF de la Ley 27181 contiene redacciones originales y
    modificadas. La extracción no debe indexarlas como si todas
    estuvieran vigentes simultáneamente.
-   Debe verificarse si existe una versión oficial posterior aplicable.
    En particular, la propuesta anterior señaló la publicación del
    Decreto Supremo N.º 006-2026-JUS como un nuevo TUO de la Ley 27444.
    Esta referencia debe comprobarse directamente en la fuente oficial
    antes de incorporarla como dato normativo vigente.

### Fuentes oficiales que deben priorizarse

-   **SPIJ:** sistema oficial del MINJUSDH para consultar legislación
    sistematizada, concordada y actualizada.
-   **El Peruano --- Normas Legales Actualizadas:** textos consolidados
    que se revisan y actualizan, con fecha de actualización indicada en
    el documento.
-   **Publicaciones oficiales del MINJUSDH:** para nuevas ediciones y
    TUO oficiales.

No reemplaces silenciosamente los PDF originales por documentos
encontrados en Internet. Almacena ambos como fuentes distintas y
registra cuál es la versión oficial cuya vigencia ha sido verificada.

## 4. Diseño de la base de datos

Utiliza PostgreSQL como sistema de registro principal. La estructura
jurídica debe ser relacional. Los vectores serán un índice adicional
para recuperación, no la base de datos jurídica.

### Tablas principales

  -----------------------------------------------------------------------
  Tabla                               Responsabilidad
  ----------------------------------- -----------------------------------
  `users`                             Cuentas e identidad de los usuarios

  `roles`, `user_roles`               Roles y permisos

  `source_documents`                  Archivos originales y procedencia

  `document_extractions`              Resultados de extracción y estado
                                      de procesamiento

  `legal_instruments`                 Leyes, decretos, reglamentos y
                                      normas técnicas

  `instrument_versions`               Versiones publicadas o consolidadas

  `provisions`                        Identidad estable de artículos y
                                      subdivisiones

  `provision_versions`                Texto exacto de cada disposición
                                      por versión

  `legal_events`                      Modificaciones, sustituciones,
                                      derogaciones y correcciones

  `provision_relations`               Referencias, excepciones,
                                      dependencias y concordancias

  `chunks`                            Fragmentos indexables con metadatos
                                      estructurales

  `chunk_embeddings`                  Representaciones vectoriales

  `consultations`                     Preguntas y respuestas generadas

  `answer_claims`                     Afirmaciones individuales de las
                                      respuestas

  `citations`                         Evidencias que respaldan las
                                      afirmaciones

  `audit_events`                      Acciones importantes de usuarios y
                                      administradores
  -----------------------------------------------------------------------

### Relaciones principales

``` mermaid
erDiagram
    SOURCE_DOCUMENTS ||--o{ DOCUMENT_EXTRACTIONS : tiene
    LEGAL_INSTRUMENTS ||--o{ INSTRUMENT_VERSIONS : tiene
    INSTRUMENT_VERSIONS ||--o{ PROVISION_VERSIONS : contiene
    PROVISIONS ||--o{ PROVISION_VERSIONS : versiona
    SOURCE_DOCUMENTS ||--o{ INSTRUMENT_VERSIONS : respalda
    PROVISION_VERSIONS ||--o{ CHUNKS : divide
    CHUNKS ||--o{ CHUNK_EMBEDDINGS : representa
    INSTRUMENT_VERSIONS ||--o{ LEGAL_EVENTS : afectada_por
    PROVISION_VERSIONS ||--o{ PROVISION_RELATIONS : relaciona
    USERS ||--o{ CONSULTATIONS : crea
    CONSULTATIONS ||--o{ ANSWER_CLAIMS : contiene
    ANSWER_CLAIMS ||--o{ CITATIONS : respaldada_por
    CHUNKS ||--o{ CITATIONS : citada_como
```

### Esquema SQL inicial

Este es un punto de partida práctico, no el conjunto completo de
migraciones:

``` sql
CREATE TABLE source_documents (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    sha256 CHAR(64) NOT NULL UNIQUE,
    mime_type TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    uploaded_by UUID NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE legal_instruments (
    id UUID PRIMARY KEY,
    instrument_type TEXT NOT NULL,
    number TEXT,
    title TEXT NOT NULL,
    issuing_authority TEXT,
    jurisdiction TEXT NOT NULL DEFAULT 'PE',
    subject_area TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE instrument_versions (
    id UUID PRIMARY KEY,
    instrument_id UUID NOT NULL REFERENCES legal_instruments(id),
    source_document_id UUID REFERENCES source_documents(id),
    publication_date DATE,
    effective_from DATE,
    effective_until DATE,
    consolidation_date DATE,
    verification_status TEXT NOT NULL,
    official_source_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE provisions (
    id UUID PRIMARY KEY,
    instrument_id UUID NOT NULL REFERENCES legal_instruments(id),
    parent_id UUID REFERENCES provisions(id),
    provision_type TEXT NOT NULL,
    provision_number TEXT NOT NULL,
    structural_path TEXT NOT NULL,
    UNIQUE (instrument_id, structural_path)
);

CREATE TABLE provision_versions (
    id UUID PRIMARY KEY,
    provision_id UUID NOT NULL REFERENCES provisions(id),
    instrument_version_id UUID NOT NULL REFERENCES instrument_versions(id),
    text TEXT NOT NULL,
    page_start INTEGER,
    page_end INTEGER,
    validity_status TEXT NOT NULL,
    UNIQUE (provision_id, instrument_version_id)
);

CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    provision_version_id UUID REFERENCES provision_versions(id),
    source_document_id UUID NOT NULL REFERENCES source_documents(id),
    content TEXT NOT NULL,
    page_start INTEGER NOT NULL,
    page_end INTEGER NOT NULL,
    chunk_type TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE consultations (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    question TEXT NOT NULL,
    answer TEXT,
    model_provider TEXT,
    model_name TEXT,
    prompt_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

La tabla `chunk_embeddings` utilizará pgvector. La dimensión dependerá
del modelo de embeddings que selecciones y pruebes. No conviene fijar
una dimensión antes de elegir el modelo.

### Reglas fundamentales del esquema

-   Mantén el PDF original inmutable y calcula su SHA-256 al subirlo.
-   Guarda por separado el número físico de página del PDF y el número
    impreso en el documento.
-   Diferencia fecha de publicación, fecha de entrada en vigor, fecha de
    consolidación y fecha de verificación.
-   Nunca sobrescribas el texto anterior de una disposición. Crea una
    nueva versión.
-   Representa las modificaciones y derogaciones parciales a nivel de
    disposición, no solamente de documento.
-   Utiliza estados explícitos como `verified_current`, `unverified`,
    `superseded`, `repealed` y `pending_review`.
-   Diferencia `unknown` de `current`. Una disposición no verificada
    nunca debe tratarse como normativa vigente verificada.

Aunque el producto inicial sea de normativa vigente, conservar
internamente las versiones anteriores es necesario para explicar la
procedencia de la información y detectar documentos desactualizados.

## 5. Pipeline de ingestión documental

La ingestión debe ser un proceso asíncrono independiente. Subir un PDF
no debe hacerlo inmediatamente disponible para consultas.

``` mermaid
flowchart TD
    A[Subir PDF] --> B[Calcular SHA-256]
    B --> C{¿Ya existe?}
    C -->|Sí| D[Devolver documento existente]
    C -->|No| E[Guardar original inmutable]
    E --> F[Extraer estructura PDF]
    F --> G{¿Calidad suficiente?}
    G -->|No| H[Procesamiento OCR]
    G -->|Sí| I[Normalizar contenido]
    H --> I
    I --> J[Identificar estructura]
    J --> K[Extraer artículos y numerales]
    K --> L[Validar metadatos jurídicos]
    L --> M[Revisión y aprobación]
    M --> N[Crear chunks]
    N --> O[Generar embeddings]
    O --> P[Indexar en PostgreSQL]
    P --> Q[Publicar versión consultable]
```

### Etapas de procesamiento

#### 5.1. Carga y procedencia

-   Aceptar inicialmente solo PDF.
-   Establecer límites de tamaño y número de páginas.
-   Calcular SHA-256.
-   Guardar el original en almacenamiento de objetos.
-   Registrar usuario, fecha, nombre y hash.
-   Detectar duplicados mediante el hash.

#### 5.2. Extracción

Utiliza PyMuPDF para extraer texto por página y coordenadas. Utiliza
Docling cuando necesites una extracción más rica de la estructura,
tablas, encabezados y orden de lectura.

Para documentos escaneados, utiliza OCRmyPDF y Tesseract. Conserva los
resultados OCR por separado del original.

#### 5.3. Análisis estructural

Identifica:

-   Título y número del instrumento.
-   Entidad emisora.
-   Fechas de publicación y vigencia, cuando estén disponibles.
-   Títulos, capítulos y secciones.
-   Artículos y numerales.
-   Anexos, tablas y notas al pie.
-   Notas de modificación y referencias a otras normas.

No asumas que todos los documentos jurídicos tienen la misma estructura.
Implementa analizadores específicos por tipo documental cuando sea
necesario.

#### 5.4. Revisión jurídica

Para los tres documentos iniciales, exigiría aprobación humana antes de
publicarlos en el corpus consultable.

El revisor debe verificar:

-   Identidad del documento y fuente.
-   Integridad del texto.
-   Vigencia de las disposiciones.
-   Identificación correcta de modificaciones y textos sustituidos.
-   Exactitud de las referencias a páginas.

#### 5.5. Indexación

Solo las versiones aprobadas estarán disponibles para recuperación. Los
documentos pendientes o con errores seguirán visibles para los
administradores, pero no podrán utilizarse en consultas normales.

## 6. Pipeline de recuperación y RAG

La calidad del producto dependerá principalmente de esta parte.

``` mermaid
flowchart TD
    A[Pregunta del usuario] --> B[Clasificación de consulta]
    B --> C[Extraer referencias legales y fechas]
    C --> D[Determinar materia y alcance]
    D --> E1[Búsqueda exacta por identificador]
    D --> E2[Búsqueda textual PostgreSQL]
    D --> E3[Búsqueda vectorial]
    E1 --> F[Combinación de candidatos]
    E2 --> F
    E3 --> F
    F --> G[Reordenamiento Cross-Encoder]
    G --> H[Expandir disposiciones relacionadas]
    H --> I[Verificar vigencia]
    I --> J[Construir paquete de evidencias]
    J --> K[Generación con LLM]
    K --> L[Validación de citas por afirmación]
    L --> M{¿Evidencia suficiente?}
    M -->|Sí| N[Respuesta con citas]
    M -->|No| O[Abstenerse o solicitar aclaración]
```

### 6.1. Clasificación de consultas

  -----------------------------------------------------------------------
  Tipo                    Ejemplo                 Estrategia
  ----------------------- ----------------------- -----------------------
  Disposición exacta      ¿Qué establece el       Búsqueda por
                          artículo 5?             identificador

  Concepto jurídico       ¿Qué es el silencio     Recuperación híbrida
                          administrativo?

  Requisitos              ¿Qué condiciones se     Recuperación de varias
                          aplican?                disposiciones

  Excepciones             ¿Existen excepciones a  Disposición y normas
                          esta regla?             relacionadas

  Comparación             ¿En qué se diferencian  Recuperar ambas
                          estos artículos?        disposiciones

  Consulta práctica       ¿Qué debemos hacer en   Evidencia + respuesta
                          este caso?              estructurada
  -----------------------------------------------------------------------

Como el alcance inicial es normativa vigente, no habilites un modo de
consulta histórica como si estuviera soportado. Si alguien pregunta por
una fecha pasada, el sistema debe explicar que el corpus actual no
permite determinar la redacción histórica aplicable.

### 6.2. Recuperación híbrida

Implementa tres mecanismos:

1.  Búsqueda exacta por número de ley, artículo, numeral u otro
    identificador.
2.  Búsqueda textual PostgreSQL mediante `tsvector` y una configuración
    apropiada para español.
3.  Búsqueda semántica mediante pgvector.

Combina los resultados con **Reciprocal Rank Fusion (RRF)** y después
aplica un modelo **Cross-Encoder** para reordenar los mejores
candidatos.

Parámetros iniciales para evaluar:

  Parámetro                          Valor inicial
  -------------------------------- ---------------
  Candidatos de búsqueda textual                30
  Candidatos vectoriales                        30
  Candidatos combinados                         30
  Pasajes después del reranking             10--15
  Evidencias finales                         5--10

Son valores iniciales para pruebas, no parámetros óptimos garantizados.

### 6.3. Fragmentación jurídica (chunking)

No utilices fragmentos de tamaño fijo arbitrario como estrategia
principal.

Es preferible:

-   Un artículo como unidad padre.
-   Cada numeral como unidad hija.
-   Fragmentos independientes para anexos y tablas.
-   Referencia al artículo padre en cada fragmento hijo.
-   Solapamiento contextual pequeño únicamente cuando sea necesario.

Ejemplo:

``` text
Instrumento: Ley N.º 27444
Artículo: 10
Numeral: 10.1
Título: Causales de nulidad
Página: 123
Texto: ...
Artículo padre: Artículo 10
Versión de la fuente: ...
```

Esto permite recuperar un numeral concreto sin perder su contexto
normativo.

### 6.4. Expansión de contexto

Las disposiciones jurídicas frecuentemente dependen de artículos
cercanos, definiciones, excepciones y referencias cruzadas.

Después de recuperar un pasaje, amplía el contexto cuando corresponda:

-   Artículo padre.
-   Otros numerales del mismo artículo.
-   Disposiciones expresamente referenciadas.
-   Definiciones relevantes.
-   Excepciones y disposiciones complementarias.

No amplíes indiscriminadamente todos los resultados. El objetivo es
proporcionar contexto jurídico suficiente sin saturar al modelo.

### 6.5. Generación de respuestas

El LLM debe recibir:

-   La pregunta del usuario.
-   Los pasajes de evidencia aprobados.
-   Identidad y versión del documento.
-   Identificadores de artículos y páginas.
-   Instrucciones explícitas para diferenciar texto normativo de
    interpretación.

Exige una respuesta estructurada, por ejemplo:

``` json
{
  "answer": "Explicación...",
  "claims": [
    {
      "text": "El requisito legal es...",
      "claim_type": "direct_rule",
      "citation_ids": ["citation-001"]
    }
  ],
  "limitations": [],
  "insufficient_evidence": false
}
```

El backend, no el LLM, debe generar los identificadores de citas y
resolverlos hacia los pasajes originales.

**Nunca permitas que el modelo invente números de artículos, páginas,
URL o citas textuales.**

### 6.6. Validación de citas

Valida cada cita contra la base de datos:

-   ¿Existe el pasaje citado?
-   ¿Pertenece a una versión documental aprobada?
-   ¿Coincide el identificador del artículo?
-   ¿La cita textual coincide con el texto almacenado?
-   ¿La fuente está marcada como vigente y verificada?
-   ¿El pasaje realmente respalda la afirmación?

Si la validación falla, elimina la afirmación no respaldada o vuelve a
generar la respuesta. Si la evidencia es insuficiente, el sistema debe
indicarlo.

### 6.7. Formato de respuesta para el usuario

Una consulta debería contener:

1.  **Conclusión:** respuesta concreta.
2.  **Fundamento jurídico:** disposiciones relevantes.
3.  **Análisis:** aplicación de las disposiciones a los hechos
    proporcionados.
4.  **Excepciones y limitaciones:** condiciones importantes.
5.  **Fuentes:** referencias navegables a la página y disposición
    exactas.
6.  **Estado de evidencia:** basado en la recuperación y validación, no
    en un porcentaje inventado por el modelo.

## 7. Arquitectura de proveedores de IA

Como has seleccionado modelos mediante API, implementa una abstracción
de proveedores en lugar de acoplar toda la aplicación a uno.

``` python
from typing import Protocol

class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...

class RerankerProvider(Protocol):
    async def rerank(self, query: str, documents: list[str]):
        ...

class GenerationProvider(Protocol):
    async def generate(self, messages: list[dict], schema: dict):
        ...
```

Separa los modelos según su función:

  -----------------------------------------------------------------------
  Tarea                               Requisito
  ----------------------------------- -----------------------------------
  Embeddings                          Buena recuperación semántica en
                                      español

  Reranking                           Cross-Encoder con buen rendimiento
                                      en español

  Generación                          Buen razonamiento, contexto amplio
                                      y salida estructurada

  Clasificación opcional              Baja latencia y bajo coste
  -----------------------------------------------------------------------

No asumas que un único modelo será el mejor para todas las tareas.
Evalúa los candidatos utilizando preguntas y pasajes jurídicos propios.
Compara calidad de recuperación, precisión de citas, latencia y coste
total.

### Seguridad de las API

-   Las claves API deben permanecer exclusivamente en el servidor.
-   No envíes documentos PDF completos al modelo de generación si no es
    necesario.
-   Envía únicamente los pasajes de evidencia seleccionados.
-   Comprueba las políticas de retención y entrenamiento de los
    proveedores.
-   Establece condiciones contractuales de tratamiento de datos cuando
    corresponda.
-   Evita incluir información personal o confidencial de expedientes si
    las políticas de tu organización y del proveedor no lo permiten.
-   Registra proveedor, modelo, versión del prompt, tokens utilizados y
    latencia, pero evita registrar innecesariamente el contenido
    sensible de las consultas.

## 8. Seguridad y operaciones

Para un despliegue interno recomiendo:

-   Autenticación OIDC mediante un proveedor de identidad existente.
    Keycloak es una alternativa razonable si necesitas administrar uno
    propio.
-   Control de acceso basado en roles: administrador, revisor jurídico y
    consultor.
-   MFA mediante el proveedor de identidad.
-   TLS en todas las comunicaciones.
-   Respaldos cifrados.
-   Acceso a PostgreSQL restringido a la aplicación y servicios
    administrativos.
-   Auditoría de aprobaciones documentales, modificaciones y consultas.
-   Límites de solicitudes y tamaños de archivos.
-   Secretos fuera del repositorio.
-   Escaneo de dependencias e imágenes de contenedores.

### Requisitos operativos

  -----------------------------------------------------------------------
  Componente                          Requisito
  ----------------------------------- -----------------------------------
  PostgreSQL                          Respaldos automáticos y
                                      recuperación a un punto en el
                                      tiempo

  Almacenamiento de objetos           Versionado y respaldo

  Redis                               Persistencia cuando las tareas en
                                      cola deban sobrevivir a reinicios

  Celery                              Política de reintentos y gestión de
                                      errores

  FastAPI                             Health checks y logs estructurados

  API de IA                           Timeouts y reintentos limitados

  Ingestión                           Idempotencia y trabajos reanudables

  Monitoreo                           Tasa de errores, latencia, cola de
                                      trabajos y coste de tokens
  -----------------------------------------------------------------------

Un error al generar embeddings no debe corromper el documento ni
publicar una versión indexada parcialmente. Utiliza una máquina de
estados para la ingestión y publica únicamente cuando todas las etapas
requeridas hayan finalizado correctamente.

## 9. Evaluación: cómo medir la precisión

No evalúes el sistema preguntando si sus respuestas parecen
convincentes. Construye un conjunto de evaluación jurídica con revisión
humana.

Empezaría con 100 preguntas y ampliaría progresivamente a 200--300.

Cada pregunta debe contener:

-   Pregunta.
-   Respuesta esperada.
-   Disposición aplicable.
-   Texto exacto de respaldo.
-   Página de origen.
-   Citas esperadas.
-   Indicador de si la pregunta puede responderse con el corpus.
-   Aprobación del revisor.

### Métricas

  -----------------------------------------------------------------------
  Métrica                             Qué evalúa
  ----------------------------------- -----------------------------------
  Recall@K                            Si se recuperó la evidencia
                                      correcta

  MRR / nDCG                          Si la evidencia relevante aparece
                                      bien posicionada

  Precisión de citas                  Si las citas respaldan realmente
                                      las afirmaciones

  Cobertura de citas                  Si se incluyen las fuentes
                                      relevantes

  Faithfulness                        Si la respuesta se mantiene dentro
                                      de la evidencia

  Corrección de respuesta             Si la conclusión jurídica es
                                      correcta

  Calidad de abstención               Si rechaza preguntas sin respaldo
                                      suficiente

  Precisión de vigencia               Si excluye disposiciones
                                      desactualizadas
  -----------------------------------------------------------------------

Puedes utilizar RAGAS y herramientas similares como diagnósticos
complementarios. No sustituyen una evaluación revisada por especialistas
jurídicos.

**Criterio de lanzamiento:** no habilitar el sistema para todo el equipo
hasta contar con un benchmark revisado y una precisión de citas
consistentemente alta. Los umbrales deben depender del riesgo del caso
de uso jurídico.

## 10. Plan de implementación

Lo construiría en siete fases:

### Fase 1 --- Inventario y validación jurídica

-   Inventariar los tres PDF.
-   Identificar instrumentos jurídicos y tipos documentales.
-   Identificar secciones desactualizadas, modificadas y explicativas.
-   Localizar versiones oficiales vigentes.
-   Definir reglas de aprobación.

### Fase 2 --- Modelo de datos e ingestión

-   Crear el esquema PostgreSQL y las migraciones.
-   Implementar almacenamiento inmutable.
-   Construir extracción PDF y OCR.
-   Implementar análisis estructural.
-   Crear el flujo de revisión y aprobación humana.

### Fase 3 --- Motor de búsqueda

-   Implementar búsqueda por artículo e identificador.
-   Añadir búsqueda textual en español.
-   Integrar embeddings y pgvector.
-   Implementar búsqueda híbrida y reranking.
-   Añadir expansión de contexto jurídico.

### Fase 4 --- RAG y citas

-   Implementar adaptadores de proveedores de modelos.
-   Crear el esquema de respuestas.
-   Implementar citas por afirmación.
-   Validar citas textuales y vigencia.
-   Añadir comportamiento de abstención.

### Fase 5 --- Aplicación para el equipo

-   Autenticación y RBAC.
-   Espacio de consultas.
-   Visor de fuentes con navegación por páginas.
-   Historial de consultas.
-   Administración documental.

### Fase 6 --- Evaluación y endurecimiento

-   Construir benchmark revisado.
-   Evaluar recuperación y calidad de citas.
-   Probar ataques de prompt injection en documentos.
-   Probar caídas y límites de los proveedores.
-   Probar restauración de respaldos.

### Fase 7 --- Despliegue de producción

-   Desplegar detrás de Nginx y TLS.
-   Configurar monitoreo y alertas.
-   Habilitar respaldos automáticos.
-   Documentar procedimientos operativos.
-   Liberar inicialmente a un grupo interno reducido.

## 11. Estrategia de escalabilidad

  -----------------------------------------------------------------------
  Crecimiento                         Cambio recomendado
  ----------------------------------- -----------------------------------
  3--100 documentos                   PostgreSQL + pgvector + FTS

  Cientos o miles                     Optimizar índices y ajustar
                                      recuperación

  Decenas de miles                    Evaluar OpenSearch para búsqueda
                                      híbrida avanzada

  Alto volumen de ingestión           Escalar trabajadores Celery
                                      independientemente

  Alto volumen de consultas           Añadir réplicas de API, caché y
                                      capacidad de lectura

  Varios equipos con datos separados  Incorporar límites explícitos entre
                                      organizaciones
  -----------------------------------------------------------------------

Mantén PostgreSQL como fuente de verdad jurídica incluso si incorporas
OpenSearch posteriormente. Los índices de búsqueda deben poder
reconstruirse a partir de los registros canónicos.

## 12. Estado de los documentos y siguiente paso

En la conversación se identificaron dos archivos disponibles:

1.  `tuo27444.pdf`
2.  `Ley-N-27181-Ley-General-de-Transporte-y-Tránsito-Terrestre.pdf`

Se confirmó que existe un tercer PDF, pero no estaba disponible para
inspeccionarlo al preparar la propuesta.

Antes de desarrollar el parser definitivo, hay que inspeccionar los tres
documentos para determinar:

-   Su estructura jurídica.
-   La autoridad emisora.
-   La fuente oficial.
-   Las modificaciones y derogaciones.
-   La presencia de anexos y tablas.
-   Los requisitos de extracción y OCR.
-   La forma correcta de representar sus disposiciones en PostgreSQL.

**Recomendación final:** primero cerrar el inventario y la validación de
fuentes; después implementar la ingestión. La calidad de un RAG jurídico
depende más de la exactitud y vigencia de su corpus que de elegir el
modelo de IA más potente.

------------------------------------------------------------------------

## Anexo A. Decisiones técnicas que deben cerrarse antes de producción

  -----------------------------------------------------------------------
  Decisión                Recomendación inicial   Criterio para cerrar
  ----------------------- ----------------------- -----------------------
  Proveedor de generación API con buen            Benchmark jurídico,
                          razonamiento y salida   privacidad, coste y
                          estructurada            latencia

  Proveedor de embeddings Modelo multilingüe con  Recall@K sobre
                          buen rendimiento en     preguntas reales
                          español

  Reranker                Cross-Encoder           nDCG y precisión de
                          compatible con español  pasajes

  Almacenamiento          S3 compatible           Durabilidad, cifrado,
                                                  versionado y coste

  Identidad               OIDC existente o        Integración con cuentas
                          Keycloak                del equipo y MFA

  Despliegue              Compose en servidor     Recursos, respaldo,
                          administrado            recuperación y
                                                  mantenimiento

  Retención de consultas  Política definida por   Confidencialidad,
                          la organización         auditoría y requisitos
                                                  legales
  -----------------------------------------------------------------------

## Anexo B. Principios que no deben negociarse

1.  Ninguna disposición no verificada se presenta como vigente.
2.  Ninguna cita se construye libremente a partir de la memoria del LLM.
3.  Toda cita debe resolver a una fuente, versión, disposición y página
    concretas.
4.  El PDF original se conserva inmutable.
5.  Toda nueva versión pasa por validación antes de publicarse.
6.  La recuperación exacta de artículos tiene prioridad sobre la
    similitud semántica cuando la pregunta identifica una disposición.
7.  El sistema debe abstenerse cuando no dispone de evidencia
    suficiente.
8.  Las respuestas deben distinguir texto normativo, interpretación y
    recomendación práctica.
9.  Los documentos se consideran datos no confiables: su contenido nunca
    debe poder cambiar las instrucciones del sistema.
10. La calidad se mide con preguntas jurídicas revisadas, no solamente
    con métricas automáticas.
