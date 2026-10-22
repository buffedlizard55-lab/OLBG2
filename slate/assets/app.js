(function () {
  function applyFilters() {
    var qEl = document.getElementById('slate-search');
    var sportEl = document.getElementById('slate-sport');
    var confEl = document.getElementById('slate-conf');
    var q = qEl ? qEl.value.trim().toLowerCase() : '';
    var sp = sportEl ? sportEl.value : 'all';
    var cf = confEl ? confEl.value : 'all';
    var items = document.querySelectorAll('[data-filter-row]');
    var shown = 0;
    items.forEach(function (el) {
      var text = el.textContent.toLowerCase();
      var rowSp = el.getAttribute('data-sport') || '';
      var rowCf = el.getAttribute('data-conf') || '';
      var ok = (!q || text.indexOf(q) !== -1) &&
               (sp === 'all' || rowSp === sp) &&
               (cf === 'all' || rowCf === cf);
      el.style.display = ok ? '' : 'none';
      if (ok) shown += 1;
    });
    var counter = document.getElementById('slate-count');
    if (counter) counter.textContent = shown + ' shown';
  }

  function applyOddsFormat() {
    var fmtEl = document.getElementById('odds-format');
    if (!fmtEl) return;
    var mode = fmtEl.value;
    document.querySelectorAll('[data-am][data-dec][data-fair]').forEach(function (el) {
      if (mode === 'dec') el.textContent = el.getAttribute('data-dec');
      else if (mode === 'fair') el.textContent = el.getAttribute('data-fair');
      else el.textContent = el.getAttribute('data-am');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    ['slate-search', 'slate-sport', 'slate-conf'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) {
        el.addEventListener('input', applyFilters);
        el.addEventListener('change', applyFilters);
      }
    });
    var fmt = document.getElementById('odds-format');
    if (fmt) fmt.addEventListener('change', applyOddsFormat);
  });
})();
