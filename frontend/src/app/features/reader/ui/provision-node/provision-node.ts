import { DatePipe } from '@angular/common';
import { Component, computed, input, output } from '@angular/core';
import { LucideTriangleExclamationPoint } from '@lucide/angular';

import { LegalEvent, ReadingRevision } from '../../../../core/api/models';
import { eventVerb, nodeLocator, noteKindLabel } from '../../data-access/provision-labels';
import { ReadingTreeNode } from '../../data-access/reading-tree';
import { CiteButton } from '../cite-button/cite-button';

export interface HistorySelection {
  readonly path: string;
  readonly revision: number;
}

/**
 * One provision of the reading view and, recursively, everything below it. Presentational: it
 * knows nothing about HTTP or the store; the page tells it what is focused and listens to events.
 */
@Component({
  selector: 'drtc-provision-node',
  imports: [CiteButton, DatePipe, LucideTriangleExclamationPoint],
  templateUrl: './provision-node.html',
  styleUrl: './provision-node.css',
  host: {
    '[attr.data-kind]': 'node().kind',
    '[class.is-focused]': 'isFocused()',
    '[class.in-focus]': 'isWithinFocus()',
    '[class.is-root]': 'depth() === 0',
    '[attr.id]': 'anchor()',
  },
})
export class ProvisionNode {
  readonly tree = input.required<ReadingTreeNode>();
  readonly depth = input(0);
  readonly focusPath = input<string | null>(null);
  readonly historyKey = input<HistorySelection | null>(null);

  /** The person wants this passage shown (highlighted) in the PDF. */
  readonly viewPassage = output<string>();
  /** The person wants a replaced text shown in the PDF. */
  readonly showHistory = output<HistorySelection>();

  protected readonly node = computed(() => this.tree().node);
  protected readonly current = computed(() => this.node().current);
  protected readonly locator = computed(() => nodeLocator(this.node()));
  protected readonly anchor = computed(
    () => `p-${this.node().path.replace(/[^A-Za-z0-9_-]/g, '_')}`,
  );
  protected readonly isFocused = computed(() => this.focusPath() === this.node().path);
  protected readonly isWithinFocus = computed(() => {
    const focus = this.focusPath();
    return focus !== null && this.node().path.startsWith(focus + '/');
  });
  protected readonly isAnnex = computed(() => this.node().kind === 'annex');
  protected readonly isContainer = computed(() =>
    ['section', 'title', 'chapter'].includes(this.node().kind),
  );
  protected readonly pages = computed(() => {
    const { page_start: start, page_end: end } = this.current();
    return start === end ? `p. ${start}` : `pp. ${start}-${end}`;
  });
  /** What a screen reader says the buttons act on. */
  protected readonly subject = computed(() => this.node().current.citation.short);

  protected verb(event: LegalEvent): string {
    return eventVerb(event);
  }

  protected noteKind(kind: string): string {
    return noteKindLabel({ kind });
  }

  /** The norm that replaced history[index] is the one that introduced the next revision. */
  protected replacedBy(index: number): LegalEvent | null {
    const history = this.node().history;
    return (history[index + 1] ?? this.node().current).event;
  }

  protected isViewingHistory(revision: ReadingRevision): boolean {
    const key = this.historyKey();
    return key?.path === this.node().path && key.revision === revision.revision;
  }
}
