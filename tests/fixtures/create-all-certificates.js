// Script to create all Romanian certificate PDFs
const fs = require('fs');
const path = require('path');

function createPDF(contentFile, outputFile) {
  const content = fs.readFileSync(path.join(__dirname, contentFile), 'utf8');

  // Create a simple PDF with the Romanian certificate content
  // This is a minimal but valid PDF structure that pdf-parse can extract from
  const lines = content.split('\n');
  const textContent = lines.map((line) => {
    const escapedLine = line.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');
    return `(${escapedLine}) Tj\n0 -15 Td`;
  }).join('\n');

  const streamContent = `BT
/F1 12 Tf
50 750 Td
${textContent}
ET`;

  const pdfContent = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length ${streamContent.length}
>>
stream
${streamContent}
endstream
endobj

xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
${850 + streamContent.length}
%%EOF`;

  const outputPath = path.join(__dirname, outputFile);
  fs.writeFileSync(outputPath, pdfContent);
  console.log(`PDF created: ${outputFile} (${pdfContent.length} bytes)`);
  return outputPath;
}

// Create all certificate PDFs
console.log('Creating Romanian certificate PDFs...\n');

createPDF('cert-sample-1-content.txt', 'cert-sample-1.pdf');
createPDF('cert-sample-2-content.txt', 'cert-sample-2.pdf');
createPDF('cert-sample-3-content.txt', 'cert-sample-3.pdf');
createPDF('cert-sample-4-content.txt', 'cert-sample-4.pdf');

console.log('\n✓ All certificate PDFs created successfully!');
console.log('\nTotal certificates available:');
console.log('  1. romanian-cert.pdf (ISO 9001:2015 - MAKYOL CONSTRUCT)');
console.log('  2. cert-sample-1.pdf (ISO 14001:2015 - CONSTRUCȚII PREMIUM)');
console.log('  3. cert-sample-2.pdf (ISO 45001:2018 - MAKYOL INFRASTRUCTURE)');
console.log('  4. cert-sample-3.pdf (ISO 9001:2015 - INSTALAȚII MODERNE)');
console.log('  5. cert-sample-4.pdf (ISO 27001:2013 - MAKYOL DIGITAL SERVICES)');
