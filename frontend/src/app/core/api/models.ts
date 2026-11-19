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

// ---- reader (spec 003)
export type Outline = Schemas['OutlineOut'];
export type OutlineEntry = Schemas['OutlineEntryOut'];
export type EditionContext = Schemas['EditionContextOut'];
export type ReadingUnit = Schemas['ReadingUnitOut'];
export type ReadingNode = Schemas['ReadingNodeOut'];
export type ReadingRevision = Schemas['ReadingRevisionOut'];
export type TextBox = Schemas['BoxOut'];
export type CitationText = Schemas['CitationOut'];
export type LegalEvent = Schemas['LegalEventOut'];
export type ReviewWarning = Schemas['ReviewWarningOut'];
export type EditorialNote = Schemas['EditorialNoteOut'];
export type ProvisionKind = Schemas['ProvisionKind'];

// ---- reference search (spec 003)
export type LookupResult = Schemas['LookupOut'];
export type LookupHit = Schemas['LookupHitOut'];
export type LookupStatus = Schemas['LookupStatus'];

// ---- content search (spec 004)
export type SearchResponse = Schemas['SearchOut'];
export type SearchResult = Schemas['SearchResultOut'];
export type SearchSegment = Schemas['SegmentOut'];
export type SearchMatchedPassage = Schemas['MatchedPassageOut'];
export type SearchFacet = Schemas['SearchFacetOut'];
export type SearchDegradedReason = SearchResponse['degraded'][number];
export type SearchVia = SearchResult['via'][number];
