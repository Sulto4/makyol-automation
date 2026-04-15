import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileWarning } from 'lucide-react';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

interface UploadDropzoneProps {
  onFilesAccepted: (files: File[]) => void;
  disabled?: boolean;
}

export default function UploadDropzone({ onFilesAccepted, disabled }: UploadDropzoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const valid = acceptedFiles.filter((f) => f.size <= MAX_FILE_SIZE);
      if (valid.length > 0) {
        onFilesAccepted(valid);
      }
    },
    [onFilesAccepted],
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
    disabled,
    maxSize: MAX_FILE_SIZE,
  });

  const oversized = fileRejections.filter((r) =>
    r.errors.some((e) => e.code === 'file-too-large'),
  );

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
        <input {...getInputProps()} />
        <Upload
          className={`mb-3 h-10 w-10 ${isDragActive ? 'text-blue-500 dark:text-blue-400' : 'text-gray-400 dark:text-gray-500'}`}
        />
        {isDragActive ? (
          <p className="text-lg font-medium text-blue-600 dark:text-blue-400">Eliberați fișierele aici...</p>
        ) : (
          <>
            <p className="text-lg font-medium text-gray-700 dark:text-gray-200">
              Trageți fișierele PDF aici
            </p>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              sau apăsați pentru a selecta fișiere (max. 10MB per fișier)
            </p>
          </>
        )}
      </div>

      {oversized.length > 0 && (
        <div className="flex items-start gap-2 rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          <FileWarning className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <div>
            <p className="font-medium">Fișiere respinse (depășesc 10MB):</p>
            <ul className="mt-1 list-inside list-disc">
              {oversized.map((r) => (
                <li key={r.file.name}>{r.file.name}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
