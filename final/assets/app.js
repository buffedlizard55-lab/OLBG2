
(function(){
  const table=document.getElementById('matches');
  if(!table) return;
  const rows=[...table.tBodies[0].rows];
  const sport=document.getElementById('f-sport');
  const conf=document.getElementById('f-conf');
  const status=document.getElementById('f-status');
  const text=document.getElementById('f-text');
  const count=document.getElementById('f-count');
  function apply(){
    const s=sport.value,c=conf.value,st=status.value,q=text.value.toLowerCase().trim();
    let n=0;
    rows.forEach(r=>{
      const ok=(!s||r.dataset.sport===s)&&(!c||r.dataset.conf===c)&&(!st||r.dataset.status===st)&&(!q||r.dataset.search.includes(q));
      r.style.display=ok?'':'none'; if(ok)n++;
    });
    if(count) count.textContent=n+' of '+rows.length+' rows';
  }
  [sport,conf,status].forEach(el=>el&&el.addEventListener('change',apply));
  text&&text.addEventListener('input',apply);
  apply();
})();
