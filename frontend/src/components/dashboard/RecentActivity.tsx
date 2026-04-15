import { format } from 'date-fns';
import { ro } from 'date-fns/locale';
import type { Document } from '../../types';
import CategoryBadge from '../documents/CategoryBadge';
import StatusBadge from '../documents/StatusBadge';

interface RecentActivityProps {
  documents: Document[];
}

export default function RecentActivity({ documents }: RecentActivityProps) {
  const recentDocs = documents
    .slice()
    .sort(
      (a, b) =>
        new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime()
    )
    .slice(0, 10);

  if (recentDocs.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          Activitate Recentă
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">Nu există documente încărcate.</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
      <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
        Activitate Recentă
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm dark:text-gray-300">
          <thead>
            <tr className="border-b border-gray-200 text-xs font-medium uppercase tracking-wider text-gray-500 dark:border-gray-700 dark:text-gray-400">
              <th className="pb-3 pr-4">Fișier</th>
              <th className="pb-3 pr-4">Categorie</th>
              <th className="pb-3 pr-4">Status</th>
              <th className="pb-3">Data Încărcare</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {recentDocs.map((doc) => (
              <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                <td className="py-3 pr-4">
                  <span
                    className="max-w-[200px] truncate block text-gray-900 dark:text-white"
                    title={doc.original_filename}
                  >
                    {doc.original_filename}
                  </span>
                </td>
                <td className="py-3 pr-4">
                  <CategoryBadge category={doc.categorie} />
                </td>
                <td className="py-3 pr-4">
                  <StatusBadge status={doc.processing_status} />
                </td>
                <td className="py-3 whitespace-nowrap text-gray-500 dark:text-gray-400">
                  {format(new Date(doc.uploaded_at), 'dd MMM yyyy, HH:mm', {
                    locale: ro,
                  })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
