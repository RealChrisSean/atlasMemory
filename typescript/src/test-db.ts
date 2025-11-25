// src/test-db.ts
import { testConnection } from './db.js';

async function main() {
    console.log('Testing TiDB connection...');
    await testConnection();
    console.log('Done.');
}

main().catch((err) => {
    console.error('Error testing DB:', err);
});