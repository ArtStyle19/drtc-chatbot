import { registerLocaleData } from '@angular/common';
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import localeEsPe from '@angular/common/locales/es-PE';
import { ApplicationConfig, LOCALE_ID, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter, withComponentInputBinding, withInMemoryScrolling } from '@angular/router';

import { routes } from './app.routes';
import {
  DEFAULT_RUNTIME_CONFIG,
  RUNTIME_CONFIG,
  RuntimeConfig,
} from './core/config/runtime-config';
import { apiBaseUrlInterceptor } from './core/http/api-base-url.interceptor';
import { sessionIdInterceptor } from './core/http/session-id.interceptor';

registerLocaleData(localeEsPe);

export function createAppConfig(
  runtimeConfig: RuntimeConfig = DEFAULT_RUNTIME_CONFIG,
): ApplicationConfig {
  return {
    providers: [
      provideBrowserGlobalErrorListeners(),
      provideRouter(
        routes,
        withComponentInputBinding(),
        withInMemoryScrolling({ scrollPositionRestoration: 'enabled' }),
      ),
      provideHttpClient(
        withFetch(),
        withInterceptors([apiBaseUrlInterceptor, sessionIdInterceptor]),
      ),
      { provide: LOCALE_ID, useValue: 'es-PE' },
      { provide: RUNTIME_CONFIG, useValue: runtimeConfig },
    ],
  };
}
