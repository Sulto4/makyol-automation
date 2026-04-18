import { Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { AuthService, AuthError } from '../services/authService';
import { registerInputSchema, loginInputSchema } from '../models/User';
import { appConfig } from '../config/app';
import { logger } from '../utils/logger';

const adminCreateUserSchema = registerInputSchema.extend({
  isAdmin: z.boolean().optional(),
});

const resetPasswordSchema = z.object({
  password: z.string().min(8, { message: 'Parola trebuie să aibă minim 8 caractere' }).max(128),
});

const setActiveSchema = z.object({
  is_active: z.boolean(),
});

export class AuthController {
  constructor(private authService: AuthService) {}

  register = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      if (!appConfig.auth.registerEnabled) {
        res.status(403).json({
          error: {
            name: 'AuthError',
            message: 'Înregistrarea publică este dezactivată. Cere adminului să îți creeze un cont.',
            code: 'REGISTER_DISABLED',
          },
        });
        return;
      }

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

  adminListUsers = async (_req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const users = await this.authService.listUsers();
      res.status(200).json({ users });
    } catch (err) {
      next(err);
    }
  };

  adminCreateUser = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const parsed = adminCreateUserSchema.safeParse(req.body);
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
      const user = await this.authService.createUserAsAdmin(parsed.data);
      logger.info(`User created by admin ${req.user?.email}: ${user.email} (admin=${user.is_admin})`);
      res.status(201).json({ user });
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

  adminSetUserActive = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const parsed = setActiveSchema.safeParse(req.body);
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
      if (req.params.id === req.user?.id && parsed.data.is_active === false) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: 'Nu îți poți dezactiva propriul cont',
            code: 'CANNOT_DEACTIVATE_SELF',
          },
        });
        return;
      }
      const user = await this.authService.setUserActive(req.params.id, parsed.data.is_active);
      if (!user) {
        res.status(404).json({
          error: { name: 'NotFoundError', message: 'Utilizator inexistent', code: 'USER_NOT_FOUND' },
        });
        return;
      }
      logger.info(`User ${user.email} active=${user.is_active} by admin ${req.user?.email}`);
      res.status(200).json({ user });
    } catch (err) {
      next(err);
    }
  };

  adminResetPassword = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const parsed = resetPasswordSchema.safeParse(req.body);
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
      const user = await this.authService.resetUserPassword(req.params.id, parsed.data.password);
      if (!user) {
        res.status(404).json({
          error: { name: 'NotFoundError', message: 'Utilizator inexistent', code: 'USER_NOT_FOUND' },
        });
        return;
      }
      logger.info(`Password reset for ${user.email} by admin ${req.user?.email}`);
      res.status(200).json({ user });
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
