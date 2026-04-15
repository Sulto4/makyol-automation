import { RefreshCw, CheckCircle2, XCircle, Clock, Loader2 } from 'lucide-react';
import CategoryBadge from '../documents/CategoryBadge';
import ConfidenceBar from '../documents/ConfidenceBar';
import type { UploadResponse } from '../../types';

export type FileStatus = 'queued' | 'uploading' | 'processing' | 'done' | 'error';

export interface FileEntry {
  id: string;
  file: File;
  status: FileStatus;
  progress: number;
  result?: UploadResponse;
  error?: string;
}

interface UploadProgressProps {
  files: FileEntry[];
  onRetry: (id: string) => void;
}

const statusConfig: Record<FileStatus, { icon: React.ReactNode; label: string; color: string }> = {
  queued: {
    icon: <Clock className="h-4 w-4" />,
    label: 'În așteptare',
    color: 'text-gray-500 dark:text-gray-400',
  },
  uploading: {
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
    label: 'Se încarcă',
    color: 'text-blue-600 dark:text-blue-400',
  },
  processing: {
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
    label: 'Se procesează',
    color: 'text-amber-600 dark:text-amber-400',
  },
  done: {
    icon: <CheckCircle2 className="h-4 w-4" />,
    label: 'Finalizat',
    color: 'text-green-600 dark:text-green-400',
  },
  error: {
    icon: <XCircle className="h-4 w-4" />,
    label: 'Eroare',
    color: 'text-red-600 dark:text-red-400',
  },
};

function ProgressBar({ percent, status }: { percent: number; status: FileStatus }) {
  const bgColor =
    status === 'error'
      ? 'bg-red-500'
      : status === 'done'
        ? 'bg-green-500'
        : status === 'processing'
          ? 'bg-amber-500'
          : 'bg-blue-500';

  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
      <div
        className={`h-full rounded-full transition-all duration-300 ${bgColor}`}
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}

export default function UploadProgress({ files, onRetry }: UploadProgressProps) {
  if (files.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
        Fișiere ({files.length})
      </h3>
      <div className="divide-y divide-gray-100 rounded-lg border border-gray-200 bg-white dark:divide-gray-700 dark:border-gray-700 dark:bg-gray-800">
        {files.map((entry) => {
          const config = statusConfig[entry.status];
          const percent =
            entry.status === 'done'
              ? 100
              : entry.status === 'processing'
                ? 95
                : entry.progress;

          return (
            <div key={entry.id} className="p-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <span className={config.color}>{config.icon}</span>
                  <span className="truncate text-sm font-medium text-gray-800 dark:text-gray-200">
                    {entry.file.name}
                  </span>
                  <span className={`text-xs ${config.color}`}>{config.label}</span>
                </div>
                <span className="ml-2 text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                  {percent}%
                </span>
              </div>

              <ProgressBar percent={percent} status={entry.status} />

              {entry.status === 'done' && entry.result && (
                <div className="flex items-center gap-3 pt-1">
                  {entry.result.document.categorie && (
                    <CategoryBadge category={entry.result.document.categorie} />
                  )}
                  {entry.result.document.confidence != null && (
                    <ConfidenceBar confidence={entry.result.document.confidence} />
                  )}
                </div>
              )}

              {entry.status === 'error' && (
                <div className="flex items-center justify-between pt-1">
                  <span className="text-xs text-red-600 dark:text-red-400">
                    {entry.error ?? 'Eroare necunoscută'}
                  </span>
                  <button
                    onClick={() => onRetry(entry.id)}
                    className="flex items-center gap-1 rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-100 transition-colors dark:bg-red-950 dark:text-red-300 dark:hover:bg-red-900"
                  >
                    <RefreshCw className="h-3 w-3" />
                    Reîncearcă
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
