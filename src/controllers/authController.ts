import { Request, Response, NextFunction } from 'express';
import { AuthService, AuthError } from '../services/authService';
import { registerInputSchema, loginInputSchema } from '../models/User';
import { logger } from '../utils/logger';

export class AuthController {
  constructor(private authService: AuthService) {}

  register = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const parsed = registerInputSchema.safeParse(req.body);
      if (!parsed.success) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: parsed.error.issues[0]?.message || 'Date invalide',
            code: 'VALIDATION_ERROR',
          },
        });
        return;
      }

      const { user, token } = await this.authService.register(parsed.data);
      logger.info(`User registered: ${user.email} (admin=${user.is_admin})`);
      res.status(201).json({ user, token });
    } catch (err) {
      if (err instanceof AuthError) {
        res.status(err.status).json({
          error: { name: 'AuthError', message: err.message, code: err.code },
        });
        return;
      }
      next(err);
    }
  };

  login = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const parsed = loginInputSchema.safeParse(req.body);
      if (!parsed.success) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: parsed.error.issues[0]?.message || 'Date invalide',
            code: 'VALIDATION_ERROR',
          },
        });
        return;
      }

      const { user, token } = await this.authService.login(parsed.data);
      logger.info(`User logged in: ${user.email}`);
      res.status(200).json({ user, token });
    } catch (err) {
      if (err instanceof AuthError) {
        res.status(err.status).json({
          error: { name: 'AuthError', message: err.message, code: err.code },
        });
        return;
      }
      next(err);
    }
  };

  me = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      if (!req.user) {
        res.status(401).json({
          error: { name: 'AuthError', message: 'Neautentificat', code: 'MISSING_TOKEN' },
        });
        return;
      }
      const user = await this.authService.findUserById(req.user.id);
      if (!user) {
        res.status(404).json({
          error: { name: 'NotFoundError', message: 'Utilizator inexistent', code: 'USER_NOT_FOUND' },
        });
        return;
      }
      res.status(200).json({ user });
    } catch (err) {
      next(err);
    }
  };
}
