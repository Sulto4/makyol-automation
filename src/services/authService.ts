import bcrypt from 'bcryptjs';
import jwt, { JwtPayload, SignOptions } from 'jsonwebtoken';
import { Pool } from 'pg';
import { UserModel, User, PublicUser, toPublicUser, RegisterInput, LoginInput } from '../models/User';

const BCRYPT_ROUNDS = 10;

export interface AuthTokenPayload extends JwtPayload {
  sub: string;
  email: string;
  is_admin: boolean;
}

export class AuthError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status: number = 400,
  ) {
    super(message);
    this.name = 'AuthError';
  }
}

function getJwtSecret(): string {
  const secret = process.env.JWT_SECRET;
  if (!secret || secret.length < 16) {
    throw new Error(
      'JWT_SECRET environment variable is missing or too short (min 16 chars). ' +
        'Generate one with: openssl rand -hex 32',
    );
  }
  return secret;
}

function getJwtExpiresIn(): string {
  return process.env.JWT_EXPIRES_IN || '7d';
}

export class AuthService {
  private userModel: UserModel;

  constructor(pool: Pool) {
    this.userModel = new UserModel(pool);
  }

  async hashPassword(password: string): Promise<string> {
    return bcrypt.hash(password, BCRYPT_ROUNDS);
  }

  async verifyPassword(password: string, hash: string): Promise<boolean> {
    return bcrypt.compare(password, hash);
  }

  signJwt(user: User): string {
    const payload: AuthTokenPayload = {
      sub: user.id,
      email: user.email,
      is_admin: user.is_admin,
    };
    const options: SignOptions = {
      expiresIn: getJwtExpiresIn() as SignOptions['expiresIn'],
    };
    return jwt.sign(payload, getJwtSecret(), options);
  }

  verifyJwt(token: string): AuthTokenPayload {
    try {
      const decoded = jwt.verify(token, getJwtSecret()) as AuthTokenPayload;
      if (!decoded.sub || !decoded.email) {
        throw new AuthError('INVALID_TOKEN', 'Token invalid', 401);
      }
      return decoded;
    } catch (err: any) {
      if (err.name === 'TokenExpiredError') {
        throw new AuthError('TOKEN_EXPIRED', 'Sesiune expirată. Te rog autentifică-te din nou.', 401);
      }
      throw new AuthError('INVALID_TOKEN', 'Token invalid', 401);
    }
  }

  async register(input: RegisterInput): Promise<{ user: PublicUser; token: string }> {
    const normalizedEmail = input.email.trim().toLowerCase();

    const existing = await this.userModel.findByEmail(normalizedEmail);
    if (existing) {
      throw new AuthError('EMAIL_IN_USE', 'Există deja un cont cu acest email', 409);
    }

    const isFirstUser = (await this.userModel.countAll()) === 0;
    const hash = await this.hashPassword(input.password);
    const user = await this.userModel.create(normalizedEmail, hash, isFirstUser);

    const token = this.signJwt(user);
    return { user: toPublicUser(user), token };
  }

  async login(input: LoginInput): Promise<{ user: PublicUser; token: string }> {
    const normalizedEmail = input.email.trim().toLowerCase();
    const user = await this.userModel.findByEmail(normalizedEmail);

    if (!user || !user.is_active) {
      throw new AuthError('INVALID_CREDENTIALS', 'Email sau parolă incorecte', 401);
    }

    const ok = await this.verifyPassword(input.password, user.password_hash);
    if (!ok) {
      throw new AuthError('INVALID_CREDENTIALS', 'Email sau parolă incorecte', 401);
    }

    await this.userModel.touchLastLogin(user.id);
    const token = this.signJwt(user);
    return { user: toPublicUser(user), token };
  }

  async findUserById(id: string): Promise<PublicUser | null> {
    const user = await this.userModel.findById(id);
    return user ? toPublicUser(user) : null;
  }

  async findUserByEmail(email: string): Promise<PublicUser | null> {
    const user = await this.userModel.findByEmail(email.trim().toLowerCase());
    return user ? toPublicUser(user) : null;
  }

  async createUserAsAdmin(
    input: RegisterInput & { isAdmin?: boolean },
  ): Promise<PublicUser> {
    const normalizedEmail = input.email.trim().toLowerCase();

    const existing = await this.userModel.findByEmail(normalizedEmail);
    if (existing) {
      throw new AuthError('EMAIL_IN_USE', 'Există deja un cont cu acest email', 409);
    }

    const hash = await this.hashPassword(input.password);
    const user = await this.userModel.create(
      normalizedEmail,
      hash,
      input.isAdmin === true,
    );
    return toPublicUser(user);
  }

  async listUsers(): Promise<PublicUser[]> {
    const users = await this.userModel.listAll();
    return users.map(toPublicUser);
  }

  async setUserActive(id: string, isActive: boolean): Promise<PublicUser | null> {
    const user = await this.userModel.setActive(id, isActive);
    return user ? toPublicUser(user) : null;
  }

  async resetUserPassword(id: string, newPassword: string): Promise<PublicUser | null> {
    if (newPassword.length < 8) {
      throw new AuthError('WEAK_PASSWORD', 'Parola trebuie să aibă minim 8 caractere', 400);
    }
    const hash = await this.hashPassword(newPassword);
    const user = await this.userModel.updatePassword(id, hash);
    return user ? toPublicUser(user) : null;
  }
}
