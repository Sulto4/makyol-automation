import { Pool } from 'pg';
import {
  AuditService,
  DocumentUploadMetadata,
  DocumentStatusChangeMetadata,
  DocumentDeleteMetadata,
  ComplianceCheckMetadata,
  ReportGenerationMetadata,
  UserLoginMetadata,
  ConfigChangeMetadata,
} from '../../src/services/auditService';
import { AuditLogModel, ActionType, EntityType, AuditLog } from '../../src/models/AuditLog';

// Mock the AuditLogModel
jest.mock('../../src/models/AuditLog');

describe('AuditService', () => {
  let pool: Pool;
  let auditService: AuditService;
  let mockAuditLogModel: jest.Mocked<AuditLogModel>;

  beforeEach(() => {
    pool = new Pool();
    auditService = new AuditService(pool);
    mockAuditLogModel = (auditService as any).auditLogModel as jest.Mocked<AuditLogModel>;
    jest.clearAllMocks();
  });

  describe('logDocumentUpload', () => {
    it('should log document upload with all metadata', async () => {
      const metadata: DocumentUploadMetadata = {
        filename: 'certificate.pdf',
        original_filename: 'original_cert.pdf',
        file_size: 1024000,
        file_path: '/uploads/cert.pdf',
        supplier_id: 42,
        document_type: 'certificate',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'user-123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: {
          filename: metadata.filename,
          original_filename: metadata.original_filename,
          file_size: metadata.file_size,
          file_path: metadata.file_path,
          supplier_id: metadata.supplier_id,
          document_type: metadata.document_type,
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      const result = await auditService.logDocumentUpload(metadata, 'user-123');

      expect(result).toEqual(mockResult);
      expect(mockAuditLogModel.create).toHaveBeenCalledWith({
        user_id: 'user-123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: null,
        metadata: {
          filename: metadata.filename,
          original_filename: metadata.original_filename,
          file_size: metadata.file_size,
          file_path: metadata.file_path,
          supplier_id: metadata.supplier_id,
          document_type: metadata.document_type,
        },
      });
    });

    it('should log document upload without user ID', async () => {
      const metadata: DocumentUploadMetadata = {
        filename: 'test.pdf',
        file_size: 2048,
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: null,
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: {
          filename: metadata.filename,
          file_size: metadata.file_size,
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      const result = await auditService.logDocumentUpload(metadata);

      expect(result.user_id).toBeNull();
      expect(mockAuditLogModel.create).toHaveBeenCalledWith(
        expect.objectContaining({
          user_id: undefined,
        })
      );
    });

    it('should log document upload with minimal metadata', async () => {
      const metadata: DocumentUploadMetadata = {
        filename: 'minimal.pdf',
        file_size: 512,
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'user-456',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: {
          filename: metadata.filename,
          file_size: metadata.file_size,
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      await auditService.logDocumentUpload(metadata, 'user-456');

      expect(mockAuditLogModel.create).toHaveBeenCalledWith(
        expect.objectContaining({
          metadata: expect.objectContaining({
            filename: 'minimal.pdf',
            file_size: 512,
          }),
        })
      );
    });

    it('should set entity_id to null as document ID is not yet known', async () => {
      const metadata: DocumentUploadMetadata = {
        filename: 'test.pdf',
        file_size: 1024,
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: null,
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: {},
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      await auditService.logDocumentUpload(metadata);

      expect(mockAuditLogModel.create).toHaveBeenCalledWith(
        expect.objectContaining({
          entity_id: null,
        })
      );
    });
  });

  describe('logDocumentStatusChange', () => {
    it('should log document status change with all metadata', async () => {
      const metadata: DocumentStatusChangeMetadata = {
        document_id: 42,
        filename: 'certificate.pdf',
        previous_status: 'pending',
        new_status: 'verified',
        reason: 'Manual verification completed',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'user-123',
        action_type: ActionType.DOCUMENT_STATUS_CHANGE,
        entity_type: EntityType.DOCUMENT,
        entity_id: 42,
        before_value: { status: 'pending' },
        after_value: { status: 'verified' },
        metadata: {
          filename: metadata.filename,
          reason: metadata.reason,
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      const result = await auditService.logDocumentStatusChange(metadata, 'user-123');

      expect(result).toEqual(mockResult);
      expect(mockAuditLogModel.create).toHaveBeenCalledWith({
        user_id: 'user-123',
        action_type: ActionType.DOCUMENT_STATUS_CHANGE,
        entity_type: EntityType.DOCUMENT,
        entity_id: 42,
        before_value: { status: 'pending' },
        after_value: { status: 'verified' },
        metadata: {
          filename: metadata.filename,
          reason: metadata.reason,
        },
      });
    });

    it('should log status change without reason', async () => {
      const metadata: DocumentStatusChangeMetadata = {
        document_id: 10,
        filename: 'doc.pdf',
        previous_status: 'uploaded',
        new_status: 'processing',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: null,
        action_type: ActionType.DOCUMENT_STATUS_CHANGE,
        entity_type: EntityType.DOCUMENT,
        entity_id: 10,
        before_value: { status: 'uploaded' },
        after_value: { status: 'processing' },
        metadata: { filename: 'doc.pdf' },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      await auditService.logDocumentStatusChange(metadata);

      expect(mockAuditLogModel.create).toHaveBeenCalledWith(
        expect.objectContaining({
          before_value: { status: 'uploaded' },
          after_value: { status: 'processing' },
        })
      );
    });

    it('should include before and after values', async () => {
      const metadata: DocumentStatusChangeMetadata = {
        document_id: 5,
        filename: 'test.pdf',
        previous_status: 'draft',
        new_status: 'published',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'user-789',
        action_type: ActionType.DOCUMENT_STATUS_CHANGE,
        entity_type: EntityType.DOCUMENT,
        entity_id: 5,
        before_value: { status: 'draft' },
        after_value: { status: 'published' },
        metadata: { filename: 'test.pdf' },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      const result = await auditService.logDocumentStatusChange(metadata, 'user-789');

      expect(result.before_value).toEqual({ status: 'draft' });
      expect(result.after_value).toEqual({ status: 'published' });
    });
  });

  describe('logDocumentDelete', () => {
    it('should log document deletion with all metadata', async () => {
      const metadata: DocumentDeleteMetadata = {
        document_id: 42,
        filename: 'old_cert.pdf',
        file_path: '/uploads/old_cert.pdf',
        supplier_id: 10,
        processing_status: 'completed',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'user-123',
        action_type: ActionType.DOCUMENT_DELETE,
        entity_type: EntityType.DOCUMENT,
        entity_id: 42,
        before_value: {
          filename: metadata.filename,
          file_path: metadata.file_path,
          supplier_id: metadata.supplier_id,
          processing_status: metadata.processing_status,
        },
        after_value: null,
        metadata: { deleted_at: expect.any(String) },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      const result = await auditService.logDocumentDelete(metadata, 'user-123');

      expect(result).toBeDefined();
      expect(mockAuditLogModel.create).toHaveBeenCalledWith({
        user_id: 'user-123',
        action_type: ActionType.DOCUMENT_DELETE,
        entity_type: EntityType.DOCUMENT,
        entity_id: 42,
        before_value: {
          filename: metadata.filename,
          file_path: metadata.file_path,
          supplier_id: metadata.supplier_id,
          processing_status: metadata.processing_status,
        },
        after_value: null,
        metadata: {
          deleted_at: expect.any(String),
        },
      });
    });

    it('should set after_value to null for deletion', async () => {
      const metadata: DocumentDeleteMetadata = {
        document_id: 1,
        filename: 'test.pdf',
        file_path: '/uploads/test.pdf',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: null,
        action_type: ActionType.DOCUMENT_DELETE,
        entity_type: EntityType.DOCUMENT,
        entity_id: 1,
        before_value: {
          filename: 'test.pdf',
          file_path: '/uploads/test.pdf',
        },
        after_value: null,
        metadata: { deleted_at: new Date().toISOString() },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      const result = await auditService.logDocumentDelete(metadata);

      expect(result.after_value).toBeNull();
    });

    it('should include deleted_at timestamp in metadata', async () => {
      const metadata: DocumentDeleteMetadata = {
        document_id: 99,
        filename: 'delete_me.pdf',
        file_path: '/uploads/delete_me.pdf',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'admin',
        action_type: ActionType.DOCUMENT_DELETE,
        entity_type: EntityType.DOCUMENT,
        entity_id: 99,
        before_value: {
          filename: 'delete_me.pdf',
          file_path: '/uploads/delete_me.pdf',
        },
        after_value: null,
        metadata: { deleted_at: new Date().toISOString() },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      await auditService.logDocumentDelete(metadata, 'admin');

      expect(mockAuditLogModel.create).toHaveBeenCalledWith(
        expect.objectContaining({
          metadata: expect.objectContaining({
            deleted_at: expect.any(String),
          }),
        })
      );
    });
  });

  describe('logComplianceCheck', () => {
    it('should log compliance check with all metadata', async () => {
      const metadata: ComplianceCheckMetadata = {
        document_id: 42,
        check_type: 'certificate_validation',
        result: 'pass',
        details: { confidence: 0.95, criteria_met: ['date_valid', 'signature_valid'] },
        duration_ms: 250,
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'user-123',
        action_type: ActionType.COMPLIANCE_CHECK_EXECUTION,
        entity_type: EntityType.COMPLIANCE_CHECK,
        entity_id: 42,
        before_value: null,
        after_value: null,
        metadata: {
          check_type: metadata.check_type,
          result: metadata.result,
          details: metadata.details,
          duration_ms: metadata.duration_ms,
          executed_at: expect.any(String),
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      const result = await auditService.logComplianceCheck(metadata, 'user-123');

      expect(result).toBeDefined();
      expect(mockAuditLogModel.create).toHaveBeenCalledWith({
        user_id: 'user-123',
        action_type: ActionType.COMPLIANCE_CHECK_EXECUTION,
        entity_type: EntityType.COMPLIANCE_CHECK,
        entity_id: 42,
        metadata: {
          check_type: 'certificate_validation',
          result: 'pass',
          details: metadata.details,
          duration_ms: 250,
          executed_at: expect.any(String),
        },
      });
    });

    it('should log failed compliance check', async () => {
      const metadata: ComplianceCheckMetadata = {
        document_id: 10,
        check_type: 'expiry_check',
        result: 'fail',
        details: { reason: 'Certificate expired' },
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: null,
        action_type: ActionType.COMPLIANCE_CHECK_EXECUTION,
        entity_type: EntityType.COMPLIANCE_CHECK,
        entity_id: 10,
        before_value: null,
        after_value: null,
        metadata: {
          check_type: 'expiry_check',
          result: 'fail',
          details: { reason: 'Certificate expired' },
          executed_at: expect.any(String),
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      await auditService.logComplianceCheck(metadata);

      expect(mockAuditLogModel.create).toHaveBeenCalledWith(
        expect.objectContaining({
          metadata: expect.objectContaining({
            result: 'fail',
          }),
        })
      );
    });

    it('should log warning compliance check', async () => {
      const metadata: ComplianceCheckMetadata = {
        document_id: 5,
        check_type: 'quality_check',
        result: 'warning',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'system',
        action_type: ActionType.COMPLIANCE_CHECK_EXECUTION,
        entity_type: EntityType.COMPLIANCE_CHECK,
        entity_id: 5,
        before_value: null,
        after_value: null,
        metadata: {
          check_type: 'quality_check',
          result: 'warning',
          executed_at: new Date().toISOString(),
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      const result = await auditService.logComplianceCheck(metadata, 'system');

      expect(result.metadata.result).toBe('warning');
    });

    it('should include executed_at timestamp', async () => {
      const metadata: ComplianceCheckMetadata = {
        document_id: 1,
        check_type: 'test_check',
        result: 'pass',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: null,
        action_type: ActionType.COMPLIANCE_CHECK_EXECUTION,
        entity_type: EntityType.COMPLIANCE_CHECK,
        entity_id: 1,
        before_value: null,
        after_value: null,
        metadata: {
          check_type: 'test_check',
          result: 'pass',
          executed_at: new Date().toISOString(),
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      await auditService.logComplianceCheck(metadata);

      expect(mockAuditLogModel.create).toHaveBeenCalledWith(
        expect.objectContaining({
          metadata: expect.objectContaining({
            executed_at: expect.any(String),
          }),
        })
      );
    });
  });

  describe('logReportGeneration', () => {
    it('should log report generation with all metadata', async () => {
      const metadata: ReportGenerationMetadata = {
        report_type: 'compliance_summary',
        format: 'pdf',
        filters: { date_range: '2024-01-01 to 2024-12-31', status: 'verified' },
        result_count: 150,
        file_path: '/reports/compliance_2024.pdf',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'user-123',
        action_type: ActionType.REPORT_GENERATION,
        entity_type: EntityType.REPORT,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: {
          report_type: metadata.report_type,
          format: metadata.format,
          filters: metadata.filters,
          result_count: metadata.result_count,
          file_path: metadata.file_path,
          generated_at: expect.any(String),
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      const result = await auditService.logReportGeneration(metadata, 'user-123');

      expect(result).toBeDefined();
      expect(mockAuditLogModel.create).toHaveBeenCalledWith({
        user_id: 'user-123',
        action_type: ActionType.REPORT_GENERATION,
        entity_type: EntityType.REPORT,
        entity_id: null,
        metadata: {
          report_type: 'compliance_summary',
          format: 'pdf',
          filters: metadata.filters,
          result_count: 150,
          file_path: '/reports/compliance_2024.pdf',
          generated_at: expect.any(String),
        },
      });
    });

    it('should log report generation with minimal metadata', async () => {
      const metadata: ReportGenerationMetadata = {
        report_type: 'simple_list',
        format: 'csv',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: null,
        action_type: ActionType.REPORT_GENERATION,
        entity_type: EntityType.REPORT,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: {
          report_type: 'simple_list',
          format: 'csv',
          generated_at: new Date().toISOString(),
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      await auditService.logReportGeneration(metadata);

      expect(mockAuditLogModel.create).toHaveBeenCalledWith(
        expect.objectContaining({
          metadata: expect.objectContaining({
            report_type: 'simple_list',
            format: 'csv',
          }),
        })
      );
    });

    it('should set entity_id to null for reports', async () => {
      const metadata: ReportGenerationMetadata = {
        report_type: 'test',
        format: 'json',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'reporter',
        action_type: ActionType.REPORT_GENERATION,
        entity_type: EntityType.REPORT,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: {},
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      await auditService.logReportGeneration(metadata, 'reporter');

      expect(mockAuditLogModel.create).toHaveBeenCalledWith(
        expect.objectContaining({
          entity_id: null,
        })
      );
    });
  });

  describe('logUserLogin', () => {
    it('should log successful user login with all metadata', async () => {
      const metadata: UserLoginMetadata = {
        user_id: 'user-123',
        username: 'john.doe',
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0',
        success: true,
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'user-123',
        action_type: ActionType.USER_LOGIN,
        entity_type: EntityType.USER,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: {
          username: metadata.username,
          ip_address: metadata.ip_address,
          user_agent: metadata.user_agent,
          success: true,
          login_at: expect.any(String),
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      const result = await auditService.logUserLogin(metadata);

      expect(result).toBeDefined();
      expect(mockAuditLogModel.create).toHaveBeenCalledWith({
        user_id: 'user-123',
        action_type: ActionType.USER_LOGIN,
        entity_type: EntityType.USER,
        entity_id: null,
        metadata: {
          username: 'john.doe',
          ip_address: '192.168.1.100',
          user_agent: 'Mozilla/5.0',
          success: true,
          failure_reason: undefined,
          login_at: expect.any(String),
        },
      });
    });

    it('should log failed user login with failure reason', async () => {
      const metadata: UserLoginMetadata = {
        user_id: 'user-456',
        username: 'jane.doe',
        ip_address: '192.168.1.101',
        success: false,
        failure_reason: 'Invalid password',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'user-456',
        action_type: ActionType.USER_LOGIN,
        entity_type: EntityType.USER,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: {
          username: 'jane.doe',
          ip_address: '192.168.1.101',
          success: false,
          failure_reason: 'Invalid password',
          login_at: new Date().toISOString(),
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      const result = await auditService.logUserLogin(metadata);

      expect(result.metadata.success).toBe(false);
      expect(result.metadata.failure_reason).toBe('Invalid password');
    });

    it('should include login_at timestamp', async () => {
      const metadata: UserLoginMetadata = {
        user_id: 'test-user',
        success: true,
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'test-user',
        action_type: ActionType.USER_LOGIN,
        entity_type: EntityType.USER,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: {
          success: true,
          login_at: new Date().toISOString(),
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      await auditService.logUserLogin(metadata);

      expect(mockAuditLogModel.create).toHaveBeenCalledWith(
        expect.objectContaining({
          metadata: expect.objectContaining({
            login_at: expect.any(String),
          }),
        })
      );
    });
  });

  describe('logConfigChange', () => {
    it('should log config change with all metadata', async () => {
      const metadata: ConfigChangeMetadata = {
        config_key: 'max_file_size',
        config_section: 'upload_settings',
        previous_value: 5242880,
        new_value: 10485760,
        reason: 'Increased for large certificates',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'admin-123',
        action_type: ActionType.CONFIG_CHANGE,
        entity_type: EntityType.CONFIG,
        entity_id: null,
        before_value: { max_file_size: 5242880 },
        after_value: { max_file_size: 10485760 },
        metadata: {
          config_key: 'max_file_size',
          config_section: 'upload_settings',
          reason: 'Increased for large certificates',
          changed_at: expect.any(String),
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      const result = await auditService.logConfigChange(metadata, 'admin-123');

      expect(result).toBeDefined();
      expect(mockAuditLogModel.create).toHaveBeenCalledWith({
        user_id: 'admin-123',
        action_type: ActionType.CONFIG_CHANGE,
        entity_type: EntityType.CONFIG,
        entity_id: null,
        before_value: { max_file_size: 5242880 },
        after_value: { max_file_size: 10485760 },
        metadata: {
          config_key: 'max_file_size',
          config_section: 'upload_settings',
          reason: 'Increased for large certificates',
          changed_at: expect.any(String),
        },
      });
    });

    it('should log config change without previous value (new config)', async () => {
      const metadata: ConfigChangeMetadata = {
        config_key: 'new_feature_flag',
        new_value: true,
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'admin',
        action_type: ActionType.CONFIG_CHANGE,
        entity_type: EntityType.CONFIG,
        entity_id: null,
        before_value: null,
        after_value: { new_feature_flag: true },
        metadata: {
          config_key: 'new_feature_flag',
          changed_at: new Date().toISOString(),
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      const result = await auditService.logConfigChange(metadata, 'admin');

      expect(result.before_value).toBeNull();
      expect(mockAuditLogModel.create).toHaveBeenCalledWith(
        expect.objectContaining({
          before_value: null,
        })
      );
    });

    it('should log boolean config change', async () => {
      const metadata: ConfigChangeMetadata = {
        config_key: 'feature_enabled',
        previous_value: false,
        new_value: true,
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: 'user-789',
        action_type: ActionType.CONFIG_CHANGE,
        entity_type: EntityType.CONFIG,
        entity_id: null,
        before_value: { feature_enabled: false },
        after_value: { feature_enabled: true },
        metadata: {
          config_key: 'feature_enabled',
          changed_at: new Date().toISOString(),
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      await auditService.logConfigChange(metadata, 'user-789');

      expect(mockAuditLogModel.create).toHaveBeenCalledWith(
        expect.objectContaining({
          before_value: { feature_enabled: false },
          after_value: { feature_enabled: true },
        })
      );
    });

    it('should include changed_at timestamp', async () => {
      const metadata: ConfigChangeMetadata = {
        config_key: 'test_config',
        new_value: 'test_value',
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: null,
        action_type: ActionType.CONFIG_CHANGE,
        entity_type: EntityType.CONFIG,
        entity_id: null,
        before_value: null,
        after_value: { test_config: 'test_value' },
        metadata: {
          config_key: 'test_config',
          changed_at: new Date().toISOString(),
        },
        created_at: new Date(),
      };

      mockAuditLogModel.create = jest.fn().mockResolvedValue(mockResult);

      await auditService.logConfigChange(metadata);

      expect(mockAuditLogModel.create).toHaveBeenCalledWith(
        expect.objectContaining({
          metadata: expect.objectContaining({
            changed_at: expect.any(String),
          }),
        })
      );
    });
  });

  describe('getModel', () => {
    it('should return the underlying AuditLogModel instance', () => {
      const model = auditService.getModel();

      expect(model).toBe(mockAuditLogModel);
    });

    it('should allow access to model methods', () => {
      const model = auditService.getModel();

      expect(model.create).toBeDefined();
      expect(model.findById).toBeDefined();
      expect(model.findByEntity).toBeDefined();
      expect(model.findByUser).toBeDefined();
      expect(model.findAll).toBeDefined();
      expect(model.count).toBeDefined();
    });
  });
});
