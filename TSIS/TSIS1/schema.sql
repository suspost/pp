
-- schema.sql
-- Drop existing objects in correct order (CASCADE for functions/procedures)
DROP TABLE IF EXISTS phones CASCADE;
DROP TABLE IF EXISTS contacts CASCADE;
DROP TABLE IF EXISTS groups CASCADE;

DROP FUNCTION IF EXISTS search_contacts(text) CASCADE;
DROP PROCEDURE IF EXISTS add_phone(varchar, varchar, varchar) CASCADE;
DROP PROCEDURE IF EXISTS move_to_group(varchar, varchar) CASCADE;
DROP FUNCTION IF EXISTS get_contacts_paginated(int, int) CASCADE;

-- Groups table
CREATE TABLE groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Contacts table (extended)
CREATE TABLE contacts (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) UNIQUE NOT NULL,
    email      VARCHAR(100),
    birthday   DATE,
    group_id   INTEGER REFERENCES groups(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Phones table (1-to-many)
CREATE TABLE phones (
    id         SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20) NOT NULL,
    type       VARCHAR(10) CHECK (type IN ('home', 'work', 'mobile'))
);

-- Pre‑load default groups
INSERT INTO groups (name) VALUES ('Family'), ('Work'), ('Friend'), ('Other')
ON CONFLICT (name) DO NOTHING;