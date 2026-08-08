-- Migration-history compatibility marker for the already-applied production
-- tracker reconciliation. It intentionally makes no schema or data change.

do $$
begin
  null;
end
$$;
