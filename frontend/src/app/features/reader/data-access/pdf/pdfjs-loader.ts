import { Service } from '@angular/core';
import type { PDFDocumentProxy } from 'pdfjs-dist';

import { TextBox } from '../../../../core/api/models';
import type { PdfDocument, PdfLoader, RenderedPage } from './pdf-port';

/** Where the build copies the pdf.js worker and data files (see `assets` in angular.json). */
function asset(path: string): string {
  return new URL(`pdfjs/${path}`, document.baseURI).toString();
}

const RANGE_CHUNK_BYTES = 64 * 1024;

function abortError(): DOMException {
  return new DOMException('The rendering was cancelled', 'AbortError');
}

class PdfJsDocument implements PdfDocument {
  /** pdf.js cannot draw twice on one canvas at once: renders run one after another. */
  private queue: Promise<unknown> = Promise.resolve();

  constructor(private readonly doc: PDFDocumentProxy) {}

  get numPages(): number {
    return this.doc.numPages;
  }

  render(
    page: number,
    canvas: HTMLCanvasElement,
    cssWidth: number,
    signal: AbortSignal,
  ): Promise<RenderedPage> {
    const run = this.queue.then(() => this.draw(page, canvas, cssWidth, signal));
    this.queue = run.catch(() => undefined);
    return run;
  }

  destroy(): void {
    void this.doc.loadingTask.destroy();
  }

  private async draw(
    page: number,
    canvas: HTMLCanvasElement,
    cssWidth: number,
    signal: AbortSignal,
  ): Promise<RenderedPage> {
    if (signal.aborted) throw abortError();
    const proxy = await this.doc.getPage(page);
    if (signal.aborted) throw abortError();
    const natural = proxy.getViewport({ scale: 1 });
    const scale = cssWidth / natural.width;
    const pixelRatio = window.devicePixelRatio || 1;
    const css = proxy.getViewport({ scale });
    const device = proxy.getViewport({ scale: scale * pixelRatio });
    canvas.width = Math.floor(device.width);
    canvas.height = Math.floor(device.height);
    canvas.style.width = `${css.width}px`;
    canvas.style.height = `${css.height}px`;
    const task = proxy.render({ canvas, viewport: device });
    const cancel = (): void => task.cancel();
    signal.addEventListener('abort', cancel, { once: true });
    try {
      await task.promise;
    } catch (error: unknown) {
      if (signal.aborted) throw abortError();
      throw error;
    } finally {
      signal.removeEventListener('abort', cancel);
      proxy.cleanup();
    }
    return {
      cssWidth: css.width,
      cssHeight: css.height,
      toRect: (box: TextBox) => {
        const [ax, ay] = css.convertToViewportPoint(box.x0, box.y0) as [number, number];
        const [bx, by] = css.convertToViewportPoint(box.x1, box.y1) as [number, number];
        return {
          left: Math.min(ax, bx),
          top: Math.min(ay, by),
          width: Math.abs(bx - ax),
          height: Math.abs(by - ay),
        };
      },
    };
  }
}

/**
 * pdf.js adapter. The library is loaded on demand (it is large and only the reader needs it), the
 * worker runs off the main thread, and only the byte ranges of the pages being shown are fetched.
 */
@Service()
export class PdfJsLoader implements PdfLoader {
  async open(url: string, signal: AbortSignal): Promise<PdfDocument> {
    const pdfjs = await import('pdfjs-dist');
    pdfjs.GlobalWorkerOptions.workerSrc = asset('pdf.worker.min.mjs');
    const task = pdfjs.getDocument({
      url,
      rangeChunkSize: RANGE_CHUNK_BYTES,
      // Only the byte ranges of the pages shown are downloaded. Both flags are needed: with streaming
      // on, pdf.js keeps reading the whole file from its first request even if auto-fetch is off.
      disableStream: true,
      disableAutoFetch: true,
      standardFontDataUrl: asset('standard_fonts/'),
      wasmUrl: asset('wasm/'),
    });
    const cancel = (): void => void task.destroy();
    signal.addEventListener('abort', cancel, { once: true });
    try {
      return new PdfJsDocument(await task.promise);
    } catch (error: unknown) {
      if (signal.aborted) throw abortError();
      throw error;
    } finally {
      signal.removeEventListener('abort', cancel);
    }
  }
}
