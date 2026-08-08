-- Migration-history compatibility marker for the already-applied production
-- index operation. The live migration history contains this version; the
-- checked-in index definitions remain the source of truth for future diffs.

do $$
begin
  null;
end
$$;
