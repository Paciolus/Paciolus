/**
 * Sentry Server-side Configuration
 * Sprint 275: APM Integration (Zero-Storage compliant)
 *
 * Initialized only when NEXT_PUBLIC_SENTRY_DSN is set.
 * No PII, no request bodies.
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

    // No PII collection
    sendDefaultPii: false,

    // Strip request bodies before sending
    beforeSend(event) {
      if (event.request?.data) {
        event.request.data = "[Stripped — Zero-Storage]";
      }
      return event;
    },
  });
}
