import { Pool } from 'pg';
import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';
import { databaseConfig } from '../src/config/database';

interface MigrationFile {
  filename: string;
  path: string;
  order: number;
}

async function runMigrations(): Promise<void> {
  const pool = new Pool(databaseConfig);

  try {
    console.log('🔌 Connecting to database...');
    await pool.query('SELECT NOW()');
    console.log('✅ Database connection established');

    const migrationsDir = join(__dirname, '..', 'migrations');
    console.log(`📂 Reading migrations from: ${migrationsDir}`);

    // Read all .sql files from migrations directory
    const files = readdirSync(migrationsDir)
      .filter(file => file.endsWith('.sql'))
      .sort(); // Sort alphabetically (001_, 002_, etc.)

    if (files.length === 0) {
      console.log('⚠️  No migration files found');
      return;
    }

    console.log(`📋 Found ${files.length} migration file(s):`);
    files.forEach(file => console.log(`   - ${file}`));

    // Run each migration
    for (const file of files) {
      const filePath = join(migrationsDir, file);
      console.log(`\n🔄 Running migration: ${file}`);

      try {
        const sql = readFileSync(filePath, 'utf8');
        await pool.query(sql);
        console.log(`✅ Successfully applied: ${file}`);
      } catch (error) {
        if (error instanceof Error) {
          // Check if error is due to object already existing (idempotent migrations)
          if (error.message.includes('already exists')) {
            console.log(`⏭️  Skipped (already applied): ${file}`);
          } else {
            console.error(`❌ Failed to apply migration: ${file}`);
            console.error(`   Error: ${error.message}`);
            throw error;
          }
        } else {
          throw error;
        }
      }
    }

    // Verify migrations by checking tables
    console.log('\n🔍 Verifying database schema...');
    const result = await pool.query(`
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'public'
      ORDER BY table_name;
    `);

    if (result.rows.length > 0) {
      console.log('✅ Database tables created:');
      result.rows.forEach(row => console.log(`   - ${row.table_name}`));
    } else {
      console.log('⚠️  No tables found in database');
    }

    console.log('\n🎉 Migration completed successfully!');
  } catch (error) {
    console.error('\n💥 Migration failed:');
    if (error instanceof Error) {
      console.error(error.message);
      console.error(error.stack);
    }
    process.exit(1);
  } finally {
    await pool.end();
    console.log('🔌 Database connection closed');
  }
}

// Run migrations
runMigrations().catch(error => {
  console.error('Unhandled error:', error);
  process.exit(1);
});
