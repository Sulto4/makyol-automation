import { Pool, QueryResult } from 'pg';
import { z } from 'zod';

export interface User {
  id: string;
  email: string;
  password_hash: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: Date;
  last_login_at: Date | null;
  updated_at: Date;
}

export type PublicUser = Omit<User, 'password_hash'>;

export const registerInputSchema = z.object({
  email: z.string().email({ message: 'Email invalid' }).max(255),
  password: z
    .string()
    .min(8, { message: 'Parola trebuie să aibă minim 8 caractere' })
    .max(128, { message: 'Parola este prea lungă' }),
});

export const loginInputSchema = z.object({
  email: z.string().email({ message: 'Email invalid' }),
  password: z.string().min(1, { message: 'Parola este obligatorie' }),
});

export type RegisterInput = z.infer<typeof registerInputSchema>;
export type LoginInput = z.infer<typeof loginInputSchema>;

export function toPublicUser(user: User): PublicUser {
  const { password_hash: _pw, ...rest } = user;
  void _pw;
  return rest;
}

export class UserModel {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  async findByEmail(email: string): Promise<User | null> {
    const res: QueryResult<User> = await this.pool.query(
      'SELECT * FROM users WHERE email = $1',
      [email],
    );
    return res.rows[0] || null;
  }

  async findById(id: string): Promise<User | null> {
    const res: QueryResult<User> = await this.pool.query(
      'SELECT * FROM users WHERE id = $1',
      [id],
    );
    return res.rows[0] || null;
  }

  async countAll(): Promise<number> {
    const res: QueryResult<{ count: string }> = await this.pool.query(
      'SELECT COUNT(*)::text AS count FROM users',
    );
    return parseInt(res.rows[0].count, 10);
  }

  async create(email: string, passwordHash: string, isAdmin: boolean): Promise<User> {
    const res: QueryResult<User> = await this.pool.query(
      `INSERT INTO users (email, password_hash, is_admin)
       VALUES ($1, $2, $3)
       RETURNING *`,
      [email, passwordHash, isAdmin],
    );
    return res.rows[0];
  }

  async touchLastLogin(id: string): Promise<void> {
    await this.pool.query(
      'UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = $1',
      [id],
    );
  }
}

export default UserModel;
