import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts';
import type { Document, ClassificationMethod } from '../../types';
import { useChartTheme } from '../../hooks/useChartTheme';

interface ClassificationChartProps {
  documents: Document[];
}

const METHOD_LABELS: Record<ClassificationMethod, string> = {
  filename_regex: 'Filename Regex',
  text_rules: 'Reguli Text',
  ai: 'AI',
  text_override: 'Text Override',
  vision: 'Vision',
  'filename+text_agree': 'Filename+Text Agree',
  filename_wins: 'Filename Wins',
  fallback: 'Fallback',
};

const METHOD_COLORS: Record<ClassificationMethod, string> = {
  filename_regex: '#6366f1',
  text_rules: '#3b82f6',
  ai: '#8b5cf6',
  text_override: '#14b8a6',
  vision: '#f97316',
  'filename+text_agree': '#10b981',
  filename_wins: '#f59e0b',
  fallback: '#6b7280',
};

const ALL_METHODS: ClassificationMethod[] = [
  'filename_regex',
  'text_rules',
  'ai',
  'text_override',
  'vision',
];

export default function ClassificationChart({ documents }: ClassificationChartProps) {
  const chartTheme = useChartTheme();
  const data = useMemo(() => {
    const counts = new Map<ClassificationMethod, number>();
    for (const method of ALL_METHODS) {
      counts.set(method, 0);
    }
    for (const doc of documents) {
      if (doc.metoda_clasificare) {
        const current = counts.get(doc.metoda_clasificare) ?? 0;
        counts.set(doc.metoda_clasificare, current + 1);
      }
    }

    return ALL_METHODS.map((method) => ({
      name: METHOD_LABELS[method],
      count: counts.get(method) ?? 0,
      color: METHOD_COLORS[method],
    }));
  }, [documents]);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.grid} />
        <XAxis dataKey="name" tick={{ fill: chartTheme.axis }} />
        <YAxis allowDecimals={false} tick={{ fill: chartTheme.axis }} />
        <Tooltip
          contentStyle={{
            backgroundColor: chartTheme.tooltipBg,
            color: chartTheme.tooltipText,
            border: `1px solid ${chartTheme.tooltipBorder}`,
          }}
        />
        <Bar dataKey="count" name="Documente">
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
