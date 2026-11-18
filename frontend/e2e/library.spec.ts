import AxeBuilder from '@axe-core/playwright';
import { expect, Page, test } from '@playwright/test';

import { instrumentsResponse } from './fixtures/instruments';

const useRealApi = process.env['E2E_REAL_API'] === '1';

async function mockInstruments(page: Page, status = 200): Promise<void> {
  if (useRealApi && status === 200) {
    return;
  }
  await page.route('**/api/v1/instruments', (route) =>
    status === 200
      ? route.fulfill({ json: instrumentsResponse })
      : route.fulfill({
          status,
          contentType: 'application/problem+json',
          json: { status, code: 'internal_error', detail: 'Ocurrió un error inesperado.' },
        }),
  );
}

test.describe('Biblioteca normativa (spec 001)', () => {
  test('lists the three norms, each marked as not verified', async ({ page }) => {
    await mockInstruments(page);
    await page.goto('/');

    await expect(page).toHaveURL(/\/biblioteca$/);
    await expect(
      page.getByRole('heading', { level: 1, name: 'Biblioteca normativa' }),
    ).toBeVisible();
    const cards = page.getByRole('article');
    await expect(cards).toHaveCount(3);
    for (const card of await cards.all()) {
      await expect(card.locator('drtc-validity-seal')).toContainText('No verificado');
    }
    await expect(page.locator('.reference').first()).toHaveText('Ley N.° 27181');
  });

  test('has no serious accessibility violations', async ({ page }) => {
    await mockInstruments(page);
    await page.goto('/biblioteca');
    await expect(page.getByRole('article')).toHaveCount(3);

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    const serious = results.violations.filter((v) =>
      ['serious', 'critical'].includes(v.impact ?? ''),
    );
    expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
  });

  test('explains the error and offers a retry when the API fails', async ({ page }) => {
    test.skip(useRealApi, 'Only meaningful with a mocked API');
    await mockInstruments(page, 500);
    await page.goto('/biblioteca');

    await expect(page.getByRole('alert')).toContainText('No pudimos cargar la biblioteca');
    await expect(page.getByRole('button', { name: 'Reintentar' })).toBeVisible();
  });
});

test('Consultas shows what is coming next', async ({ page }) => {
  await page.goto('/consultas');

  await expect(page.getByRole('heading', { level: 1, name: 'Consultas citadas' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Consultas' })).toHaveAttribute(
    'aria-current',
    'page',
  );
});
