import type { ProcessingStatus, ReviewStatus } from '../../types';

const PROCESSING_STATUS_CLASSES: Record<ProcessingStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  processing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
};

const PROCESSING_STATUS_LABELS: Record<ProcessingStatus, string> = {
  pending: 'În așteptare',
  processing: 'Procesare',
  completed: 'Finalizat',
  failed: 'Eșuat',
};

const REVIEW_STATUS_CLASSES: Record<ReviewStatus, string> = {
  OK: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  REVIEW: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  NEEDS_CHECK: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
};

const REVIEW_STATUS_LABELS: Record<ReviewStatus, string> = {
  OK: 'OK',
  REVIEW: 'De revizuit',
  NEEDS_CHECK: 'Necesită verificare',
};

interface ProcessingStatusBadgeProps {
  status: ProcessingStatus;
  variant?: 'processing';
}

interface ReviewStatusBadgeProps {
  status: ReviewStatus | null;
  variant: 'review';
}

type StatusBadgeProps = ProcessingStatusBadgeProps | ReviewStatusBadgeProps;

export default function StatusBadge(props: StatusBadgeProps) {
  if (props.variant === 'review') {
    if (!props.status) return null;
    const classes = REVIEW_STATUS_CLASSES[props.status];
    const label = REVIEW_STATUS_LABELS[props.status];
    return (
      <span
        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${classes}`}
      >
        {label}
      </span>
    );
  }

  const classes = PROCESSING_STATUS_CLASSES[props.status];
  const label = PROCESSING_STATUS_LABELS[props.status];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${classes}`}
    >
      {label}
    </span>
  );
}
