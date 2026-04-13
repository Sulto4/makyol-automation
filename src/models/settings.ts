import { Pool, QueryResult } from 'pg';

/**
 * Setting value type - supports any JSON-serializable value
 */
export type SettingValue = string | number | boolean | object | null;

/**
 * Setting interface matching the settings table schema
 */
export interface Setting {
  key: string;
  value: SettingValue;
  created_at: Date;
  updated_at: Date;
}

/**
 * Input type for creating a new setting
 */
export interface CreateSettingInput {
  key: string;
  value: SettingValue;
}

/**
 * Input type for updating a setting
 */
export interface UpdateSettingInput {
  value: SettingValue;
}

/**
 * Predefined setting keys for type safety
 */
export enum SettingKey {
  OPENROUTER_API_KEY = 'openrouter_api_key',
  AI_MODEL = 'ai_model',
  AI_TEMPERATURE = 'ai_temperature',
  TESSERACT_PATH = 'tesseract_path',
  VISION_MAX_PAGES = 'vision_max_pages',
}

/**
 * Setting model class for database operations
 */
export class SettingModel {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  /**
   * Create or update a setting (upsert)
   */
  async upsert(input: CreateSettingInput): Promise<Setting> {
    const query = `
      INSERT INTO settings (key, value)
      VALUES ($1, $2)
      ON CONFLICT (key)
      DO UPDATE SET value = EXCLUDED.value
      RETURNING *
    `;

    const values = [input.key, JSON.stringify(input.value)];

    const result: QueryResult<Setting> = await this.pool.query(query, values);
    return result.rows[0];
  }

  /**
   * Find a setting by key
   */
  async findByKey(key: string): Promise<Setting | null> {
    const query = 'SELECT * FROM settings WHERE key = $1';
    const result: QueryResult<Setting> = await this.pool.query(query, [key]);
    return result.rows[0] || null;
  }

  /**
   * Find all settings
   */
  async findAll(): Promise<Setting[]> {
    const query = 'SELECT * FROM settings ORDER BY key ASC';
    const result: QueryResult<Setting> = await this.pool.query(query);
    return result.rows;
  }

  /**
   * Update a setting by key
   */
  async update(key: string, updateData: UpdateSettingInput): Promise<Setting | null> {
    const query = `
      UPDATE settings
      SET value = $1
      WHERE key = $2
      RETURNING *
    `;

    const values = [JSON.stringify(updateData.value), key];

    const result: QueryResult<Setting> = await this.pool.query(query, values);
    return result.rows[0] || null;
  }

  /**
   * Delete a setting by key
   */
  async delete(key: string): Promise<boolean> {
    const query = 'DELETE FROM settings WHERE key = $1 RETURNING key';
    const result: QueryResult = await this.pool.query(query, [key]);
    return result.rowCount !== null && result.rowCount > 0;
  }

  /**
   * Check if a setting exists
   */
  async exists(key: string): Promise<boolean> {
    const query = 'SELECT 1 FROM settings WHERE key = $1';
    const result: QueryResult = await this.pool.query(query, [key]);
    return result.rowCount !== null && result.rowCount > 0;
  }

  /**
   * Get setting value by key, with optional default
   */
  async getValue<T = SettingValue>(key: string, defaultValue?: T): Promise<T | null> {
    const setting = await this.findByKey(key);
    if (!setting) {
      return defaultValue !== undefined ? defaultValue : null;
    }
    return setting.value as T;
  }

  /**
   * Count total settings
   */
  async count(): Promise<number> {
    const query = 'SELECT COUNT(*) as count FROM settings';
    const result: QueryResult<{ count: string }> = await this.pool.query(query);
    return parseInt(result.rows[0].count, 10);
  }
}

export default SettingModel;
