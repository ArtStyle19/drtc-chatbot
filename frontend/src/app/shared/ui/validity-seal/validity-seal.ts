import { Component, computed, input } from '@angular/core';
import { LucideBadgeCheck, LucideShieldQuestionMark, LucideStamp } from '@lucide/angular';

import { VerificationStatus } from '../../../core/api/models';

type SealTone = 'verified' | 'unverified' | 'repealed' | 'superseded';

interface SealPresentation {
  readonly label: string;
  readonly tone: SealTone;
  readonly description: string;
}

const PRESENTATION: Record<VerificationStatus, SealPresentation> = {
  verified_current: {
    label: 'Vigente verificado',
    tone: 'verified',
    description: 'Texto contrastado con la fuente oficial y vigente a la fecha de verificación.',
  },
  unverified: {
    label: 'No verificado',
    tone: 'unverified',
    description: 'Texto aún no contrastado con la fuente oficial: no se presenta como vigente.',
  },
  pending_review: {
    label: 'En revisión',
    tone: 'unverified',
    description: 'Texto en revisión jurídica: no se presenta como vigente.',
  },
  superseded: {
    label: 'Sustituido',
    tone: 'superseded',
    description: 'Existe un texto posterior que reemplaza a esta edición.',
  },
  repealed: {
    label: 'Derogado',
    tone: 'repealed',
    description: 'La norma o disposición fue derogada.',
  },
  unknown: {
    label: 'Vigencia desconocida',
    tone: 'superseded',
    description: 'No hay información sobre su vigencia: no se presenta como vigente.',
  },
};

/**
 * "Sello de vigencia": the signature element of the UI. It appears wherever a norm or provision
 * is shown and states, in words, how much we know about whether its text is in force.
 */
@Component({
  selector: 'drtc-validity-seal',
  imports: [LucideBadgeCheck, LucideShieldQuestionMark, LucideStamp],
  templateUrl: './validity-seal.html',
  styleUrl: './validity-seal.css',
  host: {
    class: 'seal',
    '[attr.data-tone]': 'presentation().tone',
    '[attr.title]': 'presentation().description',
  },
})
export class ValiditySeal {
  readonly status = input.required<VerificationStatus>();
  /** Optional edition qualifier, e.g. "edición 04.01.2017". */
  readonly edition = input<string | null>(null);

  protected readonly presentation = computed(() => PRESENTATION[this.status()]);
}
