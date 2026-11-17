# Contexto `consultation` — Consultas (dominio principal)

**Responsabilidad:** responder preguntas con **citas verificables** o abstenerse.

Conceptos previstos (specs 005-006): `Conversation` (raíz del agregado), `Answer`, `Claim`
(regla directa / interpretación / recomendación), `Citation`, `EvidencePack`, `QueryIntent`,
`AbstentionPolicy`, `CitationValidator` (servicio de dominio) y `AudienceProfile` (personal / ciudadanía).

Regla de oro: el backend —no el modelo de IA— genera los identificadores de evidencia; ninguna cita sin
validar se muestra al usuario. Accede a la evidencia mediante su propio puerto `EvidenceRetriever`
(capa anticorrupción hacia `retrieval`).
