begin;

update public.hof_roadmap_items
set
  status = 'blocked',
  environment = 'source_gate',
  qa_status = case
    when slug = 'txr-1507-short-buyer-tenant-representation' then 'partial'
    else 'not_tested'
  end,
  current_release = case
    when slug = 'txr-1507-short-buyer-tenant-representation' then 'Private draft foundation + renderer QA'
    else 'Private draft foundation'
  end,
  known_issues = case
    when slug = 'txr-1507-short-buyer-tenant-representation' then 'No authorized private source record is available. Draft renderer QA is partial across four private source scenarios, but the foundation cannot expose, generate, send, or sign this Texas REALTORS form until an authorized source-owner administrator uploads and attests to the current authorized source; completed SignWell packet QA is still pending.'
    else 'No authorized private source record is available. The draft foundation cannot expose, generate, send, or sign this Texas REALTORS form until an authorized source-owner administrator uploads and attests to the current authorized source.'
  end
where slug in (
  'txr-1507-short-buyer-tenant-representation',
  'txr-1501-long-buyer-tenant-representation',
  'txr-1508-unrepresented-showing',
  'txr-1506-general-information-notice'
);

commit;

