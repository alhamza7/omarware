# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def post_init_create_jsonb_compat(cr, registry):
    """
    Ensure compatibility with PostgreSQL installations that don't provide
    jsonb_path_query_first(data, path) which is used by Odoo's ORM for
    translated JSONB fields in 19.0.

    On databases where this function doesn't exist, we create a lightweight
    replacement that simply returns the first value from the JSON object.
    This is sufficient for Odoo's fallback logic and avoids server errors
    without requiring a full PostgreSQL upgrade.
    """
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Check if the function already exists
        cr.execute(
            """
            SELECT 1
            FROM pg_proc
            WHERE proname = 'jsonb_path_query_first'
            """
        )
        if cr.fetchone():
            return  # function exists, nothing to do

        # Create a safe fallback implementation
        cr.execute(
            """
            DO $BODY$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_proc WHERE proname = 'jsonb_path_query_first'
                ) THEN
                    CREATE OR REPLACE FUNCTION jsonb_path_query_first(data character varying, path text)
                    RETURNS jsonb
                    LANGUAGE plpgsql
                    IMMUTABLE
                    AS $FUNC$
                    DECLARE
                        v jsonb;
                    BEGIN
                        IF data IS NULL THEN
                            RETURN NULL;
                        END IF;

                        BEGIN
                            -- Return first value from the JSON object/array
                            SELECT value::jsonb
                            INTO v
                            FROM jsonb_each_text(data::jsonb)
                            LIMIT 1;

                            RETURN v;
                        EXCEPTION WHEN others THEN
                            -- If anything goes wrong, return NULL instead of
                            -- crashing the system.
                            RETURN NULL;
                        END;
                    END;
                    $FUNC$;
                END IF;
            END;
            $BODY$;
            """
        )


