import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { LOOKUP_DEBOUNCE_MS } from '../../lookup/data-access/lookup.store';
import { ReferenceSearch } from '../../lookup/feature/reference-search';

/**
 * What a person types can hold personal data. Typing in the header may only ask /lookup (our own
 * server, no third party, no cost); /search (which may reach an external embeddings service) is
 * called only when the person decides, from the /buscar page.
 */
describe('privacy of what is typed in the header', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('only ever calls /lookup while typing, and never /search', async () => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    const http = TestBed.inject(HttpTestingController);
    vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    const fixture = TestBed.createComponent(ReferenceSearch);
    fixture.detectChanges();
    const input = (fixture.nativeElement as HTMLElement).querySelector('input')!;

    input.dispatchEvent(new Event('focusin', { bubbles: true }));
    for (const typed of ['mi', 'mi vecino', 'mi vecino Pedro DNI 45678912']) {
      input.value = typed;
      input.dispatchEvent(new Event('input', { bubbles: true }));
      await vi.advanceTimersByTimeAsync(LOOKUP_DEBOUNCE_MS);
    }

    expect(http.match((request) => request.url.includes('/search'))).toHaveLength(0);
    const lookups = http.match((request) => request.url.includes('/lookup'));
    expect(lookups.length).toBeGreaterThan(0);
    // A newer keystroke cancels the previous request: answer only the ones still alive.
    lookups
      .filter((request) => !request.cancelled)
      .forEach((request) =>
        request.flush({
          status: 'unrecognized',
          query: '',
          message: '',
          reference: null,
          norms: [],
          total: 0,
          hits: [],
          ignored_text: null,
        }),
      );
    await vi.advanceTimersByTimeAsync(1);
    expect(http.match((request) => request.url.includes('/search'))).toHaveLength(0);
    http.verify();
  });
});
