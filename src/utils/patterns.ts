/**
 * Regex patterns for certificate metadata extraction
 *
 * This module contains patterns for extracting key metadata fields from
 * Romanian compliance certificate PDFs, including certificate numbers,
 * issuing organizations, company names, and certification scopes.
 */

/**
 * Certificate number patterns
 *
 * Matches common certificate number formats:
 * - Nr. 12345
 * - Certificat nr. ABC-123-DEF
 * - Certificate No. ISO-9001-2024
 * - Număr: 123/2024
 */
export const CERTIFICATE_NUMBER_PATTERNS = [
  // "Nr." or "Număr" followed by certificate number
  /(?:Nr\.?|Număr|Number|No\.?)\s*[:.]?\s*([A-Z0-9\-\/._]+)/i,

  // "Certificat" followed by optional "nr." and certificate number
  /Certificat(?:\s+(?:nr\.?|număr))?\s*[:.]?\s*([A-Z0-9\-\/._]+)/i,

  // "Certificate" followed by optional "no." or "number"
  /Certificate(?:\s+(?:no\.?|number))?\s*[:.]?\s*([A-Z0-9\-\/._]+)/i,

  // Standalone pattern for format like "RO-123/2024"
  /\b([A-Z]{2,4}[-\/]?\d{2,6}(?:[-\/]\d{2,4})?)\b/,
];

/**
 * Issuing organization patterns
 *
 * Matches certification bodies and regulatory authorities:
 * - SRAC (Romanian Accreditation Association)
 * - RENAR (Romanian Accreditation Body)
 * - TÜV, SGS, Bureau Veritas, etc.
 */
export const ISSUING_ORGANIZATION_PATTERNS = [
  // "Emis de" or "Issued by" followed by organization name
  /(?:Emis(?:ă)?\s+de|Issued\s+by|Eliberat\s+de)\s*[:.]?\s*([A-Z][A-Za-z\s.&-]{3,50})/i,

  // "Organism de certificare" or "Certification body"
  /(?:Organism(?:ul)?\s+de\s+certificare|Certification\s+body)\s*[:.]?\s*([A-Z][A-Za-z\s.&-]{3,50})/i,

  // Well-known certification bodies (case-insensitive)
  /\b(SRAC|RENAR|TÜV|SGS|Bureau\s+Veritas|DNV|Lloyd'?s|BSI|LRQA|Intertek|DEKRA|RINA|URS)\b/i,

  // Generic pattern for organization-like names (capitals, spaces, &)
  /(?:de\s+către|by)\s+([A-Z][A-Za-z\s.&-]{3,50})\b/,
];

/**
 * Certified company name patterns
 *
 * Matches company names that received the certification
 */
export const CERTIFIED_COMPANY_PATTERNS = [
  // "Companie" or "Company" or "Societate"
  /(?:Companie|Company|Societate|Firma|Organization|Organizație)\s*[:.]?\s*([A-Z][A-Za-z\s.&-]{3,100})/i,

  // Romanian legal entity suffixes: S.R.L., S.A., S.C.
  /\b((?:S\.C\.|SC)\s+[A-Z][A-Za-z\s.&-]{2,80}\s+(?:S\.R\.L\.|SRL|S\.A\.|SA))\b/,

  // "Acordat" or "Granted to" followed by company name
  /(?:Acordat|Granted\s+to|Awarded\s+to)\s+(?:către|to)?\s*([A-Z][A-Za-z\s.&-]{3,100})/i,

  // "Titular" or "Holder"
  /(?:Titular|Holder)\s*[:.]?\s*([A-Z][A-Za-z\s.&-]{3,100})/i,
];

/**
 * Certification scope patterns
 *
 * Matches the scope or domain of certification
 */
export const CERTIFICATION_SCOPE_PATTERNS = [
  // "Domeniu" or "Scope"
  /(?:Domeniu(?:l)?|Scope|Field)\s*[:.]?\s*([A-Za-z][A-Za-z\s,;&\-().]{10,200})/i,

  // "Aplicabil pentru" or "Applicable for"
  /(?:Aplicabil\s+pentru|Applicable\s+for|Valid\s+for)\s*[:.]?\s*([A-Za-z][A-Za-z\s,;&\-().]{10,200})/i,

  // ISO standards mention (e.g., "ISO 9001:2015")
  /(ISO\s+\d{4,5}(?:[-:]\d{4})?(?:\s*[,;]\s*ISO\s+\d{4,5}(?:[-:]\d{4})?)*)/i,

  // Activities or services
  /(?:Activități|Activities|Servicii|Services)\s*[:.]?\s*([A-Za-z][A-Za-z\s,;&\-().]{10,200})/i,
];

/**
 * Date context patterns (to help identify which dates are issue vs expiry)
 *
 * These patterns help identify the context around dates to determine their meaning
 */
export const DATE_CONTEXT_PATTERNS = {
  // Issue date indicators
  issue: [
    /(?:Data\s+(?:emiterii|eliberării)|Issue\s+date|Issued\s+on|Emis(?:ă)?\s+la)\s*[:.]?\s*/i,
    /(?:De\s+la|From|Starting)\s*[:.]?\s*/i,
  ],

  // Expiry date indicators
  expiry: [
    /(?:Data\s+(?:expirării|valabilității)|Expiry\s+date|Expires\s+on|Valid\s+until|Valabil\s+până)\s*[:.]?\s*/i,
    /(?:Până\s+la|Until|To)\s*[:.]?\s*/i,
  ],

  // Validity period indicators
  validity: [
    /(?:Valabilitate|Validity|Valid|Valabil)\s*[:.]?\s*/i,
    /(?:Perioada\s+de\s+valabilitate|Validity\s+period)\s*[:.]?\s*/i,
  ],
};

/**
 * Clean and normalize extracted text
 *
 * Removes extra whitespace, special characters, and normalizes spacing
 */
export function cleanExtractedText(text: string): string {
  return text
    .replace(/\s+/g, ' ') // Normalize whitespace
    .replace(/[\r\n\t]+/g, ' ') // Remove newlines and tabs
    .replace(/\s*[:.]\s*$/, '') // Remove trailing punctuation
    .trim();
}

/**
 * Validate certificate number format
 *
 * Certificate numbers should be alphanumeric with optional separators
 */
export function isValidCertificateNumber(certNumber: string): boolean {
  // Must be at least 3 characters
  if (certNumber.length < 3) {
    return false;
  }

  // Must contain at least one digit or letter
  if (!/[A-Z0-9]/i.test(certNumber)) {
    return false;
  }

  // Should not be just separators
  if (/^[-\/._\s]+$/.test(certNumber)) {
    return false;
  }

  return true;
}

/**
 * Validate organization name
 *
 * Organization names should be reasonable length and not just numbers
 */
export function isValidOrganizationName(name: string): boolean {
  // Must be at least 3 characters
  if (name.length < 3) {
    return false;
  }

  // Should not be only numbers
  if (/^\d+$/.test(name)) {
    return false;
  }

  // Should contain at least some letters
  if (!/[A-Za-z]{2,}/.test(name)) {
    return false;
  }

  return true;
}

/**
 * Validate company name
 *
 * Company names should be reasonable length with mostly letters
 */
export function isValidCompanyName(name: string): boolean {
  // Must be at least 3 characters
  if (name.length < 3) {
    return false;
  }

  // Should not be only numbers or special characters
  if (!/[A-Za-z]{3,}/.test(name)) {
    return false;
  }

  return true;
}

/**
 * Validate certification scope
 *
 * Scope should be descriptive text, not too short
 */
export function isValidCertificationScope(scope: string): boolean {
  // Must be at least 10 characters for meaningful scope
  if (scope.length < 10) {
    return false;
  }

  // Should contain some letters
  if (!/[A-Za-z]{5,}/.test(scope)) {
    return false;
  }

  return true;
}
