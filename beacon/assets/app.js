(function () {
  function initTableFilter() {
    var searchInput = document.getElementById('beacon-search');
    var sportSelect = document.getElementById('beacon-sport');
    var stateSelect = document.getElementById('beacon-state');
    var confSelect = document.getElementById('beacon-conf');
    var countEl = document.getElementById('beacon-visible-count');
    var tbody = document.querySelector('table[data-filterable="1"] tbody');
    if (!tbody) return;
    var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));

    function apply() {
      var q = searchInput ? searchInput.value.trim().toLowerCase() : '';
      var sp = sportSelect ? sportSelect.value : '';
      var st = stateSelect ? stateSelect.value : '';
      var cf = confSelect ? confSelect.value : '';
      var shown = 0;
      rows.forEach(function (tr) {
        var ok = true;
        if (sp && tr.getAttribute('data-sport') !== sp) ok = false;
        if (st && tr.getAttribute('data-state') !== st) ok = false;
        if (cf && tr.getAttribute('data-conf') !== cf) ok = false;
        if (ok && q && tr.textContent.toLowerCase().indexOf(q) === -1) ok = false;
        tr.style.display = ok ? '' : 'none';
        if (ok) shown += 1;
      });
      if (countEl) countEl.textContent = shown + ' of ' + rows.length + ' rows shown';
    }

    [searchInput, sportSelect, stateSelect, confSelect].forEach(function (el) {
      if (el) el.addEventListener('input', apply);
      if (el) el.addEventListener('change', apply);
    });
    apply();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTableFilter);
  } else {
    initTableFilter();
  }
})();
