import { Clipboard } from '@angular/cdk/clipboard';
import { LiveAnnouncer } from '@angular/cdk/a11y';
import { Component, computed, DestroyRef, inject, input, signal } from '@angular/core';
import { LucideCheck, LucideCopy } from '@lucide/angular';

import { CitationText } from '../../../../core/api/models';

type CopyKind = 'formal' | 'short';
const FEEDBACK_MS = 2000;

/**
 * "Copiar cita": copies the citation written by the SERVER (formal or short). The browser never
 * composes a citation, so it can never contradict the edition's verification status.
 */
@Component({
  selector: 'drtc-cite-button',
  imports: [LucideCheck, LucideCopy],
  templateUrl: './cite-button.html',
  styleUrl: './cite-button.css',
  host: { class: 'inline-flex gap-1' },
})
export class CiteButton {
  readonly citation = input.required<CitationText>();
  /** What is being cited, for assistive technology: "artículo 2, literal e)". */
  readonly subject = input('esta disposición');

  private readonly clipboard = inject(Clipboard);
  private readonly announcer = inject(LiveAnnouncer);
  protected readonly copied = signal<CopyKind | null>(null);
  protected readonly failed = signal(false);
  protected readonly formalLabel = computed(() =>
    this.copied() === 'formal' ? 'Cita copiada' : 'Copiar cita',
  );
  protected readonly shortLabel = computed(() =>
    this.copied() === 'short' ? 'Copiada' : 'Cita breve',
  );
  private timer: ReturnType<typeof setTimeout> | undefined;

  constructor() {
    inject(DestroyRef).onDestroy(() => clearTimeout(this.timer));
  }

  protected copy(kind: CopyKind): void {
    const text = kind === 'formal' ? this.citation().formal : this.citation().short;
    const ok = this.clipboard.copy(text);
    this.failed.set(!ok);
    this.copied.set(ok ? kind : null);
    void this.announcer.announce(
      ok
        ? `Cita ${kind === 'formal' ? 'formal' : 'breve'} copiada`
        : 'No se pudo copiar la cita. Selecciónela manualmente.',
      'polite',
    );
    clearTimeout(this.timer);
    this.timer = setTimeout(() => {
      this.copied.set(null);
      this.failed.set(false);
    }, FEEDBACK_MS);
  }
}
