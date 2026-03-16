/**
 * File/blob download transport adapter.
 *
 * Owns: blob download with retry, browser download trigger.
 * Uses auth middleware for header injection, transport for error helpers.
 */

import { DOWNLOAD_TIMEOUT } from '@/utils/constants'

import type { ApiRequestOptions } from '@/utils/transport'
import {
  isRetryableError,
  parseApiError,
  getStatusMessage,
  buildUrl,
  BASE_RETRY_DELAY,
  IDEMPOTENT_METHODS,
  MAX_RETRIES,
} from '@/utils/transport'
import { injectAuthHeaders, CSRF_METHODS } from '@/utils/authMiddleware'

/**
 * Download a file from an API endpoint.
 */
export async function apiDownload(
  endpoint: string,
  token: string | null,
  options: ApiRequestOptions = {}
): Promise<{ blob?: Blob; filename?: string; error?: string; ok: boolean }> {
  const {
    method = 'GET',
    body,
    headers: customHeaders = {},
    timeout = DOWNLOAD_TIMEOUT,
    retries = IDEMPOTENT_METHODS.has(options.method ?? 'GET') ? MAX_RETRIES : 0,
    idempotencyKey,
  } = options;

  const headers: Record<string, string> = {
    ...customHeaders,
  };

  injectAuthHeaders(headers, token, method, idempotencyKey);

  let requestBody: string | FormData | undefined;
  if (body) {
    if (body instanceof FormData) {
      requestBody = body;
    } else {
      headers['Content-Type'] = 'application/json';
      requestBody = JSON.stringify(body);
    }
  }

  const url = buildUrl(endpoint);

  let lastError: string | undefined;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(url, {
        method,
        headers,
        body: requestBody,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        lastError = getStatusMessage(response.status);

        if (!isRetryableError(response.status)) {
          return { error: lastError, ok: false };
        }

        if (attempt < retries) {
          const delay = BASE_RETRY_DELAY * Math.pow(2, attempt);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }

        return { error: lastError, ok: false };
      }

      let filename: string | undefined;
      const contentDisposition = response.headers.get('Content-Disposition');
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^";\n]+)"?/);
        if (match) {
          filename = match[1];
        }
      }

      const blob = await response.blob();
      return { blob, filename, ok: true };
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        lastError = 'Download timed out';
      } else {
        lastError = parseApiError(err, 'Download failed');
      }

      if (attempt < retries) {
        const delay = BASE_RETRY_DELAY * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
    }
  }

  return { error: lastError, ok: false };
}

/**
 * Trigger a browser download for a blob.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';

  document.body.appendChild(link);
  link.click();

  setTimeout(() => {
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }, 100);
}
