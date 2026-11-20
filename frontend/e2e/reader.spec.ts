import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import AxeBuilder from '@axe-core/playwright';
import { expect, Page, test } from '@playwright/test';

import { instrumentsResponse } from './fixtures/instruments';
import {
  articulo2,
  articulo3,
  articulo5,
  lookupArt11,
  lookupArt5,
  lookupMissing,
  outlineLey,
  tituloI,
} from './fixtures/reader';

const useRealApi = process.env['E2E_REAL_API'] === '1';
const LEY_PDF = resolve(process.cwd(), '../corpus/sources/ley-27181-lgttt-texto-2020-06.pdf');
const TUO_PDF_BYTES = 14_156_131;

const problem = (status: number, code: string, detail: string) => ({
  status,
  contentType: 'application/problem+json',
  json: { status, code, detail },
});

/**
 * Mocked mode: the reader API answers with responses captured from the real one (fixtures/reader.ts)
 * and the real Ley 27181 PDF is served, so pdf.js renders a genuine page. Real mode: nothing is
 * mocked (needs the backend with the corpus ingested; run with E2E_REAL_API=1).
 */
async function mockReaderApi(page: Page): Promise<void> {
  if (useRealApi) return;
  await page.route('**/api/v1/instruments', (route) =>
    route.fulfill({ json: instrumentsResponse }),
  );
  await page.route(/\/api\/v1\/instruments\/[^/]+\/outline/, (route) =>
    route.fulfill(problem(404, 'not_found', 'The norm has no approved edition')),
  );
  await page.route(/\/api\/v1\/instruments\/ley-27181\/outline/, (route) =>
    route.fulfill({ json: outlineLey }),
  );
  await page.route(/\/api\/v1\/instruments\/ley-27181\/reading-unit/, (route) => {
    const path = new URL(route.request().url()).searchParams.get('path') ?? '';
    if (path.startsWith('articulo:2')) return route.fulfill({ json: articulo2 });
    if (path === 'articulo:3') return route.fulfill({ json: articulo3 });
    if (path === 'articulo:5') return route.fulfill({ json: articulo5 });
    if (path === 'titulo:I') return route.fulfill({ json: tituloI });
    return route.fulfill(problem(404, 'not_found', `${path} does not exist`));
  });
  await page.route(/\/api\/v1\/lookup/, (route) => {
    const q = new URL(route.request().url()).searchParams.get('q') ?? '';
    if (/999/.test(q)) return route.fulfill({ json: lookupMissing });
    if (/11/.test(q)) return route.fulfill({ json: lookupArt11 });
    return route.fulfill({ json: lookupArt5 });
  });
  await page.route(/\/api\/v1\/versions\/.+\/source/, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/pdf',
      headers: { 'accept-ranges': 'none' },
      body: readFileSync(LEY_PDF),
    }),
  );
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

const marks = (page: Page) => page.locator('drtc-folio .mark');

test.describe('Lector normativo (spec 003)', () => {
  test.beforeEach(async ({ page }) => {
    await mockReaderApi(page);
  });

  test('opens a norm from the library and offers its index', async ({ page }) => {
    await page.goto('/biblioteca');

    await page.getByRole('link', { name: 'Leer norma Ley N.° 27181' }).click();

    await expect(page).toHaveURL(/\/biblioteca\/ley-27181$/);
    await expect(
      page.getByRole('heading', {
        level: 1,
        name: 'Ley General de Transporte y Tránsito Terrestre',
      }),
    ).toBeVisible();
    await expect(page.locator('drtc-edition-header drtc-validity-seal')).toContainText(
      'No verificado',
    );
    await expect(page.getByRole('heading', { name: 'Elija una disposición' })).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'Índice de la norma' })).toBeVisible();
    await expect(page).toHaveTitle(/Ley 27181 \(LGTTT\) · DRTC Puno/);
  });

  test('reads an article chosen in the index, with its history and the PDF page', async ({
    page,
  }) => {
    await page.goto('/biblioteca/ley-27181');

    await page.getByRole('button', { name: 'Expandir Título I', exact: true }).click();
    await page.getByRole('link', { name: /Art\. 2 De las definiciones/ }).click();

    await expect(page).toHaveURL(/p=articulo(:|%3A)2$/);
    await expect(
      page.getByRole('heading', { level: 2, name: 'Artículo 2 De las definiciones' }),
    ).toBeVisible();
    await expect(page.locator('.reading')).toContainText('entiéndase por');
    await expect(page.locator('.reading details.history summary').first()).toContainText(
      'Texto anterior, no vigente',
    );
    await expect(page.locator('.reading .unit-meta drtc-validity-seal')).toContainText(
      'No verificado',
    );
    await expect(page.locator('drtc-folio .passage-label')).toContainText('art. 2');
    await expect(page.locator('drtc-folio canvas')).toBeVisible();
    await expect(marks(page).first()).toBeVisible();
    await expect(page).toHaveTitle('Artículo 2 · Ley 27181 (LGTTT) · DRTC Puno');
  });

  test('"Ver en el PDF" puts the exact passage in the URL and survives a reload', async ({
    page,
  }) => {
    await page.goto('/biblioteca/ley-27181?p=articulo:2');
    await expect(marks(page).first()).toBeVisible();

    await page
      .getByRole('button', { name: /Ver en el PDF de Ley N\.° 27181, art\. 2, lit\. e\)/ })
      .click();

    await expect(page).toHaveURL(/p=articulo(:|%3A)2(\/|%2F)literal(:|%3A)e/);
    await expect(page.locator('drtc-folio .passage-label')).toContainText('art. 2, lit. e)');
    await expect(marks(page).first()).toBeVisible();

    await page.reload();

    await expect(page.locator('#p-articulo_2_literal_e')).toHaveClass(/is-focused/);
    await expect(page.locator('drtc-folio .passage-label')).toContainText('art. 2, lit. e)');
    await expect(marks(page).first()).toBeVisible();
  });

  test('shows a replaced text in the PDF marked as no longer in force', async ({ page }) => {
    await page.goto('/biblioteca/ley-27181?p=articulo:2');
    const history = page.locator('.reading details.history').first();
    await history.locator('summary').click();

    await history
      .getByRole('button', { name: /Ver en el PDF el texto anterior \(no vigente\)/ })
      .click();

    await expect(page.locator('drtc-folio .badge')).toContainText('Texto anterior · no vigente');
    await expect(marks(page).first()).toHaveClass(/is-replaced/);
  });

  test('copies the citation written by the server', async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    await page.goto('/biblioteca/ley-27181?p=articulo:2');

    await page
      .getByRole('button', { name: /Copiar cita formal de Ley N\.° 27181, art\. 2, lit\. e\)/ })
      .click();

    const copied = await page.evaluate(() => navigator.clipboard.readText());
    expect(copied).toContain('Ley N.° 27181');
    expect(copied).toContain('art. 2, lit. e)');
    expect(copied).toContain('no verificada');
  });

  test('a título lists what it contains', async ({ page }) => {
    await page.goto('/biblioteca/ley-27181');

    await page
      .getByRole('navigation', { name: 'Índice de la norma' })
      .getByRole('link', { name: /^Título I Definiciones/ })
      .click();

    await expect(page.getByRole('heading', { level: 2, name: /^Título I/ })).toBeVisible();
    await expect(page.locator('drtc-container-view a.item').first()).toBeVisible();
    await expect(page.locator('.reading drtc-provision-node')).toHaveCount(0);
  });

  test('steps to the next provision', async ({ page }) => {
    await page.goto('/biblioteca/ley-27181?p=articulo:2');

    await page.locator('a.next').click();

    await expect(page.getByRole('heading', { level: 2, name: /^Artículo 3/ })).toBeFocused();
  });

  test('explains a provision that does not exist and keeps the index', async ({ page }) => {
    await page.goto('/biblioteca/ley-27181?p=articulo:999');

    await expect(page.locator('.reading [role="alert"]')).toContainText(
      'No encontramos esa disposición',
    );
    await expect(page.getByRole('navigation', { name: 'Índice de la norma' })).toBeVisible();
  });

  test('explains a norm that cannot be opened', async ({ page }) => {
    await page.goto('/biblioteca/norma-que-no-existe');

    await expect(page.getByRole('alert')).toContainText('No pudimos abrir esta norma');
    await expect(page.getByRole('button', { name: 'Reintentar' })).toBeVisible();
  });

  test.describe('reference search', () => {
    test('finds a reference and opens the exact place', async ({ page }) => {
      await page.goto('/biblioteca');
      await expect(page.getByRole('article')).toHaveCount(3); // the app has finished starting
      await page.keyboard.press('/');
      await expect(page.getByRole('combobox')).toBeFocused();

      await page.getByRole('combobox').fill('art 5 ley 27181');
      await expect(page.getByRole('option', { name: /Ley N\.° 27181, art\. 5/ })).toBeVisible();
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('Enter');

      await expect(page).toHaveURL(
        /\/biblioteca\/ley-27181\?p=articulo(:|%3A)5&v=ley-27181(@|%40)2020-05/,
      );
      await expect(page.getByRole('heading', { level: 2, name: /^Artículo 5/ })).toBeVisible();
    });

    test('goes straight to a unique reference on Enter', async ({ page }) => {
      await page.goto('/biblioteca');

      await page.getByRole('combobox').fill('art 5 ley 27181');
      await page.keyboard.press('Enter');

      await expect(page).toHaveURL(/p=articulo(:|%3A)5/);
    });

    test('lists every candidate of an ambiguous reference and chooses none', async ({ page }) => {
      await page.goto('/biblioteca');

      await page.getByRole('combobox').fill('art 11');

      await expect(page.getByRole('option')).toHaveCount(3);
      await expect(page.locator('drtc-reference-search .message')).toContainText('elija una');
      await expect(page).toHaveURL(/\/biblioteca$/);
    });

    test('says what it could not find', async ({ page }) => {
      await page.goto('/biblioteca');

      await page.getByRole('combobox').fill('art 999 ley 27181');

      await expect(page.locator('drtc-reference-search .message')).toContainText('art. 999');
      await expect(page.getByRole('option')).toHaveCount(0);
    });

    test('closes with Escape', async ({ page }) => {
      await page.goto('/biblioteca');
      await page.getByRole('combobox').fill('art 11');
      await expect(page.getByRole('listbox')).toBeVisible();

      await page.keyboard.press('Escape');

      await expect(page.getByRole('listbox')).toHaveCount(0);
      await expect(page.getByRole('combobox')).toHaveAttribute('aria-expanded', 'false');
    });
  });

  test.describe('accessibility (WCAG 2.2 AA)', () => {
    test('reader with a provision open', async ({ page }) => {
      await page.goto('/biblioteca/ley-27181?p=articulo:2/literal:e');
      await expect(marks(page).first()).toBeVisible();

      await expectNoSeriousViolations(page);
    });

    test('reader with a replaced text open', async ({ page }) => {
      await page.goto('/biblioteca/ley-27181?p=articulo:2');
      const history = page.locator('.reading details.history').first();
      await history.locator('summary').click();
      await history.getByRole('button', { name: /Ver en el PDF/ }).click();
      await expect(marks(page).first()).toBeVisible();

      await expectNoSeriousViolations(page);
    });

    test('a título and the cover', async ({ page }) => {
      await page.goto('/biblioteca/ley-27181');
      await expect(page.getByRole('heading', { name: 'Elija una disposición' })).toBeVisible();
      await expectNoSeriousViolations(page);

      await page.goto('/biblioteca/ley-27181?p=titulo:I');
      await expect(page.locator('drtc-container-view a.item').first()).toBeVisible();
      await expectNoSeriousViolations(page);
    });

    test('search results panel', async ({ page }) => {
      await page.goto('/biblioteca');
      await page.getByRole('combobox').fill('art 11');
      await expect(page.getByRole('option')).toHaveCount(3);
      await page.keyboard.press('ArrowDown');

      await expectNoSeriousViolations(page);
    });
  });
});

test.describe('Lector normativo en pantalla pequeña', () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test.beforeEach(async ({ page }) => {
    await mockReaderApi(page);
  });

  test('shows one pane at a time and lets the person switch to the PDF', async ({ page }) => {
    await page.goto('/biblioteca/ley-27181?p=articulo:2');
    await expect(page.locator('.reading')).toBeVisible();
    await expect(page.locator('drtc-folio')).toBeHidden();

    await page.getByRole('button', { name: 'PDF', exact: true }).click();

    await expect(page.locator('drtc-folio')).toBeVisible();
    await expect(page.locator('.reading')).toBeHidden();
    await expect(marks(page).first()).toBeVisible();
  });

  test('"Ver en el PDF" switches to the PDF pane', async ({ page }) => {
    await page.goto('/biblioteca/ley-27181?p=articulo:2');

    await page
      .getByRole('button', { name: /Ver en el PDF de Ley N\.° 27181, art\. 2, lit\. e\)/ })
      .click();

    await expect(page.locator('drtc-folio')).toBeVisible();
    await expect(marks(page).first()).toBeVisible();
  });

  test('opens the index as a panel and closes it after choosing', async ({ page }) => {
    await page.goto('/biblioteca/ley-27181');
    const toggle = page.getByRole('button', { name: 'Índice' });
    await expect(page.getByRole('navigation', { name: 'Índice de la norma' })).toBeHidden();

    await toggle.click();
    await expect(toggle).toHaveAttribute('aria-expanded', 'true');
    await page.getByRole('button', { name: 'Expandir Título I', exact: true }).click();
    await page.getByRole('link', { name: /Art\. 5 / }).click();

    await expect(page.getByRole('heading', { level: 2, name: /^Artículo 5/ })).toBeVisible();
    await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  });

  test('has no horizontal scroll', async ({ page }) => {
    await page.goto('/biblioteca/ley-27181?p=articulo:2');
    await expect(page.locator('.reading')).toBeVisible();

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
  });

  test('both panes have no serious accessibility violations', async ({ page }) => {
    await page.goto('/biblioteca/ley-27181?p=articulo:2');
    await expect(page.locator('.reading')).toBeVisible();
    await expectNoSeriousViolations(page);

    await page.getByRole('button', { name: 'PDF', exact: true }).click();
    await expect(marks(page).first()).toBeVisible();
    await expectNoSeriousViolations(page);
  });
});

/** Success criteria that need the real corpus and the real file server (E2E_REAL_API=1). */
test.describe('Contra el backend real', () => {
  test.skip(!useRealApi, 'Requires E2E_REAL_API=1 and the corpus ingested');

  test('SC-002: the highlight sits on the cited lines of the PDF', async ({ page }) => {
    await page.goto('/biblioteca/ley-27181?p=articulo:2/literal:e');
    await expect(marks(page).first()).toBeVisible();
    await page.waitForTimeout(500); // let the canvas finish painting

    // For every marker box: how much ink (text) is under it, compared with the same box moved up or
    // down by a few pixels. A box that sits on its line has at least as much ink as any nearby shift.
    const lines = await page.evaluate(() => {
      const canvas = document.querySelector<HTMLCanvasElement>('drtc-folio canvas')!;
      const context = canvas.getContext('2d')!;
      const canvasBox = canvas.getBoundingClientRect();
      const scale = canvas.width / canvasBox.width;
      const results: { inkAtMark: number; bestNearby: number }[] = [];
      for (const mark of document.querySelectorAll<HTMLElement>('drtc-folio .mark')) {
        const box = mark.getBoundingClientRect();
        const x = Math.round((box.left - canvasBox.left) * scale);
        const y = Math.round((box.top - canvasBox.top) * scale);
        const width = Math.max(1, Math.round(box.width * scale));
        const height = Math.max(1, Math.round(box.height * scale));
        const inkAt = (top: number): number => {
          const { data } = context.getImageData(x, Math.max(0, top), width, height);
          let ink = 0;
          for (let i = 0; i < data.length; i += 4) {
            if (data[i]! * 0.3 + data[i + 1]! * 0.59 + data[i + 2]! * 0.11 < 140) ink++;
          }
          return ink / (width * height);
        };
        let bestNearby = 0;
        for (let shift = -Math.round(height * 0.7); shift <= Math.round(height * 0.7); shift++) {
          bestNearby = Math.max(bestNearby, inkAt(y + shift));
        }
        results.push({ inkAtMark: inkAt(y), bestNearby });
      }
      return results;
    });

    expect(lines.length).toBeGreaterThan(0);
    for (const { inkAtMark, bestNearby } of lines) {
      expect(inkAtMark).toBeGreaterThan(0.05); // there is text under the marker
      expect(inkAtMark).toBeGreaterThanOrEqual(bestNearby * 0.9); // and it is on the line, not beside it
    }
  });

  test('SC-004: opening a TUO article does not download the whole PDF', async ({ page }) => {
    // Bytes really received (from the browser's network layer): an abandoned response counts only
    // for what arrived, unlike its Content-Length header.
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('Network.enable');
    const sourceRequests = new Set<string>();
    let received = 0;
    cdp.on('Network.requestWillBeSent', (event) => {
      if (event.request.url.includes('/api/v1/versions/')) sourceRequests.add(event.requestId);
    });
    cdp.on('Network.dataReceived', (event) => {
      if (sourceRequests.has(event.requestId)) received += event.dataLength;
    });

    await page.goto('/biblioteca/tuo-ley-27444?p=articulo:229');
    await expect(marks(page).first()).toBeVisible({ timeout: 30_000 });
    await page.waitForLoadState('networkidle');

    expect(received).toBeGreaterThan(0);
    expect(received).toBeLessThan(TUO_PDF_BYTES * 0.15);
  });

  test('highlights a numeral and a disposition of the real TUO and RENAT', async ({ page }) => {
    await page.goto('/biblioteca/tuo-ley-27444?p=articulo:218/numeral:218.2');
    await expect(marks(page).first()).toBeVisible({ timeout: 30_000 });
    await expect(page.locator('drtc-folio .passage-pages')).toContainText('236');

    await page.goto('/biblioteca/ds-017-2009-mtc?p=anexo:2');
    await expect(page.locator('.reading')).toContainText('Anexo 2');
    await expect(page.locator('.reading .warning').first()).toContainText('tabla');
  });
});
