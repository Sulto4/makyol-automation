import { parseISO, isBefore, addDays, format, isValid, parse } from 'date-fns';

/**
 * Defensively parse data_expirare (VARCHAR(100)) into a Date.
 * Tries ISO format first, then common Romanian date formats.
 */
export function parseDataExpirare(value: string | null): Date | null {
  if (!value || !value.trim()) return null;

  const trimmed = value.trim();

  // Try ISO format first (e.g., "2027-06-15")
  const isoDate = parseISO(trimmed);
  if (isValid(isoDate)) return isoDate;

  // Try common date formats defensively
  const formats = ['dd.MM.yyyy', 'dd/MM/yyyy', 'dd-MM-yyyy', 'yyyy/MM/dd'];
  for (const fmt of formats) {
    try {
      const parsed = parse(trimmed, fmt, new Date());
      if (isValid(parsed)) return parsed;
    } catch {
      // Continue to next format
    }
  }

  return null;
}

/**
 * Check if a date is in the past (expired)
 */
export function isExpired(date: Date | null): boolean {
  if (!date) return false;
  return isBefore(date, new Date());
}

/**
 * Check if a date is within the threshold (expiring soon but not yet expired)
 */
export function isExpiringSoon(date: Date | null, days: number = 30): boolean {
  if (!date) return false;
  if (isExpired(date)) return false;
  const threshold = addDays(new Date(), days);
  return isBefore(date, threshold);
}

/**
 * Format a date string for display. Returns '—' for invalid/null dates.
 */
export function formatDate(value: string | null, pattern: string = 'dd.MM.yyyy'): string {
  const date = parseDataExpirare(value);
  if (!date) return '—';
  return format(date, pattern);
}
