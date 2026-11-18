import { NgTemplateOutlet } from '@angular/common';
import {
  afterRenderEffect,
  Component,
  computed,
  ElementRef,
  inject,
  input,
  linkedSignal,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideChevronRight } from '@lucide/angular';

import { OutlineEntry } from '../../../../core/api/models';
import { entryLabel } from '../../data-access/outline-labels';
import { OutlineNode } from '../../data-access/outline-tree';

/**
 * Table of contents of a norm. Containers (títulos, capítulos, secciones) open and close;
 * every entry is a real link (`?p=`), so it can be opened in a new tab or copied.
 */
@Component({
  selector: 'drtc-outline-tree',
  imports: [NgTemplateOutlet, RouterLink, LucideChevronRight],
  templateUrl: './outline-tree.html',
  styleUrl: './outline-tree.css',
})
export class OutlineTree {
  readonly nodes = input.required<readonly OutlineNode[]>();
  readonly instrumentId = input.required<string>();
  readonly versionId = input<string | null>(null);
  /** Path of the entry being read (marked as the current location). */
  readonly currentPath = input<string | null>(null);
  /** Containers that must be open to reveal the current entry. */
  readonly ancestors = input<readonly string[]>([]);

  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  /** Containers the person opened plus the ones that hold the current entry. */
  protected readonly open = linkedSignal<readonly string[], ReadonlySet<string>>({
    source: this.ancestors,
    computation: (ancestors, previous) => new Set([...(previous?.value ?? []), ...ancestors]),
  });

  protected readonly route = computed(() => ['/biblioteca', this.instrumentId()]);

  constructor() {
    // Keep the current entry visible inside the (scrollable) index.
    afterRenderEffect(() => {
      this.currentPath();
      this.open();
      this.host.nativeElement
        .querySelector('[aria-current="location"]')
        ?.scrollIntoView?.({ block: 'nearest' });
    });
  }

  protected labelOf(entry: OutlineEntry) {
    return entryLabel(entry);
  }

  protected params(entry: OutlineEntry): Record<string, string> {
    const version = this.versionId();
    return version ? { p: entry.path, v: version } : { p: entry.path };
  }

  protected isOpen(path: string): boolean {
    return this.open().has(path);
  }

  protected isCurrent(path: string): boolean {
    return this.currentPath() === path;
  }

  protected toggle(path: string): void {
    this.open.update((current) => {
      const next = new Set(current);
      if (!next.delete(path)) next.add(path);
      return next;
    });
  }

  protected groupId(path: string): string {
    return `grupo-${path.replace(/[^A-Za-z0-9_-]/g, '_')}`;
  }
}
