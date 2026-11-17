import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { BrowserSession } from '../session/browser-session';

/** Sends the anonymous browser session id to our own API (never to third parties). */
export const sessionIdInterceptor: HttpInterceptorFn = (request, next) => {
  if (!request.url.includes('/api/')) {
    return next(request);
  }
  const sessionId = inject(BrowserSession).id();
  return next(sessionId ? request.clone({ setHeaders: { 'X-Session-Id': sessionId } }) : request);
};
