# Frontend: estructura estándar de Angular

Angular 22 con componentes standalone, signals, detección de cambios sin zone.js (zoneless) y
OnPush por defecto. Estilos con Tailwind v4 y tokens propios. Pruebas con Vitest y Playwright.

## Estructura

```text
frontend/src/
├── main.ts               carga /config.json y arranca la app
├── styles.css            tokens de diseño (@theme) y estilos base
└── app/
    ├── app.ts · app.config.ts · app.routes.ts    rutas de features con carga diferida
    ├── core/             servicios únicos y transversales
    │   ├── api/          schema.d.ts (generado del OpenAPI) + models.ts (alias)
    │   ├── config/       configuración en tiempo de ejecución (RUNTIME_CONFIG)
    │   ├── http/         interceptores (base URL, X-Session-Id), problem details
    │   └── session/      identificador anónimo del navegador
    ├── layout/           marco de la aplicación (cabecera, navegación, avisos), 404
    ├── shared/ui/        componentes de diseño reutilizables (ValiditySeal, …)
    ├── features/
    │   ├── library/      Biblioteca normativa
    │   │   ├── data-access/   LibraryApi + LibraryStore (NgRx SignalStore)
    │   │   ├── feature/       LibraryPage (contenedor, provee el store)
    │   │   └── ui/            InstrumentCard (presentacional; enlace "Leer norma")
    │   ├── reader/       Lector normativo (spec 003): índice, texto y Folio
    │   │   ├── data-access/   ReaderApi + ReaderStore · funciones puras (outline-tree, reading-tree,
    │   │   │                  outline-labels, provision-labels) · pdf/ (puerto PdfLoader + adaptador pdf.js)
    │   │   ├── feature/       ReaderPage (URL → store, foco, scroll, título del documento)
    │   │   └── ui/            OutlineTree · ContainerView · EditionHeader · ProvisionNode (recursivo)
    │   │                      · CiteButton · Folio
    │   ├── lookup/       Búsqueda por referencia (spec 003)
    │   ├── search/       «Buscar en el texto»: búsqueda por contenido (spec 004)
    │   │   ├── data-access/   LookupApi + LookupStore (debounce, cancela la petición anterior)
    │   │   └── feature/       ReferenceSearch (combobox, vive en el encabezado de la aplicación)
    │   └── chat/         Consultas (spec 005; hoy marcador de posición)
    ├── shared/util/      instrument-labels (referencia de una norma, texto de la aprobación)
    └── testing/          fixtures y dobles (reader-fixtures, FakePdfLoader)
```

## Reglas

1. **Features autocontenidas:** una feature solo importa de `core`, `shared` y de sí misma. Así se
   puede trasladar al sistema DRTC existente (también Angular) si se decide integrarlo.
2. **Tres tipos de carpeta por feature:**
   - `data-access/`: comunicación con la API y estado (SignalStore). Sin plantillas.
   - `feature/`: componentes de página que conectan el store con la interfaz.
   - `ui/`: componentes presentacionales con `input()`/`output()`; sin servicios ni estado global.
3. **Estado:** signals locales en componentes; SignalStore por feature, provisto por la página.
4. **Contrato:** los tipos de la API se generan con `npm run api:types` (o `make openapi`); nunca se
   escriben a mano.
5. **Servicios únicos:** `@Service()` (Angular 22) con `inject()`.
6. **SSR-safe:** sin acceso directo a `window`/`localStorage` fuera de `isPlatformBrowser`.
7. **Accesibilidad:** WCAG 2.2 AA; `ng lint` incluye reglas de accesibilidad de plantillas y la
   suite e2e corre axe.
8. **Idioma y formato:** `LOCALE_ID = es-PE`; textos en español en las plantillas.
9. **Fuentes autoalojadas** (`@fontsource/*`): sin llamadas a Google Fonts.

## El lector (spec 003)

[ADR-0013](adr/0013-reader-pdfjs-folio-and-reference-lookup.md) explica las decisiones; aquí, cómo está armado.

- **La URL es el estado:** `/biblioteca/:norma?p=<ruta estructural>&v=<edición>`, enlazada a los
  `input()` de `ReaderPage` (`withComponentInputBinding`). Un efecto llama a `store.open(norma, v)` y
  `store.focus(p)` **por separado**: una respuesta lenta del índice no retrasa ni pisa la elección.
- **`ReaderStore`** (SignalStore por página): índice, unidad de lectura, ruta enfocada e historial visible.
  Cada carga lleva un contador; una respuesta superada se descarta. Si `p` cae dentro de la unidad ya
  cargada (un literal del mismo artículo) no hay petición nueva.
- **Funciones puras y probadas** para lo que no es de Angular: anidar el índice por `parent_path`, anidar
  los nodos de lectura, calcular el pasaje del Folio (un numeral incluye sus literales; el historial
  apunta a su propia página y cajas), vecinos anterior/siguiente.
- **`ProvisionNode`** es recursivo y presentacional: recibe el nodo y la ruta enfocada y emite
  `viewPassage` / `showHistory`. Nunca compone una cita: el botón copia la que escribió el servidor
  (`CiteButton`, CDK `Clipboard` + `LiveAnnouncer`; avisa si no pudo copiar).
- **`Folio`** habla con el puerto `PdfLoader`, no con pdf.js: así las pruebas de unidad usan un doble
  (`FakePdfLoader`) y el adaptador (`PdfJsLoader`) es lo único que carga la librería, con `import()`.
  Dibuja el canvas (una página a la vez, cola de renders, cancelable con `AbortSignal`) y superpone
  rectángulos HTML calculados con las cajas del servidor. El `viewport` es una región con foco y etiqueta
  (axe exige poder desplazarla con teclado).
- **La URL del PDF no pasa por `HttpClient`**, así que no la alcanza el interceptor: `resolveApiUrl` le
  antepone `apiBaseUrl` cuando hace falta (`core/http/api-url.ts`).
- **Pantallas pequeñas:** un solo conjunto de componentes. Por debajo de 1024 px se muestra un panel a la
  vez (alternador Texto/PDF) y el índice es un panel desplegable que se cierra al elegir; desde 1024 px, tres
  columnas con índice y Folio fijos (`position: sticky`).
- **Foco y desplazamiento:** al cambiar de disposición el foco pasa al encabezado de la lectura (no en la
  primera carga). El router vuelve arriba en cada navegación; la página vuelve a desplazar al literal
  elegido justo después del evento `Scroll`, así no hay salto visible. En una sola columna, el encabezado de
  la disposición se lleva al borde superior de la pantalla.
- **Título del documento:** lo fija la página ("Artículo 2 · Ley 27181 (LGTTT) · DRTC Puno"); la ruta no
  declara `title` para que el `TitleStrategy` no lo pise.

### Búsqueda por referencia

`ReferenceSearch` implementa el patrón *combobox* de ARIA 1.2: el foco se queda en el campo; las flechas
mueven `aria-activedescendant` por un `listbox`; Enter abre el resultado activo (o busca de inmediato y
abre si el resultado es único); Escape cierra y, una segunda vez, borra; `/` enfoca el campo desde
cualquier parte. La región `role="status"` siempre está en el DOM para que el anuncio llegue a los
lectores de pantalla. Una referencia ambigua **lista** las candidatas y no abre ninguna.

**Camino hacia la búsqueda por contenido (spec 004).** La última opción del panel es siempre
«Buscar "…" en el texto» (se alcanza con ↓, o con clic): lleva a `/buscar?q=`. Enter sobre un texto que
no es una referencia (`unrecognized`) también va allí. **Escribir solo consulta `/lookup`** (local y
gratuito): `/search`, que puede llegar a un servicio externo de embeddings, se llama únicamente cuando la
persona decide; una prueba lo verifica.

## Buscar en el texto (spec 004)

`features/search/{data-access, feature, ui}`:

- **La URL es la única fuente de verdad** (`/buscar?q=&norma=&debug=`): enviar el formulario cambia la URL
  y la URL dispara la búsqueda, así se puede compartir, recargar y volver atrás. Un texto nuevo borra el
  filtro de norma.
- `SearchStore` (SignalStore) usa `switchMap`: la petición en curso se cancela al llegar otra, así una
  respuesta lenta **nunca** pisa a una nueva. Si solo cambia el filtro de norma, la lista anterior se
  queda en pantalla atenuada en vez de parpadear con un esqueleto.
- `ResultCard` muestra lo **hallado**, no una conclusión: cita redactada por el servidor, norma, título,
  páginas, las palabras coincidentes marcadas, el `ValiditySeal`, cómo se encontró (en palabras, no solo
  color), los otros pasajes de la unidad en un `<details>` y «Leer en la norma» (al pasaje exacto y a la
  edición de la que vino). El sello **solo puede volverse más cauteloso** que lo que dijo el servidor
  (`sealStatus`): «verificado» sin `may_be_presented_as_current` se muestra como no verificado.
- `Snippet` pinta los segmentos `{text, match}` con interpolación (`<mark>` para las coincidencias): **nunca
  `innerHTML`**, así el texto de una norma no puede convertirse en elementos.
- Estados: esqueleto en la primera carga, vacío (con sugerencias y salida del filtro), error con
  «Reintentar» (mensaje para personas, nunca el detalle técnico), aviso **degradado** (`role="note"`) si no hay
  búsqueda por significado, y la nota «se entendió "art. 5" como una referencia exacta».
- Los botones de filtro por norma muestran solo el nombre: las facetas cuentan unidades entre los mejores
  candidatos, y un número que no coincide con la lista filtrada confundiría.
- El panel de diagnóstico (qué método halló cada resultado y su posición) solo existe en compilaciones de
  desarrollo (`isDevMode()`) y el servidor lo ignora fuera de local/test.

### Reglas de plantilla aprendidas

- Entre elementos `<span>` contiguos usar `&ngsp;` (Angular elimina los nodos de solo espacio junto a
  `@if`): sin él el texto extraído y los lectores leen "Art. 229Del silencio".
- No llamar `outline` a una clase propia: choca con la utilidad de Tailwind (`outline: 1px solid`).
- Una etiqueta accesible debe contener el texto visible (axe `label-content-name-mismatch`): el botón de
  zoom dice "100 %, restablecer el zoom".
- El presupuesto de estilo por componente es de 6 kB (aviso) / 8 kB (error).

## Configuración por entorno

`public/config.json` se lee al arrancar (`apiBaseUrl`). La misma build sirve para cualquier entorno:
en desarrollo el proxy de `ng serve` (`proxy.conf.json`) y en contenedores nginx redirigen `/api` al
backend, por lo que `apiBaseUrl` queda vacío (mismo origen).

**nginx** (`nginx.conf.template`) sirve además lo que necesita el visor: gzip para JSON (el índice del TUO
baja de 65 kB a ~12 kB), el worker de pdf.js (`.mjs`) como `text/javascript` y sin caché larga, y
reenvía `Range`, `ETag` y `If-None-Match` al backend sin tocarlos (el PDF no se comprime ni se almacena en
búfer). Verificado con la compilación de producción tras el nginx real (`206`, `304`, worker como Web Worker).

## Pruebas

| Tipo | Herramienta | Ejemplo |
|---|---|---|
| Unitarias de componentes y stores | Vitest + TestBed | `validity-seal.spec.ts`, `reader.store.spec.ts`, `folio.spec.ts` (con `FakePdfLoader`), `reference-search.spec.ts`, `search.store.spec.ts`, `result-card.spec.ts`, `snippet.spec.ts`, `search-page.spec.ts` (con el router real) y `privacy.spec.ts` (escribir nunca llama a `/search`) |
| E2E de la búsqueda | Playwright + axe | `e2e/search.spec.ts`: respuestas capturadas de la API real (`e2e/fixtures/search.ts`), WCAG 2.2 AA en resultados, vacío, error, degradado y sin texto, en escritorio y móvil; bloque «Contra el backend real» |
| End-to-end + accesibilidad | Playwright + axe | `e2e/library.spec.ts`, `e2e/reader.spec.ts` (API simulada con respuestas capturadas de la real, en `e2e/fixtures/reader.ts`; `E2E_REAL_API=1` para la real) |
| Contra el backend real | Playwright (`E2E_REAL_API=1`) | SC-002: alineación del resaltado midiendo la tinta del canvas bajo cada caja; SC-004: bytes realmente recibidos del TUO por CDP (`Network.dataReceived`); numeral del TUO y anexo del RENAT |
