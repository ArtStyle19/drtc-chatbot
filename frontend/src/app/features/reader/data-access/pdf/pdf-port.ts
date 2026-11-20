import { inject, InjectionToken } from '@angular/core';

import { TextBox } from '../../../../core/api/models';
import { PdfJsLoader } from './pdfjs-loader';

/** A rectangle in CSS pixels, relative to the top-left corner of the rendered page. */
export interface PageRect {
  readonly left: number;
  readonly top: number;
  readonly width: number;
  readonly height: number;
}

export interface RenderedPage {
  readonly cssWidth: number;
  readonly cssHeight: number;
  /** Converts a text box (PDF points, origin bottom-left) to CSS pixels on this rendering. */
  toRect(box: TextBox): PageRect;
}

export interface PdfDocument {
  readonly numPages: number;
  /** Draws `page` into `canvas` so that it is `cssWidth` CSS pixels wide. Rejects with AbortError. */
  render(
    page: number,
    canvas: HTMLCanvasElement,
    cssWidth: number,
    signal: AbortSignal,
  ): Promise<RenderedPage>;
  destroy(): void;
}

/** Opens PDFs. The only place that knows about pdf.js; components and tests use this port. */
export interface PdfLoader {
  open(url: string, signal: AbortSignal): Promise<PdfDocument>;
}

export const PDF_LOADER = new InjectionToken<PdfLoader>('PDF_LOADER', {
  providedIn: 'root',
  factory: () => inject(PdfJsLoader),
});

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}
