import { Component, inject } from '@angular/core';

import { LibraryStore } from '../data-access/library.store';
import { InstrumentCard } from '../ui/instrument-card/instrument-card';

/** Biblioteca normativa: the norms available to the assistant and the status of each edition. */
@Component({
  selector: 'drtc-library-page',
  imports: [InstrumentCard],
  providers: [LibraryStore],
  templateUrl: './library-page.html',
})
export class LibraryPage {
  protected readonly store = inject(LibraryStore);
}
