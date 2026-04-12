import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts';
import type { Document, ProcessingStatus } from '../../types';

interface StatusChartProps {
  documents: Document[];
}

const STATUS_LABELS: Record<ProcessingStatus, string> = {
  pending: 'În așteptare',
  processing: 'Procesare',
  completed: 'Finalizat',
  failed: 'Eșuat',
};

const STATUS_COLORS: Record<ProcessingStatus, string> = {
  pending: '#f59e0b',
  processing: '#3b82f6',
  completed: '#22c55e',
  failed: '#ef4444',
};

const ALL_STATUSES: ProcessingStatus[] = ['pending', 'processing', 'completed', 'failed'];

export default function StatusChart({ documents }: StatusChartProps) {
  const data = useMemo(() => {
    const counts = new Map<ProcessingStatus, number>();
    for (const status of ALL_STATUSES) {
      counts.set(status, 0);
    }
    for (const doc of documents) {
      const current = counts.get(doc.processing_status) ?? 0;
      counts.set(doc.processing_status, current + 1);
    }

    return ALL_STATUSES.map((status) => ({
      name: STATUS_LABELS[status],
      count: counts.get(status) ?? 0,
      fill: STATUS_COLORS[status],
    }));
  }, [documents]);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="count" name="Documente">
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
