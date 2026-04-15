import { useMemo } from 'react';
import { useThemeStore } from '../store/themeStore';

interface ChartThemeColors {
  grid: string;
  axis: string;
  tooltipBg: string;
  tooltipText: string;
  tooltipBorder: string;
  label: string;
}

/**
 * Returns Recharts-compatible color props based on current theme.
 * Recharts SVG elements can't use Tailwind dark: classes, so we
 * read the resolved theme from the store and return JS color values.
 */
export function useChartTheme(): ChartThemeColors {
  const resolvedTheme = useThemeStore((s) => s.resolvedTheme);

  return useMemo(() => {
    if (resolvedTheme === 'dark') {
      return {
        grid: '#374151',       // gray-700
        axis: '#9ca3af',       // gray-400
        tooltipBg: '#1f2937',  // gray-800
        tooltipText: '#f3f4f6', // gray-100
        tooltipBorder: '#374151',
        label: '#d1d5db',      // gray-300
      };
    }
    return {
      grid: '#e5e7eb',       // gray-200
      axis: '#6b7280',       // gray-500
      tooltipBg: '#ffffff',
      tooltipText: '#111827', // gray-900
      tooltipBorder: '#e5e7eb',
      label: '#374151',      // gray-700
    };
  }, [resolvedTheme]);
}
