/* ── dashboard.js ── */
const API = '/api/dashboard';

async function loadDashboard() {
  try {
    const res = await fetch(API);
    const d   = await res.json();

    // KPI cards
    setText('liq-total',    fmt(d.liquidos_hoy.total));
    setText('liq-galones',  d.liquidos_hoy.galones.toFixed(2) + ' gal');
    setText('liq-registros',d.liquidos_hoy.registros + ' registros hoy');

    setText('glp-total',    fmt(d.glp_hoy.total));
    setText('glp-galones',  d.glp_hoy.galones.toFixed(2) + ' kg');
    setText('glp-registros',d.glp_hoy.registros + ' registros hoy');

    const grandTotal = d.liquidos_hoy.total + d.glp_hoy.total;
    setText('grand-total',  fmt(grandTotal));

    // Bar chart (liquidos semana)
    renderBars(d.liq_semana);

    // Activity feed
    renderActivity(d.actividad_reciente);
  } catch(e) {
    console.error('Error cargando dashboard:', e);
  }
}

function fmt(n) {
  return 'S/ ' + Number(n).toLocaleString('es-PE', {minimumFractionDigits:2, maximumFractionDigits:2});
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function renderBars(weekData) {
  const container = document.getElementById('bar-chart');
  if (!container) return;
  if (!weekData || weekData.length === 0) {
    container.innerHTML = '<p class="text-slate-500 text-sm text-center pt-8">Sin datos esta semana</p>';
    return;
  }
  const max = Math.max(...weekData.map(r => r.total), 1);
  const days = ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'];

  container.innerHTML = weekData.map((r, i) => {
    const pct  = Math.max(8, (r.total / max) * 100);
    const dow  = new Date(r.fecha + 'T00:00:00').getDay();
    const label = days[dow === 0 ? 6 : dow - 1] || r.fecha.slice(5);
    const isLast = i === weekData.length - 1;
    return `
      <div class="flex flex-col items-center gap-1 flex-1">
        <span class="text-xs text-slate-400 hidden sm:block">${fmt(r.total)}</span>
        <div class="w-full flex items-end justify-center" style="height:120px">
          <div class="bar-col w-10 rounded-t-md ${isLast ? 'highlight' : 'bg-orange-800'}"
               style="height:${pct}%"></div>
        </div>
        <span class="text-xs text-slate-300">${label}</span>
      </div>`;
  }).join('');
}

function renderActivity(items) {
  const ul = document.getElementById('activity-list');
  if (!ul) return;
  if (!items || items.length === 0) {
    ul.innerHTML = '<li class="text-slate-500 text-sm">Sin actividad reciente</li>';
    return;
  }
  // sort by fecha desc (already is, but mix)
  ul.innerHTML = items.slice(0, 5).map(r => `
    <li class="flex items-start gap-3 py-2 border-b border-slate-700/50 last:border-0">
      <span class="mt-1 w-2 h-2 rounded-full flex-shrink-0 ${r.tipo === 'Líquidos' ? 'bg-orange-400' : 'bg-sky-400'}"></span>
      <div>
        <p class="text-sm text-slate-200 font-medium">${r.tipo} – ${r.producto}</p>
        <p class="text-xs text-slate-500">${r.fecha} · ${fmt(r.total)}</p>
      </div>
    </li>`).join('');
}

document.addEventListener('DOMContentLoaded', loadDashboard);
