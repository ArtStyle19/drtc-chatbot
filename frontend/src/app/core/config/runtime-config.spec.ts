import { DEFAULT_RUNTIME_CONFIG, loadRuntimeConfig } from './runtime-config';

function fakeFetch(body: unknown, ok = true): typeof fetch {
  return (() =>
    Promise.resolve({ ok, json: () => Promise.resolve(body) } as Response)) as typeof fetch;
}

describe('loadRuntimeConfig', () => {
  it('reads the API base URL and trims trailing slashes', async () => {
    const config = await loadRuntimeConfig(fakeFetch({ apiBaseUrl: 'https://api.example.org/' }));

    expect(config.apiBaseUrl).toBe('https://api.example.org');
  });

  it('falls back to same-origin defaults when the file is missing or invalid', async () => {
    expect(await loadRuntimeConfig(fakeFetch({}, false))).toEqual(DEFAULT_RUNTIME_CONFIG);
    expect(await loadRuntimeConfig(fakeFetch({ apiBaseUrl: 42 }))).toEqual(DEFAULT_RUNTIME_CONFIG);
    expect(await loadRuntimeConfig(() => Promise.reject(new Error('offline')))).toEqual(
      DEFAULT_RUNTIME_CONFIG,
    );
  });
});
