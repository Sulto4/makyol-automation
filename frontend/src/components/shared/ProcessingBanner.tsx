import { Loader2 } from 'lucide-react';
import type { Document } from '../../types';

interface ProcessingBannerProps {
  documents: Document[];
}

/**
 * Sticky banner that appears whenever any document in the provided list is
 * pending or processing. Gives the user a clear signal that a batch is
 * running and that the rows below will update live as extractions finish.
 */
export default function ProcessingBanner({ documents }: ProcessingBannerProps) {
  const inFlight = documents.filter(
    (d) => d.processing_status === 'processing' || d.processing_status === 'pending',
  );
  if (inFlight.length === 0) return null;

  const completedAfterSubmit = documents.filter(
    (d) => d.processing_status === 'completed' || d.processing_status === 'failed',
  ).length;
  const totalWatched = completedAfterSubmit + inFlight.length;

  return (
    <div
      className="flex items-center gap-3 rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm shadow-sm dark:border-blue-800 dark:bg-blue-900/30"
      role="status"
      aria-live="polite"
    >
      <Loader2 className="h-5 w-5 shrink-0 animate-spin text-blue-600 dark:text-blue-400" />
      <div className="flex-1">
        <div className="font-medium text-blue-900 dark:text-blue-200">
          Se procesează {inFlight.length} document{inFlight.length === 1 ? '' : 'e'}
          {totalWatched > inFlight.length
            ? ` (${completedAfterSubmit}/${totalWatched} finalizate)`
            : ''}
          …
        </div>
        <div className="text-xs text-blue-700 dark:text-blue-300">
          Datele extrase apar automat în tabel pe măsură ce fiecare document se termină. Nu e nevoie de refresh.
        </div>
      </div>
    </div>
  );
}
