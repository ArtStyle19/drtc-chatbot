# Reglas del corpus normativo

Estas reglas son de negocio, no técnicas. Se implementan en el dominio (`legal_corpus`,
`consultation`) y se prueban con tests marcados con su requisito.

## 1. Distinciones fundamentales

1. **Documento fuente:** el PDF original, sin modificaciones (SHA-256).
2. **Instrumento jurídico (norma):** la ley, decreto, reglamento o TUO que el documento representa.
3. **Disposición:** artículo, numeral, literal, inciso, párrafo, disposición complementaria, anexo o tabla.
4. **Texto consolidado vigente:** redacción cuya aplicabilidad actual fue **verificada**.
5. **Material explicativo:** manuales y comentarios; **no tienen carácter normativo**.

## 2. Estados de verificación

| Estado | Significado | ¿Se presenta como vigente? |
|---|---|---|
| `verified_current` | Contrastado con fuente oficial; se registra quién, cuándo y contra qué fuente | **Sí** |
| `unverified` | Aún no contrastado (estado de los tres PDF iniciales) | No |
| `pending_review` | En revisión jurídica | No |
| `superseded` | Reemplazado por un texto posterior | No (se muestra como sustituido) |
| `repealed` | Derogado | No (se muestra como derogado) |
| `unknown` | Sin información | No — `unknown` nunca equivale a vigente |

## 3. Versiones

- Nunca se sobrescribe el texto anterior de una disposición: se crea una versión nueva.
- Las modificaciones y derogaciones parciales se representan a nivel de disposición.
- Se distinguen fecha de publicación, fecha de entrada en vigor, fecha de consolidación
  ("actualizado al") y fecha de verificación.
- Un TUO puede renumerar artículos (p. ej. el DS 006-2026-JUS frente al DS 004-2019-JUS): la
  identidad de una disposición entre versiones se registra explícitamente, nunca se infiere solo por
  su número.

## 4. Páginas

- Se guarda la página física del PDF y, por separado, la página impresa cuando exista.
- Toda cita apunta a una página física verificable del documento fuente.

## 5. Citas

- El backend genera los identificadores de evidencia; el modelo de IA solo puede referenciarlos.
- Una cita es válida si: existe el pasaje, pertenece a una versión aprobada, la disposición coincide,
  la cita textual coincide con el texto almacenado y el estado de verificación se informa.
- Si la validación falla, la afirmación se elimina o la respuesta se regenera; si no queda respaldo,
  el sistema se abstiene.

## 6. Textos con notas "(*)"

Las compilaciones tipo SPIJ intercalan el texto original, la nota de modificación y el texto nuevo.
La ingesta debe marcar el texto sustituido como `superseded` y el nuevo como el texto de la versión,
con el `LegalEvent` correspondiente; nunca se indexan ambos como si estuvieran vigentes a la vez.
