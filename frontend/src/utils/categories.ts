import type { DocumentCategory } from '../types';

/**
 * Romanian labels for document categories — matches the 14 backend categories
 */
export const CATEGORY_LABELS: Record<DocumentCategory, string> = {
  ISO: 'Certificat ISO',
  CE: 'Marcaj CE',
  FISA_TEHNICA: 'Fișă Tehnică',
  AGREMENT: 'Agrement Tehnic',
  AVIZ_TEHNIC: 'Aviz Tehnic',
  AVIZ_SANITAR: 'Aviz Sanitar',
  DECLARATIE_CONFORMITATE: 'Declarație de Conformitate',
  CERTIFICAT_CALITATE: 'Certificat de Calitate',
  AUTORIZATIE_DISTRIBUTIE: 'Autorizație de Distribuție',
  CUI: 'Certificat de Înregistrare',
  CERTIFICAT_GARANTIE: 'Certificat de Garanție',
  DECLARATIE_PERFORMANTA: 'Declarație de Performanță',
  AVIZ_TEHNIC_SI_AGREMENT: 'Aviz Tehnic + Agrement',
  ALTELE: 'Altele',
};

/**
 * Full Tailwind class strings for category badges.
 * MUST use complete class names — dynamic construction breaks Tailwind purge.
 */
export const CATEGORY_BADGE_CLASSES: Record<DocumentCategory, string> = {
  ISO: 'bg-blue-100 text-blue-800',
  CE: 'bg-red-100 text-red-800',
  FISA_TEHNICA: 'bg-green-100 text-green-800',
  AGREMENT: 'bg-violet-100 text-violet-800',
  AVIZ_TEHNIC: 'bg-indigo-100 text-indigo-800',
  AVIZ_SANITAR: 'bg-teal-100 text-teal-800',
  DECLARATIE_CONFORMITATE: 'bg-pink-100 text-pink-800',
  CERTIFICAT_CALITATE: 'bg-amber-100 text-amber-800',
  AUTORIZATIE_DISTRIBUTIE: 'bg-orange-100 text-orange-800',
  CUI: 'bg-gray-100 text-gray-800',
  CERTIFICAT_GARANTIE: 'bg-emerald-100 text-emerald-800',
  DECLARATIE_PERFORMANTA: 'bg-purple-100 text-purple-800',
  AVIZ_TEHNIC_SI_AGREMENT: 'bg-cyan-100 text-cyan-800',
  ALTELE: 'bg-slate-100 text-slate-800',
};

/**
 * Recharts-compatible hex colors for each category
 */
export const CATEGORY_CHART_COLORS: Record<DocumentCategory, string> = {
  ISO: '#3b82f6',
  CE: '#ef4444',
  FISA_TEHNICA: '#22c55e',
  AGREMENT: '#8b5cf6',
  AVIZ_TEHNIC: '#6366f1',
  AVIZ_SANITAR: '#14b8a6',
  DECLARATIE_CONFORMITATE: '#ec4899',
  CERTIFICAT_CALITATE: '#f59e0b',
  AUTORIZATIE_DISTRIBUTIE: '#f97316',
  CUI: '#6b7280',
  CERTIFICAT_GARANTIE: '#10b981',
  DECLARATIE_PERFORMANTA: '#a855f7',
  AVIZ_TEHNIC_SI_AGREMENT: '#06b6d4',
  ALTELE: '#64748b',
};

/**
 * Get the label for a category, with fallback for unknown values
 */
export function getCategoryLabel(category: string | null): string {
  if (!category) return 'Necunoscut';
  return CATEGORY_LABELS[category as DocumentCategory] ?? category;
}

/**
 * Get badge classes for a category, with fallback
 */
export function getCategoryBadgeClasses(category: string | null): string {
  if (!category) return 'bg-gray-100 text-gray-800';
  return CATEGORY_BADGE_CLASSES[category as DocumentCategory] ?? 'bg-gray-100 text-gray-800';
}
