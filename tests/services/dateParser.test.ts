import { DateParserService } from '../../src/services/dateParser';
import { format } from 'date-fns';

describe('DateParserService', () => {
  let parser: DateParserService;

  beforeEach(() => {
    parser = new DateParserService();
  });

  describe('parse - dd.MM.yyyy format', () => {
    it('should parse date with dot separator', () => {
      const result = parser.parse('15.03.2024');

      expect(result).not.toBeNull();
      expect(result?.date).toBeInstanceOf(Date);
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
      expect(result?.confidence).toBeGreaterThan(0.9);
      expect(result?.format).toBe('dotNumeric');
    });

    it('should parse single-digit day and month with dots', () => {
      const result = parser.parse('5.3.2024');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-05');
    });

    it('should parse date from longer text', () => {
      const result = parser.parse('Emis la data de 15.03.2024 de către SRAC');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
    });

    it('should handle end of month dates', () => {
      const result = parser.parse('31.12.2023');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2023-12-31');
    });

    it('should reject invalid day', () => {
      const result = parser.parse('32.03.2024', { strict: true });

      expect(result).toBeNull();
    });

    it('should reject invalid month', () => {
      const result = parser.parse('15.13.2024', { strict: true });

      expect(result).toBeNull();
    });
  });

  describe('parse - dd/MM/yyyy format', () => {
    it('should parse date with slash separator', () => {
      const result = parser.parse('15/03/2024');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
      expect(result?.format).toBe('slashNumeric');
    });

    it('should parse single-digit day and month with slashes', () => {
      const result = parser.parse('5/3/2024');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-05');
    });

    it('should parse date embedded in text', () => {
      const result = parser.parse('Certificat valabil până la 30/06/2025');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2025-06-30');
    });
  });

  describe('parse - dd-MM-yyyy format', () => {
    it('should parse date with dash separator', () => {
      const result = parser.parse('15-03-2024');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
      expect(result?.format).toBe('dashNumeric');
    });

    it('should parse date with dashes from text', () => {
      const result = parser.parse('Data expirării: 31-12-2025');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2025-12-31');
    });
  });

  describe('parse - month name format (dd month yyyy)', () => {
    it('should parse date with full Romanian month name', () => {
      const testCases = [
        { text: '15 ianuarie 2024', expected: '2024-01-15' },
        { text: '28 februarie 2024', expected: '2024-02-28' },
        { text: '15 martie 2024', expected: '2024-03-15' },
        { text: '20 aprilie 2024', expected: '2024-04-20' },
        { text: '1 mai 2024', expected: '2024-05-01' },
        { text: '15 iunie 2024', expected: '2024-06-15' },
        { text: '4 iulie 2024', expected: '2024-07-04' },
        { text: '15 august 2024', expected: '2024-08-15' },
        { text: '1 septembrie 2024', expected: '2024-09-01' },
        { text: '15 octombrie 2024', expected: '2024-10-15' },
        { text: '1 noiembrie 2024', expected: '2024-11-01' },
        { text: '25 decembrie 2024', expected: '2024-12-25' },
      ];

      testCases.forEach(({ text, expected }) => {
        const result = parser.parse(text);
        expect(result).not.toBeNull();
        expect(format(result!.date, 'yyyy-MM-dd')).toBe(expected);
        expect(result?.format).toBe('monthName');
      });
    });

    it('should parse date with abbreviated Romanian month name', () => {
      const testCases = [
        { text: '15 ian 2024', expected: '2024-01-15' },
        { text: '15 feb 2024', expected: '2024-02-15' },
        { text: '15 mar 2024', expected: '2024-03-15' },
        { text: '15 apr 2024', expected: '2024-04-15' },
        { text: '15 iun 2024', expected: '2024-06-15' },
        { text: '15 iul 2024', expected: '2024-07-15' },
        { text: '15 aug 2024', expected: '2024-08-15' },
        { text: '15 sep 2024', expected: '2024-09-15' },
        { text: '15 oct 2024', expected: '2024-10-15' },
        { text: '15 noi 2024', expected: '2024-11-15' },
        { text: '15 dec 2024', expected: '2024-12-15' },
      ];

      testCases.forEach(({ text, expected }) => {
        const result = parser.parse(text);
        expect(result).not.toBeNull();
        expect(format(result!.date, 'yyyy-MM-dd')).toBe(expected);
      });
    });

    it('should parse date with abbreviated month with period', () => {
      const result = parser.parse('15 ian. 2024');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-01-15');
    });

    it('should parse month name embedded in Romanian text', () => {
      const result = parser.parse('Certificat eliberat la 15 martie 2024 de către SRAC');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
    });

    it('should handle case-insensitive month names', () => {
      const testCases = [
        '15 MARTIE 2024',
        '15 Martie 2024',
        '15 MaRtIe 2024',
      ];

      testCases.forEach((text) => {
        const result = parser.parse(text);
        expect(result).not.toBeNull();
        expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
      });
    });
  });

  describe('parse - reverse month name format (month dd, yyyy)', () => {
    it('should parse reverse order with full month name', () => {
      const result = parser.parse('martie 15, 2024');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
      expect(result?.format).toBe('reverseMonthName');
    });

    it('should parse reverse order without comma', () => {
      const result = parser.parse('martie 15 2024');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
    });

    it('should parse reverse order with abbreviated month', () => {
      const result = parser.parse('mar 15, 2024');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
    });
  });

  describe('parse - ISO format (yyyy-MM-dd)', () => {
    it('should parse ISO date format', () => {
      const result = parser.parse('2024-03-15');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
      expect(result?.format).toBe('iso');
    });

    it('should parse ISO format with single-digit month and day', () => {
      const result = parser.parse('2024-3-5');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-05');
    });
  });

  describe('parseAll - multiple dates', () => {
    it('should extract all dates from text with multiple formats', () => {
      const text = 'Certificat emis la 15.03.2024 și valabil până la 15/03/2025';
      const results = parser.parseAll(text);

      expect(results).toHaveLength(2);
      expect(format(results[0].date, 'yyyy-MM-dd')).toBe('2024-03-15');
      expect(format(results[1].date, 'yyyy-MM-dd')).toBe('2025-03-15');
    });

    it('should extract dates with month names', () => {
      const text = 'De la 1 ianuarie 2024 până la 31 decembrie 2024';
      const results = parser.parseAll(text);

      expect(results).toHaveLength(2);
      expect(format(results[0].date, 'yyyy-MM-dd')).toBe('2024-01-01');
      expect(format(results[1].date, 'yyyy-MM-dd')).toBe('2024-12-31');
    });

    it('should deduplicate identical dates', () => {
      const text = '15.03.2024 sau 15/03/2024';
      const results = parser.parseAll(text);

      // Should find same date in different formats but deduplicate
      expect(results.length).toBeGreaterThan(0);
      // All unique dates
      const uniqueDates = new Set(results.map(r => format(r.date, 'yyyy-MM-dd')));
      expect(uniqueDates.size).toBe(results.length);
    });

    it('should return empty array for text with no dates', () => {
      const text = 'This text has no dates at all';
      const results = parser.parseAll(text);

      expect(results).toEqual([]);
    });
  });

  describe('leap year handling', () => {
    it('should correctly handle February 29 in leap year', () => {
      const result = parser.parse('29.02.2024');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-02-29');
    });

    it('should reject February 29 in non-leap year', () => {
      const result = parser.parse('29.02.2023', { strict: true });

      expect(result).toBeNull();
    });

    it('should correctly handle February 28 in non-leap year', () => {
      const result = parser.parse('28.02.2023');

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2023-02-28');
    });
  });

  describe('edge cases', () => {
    it('should return null for invalid input', () => {
      const testCases = [
        null,
        undefined,
        '',
        '   ',
        'no date here',
      ];

      testCases.forEach((input) => {
        const result = parser.parse(input as any);
        expect(result).toBeNull();
      });
    });

    it('should return null for dates outside valid range', () => {
      const testCases = [
        '15.03.1800', // Too old
        '15.03.2200', // Too far in future
      ];

      testCases.forEach((input) => {
        const result = parser.parse(input, { strict: true });
        expect(result).toBeNull();
      });
    });

    it('should handle dates at year boundaries', () => {
      const result1 = parser.parse('01.01.2024');
      const result2 = parser.parse('31.12.2024');

      expect(result1).not.toBeNull();
      expect(result2).not.toBeNull();
      expect(format(result1!.date, 'yyyy-MM-dd')).toBe('2024-01-01');
      expect(format(result2!.date, 'yyyy-MM-dd')).toBe('2024-12-31');
    });
  });

  describe('strict mode', () => {
    it('should not fallback to natural language in strict mode', () => {
      const result = parser.parse('tomorrow', { strict: true });

      expect(result).toBeNull();
    });

    it('should still parse exact formats in strict mode', () => {
      const result = parser.parse('15.03.2024', { strict: true });

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
    });
  });

  describe('natural language parsing', () => {
    it('should parse natural language dates when not in strict mode', () => {
      const result = parser.parse('yesterday');

      // Natural language should work (lower confidence)
      expect(result).not.toBeNull();
      expect(result?.confidence).toBeLessThan(0.9);
      expect(result?.format).toBe('natural');
    });

    it('should disable natural language when option is false', () => {
      const result = parser.parse('yesterday', { enableNaturalLanguage: false });

      expect(result).toBeNull();
    });
  });

  describe('formatRomanian', () => {
    it('should format date in dd.MM.yyyy format', () => {
      const date = new Date(2024, 2, 15); // March 15, 2024
      const formatted = parser.formatRomanian(date);

      expect(formatted).toBe('15.03.2024');
    });

    it('should throw error for invalid date', () => {
      const invalidDate = new Date('invalid');

      expect(() => parser.formatRomanian(invalidDate)).toThrow('Invalid date');
    });
  });

  describe('formatRomanianWithMonth', () => {
    it('should format date with Romanian month name', () => {
      const date = new Date(2024, 2, 15); // March 15, 2024
      const formatted = parser.formatRomanianWithMonth(date);

      expect(formatted).toBe('15 martie 2024');
    });

    it('should format all months correctly', () => {
      const expectedMonths = [
        'ianuarie', 'februarie', 'martie', 'aprilie', 'mai', 'iunie',
        'iulie', 'august', 'septembrie', 'octombrie', 'noiembrie', 'decembrie'
      ];

      expectedMonths.forEach((month, index) => {
        const date = new Date(2024, index, 15);
        const formatted = parser.formatRomanianWithMonth(date);
        expect(formatted).toContain(month);
      });
    });

    it('should throw error for invalid date', () => {
      const invalidDate = new Date('invalid');

      expect(() => parser.formatRomanianWithMonth(invalidDate)).toThrow('Invalid date');
    });
  });

  describe('confidence scores', () => {
    it('should assign high confidence to exact pattern matches', () => {
      const result = parser.parse('15.03.2024');

      expect(result).not.toBeNull();
      expect(result!.confidence).toBeGreaterThanOrEqual(0.9);
    });

    it('should assign lower confidence to natural language parsing', () => {
      const result = parser.parse('yesterday');

      expect(result).not.toBeNull();
      expect(result!.confidence).toBeLessThan(0.9);
    });
  });

  describe('real-world Romanian certificate examples', () => {
    it('should parse typical SRAC certificate date format', () => {
      const text = 'Certificat SRAC Nr. 123/2024 emis la data de 15.03.2024';
      const result = parser.parse(text);

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
    });

    it('should parse validity period text', () => {
      const text = 'Valabil de la 01.01.2024 până la 31.12.2024';
      const results = parser.parseAll(text);

      expect(results).toHaveLength(2);
      expect(format(results[0].date, 'yyyy-MM-dd')).toBe('2024-01-01');
      expect(format(results[1].date, 'yyyy-MM-dd')).toBe('2024-12-31');
    });

    it('should parse expiry date with Romanian keywords', () => {
      const text = 'Data expirării: 30.06.2025';
      const result = parser.parse(text);

      expect(result).not.toBeNull();
      expect(format(result!.date, 'yyyy-MM-dd')).toBe('2025-06-30');
    });

    it('should handle multiple date formats in same certificate', () => {
      const text = `
        Certificat de Conformitate ISO 9001:2015
        Nr. Certificat: 123/2024
        Emis: 15 martie 2024
        Valabil până la: 14/03/2027
        Data următoarei evaluări: 2025-03-15
      `;
      const results = parser.parseAll(text);

      expect(results.length).toBeGreaterThanOrEqual(3);
      // Check that we found dates in different formats
      const formats = new Set(results.map(r => r.format));
      expect(formats.size).toBeGreaterThan(1);
    });
  });
});
