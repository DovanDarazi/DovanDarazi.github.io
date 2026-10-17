// Preserve older shared section URLs when using the new CV website.
(function () {
  const aliases = {
    'contact-information': 'top',
    'academic-history': 'education',
    'qualifications-skills': 'skills',
    'awards-honors': 'awards',
    'publications-presentations': 'publications',
    'licenses-certifications': 'certifications',
    'grants-scholarships': 'awards'
  };
  function resolveLegacyLink() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    if (!id || document.getElementById(id)) return;
    const target = document.getElementById(aliases[id] || '');
    if (target) {
      history.replaceState(null, '', '#' + target.id);
      target.scrollIntoView();
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', resolveLegacyLink);
  } else { resolveLegacyLink(); }
  window.addEventListener('hashchange', resolveLegacyLink);
})();
