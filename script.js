(function () {
  function fileURL(file) {
    if (typeof file !== 'string' || !file.startsWith('documents/') || file.includes('\\')) return null;
    const pieces = file.split('/');
    if (pieces.some(p => !p || p === '.' || p === '..')) return null;
    return pieces.map(encodeURIComponent).join('/');
  }
  function card(doc, id) {
    const row = document.createElement('div');
    row.className = 'document';
    if (id) row.id = id;
    const info = document.createElement('a');
    info.className = 'document-info';
    info.href = fileURL(doc.file);
    info.target = '_blank';
    info.rel = 'noopener';
    const title = document.createElement('strong');
    title.textContent = doc.title;
    const description = document.createElement('small');
    description.textContent = doc.description || '';
    info.append(title, description);
    const download = document.createElement('a');
    download.href = info.getAttribute('href');
    download.setAttribute('download', '');
    download.className = 'document-download';
    download.textContent = 'Download ↓';
    download.setAttribute('aria-label', 'Download ' + doc.title);
    row.append(info, download);
    return row;
  }
  const cv = window.siteCV;
  const cvArea = document.querySelector('#cv-download');
  if (cvArea) {
    cvArea.replaceChildren();
    if (cv && cv.title && fileURL(cv.file)) cvArea.append(card(cv, 'cv-pdf'));
  }
  const list = document.querySelector('#document-list');
  const usedIDs = new Set([...document.querySelectorAll('[id]')].map(e => e.id));
  const seenFiles = new Set(cv && cv.file ? [cv.file] : []);
  if (list && Array.isArray(window.siteDocuments)) {
    list.replaceChildren();
    for (const [index, doc] of window.siteDocuments.entries()) {
      if (!doc.title || !fileURL(doc.file) || seenFiles.has(doc.file)) continue;
      // Never display legacy generated text CVs in the general document list.
      if (doc.file === 'documents/dovan-darazi-cv.txt') continue;
      seenFiles.add(doc.file);
      const requested = 'document-' + (doc.id || String(index + 1)).replace(/[^a-z0-9-]/gi, '-').toLowerCase();
      let id = requested;
      let suffix = 2;
      while (usedIDs.has(id)) id = requested + '-' + suffix++;
      usedIDs.add(id);
      list.append(card(doc, id));
      if (doc.section) {
        const target = document.getElementById(doc.section);
        if (target && target.tagName === 'ARTICLE') {
          let group = target.querySelector('.entry-documents');
          if (!group) {
            group = document.createElement('div');
            group.className = 'entry-documents';
            const heading = document.createElement('h4');
            heading.textContent = 'Documents';
            group.append(heading);
            target.append(group);
          }
          group.append(card(doc));
        }
      }
    }
    if (!list.children.length && !(cv && cv.file)) {
      const empty = document.createElement('p');
      empty.textContent = 'No documents published yet.';
      list.append(empty);
    }
  }
  if ('IntersectionObserver' in window) {
    const links = [...document.querySelectorAll('nav a')];
    const observer = new IntersectionObserver(entries => {
      const visible = entries.filter(e => e.isIntersecting);
      if (!visible.length) return;
      const id = visible[0].target.id;
      links.forEach(a => {
        const active = a.hash === '#' + id;
        a.classList.toggle('active', active);
        if (active) a.setAttribute('aria-current', 'location');
        else a.removeAttribute('aria-current');
      });
    }, { rootMargin: '-10% 0px -65% 0px', threshold: 0 });
    document.querySelectorAll('main section').forEach(s => observer.observe(s));
  }
  // Resolve direct links to document cards created above.
  try {
    const id = decodeURIComponent(location.hash.slice(1));
    if (id.startsWith('document-') || id === 'cv-pdf') {
      document.getElementById(id)?.scrollIntoView();
    }
  } catch (_) { /* Keep the page usable for an invalid URL fragment. */ }
})();
