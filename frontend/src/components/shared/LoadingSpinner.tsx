import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  variant?: 'spinner' | 'skeleton';
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  rows?: number;
}

function Spinner({ size = 'md', text }: Pick<LoadingSpinnerProps, 'size' | 'text'>) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  return (
    <div className="flex flex-col items-center justify-center gap-2 py-8">
      <Loader2 className={`${sizeClasses[size]} animate-spin text-blue-600`} />
      {text && <p className="text-sm text-gray-500">{text}</p>}
    </div>
  );
}

function SkeletonLoader({ rows = 5 }: Pick<LoadingSpinnerProps, 'rows'>) {
  return (
    <div className="animate-pulse space-y-3 py-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4">
          <div className="h-4 w-1/4 rounded bg-gray-200" />
          <div className="h-4 w-1/3 rounded bg-gray-200" />
          <div className="h-4 w-1/6 rounded bg-gray-200" />
          <div className="h-4 w-1/5 rounded bg-gray-200" />
        </div>
      ))}
    </div>
  );
}

export default function LoadingSpinner({
  variant = 'spinner',
  size = 'md',
  text,
  rows = 5,
}: LoadingSpinnerProps) {
  if (variant === 'skeleton') {
    return <SkeletonLoader rows={rows} />;
  }
  return <Spinner size={size} text={text} />;
}
