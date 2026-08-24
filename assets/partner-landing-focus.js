(() => {
  const guideNote = Array.from(document.querySelectorAll('p.note')).find((node) =>
    node.textContent.includes('Want the short version first?')
  );
  if (!guideNote) return;
  const details = document.createElement('details');
  details.className = 'partner-resource-links';
  const summary = document.createElement('summary');
  summary.textContent = 'Read the short partner placement guide';
  details.append(summary);
  const content = document.createElement('p');
  content.innerHTML = guideNote.innerHTML.replace('Want the short version first? ', '');
  details.append(content);
  guideNote.replaceWith(details);
})();
