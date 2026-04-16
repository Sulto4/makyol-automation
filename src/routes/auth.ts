import { Router } from 'express';
import { Pool } from 'pg';
import { AuthService } from '../services/authService';
import { AuthController } from '../controllers/authController';
import { createAuthMiddleware } from '../middleware/authMiddleware';

export function createAuthRoutes(pool: Pool): Router {
  const router = Router();
  const authService = new AuthService(pool);
  const controller = new AuthController(authService);
  const requireAuth = createAuthMiddleware(authService);

  router.post('/register', controller.register);
  router.post('/login', controller.login);
  router.get('/me', requireAuth, controller.me);

  return router;
}
