import { DatePipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';

import { EditionContext } from '../../../../core/api/models';
import { ValiditySeal } from '../../../../shared/ui/validity-seal/validity-seal';
import { approvalNote, instrumentReference } from '../../../../shared/util/instrument-labels';

/** Which norm and which edition is being read, and how much is known about its validity. */
@Component({
  selector: 'drtc-edition-header',
  imports: [DatePipe, ValiditySeal],
  templateUrl: './edition-header.html',
  styleUrl: './edition-header.css',
})
export class EditionHeader {
  readonly edition = input.required<EditionContext>();

  protected readonly reference = computed(() => {
    const { type, number } = this.edition();
    return instrumentReference(type, number);
  });
  protected readonly approval = computed(() => approvalNote(this.edition().approval_mode));
}
