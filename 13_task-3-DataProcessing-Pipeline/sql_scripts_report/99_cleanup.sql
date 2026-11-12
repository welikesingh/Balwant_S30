-- Removes ONLY the working schema created by scripts 10-12 (sentinel_dq).
-- Your loaded data in public.* is not touched.
DROP SCHEMA IF EXISTS sentinel_dq CASCADE;
