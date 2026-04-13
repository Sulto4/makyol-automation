import { Pool, QueryResult } from 'pg';
import {
  AuditLogModel,
  AuditLog,
  CreateAuditLogInput,
  ActionType,
  EntityType,
  AuditLogFilters,
} from '../../src/models/AuditLog';

// Mock pg Pool
jest.mock('pg', () => {
  const mPool = {
    query: jest.fn(),
  };
  return { Pool: jest.fn(() => mPool) };
});

describe('AuditLogModel', () => {
  let pool: Pool;
  let auditLogModel: AuditLogModel;
  let mockQuery: jest.Mock;

  beforeEach(() => {
    pool = new Pool();
    mockQuery = pool.query as jest.Mock;
    auditLogModel = new AuditLogModel(pool);
    mockQuery.mockClear();
  });

  describe('create', () => {
    it('should create a new audit log entry with all fields', async () => {
      const input: CreateAuditLogInput = {
        user_id: 'user-123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: 42,
        before_value: { status: 'pending' },
        after_value: { status: 'uploaded' },
        metadata: { filename: 'test.pdf', file_size: 1024 },
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date('2024-01-01T10:00:00Z'),
        user_id: input.user_id!,
        action_type: input.action_type,
        entity_type: input.entity_type,
        entity_id: input.entity_id!,
        before_value: input.before_value!,
        after_value: input.after_value!,
        metadata: input.metadata!,
        created_at: new Date('2024-01-01T10:00:00Z'),
      };

      mockQuery.mockResolvedValueOnce({ rows: [mockResult] });

      const result = await auditLogModel.create(input);

      expect(result).toEqual(mockResult);
      expect(mockQuery).toHaveBeenCalledTimes(1);
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO audit_logs'),
        expect.arrayContaining([
          expect.any(Date),
          input.user_id,
          input.action_type,
          input.entity_type,
          input.entity_id,
          JSON.stringify(input.before_value),
          JSON.stringify(input.after_value),
          JSON.stringify(input.metadata),
        ])
      );
    });

    it('should create audit log with null user_id', async () => {
      const input: CreateAuditLogInput = {
        user_id: null,
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        metadata: { filename: 'test.pdf' },
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: null,
        action_type: input.action_type,
        entity_type: input.entity_type,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: input.metadata!,
        created_at: new Date(),
      };

      mockQuery.mockResolvedValueOnce({ rows: [mockResult] });

      const result = await auditLogModel.create(input);

      expect(result.user_id).toBeNull();
      expect(mockQuery).toHaveBeenCalledWith(
        expect.any(String),
        expect.arrayContaining([expect.any(Date), null])
      );
    });

    it('should create audit log with null entity_id', async () => {
      const input: CreateAuditLogInput = {
        user_id: 'user-123',
        action_type: ActionType.REPORT_GENERATION,
        entity_type: EntityType.REPORT,
        entity_id: null,
        metadata: { report_type: 'compliance_summary' },
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: input.user_id!,
        action_type: input.action_type,
        entity_type: input.entity_type,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: input.metadata!,
        created_at: new Date(),
      };

      mockQuery.mockResolvedValueOnce({ rows: [mockResult] });

      const result = await auditLogModel.create(input);

      expect(result.entity_id).toBeNull();
    });

    it('should use current timestamp when not provided', async () => {
      const input: CreateAuditLogInput = {
        action_type: ActionType.USER_LOGIN,
        entity_type: EntityType.USER,
        metadata: {},
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: null,
        action_type: input.action_type,
        entity_type: input.entity_type,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: {},
        created_at: new Date(),
      };

      mockQuery.mockResolvedValueOnce({ rows: [mockResult] });

      await auditLogModel.create(input);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.any(String),
        expect.arrayContaining([expect.any(Date)])
      );
    });

    it('should use custom timestamp when provided', async () => {
      const customTimestamp = new Date('2024-06-15T12:00:00Z');
      const input: CreateAuditLogInput = {
        action_type: ActionType.CONFIG_CHANGE,
        entity_type: EntityType.CONFIG,
        metadata: {},
        timestamp: customTimestamp,
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: customTimestamp,
        user_id: null,
        action_type: input.action_type,
        entity_type: input.entity_type,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: {},
        created_at: new Date(),
      };

      mockQuery.mockResolvedValueOnce({ rows: [mockResult] });

      const result = await auditLogModel.create(input);

      expect(result.timestamp).toEqual(customTimestamp);
      expect(mockQuery).toHaveBeenCalledWith(
        expect.any(String),
        expect.arrayContaining([customTimestamp])
      );
    });

    it('should stringify JSON fields correctly', async () => {
      const input: CreateAuditLogInput = {
        action_type: ActionType.DOCUMENT_STATUS_CHANGE,
        entity_type: EntityType.DOCUMENT,
        before_value: { status: 'pending', verified: false },
        after_value: { status: 'verified', verified: true },
        metadata: { filename: 'cert.pdf', reason: 'manual review' },
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: null,
        action_type: input.action_type,
        entity_type: input.entity_type,
        entity_id: null,
        before_value: input.before_value!,
        after_value: input.after_value!,
        metadata: input.metadata!,
        created_at: new Date(),
      };

      mockQuery.mockResolvedValueOnce({ rows: [mockResult] });

      await auditLogModel.create(input);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.any(String),
        expect.arrayContaining([
          expect.any(Date),
          null,
          input.action_type,
          input.entity_type,
          null,
          JSON.stringify(input.before_value),
          JSON.stringify(input.after_value),
          JSON.stringify(input.metadata),
        ])
      );
    });

    it('should handle empty metadata', async () => {
      const input: CreateAuditLogInput = {
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
      };

      const mockResult: AuditLog = {
        id: 1,
        timestamp: new Date(),
        user_id: null,
        action_type: input.action_type,
        entity_type: input.entity_type,
        entity_id: null,
        before_value: null,
        after_value: null,
        metadata: {},
        created_at: new Date(),
      };

      mockQuery.mockResolvedValueOnce({ rows: [mockResult] });

      const result = await auditLogModel.create(input);

      expect(result.metadata).toEqual({});
      expect(mockQuery).toHaveBeenCalledWith(
        expect.any(String),
        expect.arrayContaining([JSON.stringify({})])
      );
    });
  });

  describe('findById', () => {
    it('should find an audit log by ID', async () => {
      const mockLog: AuditLog = {
        id: 42,
        timestamp: new Date('2024-01-01T10:00:00Z'),
        user_id: 'user-123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: 100,
        before_value: null,
        after_value: null,
        metadata: { filename: 'test.pdf' },
        created_at: new Date('2024-01-01T10:00:00Z'),
      };

      mockQuery.mockResolvedValueOnce({ rows: [mockLog] });

      const result = await auditLogModel.findById(42);

      expect(result).toEqual(mockLog);
      expect(mockQuery).toHaveBeenCalledWith(
        'SELECT * FROM audit_logs WHERE id = $1',
        [42]
      );
    });

    it('should return null when audit log not found', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const result = await auditLogModel.findById(999);

      expect(result).toBeNull();
      expect(mockQuery).toHaveBeenCalledWith(
        'SELECT * FROM audit_logs WHERE id = $1',
        [999]
      );
    });
  });

  describe('findByEntity', () => {
    it('should find audit logs by entity type and ID', async () => {
      const mockLogs: AuditLog[] = [
        {
          id: 1,
          timestamp: new Date('2024-01-02T10:00:00Z'),
          user_id: 'user-123',
          action_type: ActionType.DOCUMENT_STATUS_CHANGE,
          entity_type: EntityType.DOCUMENT,
          entity_id: 42,
          before_value: { status: 'pending' },
          after_value: { status: 'verified' },
          metadata: {},
          created_at: new Date('2024-01-02T10:00:00Z'),
        },
        {
          id: 2,
          timestamp: new Date('2024-01-01T10:00:00Z'),
          user_id: 'user-456',
          action_type: ActionType.DOCUMENT_UPLOAD,
          entity_type: EntityType.DOCUMENT,
          entity_id: 42,
          before_value: null,
          after_value: null,
          metadata: { filename: 'test.pdf' },
          created_at: new Date('2024-01-01T10:00:00Z'),
        },
      ];

      mockQuery.mockResolvedValueOnce({ rows: mockLogs });

      const result = await auditLogModel.findByEntity(EntityType.DOCUMENT, 42);

      expect(result).toEqual(mockLogs);
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('WHERE entity_type = $1 AND entity_id = $2'),
        [EntityType.DOCUMENT, 42]
      );
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('ORDER BY timestamp DESC'),
        expect.any(Array)
      );
    });

    it('should apply limit when provided', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      await auditLogModel.findByEntity(EntityType.DOCUMENT, 42, 10);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('LIMIT $3'),
        [EntityType.DOCUMENT, 42, 10]
      );
    });

    it('should apply offset when provided', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      await auditLogModel.findByEntity(EntityType.DOCUMENT, 42, 10, 20);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('LIMIT $3'),
        [EntityType.DOCUMENT, 42, 10, 20]
      );
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('OFFSET $4'),
        expect.any(Array)
      );
    });

    it('should return empty array when no logs found', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const result = await auditLogModel.findByEntity(EntityType.DOCUMENT, 999);

      expect(result).toEqual([]);
    });
  });

  describe('findByUser', () => {
    it('should find audit logs by user ID', async () => {
      const mockLogs: AuditLog[] = [
        {
          id: 1,
          timestamp: new Date('2024-01-02T10:00:00Z'),
          user_id: 'user-123',
          action_type: ActionType.DOCUMENT_UPLOAD,
          entity_type: EntityType.DOCUMENT,
          entity_id: 42,
          before_value: null,
          after_value: null,
          metadata: {},
          created_at: new Date('2024-01-02T10:00:00Z'),
        },
      ];

      mockQuery.mockResolvedValueOnce({ rows: mockLogs });

      const result = await auditLogModel.findByUser('user-123');

      expect(result).toEqual(mockLogs);
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('WHERE user_id = $1'),
        ['user-123']
      );
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('ORDER BY timestamp DESC'),
        expect.any(Array)
      );
    });

    it('should apply limit when provided', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      await auditLogModel.findByUser('user-123', 5);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('LIMIT $2'),
        ['user-123', 5]
      );
    });

    it('should apply offset when provided', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      await auditLogModel.findByUser('user-123', 5, 10);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('LIMIT $2'),
        ['user-123', 5, 10]
      );
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('OFFSET $3'),
        expect.any(Array)
      );
    });

    it('should return empty array when no logs found', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const result = await auditLogModel.findByUser('nonexistent-user');

      expect(result).toEqual([]);
    });
  });

  describe('findAll', () => {
    it('should find all audit logs without filters', async () => {
      const mockLogs: AuditLog[] = [
        {
          id: 1,
          timestamp: new Date('2024-01-02T10:00:00Z'),
          user_id: 'user-123',
          action_type: ActionType.DOCUMENT_UPLOAD,
          entity_type: EntityType.DOCUMENT,
          entity_id: 42,
          before_value: null,
          after_value: null,
          metadata: {},
          created_at: new Date('2024-01-02T10:00:00Z'),
        },
      ];

      mockQuery.mockResolvedValueOnce({ rows: mockLogs });

      const result = await auditLogModel.findAll();

      expect(result).toEqual(mockLogs);
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('SELECT * FROM audit_logs'),
        []
      );
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('ORDER BY timestamp DESC'),
        expect.any(Array)
      );
    });

    it('should filter by user_id', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const filters: AuditLogFilters = { user_id: 'user-123' };
      await auditLogModel.findAll(filters);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('WHERE user_id = $1'),
        ['user-123']
      );
    });

    it('should filter by action_type', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const filters: AuditLogFilters = { action_type: ActionType.DOCUMENT_UPLOAD };
      await auditLogModel.findAll(filters);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('WHERE action_type = $1'),
        [ActionType.DOCUMENT_UPLOAD]
      );
    });

    it('should filter by entity_type', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const filters: AuditLogFilters = { entity_type: EntityType.DOCUMENT };
      await auditLogModel.findAll(filters);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('WHERE entity_type = $1'),
        [EntityType.DOCUMENT]
      );
    });

    it('should filter by entity_id', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const filters: AuditLogFilters = { entity_id: 42 };
      await auditLogModel.findAll(filters);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('WHERE entity_id = $1'),
        [42]
      );
    });

    it('should filter by start_date', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const startDate = new Date('2024-01-01T00:00:00Z');
      const filters: AuditLogFilters = { start_date: startDate };
      await auditLogModel.findAll(filters);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('WHERE timestamp >= $1'),
        [startDate]
      );
    });

    it('should filter by end_date', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const endDate = new Date('2024-12-31T23:59:59Z');
      const filters: AuditLogFilters = { end_date: endDate };
      await auditLogModel.findAll(filters);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('WHERE timestamp <= $1'),
        [endDate]
      );
    });

    it('should apply multiple filters with AND', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const filters: AuditLogFilters = {
        user_id: 'user-123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
      };
      await auditLogModel.findAll(filters);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('WHERE'),
        ['user-123', ActionType.DOCUMENT_UPLOAD, EntityType.DOCUMENT]
      );
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('AND'),
        expect.any(Array)
      );
    });

    it('should apply date range filter', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const startDate = new Date('2024-01-01T00:00:00Z');
      const endDate = new Date('2024-12-31T23:59:59Z');
      const filters: AuditLogFilters = {
        start_date: startDate,
        end_date: endDate,
      };
      await auditLogModel.findAll(filters);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('timestamp >= $1'),
        [startDate, endDate]
      );
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('timestamp <= $2'),
        expect.any(Array)
      );
    });

    it('should apply limit', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const filters: AuditLogFilters = { limit: 10 };
      await auditLogModel.findAll(filters);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('LIMIT $1'),
        [10]
      );
    });

    it('should apply offset', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const filters: AuditLogFilters = { limit: 10, offset: 20 };
      await auditLogModel.findAll(filters);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('LIMIT $1'),
        [10, 20]
      );
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('OFFSET $2'),
        expect.any(Array)
      );
    });

    it('should handle all filters combined', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });

      const filters: AuditLogFilters = {
        user_id: 'user-123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: 42,
        start_date: new Date('2024-01-01'),
        end_date: new Date('2024-12-31'),
        limit: 50,
        offset: 100,
      };
      await auditLogModel.findAll(filters);

      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('WHERE'),
        expect.arrayContaining([
          'user-123',
          ActionType.DOCUMENT_UPLOAD,
          EntityType.DOCUMENT,
          42,
          filters.start_date,
          filters.end_date,
          50,
          100,
        ])
      );
    });
  });

  describe('count', () => {
    it('should count all audit logs without filters', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [{ count: '42' }] });

      const result = await auditLogModel.count();

      expect(result).toBe(42);
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('SELECT COUNT(*) as count FROM audit_logs'),
        []
      );
    });

    it('should filter by user_id', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [{ count: '10' }] });

      const result = await auditLogModel.count({ user_id: 'user-123' });

      expect(result).toBe(10);
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('WHERE user_id = $1'),
        ['user-123']
      );
    });

    it('should filter by action_type', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [{ count: '5' }] });

      const result = await auditLogModel.count({
        action_type: ActionType.DOCUMENT_UPLOAD,
      });

      expect(result).toBe(5);
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('WHERE action_type = $1'),
        [ActionType.DOCUMENT_UPLOAD]
      );
    });

    it('should filter by entity_type', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [{ count: '15' }] });

      const result = await auditLogModel.count({ entity_type: EntityType.DOCUMENT });

      expect(result).toBe(15);
    });

    it('should filter by entity_id', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [{ count: '3' }] });

      const result = await auditLogModel.count({ entity_id: 42 });

      expect(result).toBe(3);
    });

    it('should filter by date range', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [{ count: '25' }] });

      const result = await auditLogModel.count({
        start_date: new Date('2024-01-01'),
        end_date: new Date('2024-12-31'),
      });

      expect(result).toBe(25);
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('timestamp >= $1'),
        expect.arrayContaining([expect.any(Date), expect.any(Date)])
      );
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('timestamp <= $2'),
        expect.any(Array)
      );
    });

    it('should apply multiple filters', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [{ count: '7' }] });

      const result = await auditLogModel.count({
        user_id: 'user-123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
      });

      expect(result).toBe(7);
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('WHERE'),
        ['user-123', ActionType.DOCUMENT_UPLOAD, EntityType.DOCUMENT]
      );
    });

    it('should return 0 when no matching logs', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [{ count: '0' }] });

      const result = await auditLogModel.count({ user_id: 'nonexistent' });

      expect(result).toBe(0);
    });

    it('should parse count as integer', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [{ count: '1234' }] });

      const result = await auditLogModel.count();

      expect(result).toBe(1234);
      expect(typeof result).toBe('number');
    });
  });
});
