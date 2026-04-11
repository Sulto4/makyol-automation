# Romanian Certificate Test Fixtures

This directory contains sample Romanian ISO certificates for testing the PDF text extraction pipeline.

## Test Certificates Overview

### 1. romanian-cert.pdf
- **Standard**: ISO 9001:2015
- **Certificate Number**: ISO-RO-2024-12345
- **Company**: SC MAKYOL CONSTRUCT SRL
- **Issuing Org**: SRAC (Asociația Română pentru Certificare și Acreditare)
- **Issue Date**: 15.03.2024 (dd.MM.yyyy format)
- **Expiry Date**: 15.03.2027
- **Scope**: Proiectare, execuție și montaj de instalații pentru construcții
- **CUI**: RO12345678

### 2. cert-sample-1.pdf
- **Standard**: ISO 14001:2015 (Environmental Management)
- **Certificate Number**: ENV-RO-2023-78901
- **Company**: SC CONSTRUCȚII PREMIUM SRL
- **Issuing Org**: SRAC (Societatea Română de Asigurare a Calității)
- **Issue Date**: 20/06/2023 (dd/MM/yyyy format - alternative Romanian format)
- **Expiry Date**: 20/06/2026
- **Scope**: Execuție de lucrări de construcții civile și industriale
- **CUI**: RO23456789

### 3. cert-sample-2.pdf
- **Standard**: ISO 45001:2018 (Occupational Health & Safety)
- **Certificate Number**: OHSAS-2024-56789
- **Company**: MAKYOL INFRASTRUCTURE SRL
- **Issuing Org**: ACAR (Asociația de Certificare și Acreditare din România)
- **Issue Date**: 10.01.2024 (dd.MM.yyyy format)
- **Expiry Date**: 10.01.2027
- **Scope**: Proiectare și execuție de infrastructură rutieră și feroviară
- **CUI**: RO34567890

### 4. cert-sample-3.pdf
- **Standard**: ISO 9001:2015
- **Certificate Number**: QMS-RO-2025-11223
- **Company**: SC INSTALAȚII MODERNE SRL
- **Issuing Org**: RENAR (Asociația de Normalizare și Certificare)
- **Issue Date**: 05.11.2025 (dd.MM.yyyy format)
- **Expiry Date**: 05.11.2028
- **Scope**: Proiectare instalații sanitare, termice și de ventilație
- **CUI**: RO45678901

### 5. cert-sample-4.pdf
- **Standard**: ISO 27001:2013 (Information Security)
- **Certificate Number**: ISMS-2024-99887
- **Company**: MAKYOL DIGITAL SERVICES SRL
- **Issuing Org**: ARS (Asociația Română pentru Standarde)
- **Issue Date**: 30-08-2024 (dd-MM-yyyy format - alternative format)
- **Expiry Date**: 30-08-2027
- **Scope**: Furnizare servicii de dezvoltare software și securitate
- **CUI**: RO56789012

## Date Format Variations

The test set includes multiple Romanian date formats to ensure robust parsing:
- **dd.MM.yyyy** - Most common format (e.g., 15.03.2024)
- **dd/MM/yyyy** - Alternative slash format (e.g., 20/06/2023)
- **dd-MM-yyyy** - Alternative dash format (e.g., 30-08-2024)
- **dd Month yyyy** - Written month names in Romanian (e.g., "15 martie 2024")

## Issuing Organizations

The certificates represent different Romanian certification bodies:
- **SRAC** - Societatea/Asociația Română de Asigurare a Calității
- **ACAR** - Asociația de Certificare și Acreditare din România
- **RENAR** - Asociația de Normalizare și Certificare
- **ARS** - Asociația Română pentru Standarde

## Testing Criteria

To meet the **80%+ success rate** requirement, the extraction pipeline must successfully extract:
1. **Certificate Number** - Unique identifier (e.g., ISO-RO-2024-12345)
2. **Issuing Organization** - Certification body name
3. **Issue Date** - Certificate issuance date
4. **Expiry Date** - Certificate expiration/validity date
5. **Company Name** - Certified organization
6. **Certification Scope** - Description of certified activities

Success is defined as correctly extracting at least 4 out of 5 certificates (80%) for each metadata field.

## Usage

Run the success rate verification test:
```bash
npm test -- certificate-success-rate.test.ts
```

This will process all 5 certificates and generate a detailed report showing:
- Success rate per metadata field
- Detailed extraction results for each certificate
- Overall pass/fail status against 80% target
