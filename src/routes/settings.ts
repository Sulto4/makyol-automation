import { Router } from 'express';
import { Pool } from 'pg';
import { SettingsController } from '../controllers/settingsController';

/**
 * Create and configure settings routes
 *
 * @param pool - PostgreSQL connection pool
 * @returns Configured Express router
 */
export function createSettingsRoutes(pool: Pool): Router {
  const router = Router();
  const controller = new SettingsController(pool);

  /**
   * POST /api/settings/initialize
   * Initialize default settings
   *
   * @returns 200 - Default settings initialized successfully
   * @returns 500 - Server error
   */
  router.post('/initialize', (req, res, next) => controller.initializeDefaults(req, res, next));

  /**
   * GET /api/settings
   * Get all settings with default values
   *
   * @returns 200 - List of all settings with their values
   * @returns 500 - Server error
   */
  router.get('/', (req, res, next) => controller.getAllSettings(req, res, next));

  /**
   * GET /api/settings/:key
   * Get a single setting by key
   *
   * @param key - Setting key
   * @returns 200 - Setting found
   * @returns 400 - Missing setting key
   * @returns 404 - Setting not found
   * @returns 500 - Server error
   */
  router.get('/:key', (req, res, next) => controller.getSetting(req, res, next));

  /**
   * PUT /api/settings/:key
   * Update or create a setting (upsert)
   *
   * @param key - Setting key
   * @body value - Setting value (any type)
   * @returns 200 - Setting updated successfully
   * @returns 400 - Invalid request (missing key or value, validation failed)
   * @returns 500 - Server error
   */
  router.put('/:key', (req, res, next) => controller.updateSetting(req, res, next));

  /**
   * DELETE /api/settings/:key
   * Delete a setting
   *
   * @param key - Setting key
   * @returns 200 - Setting deleted successfully
   * @returns 400 - Missing setting key
   * @returns 404 - Setting not found
   * @returns 500 - Server error
   */
  router.delete('/:key', (req, res, next) => controller.deleteSetting(req, res, next));

  return router;
}

export default createSettingsRoutes;
