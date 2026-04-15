import { FileX, Bell, Search, type LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  message: string;
  icon?: 'document' | 'alert' | 'search';
  description?: string;
}

const iconMap: Record<string, LucideIcon> = {
  document: FileX,
  alert: Bell,
  search: Search,
};

export default function EmptyState({
  message,
  icon = 'document',
  description,
}: EmptyStateProps) {
  const Icon = iconMap[icon] ?? FileX;

  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Icon className="h-12 w-12 text-gray-300 dark:text-gray-600" />
      <h3 className="mt-3 text-sm font-medium text-gray-900 dark:text-gray-100">{message}</h3>
      {description && <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{description}</p>}
    </div>
  );
}
