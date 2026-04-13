import { Request, Response, NextFunction } from 'express';
import { Pool } from 'pg';
import { SettingsService } from '../services/settingsService';
import { logger } from '../utils/logger';

/**
 * Settings controller class
 * Handles HTTP requests for settings management
 */
export class SettingsController {
  private settingsService: SettingsService;

  constructor(pool: Pool) {
    this.settingsService = new SettingsService(pool);
  }

  /**
   * Get all settings with default values
   *
   * GET /api/settings
   */
  async getAllSettings(_req: Request, res: Response, _next: NextFunction): Promise<void> {
    try {
      logger.info('Fetching all settings');
      const settings = await this.settingsService.getAllSettings();

      res.status(200).json({
        success: true,
        data: settings,
        count: settings.length,
      });
    } catch (error: any) {
      logger.error('Failed to get all settings:', error);
      res.status(500).json({
        error: {
          name: 'InternalServerError',
          message: 'Failed to retrieve settings',
          code: 'SETTINGS_FETCH_FAILED',
          details: error.message,
        },
      });
    }
  }

  /**
   * Get a single setting by key
   *
   * GET /api/settings/:key
   */
  async getSetting(req: Request, res: Response, _next: NextFunction): Promise<void> {
    try {
      const { key } = req.params;

      if (!key) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: 'Setting key is required',
            code: 'MISSING_SETTING_KEY',
          },
        });
        return;
      }

      logger.info(`Fetching setting: ${key}`);
      const setting = await this.settingsService.getSetting(key);

      if (!setting) {
        res.status(404).json({
          error: {
            name: 'NotFoundError',
            message: `Setting '${key}' not found`,
            code: 'SETTING_NOT_FOUND',
          },
        });
        return;
      }

      res.status(200).json({
        success: true,
        data: setting,
      });
    } catch (error: any) {
      logger.error(`Failed to get setting ${req.params.key}:`, error);
      res.status(500).json({
        error: {
          name: 'InternalServerError',
          message: 'Failed to retrieve setting',
          code: 'SETTING_FETCH_FAILED',
          details: error.message,
        },
      });
    }
  }

  /**
   * Update or create a setting (upsert)
   *
   * PUT /api/settings/:key
   *
   * Body: { value: any }
   */
  async updateSetting(req: Request, res: Response, _next: NextFunction): Promise<void> {
    try {
      const { key } = req.params;
      const { value } = req.body;

      // Validate key
      if (!key) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: 'Setting key is required',
            code: 'MISSING_SETTING_KEY',
          },
        });
        return;
      }

      // Validate value
      if (value === undefined) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: 'Setting value is required',
            code: 'MISSING_SETTING_VALUE',
          },
        });
        return;
      }

      logger.info(`Updating setting: ${key}`);

      // Use upsert to create or update
      const setting = await this.settingsService.upsertSetting(key, value, null);

      res.status(200).json({
        success: true,
        data: setting,
        message: 'Setting updated successfully',
      });
    } catch (error: any) {
      logger.error(`Failed to update setting ${req.params.key}:`, error);

      // Check if it's a validation error
      if (error.message.includes('must be') || error.message.includes('required')) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: error.message,
            code: 'SETTING_VALIDATION_FAILED',
          },
        });
        return;
      }

      res.status(500).json({
        error: {
          name: 'InternalServerError',
          message: 'Failed to update setting',
          code: 'SETTING_UPDATE_FAILED',
          details: error.message,
        },
      });
    }
  }

  /**
   * Delete a setting
   *
   * DELETE /api/settings/:key
   */
  async deleteSetting(req: Request, res: Response, _next: NextFunction): Promise<void> {
    try {
      const { key } = req.params;

      if (!key) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: 'Setting key is required',
            code: 'MISSING_SETTING_KEY',
          },
        });
        return;
      }

      logger.info(`Deleting setting: ${key}`);
      const deleted = await this.settingsService.deleteSetting(key, null);

      if (!deleted) {
        res.status(404).json({
          error: {
            name: 'NotFoundError',
            message: `Setting '${key}' not found`,
            code: 'SETTING_NOT_FOUND',
          },
        });
        return;
      }

      res.status(200).json({
        success: true,
        message: `Setting '${key}' deleted successfully`,
      });
    } catch (error: any) {
      logger.error(`Failed to delete setting ${req.params.key}:`, error);
      res.status(500).json({
        error: {
          name: 'InternalServerError',
          message: 'Failed to delete setting',
          code: 'SETTING_DELETE_FAILED',
          details: error.message,
        },
      });
    }
  }

  /**
   * Initialize default settings
   *
   * POST /api/settings/initialize
   */
  async initializeDefaults(_req: Request, res: Response, _next: NextFunction): Promise<void> {
    try {
      logger.info('Initializing default settings');
      const count = await this.settingsService.initializeDefaults();

      res.status(200).json({
        success: true,
        message: `Initialized ${count} default settings`,
        count,
      });
    } catch (error: any) {
      logger.error('Failed to initialize default settings:', error);
      res.status(500).json({
        error: {
          name: 'InternalServerError',
          message: 'Failed to initialize default settings',
          code: 'SETTINGS_INIT_FAILED',
          details: error.message,
        },
      });
    }
  }
}
