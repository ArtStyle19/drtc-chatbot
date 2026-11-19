import { sealStatus } from './verification';

describe('sealStatus', () => {
  it('keeps a status the server confirmed', () => {
    expect(sealStatus('verified_current', true)).toBe('verified_current');
    expect(sealStatus('unverified', false)).toBe('unverified');
    expect(sealStatus('repealed', false)).toBe('repealed');
  });

  it('never shows "verified" without the explicit permission to present it as current', () => {
    expect(sealStatus('verified_current', false)).toBe('unverified');
  });

  it('turns a value it does not know into "unknown", never into something stronger', () => {
    expect(sealStatus('official', true)).toBe('unknown');
    expect(sealStatus('', true)).toBe('unknown');
  });
});
