import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { FolderOpen, FileWarning } from 'lucide-react';
import type { FolderUploadFile } from '../../types';

interface FolderUploadDropzoneProps {
  onFolderSelected: (files: FolderUploadFile[]) => void;
  disabled?: boolean;
}

export default function FolderUploadDropzone({ onFolderSelected, disabled }: FolderUploadDropzoneProps) {
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setError(null);

      const pdfFiles = acceptedFiles.filter(
        (f) => f.name.toLowerCase().endsWith('.pdf'),
      );

      if (pdfFiles.length === 0) {
        setError('Nu s-au găsit fișiere PDF în folderul selectat.');
        return;
      }

      const folderFiles: FolderUploadFile[] = pdfFiles.map((file) => {
        // On drop: react-dropzone sets file.path = '/Folder/sub/file.pdf' (leading slash)
        // On click with webkitdirectory: webkitRelativePath = 'Folder/sub/file.pdf'
        const droppedPath = (file as any).path as string | undefined;
        const webkitPath = (file as any).webkitRelativePath as string | undefined;
        const fullPath = (droppedPath ?? webkitPath ?? file.name).replace(/^\/+/, '');
        // Strip root folder name: 'MyFolder/sub/file.pdf' → 'sub/file.pdf'
        const parts = fullPath.split('/');
        const relativePath = parts.length > 1 ? parts.slice(1).join('/') : parts[0];
        return { file, relativePath };
      });

      onFolderSelected(folderFiles);
    },
    [onFolderSelected],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
    disabled,
    useFsAccessApi: false,
  });

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 text-center transition-colors cursor-pointer ${
          isDragActive
            ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-950'
            : disabled
              ? 'border-gray-200 bg-gray-50 cursor-not-allowed dark:border-gray-700 dark:bg-gray-800'
              : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:hover:border-blue-500 dark:hover:bg-gray-700'
        }`}
      >
        <input {...getInputProps({ webkitdirectory: 'true' } as any)} />
        <FolderOpen
          className={`mb-3 h-10 w-10 ${isDragActive ? 'text-blue-500 dark:text-blue-400' : 'text-gray-400 dark:text-gray-500'}`}
        />
        {isDragActive ? (
          <p className="text-lg font-medium text-blue-600 dark:text-blue-400">
            Eliberați folderul aici...
          </p>
        ) : (
          <>
            <p className="text-lg font-medium text-gray-700 dark:text-gray-200">
              Trageți un folder aici sau apăsați pentru a selecta
            </p>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Toate fișierele PDF din folder (inclusiv subfoldere) vor fi procesate
            </p>
          </>
        )}
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          <FileWarning className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <p className="font-medium">{error}</p>
        </div>
      )}
    </div>
  );
}
