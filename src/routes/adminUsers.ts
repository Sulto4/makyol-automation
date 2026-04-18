import { Router } from 'express';
import { Pool } from 'pg';
import { AuthService } from '../services/authService';
import { AuthController } from '../controllers/authController';
import { createAuthMiddleware, requireAdmin } from '../middleware/authMiddleware';

export function createAdminUsersRoutes(pool: Pool): Router {
  const router = Router();
  const authService = new AuthService(pool);
  const controller = new AuthController(authService);
  const requireAuth = createAuthMiddleware(authService);

  router.use(requireAuth, requireAdmin);

  router.get('/', controller.adminListUsers);
  router.post('/', controller.adminCreateUser);
  router.patch('/:id/active', controller.adminSetUserActive);
  router.patch('/:id/password', controller.adminResetPassword);

  return router;
}
