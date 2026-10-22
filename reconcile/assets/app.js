// Filter any table whose rows carry data-search attributes.
document.querySelectorAll('[data-filter]').forEach(function(box){
  var target = document.getElementById(box.dataset.filter);
  if(!target) return;
  box.addEventListener('input', function(){
    var q = box.value.toLowerCase();
    target.querySelectorAll('tbody tr').forEach(function(tr){
      tr.style.display = (!q || (tr.dataset.search||'').toLowerCase().includes(q)) ? '' : 'none';
    });
  });
});
document.querySelectorAll('th[data-sort]').forEach(function(th){
  th.style.cursor='pointer';
  th.addEventListener('click', function(){
    var table = th.closest('table'), idx = Array.from(th.parentNode.children).indexOf(th);
    var dir = th.dataset.dir === 'asc' ? -1 : 1; th.dataset.dir = dir === 1 ? 'asc' : 'desc';
    var rows = Array.from(table.tBodies[0].rows);
    rows.sort(function(a,b){
      var av = a.cells[idx].dataset.v || a.cells[idx].innerText;
      var bv = b.cells[idx].dataset.v || b.cells[idx].innerText;
      var an = parseFloat(av), bn = parseFloat(bv);
      if(!isNaN(an) && !isNaN(bn)) return (an-bn)*dir;
      return av.localeCompare(bv)*dir;
    });
    rows.forEach(function(r){ table.tBodies[0].appendChild(r); });
  });
});
