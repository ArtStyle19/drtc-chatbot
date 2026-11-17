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

/** Turns any error into a short Spanish message that is safe to show to the user. */
export function toUserMessage(error: unknown): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) {
      return 'No se pudo conectar con el servidor. Verifique su conexión e intente nuevamente.';
    }
    const problem = error.error as ProblemDetails | null;
    if (problem && typeof problem.detail === 'string' && problem.detail.trim()) {
      return problem.detail;
    }
    return `El servidor respondió con un error (${error.status}). Intente nuevamente.`;
  }
  return 'Ocurrió un error inesperado. Intente nuevamente.';
}
