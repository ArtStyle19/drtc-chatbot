import { TextBox } from '../core/api/models';
import { PdfDocument, PdfLoader, RenderedPage } from '../features/reader/data-access/pdf/pdf-port';

export interface RenderCall {
  readonly page: number;
  readonly cssWidth: number;
}

/** A 10-page, A4-shaped fake document: points map to pixels at `cssWidth / 595`. */
export class FakePdfDocument implements PdfDocument {
  readonly renders: RenderCall[] = [];
  destroyed = false;
  constructor(readonly numPages = 10) {}

  render(
    page: number,
    _canvas: HTMLCanvasElement,
    cssWidth: number,
    signal: AbortSignal,
  ): Promise<RenderedPage> {
    if (signal.aborted) return Promise.reject(new DOMException('aborted', 'AbortError'));
    this.renders.push({ page, cssWidth });
    const k = cssWidth / 595;
    const cssHeight = 842 * k;
    return Promise.resolve({
      cssWidth,
      cssHeight,
      toRect: (box: TextBox) => ({
        left: box.x0 * k,
        top: cssHeight - box.y1 * k,
        width: (box.x1 - box.x0) * k,
        height: (box.y1 - box.y0) * k,
      }),
    });
  }

  destroy(): void {
    this.destroyed = true;
  }
}

export class FakePdfLoader implements PdfLoader {
  readonly opened: { url: string; doc: FakePdfDocument }[] = [];
  failNext = false;
  numPages = 10;

  open(url: string, signal: AbortSignal): Promise<PdfDocument> {
    if (this.failNext) {
      this.failNext = false;
      return Promise.reject(new Error('network'));
    }
    if (signal.aborted) return Promise.reject(new DOMException('aborted', 'AbortError'));
    const doc = new FakePdfDocument(this.numPages);
    this.opened.push({ url, doc });
    return Promise.resolve(doc);
  }
}
