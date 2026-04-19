/**
 * Heuristic country detector for distributor / producer addresses.
 *
 * Mirrors `pipeline/country_detector.py`. The decisive check runs server-side
 * (pipeline emits `distribuitor_not_romanian` review_reason when applicable);
 * this client-side version is used only for the warning badge in the UI so
 * the user sees the flag immediately without waiting for a metadata round-trip.
 *
 * Keep the two lists in sync when adding entries.
 */

const RO_CITIES = new Set<string>([
  'bucuresti', 'cluj-napoca', 'cluj napoca', 'iasi', 'timisoara', 'constanta',
  'brasov', 'sibiu', 'oradea', 'ploiesti', 'bacau', 'pitesti', 'craiova',
  'galati', 'arad', 'targu mures', 'tirgu mures', 'buzau', 'satu mare',
  'botosani', 'baia mare', 'suceava', 'ramnicu valcea', 'rimnicu valcea',
  'focsani', 'tulcea', 'resita', 'slatina', 'alba iulia', 'giurgiu',
  'targoviste', 'tirgoviste', 'zalau', 'deva', 'bistrita', 'vaslui',
  'miercurea ciuc', 'sfantu gheorghe', 'sfintu gheorghe', 'piatra neamt',
  'calarasi', 'slobozia', 'alexandria', 'roman', 'medias', 'turda',
  'mangalia', 'saratel', 'hunedoara', 'campulung', 'campina', 'onesti',
  'reghin', 'falticeni', 'barlad', 'sighisoara', 'fagaras', 'lugoj',
  'mioveni', 'caracal', 'husi', 'odorheiu secuiesc', 'carei',
]);

const FOREIGN_COUNTRIES = new Set<string>([
  'italia', 'italy', 'italien',
  'germania', 'germany', 'deutschland',
  'franta', 'france',
  'turcia', 'turkey', 'turkiye',
  'china', 'p.r.c.', 'p.r. china', 'pr china',
  'spania', 'spain', 'espana',
  'polonia', 'poland', 'polska',
  'ungaria', 'hungary', 'magyarorszag',
  'bulgaria',
  'austria', 'osterreich',
  'olanda', 'netherlands', 'holland', 'nederland',
  'belgia', 'belgium', 'belgique',
  'grecia', 'greece', 'hellas',
  'cehia', 'czech republic', 'czechia',
  'slovacia', 'slovakia',
  'suedia', 'sweden',
  'elvetia', 'switzerland', 'schweiz', 'suisse',
  'uk', 'united kingdom', 'regatul unit', 'great britain', 'england',
  'usa', 'united states', 'statele unite',
  'japan', 'japonia',
  'korea', 'coreea',
  'serbia', 'srbija',
  'croatia', 'hrvatska',
  'slovenia',
  'ucraina', 'ukraine',
  'rusia', 'russia',
  'portugalia', 'portugal',
  'irlanda', 'ireland',
  'danemarca', 'denmark',
  'finlanda', 'finland',
  'norvegia', 'norway',
]);

const STREET_PATTERNS: RegExp[] = [
  /\bstr\./i, /\bstrada\b/i, /\bstr\b/i,
  /\bbd\./i, /\bbulevardul\b/i, /\bb-dul\b/i, /\bb\.dul\b/i,
  /\baleea\b/i, /\bcalea\b/i, /\bpiata\b/i, /\bpta\./i,
  /\bsos\./i, /\bsoseaua\b/i, /\bintrarea\b/i, /\bintr\./i,
  /\bdn\d+\b/i,
];

const ADMIN_PATTERNS: RegExp[] = [
  /\bjud\./i, /\bjudetul\b/i,
  /\bsector\s*[1-6]\b/i,
  /\bmun\./i,
  /\bcom\./i,
  /\bsat\s/i,
];

const RO_PREFIXED_POSTCODE = /\bro[-\s]?\d{5,6}\b/i;
const RO_POSTCODE = /\b\d{6}\b/;

function stripDiacritics(s: string): string {
  return s.normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
}

function normalize(addr: string): string {
  return stripDiacritics(addr).toLowerCase().trim();
}

export type Country = 'RO' | 'OTHER';

/**
 * Return 'RO', 'OTHER', or null (empty input).
 *
 * Decision order (matches Python):
 *   1. Foreign-country tokens → OTHER
 *   2. Explicit RO signal (keyword / street / admin / postcode / city) → RO
 *   3. Default → OTHER (conservative — favors flagging for review)
 */
export function detectAddressCountry(addr: string | null | undefined): Country | null {
  if (!addr || !addr.trim()) return null;
  const norm = normalize(addr);

  for (const country of FOREIGN_COUNTRIES) {
    if (country.includes('.') || country.includes(' ')) {
      if (norm.includes(country)) return 'OTHER';
    } else {
      const boundary = new RegExp(`\\b${country.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`);
      if (boundary.test(norm)) return 'OTHER';
    }
  }

  if (norm.includes('romania')) return 'RO';
  if (RO_PREFIXED_POSTCODE.test(norm)) return 'RO';
  if (STREET_PATTERNS.some((re) => re.test(norm))) return 'RO';
  if (ADMIN_PATTERNS.some((re) => re.test(norm))) return 'RO';
  if (RO_POSTCODE.test(norm)) return 'RO';
  for (const city of RO_CITIES) {
    const boundary = new RegExp(`\\b${city.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`);
    if (boundary.test(norm)) return 'RO';
  }

  return 'OTHER';
}

/** Convenience wrapper: true / false / null (empty input). */
export function isRomanianAddress(addr: string | null | undefined): boolean | null {
  const c = detectAddressCountry(addr);
  if (c === null) return null;
  return c === 'RO';
}
