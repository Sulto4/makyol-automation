import { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { FileText } from 'lucide-react';
import toast from 'react-hot-toast';
import UploadDropzone from '../components/upload/UploadDropzone';
import UploadProgress from '../components/upload/UploadProgress';
import type { FileEntry } from '../components/upload/UploadProgress';
import { useUpload } from '../hooks/useUpload';

let fileIdCounter = 0;

export default function UploadPage() {
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

      // Process sequentially
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

  // Sync upload progress to the currently uploading file
  const uploading = files.find((f) => f.status === 'uploading');
  const filesWithProgress = files.map((f) =>
    f.id === uploading?.id ? { ...f, progress } : f,
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

      <UploadDropzone
        onFilesAccepted={handleFilesAccepted}
        disabled={!!uploading}
      />

      <UploadProgress files={filesWithProgress} onRetry={handleRetry} />
    </div>
  );
}
