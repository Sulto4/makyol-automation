import { useState } from 'react';
import { ChevronDown, ChevronRight, FileText, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { DocumentWithExtraction } from '../../types';
import CategoryBadge from './CategoryBadge';
import StatusBadge from './StatusBadge';
import ConfidenceBar from './ConfidenceBar';
import ExpirationWarning from '../shared/ExpirationWarning';
import RejectionModal from './RejectionModal';
import { useReviewDocument } from '../../hooks/useDocuments';
import { reprocessDocument } from '../../api/documents';
import { isRomanianAddress } from '../../utils/countryDetector';

interface DocumentDetailProps {
  data: DocumentWithExtraction;
}

export default function DocumentDetail({ data }: DocumentDetailProps) {
  const { document: doc, extraction } = data;
  const [aiExpanded, setAiExpanded] = useState(false);
  const [rejectionModalOpen, setRejectionModalOpen] = useState(false);
  const reviewMutation = useReviewDocument();
  const queryClient = useQueryClient();
  const reprocessMutation = useMutation({
    mutationFn: () => reprocessDocument(doc.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', doc.id] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast.success('Document reprocesare reușită');
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const pdfUrl = `/uploads/${doc.filename}`;

  return (
    <div className="flex h-full gap-6">
      {/* Left: PDF Viewer (60%) */}
      <div className="w-[60%] flex-shrink-0">
        <div className="h-full rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
          <iframe
            src={pdfUrl}
            title={doc.original_filename}
            className="h-full w-full rounded-lg"
            onError={(e) => {
              const target = e.currentTarget;
              target.style.display = 'none';
              target.parentElement?.querySelector('.pdf-fallback')?.classList.remove('hidden');
            }}
          />
          <div className="pdf-fallback hidden flex h-full flex-col items-center justify-center gap-3 text-gray-400 dark:text-gray-500">
            <FileText className="h-16 w-16" />
            <p className="text-lg font-medium">PDF indisponibil</p>
            <p className="text-sm">{doc.original_filename}</p>
          </div>
        </div>
      </div>

      {/* Right: Extracted Data (40%) */}
      <div className="w-[40%] overflow-y-auto space-y-4">
        {/* Document Info Card */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-gray-100">Informații Document</h3>
          <dl className="space-y-2 text-sm">
            <DataField label="Nume fișier" value={doc.original_filename} />
            <DataField label="Categorie">
              <CategoryBadge category={doc.categorie} />
            </DataField>
            <DataField label="Status procesare">
              <StatusBadge status={doc.processing_status} />
            </DataField>
            <DataField label="Status revizuire">
              <StatusBadge status={doc.review_status} variant="review" />
            </DataField>
            <DataField label="Încredere clasificare">
              <ConfidenceBar confidence={doc.confidence} />
            </DataField>
            <DataField label="Metodă clasificare" value={doc.metoda_clasificare ?? 'N/A'} />
            <DataField label="Dimensiune" value={formatFileSize(doc.file_size)} />
            <DataField label="Număr pagini" value={doc.page_count != null ? String(doc.page_count) : null} />
          </dl>
        </div>

        {/* Extracted Data Card */}
        {extraction && (
          <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-gray-100">Date Extrase</h3>
            <dl className="space-y-2 text-sm">
              <DataField label="Material" value={extraction.material} />
              <DataField label="Companie" value={extraction.companie} />
              <DataField label="Producător" value={extraction.producator} />
              <DataField label="Distribuitor" value={extraction.distribuitor} />
              <DataField label="Adresă producător" value={extraction.adresa_producator} />
              <DataField label="Adresă distribuitor">
                {extraction.adresa_distribuitor ? (
                  <span className="flex flex-wrap items-center justify-end gap-2">
                    <span>{extraction.adresa_distribuitor}</span>
                    {isRomanianAddress(extraction.adresa_distribuitor) === false && (
                      <span
                        className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-300"
                        title="Adresa distribuitorului nu pare să fie din România"
                      >
                        Non-RO
                      </span>
                    )}
                  </span>
                ) : (
                  <span className="text-gray-400 dark:text-gray-500">N/A</span>
                )}
              </DataField>
              <DataField label="Data expirare">
                <ExpirationWarning dataExpirare={extraction.data_expirare} />
              </DataField>
              <DataField label="Status extracție" value={extraction.extraction_status} />
              <DataField label="Model extracție" value={extraction.extraction_model} />
              <DataField label="Scor încredere">
                <ConfidenceBar confidence={extraction.confidence_score} />
              </DataField>
            </dl>
          </div>
        )}

        {/* AI Metadata Section */}
        {extraction && (
          <div className="rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
            <button
              onClick={() => setAiExpanded(!aiExpanded)}
              className="flex w-full items-center justify-between p-4 text-left"
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Metadate AI</h3>
              {aiExpanded ? (
                <ChevronDown className="h-5 w-5 text-gray-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-gray-400" />
              )}
            </button>
            {aiExpanded && (
              <div className="border-t border-gray-200 p-4 space-y-4 dark:border-gray-700">
                {extraction.metadata && Object.keys(extraction.metadata).length > 0 && (
                  <div>
                    <h4 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Metadata</h4>
                    <pre className="overflow-x-auto rounded bg-gray-50 p-3 text-xs text-gray-700 dark:bg-gray-900/50 dark:text-gray-300">
                      {JSON.stringify(extraction.metadata, null, 2)}
                    </pre>
                  </div>
                )}
                {extraction.extracted_text && (
                  <div>
                    <h4 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Text Extras</h4>
                    <div className="max-h-64 overflow-y-auto rounded bg-gray-50 p-3 text-xs text-gray-700 whitespace-pre-wrap dark:bg-gray-900/50 dark:text-gray-300">
                      {extraction.extracted_text}
                    </div>
                  </div>
                )}
                {extraction.error_details && (
                  <div>
                    <h4 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Erori</h4>
                    <pre className="overflow-x-auto rounded bg-red-50 p-3 text-xs text-red-700 dark:bg-red-900/30 dark:text-red-400">
                      {JSON.stringify(extraction.error_details, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Review Buttons */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <h3 className="mb-3 text-lg font-semibold text-gray-900 dark:text-gray-100">Acțiuni</h3>
          <div className="flex gap-3">
            <button
              onClick={() => reprocessMutation.mutate()}
              disabled={reprocessMutation.isPending}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              <span className="flex items-center gap-2">
                <RefreshCw className={`h-4 w-4 ${reprocessMutation.isPending ? 'animate-spin' : ''}`} />
                {reprocessMutation.isPending ? 'Se reprocesează...' : 'Reprocesează'}
              </span>
            </button>
            <button
              onClick={() => {
                reviewMutation.mutate(
                  { id: doc.id, payload: { action: 'approve' } },
                  {
                    onSuccess: () => toast.success('Document aprobat'),
                    onError: (err) => toast.error(err.message),
                  }
                );
              }}
              disabled={reviewMutation.isPending}
              className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              {reviewMutation.isPending ? 'Se procesează...' : 'Aprobă'}
            </button>
            <button
              onClick={() => setRejectionModalOpen(true)}
              disabled={reviewMutation.isPending}
              className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              Respinge
            </button>
          </div>
        </div>

        <RejectionModal
          isOpen={rejectionModalOpen}
          onClose={() => setRejectionModalOpen(false)}
          onSubmit={(data) => {
            reviewMutation.mutate(
              {
                id: doc.id,
                payload: {
                  action: 'reject' as const,
                  ...data,
                },
              },
              {
                onSuccess: () => {
                  toast.success('Feedback trimis');
                  setRejectionModalOpen(false);
                },
                onError: (err) => toast.error(err.message),
              }
            );
          }}
          currentCategory={doc.categorie}
          isSubmitting={reviewMutation.isPending}
        />
      </div>
    </div>
  );
}

function DataField({
  label,
  value,
  children,
}: {
  label: string;
  value?: string | null;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-2">
      <dt className="font-medium text-gray-500 dark:text-gray-400">{label}</dt>
      <dd className="text-right text-gray-900 dark:text-gray-100">
        {children ?? (value || <span className="text-gray-400 dark:text-gray-500">N/A</span>)}
      </dd>
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
