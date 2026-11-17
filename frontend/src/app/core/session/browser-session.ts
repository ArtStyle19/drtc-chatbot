import { isPlatformBrowser } from '@angular/common';
import { inject, PLATFORM_ID, Service } from '@angular/core';

const STORAGE_KEY = 'drtc-chatbot.session-id';

/**
 * Anonymous per-browser identifier (random UUID, never personal data). It lets the backend group
 * an anonymous visitor's conversations while there is no login (ADR-0007). SSR-safe.
 */
@Service()
export class BrowserSession {
  private readonly platformId = inject(PLATFORM_ID);
  private cachedId: string | null = null;

  id(): string | null {
    if (!isPlatformBrowser(this.platformId)) {
      return null;
    }
    this.cachedId ??= this.readOrCreate();
    return this.cachedId;
  }

  private readOrCreate(): string {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        return stored;
      }
      const created = crypto.randomUUID();
      localStorage.setItem(STORAGE_KEY, created);
      return created;
    } catch {
      return crypto.randomUUID(); // storage blocked (private mode): keep it for this page only
    }
  }
}
