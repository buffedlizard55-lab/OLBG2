
// Client-side filter + column sort. Progressive enhancement: the tables are
// complete and readable with JavaScript disabled.
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('input[data-filter]').forEach(function (inp) {
    inp.addEventListener('input', function () {
      var q = inp.value.trim().toLowerCase();
      var tbl = document.querySelector(inp.getAttribute('data-filter'));
      if (!tbl) return;
      tbl.querySelectorAll('tbody tr').forEach(function (tr) {
        tr.style.display = !q || tr.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
      });
    });
  });
  document.querySelectorAll('select[data-sportfilter]').forEach(function (sel) {
    sel.addEventListener('change', function () {
      var tbl = document.querySelector(sel.getAttribute('data-sportfilter'));
      if (!tbl) return;
      tbl.querySelectorAll('tbody tr').forEach(function (tr) {
        tr.style.display = sel.value === 'all' || tr.getAttribute('data-sport') === sel.value ? '' : 'none';
      });
    });
  });
  document.querySelectorAll('table[data-sortable] th').forEach(function (th, i) {
    th.addEventListener('click', function () {
      var tbl = th.closest('table'), tb = tbl.querySelector('tbody');
      var rows = Array.prototype.slice.call(tb.querySelectorAll('tr'));
      var dir = th.getAttribute('data-dir') === 'asc' ? 'desc' : 'asc';
      tbl.querySelectorAll('th').forEach(function (o) { o.removeAttribute('data-dir'); });
      th.setAttribute('data-dir', dir);
      rows.sort(function (a, b) {
        var x = (a.children[i] ? a.children[i].textContent : '').trim();
        var y = (b.children[i] ? b.children[i].textContent : '').trim();
        var nx = parseFloat(x.replace(/[^0-9.\-]/g, '')), ny = parseFloat(y.replace(/[^0-9.\-]/g, ''));
        var c = (!isNaN(nx) && !isNaN(ny)) ? nx - ny : x.localeCompare(y);
        return dir === 'asc' ? c : -c;
      });
      rows.forEach(function (r) { tb.appendChild(r); });
    });
  });
});
