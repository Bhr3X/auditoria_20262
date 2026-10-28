// Runtime mínimo que substitui o do painel do Claude: carrega os JSON de data/,
// roda os cálculos (dash.calc) e redesenha a página (dash.onData).
(() => {
  const SRC = ['casos', 'provas', 'secoes', 'dims', 'norte', 'censo'];
  const DEF = { recorte: 'all' };
  const state = {}, calcs = {}, subs = [];
  let params = { ...DEF };
  SRC.forEach((id) => { state[id] = { status: 'loading', data: [], meta: [] }; });
  const okIn = (i) => state[i] && state[i].status === 'ok';
  function run() {
    Object.entries(calcs).forEach(([id, c]) => {
      if (okIn(id)) return;
      if (c.inputs.every(okIn)) {
        try { state[id] = { status: 'ok', data: c.fn(...c.inputs.map((i) => state[i].data)), meta: [] }; }
        catch (e) { state[id] = { status: 'error', data: [], message: String(e) }; console.error(id, e); }
      } else if (c.inputs.some((i) => state[i] && state[i].status === 'error')) state[id] = { status: 'error', data: [] };
    });
  }
  function notify() { run(); subs.forEach((fn) => { try { fn(); } catch (e) { console.error(e); } }); }
  window.dash = {
    data: (id) => state[id] || { status: 'missing', data: [] },
    onData: (fn) => { subs.push(fn); try { fn(); } catch (e) { console.error(e); } },
    calc: (id, o) => { calcs[id] = o; state[id] = { status: 'loading', data: [] }; run(); },
    loader: () => {},
    refresh: () => {},
    params: () => ({ ...params }),
    setParams: (p) => { params = { ...params, ...p }; notify(); },
    resetParams: () => { params = { ...DEF }; notify(); },
    setLink: (name) => { try { history.replaceState(null, '', '#' + name); } catch (e) { /* sem histórico */ } },
    colors: ['var(--cds-chart-1)', 'var(--cds-chart-2)', 'var(--cds-chart-3)', 'var(--cds-chart-4)', 'var(--cds-chart-5)', 'var(--cds-chart-6)', 'var(--cds-chart-7)', 'var(--cds-chart-8)'],
  };
  SRC.forEach((id) => fetch('data/' + id + '.json')
    .then((r) => { if (!r.ok) throw new Error(r.status + ' ' + r.statusText); return r.json(); })
    .then((d) => { state[id] = { status: 'ok', data: d, meta: [] }; notify(); })
    .catch((e) => { state[id] = { status: 'error', data: [], message: String(e) }; notify(); }));
  let t; let lastW = innerWidth;
  addEventListener('resize', () => { clearTimeout(t); t = setTimeout(() => { if (innerWidth !== lastW) { lastW = innerWidth; notify(); } }, 150); });
})();
