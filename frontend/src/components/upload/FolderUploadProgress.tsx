import { CheckCircle2, XCircle, Clock, Loader2, Download, Archive } from 'lucide-react';
import type { FileStatus } from './UploadProgress';

export interface FolderFileEntry {
  id: string;
  file: File;
  relativePath: string;
  status: FileStatus;
  progress: number;
  error?: string;
}

interface FolderUploadProgressProps {
  files: FolderFileEntry[];
  onDownloadArchive: () => void;
  isDownloading?: boolean;
  downloadReady?: boolean;
}

const statusConfig: Record<FileStatus, { icon: React.ReactNode; label: string; color: string }> = {
  queued: {
    icon: <Clock className="h-4 w-4" />,
    label: 'În așteptare',
    color: 'text-gray-500',
  },
  uploading: {
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
    label: 'Se încarcă',
    color: 'text-blue-600',
  },
  processing: {
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
    label: 'Se procesează',
    color: 'text-amber-600',
  },
  done: {
    icon: <CheckCircle2 className="h-4 w-4" />,
    label: 'Finalizat',
    color: 'text-green-600',
  },
  error: {
    icon: <XCircle className="h-4 w-4" />,
    label: 'Eroare',
    color: 'text-red-600',
  },
};

function OverallProgressBar({ done, total }: { done: number; total: number }) {
  const percent = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-gray-700">
          Progres: {done} din {total} fișiere procesate
        </span>
        <span className="text-gray-500">{percent}%</span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-300"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

function CompletionSummary({ succeeded, failed }: { succeeded: number; failed: number }) {
  return (
    <div className="flex items-center gap-4 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
      <div className="flex items-center gap-1.5">
        <CheckCircle2 className="h-4 w-4 text-green-600" />
        <span className="text-sm font-medium text-green-700">{succeeded} reușite</span>
      </div>
      {failed > 0 && (
        <div className="flex items-center gap-1.5">
          <XCircle className="h-4 w-4 text-red-600" />
          <span className="text-sm font-medium text-red-700">{failed} eșuate</span>
        </div>
      )}
    </div>
  );
}

export default function FolderUploadProgress({
  files,
  onDownloadArchive,
  isDownloading = false,
  downloadReady = false,
}: FolderUploadProgressProps) {
  if (files.length === 0) return null;

  const doneCount = files.filter((f) => f.status === 'done' || f.status === 'error').length;
  const succeeded = files.filter((f) => f.status === 'done').length;
  const failed = files.filter((f) => f.status === 'error').length;
  const allFinished = doneCount === files.length;

  return (
    <div className="space-y-4">
      <OverallProgressBar done={doneCount} total={files.length} />

      {allFinished && (
        <>
          <CompletionSummary succeeded={succeeded} failed={failed} />

          <button
            onClick={onDownloadArchive}
            disabled={isDownloading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isDownloading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Se descarcă arhiva...
              </>
            ) : downloadReady ? (
              <>
                <Download className="h-5 w-5" />
                Descarcă Arhiva ZIP
              </>
            ) : (
              <>
                <Archive className="h-5 w-5" />
                Descarcă Arhiva ZIP
              </>
            )}
          </button>
        </>
      )}

      <div className="space-y-1">
        <h3 className="text-sm font-medium text-gray-700">
          Fișiere ({files.length})
        </h3>
        <div className="max-h-80 divide-y divide-gray-100 overflow-y-auto rounded-lg border border-gray-200 bg-white">
          {files.map((entry) => {
            const config = statusConfig[entry.status];
            const percent =
              entry.status === 'done'
                ? 100
                : entry.status === 'processing'
                  ? 95
                  : entry.progress;

            return (
              <div key={entry.id} className="px-4 py-3 space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className={`flex-shrink-0 ${config.color}`}>{config.icon}</span>
                    <span className="truncate text-sm text-gray-800" title={entry.relativePath}>
                      {entry.relativePath}
                    </span>
                    <span className={`flex-shrink-0 text-xs ${config.color}`}>{config.label}</span>
                  </div>
                  <span className="ml-2 text-xs text-gray-500 flex-shrink-0">{percent}%</span>
                </div>

                <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-200">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      entry.status === 'error'
                        ? 'bg-red-500'
                        : entry.status === 'done'
                          ? 'bg-green-500'
                          : entry.status === 'processing'
                            ? 'bg-amber-500'
                            : 'bg-blue-500'
                    }`}
                    style={{ width: `${percent}%` }}
                  />
                </div>

                {entry.status === 'error' && entry.error && (
                  <span className="text-xs text-red-600">{entry.error}</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
