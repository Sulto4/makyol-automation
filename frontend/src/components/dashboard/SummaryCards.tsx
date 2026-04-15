import { FileText, AlertTriangle, Clock, Search } from 'lucide-react';
import { useMemo } from 'react';
import type { Document } from '../../types';

interface SummaryCardsProps {
  documents: Document[];
  expiredCount?: number;
}

interface CardConfig {
  label: string;
  icon: React.ReactNode;
  count: number;
  bgColor: string;
  iconColor: string;
}

export default function SummaryCards({ documents, expiredCount = 0 }: SummaryCardsProps) {
  const cards = useMemo<CardConfig[]>(() => {
    const totalDocuments = documents.length;

    const failedDocuments = documents.filter(
      (d) => d.processing_status === 'failed'
    ).length;

    const needsReviewDocuments = documents.filter(
      (d) => d.review_status === 'NEEDS_CHECK' || d.review_status === 'REVIEW'
    ).length;

    return [
      {
        label: 'Total Documente',
        icon: <FileText className="h-6 w-6" />,
        count: totalDocuments,
        bgColor: 'bg-blue-50 dark:bg-blue-900/30',
        iconColor: 'text-blue-600 dark:text-blue-400',
      },
      {
        label: 'Documente Eșuate',
        icon: <AlertTriangle className="h-6 w-6" />,
        count: failedDocuments,
        bgColor: 'bg-red-50 dark:bg-red-900/30',
        iconColor: 'text-red-600 dark:text-red-400',
      },
      {
        label: 'Documente Expirate',
        icon: <Clock className="h-6 w-6" />,
        count: expiredCount,
        bgColor: 'bg-amber-50 dark:bg-amber-900/30',
        iconColor: 'text-amber-600 dark:text-amber-400',
      },
      {
        label: 'Necesită Revizuire',
        icon: <Search className="h-6 w-6" />,
        count: needsReviewDocuments,
        bgColor: 'bg-purple-50 dark:bg-purple-900/30',
        iconColor: 'text-purple-600 dark:text-purple-400',
      },
    ];
  }, [documents, expiredCount]);

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`rounded-lg ${card.bgColor} p-5 transition-shadow hover:shadow-md`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{card.label}</p>
              <p className="mt-1 text-3xl font-bold text-gray-900 dark:text-gray-100">
                {card.count}
              </p>
            </div>
            <div className={card.iconColor}>{card.icon}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
