-- Reconcile the mobile-app roadmap with the live, low-cost PWA bridge.
-- This is tracker metadata only: it does not alter PWA caching, authentication,
-- offer data, billing, documents, or any restricted Texas-form gate.

update public.hof_roadmap_items
set
  status = 'in_progress',
  environment = 'production',
  qa_status = 'partial',
  current_release = '08f49fd keyboard-accessible Google Places PWA shell (2026-08-14)',
  known_issues = 'The installable PWA is live with a network-first public shell, explicit update control, and safe shortcuts for workspace, new offer, buyer offer, signing queue, and Seller Plan. It intentionally does not cache APIs, signed documents, or authenticated data offline. No native iOS or Android app exists yet.',
  next_action = 'Use privacy-safe PWA install and shortcut-return signals to prioritize the next mobile workflow. Keep the PWA as the low-cost app bridge; evaluate a native build only after sustained demand and a mobile authentication, RLS, push-notification, app-store, and release-QA plan.',
  metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
    'pwa_status', 'production',
    'native_status', 'not_started',
    'pwa_shortcuts', jsonb_build_array('workspace', 'new_offer', 'buyer_offer', 'signing_queue', 'seller_plan'),
    'offline_policy', 'public_shell_only_no_api_documents_or_authenticated_data'
  ),
  updated_at = now()
where slug = 'mobile-app';

-- Verification after applying:
-- select slug, status, environment, qa_status, current_release, known_issues,
--        next_action, metadata
-- from public.hof_roadmap_items where slug = 'mobile-app';
