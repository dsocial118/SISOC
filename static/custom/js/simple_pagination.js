// Paginación simple que funciona
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(() => {
    const selector = document.getElementById('legajos-page-size');
    const list = document.getElementById('legajos-list');
    
    console.log('Simple pagination - Elements:', { 
      selector: !!selector, 
      list: !!list,
      selectorValue: selector?.value
    });
    
    if (!selector || !list) {
      console.log('Missing elements for pagination');
      return;
    }
    
    const items = list.querySelectorAll('.legajo-item');
    console.log('Simple pagination - Items found:', items.length);
    
    if (items.length === 0) {
      console.log('No items to paginate');
      return;
    }
    
    function applyPagination() {
      const pageSize = selector.value === 'all' ? items.length : parseInt(selector.value) || 10;
      
      console.log(`APPLYING PAGINATION: pageSize=${pageSize}, totalItems=${items.length}`);
      
      items.forEach((item, index) => {
        const shouldShow = index < pageSize;
        item.style.display = shouldShow ? '' : 'none';
        
        if (index < 3) {
          console.log(`Item ${index}: ${shouldShow ? 'VISIBLE' : 'HIDDEN'}`);
        }
      });
      
      console.log(`LEGAJOS: Showing ${Math.min(pageSize, items.length)} of ${items.length} items`);
    }
    
    selector.addEventListener('change', function() {
      console.log('LEGAJOS: Selector changed to:', this.value);
      applyPagination();
    });
    
    console.log('Applying initial pagination...');
    applyPagination();
    
    window.testLegajosPagination = applyPagination;
    
  }, 200);
});