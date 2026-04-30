export function enhanceTables() {
  // Global Table Enhancement: Fix glass effect clipping, add Global Search & Global Sort
  document.querySelectorAll('.section-card table').forEach(table => {
    // 1. Wrap table to fix glass effect clipping (keeps backdrop-filter intact on scroll)
    let wrapper = table.parentElement;
    if (!wrapper.classList.contains('table-responsive')) {
      wrapper = document.createElement('div');
      wrapper.className = 'table-responsive';
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    }
    
    const sectionCard = table.closest('.section-card');
    const tbody = table.querySelector('tbody');
    
    // 2. Add Global Search Feature
    let toolbar = sectionCard.querySelector('.toolbar');
    if (!toolbar) {
      toolbar = document.createElement('div');
      toolbar.className = 'toolbar';
      sectionCard.insertBefore(toolbar, wrapper);
    }
    
    let searchInput = toolbar.querySelector('input[type="text"]');
    if (!searchInput) {
      searchInput = document.createElement('input');
      searchInput.type = 'text';
      searchInput.placeholder = 'Search table...';
      toolbar.insertBefore(searchInput, toolbar.firstChild);
      
      if (tbody) {
        const doSearch = () => {
          const term = searchInput.value.toLowerCase();
          Array.from(tbody.querySelectorAll('tr')).forEach(row => {
            if (row.querySelector('td[colspan]')) return; 
            row.style.display = row.textContent.toLowerCase().includes(term) ? '' : 'none';
          });
        };
        
        searchInput.addEventListener('input', doSearch);
        new MutationObserver(doSearch).observe(tbody, { childList: true });
      }
    }
    
    // 3. Add Global Sorting Feature
    const thead = table.querySelector('thead');
    if (thead && tbody) {
      thead.querySelectorAll('th').forEach(th => {
        th.classList.add('sortable-th');
        th.title = 'Click to sort';
        th.addEventListener('click', () => {
          const rows = Array.from(tbody.querySelectorAll('tr'));
          if (rows.length === 0 || rows[0].querySelector('td[colspan]')) return; 
          
          const index = Array.from(th.parentNode.children).indexOf(th);
          const isAscending = th.dataset.sortDir === 'asc';
          
          rows.sort((a, b) => {
            const aText = a.children[index].textContent.trim();
            const bText = b.children[index].textContent.trim();
            
            // Check for ISO dates like YYYY-MM-DD
            const isDate = /^\d{4}-\d{2}-\d{2}/.test(aText) && /^\d{4}-\d{2}-\d{2}/.test(bText);
            if (isDate) {
              return isAscending ? aText.localeCompare(bText) : bText.localeCompare(aText);
            }
            
            const aNum = parseFloat(aText.replace(/[^0-9.-]+/g, ''));
            const bNum = parseFloat(bText.replace(/[^0-9.-]+/g, ''));
            const isNum = !isNaN(aNum) && !isNaN(bNum) && /^[0-9$.%-]/.test(aText) && /^[0-9$.%-]/.test(bText);
            
            if (isNum) {
              return isAscending ? aNum - bNum : bNum - aNum;
            } else {
              return isAscending ? aText.localeCompare(bText) : bText.localeCompare(aText);
            }
          });
          
          thead.querySelectorAll('th').forEach(h => h.dataset.sortDir = '');
          th.dataset.sortDir = isAscending ? 'desc' : 'asc';
          tbody.append(...rows);
        });
      });
    }
  });
}
