import { Pool } from 'pg';
import { AuditLogModel, ActionType, EntityType, CreateAuditLogInput, AuditLog } from '../models/AuditLog';

/**
 * Document upload metadata for audit logging
 */
export interface DocumentUploadMetadata {
  filename: string;
  original_filename?: string;
  file_size: number;
  file_path?: string;
  supplier_id?: number;
  document_type?: string;
}

/**
 * Document status change metadata for audit logging
 */
export interface DocumentStatusChangeMetadata {
  document_id: number;
  filename: string;
  previous_status: string;
  new_status: string;
  reason?: string;
}

/**
 * Document delete metadata for audit logging
 */
export interface DocumentDeleteMetadata {
  document_id: number;
  filename: string;
  file_path: string;
  supplier_id?: number;
  processing_status?: string;
}

/**
 * Compliance check metadata for audit logging
 */
export interface ComplianceCheckMetadata {
  document_id: number;
  check_type: string;
  result: 'pass' | 'fail' | 'warning';
  details?: Record<string, any>;
  duration_ms?: number;
}

/**
 * Report generation metadata for audit logging
 */
export interface ReportGenerationMetadata {
  report_type: string;
  format: string;
  filters?: Record<string, any>;
  result_count?: number;
  file_path?: string;
}

/**
 * User login metadata for audit logging
 */
export interface UserLoginMetadata {
  user_id: string;
  username?: string;
  ip_address?: string;
  user_agent?: string;
  success: boolean;
  failure_reason?: string;
}

/**
 * Configuration change metadata for audit logging
 */
export interface ConfigChangeMetadata {
  config_key: string;
  config_section?: string;
  previous_value?: any;
  new_value: any;
  reason?: string;
}

/**
 * Audit Service
 *
 * Provides standardized methods for creating audit log entries across the application.
 * All audit operations are immutable - logs cannot be modified or deleted once created.
 */
export class AuditService {
  private auditLogModel: AuditLogModel;

  constructor(pool: Pool) {
    this.auditLogModel = new AuditLogModel(pool);
  }

  /**
   * Log a document upload event
   *
   * @param metadata - Document upload metadata
   * @param userId - Optional user ID performing the upload
   * @returns Created audit log entry
   *
   * @example
   * await auditService.logDocumentUpload({
   *   filename: 'certificate.pdf',
   *   file_size: 1024000,
   *   supplier_id: 42
   * }, 'user-123');
   */
  async logDocumentUpload(
    metadata: DocumentUploadMetadata,
    userId?: string | null
  ): Promise<AuditLog> {
    const input: CreateAuditLogInput = {
      user_id: userId,
      action_type: ActionType.DOCUMENT_UPLOAD,
      entity_type: EntityType.DOCUMENT,
      entity_id: null, // Document ID not yet known at upload time
      metadata: {
        filename: metadata.filename,
        original_filename: metadata.original_filename,
        file_size: metadata.file_size,
        file_path: metadata.file_path,
        supplier_id: metadata.supplier_id,
        document_type: metadata.document_type,
      },
    };

    return await this.auditLogModel.create(input);
  }

  /**
   * Log a document status change event
   *
   * @param metadata - Document status change metadata
   * @param userId - Optional user ID performing the change
   * @returns Created audit log entry
   *
   * @example
   * await auditService.logDocumentStatusChange({
   *   document_id: 42,
   *   filename: 'certificate.pdf',
   *   previous_status: 'pending',
   *   new_status: 'verified'
   * }, 'user-123');
   */
  async logDocumentStatusChange(
    metadata: DocumentStatusChangeMetadata,
    userId?: string | null
  ): Promise<AuditLog> {
    const input: CreateAuditLogInput = {
      user_id: userId,
      action_type: ActionType.DOCUMENT_STATUS_CHANGE,
      entity_type: EntityType.DOCUMENT,
      entity_id: metadata.document_id,
      before_value: {
        status: metadata.previous_status,
      },
      after_value: {
        status: metadata.new_status,
      },
      metadata: {
        filename: metadata.filename,
        reason: metadata.reason,
      },
    };

    return await this.auditLogModel.create(input);
  }

  /**
   * Log a document deletion event
   *
   * @param metadata - Document delete metadata
   * @param userId - Optional user ID performing the deletion
   * @returns Created audit log entry
   *
   * @example
   * await auditService.logDocumentDelete({
   *   document_id: 42,
   *   filename: 'certificate.pdf',
   *   file_path: '/uploads/cert.pdf'
   * }, 'user-123');
   */
  async logDocumentDelete(
    metadata: DocumentDeleteMetadata,
    userId?: string | null
  ): Promise<AuditLog> {
    const input: CreateAuditLogInput = {
      user_id: userId,
      action_type: ActionType.DOCUMENT_DELETE,
      entity_type: EntityType.DOCUMENT,
      entity_id: metadata.document_id,
      before_value: {
        filename: metadata.filename,
        file_path: metadata.file_path,
        supplier_id: metadata.supplier_id,
        processing_status: metadata.processing_status,
      },
      after_value: null,
      metadata: {
        deleted_at: new Date().toISOString(),
      },
    };

    return await this.auditLogModel.create(input);
  }

  /**
   * Log a compliance check execution event
   *
   * @param metadata - Compliance check metadata
   * @param userId - Optional user ID performing the check
   * @returns Created audit log entry
   *
   * @example
   * await auditService.logComplianceCheck({
   *   document_id: 42,
   *   check_type: 'certificate_validation',
   *   result: 'pass',
   *   details: { confidence: 0.95 }
   * }, 'user-123');
   */
  async logComplianceCheck(
    metadata: ComplianceCheckMetadata,
    userId?: string | null
  ): Promise<AuditLog> {
    const input: CreateAuditLogInput = {
      user_id: userId,
      action_type: ActionType.COMPLIANCE_CHECK_EXECUTION,
      entity_type: EntityType.COMPLIANCE_CHECK,
      entity_id: metadata.document_id,
      metadata: {
        check_type: metadata.check_type,
        result: metadata.result,
        details: metadata.details,
        duration_ms: metadata.duration_ms,
        executed_at: new Date().toISOString(),
      },
    };

    return await this.auditLogModel.create(input);
  }

  /**
   * Log a report generation event
   *
   * @param metadata - Report generation metadata
   * @param userId - Optional user ID generating the report
   * @returns Created audit log entry
   *
   * @example
   * await auditService.logReportGeneration({
   *   report_type: 'compliance_summary',
   *   format: 'pdf',
   *   filters: { date_range: '2024-01-01 to 2024-12-31' },
   *   result_count: 150
   * }, 'user-123');
   */
  async logReportGeneration(
    metadata: ReportGenerationMetadata,
    userId?: string | null
  ): Promise<AuditLog> {
    const input: CreateAuditLogInput = {
      user_id: userId,
      action_type: ActionType.REPORT_GENERATION,
      entity_type: EntityType.REPORT,
      entity_id: null,
      metadata: {
        report_type: metadata.report_type,
        format: metadata.format,
        filters: metadata.filters,
        result_count: metadata.result_count,
        file_path: metadata.file_path,
        generated_at: new Date().toISOString(),
      },
    };

    return await this.auditLogModel.create(input);
  }

  /**
   * Log a user login event
   *
   * @param metadata - User login metadata
   * @returns Created audit log entry
   *
   * @example
   * await auditService.logUserLogin({
   *   user_id: 'user-123',
   *   username: 'john.doe',
   *   ip_address: '192.168.1.1',
   *   success: true
   * });
   */
  async logUserLogin(metadata: UserLoginMetadata): Promise<AuditLog> {
    const input: CreateAuditLogInput = {
      user_id: metadata.user_id,
      action_type: ActionType.USER_LOGIN,
      entity_type: EntityType.USER,
      entity_id: null,
      metadata: {
        username: metadata.username,
        ip_address: metadata.ip_address,
        user_agent: metadata.user_agent,
        success: metadata.success,
        failure_reason: metadata.failure_reason,
        login_at: new Date().toISOString(),
      },
    };

    return await this.auditLogModel.create(input);
  }

  /**
   * Log a configuration change event
   *
   * @param metadata - Configuration change metadata
   * @param userId - Optional user ID making the change
   * @returns Created audit log entry
   *
   * @example
   * await auditService.logConfigChange({
   *   config_key: 'max_file_size',
   *   config_section: 'upload_settings',
   *   previous_value: 5242880,
   *   new_value: 10485760,
   *   reason: 'Increased for large certificates'
   * }, 'user-123');
   */
  async logConfigChange(
    metadata: ConfigChangeMetadata,
    userId?: string | null
  ): Promise<AuditLog> {
    const input: CreateAuditLogInput = {
      user_id: userId,
      action_type: ActionType.CONFIG_CHANGE,
      entity_type: EntityType.CONFIG,
      entity_id: null,
      before_value: metadata.previous_value !== undefined
        ? { [metadata.config_key]: metadata.previous_value }
        : null,
      after_value: {
        [metadata.config_key]: metadata.new_value,
      },
      metadata: {
        config_key: metadata.config_key,
        config_section: metadata.config_section,
        reason: metadata.reason,
        changed_at: new Date().toISOString(),
      },
    };

    return await this.auditLogModel.create(input);
  }

  /**
   * Get the underlying AuditLogModel for advanced queries
   *
   * @returns AuditLogModel instance
   */
  getModel(): AuditLogModel {
    return this.auditLogModel;
  }
}
