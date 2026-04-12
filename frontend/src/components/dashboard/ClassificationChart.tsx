import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts';
import type { Document, ClassificationMethod } from '../../types';

interface ClassificationChartProps {
  documents: Document[];
}

const METHOD_LABELS: Record<ClassificationMethod, string> = {
  filename_regex: 'Filename Regex',
  text_rules: 'Reguli Text',
  ai: 'AI',
  text_override: 'Text Override',
  vision: 'Vision',
};

const METHOD_COLORS: Record<ClassificationMethod, string> = {
  filename_regex: '#6366f1',
  text_rules: '#3b82f6',
  ai: '#8b5cf6',
  text_override: '#14b8a6',
  vision: '#f97316',
};

const ALL_METHODS: ClassificationMethod[] = [
  'filename_regex',
  'text_rules',
  'ai',
  'text_override',
  'vision',
];

export default function ClassificationChart({ documents }: ClassificationChartProps) {
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
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="count" name="Documente">
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
