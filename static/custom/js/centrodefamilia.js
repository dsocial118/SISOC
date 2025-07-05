// centrodefamilia.js

// 1) Live filters immediately invoked (no need to wait for DOMContentLoaded)
(function(){
  // Filtrar Centros
  const fc = document.getElementById('filterCentros'),
        tbC = document.querySelector('#tablaCentros tbody');
  fc?.addEventListener('input', ()=>{
    const t = fc.value.trim().toLowerCase();
    tbC.querySelectorAll('tr').forEach(r=>{
      r.style.display = r.cells[0].textContent.trim().toLowerCase().startsWith(t)
        ? '' : 'none';
    });
  });

  // Filtrar Actividades
  const fa = document.getElementById('filterActividades'),
        tbA = document.querySelector('#tablaActividades tbody');
  fa?.addEventListener('input', ()=>{
    const t = fa.value.trim().toLowerCase();
    tbA.querySelectorAll('tr').forEach(r=>{
      const cols = [
        r.cells[0].textContent.trim().toLowerCase(),  // Centro
        r.cells[1].textContent.trim().toLowerCase(),  // Actividad
        r.cells[2].textContent.trim().toLowerCase(),  // Categoría
        r.cells[3].textContent.trim().toLowerCase()   // Estado
      ];
      r.style.display = cols.some(c => c.startsWith(t)) ? '' : 'none';
    });
  });
})();

// 2) Gauges: wait for DOM + Chart.js
document.addEventListener("DOMContentLoaded", function(){
  // parse the JSON-encoded metrics from the <script id="catMetrics"> tag
  const script = document.getElementById('catMetrics');
  if (!script) return;
  let catMetrics;
  try {
    catMetrics = JSON.parse(script.textContent);
  } catch (e) {
    console.error('Invalid JSON in catMetrics', e);
    return;
  }

  if (typeof Chart === 'undefined') {
    console.error('Chart.js is not loaded');
    return;
  }

  catMetrics.forEach((cat, idx) => {
    const canvas = document.getElementById(`gauge-${idx+1}`);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['F','M'],
        datasets: [{
          data: [cat.female, cat.male],
          backgroundColor: [cat.colorF, cat.colorM],
          hoverOffset: 4,
          circumference: Math.PI,
          rotation: -Math.PI,
          cutout: '80%'
        }]
      },
      options: {
        responsive: false,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false }
        }
      }
    });
  });
});
