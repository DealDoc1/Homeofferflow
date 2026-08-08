-- Migration-history compatibility marker.
-- This version already exists in the production Supabase migration history.
-- The original tracker-only operation was applied remotely before the SQL was
-- committed to this repository; keep the exact version locally so Supabase
-- branches can replay the ordered history without migration drift.

do $$
begin
  null;
end
$$;
