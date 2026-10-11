-- Owner-confirmed business identity; blank-only, idempotent data maintenance.
-- No roles, memberships, signed documents, or existing licenses are changed.
update public.hof_brokerages
set license_number = '9010832', updated_at = now()
where id = '57f5c952-80af-4ba9-9f7f-ad99dcbc31c5'
  and lower(slug) = 'ondemand'
  and nullif(btrim(license_number), '') is null;

select slug, name, license_number
from public.hof_brokerages
where id = '57f5c952-80af-4ba9-9f7f-ad99dcbc31c5';
