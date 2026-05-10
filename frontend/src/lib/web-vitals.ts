"use client";

/**
 * Web Vitals Reporting.
 *
 * Reports Core Web Vitals (LCP, FID, CLS, TTFB, INP) to:
 * - Console (development)
 * - Analytics endpoint (production)
 *
 * Integrates with Next.js reportWebVitals callback.
 */

import { type Metric, onCLS, onFID, onLCP, onTTFB, onINP } from "web-vitals";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

interface VitalsPayload {
  name: string;
  value: number;
  rating: string;
  delta: number;
  id: string;
  navigationType: string;
  url: string;
}

/**
 * Send vital metric to analytics endpoint.
 */
function sendToAnalytics(metric: Metric): void {
  const payload: VitalsPayload = {
    name: metric.name,
    value: metric.value,
    rating: metric.rating,
    delta: metric.delta,
    id: metric.id,
    navigationType: metric.navigationType,
    url: window.location.pathname,
  };

  // In development, log to console
  if (process.env.NODE_ENV === "development") {
    console.log(`[Web Vital] ${metric.name}:`, {
      value: Math.round(metric.value * 100) / 100,
      rating: metric.rating,
    });
    return;
  }

  // In production, send to analytics endpoint (using sendBeacon for reliability)
  const body = JSON.stringify(payload);

  if (navigator.sendBeacon) {
    navigator.sendBeacon(`${API_URL}/api/v1/analytics/vitals`, body);
  } else {
    fetch(`${API_URL}/api/v1/analytics/vitals`, {
      method: "POST",
      body,
      headers: { "Content-Type": "application/json" },
      keepalive: true,
    });
  }
}

/**
 * Initialize Web Vitals measurement.
 * Call once in the root layout (client component).
 */
export function initWebVitals(): void {
  try {
    onCLS(sendToAnalytics);
    onFID(sendToAnalytics);
    onLCP(sendToAnalytics);
    onTTFB(sendToAnalytics);
    onINP(sendToAnalytics);
  } catch {
    // web-vitals may not be supported in all environments
  }
}

/**
 * Component that initializes Web Vitals on mount.
 */
export function WebVitalsReporter(): null {
  if (typeof window !== "undefined") {
    initWebVitals();
  }
  return null;
}
