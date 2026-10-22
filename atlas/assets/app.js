
document.addEventListener('DOMContentLoaded',function(){
  var q=document.getElementById('q');
  if(!q) return;
  var rows=[].slice.call(document.querySelectorAll('tbody tr'));
  function apply(){
    var v=q.value.toLowerCase();
    rows.forEach(function(r){
      r.style.display = r.textContent.toLowerCase().indexOf(v)>-1 ? '' : 'none';
    });
  }
  q.addEventListener('input',apply);
  var sp=document.getElementById('fsport');
  if(sp){ sp.addEventListener('change',function(){
    var s=sp.value;
    rows.forEach(function(r){ r.style.display = (!s||r.dataset.sport===s)?'':'none'; });
  });}
});
