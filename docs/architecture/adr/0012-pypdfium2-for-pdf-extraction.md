# 0012. pypdfium2 para la extracción de texto de los PDF

- Estado: aceptada
- Fecha: 2026-11-18

## Contexto y problema

La ingesta (spec 002) necesita el texto de cada página en orden de lectura y las cajas delimitadoras de
los caracteres (para resaltar pasajes en el visor, spec 003). La arquitectura de referencia propone
PyMuPDF, pero se distribuye bajo AGPL-3.0 (o licencia comercial): usarlo en un servicio de red de la
DRTC obligaría a publicar el código bajo AGPL o a comprar licencia.

## Opciones consideradas

1. PyMuPDF (AGPL / comercial).
2. pdfplumber / pdfminer.six (MIT): API cómoda, más lento.
3. **pypdfium2** (BSD-3 / Apache-2.0): enlace a PDFium, rápido, con texto por página y caja de cada carácter.

## Decisión

pypdfium2. Una prueba con los PDF reales mostró: orden de lectura limpio (encabezados incluidos, que cada
analizador descarta), `get_charbox` por carácter y 0,2 s para las 207 páginas normativas del TUO
(el requisito era < 1 min). El puerto `PdfTextExtractor` aísla la librería: cambiar a otra es un adaptador.
Docling y OCR siguen fuera de alcance (los tres PDF tienen capa de texto).

## Consecuencias

- (+) Licencia permisiva y extracción muy rápida.
- (−) Menos funciones de análisis de diseño que Docling/PyMuPDF; si aparecen tablas complejas
  (anexos), se evaluará un adaptador adicional.
