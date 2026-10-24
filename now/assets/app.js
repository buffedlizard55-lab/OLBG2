// Small progressive enhancement only: deep-link sections and copy a pick.
document.addEventListener('click', function (e) {
  var a = e.target.closest('a[data-copy]');
  if (!a) return;
  e.preventDefault();
  if (navigator.clipboard) navigator.clipboard.writeText(a.getAttribute('data-copy'));
  a.textContent = 'copied';
});
