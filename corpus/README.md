# Corpus normativo

Documentos fuente del asistente. **Fuente de verdad:** [`manifest.yaml`](manifest.yaml).

```text
corpus/
├── manifest.yaml   documentos fuente (SHA-256, páginas, procedencia) y normas con sus versiones
└── sources/        PDF originales, INMUTABLES
```

## Reglas

1. **Nunca edite, reemplace ni renombre** un PDF de `sources/`. La suite verifica el SHA-256 de cada
   archivo (`make corpus-check`) y falla si algo cambia o si hay un PDF sin registrar.
2. Una edición nueva de una norma (p. ej. el texto oficial vigente obtenido del SPIJ) entra como:
   - un **documento fuente nuevo** en `sources/` y en `manifest.yaml` (`sources:`), y
   - una **versión nueva** del instrumento (`instruments[].versions`), al final de la lista.
3. `verification_status: verified_current` solo se usa tras contrastar el texto con la fuente oficial;
   registre en `consolidation_note` quién verificó, cuándo y contra qué fuente.
4. Marque los rangos de páginas por rol (`normative`, `explanatory`, `front_matter`, `index`,
   `back_matter`): el material explicativo nunca se cita como norma.
5. Los cambios en esta carpeta requieren aprobación del revisor jurídico en el PR.

## Agregar un documento

```bash
sha256sum corpus/sources/<archivo>.pdf      # huella para el manifiesto
pdfinfo corpus/sources/<archivo>.pdf        # número de páginas
make corpus-check                           # verifica integridad y registro
```

Detalle del contenido y del estado de vigencia de cada PDF:
[docs/domain/corpus-inventory.md](../docs/domain/corpus-inventory.md).
