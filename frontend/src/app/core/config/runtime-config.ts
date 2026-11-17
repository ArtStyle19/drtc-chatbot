import { InjectionToken } from '@angular/core';

/**
 * Configuration read at startup from `/config.json`, so the same build can be deployed to any
 * environment (the file is replaced at deploy time, never rebuilt).
 */
export interface RuntimeConfig {
  /** Base URL of the backend. Empty string = same origin (reverse proxy or dev proxy). */
  readonly apiBaseUrl: string;
}

export const DEFAULT_RUNTIME_CONFIG: RuntimeConfig = { apiBaseUrl: '' };

export const RUNTIME_CONFIG = new InjectionToken<RuntimeConfig>('RUNTIME_CONFIG', {
  providedIn: 'root',
  factory: () => DEFAULT_RUNTIME_CONFIG,
});

export async function loadRuntimeConfig(fetchFn: typeof fetch = fetch): Promise<RuntimeConfig> {
  try {
    const response = await fetchFn('config.json', { cache: 'no-store' });
    if (!response.ok) {
      return DEFAULT_RUNTIME_CONFIG;
    }
    const raw = (await response.json()) as Partial<Record<keyof RuntimeConfig, unknown>>;
    const apiBaseUrl = typeof raw.apiBaseUrl === 'string' ? raw.apiBaseUrl.replace(/\/+$/, '') : '';
    return { apiBaseUrl };
  } catch {
    return DEFAULT_RUNTIME_CONFIG;
  }
}
