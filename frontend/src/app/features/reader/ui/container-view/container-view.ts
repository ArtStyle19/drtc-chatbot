import { Component, computed, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { OutlineEntry } from '../../../../core/api/models';
import { entryLabel } from '../../data-access/outline-labels';

/** Reading view of a título, capítulo or sección: it has no text, so it lists what it contains. */
@Component({
  selector: 'drtc-container-view',
  imports: [RouterLink],
  templateUrl: './container-view.html',
  styleUrl: './container-view.css',
})
export class ContainerView {
  readonly children = input.required<readonly OutlineEntry[]>();
  readonly instrumentId = input.required<string>();
  readonly versionId = input<string | null>(null);

  protected readonly route = computed(() => ['/biblioteca', this.instrumentId()]);
  protected readonly items = computed(() =>
    this.children().map((entry) => ({ entry, label: entryLabel(entry) })),
  );

  protected params(entry: OutlineEntry): Record<string, string> {
    const version = this.versionId();
    return version ? { p: entry.path, v: version } : { p: entry.path };
  }
}
