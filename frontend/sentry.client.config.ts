/**
 * Sentry Client-side Configuration
 * Sprint 275: APM Integration (Zero-Storage compliant)
 *
 * Initialized only when NEXT_PUBLIC_SENTRY_DSN is set.
 * No session replays, no PII, no request bodies.
 */
import * as Sentry from "@sentry/nextjs";

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    environment: process.env.NODE_ENV,

    // Performance monitoring — sample 10% of transactions
    tracesSampleRate: parseFloat(
      process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || "0.1"
    ),

    // Zero-Storage compliance: no session replays
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0,

    // No PII collection
    sendDefaultPii: false,

    // Strip request bodies before sending
    beforeSend(event) {
      if (event.request?.data) {
        event.request.data = "[Stripped — Zero-Storage]";
      }
      return event;
    },

    // Strip URL query params from breadcrumbs (engagement/client IDs)
    beforeBreadcrumb(breadcrumb) {
      if (
        (breadcrumb.category === "xhr" || breadcrumb.category === "fetch") &&
        breadcrumb.data?.url
      ) {
        const url = breadcrumb.data.url as string;
        const qIdx = url.indexOf("?");
        if (qIdx !== -1) {
          breadcrumb.data.url = url.slice(0, qIdx);
        }
      }
      return breadcrumb;
    },
  });
}
