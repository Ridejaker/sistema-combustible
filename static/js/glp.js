/* ── glp.js ──
   FORMULA GLP:
   Monto Unitario = (Monto Facturado USD / Cantidad) * Tipo de Cambio
   Precio = Monto Unitario  (mismo resultado)
*/
const API = '/api/glp';
let editingId  = null;
let tipoCambio = 0;

// ── Calculo en tiempo real ────────────────────────────────
function recalc() {
  const montoUSD   = parseFloat(document.getElementById('monto_facturado').value) || 0;
  const cantidad   = parseFloat(document.getElementById('cantidad').value)        || 0;
  const tc         = parseFloat(document.getElementById('tipo_cambio').value)     || tipoCambio || 0;

  // Monto Unitario = (USD / cantidad) * TC
  const montoUnitario = cantidad > 0 ? (montoUSD / cantidad) * tc : 0;

  const fmt = v => v.toLocaleString('es-PE',{minimumFractionDigits:2,maximumFractionDigits:2});
  document.getElementById('monto_unitario_display').textContent = 'S/ ' + fmt(montoUnitario);
  document.getElementById('monto_unitario').value = montoUnitario.toFixed(6);

  // Actualizar formula visual en tiempo real
  const fMonto    = document.getElementById('f-monto');
  const fCantidad = document.getElementById('f-cantidad');
  const tcEl      = document.getElementById('tc-formula');
  if (fMonto)    fMonto.textContent    = montoUSD ? '$ ' + fmt(montoUSD)  : '$ —';
  if (fCantidad) fCantidad.textContent = cantidad  ? fmt(cantidad) 'gls' : '— kg';
  if (tcEl)      tcEl.textContent      = tc ? fmt(tc) : '—';
}

// ── Registros ─────────────────────────────────────────────
async function loadRecords() {
  const res  = await fetch(API);
  const data = await res.json();
  renderTable(data);
  updateCounters(data);
}

function updateCounters(data) {
  const hoy  = todayISO();
  const rows = data.filter(r => r.fecha === hoy);
  document.getElementById('cnt-registros').textContent = rows.length;
  document.getElementById('cnt-cantidad').textContent  =
    rows.reduce((s,r)=>s+r.cantidad,0).toFixed(2) 'gls';
  document.getElementById('cnt-soles').textContent =
    fmtPEN(rows.reduce((s,r)=>s+r.monto_soles,0));
}

function renderTable(data) {
  const n = (v, dec=2) => Number(v||0).toLocaleString('es-PE',{minimumFractionDigits:dec,maximumFractionDigits:dec});

  // ── Desktop table ──────────────────────────────────────
  const tbody = document.getElementById('records-tbody');
  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="14" class="text-center py-10 text-slate-500">Sin registros aun</td></tr>`;
  } else {
    tbody.innerHTML = data.map(r => `
      <tr class="tbl-row border-b border-slate-700/40 text-sm">
        <td class="px-3 py-2.5 text-white font-medium">${r.cliente}</td>
        <td class="px-3 py-2.5 text-white whitespace-nowrap">${r.nro_factura}</td>
        <td class="px-3 py-2.5 text-white whitespace-nowrap">${r.nro_guia}</td>
        <td class="px-3 py-2.5 text-right text-white font-semibold">${n(r.cantidad)}</td>
        <td class="px-3 py-2.5 text-right text-white font-semibold">$ ${n(r.monto_facturado)}</td>
        <td class="px-3 py-2.5 text-right text-sky-400 font-semibold">S/ ${n(r.monto_unitario)}</td>
        <td class="px-3 py-2.5 text-right text-slate-400 text-xs">${Number(r.tipo_cambio).toFixed(4)}</td>
        <td class="px-3 py-2.5">
          <span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-sky-900/60 text-sky-300">${r.producto}</span>
        </td>
        <td class="px-3 py-2.5 text-slate-400 whitespace-nowrap text-xs">${r.fecha}</td>
        <td class="px-3 py-2.5 text-slate-400 whitespace-nowrap text-xs">${r.planta}</td>
        <td class="px-3 py-2.5 text-slate-400 whitespace-nowrap text-xs">${r.proveedor}</td>
        <td class="px-3 py-2.5 text-slate-400 whitespace-nowrap text-xs">${r.chofer}</td>
        <td class="px-3 py-2.5 text-slate-400 text-xs whitespace-nowrap">${r.placa}</td>
        <td class="px-3 py-2.5">
          <div class="flex gap-1.5 justify-end">
            <button onclick="openEdit(${r.id})"
              class="px-2.5 py-1 rounded-lg bg-slate-600 hover:bg-slate-500 text-xs text-white transition">Editar</button>
            <button onclick="confirmDelete(${r.id})"
              class="px-2.5 py-1 rounded-lg bg-red-800/70 hover:bg-red-600 text-xs text-white transition">Borrar</button>
          </div>
        </td>
      </tr>`).join('');
  }

  // ── Mobile cards ───────────────────────────────────────
  const cardsContainer = document.getElementById('glp-cards-container');
  if (!cardsContainer) return;
  if (!data.length) {
    cardsContainer.innerHTML = '<p class="text-center text-slate-500 text-sm py-6">Sin registros aun</p>';
    return;
  }
  cardsContainer.innerHTML = data.map(r => `
    <div class="record-card">
      <div class="card-header">
        <div>
          <div class="card-title">${r.cliente}</div>
          <div class="card-sub">${r.fecha} · ${r.planta}</div>
        </div>
        <span class="card-badge">${r.producto}</span>
      </div>
      <div class="card-grid">
        <div class="card-item">
          <label>Factura</label>
          <span>${r.nro_factura}</span>
        </div>
        <div class="card-item">
          <label>Guia</label>
          <span>${r.nro_guia}</span>
        </div>
        <div class="card-item">
          <label>Total GLS</label>
          <span style="color:#e2e8f0;font-weight:700">${n(r.cantidad)} gls</span>
        </div>
        <div class="card-item">
          <label>Monto USD</label>
          <span style="color:#fbbf24;font-weight:700">$ ${n(r.monto_facturado)}</span>
        </div>
        <div class="card-item">
          <label>Mto. Unitario</label>
          <span style="color:#38bdf8;font-weight:700">S/ ${n(r.monto_unitario)}</span>
        </div>
        <div class="card-item">
          <label>T. Cambio</label>
          <span>${Number(r.tipo_cambio).toFixed(4)}</span>
        </div>
        <div class="card-item">
          <label>Proveedor</label>
          <span>${r.proveedor}</span>
        </div>
        <div class="card-item">
          <label>Chofer · Placa</label>
          <span>${r.chofer} / ${r.placa}</span>
        </div>
      </div>
      <div class="card-actions">
        <button onclick="openEdit(${r.id})"
          style="background:#334155;color:white;">✏️ Editar</button>
        <button onclick="confirmDelete(${r.id})"
          style="background:rgba(153,27,27,.6);color:#fca5a5;">🗑 Borrar</button>
      </div>
    </div>`).join('');
}

// ── Submit ────────────────────────────────────────────────
async function submitForm(e) {
  e.preventDefault();
  const g = id => document.getElementById(id)?.value || '';
  const required = ['planta','fecha','proveedor','chofer','placa',
                    'cliente','nro_factura','nro_guia','producto','cantidad',
                    'monto_facturado','tipo_cambio'];
  for (const f of required) {
    if (!g(f)) { showToast('Completa todos los campos obligatorios', false); return; }
  }

  const montoUSD   = parseFloat(g('monto_facturado')) || 0;
  const cantidad   = parseFloat(g('cantidad'))        || 0;
  const tc         = parseFloat(g('tipo_cambio'))     || 0;
  const montoUnit  = cantidad > 0 ? (montoUSD / cantidad) * tc : 0;
  const montoSoles = montoUSD * tc;  // total en soles para dashboard

  const payload = {
    planta: g('planta'), fecha: g('fecha'), proveedor: g('proveedor'),
    chofer: g('chofer'), placa: g('placa'), cliente: g('cliente'),
    nro_factura: g('nro_factura'), nro_guia: g('nro_guia'),
    flete_factura: parseFloat(g('flete_factura')) || 0,
    producto: g('producto'), cantidad: cantidad,
    monto_facturado: montoUSD,
    monto_unitario: montoUnit,
    tipo_cambio: tc,
    monto_soles: montoSoles,
    precio: montoUnit
  };

  const url    = editingId ? `${API}/${editingId}` : API;
  const method = editingId ? 'PUT' : 'POST';
  const res    = await fetch(url, {method, headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  if (res.ok) {
    showToast(editingId ? 'Registro actualizado' : 'Registro guardado');
    resetForm(); loadRecords();
  } else {
    showToast('Error al guardar', false);
  }
}

function resetForm() {
  editingId = null;
  document.getElementById('form-title').textContent = 'Nuevo Registro de Carga GLP';
  document.getElementById('btn-submit').textContent = 'Registrar Carga';
  document.getElementById('btn-cancel').classList.add('hidden');
  document.getElementById('glp-form').reset();
  document.getElementById('fecha').value = todayISO();
  if (tipoCambio) document.getElementById('tipo_cambio').value = tipoCambio;
  document.getElementById('monto_unitario_display').textContent = 'S/ 0.00';
  document.getElementById('monto_unitario').value = '0';
}

async function openEdit(id) {
  const res  = await fetch(API);
  const data = await res.json();
  const r    = data.find(x=>x.id===id);
  if (!r) return;
  editingId = id;
  document.getElementById('form-title').textContent = 'Editar Registro GLP';
  document.getElementById('btn-submit').textContent = 'Actualizar';
  document.getElementById('btn-cancel').classList.remove('hidden');
  const set = (fid,val) => { const el=document.getElementById(fid); if(el) el.value=val; };
  set('planta',r.planta); set('fecha',r.fecha); set('proveedor',r.proveedor);
  set('chofer',r.chofer); set('placa',r.placa); set('cliente',r.cliente);
  set('nro_factura',r.nro_factura); set('nro_guia',r.nro_guia);
  set('flete_factura',r.flete_factura); set('producto',r.producto);
  set('cantidad',r.cantidad); set('monto_facturado',r.monto_facturado);
  set('tipo_cambio',r.tipo_cambio);
  recalc();
  const formEl = document.getElementById('glp-form') || document.getElementById('liq-form');
  if (formEl) formEl.scrollIntoView({behavior:'smooth', block:'start'});
  window.scrollTo({top:0, behavior:'smooth'});
}

let deleteTarget = null;
function confirmDelete(id) { deleteTarget=id; document.getElementById('delete-modal').classList.remove('hidden'); }
async function doDelete() {
  if (!deleteTarget) return;
  await fetch(`${API}/${deleteTarget}`,{method:'DELETE'});
  document.getElementById('delete-modal').classList.add('hidden');
  showToast('Registro eliminado'); loadRecords(); deleteTarget=null;
}

document.addEventListener('DOMContentLoaded', async () => {
  fillSelect('planta',    PLANTAS_GLP,     'Seleccionar planta...');
  fillSelect('proveedor', PROVEEDORES_GLP, 'Seleccionar proveedor...');
  fillSelect('chofer',    CHOFERES,        'Seleccionar chofer...');
  fillSelect('placa',     PLACAS_GLP,      'Seleccionar placa...');
  fillSelect('producto',  PROD_GLP,        'Seleccionar producto...');
  document.getElementById('fecha').value = todayISO();

  // Cargar tipo de cambio en tiempo real
  tipoCambio = await fetchTipoCambio() || 0;
  setInterval(async () => {
    const tc = await fetchTipoCambio();
    if (tc) { tipoCambio = tc; recalc(); }
  }, 300000);

  ['monto_facturado','cantidad','tipo_cambio'].forEach(id=>{
    document.getElementById(id)?.addEventListener('input', recalc);
  });
  document.getElementById('glp-form').addEventListener('submit', submitForm);
  document.getElementById('btn-cancel').addEventListener('click', resetForm);
  document.getElementById('btn-delete-confirm').addEventListener('click', doDelete);
  document.getElementById('btn-delete-cancel').addEventListener('click', ()=>{
    document.getElementById('delete-modal').classList.add('hidden'); deleteTarget=null;
  });
  loadRecords();
});
