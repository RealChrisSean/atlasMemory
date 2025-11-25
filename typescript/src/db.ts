// src/db.ts

import mysql from 'mysql2/promise';
import 'dotenv/config';

export const pool = mysql.createPool({
    host: process.env.TIDB_HOST!,
    port: Number(process.env.TIDB_PORT || 4000),
    user: process.env.TIDB_USER!,
    password: process.env.TIDB_PASSWORD!,
    database: process.env.TIDB_DATABASE!,
    ssl: { rejectUnauthorized: true },
});

export async function testConnection() {
    const [rows] = await pool.query('SELECT 1 + 1 AS result');
    console.log(rows);
}