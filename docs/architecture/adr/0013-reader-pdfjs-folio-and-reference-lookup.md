# 0013. Lector: visor pdf.js (Folio), la URL como estado y búsqueda por referencia determinista

- Estado: aceptada
- Fecha: 2026-11-18
- Decisores: líder del proyecto (spec 003)

## Contexto y problema

La spec 003 entrega el primer producto utilizable: leer una norma, ver la página original del PDF con
el pasaje resaltado y encontrar una disposición escribiendo su referencia. Había que decidir cómo
mostrar el PDF (descargas de hasta 14 MB), de dónde salen las citas y el resaltado, cómo se comparte
un enlace a un pasaje y dónde vive la búsqueda por referencia.

## Opciones consideradas

**Visor del PDF**

1. `<iframe>`/visor del navegador: sin control del resaltado ni de la carga.
2. **pdf.js** (Apache-2.0), cargado bajo demanda, dibujando solo el canvas de la página y superponiendo
   rectángulos HTML con las cajas guardadas por la ingesta.
3. Convertir las páginas a imágenes en el servidor: más infraestructura y sin zoom nítido.

**Dónde se calcula el resaltado y la cita**

1. En el navegador, buscando el texto en la capa de texto de pdf.js: frágil (saltos de línea, guiones,
   textos repetidos) y la cita saldría del cliente.
2. **En el servidor**: la ingesta guarda las cajas (puntos del PDF, origen abajo-izquierda) por
   disposición y el backend redacta la cita; el navegador solo dibuja y copia.

**Estado de la vista**

1. Estado interno de la aplicación.
2. **La URL** (`/biblioteca/:norma?p=<ruta estructural>&v=<edición>`).

**Búsqueda por referencia**

1. Dentro de `legal_corpus`.
2. **Contexto propio `retrieval`**, que solo conoce `legal_corpus.api` (capa anticorrupción).

## Decisión

- **pdf.js 6** detrás del puerto `PdfLoader` (`features/reader/data-access/pdf`); el adaptador es lo
  único que importa la librería, que se carga con `import()` (chunk aparte de ~112 kB; el paquete
  inicial no cambia). El resaltado son rectángulos sobre el canvas, calculados con
  `convertToViewportPoint` a partir de las cajas del servidor.
- **Solo se descargan los rangos necesarios.** Hay que fijar **`disableStream: true` y
  `disableAutoFetch: true`** a la vez: con el streaming activo pdf.js sigue leyendo el archivo entero desde
  su primera petición aunque `disableAutoFetch` esté activo (medido: 100 % del TUO). Con ambas, abrir un
  artículo del TUO recibe ~2,4 % del archivo (SC-004 exige < 15 %). El servidor responde `206`,
  `Accept-Ranges`, `ETag` = SHA-256 y `304`.
- **El worker de pdf.js es un módulo ES (`.mjs`)**: nginx no lo conoce, lo servía como
  `application/octet-stream` y los navegadores rechazan módulos sin tipo JavaScript. La plantilla de nginx
  lo sirve como `text/javascript`, con `no-cache` + ETag (su nombre no lleva hash: una caché larga
  dejaría un worker viejo junto a una librería nueva).
- **Las citas y las cajas las entrega el backend** en la unidad de lectura; el botón "Copiar cita" copia
  tal cual el texto del servidor (principio I.2-3 de la constitución).
- **La URL es el estado**: `p` identifica la disposición por su ruta estructural (estable entre
  ediciones, legible, la que escribe el usuario) y `v` fija la edición. "Ver en el PDF" de un literal
  actualiza `p`; recargar o compartir lleva al mismo pasaje. Una navegación a otra disposición del
  mismo artículo no vuelve a pedir datos.
- **La búsqueda por referencia es determinista**: un analizador de referencias + un índice de normas
  (alias del manifiesto, la sigla más larga gana) + un resolvedor. Nunca elige por la persona (referencia
  sin norma → lista de candidatas) ni inventa (texto que no es una referencia → se explica que por ahora
  solo se busca por referencia). Vive en `retrieval`, verificado con import-linter.
- **Un resultado tardío no pisa a uno nuevo**: los stores descartan respuestas de peticiones superadas
  (contador de petición; `switchMap` en la búsqueda).

## Consecuencias

- (+) La fuente está a un clic y el pasaje se ve en su página; el texto sigue siendo legible si el PDF falla.
- (+) Cualquier vista se comparte con un enlace; la persona puede volver con el botón Atrás.
- (+) Cambiar de visor es cambiar un adaptador (`PdfLoader`).
- (−) El resaltado depende de la exactitud de las cajas de la ingesta; se mide en el navegador contra los
  PDF reales (prueba SC-002: tinta bajo cada caja frente a la misma caja desplazada).
- (−) Los anexos (tablas) se muestran como texto plano con una advertencia y solo se resalta su
  encabezado: la tabla no se estructura (spec 002, `annex_table_unstructured`).
- (−) pdf.js y su worker/fuentes/wasm se copian como assets (`/pdfjs/`); actualizarlo exige revalidar
  ese directorio y la prueba de alineación.

## Hallazgos de la implementación (para no repetirlos)

- La clase CSS `outline` choca con la utilidad `outline` de Tailwind (`outline: 1px solid`): usar
  nombres propios (`index-panel`) en los componentes.
- Angular elimina los nodos de solo espacio junto a `@if`: entre elementos `<span>` consecutivos poner
  `&ngsp;`, o el texto copiado y los lectores de pantalla leen "Art. 229Del silencio".
- El router vuelve al inicio de la página en cada navegación (`scrollPositionRestoration`); el lector
  vuelve a desplazar al pasaje elegido justo después del evento `Scroll`, en la misma tarea, para que no
  haya salto visible.
