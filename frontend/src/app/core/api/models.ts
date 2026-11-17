/**
 * Friendly aliases over the types generated from the backend OpenAPI contract.
 * Regenerate `schema.d.ts` with `npm run api:types` (never edit it by hand).
 */
import type { components } from './schema';

type Schemas = components['schemas'];

export type LegalInstrument = Schemas['LegalInstrumentOut'];
export type LegalInstrumentList = Schemas['LegalInstrumentListOut'];
export type Edition = Schemas['EditionOut'];
export type InstrumentType = Schemas['InstrumentType'];
export type VerificationStatus = Schemas['VerificationStatus'];
