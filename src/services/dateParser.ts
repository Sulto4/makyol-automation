import { parse, isValid, format } from 'date-fns';
import * as chrono from 'chrono-node';
import {
  ROMANIAN_DATE_PATTERNS,
  MONTH_NAME_TO_NUMBER,
  isValidYear,
  isValidMonth,
  isValidDay,
  normalizeRomanianText,
} from '../config/romanian-locale';

/**
 * Parsed date result interface
 */
export interface ParsedDate {
  date: Date;
  confidence: number; // 0.0 - 1.0
  source: string; // Original matched text
  format: string; // Format type that matched
}

/**
 * Date parsing options
 */
export interface DateParserOptions {
  /**
   * Strict mode: only accept exact format matches
   * Default: false (allows fuzzy parsing as fallback)
   */
  strict?: boolean;

  /**
   * Preferred formats to try first
   */
  preferredFormats?: string[];

  /**
   * Enable natural language parsing with chrono-node
   * Default: true
   */
  enableNaturalLanguage?: boolean;
}

/**
 * Romanian Date Parser Service
 *
 * Parses dates from Romanian-language text with support for multiple formats:
 * - dd.MM.yyyy (e.g., 15.03.2024)
 * - dd/MM/yyyy (e.g., 15/03/2024)
 * - dd-MM-yyyy (e.g., 15-03-2024)
 * - dd month yyyy (e.g., 15 martie 2024, 15 mar 2024)
 * - month dd, yyyy (e.g., martie 15, 2024)
 * - ISO format (e.g., 2024-03-15)
 */
export class DateParserService {
  /**
   * Parse a date from Romanian text
   *
   * @param text - Text containing a date
   * @param options - Parsing options
   * @returns Parsed date or null if no valid date found
   */
  parse(text: string, options?: DateParserOptions): ParsedDate | null {
    if (!text || typeof text !== 'string') {
      return null;
    }

    const opts = {
      strict: false,
      enableNaturalLanguage: true,
      ...options,
    };

    // Try Romanian-specific patterns first
    const patterns = [
      { name: 'dotNumeric', pattern: ROMANIAN_DATE_PATTERNS.dotNumeric, parser: this.parseDotNumeric.bind(this) },
      { name: 'slashNumeric', pattern: ROMANIAN_DATE_PATTERNS.slashNumeric, parser: this.parseSlashNumeric.bind(this) },
      { name: 'dashNumeric', pattern: ROMANIAN_DATE_PATTERNS.dashNumeric, parser: this.parseDashNumeric.bind(this) },
      { name: 'monthName', pattern: ROMANIAN_DATE_PATTERNS.monthName, parser: this.parseMonthName.bind(this) },
      { name: 'reverseMonthName', pattern: ROMANIAN_DATE_PATTERNS.reverseMonthName, parser: this.parseReverseMonthName.bind(this) },
      { name: 'iso', pattern: ROMANIAN_DATE_PATTERNS.iso, parser: this.parseISO.bind(this) },
    ];

    for (const { name, pattern, parser } of patterns) {
      const match = text.match(pattern);
      if (match) {
        const result = parser(match);
        if (result) {
          return {
            ...result,
            format: name,
            confidence: 0.95, // High confidence for exact pattern matches
          };
        }
      }
    }

    // Fallback to natural language parsing if enabled and not in strict mode
    if (opts.enableNaturalLanguage && !opts.strict) {
      return this.parseNaturalLanguage(text);
    }

    return null;
  }

  /**
   * Parse all dates from text
   *
   * @param text - Text potentially containing multiple dates
   * @param options - Parsing options
   * @returns Array of parsed dates
   */
  parseAll(text: string, options?: DateParserOptions): ParsedDate[] {
    if (!text || typeof text !== 'string') {
      return [];
    }

    const dates: ParsedDate[] = [];
    const patterns = [
      { name: 'dotNumeric', pattern: ROMANIAN_DATE_PATTERNS.dotNumeric, parser: this.parseDotNumeric.bind(this) },
      { name: 'slashNumeric', pattern: ROMANIAN_DATE_PATTERNS.slashNumeric, parser: this.parseSlashNumeric.bind(this) },
      { name: 'dashNumeric', pattern: ROMANIAN_DATE_PATTERNS.dashNumeric, parser: this.parseDashNumeric.bind(this) },
      { name: 'monthName', pattern: ROMANIAN_DATE_PATTERNS.monthName, parser: this.parseMonthName.bind(this) },
      { name: 'reverseMonthName', pattern: ROMANIAN_DATE_PATTERNS.reverseMonthName, parser: this.parseReverseMonthName.bind(this) },
      { name: 'iso', pattern: ROMANIAN_DATE_PATTERNS.iso, parser: this.parseISO.bind(this) },
    ];

    // Extract all matches for each pattern
    for (const { name, pattern, parser } of patterns) {
      const regex = new RegExp(pattern, 'g');
      let match;

      while ((match = regex.exec(text)) !== null) {
        const result = parser(match);
        if (result) {
          dates.push({
            ...result,
            format: name,
            confidence: 0.95,
          });
        }
      }
    }

    // Remove duplicates (same date found by different patterns)
    return this.deduplicateDates(dates);
  }

  /**
   * Parse dd.MM.yyyy format (e.g., 15.03.2024)
   */
  private parseDotNumeric(match: RegExpMatchArray): ParsedDate | null {
    const [fullMatch, dayStr, monthStr, yearStr] = match;
    return this.parseNumericDate(fullMatch, dayStr, monthStr, yearStr);
  }

  /**
   * Parse dd/MM/yyyy format (e.g., 15/03/2024)
   */
  private parseSlashNumeric(match: RegExpMatchArray): ParsedDate | null {
    const [fullMatch, dayStr, monthStr, yearStr] = match;
    return this.parseNumericDate(fullMatch, dayStr, monthStr, yearStr);
  }

  /**
   * Parse dd-MM-yyyy format (e.g., 15-03-2024)
   */
  private parseDashNumeric(match: RegExpMatchArray): ParsedDate | null {
    const [fullMatch, dayStr, monthStr, yearStr] = match;
    return this.parseNumericDate(fullMatch, dayStr, monthStr, yearStr);
  }

  /**
   * Common parser for numeric date formats
   */
  private parseNumericDate(source: string, dayStr: string, monthStr: string, yearStr: string): ParsedDate | null {
    const day = parseInt(dayStr, 10);
    const month = parseInt(monthStr, 10);
    const year = parseInt(yearStr, 10);

    if (!isValidYear(year) || !isValidMonth(month) || !isValidDay(day, month, year)) {
      return null;
    }

    const date = new Date(year, month - 1, day);

    if (!isValid(date)) {
      return null;
    }

    return {
      date,
      confidence: 0.95,
      source,
      format: 'numeric',
    };
  }

  /**
   * Parse dd month yyyy format (e.g., 15 martie 2024)
   */
  private parseMonthName(match: RegExpMatchArray): ParsedDate | null {
    const [fullMatch, dayStr, monthName, yearStr] = match;

    const day = parseInt(dayStr, 10);
    const year = parseInt(yearStr, 10);
    const month = this.getMonthNumber(monthName);

    if (month === null || !isValidYear(year) || !isValidDay(day, month, year)) {
      return null;
    }

    const date = new Date(year, month - 1, day);

    if (!isValid(date)) {
      return null;
    }

    return {
      date,
      confidence: 0.95,
      source: fullMatch,
      format: 'monthName',
    };
  }

  /**
   * Parse month dd, yyyy format (e.g., martie 15, 2024)
   */
  private parseReverseMonthName(match: RegExpMatchArray): ParsedDate | null {
    const [fullMatch, monthName, dayStr, yearStr] = match;

    const day = parseInt(dayStr, 10);
    const year = parseInt(yearStr, 10);
    const month = this.getMonthNumber(monthName);

    if (month === null || !isValidYear(year) || !isValidDay(day, month, year)) {
      return null;
    }

    const date = new Date(year, month - 1, day);

    if (!isValid(date)) {
      return null;
    }

    return {
      date,
      confidence: 0.95,
      source: fullMatch,
      format: 'reverseMonthName',
    };
  }

  /**
   * Parse ISO format (e.g., 2024-03-15)
   */
  private parseISO(match: RegExpMatchArray): ParsedDate | null {
    const [fullMatch, yearStr, monthStr, dayStr] = match;
    return this.parseNumericDate(fullMatch, dayStr, monthStr, yearStr);
  }

  /**
   * Fallback: use chrono-node for natural language parsing
   */
  private parseNaturalLanguage(text: string): ParsedDate | null {
    const results = chrono.parse(text);

    if (results.length === 0) {
      return null;
    }

    const result = results[0];
    const date = result.start.date();

    if (!isValid(date)) {
      return null;
    }

    return {
      date,
      confidence: 0.7, // Lower confidence for fuzzy parsing
      source: result.text,
      format: 'natural',
    };
  }

  /**
   * Get month number from Romanian month name
   */
  private getMonthNumber(monthName: string): number | null {
    const normalized = normalizeRomanianText(monthName);
    return MONTH_NAME_TO_NUMBER[normalized] || null;
  }

  /**
   * Remove duplicate dates from results
   */
  private deduplicateDates(dates: ParsedDate[]): ParsedDate[] {
    const seen = new Set<string>();
    const unique: ParsedDate[] = [];

    for (const item of dates) {
      const key = format(item.date, 'yyyy-MM-dd');
      if (!seen.has(key)) {
        seen.add(key);
        unique.push(item);
      }
    }

    return unique;
  }

  /**
   * Format a date in Romanian format (dd.MM.yyyy)
   */
  formatRomanian(date: Date): string {
    if (!isValid(date)) {
      throw new Error('Invalid date');
    }
    return format(date, 'dd.MM.yyyy');
  }

  /**
   * Format a date with Romanian month name (dd month yyyy)
   */
  formatRomanianWithMonth(date: Date): string {
    if (!isValid(date)) {
      throw new Error('Invalid date');
    }

    const day = format(date, 'd');
    const month = date.getMonth();
    const year = format(date, 'yyyy');

    const monthNames = [
      'ianuarie', 'februarie', 'martie', 'aprilie', 'mai', 'iunie',
      'iulie', 'august', 'septembrie', 'octombrie', 'noiembrie', 'decembrie'
    ];

    return `${day} ${monthNames[month]} ${year}`;
  }
}
