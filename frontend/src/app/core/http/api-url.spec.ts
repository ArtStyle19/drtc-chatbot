import { resolveApiUrl } from './api-url';

describe('resolveApiUrl', () => {
  it('keeps same-origin URLs when there is no base URL', () => {
    expect(resolveApiUrl('/api/v1/versions/x/source', '')).toBe('/api/v1/versions/x/source');
  });

  it('prefixes API paths with the base URL, without doubling slashes', () => {
    expect(resolveApiUrl('/api/v1/versions/x/source', 'https://api.drtc.test')).toBe(
      'https://api.drtc.test/api/v1/versions/x/source',
    );
    expect(resolveApiUrl('/api/v1/x', 'https://api.drtc.test/')).toBe(
      'https://api.drtc.test/api/v1/x',
    );
  });

  it('leaves absolute and non-API URLs alone', () => {
    expect(resolveApiUrl('https://other.test/a.pdf', 'https://api.drtc.test')).toBe(
      'https://other.test/a.pdf',
    );
    expect(resolveApiUrl('/assets/a.pdf', 'https://api.drtc.test')).toBe('/assets/a.pdf');
  });
});
