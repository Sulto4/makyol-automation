import { DateParserService, ParsedDate } from './dateParser';
import {
  CERTIFICATE_NUMBER_PATTERNS,
  ISSUING_ORGANIZATION_PATTERNS,
  CERTIFIED_COMPANY_PATTERNS,
  CERTIFICATION_SCOPE_PATTERNS,
  DATE_CONTEXT_PATTERNS,
  cleanExtractedText,
  isValidCertificateNumber,
  isValidOrganizationName,
  isValidCompanyName,
  isValidCertificationScope,
} from '../utils/patterns';
import { ROMANIAN_DATE_KEYWORDS } from '../config/romanian-locale';

/**
 * Parsed certificate metadata with confidence scores
 */
export interface ParsedMetadata {
  certificate_number?: string;
  certificate_number_confidence?: number;
  issuing_organization?: string;
  issuing_organization_confidence?: number;
  issue_date?: string;
  issue_date_confidence?: number;
  expiry_date?: string;
  expiry_date_confidence?: number;
  certified_company?: string;
  certified_company_confidence?: number;
  certification_scope?: string;
  certification_scope_confidence?: number;
}

/**
 * Options for metadata parsing
 */
export interface MetadataParserOptions {
  /**
   * Minimum confidence threshold for accepting results (0.0 - 1.0)
   * Default: 0.5
   */
  minConfidence?: number;

  /**
   * Enable strict mode (only accept high-confidence matches)
   * Default: false
   */
  strictMode?: boolean;

  /**
   * Maximum context distance for date extraction (characters)
   * Default: 100
   */
  maxDateContextDistance?: number;
}

/**
 * Metadata Parser Service
 *
 * Extracts certificate metadata from Romanian PDF text including:
 * - Certificate numbers
 * - Issuing organizations (e.g., SRAC, RENAR)
 * - Issue and expiry dates
 * - Certified company names
 * - Certification scope
 */
export class MetadataParserService {
  private dateParser: DateParserService;

  constructor() {
    this.dateParser = new DateParserService();
  }

  /**
   * Parse all metadata from certificate text
   *
   * @param text - Extracted PDF text content
   * @param options - Parsing options
   * @returns Parsed metadata with confidence scores
   */
  parse(text: string, options?: MetadataParserOptions): ParsedMetadata {
    if (!text || typeof text !== 'string') {
      return {};
    }

    const opts = {
      minConfidence: 0.5,
      strictMode: false,
      maxDateContextDistance: 100,
      ...options,
    };

    const metadata: ParsedMetadata = {};

    // Extract certificate number
    const certNumber = this.extractCertificateNumber(text);
    if (certNumber && certNumber.confidence >= opts.minConfidence) {
      metadata.certificate_number = certNumber.value;
      metadata.certificate_number_confidence = certNumber.confidence;
    }

    // Extract issuing organization
    const issuingOrg = this.extractIssuingOrganization(text);
    if (issuingOrg && issuingOrg.confidence >= opts.minConfidence) {
      metadata.issuing_organization = issuingOrg.value;
      metadata.issuing_organization_confidence = issuingOrg.confidence;
    }

    // Extract certified company
    const company = this.extractCertifiedCompany(text);
    if (company && company.confidence >= opts.minConfidence) {
      metadata.certified_company = company.value;
      metadata.certified_company_confidence = company.confidence;
    }

    // Extract certification scope
    const scope = this.extractCertificationScope(text);
    if (scope && scope.confidence >= opts.minConfidence) {
      metadata.certification_scope = scope.value;
      metadata.certification_scope_confidence = scope.confidence;
    }

    // Extract dates (issue and expiry)
    const dates = this.extractDates(text, opts.maxDateContextDistance);
    if (dates.issueDate) {
      metadata.issue_date = dates.issueDate.date.toISOString();
      metadata.issue_date_confidence = dates.issueDate.confidence;
    }
    if (dates.expiryDate) {
      metadata.expiry_date = dates.expiryDate.date.toISOString();
      metadata.expiry_date_confidence = dates.expiryDate.confidence;
    }

    return metadata;
  }

  /**
   * Extract certificate number from text
   *
   * @param text - Certificate text
   * @returns Extracted certificate number with confidence score
   */
  extractCertificateNumber(text: string): { value: string; confidence: number } | null {
    for (let i = 0; i < CERTIFICATE_NUMBER_PATTERNS.length; i++) {
      const pattern = CERTIFICATE_NUMBER_PATTERNS[i];
      const match = text.match(pattern);

      if (match && match[1]) {
        const certNumber = cleanExtractedText(match[1]);

        if (isValidCertificateNumber(certNumber)) {
          // Higher confidence for patterns with explicit keywords
          const confidence = i < 3 ? 0.9 : 0.7;
          return { value: certNumber, confidence };
        }
      }
    }

    return null;
  }

  /**
   * Extract issuing organization from text
   *
   * @param text - Certificate text
   * @returns Extracted organization name with confidence score
   */
  extractIssuingOrganization(text: string): { value: string; confidence: number } | null {
    for (let i = 0; i < ISSUING_ORGANIZATION_PATTERNS.length; i++) {
      const pattern = ISSUING_ORGANIZATION_PATTERNS[i];
      const match = text.match(pattern);

      if (match && match[1]) {
        const orgName = cleanExtractedText(match[1]);

        if (isValidOrganizationName(orgName)) {
          // Higher confidence for well-known certification bodies
          const confidence = i === 2 ? 0.95 : i === 0 ? 0.85 : 0.7;
          return { value: orgName, confidence };
        }
      }
    }

    return null;
  }

  /**
   * Extract certified company name from text
   *
   * @param text - Certificate text
   * @returns Extracted company name with confidence score
   */
  extractCertifiedCompany(text: string): { value: string; confidence: number } | null {
    for (let i = 0; i < CERTIFIED_COMPANY_PATTERNS.length; i++) {
      const pattern = CERTIFIED_COMPANY_PATTERNS[i];
      const match = text.match(pattern);

      if (match && match[1]) {
        const companyName = cleanExtractedText(match[1]);

        if (isValidCompanyName(companyName)) {
          // Higher confidence for Romanian legal entity format (S.R.L., S.A.)
          const confidence = i === 1 ? 0.9 : i === 3 ? 0.85 : 0.75;
          return { value: companyName, confidence };
        }
      }
    }

    return null;
  }

  /**
   * Extract certification scope from text
   *
   * @param text - Certificate text
   * @returns Extracted scope with confidence score
   */
  extractCertificationScope(text: string): { value: string; confidence: number } | null {
    for (let i = 0; i < CERTIFICATION_SCOPE_PATTERNS.length; i++) {
      const pattern = CERTIFICATION_SCOPE_PATTERNS[i];
      const match = text.match(pattern);

      if (match && match[1]) {
        const scope = cleanExtractedText(match[1]);

        if (isValidCertificationScope(scope)) {
          // Higher confidence for explicit scope keywords
          const confidence = i === 0 ? 0.85 : i === 2 ? 0.9 : 0.75;
          return { value: scope, confidence };
        }
      }
    }

    return null;
  }

  /**
   * Extract and classify dates as issue or expiry dates
   *
   * @param text - Certificate text
   * @param maxContextDistance - Maximum distance to look for context keywords
   * @returns Classified dates with confidence scores
   */
  extractDates(
    text: string,
    maxContextDistance: number = 100
  ): {
    issueDate: ParsedDate | null;
    expiryDate: ParsedDate | null;
  } {
    // Parse all dates from text
    const allDates = this.dateParser.parseAll(text);

    if (allDates.length === 0) {
      return { issueDate: null, expiryDate: null };
    }

    let issueDate: ParsedDate | null = null;
    let expiryDate: ParsedDate | null = null;

    // Try to classify dates based on context
    for (const parsedDate of allDates) {
      const datePosition = text.indexOf(parsedDate.source);
      if (datePosition === -1) continue;

      // Get context before the date
      const contextStart = Math.max(0, datePosition - maxContextDistance);
      const contextBefore = text.substring(contextStart, datePosition).toLowerCase();

      // Check for issue date indicators
      const isIssueDate = this.hasIssueDateContext(contextBefore);
      const isExpiryDate = this.hasExpiryDateContext(contextBefore);

      if (isIssueDate && !issueDate) {
        issueDate = parsedDate;
      } else if (isExpiryDate && !expiryDate) {
        expiryDate = parsedDate;
      }
    }

    // Fallback: if we have 2+ dates and couldn't classify by context,
    // assume first is issue date and last is expiry date
    if (!issueDate && !expiryDate && allDates.length >= 2) {
      const sortedDates = [...allDates].sort((a, b) => a.date.getTime() - b.date.getTime());
      issueDate = sortedDates[0];
      expiryDate = sortedDates[sortedDates.length - 1];

      // Reduce confidence since we're guessing
      if (issueDate) {
        issueDate = { ...issueDate, confidence: issueDate.confidence * 0.7 };
      }
      if (expiryDate) {
        expiryDate = { ...expiryDate, confidence: expiryDate.confidence * 0.7 };
      }
    } else if (!issueDate && !expiryDate && allDates.length === 1) {
      // Single date - try to determine if it's issue or expiry based on context
      const singleDate = allDates[0];
      const datePosition = text.indexOf(singleDate.source);
      const contextStart = Math.max(0, datePosition - maxContextDistance);
      const contextBefore = text.substring(contextStart, datePosition).toLowerCase();

      if (this.hasIssueDateContext(contextBefore)) {
        issueDate = singleDate;
      } else if (this.hasExpiryDateContext(contextBefore)) {
        expiryDate = singleDate;
      } else {
        // Default to issue date if unclear
        issueDate = { ...singleDate, confidence: singleDate.confidence * 0.6 };
      }
    }

    return { issueDate, expiryDate };
  }

  /**
   * Check if context contains issue date indicators
   */
  private hasIssueDateContext(context: string): boolean {
    const issueKeywords = [
      ...ROMANIAN_DATE_KEYWORDS.issued,
      ...DATE_CONTEXT_PATTERNS.issue.map((p) => p.source.replace(/[()[\]{}^$*+?.|\\]/g, '')),
    ];

    return issueKeywords.some((keyword) =>
      context.toLowerCase().includes(keyword.toLowerCase())
    );
  }

  /**
   * Check if context contains expiry date indicators
   */
  private hasExpiryDateContext(context: string): boolean {
    const expiryKeywords = [
      ...ROMANIAN_DATE_KEYWORDS.expiry,
      ...DATE_CONTEXT_PATTERNS.expiry.map((p) => p.source.replace(/[()[\]{}^$*+?.|\\]/g, '')),
    ];

    return expiryKeywords.some((keyword) =>
      context.toLowerCase().includes(keyword.toLowerCase())
    );
  }

  /**
   * Calculate overall confidence score for metadata extraction
   *
   * @param metadata - Parsed metadata
   * @returns Average confidence score (0.0 - 1.0)
   */
  calculateConfidence(metadata: ParsedMetadata): number {
    const confidenceScores: number[] = [];

    if (metadata.certificate_number_confidence !== undefined) {
      confidenceScores.push(metadata.certificate_number_confidence);
    }
    if (metadata.issuing_organization_confidence !== undefined) {
      confidenceScores.push(metadata.issuing_organization_confidence);
    }
    if (metadata.issue_date_confidence !== undefined) {
      confidenceScores.push(metadata.issue_date_confidence);
    }
    if (metadata.expiry_date_confidence !== undefined) {
      confidenceScores.push(metadata.expiry_date_confidence);
    }
    if (metadata.certified_company_confidence !== undefined) {
      confidenceScores.push(metadata.certified_company_confidence);
    }
    if (metadata.certification_scope_confidence !== undefined) {
      confidenceScores.push(metadata.certification_scope_confidence);
    }

    if (confidenceScores.length === 0) {
      return 0;
    }

    return confidenceScores.reduce((sum, score) => sum + score, 0) / confidenceScores.length;
  }
}
