/**
 * Romanian locale configuration for date parsing
 *
 * Provides month names, patterns, and localization data for parsing
 * Romanian-language date formats commonly found in compliance certificates.
 */

/**
 * Romanian month names in various forms
 */
export const ROMANIAN_MONTHS = {
  // Full month names (nominative case)
  full: [
    'ianuarie',
    'februarie',
    'martie',
    'aprilie',
    'mai',
    'iunie',
    'iulie',
    'august',
    'septembrie',
    'octombrie',
    'noiembrie',
    'decembrie',
  ] as const,

  // Abbreviated month names (3-letter)
  abbreviated: [
    'ian',
    'feb',
    'mar',
    'apr',
    'mai',
    'iun',
    'iul',
    'aug',
    'sep',
    'oct',
    'noi',
    'dec',
  ] as const,

  // Alternative abbreviated forms
  alternativeAbbr: [
    'ian.',
    'feb.',
    'mar.',
    'apr.',
    'mai.',
    'iun.',
    'iul.',
    'aug.',
    'sep.',
    'oct.',
    'noi.',
    'dec.',
  ] as const,
};

/**
 * Map Romanian month names to month numbers (1-12)
 */
export const MONTH_NAME_TO_NUMBER: Record<string, number> = {
  // Full names
  'ianuarie': 1,
  'februarie': 2,
  'martie': 3,
  'aprilie': 4,
  'mai': 5,
  'iunie': 6,
  'iulie': 7,
  'august': 8,
  'septembrie': 9,
  'octombrie': 10,
  'noiembrie': 11,
  'decembrie': 12,

  // Abbreviated forms
  'ian': 1,
  'ian.': 1,
  'feb': 2,
  'feb.': 2,
  'mar': 3,
  'mar.': 3,
  'apr': 4,
  'apr.': 4,
  'iun': 6,
  'iun.': 6,
  'iul': 7,
  'iul.': 7,
  'aug': 8,
  'aug.': 8,
  'sep': 9,
  'sep.': 9,
  'sept': 9,
  'sept.': 9,
  'oct': 10,
  'oct.': 10,
  'noi': 11,
  'noi.': 11,
  'nov': 11,
  'nov.': 11,
  'dec': 12,
  'dec.': 12,
};

/**
 * Date format patterns commonly found in Romanian documents
 */
export const ROMANIAN_DATE_PATTERNS = {
  // Numeric formats with dots: 15.03.2024
  dotNumeric: /(\d{1,2})\.(\d{1,2})\.(\d{4})/,

  // Numeric formats with slashes: 15/03/2024
  slashNumeric: /(\d{1,2})\/(\d{1,2})\/(\d{4})/,

  // Numeric formats with dashes: 15-03-2024
  dashNumeric: /(\d{1,2})-(\d{1,2})-(\d{4})/,

  // Month name format: 15 martie 2024, 15 mar 2024
  monthName: /(\d{1,2})\s+(ianuarie|februarie|martie|aprilie|mai|iunie|iulie|august|septembrie|octombrie|noiembrie|decembrie|ian\.?|feb\.?|mar\.?|apr\.?|iun\.?|iul\.?|aug\.?|sep\.?|sept\.?|oct\.?|noi\.?|nov\.?|dec\.?)\s+(\d{4})/i,

  // Reverse month name format: martie 15, 2024
  reverseMonthName: /(ianuarie|februarie|martie|aprilie|mai|iunie|iulie|august|septembrie|octombrie|noiembrie|decembrie|ian\.?|feb\.?|mar\.?|apr\.?|iun\.?|iul\.?|aug\.?|sep\.?|sept\.?|oct\.?|noi\.?|nov\.?|dec\.?)\s+(\d{1,2}),?\s+(\d{4})/i,

  // ISO format: 2024-03-15
  iso: /(\d{4})-(\d{1,2})-(\d{1,2})/,
};

/**
 * Common date-related keywords in Romanian
 */
export const ROMANIAN_DATE_KEYWORDS = {
  issued: ['emis', 'emisa', 'emisă', 'eliberat', 'eliberată', 'data emiterii'],
  expiry: ['expirare', 'expira', 'expiră', 'valabil până', 'valabilitate', 'până la'],
  valid: ['valabil', 'valabilă', 'valid', 'validă'],
  from: ['de la', 'din', 'începând cu'],
  to: ['până la', 'până', 'la'],
};

/**
 * Date validation constraints
 */
export const DATE_CONSTRAINTS = {
  minDay: 1,
  maxDay: 31,
  minMonth: 1,
  maxMonth: 12,
  minYear: 1900,
  maxYear: 2100,
};

/**
 * Check if a year is valid within reasonable bounds
 */
export function isValidYear(year: number): boolean {
  return year >= DATE_CONSTRAINTS.minYear && year <= DATE_CONSTRAINTS.maxYear;
}

/**
 * Check if a month is valid (1-12)
 */
export function isValidMonth(month: number): boolean {
  return month >= DATE_CONSTRAINTS.minMonth && month <= DATE_CONSTRAINTS.maxMonth;
}

/**
 * Check if a day is valid for a given month and year
 */
export function isValidDay(day: number, month: number, year: number): boolean {
  if (day < DATE_CONSTRAINTS.minDay) {
    return false;
  }

  // Days in each month (index 0 = January)
  const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

  // Check for leap year
  if (month === 2 && isLeapYear(year)) {
    return day <= 29;
  }

  return day <= daysInMonth[month - 1];
}

/**
 * Check if a year is a leap year
 */
export function isLeapYear(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
}

/**
 * Normalize Romanian text for matching (remove diacritics, lowercase)
 */
export function normalizeRomanianText(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Remove diacritics
    .replace(/ă/g, 'a')
    .replace(/â/g, 'a')
    .replace(/î/g, 'i')
    .replace(/ș/g, 's')
    .replace(/ț/g, 't')
    .trim();
}
