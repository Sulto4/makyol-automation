import { Pool } from 'pg';
import { SettingModel, Setting, CreateSettingInput, UpdateSettingInput, SettingKey, SettingValue } from '../models/settings';
import { AuditService, ConfigChangeMetadata } from './auditService';
import { logger } from '../utils/logger';

/**
 * Default values for settings
 */
export const DEFAULT_SETTINGS: Record<string, SettingValue> = {
  [SettingKey.AI_MODEL]: 'google/gemini-2.5-flash',
  [SettingKey.AI_TEMPERATURE]: 0.0,
  [SettingKey.TESSERACT_PATH]: 'D:\\Tesseract-OCR\\tesseract.exe',
  [SettingKey.VISION_MAX_PAGES]: 3,
  [SettingKey.BATCH_CONCURRENCY]: 3,
};

/**
 * Settings validation rules
 */
interface ValidationRule {
  required?: boolean;
  type?: 'string' | 'number' | 'boolean';
  min?: number;
  max?: number;
  options?: string[];
}

const VALIDATION_RULES: Record<string, ValidationRule> = {
  [SettingKey.OPENROUTER_API_KEY]: {
    required: true,
    type: 'string',
  },
  [SettingKey.AI_MODEL]: {
    required: true,
    type: 'string',
    // Restricted to vision-capable models only — the pipeline uses the
    // same model for classification, text extraction AND vision fallback,
    // so a text-only model would fail on vision requests. Ordering
    // roughly matches quality-per-dollar on the 20-hard-doc benchmark.
    options: [
      'google/gemini-2.0-flash-001',
      'google/gemini-2.5-flash',
      'google/gemini-3-flash-preview',
      'google/gemini-2.5-pro',
      'anthropic/claude-haiku-4.5',
      'anthropic/claude-sonnet-4.5',
      'openai/gpt-5.4-mini',
      'openai/gpt-4o',
      'qwen/qwen3-vl-235b-a22b-instruct',
    ],
  },
  [SettingKey.AI_TEMPERATURE]: {
    required: true,
    type: 'number',
    min: 0,
    max: 1,
  },
  [SettingKey.TESSERACT_PATH]: {
    required: false,
    type: 'string',
  },
  [SettingKey.VISION_MAX_PAGES]: {
    required: true,
    type: 'number',
    min: 1,
    max: 10,
  },
  [SettingKey.BATCH_CONCURRENCY]: {
    required: true,
    type: 'number',
    // 1 = serial (old behavior), up to 10 is safe per benchmark; going
    // higher risks saturating OpenRouter bursts and container memory.
    min: 1,
    max: 10,
  },
};

/**
 * Settings Service
 *
 * Provides business logic for settings management, including validation,
 * default values, and audit logging of configuration changes.
 */
export class SettingsService {
  private settingModel: SettingModel;
  private auditService: AuditService;

  constructor(pool: Pool) {
    this.settingModel = new SettingModel(pool);
    this.auditService = new AuditService(pool);
  }

  /**
   * Get all settings with default values for missing settings
   *
   * @returns Array of all settings
   *
   * @example
   * const settings = await settingsService.getAllSettings();
   * // Returns all settings from DB, plus defaults for any missing settings
   */
  async getAllSettings(): Promise<Setting[]> {
    try {
      const dbSettings = await this.settingModel.findAll();
      const settingsMap = new Map(dbSettings.map(s => [s.key, s]));

      // Add default values for missing settings
      const allSettings: Setting[] = [...dbSettings];

      for (const [key, defaultValue] of Object.entries(DEFAULT_SETTINGS)) {
        if (!settingsMap.has(key)) {
          allSettings.push({
            key,
            value: defaultValue,
            created_at: new Date(),
            updated_at: new Date(),
          });
        }
      }

      return allSettings;
    } catch (error: any) {
      logger.error('Failed to get all settings:', error);
      throw new Error(`Failed to retrieve settings: ${error.message}`);
    }
  }

  /**
   * Get a single setting by key
   *
   * @param key - Setting key
   * @returns Setting or null if not found
   *
   * @example
   * const apiKey = await settingsService.getSetting('openrouter_api_key');
   */
  async getSetting(key: string): Promise<Setting | null> {
    try {
      const setting = await this.settingModel.findByKey(key);

      // Return default value if setting not found and default exists
      if (!setting && DEFAULT_SETTINGS[key] !== undefined) {
        return {
          key,
          value: DEFAULT_SETTINGS[key],
          created_at: new Date(),
          updated_at: new Date(),
        };
      }

      return setting;
    } catch (error: any) {
      logger.error(`Failed to get setting ${key}:`, error);
      throw new Error(`Failed to retrieve setting: ${error.message}`);
    }
  }

  /**
   * Get a setting value by key with optional default
   *
   * @param key - Setting key
   * @param defaultValue - Optional default value
   * @returns Setting value or default
   *
   * @example
   * const temperature = await settingsService.getSettingValue('ai_temperature', 0.0);
   */
  async getSettingValue<T = SettingValue>(key: string, defaultValue?: T): Promise<T | null> {
    try {
      const setting = await this.getSetting(key);
      if (setting) {
        return setting.value as T;
      }
      return defaultValue !== undefined ? defaultValue : null;
    } catch (error: any) {
      logger.error(`Failed to get setting value ${key}:`, error);
      throw new Error(`Failed to retrieve setting value: ${error.message}`);
    }
  }

  /**
   * Validate a setting value against validation rules
   *
   * @param key - Setting key
   * @param value - Setting value to validate
   * @throws Error if validation fails
   */
  private validateSetting(key: string, value: SettingValue): void {
    const rule = VALIDATION_RULES[key];
    if (!rule) {
      // No validation rules defined for this key
      return;
    }

    // Check required
    if (rule.required && (value === null || value === undefined || value === '')) {
      throw new Error(`Setting '${key}' is required`);
    }

    // Check type
    if (rule.type && value !== null && value !== undefined) {
      const actualType = typeof value;
      if (actualType !== rule.type) {
        throw new Error(`Setting '${key}' must be of type ${rule.type}, got ${actualType}`);
      }
    }

    // Check numeric range
    if (rule.type === 'number' && typeof value === 'number') {
      if (rule.min !== undefined && value < rule.min) {
        throw new Error(`Setting '${key}' must be at least ${rule.min}`);
      }
      if (rule.max !== undefined && value > rule.max) {
        throw new Error(`Setting '${key}' must be at most ${rule.max}`);
      }
    }

    // Check options
    if (rule.options && typeof value === 'string') {
      if (!rule.options.includes(value)) {
        throw new Error(`Setting '${key}' must be one of: ${rule.options.join(', ')}`);
      }
    }
  }

  /**
   * Update or create a setting (upsert)
   *
   * @param key - Setting key
   * @param value - Setting value
   * @param userId - Optional user ID making the change
   * @returns Updated setting
   *
   * @example
   * const setting = await settingsService.upsertSetting(
   *   'openrouter_api_key',
   *   'sk-or-v1-...',
   *   'user-123'
   * );
   */
  async upsertSetting(
    key: string,
    value: SettingValue,
    userId?: string | null
  ): Promise<Setting> {
    try {
      // Validate the setting value
      this.validateSetting(key, value);

      // Get previous value for audit log
      const previousSetting = await this.settingModel.findByKey(key);
      const previousValue = previousSetting?.value;

      // Upsert the setting
      const input: CreateSettingInput = { key, value };
      const setting = await this.settingModel.upsert(input);

      logger.info(`Setting '${key}' updated successfully`);

      // Audit log: Configuration change
      try {
        const metadata: ConfigChangeMetadata = {
          config_key: key,
          config_section: 'settings',
          previous_value: previousValue,
          new_value: value,
        };
        await this.auditService.logConfigChange(metadata, userId);
      } catch (auditError: any) {
        logger.error(`Failed to create audit log for setting update ${key}:`, auditError);
        // Don't fail the operation if audit logging fails
      }

      return setting;
    } catch (error: any) {
      logger.error(`Failed to upsert setting ${key}:`, error);
      throw error;
    }
  }

  /**
   * Update an existing setting
   *
   * @param key - Setting key
   * @param value - New setting value
   * @param userId - Optional user ID making the change
   * @returns Updated setting or null if not found
   *
   * @example
   * const setting = await settingsService.updateSetting(
   *   'ai_temperature',
   *   0.5,
   *   'user-123'
   * );
   */
  async updateSetting(
    key: string,
    value: SettingValue,
    userId?: string | null
  ): Promise<Setting | null> {
    try {
      // Validate the setting value
      this.validateSetting(key, value);

      // Check if setting exists
      const exists = await this.settingModel.exists(key);
      if (!exists) {
        logger.warn(`Setting '${key}' not found for update`);
        return null;
      }

      // Get previous value for audit log
      const previousSetting = await this.settingModel.findByKey(key);
      const previousValue = previousSetting?.value;

      // Update the setting
      const updateData: UpdateSettingInput = { value };
      const setting = await this.settingModel.update(key, updateData);

      if (setting) {
        logger.info(`Setting '${key}' updated successfully`);

        // Audit log: Configuration change
        try {
          const metadata: ConfigChangeMetadata = {
            config_key: key,
            config_section: 'settings',
            previous_value: previousValue,
            new_value: value,
          };
          await this.auditService.logConfigChange(metadata, userId);
        } catch (auditError: any) {
          logger.error(`Failed to create audit log for setting update ${key}:`, auditError);
          // Don't fail the operation if audit logging fails
        }
      }

      return setting;
    } catch (error: any) {
      logger.error(`Failed to update setting ${key}:`, error);
      throw error;
    }
  }

  /**
   * Delete a setting
   *
   * @param key - Setting key
   * @param userId - Optional user ID making the change
   * @returns True if setting was deleted, false if not found
   *
   * @example
   * const deleted = await settingsService.deleteSetting('old_setting', 'user-123');
   */
  async deleteSetting(key: string, userId?: string | null): Promise<boolean> {
    try {
      // Get current value for audit log
      const previousSetting = await this.settingModel.findByKey(key);
      if (!previousSetting) {
        logger.warn(`Setting '${key}' not found for deletion`);
        return false;
      }

      const deleted = await this.settingModel.delete(key);

      if (deleted) {
        logger.info(`Setting '${key}' deleted successfully`);

        // Audit log: Configuration change (deletion)
        try {
          const metadata: ConfigChangeMetadata = {
            config_key: key,
            config_section: 'settings',
            previous_value: previousSetting.value,
            new_value: null,
            reason: 'Setting deleted',
          };
          await this.auditService.logConfigChange(metadata, userId);
        } catch (auditError: any) {
          logger.error(`Failed to create audit log for setting deletion ${key}:`, auditError);
          // Don't fail the operation if audit logging fails
        }
      }

      return deleted;
    } catch (error: any) {
      logger.error(`Failed to delete setting ${key}:`, error);
      throw error;
    }
  }

  /**
   * Initialize default settings in the database
   *
   * Creates default settings for any that don't exist.
   * Useful for first-time setup or after adding new settings.
   *
   * @returns Number of settings initialized
   *
   * @example
   * const count = await settingsService.initializeDefaults();
   * console.log(`Initialized ${count} default settings`);
   */
  async initializeDefaults(): Promise<number> {
    let initialized = 0;

    try {
      for (const [key, value] of Object.entries(DEFAULT_SETTINGS)) {
        const exists = await this.settingModel.exists(key);
        if (!exists) {
          await this.settingModel.upsert({ key, value });
          initialized++;
          logger.info(`Initialized default setting: ${key}`);
        }
      }

      return initialized;
    } catch (error: any) {
      logger.error('Failed to initialize default settings:', error);
      throw new Error(`Failed to initialize defaults: ${error.message}`);
    }
  }

  /**
   * Get the underlying SettingModel for advanced queries
   *
   * @returns SettingModel instance
   */
  getModel(): SettingModel {
    return this.settingModel;
  }
}
