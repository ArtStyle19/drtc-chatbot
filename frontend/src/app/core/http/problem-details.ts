import { HttpErrorResponse } from '@angular/common/http';

/** RFC 9457 problem details as returned by the backend (`application/problem+json`). */
export interface ProblemDetails {
  readonly type?: string;
  readonly title?: string;
  readonly status?: number;
  readonly detail?: string | null;
  readonly code?: string;
  readonly request_id?: string | null;
}

/** Codes whose `detail` is already a Spanish sentence meant for people (see backend errors.py). */
const USER_FACING_CODES = new Set(['validation_error', 'internal_error', 'integrity_violation']);

export interface MessageOptions {
  /** What a 404 means in the current screen, e.g. "No encontramos esa disposición.". */
  readonly notFound?: string;
}

/**
 * Turns any error into a short Spanish message that is safe to show to the user. Technical English
 * `detail` strings from the API are never shown: the message depends on the situation instead.
 */
export function toUserMessage(error: unknown, options: MessageOptions = {}): string {
  if (!(error instanceof HttpErrorResponse)) {
    return 'Ocurrió un error inesperado. Intente nuevamente.';
  }
  if (error.status === 0) {
    return 'No se pudo conectar con el servidor. Verifique su conexión e intente nuevamente.';
  }
  const problem = error.error as ProblemDetails | null;
  if (problem?.code && USER_FACING_CODES.has(problem.code) && problem.detail?.trim()) {
    return problem.detail;
  }
  if (error.status === 404) {
    return options.notFound ?? 'No se encontró lo solicitado.';
  }
  const reference = problem?.request_id ? ` (código ${problem.request_id.slice(0, 8)})` : '';
  return error.status >= 500
    ? `El servidor tuvo un problema. Intente nuevamente o avise al equipo técnico${reference}.`
    : `No se pudo completar la solicitud${reference}. Intente nuevamente.`;
}
