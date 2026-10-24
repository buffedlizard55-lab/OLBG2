(() => {
  const table = document.querySelector('table.table tbody');
  const rows = table ? Array.from(table.querySelectorAll('tr')) : [];
  const search = document.querySelector('#filter-search');
  const sport = document.querySelector('#filter-sport');
  const status = document.querySelector('#filter-status');
  const category = document.querySelector('#filter-category');
  const count = document.querySelector('#filter-count');
  function applyFilters() {
    let n = 0;
    const q = (search?.value || '').trim().toLocaleLowerCase();
    for (const row of rows) {
      const text = (row.dataset.search || row.textContent).toLocaleLowerCase();
      const ok = (!q || text.includes(q)) && (!sport?.value || row.dataset.sport === sport.value)
        && (!status?.value || row.dataset.status === status.value)
        && (!category?.value || row.dataset.category === category.value);
      row.hidden = !ok;
      if (ok) n++;
    }
    if (count) count.textContent = `${n} of ${rows.length} rows`;
  }
  [search, sport, status, category].filter(Boolean).forEach(control => control.addEventListener('input', applyFilters));
  if (count) applyFilters();
  function expireHighlights() {
    const now = Date.now();
    document.querySelectorAll('[data-archive-badge][data-start]').forEach(card => {
      const date = Date.parse(card.dataset.start);
      const label = card.querySelector('.expiry');
      if (Number.isFinite(date) && date <= now) {
        if (label) { label.textContent = 'Started / archived'; label.classList.add('expired'); }
        if (card.closest('[data-expire-group]')) card.hidden = true;
      } else if (label) { label.textContent = 'Future at device time'; label.classList.remove('expired'); }
    });
    const group = document.querySelector('[data-expire-group]');
    const empty = document.querySelector('.after-expiry');
    if (group && empty) empty.hidden = !!group.querySelector('[data-start]:not([hidden])');
  }
  expireHighlights();
  setInterval(expireHighlights, 60000);
})();