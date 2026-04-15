import { useMemo } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { Document, DocumentCategory } from '../../types';
import { CATEGORY_LABELS, CATEGORY_CHART_COLORS } from '../../utils/categories';
import { useChartTheme } from '../../hooks/useChartTheme';

interface CategoryChartProps {
  documents: Document[];
}

interface CategoryDatum {
  name: string;
  value: number;
  color: string;
}

export default function CategoryChart({ documents }: CategoryChartProps) {
  const chartTheme = useChartTheme();
  const data = useMemo<CategoryDatum[]>(() => {
    const counts = new Map<string, number>();
    for (const doc of documents) {
      const cat = doc.categorie ?? 'UNKNOWN';
      counts.set(cat, (counts.get(cat) ?? 0) + 1);
    }

    return Array.from(counts.entries())
      .map(([cat, count]) => ({
        name: CATEGORY_LABELS[cat as DocumentCategory] ?? cat,
        value: count,
        color: CATEGORY_CHART_COLORS[cat as DocumentCategory] ?? '#6b7280',
      }))
      .sort((a, b) => b.value - a.value);
  }, [documents]);

  if (data.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-gray-500">
        Nu există date disponibile
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          outerRadius={100}
          dataKey="value"
          nameKey="name"
          label={({ name, percent }) =>
            `${name} (${(percent * 100).toFixed(0)}%)`
          }
          labelLine={{ stroke: chartTheme.axis }}
          stroke={chartTheme.tooltipBg}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: chartTheme.tooltipBg,
            color: chartTheme.tooltipText,
            border: `1px solid ${chartTheme.tooltipBorder}`,
          }}
        />
        <Legend wrapperStyle={{ color: chartTheme.label }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
