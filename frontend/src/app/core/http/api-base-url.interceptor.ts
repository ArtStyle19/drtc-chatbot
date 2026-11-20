import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { RUNTIME_CONFIG } from '../config/runtime-config';
import { resolveApiUrl } from './api-url';

/** Prefixes relative `/api/...` calls with the configured backend base URL. */
export const apiBaseUrlInterceptor: HttpInterceptorFn = (request, next) => {
  const url = resolveApiUrl(request.url, inject(RUNTIME_CONFIG).apiBaseUrl);
  return next(url === request.url ? request : request.clone({ url }));
};
