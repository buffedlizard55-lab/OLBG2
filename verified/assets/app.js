(function () {
  function initTableFilter() {
    var search = document.getElementById('filter-search');
    var sport = document.getElementById('filter-sport');
    var conf = document.getElementById('filter-conf');
    var status = document.getElementById('filter-status');
    var countEl = document.getElementById('filter-count');
    var rows = Array.prototype.slice.call(document.querySelectorAll('tr[data-match-row="1"]'));
    if (!rows.length) return;

    function apply() {
      var q = search ? search.value.trim().toLowerCase() : '';
      var sp = sport ? sport.value : 'all';
      var cf = conf ? conf.value : 'all';
      var st = status ? status.value : 'all';
      var shown = 0;
      rows.forEach(function (tr) {
        var ok = true;
        if (sp !== 'all' && tr.getAttribute('data-sport') !== sp) ok = false;
        if (cf !== 'all' && tr.getAttribute('data-conf') !== cf) ok = false;
        if (st !== 'all' && tr.getAttribute('data-status') !== st) ok = false;
        if (ok && q && tr.textContent.toLowerCase().indexOf(q) === -1) ok = false;
        tr.style.display = ok ? '' : 'none';
        if (ok) shown += 1;
      });
      if (countEl) {
        countEl.textContent = 'Showing ' + shown + ' of ' + rows.length + ' verified rows';
      }
    }

    [search, sport, conf, status].forEach(function (el) {
      if (el) {
        el.addEventListener('input', apply);
        el.addEventListener('change', apply);
      }
    });
    apply();
  }

  function initPredFilter() {
    var sel = document.getElementById('pred-sport-filter');
    var cards = Array.prototype.slice.call(document.querySelectorAll('[data-pred-card="1"]'));
    var countEl = document.getElementById('pred-filter-count');
    if (!sel || !cards.length) return;
    sel.addEventListener('change', function () {
      var v = sel.value;
      var shown = 0;
      cards.forEach(function (c) {
        var ok = (v === 'all' || c.getAttribute('data-sport') === v);
        c.style.display = ok ? '' : 'none';
        if (ok) shown += 1;
      });
      if (countEl) countEl.textContent = 'Showing ' + shown + ' of ' + cards.length + ' HIGH confidence picks';
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTableFilter();
    initPredFilter();
  });
})();
