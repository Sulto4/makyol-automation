import { Request, Response, NextFunction } from 'express';
import { AuthService, AuthError } from '../services/authService';

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Express {
    interface Request {
      user?: {
        id: string;
        email: string;
        is_admin: boolean;
      };
    }
  }
}

export interface AuthenticatedRequest extends Request {
  user: {
    id: string;
    email: string;
    is_admin: boolean;
  };
}

function extractBearerToken(req: Request): string | null {
  const header = req.headers.authorization;
  if (!header || typeof header !== 'string') return null;
  const [scheme, token] = header.split(' ');
  if (scheme?.toLowerCase() !== 'bearer' || !token) return null;
  return token;
}

/**
 * Require a valid Bearer JWT. On success populates req.user.
 * On failure responds 401 with a structured error body.
 */
export function createAuthMiddleware(authService: AuthService) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const token = extractBearerToken(req);
    if (!token) {
      res.status(401).json({
        error: { name: 'AuthError', message: 'Autentificare necesară', code: 'MISSING_TOKEN' },
      });
      return;
    }

    try {
      const payload = authService.verifyJwt(token);
      req.user = {
        id: payload.sub,
        email: payload.email,
        is_admin: payload.is_admin,
      };
      next();
    } catch (err) {
      if (err instanceof AuthError) {
        res.status(err.status).json({
          error: { name: 'AuthError', message: err.message, code: err.code },
        });
        return;
      }
      res.status(401).json({
        error: { name: 'AuthError', message: 'Token invalid', code: 'INVALID_TOKEN' },
      });
    }
  };
}
