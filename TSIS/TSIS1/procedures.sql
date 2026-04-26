
-- procedures.sql (исправленный)

-- 1. Extended search function (matches name, email, or any phone number)
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE(
    id          INTEGER,
    name        VARCHAR,
    email       VARCHAR,
    birthday    DATE,
    group_name  VARCHAR,
    phones      VARCHAR[],   -- изменено с TEXT[]
    created_at  TIMESTAMP
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.name, c.email, c.birthday, g.name AS group_name,
           ARRAY_AGG(DISTINCT p.phone) FILTER (WHERE p.phone IS NOT NULL) AS phones,
           c.created_at
    FROM contacts c
    LEFT JOIN groups g ON c.group_id = g.id
    LEFT JOIN phones p ON c.id = p.contact_id
    WHERE c.name ILIKE '%' || p_query || '%'
       OR c.email ILIKE '%' || p_query || '%'
       OR p.phone ILIKE '%' || p_query || '%'
    GROUP BY c.id, g.name, c.created_at
    ORDER BY c.name;
END;
$$;

-- 2. Add phone to an existing contact (by name) – без изменений
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR
) LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    SELECT id INTO v_contact_id FROM contacts WHERE name = p_contact_name;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Contact "%" does not exist', p_contact_name;
    END IF;

    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Invalid phone type: % (must be home, work, mobile)', p_type;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type)
    ON CONFLICT DO NOTHING;
END;
$$;

-- 3. Move contact to a group – без изменений
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
) LANGUAGE plpgsql AS $$
DECLARE
    v_group_id INTEGER;
    v_contact_id INTEGER;
BEGIN
    INSERT INTO groups (name) VALUES (p_group_name)
    ON CONFLICT (name) DO NOTHING;

    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;
    SELECT id INTO v_contact_id FROM contacts WHERE name = p_contact_name;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" does not exist', p_contact_name;
    END IF;

    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;
END;
$$;

-- 4. Paginated contact query – исправлено
CREATE OR REPLACE FUNCTION get_contacts_paginated(
    p_limit INT,
    p_offset INT
)
RETURNS TABLE(
    id         INTEGER,
    name       VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR,
    phones     VARCHAR[],   -- изменено с TEXT[]
    created_at TIMESTAMP
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.name, c.email, c.birthday, g.name,
           ARRAY_AGG(DISTINCT p.phone) FILTER (WHERE p.phone IS NOT NULL),
           c.created_at
    FROM contacts c
    LEFT JOIN groups g ON c.group_id = g.id
    LEFT JOIN phones p ON c.id = p.contact_id
    GROUP BY c.id, g.name, c.created_at
    ORDER BY c.name
    LIMIT p_limit OFFSET p_offset;
END;
$$;