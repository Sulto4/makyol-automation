# Task 029: Add Batch Reprocessing & Database Query Endpoints

## Priority: MEDIUM (P2)
## Estimated effort: 3-4 hours
## Depends on: Tasks 025-028

## Problem

After fixing the pipeline (Tasks 025-028), we need to reprocess the ~300 documents that were already uploaded with the broken pipeline. Currently there's no way to:
1. Reprocess existing documents without re-uploading
2. Query the database for extraction statistics
3. Compare before/after results

## Requirements

### 1. Add reprocessing endpoint to backend

`POST /api/documents/:id/reprocess`

```typescript
// In documentController.ts
async reprocessDocument(req: Request, res: Response, next: NextFunction): Promise<void> {
    const documentId = parseInt(req.params.id, 10);
    const document = await this.documentModel.findById(documentId);
    
    if (!document) {
        res.status(404).json({ error: { message: 'Document not found' } });
        return;
    }
    
    // Re-send to pipeline
    const pipelineResponse = await this.pipelineClient.processDocument(document.file_path);
    
    // Update classification
    await this.documentModel.updateClassification(document.id, {
        categorie: pipelineResponse.classification,
        confidence: pipelineResponse.confidence,
        metoda_clasificare: pipelineResponse.method,
    });
    
    // Update extraction results
    await this.extractionResultModel.updateByDocumentId(document.id, {
        material: pipelineResponse.extraction?.material ?? null,
        companie: pipelineResponse.extraction?.companie ?? null,
        // ... all fields
    });
    
    res.json({ document: updatedDocument, extraction: updatedExtraction });
}
```

### 2. Add batch reprocessing endpoint

`POST /api/documents/reprocess-all`

```typescript
async reprocessAll(req: Request, res: Response, next: NextFunction): Promise<void> {
    const { status, limit } = req.body; // Optional filters
    
    // Get documents to reprocess
    const documents = await this.documentModel.findAll(
        limit || 500, 0, 
        status || undefined // e.g., 'completed' to reprocess all, or 'failed' for failures only
    );
    
    // Process in background, return immediately
    res.json({ 
        message: `Reprocessing ${documents.length} documents`,
        jobId: jobId,
    });
    
    // Process documents sequentially with delay to avoid rate limits
    for (const doc of documents) {
        try {
            await this.reprocessSingleDocument(doc);
            await new Promise(r => setTimeout(r, 1000)); // 1s delay between docs
        } catch (e) {
            logger.error(`Reprocess failed for ${doc.id}: ${e}`);
        }
    }
}
```

### 3. Add statistics endpoint to backend

`GET /api/documents/stats`

```typescript
async getStats(req: Request, res: Response, next: NextFunction): Promise<void> {
    const stats = await this.pool.query(`
        SELECT 
            COUNT(*) as total_documents,
            COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as completed,
            COUNT(CASE WHEN processing_status = 'failed' THEN 1 END) as failed,
            COUNT(CASE WHEN categorie IS NOT NULL THEN 1 END) as classified,
            COUNT(CASE WHEN categorie = 'ALTELE' THEN 1 END) as altele,
            COUNT(CASE WHEN metoda_clasificare = 'filename_regex' THEN 1 END) as by_filename,
            COUNT(CASE WHEN metoda_clasificare = 'text_rules' THEN 1 END) as by_text,
            COUNT(CASE WHEN metoda_clasificare = 'ai' THEN 1 END) as by_ai,
            COUNT(CASE WHEN metoda_clasificare = 'filename+text_agree' THEN 1 END) as by_hybrid,
            AVG(confidence) as avg_confidence
        FROM documents
    `);
    
    const extractionStats = await this.pool.query(`
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN companie IS NOT NULL THEN 1 END) as has_companie,
            COUNT(CASE WHEN material IS NOT NULL THEN 1 END) as has_material,
            COUNT(CASE WHEN data_expirare IS NOT NULL THEN 1 END) as has_data_expirare,
            COUNT(CASE WHEN producator IS NOT NULL THEN 1 END) as has_producator,
            COUNT(CASE WHEN distribuitor IS NOT NULL THEN 1 END) as has_distribuitor,
            COUNT(CASE WHEN adresa_producator IS NOT NULL THEN 1 END) as has_adresa
        FROM extraction_results
    `);
    
    res.json({
        classification: stats.rows[0],
        extraction: extractionStats.rows[0],
    });
}
```

### 4. Add stats display to frontend dashboard

The frontend Dashboard page should call `GET /api/documents/stats` and display:
- Total documents processed
- Classification breakdown by method (pie chart)
- Extraction fill rates (bar chart)
- Category distribution

### 5. Add ExtractionResult update method to model

The `ExtractionResultModel` currently only has `create()` and `findByDocumentId()`. Add:

```typescript
async updateByDocumentId(documentId: number, fields: Partial<CreateExtractionResultInput>): Promise<ExtractionResult> {
    // UPDATE extraction_results SET ... WHERE document_id = $1
}
```

## Verification

1. `GET /api/documents/stats` returns correct counts
2. `POST /api/documents/1/reprocess` successfully reprocesses and updates DB
3. `POST /api/documents/reprocess-all` processes all documents with progress logging
4. Frontend dashboard shows statistics

## Files to modify

- `src/controllers/documentController.ts` — add reprocess and stats endpoints
- `src/models/ExtractionResult.ts` — add updateByDocumentId method
- `src/routes/documents.ts` — register new routes
- `frontend/src/pages/Dashboard.tsx` — add stats display
- `frontend/src/api/documents.ts` — add API calls for new endpoints
