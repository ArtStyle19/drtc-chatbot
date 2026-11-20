import { Component, input } from '@angular/core';

import { SearchSegment } from '../../../../core/api/models';

/**
 * A fragment of legal text with the words that matched the search marked. It is built from the
 * server's segments with text interpolation only: no `innerHTML`, so a norm that contains `<` or
 * `&` is shown as written and nothing in the text can ever run.
 */
@Component({
  selector: 'drtc-snippet',
  template: `@for (segment of segments(); track $index) {
    @if (segment.match) {
      <mark>{{ segment.text }}</mark>
    } @else {
      <span>{{ segment.text }}</span>
    }
  }`,
  styles: `
    :host {
      font-family: var(--font-serif);
      overflow-wrap: anywhere;
    }

    /* Matches are NOT the yellow marker: that colour is reserved for passages cited in the reader. */
    mark {
      padding: 0 0.1em;
      border-radius: 2px;
      background: var(--color-ink-100);
      color: var(--color-ink-900);
      font-weight: 700;
    }
  `,
})
export class Snippet {
  readonly segments = input.required<readonly SearchSegment[]>();
}
