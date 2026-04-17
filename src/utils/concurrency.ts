/**
 * Bounded concurrency primitives.
 *
 * We want to process N items but never run more than `limit` of them at a
 * time. Node.js is single-threaded but async, so this is purely a way to
 * throttle outstanding async calls — avoiding e.g. slamming the pipeline
 * service with a 300-item Promise.all.
 */

/**
 * Returns a function that wraps promise-returning tasks and caps how many
 * are in flight at once. Tasks beyond the cap queue FIFO.
 *
 *     const limit = createLimiter(3);
 *     const results = await Promise.all(items.map(it => limit(() => work(it))));
 *
 * Each `limit(fn)` call returns a promise that resolves (or rejects) with
 * whatever `fn` resolves to — same semantics as calling fn() directly,
 * just rate-limited.
 */
export function createLimiter(limit: number): <T>(fn: () => Promise<T>) => Promise<T> {
  if (!Number.isInteger(limit) || limit < 1) {
    throw new Error(`createLimiter: limit must be a positive integer, got ${limit}`);
  }

  let active = 0;
  const queue: Array<() => void> = [];

  const next = () => {
    if (active >= limit) return;
    const run = queue.shift();
    if (!run) return;
    active++;
    run();
  };

  return <T>(fn: () => Promise<T>): Promise<T> => {
    return new Promise<T>((resolve, reject) => {
      const run = () => {
        fn()
          .then(resolve, reject)
          .finally(() => {
            active--;
            next();
          });
      };
      queue.push(run);
      next();
    });
  };
}
