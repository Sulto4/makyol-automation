import { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { FileText, File, FolderOpen } from 'lucide-react';
import toast from 'react-hot-toast';
import UploadDropzone from '../components/upload/UploadDropzone';
import UploadProgress from '../components/upload/UploadProgress';
import type { FileEntry } from '../components/upload/UploadProgress';
import FolderUploadDropzone from '../components/upload/FolderUploadDropzone';
import FolderUploadProgress from '../components/upload/FolderUploadProgress';
import type { FolderFileEntry } from '../components/upload/FolderUploadProgress';
import { useUpload, useFolderUpload } from '../hooks/useUpload';
import type { FolderUploadFile } from '../types';

type UploadMode = 'files' | 'folder';

let fileIdCounter = 0;
let folderFileIdCounter = 0;

export default function UploadPage() {
  const [mode, setMode] = useState<UploadMode>('files');

  // --- Single-file upload state (unchanged) ---
  const [files, setFiles] = useState<FileEntry[]>([]);
  const { mutateAsync, progress } = useUpload();

  const processFile = useCallback(
    async (entry: FileEntry) => {
      const updateEntry = (patch: Partial<FileEntry>) =>
        setFiles((prev) => prev.map((f) => (f.id === entry.id ? { ...f, ...patch } : f)));

      updateEntry({ status: 'uploading' });

      try {
        const result = await mutateAsync(entry.file);
        updateEntry({ status: 'done', progress: 100, result });
        toast.success(`${entry.file.name} încărcat cu succes`);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Eroare la încărcare';
        updateEntry({ status: 'error', error: message });
        toast.error(`Eroare: ${entry.file.name}`);
      }
    },
    [mutateAsync],
  );

  const handleFilesAccepted = useCallback(
    (accepted: File[]) => {
      const newEntries: FileEntry[] = accepted.map((file) => ({
        id: `file-${++fileIdCounter}`,
        file,
        status: 'queued' as const,
        progress: 0,
      }));

      setFiles((prev) => [...prev, ...newEntries]);

      newEntries.reduce<Promise<void>>(
        (chain, entry) => chain.then(() => processFile(entry)),
        Promise.resolve(),
      );
    },
    [processFile],
  );

  const handleRetry = useCallback(
    (id: string) => {
      const entry = files.find((f) => f.id === id);
      if (entry) {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === id ? { ...f, status: 'queued' as const, progress: 0, error: undefined } : f,
          ),
        );
        processFile({ ...entry, status: 'queued', progress: 0, error: undefined });
      }
    },
    [files, processFile],
  );

  const uploading = files.find((f) => f.status === 'uploading');
  const filesWithProgress = files.map((f) =>
    f.id === uploading?.id ? { ...f, progress } : f,
  );

  // --- Folder upload state ---
  const [folderFiles, setFolderFiles] = useState<FolderFileEntry[]>([]);
  const [isDownloading, setIsDownloading] = useState(false);
  const {
    mutateAsync: mutateFolder,
    progress: folderProgress,
    downloadArchive,
    isPending: isFolderProcessing,
    isSuccess: isFolderDone,
  } = useFolderUpload();

  const handleFolderSelected = useCallback(
    async (selected: FolderUploadFile[]) => {
      const entries: FolderFileEntry[] = selected.map((f) => ({
        id: `folder-file-${++folderFileIdCounter}`,
        file: f.file,
        relativePath: f.relativePath,
        status: 'queued' as const,
        progress: 0,
      }));

      setFolderFiles(entries);

      setFolderFiles((prev) => prev.map((f) => ({ ...f, status: 'uploading' as const })));

      try {
        const result = await mutateFolder(
          selected.map((f) => ({ file: f.file, relativePath: f.relativePath })),
        );

        setFolderFiles((prev) =>
          prev.map((f) => {
            const match = result.results.find(
              (r) => r.relativePath === f.relativePath,
            );
            if (match && match.success) {
              return { ...f, status: 'done' as const, progress: 100 };
            }
            return {
              ...f,
              status: 'error' as const,
              error: match?.error ?? 'Eroare necunoscută',
            };
          }),
        );

        toast.success(
          `Folder procesat: ${result.totalProcessed - result.totalFailed} reușite, ${result.totalFailed} erori`,
        );
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Eroare la procesare folder';
        setFolderFiles((prev) =>
          prev.map((f) => ({ ...f, status: 'error' as const, error: message })),
        );
        toast.error('Eroare la procesarea folderului');
      }
    },
    [mutateFolder],
  );

  const handleDownloadArchive = useCallback(async () => {
    setIsDownloading(true);
    try {
      await downloadArchive();
    } finally {
      setIsDownloading(false);
    }
  }, [downloadArchive]);

  const folderFilesWithProgress = folderFiles.map((f) =>
    f.status === 'uploading' ? { ...f, progress: folderProgress } : f,
  );

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Încărcare documente</h1>
        <Link
          to="/documents"
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          <FileText className="h-4 w-4" />
          Vezi toate documentele
        </Link>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
        <button
          type="button"
          onClick={() => setMode('files')}
          className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            mode === 'files'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <File className="h-4 w-4" />
          Fișiere
        </button>
        <button
          type="button"
          onClick={() => setMode('folder')}
          className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            mode === 'folder'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <FolderOpen className="h-4 w-4" />
          Folder
        </button>
      </div>

      {mode === 'files' ? (
        <>
          <UploadDropzone
            onFilesAccepted={handleFilesAccepted}
            disabled={!!uploading}
          />
          <UploadProgress files={filesWithProgress} onRetry={handleRetry} />
        </>
      ) : (
        <>
          <FolderUploadDropzone
            onFolderSelected={handleFolderSelected}
            disabled={isFolderProcessing}
          />
          <FolderUploadProgress
            files={folderFilesWithProgress}
            onDownloadArchive={handleDownloadArchive}
            isDownloading={isDownloading}
            downloadReady={isFolderDone}
          />
        </>
      )}
    </div>
  );
}
