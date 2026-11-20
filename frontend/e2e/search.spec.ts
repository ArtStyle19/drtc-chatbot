import AxeBuilder from '@axe-core/playwright';
import { expect, Page, test } from '@playwright/test';

import { instrumentsResponse } from './fixtures/instruments';
import { searchEmpty, searchFiltered, searchPlazo, searchReference } from './fixtures/search';

const useRealApi = process.env['E2E_REAL_API'] === '1';
const QUERY = 'plazo para interponer recurso de apelación';

const lookupUnrecognized = {
  status: 'unrecognized',
  query: QUERY,
  message: 'No reconozco una referencia en ese texto, pero puede buscarlo por su contenido.',
  reference: null,
  norms: [],
  total: 0,
  hits: [],
  ignored_text: null,
};

/** The same answer as the real one, but with the meaning search "available". */
const searchWorked = { ...searchPlazo, degraded: [] as string[] };

interface Mock {
  /** Query strings of every GET /api/v1/search the page made. */
  readonly searches: string[];
  readonly lookups: string[];
}

/**
 * Mocked mode: /search and /lookup answer with responses captured from the real API
 * (fixtures/search.ts). Real mode (E2E_REAL_API=1): nothing is mocked, only recorded.
 */
async function mockApi(
  page: Page,
  answer: (params: URLSearchParams) => { status?: number; json: unknown } = (params) => ({
    json: params.get('instrument') ? searchFiltered : searchPlazo,
  }),
): Promise<Mock> {
  const mock: { searches: string[]; lookups: string[] } = { searches: [], lookups: [] };
  page.on('request', (request) => {
    const url = new URL(request.url());
    if (url.pathname === '/api/v1/search') mock.searches.push(url.search);
    if (url.pathname === '/api/v1/lookup') mock.lookups.push(url.search);
  });
  if (useRealApi) return mock;
  await page.route('**/api/v1/instruments', (route) =>
    route.fulfill({ json: instrumentsResponse }),
  );
  await page.route(/\/api\/v1\/lookup/, (route) => route.fulfill({ json: lookupUnrecognized }));
  await page.route(/\/api\/v1\/search/, (route) => {
    const { status = 200, json } = answer(new URL(route.request().url()).searchParams);
    return route.fulfill(
      status === 200 ? { json } : { status, contentType: 'application/problem+json', json },
    );
  });
  return mock;
}

async function expectNoSeriousViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  const serious = results.violations.filter((v) =>
    ['serious', 'critical'].includes(v.impact ?? ''),
  );
  expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
}

const header = (page: Page) => page.getByRole('search').first();
const cards = (page: Page) => page.locator('drtc-result-card');

test.describe('Buscar en el texto (spec 004)', () => {
  test.skip(useRealApi, 'Mocked scenarios; the real API has its own block at the end');

  test('typing in the header never searches the text: only Enter or the option does', async ({
    page,
  }) => {
    const mock = await mockApi(page);
    await page.goto('/biblioteca');
    const box = header(page).getByRole('combobox');

    await box.fill(QUERY);
    await expect(page.getByRole('option', { name: /en el texto/ })).toBeVisible();
    await page.waitForTimeout(600); // well past the typing delay

    expect(mock.lookups.length).toBeGreaterThan(0); // the reference search did run
    expect(mock.searches).toEqual([]); // the content search did NOT

    await box.press('Enter');
    await expect(page).toHaveURL(/\/buscar\?q=plazo/);
    await expect(cards(page).first()).toBeVisible();
    expect(mock.searches).toHaveLength(1);
  });

  test('«Buscar … en el texto» is reached with the keyboard from the header', async ({ page }) => {
    await mockApi(page);
    await page.goto('/biblioteca');
    const box = header(page).getByRole('combobox');

    await box.fill('licencia de conducir');
    await box.press('ArrowDown');
    await expect(page.getByRole('option', { name: /en el texto/ })).toHaveAttribute(
      'aria-selected',
      'true',
    );
    await box.press('Enter');

    await expect(page).toHaveURL(/\/buscar\?q=licencia/);
    await expect(page.getByRole('heading', { level: 1, name: 'Buscar en el texto' })).toBeVisible();
  });

  test('lists the matches with their citation, source and a link to read them', async ({
    page,
  }) => {
    await mockApi(page, () => ({ json: searchWorked }));
    await page.goto(`/buscar?q=${encodeURIComponent(QUERY)}`);

    await expect(page.getByRole('status').filter({ hasText: /resultados/ })).toContainText(
      'Se muestran 6 de 29 resultados.',
    );
    await expect(cards(page)).toHaveCount(6);
    const first = cards(page).first();
    await expect(first.getByRole('heading', { level: 2 })).toHaveText(
      'TUO de la Ley N.° 27444, art. 220',
    );
    await expect(first.locator('drtc-validity-seal')).toContainText('No verificado');
    await expect(first.locator('mark').first()).toHaveText(/recurso/i);
    await expect(first.locator('.via')).toHaveText('Por palabras');
    const link = first.getByRole('link', { name: /Leer en la norma/ });
    await expect(link).toHaveAttribute(
      'href',
      /^\/biblioteca\/tuo-ley-27444\?p=articulo(:|%3A)220&v=/,
    );
    await expect(page.locator('main .notice')).toHaveCount(0); // nothing degraded
    await expect(page).toHaveTitle(`Buscar «${QUERY}» · DRTC Puno`);
  });

  test('says the meaning search is unavailable, and still lists what it found', async ({
    page,
  }) => {
    await mockApi(page);
    await page.goto(`/buscar?q=${encodeURIComponent(QUERY)}`);

    await expect(page.locator('main .notice')).toContainText(
      'La búsqueda por significado no está disponible ahora',
    );
    await expect(cards(page)).toHaveCount(6);
  });

  test('a reference typed with other words goes first and says why', async ({ page }) => {
    await mockApi(page, () => ({ json: searchReference }));
    await page.goto('/buscar?q=art.%205%20Ley%2027181%20plazo');

    await expect(cards(page).first().getByRole('heading', { level: 2 })).toHaveText(
      'Ley N.° 27181, art. 5',
    );
    await expect(cards(page).first().locator('.via')).toHaveText('Referencia exacta');
    await expect(page.locator('.reference-note')).toContainText(
      '«art. 5» como una referencia exacta',
    );
  });

  test('filters by norm asking the server, and the filter can be removed', async ({ page }) => {
    const mock = await mockApi(page);
    await page.goto(`/buscar?q=${encodeURIComponent(QUERY)}`);
    const group = page.getByRole('group', { name: 'Filtrar por norma' });
    await expect(group.getByRole('button', { name: 'Todas las normas' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );

    await group.getByRole('button', { name: /27444/ }).click();

    await expect(page).toHaveURL(/norma=tuo-ley-27444/);
    await expect(cards(page)).toHaveCount(4);
    expect(mock.searches.at(-1)).toContain('instrument=tuo-ley-27444');
    await expect(group.getByRole('button', { name: /27444/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    );

    await group.getByRole('button', { name: 'Todas las normas' }).click();
    await expect(page).not.toHaveURL(/norma=/);
    await expect(cards(page)).toHaveCount(6);
  });

  test('shows the other passages that matched inside a result', async ({ page }) => {
    await mockApi(page);
    await page.goto(`/buscar?q=${encodeURIComponent(QUERY)}`);
    const card = cards(page).filter({ hasText: 'art. 218, num. 218.1, lit. b)' });

    await card.getByText(/pasajes más coinciden/).click();

    await expect(card.locator('.other-link').first()).toBeVisible();
    await expect(card.locator('.other-link')).toHaveCount(4);
  });

  test('shows an empty state with suggestions', async ({ page }) => {
    await mockApi(page, () => ({ json: searchEmpty }));
    await page.goto('/buscar?q=zzzz%20qqqq');

    await expect(page.getByText('No encontramos coincidencias para «zzzz qqqq»')).toBeVisible();
    await expect(page.getByRole('status').filter({ hasText: 'Sin resultados.' })).toBeVisible();
    await expect(cards(page)).toHaveCount(0);
  });

  test('shows an error that can be retried', async ({ page }) => {
    let fail = true;
    await mockApi(page, () =>
      fail
        ? { status: 500, json: { status: 500, code: 'db_exploded', detail: 'boom' } }
        : { json: searchPlazo },
    );
    await page.goto(`/buscar?q=${encodeURIComponent(QUERY)}`);
    await expect(page.getByRole('alert')).toContainText('No pudimos buscar.');
    await expect(page.getByRole('alert')).not.toContainText('boom');

    fail = false;
    await page.getByRole('button', { name: 'Reintentar' }).click();

    await expect(page.getByRole('alert')).toHaveCount(0);
    await expect(cards(page)).toHaveCount(6);
  });

  test('the form searches a new text from the page itself', async ({ page }) => {
    const mock = await mockApi(page);
    await page.goto('/buscar');
    await expect(page.getByText('Pruebe con una pregunta o unas palabras')).toBeVisible();
    expect(mock.searches).toEqual([]);

    await page.getByLabel('¿Qué quiere encontrar?').fill(QUERY);
    await page.getByRole('button', { name: 'Buscar', exact: true }).click();

    await expect(page).toHaveURL(/\/buscar\?q=plazo/);
    await expect(cards(page)).toHaveCount(6);
  });

  test('the privacy notice is in the page and tied to the field', async ({ page }) => {
    await mockApi(page);
    await page.goto('/buscar');

    await expect(page.locator('#buscar-privacidad')).toContainText(
      'No escriba nombres, DNI, placas',
    );
    await expect(page.getByLabel('¿Qué quiere encontrar?')).toHaveAccessibleDescription(
      /No escriba nombres, DNI, placas/,
    );
  });

  test('the diagnostic view shows how each result was found (development builds)', async ({
    page,
  }) => {
    const mock = await mockApi(page);
    await page.goto(`/buscar?q=${encodeURIComponent(QUERY)}`);
    await expect(cards(page).first()).toBeVisible();
    await expect(page.locator('.debug')).toHaveCount(0);

    await page.getByRole('button', { name: 'Mostrar diagnóstico' }).click();

    await expect(page).toHaveURL(/debug=1/);
    await expect.poll(() => mock.searches.at(-1)).toContain('debug=true');
    await page.locator('.debug summary').first().click();
    await expect(page.locator('.debug').first()).toContainText('lexical_rank');
  });

  test('a search can be shared: the URL alone reproduces it', async ({ page }) => {
    await mockApi(page);
    await page.goto(`/buscar?q=${encodeURIComponent(QUERY)}&norma=tuo-ley-27444`);

    await expect(cards(page)).toHaveCount(4);
    await expect(page.getByLabel('¿Qué quiere encontrar?')).toHaveValue(QUERY);
  });

  test('every result can be reached and used with the keyboard', async ({ page }) => {
    await mockApi(page);
    await page.goto(`/buscar?q=${encodeURIComponent(QUERY)}`);
    await expect(cards(page).first()).toBeVisible();

    const link = cards(page)
      .first()
      .getByRole('link', { name: /Leer en la norma/ });
    await link.focus();
    await expect(link).toBeFocused();
  });

  test.describe('on a phone', () => {
    test.use({ viewport: { width: 390, height: 844 } });

    test('has no horizontal scroll and the results are readable', async ({ page }) => {
      await mockApi(page);
      await page.goto(`/buscar?q=${encodeURIComponent(QUERY)}`);
      await expect(cards(page).first()).toBeVisible();

      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(0);
      const box = await cards(page).first().boundingBox();
      expect(box!.width).toBeLessThanOrEqual(390);
    });
  });

  test.describe('accessibility (WCAG 2.2 AA, axe)', () => {
    const scenarios: { name: string; url: string; answer: Parameters<typeof mockApi>[1] }[] = [
      {
        name: 'results',
        url: `/buscar?q=${encodeURIComponent(QUERY)}`,
        answer: () => ({ json: searchWorked }),
      },
      {
        name: 'degraded results',
        url: `/buscar?q=${encodeURIComponent(QUERY)}`,
        answer: undefined,
      },
      { name: 'empty', url: '/buscar?q=zzzz%20qqqq', answer: () => ({ json: searchEmpty }) },
      {
        name: 'error',
        url: `/buscar?q=${encodeURIComponent(QUERY)}`,
        answer: () => ({ status: 500, json: { status: 500, code: 'internal_error', detail: 'x' } }),
      },
      { name: 'no text', url: '/buscar', answer: undefined },
    ];

    for (const viewport of [
      { label: 'desktop', width: 1280, height: 900 },
      { label: 'mobile', width: 390, height: 844 },
    ]) {
      for (const scenario of scenarios) {
        test(`${scenario.name} — ${viewport.label}`, async ({ page }) => {
          await page.setViewportSize({ width: viewport.width, height: viewport.height });
          await mockApi(page, scenario.answer);
          await page.goto(scenario.url);
          if (scenario.name === 'error') await expect(page.getByRole('alert')).toBeVisible();
          else if (scenario.name === 'empty')
            await expect(page.getByText(/No encontramos/)).toBeVisible();
          else if (scenario.name !== 'no text') await expect(cards(page).first()).toBeVisible();
          else await expect(page.getByText('Pruebe con una pregunta')).toBeVisible();

          await expectNoSeriousViolations(page);
        });
      }
    }

    test('the header search with the «en el texto» option open', async ({ page }) => {
      await mockApi(page);
      await page.goto('/biblioteca');
      await header(page).getByRole('combobox').fill(QUERY);
      await expect(page.getByRole('option', { name: /en el texto/ })).toBeVisible();

      await expectNoSeriousViolations(page);
    });

    test('the diagnostic view open', async ({ page }) => {
      await mockApi(page);
      await page.goto(`/buscar?q=${encodeURIComponent(QUERY)}&debug=1`);
      await page.locator('.debug summary').first().click();

      await expectNoSeriousViolations(page);
    });
  });
});

/** Success criteria that need the real backend and the corpus ingested (E2E_REAL_API=1). */
test.describe('Contra el backend real', () => {
  test.skip(!useRealApi, 'Requires E2E_REAL_API=1 and the corpus ingested');

  test('finds the interposition term of the appeals in the TUO by its own words', async ({
    page,
  }) => {
    await page.goto(`/buscar?q=${encodeURIComponent('plazo para apelar una resolución')}`);

    await expect(cards(page).first()).toBeVisible();
    await expect(page.locator('main')).toContainText('27444');
    await expectNoSeriousViolations(page);
  });

  test('a reference typed in the page goes first', async ({ page }) => {
    await page.goto('/buscar?q=art.%205%20Ley%2027181%20plazo');

    await expect(cards(page).first().getByRole('heading', { level: 2 })).toContainText(
      '27181, art. 5',
    );
    await expect(cards(page).first().locator('.via').first()).toHaveText('Referencia exacta');
  });

  test('from the header: text that is not a reference ends in the search page', async ({
    page,
  }) => {
    await page.goto('/biblioteca');
    const box = header(page).getByRole('combobox');

    await box.fill('mototaxi');
    await box.press('Enter');

    await expect(page).toHaveURL(/\/buscar\?q=mototaxi/);
    await expect(page.getByRole('status').filter({ hasText: /resultado/ })).toBeVisible();
  });

  test('nothing found is a clear state, not an error', async ({ page }) => {
    await page.goto('/buscar?q=zzzzqqqq');

    await expect(page.getByText(/No encontramos coincidencias/)).toBeVisible();
    await expect(page.getByRole('alert')).toHaveCount(0);
  });

  test('a result opens the reader at that provision', async ({ page }) => {
    await page.goto(`/buscar?q=${encodeURIComponent('silencio administrativo positivo')}`);
    await expect(cards(page).first()).toBeVisible();

    await cards(page)
      .first()
      .getByRole('link', { name: /Leer en la norma/ })
      .click();

    await expect(page).toHaveURL(/\/biblioteca\/[^/?]+\?p=/);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });
});
