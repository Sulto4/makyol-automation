import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts';
import type { ExtractionStats } from '../../types';
import { useChartTheme } from '../../hooks/useChartTheme';

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
  const chartTheme = useChartTheme();
  const data = useMemo(() => {
    if (stats.total === 0) return [];

    return ALL_FIELDS.map((field) => ({
      name: FIELD_LABELS[field],
      percent: Math.round(((stats[`has_${field}` as keyof ExtractionStats] as number) / stats.total) * 100),
      color: FIELD_COLORS[field],
    }));
  }, [stats]);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.grid} />
        <XAxis dataKey="name" tick={{ fill: chartTheme.axis }} />
        <YAxis allowDecimals={false} domain={[0, 100]} unit="%" tick={{ fill: chartTheme.axis }} />
        <Tooltip
          formatter={(value: number) => `${value}%`}
          contentStyle={{
            backgroundColor: chartTheme.tooltipBg,
            color: chartTheme.tooltipText,
            border: `1px solid ${chartTheme.tooltipBorder}`,
          }}
        />
        <Bar dataKey="percent" name="Completare">
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
