import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Tag, FileText, Loader2 } from 'lucide-react';
import { CATEGORY_LABELS } from '../../utils/categories';
import type { DocumentCategory } from '../../types';

interface RejectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    rejection_reason: 'wrong_classification' | 'wrong_extraction';
    corrected_category?: string;
    wrong_fields?: string[];
    comment?: string;
  }) => void;
  currentCategory: string | null;
  isSubmitting: boolean;
}

const EXTRACTION_FIELDS = [
  { key: 'material', label: 'Material' },
  { key: 'companie', label: 'Companie' },
  { key: 'producator', label: 'Producator' },
  { key: 'data_expirare', label: 'Data expirare' },
  { key: 'adresa_producator', label: 'Adresa producator' },
] as const;

export default function RejectionModal({
  isOpen,
  onClose,
  onSubmit,
  currentCategory,
  isSubmitting,
}: RejectionModalProps) {
  const [reason, setReason] = useState<'wrong_classification' | 'wrong_extraction' | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [wrongFields, setWrongFields] = useState<string[]>([]);
  const [comment, setComment] = useState('');

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      setReason(null);
      setSelectedCategory(null);
      setWrongFields([]);
      setComment('');
    }
  }, [isOpen]);

  // Escape key to close
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const canSubmit =
    reason !== null &&
    !isSubmitting &&
    (reason === 'wrong_classification' ? selectedCategory !== null : wrongFields.length > 0);

  const handleSubmit = () => {
    if (!reason || !canSubmit) return;
    if (reason === 'wrong_classification') {
      onSubmit({
        rejection_reason: 'wrong_classification',
        corrected_category: selectedCategory!,
      });
    } else {
      onSubmit({
        rejection_reason: 'wrong_extraction',
        wrong_fields: wrongFields,
        comment: comment || undefined,
      });
    }
  };

  const toggleField = (field: string) => {
    setWrongFields((prev) =>
      prev.includes(field) ? prev.filter((f) => f !== field) : [...prev, field],
    );
  };

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50 transition-opacity" onClick={onClose} />
      <div className="relative z-10 w-full max-w-lg rounded-lg bg-white dark:bg-gray-800 p-6 shadow-xl max-h-[90vh] overflow-y-auto">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">Respinge document</h2>

        {/* Reason selection */}
        <div className="mb-4 flex gap-3">
          <button
            type="button"
            onClick={() => {
              setReason('wrong_classification');
              setWrongFields([]);
              setComment('');
            }}
            className={`flex flex-1 items-center justify-center gap-2 rounded-lg border-2 px-3 py-2.5 text-sm font-medium transition-colors ${
              reason === 'wrong_classification'
                ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-400'
                : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            <Tag className="h-4 w-4" />
            Clasificare gresita
          </button>
          <button
            type="button"
            onClick={() => {
              setReason('wrong_extraction');
              setSelectedCategory(null);
            }}
            className={`flex flex-1 items-center justify-center gap-2 rounded-lg border-2 px-3 py-2.5 text-sm font-medium transition-colors ${
              reason === 'wrong_extraction'
                ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-400'
                : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            <FileText className="h-4 w-4" />
            Date extrase gresit
          </button>
        </div>

        {/* Wrong classification panel */}
        {reason === 'wrong_classification' && (
          <div className="mb-4">
            <p className="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">Selecteaza categoria corecta:</p>
            <div className="grid grid-cols-3 gap-2">
              {(Object.entries(CATEGORY_LABELS) as [DocumentCategory, string][]).map(
                ([key, label]) => {
                  const isCurrent = key === currentCategory;
                  const isSelected = key === selectedCategory;
                  return (
                    <button
                      key={key}
                      type="button"
                      disabled={isCurrent}
                      onClick={() => setSelectedCategory(key)}
                      className={`rounded-md border-2 px-2 py-1.5 text-xs font-medium transition-colors ${
                        isCurrent
                          ? 'cursor-not-allowed border-gray-200 bg-gray-100 text-gray-400 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-500'
                          : isSelected
                            ? 'border-blue-500 bg-blue-50 text-blue-700 ring-2 ring-blue-300 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-400 dark:ring-blue-500'
                            : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                      }`}
                    >
                      {label}
                      {isCurrent && ' (actual)'}
                    </button>
                  );
                },
              )}
            </div>
          </div>
        )}

        {/* Wrong extraction panel */}
        {reason === 'wrong_extraction' && (
          <div className="mb-4">
            <div className="mb-3 space-y-2">
              {EXTRACTION_FIELDS.map(({ key, label }) => (
                <label
                  key={key}
                  className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={wrongFields.includes(key)}
                    onChange={() => toggleField(key)}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  {label}
                </label>
              ))}
            </div>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Descrie valorile corecte..."
              rows={3}
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 dark:bg-gray-700 placeholder-gray-400 dark:placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            Anuleaza
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            Trimite feedback
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
