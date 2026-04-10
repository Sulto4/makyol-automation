// Script to create a Romanian certificate PDF
const fs = require('fs');
const path = require('path');

const content = fs.readFileSync(path.join(__dirname, 'romanian-cert-content.txt'), 'utf8');

// Create a simple PDF with the Romanian certificate content
// This is a minimal but valid PDF structure that pdf-parse can extract from
const lines = content.split('\n');
const textContent = lines.map((line, idx) => {
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

const outputPath = path.join(__dirname, 'romanian-cert.pdf');
fs.writeFileSync(outputPath, pdfContent);
console.log(`PDF created at: ${outputPath}`);
console.log(`PDF size: ${pdfContent.length} bytes`);
