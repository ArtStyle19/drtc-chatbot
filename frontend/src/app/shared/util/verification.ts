import { VerificationStatus } from '../../core/api/models';

const KNOWN: readonly VerificationStatus[] = [
  'verified_current',
  'unverified',
  'pending_review',
  'superseded',
  'repealed',
  'unknown',
];

/**
 * The status to show on a seal for a search result. It can only get MORE cautious than what the
 * server said: an unknown value becomes `unknown`, and "verified" without the server's explicit
 * `may_be_presented_as_current` is shown as unverified (constitution I: nothing unverified is
 * ever presented as current).
 */
export function sealStatus(status: string, mayBePresentedAsCurrent: boolean): VerificationStatus {
  const known = KNOWN.find((candidate) => candidate === status) ?? 'unknown';
  return known === 'verified_current' && !mayBePresentedAsCurrent ? 'unverified' : known;
}
