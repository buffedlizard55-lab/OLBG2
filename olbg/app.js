
document.querySelectorAll('[data-menu]').forEach(function(button){button.addEventListener('click',function(){var nav=document.querySelector('[data-nav]');var open=nav.classList.toggle('open');button.setAttribute('aria-expanded',String(open));});});
document.querySelectorAll('[data-filter]').forEach(function(input){input.addEventListener('input',function(){var table=document.getElementById(input.dataset.filter);var query=input.value.toLowerCase().trim();table.querySelectorAll('tbody tr').forEach(function(row){row.hidden=query && !row.textContent.toLowerCase().includes(query);});});});
