import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { RUNTIME_CONFIG } from '../config/runtime-config';

/** Prefixes relative `/api/...` calls with the configured backend base URL. */
export const apiBaseUrlInterceptor: HttpInterceptorFn = (request, next) => {
  if (!request.url.startsWith('/api/')) {
    return next(request);
  }
  const { apiBaseUrl } = inject(RUNTIME_CONFIG);
  return next(apiBaseUrl ? request.clone({ url: `${apiBaseUrl}${request.url}` }) : request);
};
