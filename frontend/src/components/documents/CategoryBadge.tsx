import type { DocumentCategory } from '../../types';
import { getCategoryLabel, getCategoryBadgeClasses } from '../../utils/categories';

interface CategoryBadgeProps {
  category: DocumentCategory | string | null;
}

export default function CategoryBadge({ category }: CategoryBadgeProps) {
  const label = category ? getCategoryLabel(category) : 'Neclasificat';
  const classes = category ? getCategoryBadgeClasses(category) : 'bg-gray-100 text-gray-800';

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${classes}`}
    >
      {label}
    </span>
  );
}
