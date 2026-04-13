import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts';
import type { ExtractionStats } from '../../types';

interface ExtractionFillChartProps {
  stats: ExtractionStats;
}

const FIELD_LABELS: Record<string, string> = {
  companie: 'Companie',
  material: 'Material',
  data_expirare: 'Data Expirare',
  producator: 'Producător',
  distribuitor: 'Distribuitor',
  adresa_producator: 'Adresă Producător',
};

const FIELD_COLORS: Record<string, string> = {
  companie: '#6366f1',
  material: '#3b82f6',
  data_expirare: '#8b5cf6',
  producator: '#14b8a6',
  distribuitor: '#f97316',
  adresa_producator: '#ec4899',
};

const ALL_FIELDS = [
  'companie',
  'material',
  'data_expirare',
  'producator',
  'distribuitor',
  'adresa_producator',
] as const;

export default function ExtractionFillChart({ stats }: ExtractionFillChartProps) {
  const data = useMemo(() => {
    if (stats.total === 0) return [];

    return ALL_FIELDS.map((field) => ({
      name: FIELD_LABELS[field],
      percent: Math.round((stats.fieldCounts[field] / stats.total) * 100),
      color: FIELD_COLORS[field],
    }));
  }, [stats]);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis allowDecimals={false} domain={[0, 100]} unit="%" />
        <Tooltip formatter={(value: number) => `${value}%`} />
        <Bar dataKey="percent" name="Completare">
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
