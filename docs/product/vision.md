# Visión del producto

## Problema

El personal de la DRTC Puno (OAJ, SDT, DCT, Mesa de Partes, Dirección) resuelve a diario casos de
transporte que exigen ubicar con precisión qué dice la norma aplicable: plazos del procedimiento
administrativo, requisitos de habilitación, competencias del gobierno regional, recursos
administrativos. Hoy eso implica buscar a mano en PDF de cientos de páginas, con ediciones de
vigencia incierta y textos originales mezclados con textos modificados.

## Propuesta

Un asistente que **responde con citas verificables** (norma, versión, disposición y página), permite
**leer la fuente exacta** con un clic y **se abstiene** cuando no hay respaldo suficiente. Nunca
presenta como vigente un texto no verificado.

## Objetivos (12 meses)

1. Reducir el tiempo de ubicar el fundamento normativo de un caso de minutos a segundos.
2. Que el 100 % de las afirmaciones jurídicas mostradas estén respaldadas por una cita validada.
3. Que el personal confíe en la herramienta porque puede comprobar cada respuesta en la fuente.
4. Preparar una versión para la ciudadanía (lenguaje claro, acceso público controlado).

## No-objetivos

- No reemplaza la opinión legal de la OAJ ni emite pronunciamientos oficiales.
- No gestiona expedientes ni trámites (eso lo hace el sistema de Habilitación Vehicular existente).
- No responde preguntas fuera del corpus cargado (se abstiene y lo explica).
- No ofrece consultas históricas ("¿qué decía en 2015?") en el alcance inicial.

## Métricas de éxito

| Métrica | Meta inicial | Fuente |
|---|---|---|
| Precisión de citas (golden set) | ≥ 95 % | `evaluation/` (spec 004-005) |
| Recall@10 de la recuperación | ≥ 90 % | `evaluation/` |
| Abstención correcta en preguntas sin respaldo | ≥ 90 % | `evaluation/` |
| Latencia p95 de una respuesta citada | ≤ 15 s | métricas del backend |
| Satisfacción del personal (👍 / total) | ≥ 80 % | feedback (spec 006) |

## Criterio de lanzamiento

No se habilita para todo el personal sin un golden set revisado por un abogado y una precisión de
citas consistentemente alta (arquitectura de referencia, §9).
