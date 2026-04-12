interface ConfidenceBarProps {
  confidence: number | null;
}

export default function ConfidenceBar({ confidence }: ConfidenceBarProps) {
  if (confidence === null || confidence === undefined) {
    return <span className="text-xs text-gray-400">N/A</span>;
  }

  const percentage = Math.round(confidence * 100);
  const colorClass =
    confidence > 0.7
      ? 'bg-green-500'
      : confidence >= 0.5
        ? 'bg-yellow-500'
        : 'bg-red-500';

  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-20 rounded-full bg-gray-200">
        <div
          className={`h-2 rounded-full ${colorClass}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs text-gray-600">{percentage}%</span>
    </div>
  );
}
