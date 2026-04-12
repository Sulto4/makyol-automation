import type { DocumentCategory } from '../types';

/**
 * Romanian labels for document categories
 */
export const CATEGORY_LABELS: Record<DocumentCategory, string> = {
  ISO: 'Certificat ISO',
  CE: 'Marcaj CE',
  FISA_TEHNICA: 'Fișă Tehnică',
  DECLARATIE_PERFORMANTA: 'Declarație de Performanță',
  DECLARATIE_CONFORMITATE: 'Declarație de Conformitate',
  CERTIFICAT_CONSTANTA: 'Certificat de Constanță',
  AVIZ_SANITAR: 'Aviz Sanitar',
  RAPORT_INCERCARE: 'Raport de Încercare',
  CERTIFICAT_CALITATE: 'Certificat de Calitate',
  PROCES_VERBAL: 'Proces Verbal',
  AGREMENTARE_TEHNICA: 'Agrementare Tehnică',
  BULETIN_ANALIZA: 'Buletin de Analiză',
  CERTIFICAT_GARANTIE: 'Certificat de Garanție',
  UNKNOWN: 'Necunoscut',
};

/**
 * Full Tailwind class strings for category badges.
 * MUST use complete class names — dynamic construction breaks Tailwind purge.
 */
export const CATEGORY_BADGE_CLASSES: Record<DocumentCategory, string> = {
  ISO: 'bg-blue-100 text-blue-800',
  CE: 'bg-red-100 text-red-800',
  FISA_TEHNICA: 'bg-green-100 text-green-800',
  DECLARATIE_PERFORMANTA: 'bg-indigo-100 text-indigo-800',
  DECLARATIE_CONFORMITATE: 'bg-pink-100 text-pink-800',
  CERTIFICAT_CONSTANTA: 'bg-purple-100 text-purple-800',
  AVIZ_SANITAR: 'bg-teal-100 text-teal-800',
  RAPORT_INCERCARE: 'bg-orange-100 text-orange-800',
  CERTIFICAT_CALITATE: 'bg-amber-100 text-amber-800',
  PROCES_VERBAL: 'bg-lime-100 text-lime-800',
  AGREMENTARE_TEHNICA: 'bg-violet-100 text-violet-800',
  BULETIN_ANALIZA: 'bg-cyan-100 text-cyan-800',
  CERTIFICAT_GARANTIE: 'bg-emerald-100 text-emerald-800',
  UNKNOWN: 'bg-gray-100 text-gray-800',
};

/**
 * Recharts-compatible hex colors for each category
 */
export const CATEGORY_CHART_COLORS: Record<DocumentCategory, string> = {
  ISO: '#3b82f6',
  CE: '#ef4444',
  FISA_TEHNICA: '#22c55e',
  DECLARATIE_PERFORMANTA: '#6366f1',
  DECLARATIE_CONFORMITATE: '#ec4899',
  CERTIFICAT_CONSTANTA: '#a855f7',
  AVIZ_SANITAR: '#14b8a6',
  RAPORT_INCERCARE: '#f97316',
  CERTIFICAT_CALITATE: '#f59e0b',
  PROCES_VERBAL: '#84cc16',
  AGREMENTARE_TEHNICA: '#8b5cf6',
  BULETIN_ANALIZA: '#06b6d4',
  CERTIFICAT_GARANTIE: '#10b981',
  UNKNOWN: '#6b7280',
};

/**
 * Get the label for a category, with fallback for unknown values
 */
export function getCategoryLabel(category: string | null): string {
  if (!category) return CATEGORY_LABELS.UNKNOWN;
  return CATEGORY_LABELS[category as DocumentCategory] ?? category;
}

/**
 * Get badge classes for a category, with fallback
 */
export function getCategoryBadgeClasses(category: string | null): string {
  if (!category) return CATEGORY_BADGE_CLASSES.UNKNOWN;
  return CATEGORY_BADGE_CLASSES[category as DocumentCategory] ?? CATEGORY_BADGE_CLASSES.UNKNOWN;
}
