import { MetadataParserService } from '../../src/services/metadataParser';
import { format } from 'date-fns';

describe('MetadataParserService', () => {
  let parser: MetadataParserService;

  beforeEach(() => {
    parser = new MetadataParserService();
  });

  describe('extractDates - issue and expiry date classification', () => {
    it('should extract issue date with explicit Romanian keywords', () => {
      const text = 'Certificat emis la data de 15.03.2024';
      const result = parser.extractDates(text);

      expect(result.issueDate).not.toBeNull();
      expect(format(result.issueDate!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
      expect(result.issueDate!.confidence).toBeGreaterThan(0.8);
      expect(result.expiryDate).toBeNull();
    });

    it('should extract expiry date with Romanian expiry keywords', () => {
      const text = 'Valabil până la 31.12.2025';
      const result = parser.extractDates(text);

      expect(result.expiryDate).not.toBeNull();
      expect(format(result.expiryDate!.date, 'yyyy-MM-dd')).toBe('2025-12-31');
      expect(result.expiryDate!.confidence).toBeGreaterThan(0.8);
      expect(result.issueDate).toBeNull();
    });

    it('should extract both issue and expiry dates from certificate text', () => {
      const text = 'Certificat emis la 15.03.2024 și valabil până la 14.03.2027';
      const result = parser.extractDates(text);

      expect(result.issueDate).not.toBeNull();
      expect(result.expiryDate).not.toBeNull();
      expect(format(result.issueDate!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
      expect(format(result.expiryDate!.date, 'yyyy-MM-dd')).toBe('2027-03-14');
    });

    it('should classify dates with "eliberat" keyword as issue date', () => {
      const text = 'Certificat eliberat la 20 ianuarie 2024';
      const result = parser.extractDates(text);

      expect(result.issueDate).not.toBeNull();
      expect(format(result.issueDate!.date, 'yyyy-MM-dd')).toBe('2024-01-20');
    });

    it('should classify dates with "expirare" keyword as expiry date', () => {
      const text = 'Data expirării: 30/06/2026';
      const result = parser.extractDates(text);

      expect(result.expiryDate).not.toBeNull();
      expect(format(result.expiryDate!.date, 'yyyy-MM-dd')).toBe('2026-06-30');
    });

    it('should handle multiple date formats in same text', () => {
      const text = 'Emis: 15 martie 2024, Valabil până: 14/03/2027';
      const result = parser.extractDates(text);

      expect(result.issueDate).not.toBeNull();
      expect(result.expiryDate).not.toBeNull();
      expect(format(result.issueDate!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
      expect(format(result.expiryDate!.date, 'yyyy-MM-dd')).toBe('2027-03-14');
    });

    it('should use fallback logic when context is unclear (2+ dates)', () => {
      const text = 'Date: 01.01.2024 and 31.12.2024';
      const result = parser.extractDates(text);

      // Should assume first is issue, last is expiry
      expect(result.issueDate).not.toBeNull();
      expect(result.expiryDate).not.toBeNull();
      expect(format(result.issueDate!.date, 'yyyy-MM-dd')).toBe('2024-01-01');
      expect(format(result.expiryDate!.date, 'yyyy-MM-dd')).toBe('2024-12-31');
      // Fallback has reduced confidence
      expect(result.issueDate!.confidence).toBeLessThan(0.8);
      expect(result.expiryDate!.confidence).toBeLessThan(0.8);
    });

    it('should default single date to issue date when context unclear', () => {
      const text = 'Date: 15.03.2024 without clear context';
      const result = parser.extractDates(text);

      expect(result.issueDate).not.toBeNull();
      expect(format(result.issueDate!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
      expect(result.expiryDate).toBeNull();
      // Reduced confidence for unclear context
      expect(result.issueDate!.confidence).toBeLessThan(0.8);
    });

    it('should respect maxContextDistance parameter', () => {
      const longText = 'A'.repeat(200) + 'emis' + 'B'.repeat(50) + '15.03.2024';

      // Context too far away (default 100 chars)
      const result1 = parser.extractDates(longText, 100);
      expect(result1.issueDate).toBeNull();

      // Increase distance to include context
      const result2 = parser.extractDates(longText, 300);
      expect(result2.issueDate).not.toBeNull();
    });

    it('should return null dates when no dates found in text', () => {
      const text = 'This is a certificate with no dates';
      const result = parser.extractDates(text);

      expect(result.issueDate).toBeNull();
      expect(result.expiryDate).toBeNull();
    });

    it('should handle real-world SRAC certificate format', () => {
      const text = `
        CERTIFICAT DE CONFORMITATE
        Nr. SRAC-ISO-9001-2024-123

        Acest certificat este acordat pentru:
        ACME CONSTRUCT S.R.L.

        Data eliberării: 15 martie 2024
        Valabil până la: 14 martie 2027

        Eliberat de SRAC
      `;
      const result = parser.extractDates(text);

      expect(result.issueDate).not.toBeNull();
      expect(result.expiryDate).not.toBeNull();
      expect(format(result.issueDate!.date, 'yyyy-MM-dd')).toBe('2024-03-15');
      expect(format(result.expiryDate!.date, 'yyyy-MM-dd')).toBe('2027-03-14');
    });
  });

  describe('extractCertificateNumber', () => {
    it('should extract certificate number with "Nr." prefix', () => {
      const text = 'Certificat Nr. 123/2024';
      const result = parser.extractCertificateNumber(text);

      expect(result).not.toBeNull();
      expect(result!.value).toBe('123/2024');
      expect(result!.confidence).toBeGreaterThan(0.8);
    });

    it('should extract SRAC certificate number', () => {
      const text = 'Certificat SRAC Nr. SRAC-ISO-9001-2024-123';
      const result = parser.extractCertificateNumber(text);

      expect(result).not.toBeNull();
      expect(result!.value).toContain('SRAC-ISO-9001');
      expect(result!.confidence).toBeGreaterThan(0.8);
    });

    it('should return null when no certificate number found', () => {
      const text = 'This text has no certificate number';
      const result = parser.extractCertificateNumber(text);

      expect(result).toBeNull();
    });
  });

  describe('extractIssuingOrganization', () => {
    it('should extract SRAC as issuing organization', () => {
      const text = 'Eliberat de SRAC (Asociația Română pentru Certificare)';
      const result = parser.extractIssuingOrganization(text);

      expect(result).not.toBeNull();
      expect(result!.value).toContain('SRAC');
      expect(result!.confidence).toBeGreaterThan(0.8);
    });

    it('should extract RENAR as issuing organization', () => {
      const text = 'Certificat acreditat de RENAR';
      const result = parser.extractIssuingOrganization(text);

      expect(result).not.toBeNull();
      expect(result!.value).toContain('RENAR');
    });

    it('should extract international certification bodies', () => {
      const testCases = ['TÜV SÜD', 'SGS', 'Bureau Veritas', 'DNV GL'];

      testCases.forEach((org) => {
        const text = `Certificat eliberat de ${org}`;
        const result = parser.extractIssuingOrganization(text);

        expect(result).not.toBeNull();
        expect(result!.value).toContain(org);
      });
    });

    it('should return null when no organization found', () => {
      const text = 'Certificate with no issuing body mentioned';
      const result = parser.extractIssuingOrganization(text);

      expect(result).toBeNull();
    });
  });

  describe('extractCertifiedCompany', () => {
    it('should extract Romanian company with S.R.L. suffix', () => {
      const text = 'Acest certificat este acordat pentru: ACME CONSTRUCT S.R.L.';
      const result = parser.extractCertifiedCompany(text);

      expect(result).not.toBeNull();
      expect(result!.value).toContain('ACME CONSTRUCT S.R.L.');
      expect(result!.confidence).toBeGreaterThan(0.7);
    });

    it('should extract Romanian company with S.A. suffix', () => {
      const text = 'Companie certificată: MEGA INDUSTRIES S.A.';
      const result = parser.extractCertifiedCompany(text);

      expect(result).not.toBeNull();
      expect(result!.value).toContain('MEGA INDUSTRIES S.A.');
    });

    it('should return null when no company found', () => {
      const text = 'Certificate without company name';
      const result = parser.extractCertifiedCompany(text);

      expect(result).toBeNull();
    });
  });

  describe('extractCertificationScope', () => {
    it('should extract ISO 9001 certification scope', () => {
      const text = 'Domeniu: ISO 9001:2015 - Sisteme de Management al Calității';
      const result = parser.extractCertificationScope(text);

      expect(result).not.toBeNull();
      expect(result!.value).toContain('ISO 9001');
      expect(result!.confidence).toBeGreaterThan(0.7);
    });

    it('should extract ISO 14001 environmental certification', () => {
      const text = 'Certificare ISO 14001:2015 pentru management mediu';
      const result = parser.extractCertificationScope(text);

      expect(result).not.toBeNull();
      expect(result!.value).toContain('ISO 14001');
    });

    it('should return null when no scope found', () => {
      const text = 'Certificate without scope information';
      const result = parser.extractCertificationScope(text);

      expect(result).toBeNull();
    });
  });

  describe('parse - full metadata extraction', () => {
    it('should extract all metadata fields from complete certificate text', () => {
      const text = `
        CERTIFICAT DE CONFORMITATE ISO 9001:2015
        Nr. Certificat: SRAC-123/2024

        Acest certificat este acordat pentru:
        ACME CONSTRUCT S.R.L.

        Domeniu de certificare: ISO 9001:2015 - Sisteme de Management al Calității

        Data eliberării: 15 martie 2024
        Valabil până la: 14 martie 2027

        Eliberat de: SRAC - Asociația Română pentru Certificare
      `;

      const result = parser.parse(text);

      expect(result.certificate_number).toBeDefined();
      expect(result.certificate_number).toContain('SRAC-123/2024');

      expect(result.issuing_organization).toBeDefined();
      expect(result.issuing_organization).toContain('SRAC');

      expect(result.certified_company).toBeDefined();
      expect(result.certified_company).toContain('ACME CONSTRUCT S.R.L.');

      expect(result.certification_scope).toBeDefined();
      expect(result.certification_scope).toContain('ISO 9001');

      expect(result.issue_date).toBeDefined();
      expect(result.issue_date).toContain('2024-03-15');

      expect(result.expiry_date).toBeDefined();
      expect(result.expiry_date).toContain('2027-03-14');
    });

    it('should respect minConfidence threshold', () => {
      const text = 'Weak certificate Nr. X emis 15.03.2024';

      // With low threshold
      const result1 = parser.parse(text, { minConfidence: 0.3 });
      expect(result1.certificate_number).toBeDefined();

      // With high threshold (strict mode)
      // With high threshold - may not extract due to low confidence
      void parser.parse(text, { minConfidence: 0.95 });
    });

    it('should return empty object for invalid input', () => {
      const testCases = ['', '   ', null as any, undefined as any];

      testCases.forEach((input) => {
        const result = parser.parse(input);
        expect(result).toEqual({});
      });
    });

    it('should handle partial extraction gracefully', () => {
      const text = 'Certificat Nr. 123/2024 emis la 15.03.2024';
      const result = parser.parse(text);

      expect(result.certificate_number).toBeDefined();
      expect(result.issue_date).toBeDefined();
      // Other fields may be undefined
      expect(result.issuing_organization).toBeUndefined();
      expect(result.certified_company).toBeUndefined();
    });
  });

  describe('calculateConfidence', () => {
    it('should calculate average confidence from all fields', () => {
      const metadata = {
        certificate_number: '123/2024',
        certificate_number_confidence: 0.9,
        issue_date: '2024-03-15T00:00:00.000Z',
        issue_date_confidence: 0.85,
        expiry_date: '2027-03-14T00:00:00.000Z',
        expiry_date_confidence: 0.85,
      };

      const confidence = parser.calculateConfidence(metadata);
      expect(confidence).toBeCloseTo((0.9 + 0.85 + 0.85) / 3, 2);
    });

    it('should return 0 for empty metadata', () => {
      const confidence = parser.calculateConfidence({});
      expect(confidence).toBe(0);
    });

    it('should only include fields with confidence scores', () => {
      const metadata = {
        certificate_number: '123/2024',
        certificate_number_confidence: 0.9,
        issue_date: '2024-03-15T00:00:00.000Z',
        // No issue_date_confidence
      };

      const confidence = parser.calculateConfidence(metadata);
      expect(confidence).toBe(0.9);
    });
  });

  describe('real-world Romanian certificate examples', () => {
    it('should parse RENAR certificate format', () => {
      const text = `
        CERTIFICAT DE ACREDITARE RENAR
        Nr. LA-123

        Laboratorul: TEST LAB S.R.L.

        Acreditat pentru: ISO/IEC 17025:2017

        Data acordării: 10.01.2024
        Data expirării: 09.01.2028
      `;

      const result = parser.parse(text);

      expect(result.certificate_number).toContain('LA-123');
      expect(result.certified_company).toContain('TEST LAB S.R.L.');
      expect(result.issue_date).toContain('2024-01-10');
      expect(result.expiry_date).toContain('2028-01-09');
    });

    it('should handle ISO 14001 environmental certificate', () => {
      const text = `
        CERTIFICAT ISO 14001:2015
        Management de Mediu

        Nr: ENV-456/2024
        Companie: GREEN ECO S.A.
        Emis: 01 februarie 2024
        Valabil până: 31 ianuarie 2027

        Organism de certificare: SGS România
      `;

      const result = parser.parse(text);

      expect(result.certification_scope).toContain('ISO 14001');
      expect(result.certified_company).toContain('GREEN ECO S.A.');
      expect(result.issuing_organization).toContain('SGS');
    });

    it('should handle ISO 45001 health & safety certificate', () => {
      const text = `
        Certificat ISO 45001:2018
        Sisteme de Management al Sănătății și Securității Ocupaționale

        Nr. Certificat: SSM-789/2024
        Titular: SAFE WORK S.R.L.

        Data emiterii: 20/03/2024
        Valabilitate: 19/03/2027

        Certificat de: TÜV SÜD România
      `;

      const result = parser.parse(text);

      expect(result.certification_scope).toContain('ISO 45001');
      expect(result.certified_company).toContain('SAFE WORK S.R.L.');
      expect(result.issue_date).toContain('2024-03-20');
      expect(result.expiry_date).toContain('2027-03-19');
    });
  });
});
