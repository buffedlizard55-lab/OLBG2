document.addEventListener('DOMContentLoaded', () => {
  const sportSel = document.getElementById('filter-sport');
  const confSel = document.getElementById('filter-conf');
  const statusSel = document.getElementById('filter-status');
  const searchInp = document.getElementById('filter-search');
  const countSpan = document.getElementById('filter-count');

  function applyFilters() {
    const rows = document.querySelectorAll('#matches-table tbody tr');
    if (!rows.length) return;
    const sp = sportSel ? sportSel.value : '';
    const cf = confSel ? confSel.value : '';
    const st = statusSel ? statusSel.value : '';
    const q = searchInp ? searchInp.value.toLowerCase().trim() : '';
    let visible = 0;
    rows.forEach(r => {
      const mSp = !sp || r.dataset.sport === sp;
      const mCf = !cf || r.dataset.conf === cf;
      const mSt = !st || r.dataset.status === st;
      const mQ = !q || r.textContent.toLowerCase().includes(q);
      const show = mSp && mCf && mSt && mQ;
      r.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    if (countSpan) countSpan.textContent = visible;
  }

  [sportSel, confSel, statusSel].forEach(el => el && el.addEventListener('change', applyFilters));
  if (searchInp) searchInp.addEventListener('input', applyFilters);
});
