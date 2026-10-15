import { sql } from "drizzle-orm";
import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const customEntries = sqliteTable("custom_entries", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  name: text("name").notNull(),
  owner: text("owner"),
  excerpt: text("excerpt").notNull(),
  notes: text("notes").notNull().default(""),
  createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
});

export const restorations = sqliteTable('restorations', {
  id: text('id').primaryKey(),
  owner: text('owner').notNull(),
  title: text('title').notNull(),
  source: text('source').notNull().default(''),
  notes: text('notes').notNull().default(''),
  observed: text('observed').notNull(),
  result: text('result').notNull(),
  modelVersion: text('model_version').notNull(),
  published: integer('published').notNull().default(0),
  createdAt: text('created_at').notNull().default(sql`CURRENT_TIMESTAMP`),
});

export const createEntriesTable = `
  CREATE TABLE IF NOT EXISTS custom_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )
`;
