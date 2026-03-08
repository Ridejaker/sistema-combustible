/* ── shared.js ── listas y utilidades compartidas ── */

// ── LIQUIDOS ──────────────────────────────────────────────
const PLANTAS_LIQ    = ['CALLAO TERMINALES','CONCHAN','PAMPILLA','VALERO'];
const PROVEEDORES_LIQ= ['PETRO PERU','VALERO','GLOBAL PERU','IDROCARBUROS DEL MUNDO','REPSOL','SAC PERU'];
const PROD_LIQ       = ['Diesel B5 S50','Gasohol 90','Gasohol 95'];

// ── GLP ───────────────────────────────────────────────────
// SOL GAS / ZETAS / PRIMAX actuan como planta Y proveedor
const PLANTAS_GLP    = ['SOL GAS','ZETA','PRIMAX'];
const PROVEEDORES_GLP= ['SOL GAS','ZETA','PRIMAX'];
const PROD_GLP       = ['GLP Granel','GLP Envasado 10kg'];

// ── COMUNES ───────────────────────────────────────────────
const CHOFERES   = ['ANIBAL','JORGE LUIS','TOMAS','JOHON'];
const PLACAS_LIQ = [
  'TANQUE LIQUIDOS BCE-975 / TRACTO AMQ-867',
  'TANQUE LIQUIDOS F3C-977 / TRACTO ADR-921'
];
const PLACAS_GLP = [
  'TANQUE GLP BFH-980 / TRACTO ATU-934',
  'TANQUE GLP BKZ-978 / TRACTO V9M-851'
];

// ── Helpers ───────────────────────────────────────────────
function fmtPEN(n) {
  return 'S/ ' + Number(n).toLocaleString('es-PE',{minimumFractionDigits:2,maximumFractionDigits:2});
}
function fmtUSD(n) {
  return '$ ' + Number(n).toLocaleString('es-PE',{minimumFractionDigits:2,maximumFractionDigits:2});
}
function todayISO() { return new Date().toISOString().slice(0,10); }

function showToast(msg, ok=true) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl text-sm font-semibold shadow-2xl
    ${ok ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`;
  t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'), 3000);
}

function fillSelect(id, items, placeholder='Seleccionar...') {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = `<option value="">${placeholder}</option>` +
    items.map(i=>`<option value="${i}">${i}</option>`).join('');
}

async function fetchTipoCambio() {
  try {
    const res  = await fetch('/api/tipo_cambio');
    const data = await res.json();
    if (data.tipo_cambio) {
      const el = document.getElementById('tc-valor');
      if (el) el.textContent = data.tipo_cambio.toFixed(4);
      const inp = document.getElementById('tipo_cambio');
      if (inp && !inp.value) inp.value = data.tipo_cambio;
      return data.tipo_cambio;
    }
  } catch(e) {}
  return null;
}
