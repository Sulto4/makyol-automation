declare module 'pdf-parse' {
  interface PDFInfo {
    [key: string]: any;
  }

  interface PDFMetadata {
    [key: string]: any;
  }

  interface PDFData {
    numpages: number;
    numrender: number;
    info: PDFInfo;
    metadata: PDFMetadata | null;
    text: string;
    version: string;
  }

  interface PDFParseOptions {
    max?: number;
    version?: string;
    pagerender?: (pageData: any) => Promise<string>;
  }

  function pdfParse(
    dataBuffer: Buffer,
    options?: PDFParseOptions
  ): Promise<PDFData>;

  export = pdfParse;
}
