// One optional enhancement: a filter box above the large tables.
document.querySelectorAll('[data-filterable]').forEach(function (wrap) {
  var input = document.createElement('input');
  input.type = 'search';
  input.placeholder = 'Filter rows…';
  input.setAttribute('aria-label', 'Filter table rows');
  input.style.cssText = 'margin:10px 0;padding:8px 12px;width:min(320px,100%);border:1px solid #cbd5e1;'
    + 'border-radius:8px;font:inherit;font-size:13.5px;background:#fff';
  wrap.parentNode.insertBefore(input, wrap);
  input.addEventListener('input', function () {
    var q = input.value.toLowerCase();
    wrap.querySelectorAll('tbody tr').forEach(function (tr) {
      tr.style.display = tr.textContent.toLowerCase().indexOf(q) === -1 ? 'none' : '';
    });
  });
});
