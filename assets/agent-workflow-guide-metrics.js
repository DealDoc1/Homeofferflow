(() => {
  const storagePrefix = 'hof_agent_workflow_guide_';
  const record = (eventType) => {
    try {
      if (sessionStorage.getItem(storagePrefix + eventType)) return;
      sessionStorage.setItem(storagePrefix + eventType, '1');
      fetch('/api/fsbo-lead', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        keepalive: true,
        body: JSON.stringify({
          request_type: 'agent_landing_event',
          event_type: eventType,
          channel: 'unspecified',
        }),
      }).catch(() => {});
    } catch (_) {}
  };

  record('agent_workflow_guide_viewed');
  document.querySelectorAll('a[href^="/?agent=1"]').forEach((link) => {
    link.addEventListener('click', () => record('agent_workflow_guide_cta_selected'));
  });
})();
