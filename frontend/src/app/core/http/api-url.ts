/**
 * Resolves a server-relative URL (`/api/...`) against the configured backend base URL. Needed for
 * requests that do not go through Angular's HttpClient (pdf.js downloads the PDF itself).
 * Absolute URLs and non-API paths are returned untouched.
 */
export function resolveApiUrl(url: string, apiBaseUrl: string): string {
  if (!apiBaseUrl || !url.startsWith('/api/')) return url;
  return `${apiBaseUrl.replace(/\/+$/, '')}${url}`;
}
