import rateLimit from 'express-rate-limit';

/**
 * Brute-force protection for authentication endpoints.
 * 5 attempts per IP per minute; success counts are skipped so a real user
 * who just typed their password right doesn't get punished by earlier typos.
 */
export const authLimiter = rateLimit({
  windowMs: 60 * 1000,
  limit: 5,
  standardHeaders: 'draft-7',
  legacyHeaders: false,
  skipSuccessfulRequests: true,
  message: {
    error: {
      name: 'RateLimitError',
      message: 'Prea multe încercări. Așteaptă un minut și reîncearcă.',
      code: 'RATE_LIMIT',
    },
  },
});

/**
 * Global API limiter — coarse-grained abuse guard in front of every /api route.
 * 2000 requests per IP per minute. Sized generously because the frontend can
 * legitimately burst-fire hundreds of parallel detail fetches — AlertsPage
 * calls `useDocumentDetails(allIds)` across every document to compute the
 * expiration/review tabs, and DocumentsPage pre-fetches every extraction on
 * Excel export. With ~300 documents, the old 100/min cap truncated the bulk
 * fetches and left rows blank. Behind Cloudflare + JWT auth, brute abuse is
 * already constrained; this limiter is a secondary safety net, not the
 * primary boundary.
 */
export const apiLimiter = rateLimit({
  windowMs: 60 * 1000,
  limit: 2000,
  standardHeaders: 'draft-7',
  legacyHeaders: false,
  message: {
    error: {
      name: 'RateLimitError',
      message: 'Prea multe cereri. Așteaptă un minut și reîncearcă.',
      code: 'RATE_LIMIT',
    },
  },
});
