/**
 * Bootstrap script: create the first admin user.
 *
 * Usage (inside the running backend container):
 *   docker compose exec -e ADMIN_EMAIL=you@example.com -e ADMIN_PASSWORD=strongpw backend \
 *     npx ts-node scripts/create-admin.ts
 *
 * Or locally with a reachable DB (set DB_* env + ADMIN_EMAIL + ADMIN_PASSWORD):
 *   npx ts-node scripts/create-admin.ts
 *
 * Idempotent: if the email already exists, the script exits without changes.
 */
import { config } from 'dotenv';
import { Pool } from 'pg';
import { databaseConfig } from '../src/config/database';
import { AuthService } from '../src/services/authService';

config();

async function main(): Promise<void> {
  const email = process.env.ADMIN_EMAIL?.trim().toLowerCase();
  const password = process.env.ADMIN_PASSWORD;

  if (!email || !password) {
    console.error('ERROR: set ADMIN_EMAIL and ADMIN_PASSWORD env vars');
    process.exit(1);
  }
  if (password.length < 8) {
    console.error('ERROR: ADMIN_PASSWORD must be at least 8 characters');
    process.exit(1);
  }

  const pool = new Pool(databaseConfig);
  const auth = new AuthService(pool);

  try {
    const existing = await auth.findUserByEmail(email);
    if (existing) {
      console.log(`User ${email} already exists (admin=${existing.is_admin}). Nothing to do.`);
      return;
    }
    const user = await auth.createUserAsAdmin({ email, password, isAdmin: true });
    console.log(`Admin created: ${user.email} (id=${user.id})`);
  } finally {
    await pool.end();
  }
}

main().catch((err) => {
  console.error('Failed to create admin:', err);
  process.exit(1);
});
