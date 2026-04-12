import { parseDataExpirare, isExpired, isExpiringSoon, formatDate } from '../../utils/dates';

interface ExpirationWarningProps {
  dataExpirare: string | null;
}

export default function ExpirationWarning({ dataExpirare }: ExpirationWarningProps) {
  if (!dataExpirare) {
    return (
      <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
        Nedefinit
      </span>
    );
  }

  const date = parseDataExpirare(dataExpirare);

  if (!date) {
    return (
      <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
        {dataExpirare}
      </span>
    );
  }

  const formattedDate = formatDate(dataExpirare);

  if (isExpired(date)) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
        <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
        Expirat — {formattedDate}
      </span>
    );
  }

  if (isExpiringSoon(date)) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800">
        <span className="h-1.5 w-1.5 rounded-full bg-yellow-500" />
        Expiră curând — {formattedDate}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
      <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
      {formattedDate}
    </span>
  );
}
