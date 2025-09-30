// Fix directo para paginación
(function() {
  const selector = document.getElementById('legajos-page-size');
  if (!selector) return;
  
  selector.addEventListener('change', function() {
    const pageSize = this.value === 'all' ? 999999 : parseInt(this.value) || 10;
    const items = document.querySelectorAll('.legajo-item');
    
    console.log(`FIXING PAGINATION: ${pageSize} items, found ${items.length} legajos`);
    
    items.forEach((item, i) => {
      item.style.display = i < pageSize ? '' : 'none';
    });
  });
})();