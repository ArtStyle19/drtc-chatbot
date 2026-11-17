import { DatePipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';

import { InstrumentType, LegalInstrument } from '../../../../core/api/models';
import { ValiditySeal } from '../../../../shared/ui/validity-seal/validity-seal';

const TYPE_LABELS: Record<InstrumentType, string> = {
  ley: 'Ley',
  decreto_supremo: 'Decreto Supremo',
  decreto_legislativo: 'Decreto Legislativo',
  decreto_de_urgencia: 'Decreto de Urgencia',
  texto_unico_ordenado: 'Texto Único Ordenado',
  reglamento: 'Reglamento',
  resolucion: 'Resolución',
  ordenanza_regional: 'Ordenanza Regional',
  otro: 'Norma',
};

/** Presentational card of a legal instrument (no data access, no state). */
@Component({
  selector: 'drtc-instrument-card',
  imports: [DatePipe, ValiditySeal],
  templateUrl: './instrument-card.html',
  styleUrl: './instrument-card.css',
})
export class InstrumentCard {
  readonly instrument = input.required<LegalInstrument>();

  protected readonly reference = computed(() => {
    const { type, number } = this.instrument();
    return `${TYPE_LABELS[type]} N.° ${number}`;
  });
  protected readonly edition = computed(() => this.instrument().current_edition);
  protected readonly titleId = computed(() => `norma-${this.instrument().id}`);
}
