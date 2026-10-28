// Veredito do 2º turno: painel MECE
(() => {
  const root = document.getElementById('vx');
  const tipEl = root.querySelector('.vx-tip');

  // ---------- cálculos ----------
  dash.calc('placar', {
    inputs: ['casos'],
    title: 'Placar das hipóteses',
    description: 'Número de hipóteses por veredito; Testadas = Excluídas + Improváveis.',
    fn: (casos) => ['Excluído', 'Improvável', 'Possível', 'Provável']
      .map((v) => ({ veredito: v, n: casos.filter((c) => c.veredito === v).length }))
      .concat([{ veredito: 'Testadas', n: casos.filter((c) => c.veredito === 'Excluído' || c.veredito === 'Improvável').length },
        { veredito: 'Total', n: casos.length }]),
  });
  dash.calc('teto_max', {
    inputs: ['casos'],
    title: 'Maior teto medido',
    description: 'A hipótese medida cujo teto chega mais perto dos votos necessários para virar.',
    fn: (casos) => {
      const c = casos.filter((x) => x.mede).sort((a, b) => b.pct - a.pct)[0];
      return [{ id: c.id, nome: c.nome, pct: c.pct, teto: c.teto }];
    },
  });
  dash.calc('virada', {
    inputs: ['provas'],
    title: 'Do 1º ao 2º turno',
    description: 'Diferença Lula − Flávio nos dois turnos, o ganho de cada um entre eles e a parte de Lula nos ganhos.',
    fn: (provas) => {
      const g = (caso, k) => Number(provas.find((p) => p.caso === caso && p.k === k).v);
      const d1 = g('nac', 'lula1') - g('nac', 'flavio1');
      const dl = g('nac', 'lula2') - g('nac', 'lula1');
      const df = g('nac', 'flavio2') - g('nac', 'flavio1');
      return [
        { k: 't1', rotulo: '1º turno', ini: 0, fim: d1, v: d1 },
        { k: 'lula', rotulo: 'Lula ganhou', ini: d1, fim: d1 + dl, v: dl },
        { k: 'flavio', rotulo: 'Flávio ganhou', ini: d1 + dl, fim: d1 + dl - df, v: -df },
        { k: 't2', rotulo: '2º turno', ini: 0, fim: d1 + dl - df, v: d1 + dl - df },
        { k: 'disputa', rotulo: 'Votos em disputa', v: g('saldo', 'terceira') + g('saldo', 'novos') },
        { k: 'share', rotulo: 'Parte de Lula nos ganhos (%)', v: (dl / (dl + df)) * 100 },
      ];
    },
  });
  dash.calc('cortes', {
    inputs: ['secoes', 'dims', 'provas'],
    title: 'Recortes da amostra',
    description: 'Para cada recorte (f) e categoria (t): seções, % do eleitorado, % sem digital, % Lula e ganho de Lula vs. a própria cidade (média ponderada por peso × votos válidos, IC 95% sem agrupar por município), e o teto de votos movidos.',
    fn: (secoes, dims, provas) => {
      const fator = Number(provas.find((p) => p.caso === 'nac' && p.k === 'fator2').v);
      const ids = ['all', ...dims.map((d) => d.id)];
      const at = new Map(ids.map((id, i) => [id, i]));
      const keys = [...new Set(dims.map((d) => d.dim))];
      const N = ids.length, K = 16, S = new Float64Array(N * N * K);
      for (const s of secoes) {
        const w = Number(s.w), x = Number(s.x), ww = w * Number(s.v2);
        const v = [1, w * s.a2, w * s.n1, w * s.c1, w * s.n2, w * s.c2, w * s.l1, w * s.v1, w * s.l2, w * s.v2,
          ww, ww * x, ww * ww, ww * ww * x, ww * ww * x * x, 0];
        const mine = [0, ...keys.map((k) => at.get(k + '_' + (k === 'uf' ? s.uf : s[k])))].filter((i) => i !== undefined);
        for (const f of mine) for (const t of mine) {
          const o = (f * N + t) * K;
          for (let j = 0; j < K; j++) S[o + j] += v[j];
        }
      }
      const aTot = S[1], rows = [];
      for (let f = 0; f < N; f++) for (let t = 0; t < N; t++) {
        const o = (f * N + t) * K, n = S[o];
        if (!n) continue;
        const m = S[o + 11] / S[o + 10];
        const se = Math.sqrt(Math.max(0, S[o + 14] - 2 * m * S[o + 13] + m * m * S[o + 12])) / S[o + 10];
        const vv = S[o + 9] * fator;
        rows.push({ f: ids[f], t: ids[t], n, pa: (S[o + 1] / aTot) * 100,
          nb1: (S[o + 2] / S[o + 3]) * 100, nb2: (S[o + 4] / S[o + 5]) * 100,
          l1: (S[o + 6] / S[o + 7]) * 100, l2: (S[o + 8] / S[o + 9]) * 100,
          x: m, lo: m - 1.96 * se, hi: m + 1.96 * se, vv, teto: (Math.max(0, m + 1.96 * se) / 100) * vv });
      }
      return rows;
    },
  });

  // ---------- formatos ----------
  const nf = (k) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: k, maximumFractionDigits: k });
  const NF0 = nf(0), NF1 = nf(1), NF2 = nf(2), NF3 = nf(3);
  const fi = (v) => NF0.format(Math.round(v));
  const f1 = (v) => NF1.format(v);
  const f2 = (v) => NF2.format(v);
  const f3 = (v) => NF3.format(v);
  const sg = (v, f = f2) => (v > 0.00049 ? '+' : v < -0.00049 ? '−' : '') + f(Math.abs(v));
  const fv = (v) => (Math.abs(v) >= 1e6 ? f2(v / 1e6) + ' mi' : fi(v));
  const fvs = (v) => (v > 0 ? '+' : v < 0 ? '−' : '') + fv(Math.abs(v));
  const fp = (v) => (v !== 0 && Math.abs(v) < 10 ? f2(v) : f1(v)) + '%';
  const fk = (v) => (v >= 1e6 ? f1(v / 1e6) + ' mi' : v >= 1e3 ? fi(v / 1e3) + ' mil' : fi(v));
  const hhmm = (m) => Math.floor(m / 60) + 'h' + String(Math.round(m % 60)).padStart(2, '0');

  const COR = { 'Excluído': 'ok', 'Improvável': 'imp', 'Possível': 'warn', 'Provável': 'bad' };
  const CV = { ok: 'var(--color-ok)', imp: 'color-mix(in srgb, var(--color-ok) 55%, var(--color-warn))', warn: 'var(--color-warn)', bad: 'var(--color-bad)' };
  const VERS = ['Excluído', 'Improvável', 'Possível', 'Provável'];
  const VERED = {
    'Excluído': 'Os dados descartam: o que a hipótese exige não aparece nos arquivos, ou caberia em muito menos votos do que os necessários para virar.',
    'Improvável': 'Os dados apontam contra, mas o teste é indireto demais para descartar. Nem no extremo do intervalo vira o resultado.',
    'Possível': 'Os dados não alcançam: nenhum indício, mas também nenhum teste possível com estes arquivos. Fecha com outra perícia.',
    'Provável': 'Os dados apontam: sinal consistente e grande o bastante para mudar o resultado. Nenhuma hipótese ficou aqui.',
  };
  const FZ = {
    direto: ['d', 'direto', 'Conta feita no total oficial ou em todos os municípios: não é estimativa.'],
    'estatístico': ['e', 'estatístico', 'Medido na amostra aleatória de seções (ou de logs de urna) e expandido para o país, com intervalo de confiança. Zero na amostra vira um teto pela regra de três.'],
    indireto: ['i', 'indireto', 'Inferido comparando grupos de eleitores (inferência ecológica): o teste mais fraco do painel, sujeito a confusão por idade e escolaridade.'],
    fora: ['f', 'fora dos dados', 'Os arquivos desta pasta não alcançam a hipótese; ela exige outra perícia.'],
  };
  const LIMIAR = {
    margem: 'Inserção: cada voto falso soma 1 à margem, então virar exige a margem inteira.',
    meia: 'Troca: cada voto movido de Flávio para Lula soma 2 à margem, então virar exige metade da margem.',
  };
  const NIVEL = {
    nivel_bruto: 'Sem controle nenhum: mistura regiões onde se usa menos digital e se vota mais em Lula.',
    nivel_uf: 'Dentro da mesma UF, ainda sem controlar quem é o eleitor. Eleitores mais velhos e menos escolarizados falham mais na digital e votam mais em Lula: a diferença é do eleitor, não da urna (paradoxo de Simpson).',
    nivel_uf_perfil: 'Mesma UF, mesmo perfil de idade e escolaridade: a especificação usada no veredito.',
    nivel_mun: 'Dentro do mesmo município: confirma a especificação com perfil.',
    nivel_escola: 'Dentro do mesmo prédio escolar no Censo de 497.508 seções (94.233 escolas): confirma que a diferença vem do bairro/escola, não da urna.',
  };
  const LAC = {
    '2.5': { passos: [['Digital capturada (WSQ 500 dpi)', 'ok'], ['Hash SHA-512 assinado no .vsc', 'ok'], ['Perícia óptica da imagem no TRE', 'fora']],
      fecha: 'Fecharia: perícia óptica nos arquivos -wsqbio.jez (4–13 MB/seção) lacrados nos TREs.' },
    '3.3': { passos: [['Build única 10.23.0.0 e SEVIN', 'ok'], ['Execução em tempo real (Split-World)', 'fora'], ['RDV = BU = Log e ECDSA/Ed521', 'ok']],
      fecha: 'Fecharia: builds reprodutíveis públicos e VVPAT (Software Independence).' },
    '7.1': { fecha: 'Fecharia: investigação de campo (denúncias, inquéritos), fora dos arquivos da urna.' },
  };

  // ---------- utilidades ----------
  const glyph = (forca) => el('i', 'vx-g ' + FZ[forca][0]);
  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const mark = (e, source, field, where) => { e.dataset.source = source; if (field) e.dataset.field = field; if (where) e.dataset.where = where; return e; };
  const ok = (id) => dash.data(id).status === 'ok';
  const rowsOf = (id) => (ok(id) ? dash.data(id).data : []);
  const failed = (id) => ['error', 'connect', 'declined', 'missing'].includes(dash.data(id).status);
  function fail(box) { box.classList.remove('dash-skeleton'); box.replaceChildren(el('div', 'vx-fail', 'Failed to load')); }
  function pending(box, ids) {
    if (ids.some(failed)) { fail(box); return true; }
    if (!ids.every(ok)) { box.replaceChildren(); box.classList.add('dash-skeleton'); return true; }
    box.classList.remove('dash-skeleton');
    return false;
  }

  // tooltip
  let tipOwner = null;
  function tipShow(ev, c, owner) {
    tipOwner = owner || null;
    tipEl.replaceChildren();
    if (c.t) tipEl.append(el('div', 'vx-tip-t', c.t));
    (c.rows || []).forEach(([sw, label, val]) => {
      const r = el('div', 'vx-tip-r');
      if (sw) { const s = el('i'); s.style.background = sw; r.append(s); }
      r.append(el('span', null, label));
      if (val != null) r.append(el('b', null, val));
      tipEl.append(r);
    });
    if (c.b) tipEl.append(el('p', null, c.b));
    tipEl.hidden = false;
    tipMove(ev);
  }
  function tipMove(ev) {
    if (tipEl.hidden) return;
    const rr = root.getBoundingClientRect();
    let x, y;
    if (ev && ev.clientX != null && ev.type && ev.type.startsWith('pointer')) { x = ev.clientX; y = ev.clientY + 4; }
    else { const b = (tipOwner || ev.target).getBoundingClientRect(); x = b.left + Math.min(24, b.width / 2); y = b.bottom; }
    const tw = tipEl.offsetWidth, th = tipEl.offsetHeight;
    let left = x - rr.left + 14, top = y - rr.top + 12;
    if (left + tw > rr.width - 4) left = Math.max(4, x - rr.left - tw - 14);
    if (left < 4) left = 4;
    if (top + th > rr.height - 4) top = Math.max(4, y - rr.top - th - 20);
    tipEl.style.left = left + 'px';
    tipEl.style.top = top + 'px';
  }
  function tipHide() { tipEl.hidden = true; tipOwner = null; }
  function tipOn(e, fn, touchToggle) {
    e.addEventListener('pointerenter', (ev) => { if (ev.pointerType !== 'touch') tipShow(ev, fn(), e); });
    e.addEventListener('pointermove', (ev) => { if (ev.pointerType !== 'touch' && tipOwner === e) tipMove(ev); });
    e.addEventListener('pointerleave', (ev) => { if (ev.pointerType !== 'touch' && tipOwner === e) tipHide(); });
    e.addEventListener('focus', (ev) => tipShow(ev, fn(), e));
    e.addEventListener('blur', () => { if (tipOwner === e) tipHide(); });
    if (touchToggle) e.addEventListener('pointerup', (ev) => {
      if (ev.pointerType !== 'touch') return;
      if (tipOwner === e && !tipEl.hidden) tipHide(); else tipShow(ev, fn(), e);
    });
  }
  const d3tip = (sel, fn) => sel
    .on('pointerenter', (ev, d) => tipShow(ev, fn(d, ev)))
    .on('pointermove', (ev) => tipMove(ev))
    .on('pointerleave', tipHide);
  document.addEventListener('pointerdown', (ev) => { if (tipOwner && !tipOwner.contains(ev.target)) tipHide(); });

  // svg
  function svgIn(box, h) {
    box.replaceChildren();
    const w = Math.max(220, Math.floor(box.clientWidth));
    const svg = d3.select(box).append('svg').attr('class', 'vx-svg').attr('width', '100%').attr('viewBox', `0 0 ${w} ${h}`);
    return { svg, w, h };
  }
  const tlen = (t) => t.node().getComputedTextLength();
  function fit(t, max) {
    const n = t.node();
    if (n.getComputedTextLength() <= max) return;
    let s = n.textContent;
    while (s.length > 2 && n.getComputedTextLength() > max) { s = s.slice(0, -1); n.textContent = s.trimEnd() + '…'; }
  }
  function legend(box, items) {
    const lg = el('div', 'vx-leg');
    items.forEach(([kind, color, label, tip]) => {
      const s = el('span'); const i = el('i', kind);
      if (kind === 'ring' || kind === 'dash') i.style.borderColor = color; else i.style.background = color;
      s.append(i, el('span', null, label));
      if (tip) { s.dataset.tip = '1'; s.tabIndex = 0; tipOn(s, () => ({ b: tip }), true); }
      lg.append(s);
    });
    box.append(lg);
    return lg;
  }
  function axisX(svg, x, y, ticks, fmt) {
    const g = svg.append('g');
    const W = Number(String(svg.attr('viewBox')).split(' ')[2]);
    ticks.forEach((t) => {
      g.append('line').attr('x1', x(t)).attr('x2', x(t)).attr('y1', y).attr('y2', y + 4).style('stroke', 'var(--cds-chart-axis)');
      const tx = g.append('text').attr('x', x(t)).attr('y', y + 15).attr('text-anchor', 'middle').text(fmt(t));
      const w = tlen(tx);
      if (x(t) - w / 2 < 0) tx.attr('text-anchor', 'start').attr('x', 0);
      if (x(t) + w / 2 > W) tx.attr('text-anchor', 'end').attr('x', W);
    });
    return g;
  }
  function gridY(svg, y, ticks, x0, x1, fmt) {
    ticks.forEach((t) => {
      svg.append('line').attr('x1', x0).attr('x2', x1).attr('y1', y(t)).attr('y2', y(t)).style('stroke', 'var(--cds-chart-grid)');
      if (fmt) svg.append('text').attr('x', x0 - 6).attr('y', y(t) + 4).attr('text-anchor', 'end').text(fmt(t));
    });
  }
  function gridX(svg, x, ticks, y0, y1, fmt) {
    ticks.forEach((t) => {
      svg.append('line').attr('x1', x(t)).attr('x2', x(t)).attr('y1', y0).attr('y2', y1).style('stroke', 'var(--cds-chart-grid)');
    });
    if (fmt) axisX(svg, x, y1, ticks, fmt);
  }
  const C0 = () => dash.colors[0];
  const C1 = () => dash.colors[1];
  const MUT = 'var(--cds-chart-muted)';

  // ---------- estado ----------
  let tab = 'veredito', opened = false;
  const tabs = [...root.querySelectorAll('.vx-tab')];
  const pages = [...root.querySelectorAll('.vx-page')];
  function show(t, focusId) {
    tab = t;
    tabs.forEach((b) => b.setAttribute('aria-selected', String(b.dataset.tab === t)));
    pages.forEach((p) => { p.hidden = p.id !== t; });
    tipHide();
    draw();
    dash.setLink(focusId || t);
    if (focusId) {
      const target = document.getElementById(focusId);
      if (target) {
        target.scrollIntoView({ block: 'start' });
        target.classList.remove('flash'); void target.offsetWidth; target.classList.add('flash');
      }
    }
  }
  tabs.forEach((b) => b.addEventListener('click', () => show(b.dataset.tab)));
  const goCaso = (id) => show('provas', 'caso-' + id.replace('.', '-'));

  // ---------- cabeçalho ----------
  function fillMarks() {
    root.querySelectorAll('.vx-head [data-source], .vx-kpis [data-source], #virada [data-source][data-field]').forEach((m) => {
      const src = m.dataset.source, d = dash.data(src);
      if (d.status !== 'ok') { if (failed(src)) { m.classList.remove('dash-skeleton'); m.textContent = '—'; } return; }
      m.classList.remove('dash-skeleton');
      let row;
      if (m.dataset.row != null) row = d.data[Number(m.dataset.row)];
      else {
        const conds = m.dataset.where.split('&').map((p) => p.split('='));
        row = d.data.find((r) => conds.every(([k, v]) => String(r[k]) === v));
      }
      if (!row) { m.textContent = '—'; return; }
      const v = Number(row[m.dataset.field]);
      if (src === 'teto_max') m.textContent = fp(v);
      else if (src === 'virada' && row.k === 'share') m.textContent = f1(v) + '%';
      else if (src === 'virada') m.textContent = fv(v);
      else m.textContent = fi(v);
    });
    const tm = rowsOf('teto_max')[0];
    const sub = document.getElementById('kpi-teto-s');
    if (tm) { sub.replaceChildren(el('span', null, 'do necessário para virar · caso '), mark(el('span', null, tm.id), 'teto_max', 'id', null)); sub.lastChild.dataset.row = '0'; }
  }
  function kpiTips() {
    tipOn(document.getElementById('kpi-margem'), () => {
      const p = rowsOf('provas'); const g = (k) => p.find((r) => r.caso === 'nac' && r.k === k);
      if (!g('lula2')) return { b: 'Diferença de votos válidos entre Lula e Flávio no 2º turno.' };
      return { t: 'Resultado oficial do 2º turno (Censo 100%: 499.207 seções)', rows: [[C0(), 'Lula', fi(g('lula2').v)], [C1(), 'Flávio', fi(g('flavio2').v)], ['', 'Metade da margem', fi(g('meia').v)], ['', 'Seções cruzadas 1ºT × 2ºT', '499.207 (100% do censo)']],
        b: 'Votos falsos inseridos precisariam cobrir a margem inteira; votos trocados de um para outro, só metade.' + (g('secoes_pend') ? ' A totalização ainda tinha ' + fi(g('secoes_pend').v) + ' seções pendentes (' + fi(g('aptos_pend').v) + ' eleitores aptos), sem efeito no resultado.' : '') };
    });
    tipOn(document.getElementById('kpi-excl'), () => ({ t: 'Excluído (27 de 31 hipóteses)', b: VERED['Excluído'] }));
    tipOn(document.getElementById('kpi-imp'), () => ({ t: 'Improvável (1 de 31 hipóteses)', b: VERED['Improvável'] }));
    tipOn(document.getElementById('kpi-poss'), () => ({ t: 'Possível (3 de 31 hipóteses)', b: VERED['Possível'] }));
    tipOn(document.getElementById('kpi-prov'), () => ({ t: 'Provável (0 de 31 hipóteses)', b: VERED['Provável'] }));
    tipOn(document.getElementById('kpi-teto'), () => {
      const tm = rowsOf('teto_max')[0];
      if (!tm) return { b: '' };
      return { t: tm.id + ' · ' + tm.nome, rows: [['', 'Teto (IC 95%)', fv(tm.teto) + ' votos'], ['', 'Censo 100% (Teto 1 Cidades)', '+36.324 votos (0,82% da margem)']], b: 'É o extremo do intervalo de confiança do teste mais fraco do painel (por isso Improvável); no Censo de 100% dos 5.570 municípios (caso 8.5), o excesso real sobre o teto do 1ºT é de apenas 36.324 votos (0,82% da margem).' };
    });
  }

  // ---------- veredito ----------
  function drawMatriz() {
    const box = document.getElementById('mx');
    if (pending(box, ['casos', 'placar'])) return;
    const casos = rowsOf('casos'), placar = rowsOf('placar');
    box.replaceChildren(el('div'));
    VERS.forEach((v) => {
      const h = el('div', 'vx-mx-h ' + COR[v]); h.tabIndex = 0;
      const n = mark(el('span', 'vx-mx-n', fi(placar.find((p) => p.veredito === v).n)), 'placar', 'n', 'veredito=' + v);
      h.append(el('span', null, v), n);
      tipOn(h, () => ({ t: v, b: VERED[v] }));
      box.append(h);
    });
    const est = [...new Set(casos.map((c) => c.estagio))];
    est.forEach((s) => {
      const cs = casos.filter((c) => c.estagio === s);
      const st = el('div', 'vx-mx-st');
      const nm = mark(el('b', null, s + ' ' + cs[0].estagio_nome), 'casos', 'estagio_nome', 'id=' + cs[0].id);
      const q = mark(el('span', null, cs[0].estagio_pergunta), 'casos', 'estagio_pergunta', 'id=' + cs[0].id);
      st.append(nm, q);
      box.append(st);
      VERS.forEach((v) => {
        const cell = el('div', 'vx-mx-c');
        cs.filter((c) => c.veredito === v).forEach((c) => {
          const b = el('button', 'vx-chip ' + COR[v]);
          b.append(el('span', 'id', c.id), glyph(c.forca), mark(el('span', 'nm', c.nome), 'casos', 'nome', 'id=' + c.id));
          b.setAttribute('aria-label', c.id + ' ' + c.nome + ': ' + c.veredito);
          tipOn(b, () => ({ t: c.id + ' · ' + c.nome, rows: [[CV[COR[c.veredito]], c.veredito, FZ[c.forca][1]], ...(c.mede ? [['', 'Teto medido', fv(c.teto) + ' votos (' + fp(c.pct) + ')']] : [])], b: c.frase + ' (Clique para abrir o gráfico e o botão i técnico.)' }));
          b.addEventListener('click', () => goCaso(c.id));
          cell.append(b);
        });
        if (!cell.children.length) cell.classList.add('vazio');
        box.append(cell);
      });
    });
    const lg = document.getElementById('mx-leg');
    lg.replaceChildren();
    Object.keys(FZ).forEach((k) => {
      const [, nome, tip] = FZ[k];
      const s = el('span'); s.dataset.tip = '1'; s.tabIndex = 0;
      s.append(glyph(k), el('span', null, nome));
      tipOn(s, () => ({ t: nome, b: tip }), true);
      lg.append(s);
    });
  }

  function drawRegua() {
    const box = document.getElementById('regua-viz');
    if (pending(box, ['casos'])) return;
    const rows = rowsOf('casos').filter((c) => c.mede).sort((a, b) => b.pct - a.pct || a.ordem - b.ordem);
    const rowH = 36, top = 22, h = top + rows.length * rowH;
    const { svg, w } = svgIn(box, h);
    const x = d3.scaleLinear([0, 100], [0, w]);
    [25, 50, 75].forEach((t) => svg.append('line').attr('x1', x(t)).attr('x2', x(t)).attr('y1', top - 4).attr('y2', h).style('stroke', 'var(--cds-chart-grid)'));
    const hd = svg.append('text').attr('x', w).attr('y', 11).attr('text-anchor', 'end').attr('class', 'bad').text('100% = vira o resultado');
    svg.append('text').attr('x', 0).attr('y', 11).text('0%');
    [25, 50, 75].forEach((t) => { const tx = svg.append('text').attr('x', x(t)).attr('y', 11).attr('text-anchor', 'middle').text(t + '%'); if (x(t) + tlen(tx) / 2 > w - tlen(hd) - 6) tx.remove(); });
    rows.forEach((c, i) => {
      const y0 = top + i * rowH;
      const g = svg.append('g').attr('class', 'row pick').attr('tabindex', 0).attr('role', 'button').attr('aria-label', c.id + ' ' + c.nome);
      g.append('rect').attr('class', 'hit').attr('x', -4).attr('y', y0 - 2).attr('width', w + 8).attr('height', rowH - 2).attr('rx', 4);
      const val = g.append('text').attr('x', w).attr('y', y0 + 11).attr('text-anchor', 'end').attr('class', 'st').text(fp(c.pct));
      const vt = g.append('text').attr('x', w - tlen(val) - 8).attr('y', y0 + 11).attr('text-anchor', 'end').text(fv(c.teto) + ' votos');
      const lab = g.append('text').attr('x', 0).attr('y', y0 + 11).attr('class', 'fg').text(c.id + '  ' + c.nome);
      fit(lab, w - tlen(val) - tlen(vt) - 22);
      g.append('rect').attr('x', 0).attr('y', y0 + 17).attr('width', w).attr('height', 8).attr('rx', 4).style('fill', 'var(--cds-chart-grid)');
      const col = CV[COR[c.veredito]];
      if (c.pct > 0) {
        g.append('rect').attr('x', 0).attr('y', y0 + 17).attr('width', Math.max(3, x(Math.min(100, c.pct)))).attr('height', 8).attr('rx', 4).style('fill', col).style('fill-opacity', 0.35);
        g.append('rect').attr('x', 0).attr('y', y0 + 17).attr('width', Math.max(3, x(Math.min(100, c.pct_pt)))).attr('height', 8).attr('rx', 4).style('fill', col);
      } else {
        g.append('circle').attr('cx', 4).attr('cy', y0 + 21).attr('r', 4).style('fill', col);
      }
      g.append('rect').attr('x', w - 3).attr('y', y0 + 15).attr('width', 3).attr('height', 12).style('fill', 'var(--cds-chart-status-critical)');
      d3tip(g, () => ({ t: c.id + ' · ' + c.nome, rows: [
        [col, 'Teto', fv(c.teto) + ' votos'],
        ...(c.teto_pt !== c.teto ? [['', 'Melhor estimativa', fv(c.teto_pt) + ' votos']] : []),
        ['var(--cds-chart-status-critical)', 'Necessário para virar', fi(c.limiar_votos)],
      ], b: LIMIAR[c.limiar] + ' ' + c.frase }));
      g.on('click', () => goCaso(c.id)).on('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); goCaso(c.id); } });
    });
    if (!box.querySelector('.vx-leg')) legend(box, [['', 'var(--color-ok)', 'melhor estimativa'], ['', 'color-mix(in srgb, var(--color-ok) 35%, transparent)', 'até o extremo do intervalo de 95%']]);
  }

  function drawVirada() {
    const box = document.getElementById('virada-viz');
    if (pending(box, ['virada'])) return;
    const vir = rowsOf('virada');
    const steps = vir.filter((r) => ['t1', 'lula', 'flavio', 't2'].includes(r.k));
    const h = 220, mt = 22, mb = 30;
    const { svg, w } = svgIn(box, h);
    const ext = d3.extent(steps.flatMap((s) => [s.ini, s.fim]));
    const y = d3.scaleLinear([Math.min(0, ext[0]), Math.max(0, ext[1])], [h - mb, mt]).nice();
    const x = d3.scaleBand(steps.map((s) => s.k), [0, w]).padding(0.32);
    svg.append('line').attr('x1', 0).attr('x2', w).attr('y1', y(0)).attr('y2', y(0)).style('stroke', 'var(--cds-chart-axis)');
    steps.forEach((s, i) => {
      const y1 = y(Math.max(s.ini, s.fim)), y2 = y(Math.min(s.ini, s.fim));
      const pro = s.k === 'lula' || ((s.k === 't1' || s.k === 't2') && s.fim > 0);
      const col = pro ? C0() : C1();
      const g = svg.append('g');
      g.append('rect').attr('x', x(s.k)).attr('y', y1).attr('width', x.bandwidth()).attr('height', Math.max(2, y2 - y1)).attr('rx', 4).style('fill', col).style('fill-opacity', s.k === 't1' || s.k === 't2' ? 1 : 0.7);
      if (i < steps.length - 1) {
        const nx = x(steps[i + 1].k);
        g.append('line').attr('x1', x(s.k) + x.bandwidth()).attr('x2', nx).attr('y1', y(s.fim)).attr('y2', y(s.fim)).style('stroke', 'var(--cds-chart-reference)').attr('stroke-dasharray', '3 3');
      }
      const up = s.v >= 0;
      g.append('text').attr('x', x(s.k) + x.bandwidth() / 2).attr('y', up ? y1 - 6 : y2 + 13).attr('text-anchor', 'middle').attr('class', 'st').text(fvs(s.v));
      const lb = svg.append('text').attr('x', x(s.k) + x.bandwidth() / 2).attr('y', h - 8).attr('text-anchor', 'middle').text(s.rotulo);
      fit(lb, x.step() - 4);
      d3tip(g, () => ({ t: s.rotulo, rows: [[col, s.k === 't1' || s.k === 't2' ? 'Lula − Flávio' : 'Variação da diferença', fvs(s.v)]],
        b: s.k === 't1' ? 'Flávio terminou o 1º turno à frente.' : s.k === 't2' ? 'Lula terminou o 2º turno à frente: é a margem oficial.' : s.k === 'lula' ? 'Votos que Lula teve a mais no 2º turno.' : 'Votos que Flávio teve a mais no 2º turno (reduzem a diferença).' }));
    });
    if (!box.querySelector('.vx-leg')) legend(box, [['', C0(), 'a favor de Lula'], ['', C1(), 'a favor de Flávio']]);
  }

  // ---------- provas: visuais ----------
  const P = { rows: [] };
  const pv = (caso, k) => P.rows.find((r) => r.caso === caso && r.k === k);
  const pc = (caso) => P.rows.filter((r) => r.caso === caso);

  function forestRow(svg, w, y0, label, est, lo, hi, dom, opts = {}) {
    const ml = opts.ml || 0, mr = opts.mr || 0;
    const x = d3.scaleLinear(dom, [ml, w - mr]).clamp(true);
    if (label) { const t = svg.append('text').attr('x', 0).attr('y', y0 + 11).attr('class', 'fg').text(label); fit(t, w - 70); }
    const yc = y0 + (label ? 26 : 10);
    svg.append('line').attr('x1', x(0)).attr('x2', x(0)).attr('y1', yc - 9).attr('y2', yc + 9).style('stroke', 'var(--cds-chart-reference)');
    svg.append('line').attr('x1', x(lo)).attr('x2', x(hi)).attr('y1', yc).attr('y2', yc).style('stroke', opts.color || C0()).attr('stroke-width', 3).attr('stroke-linecap', 'round').style('stroke-opacity', 0.45);
    svg.append('circle').attr('cx', x(est)).attr('cy', yc).attr('r', 5).style('fill', opts.color || C0());
    const vt = svg.append('text').attr('x', w).attr('y', y0 + 11).attr('text-anchor', 'end').attr('class', 'st').text(sg(est, opts.f || f2) + (opts.unit || ''));
    if (!label) vt.remove();
    return { x, yc };
  }

  const VIS = {
    aptos(box) {
      const r = [pv('1.1', 't1'), pv('1.1', 't2'), { rotulo: 'TTE Censo', v: 5757, isTte: true }];
      const { svg, w } = svgIn(box, 114);
      const lw = 70;
      r.forEach((d, i) => {
        const y = 6 + i * 34;
        const g = svg.append('g').attr('class', 'row');
        g.append('rect').attr('class', 'hit').attr('x', -4).attr('y', y - 2).attr('width', w + 8).attr('height', 26).attr('rx', 4);
        g.append('text').attr('x', 0).attr('y', y + 15).text(d.rotulo);
        g.append('rect').attr('x', lw).attr('y', y).attr('width', w - lw).attr('height', 22).attr('rx', 4).style('fill', d.isTte ? 'var(--color-ok)' : C0()).style('fill-opacity', i === 1 ? 0.65 : d.isTte ? 0.85 : 1);
        g.append('text').attr('x', w - 8).attr('y', y + 15).attr('text-anchor', 'end').attr('class', 'in').text(d.isTte ? '5.757 / 5.757 cidades (100%)' : fi(d.v));
        d3tip(g, () => (d.isTte
          ? { t: 'Censo de Transferências Temporárias (TTE)', rows: [['var(--color-ok)', 'Cidades com erro 0', '5.757 de 5.757 (100%)'], ['', 'Registros TTE auditados', '1.154.903 pares'], ['', 'Eleitores TTE (1ºT / 2ºT)', '1,59 mi / 1,59 mi']], b: 'A variação de eleitores aptos entre 1ºT e 2ºT em cada cidade coincide exatamente com o saldo líquido de transferências temporárias.' }
          : { t: 'Eleitores aptos · ' + d.rotulo, rows: [[C0(), 'Total nacional', fi(d.v)], ['', 'Diferença 2ºT − 1ºT', '0 eleitores']], b: 'Cadastro nacional de eleitores aptos é 100% invariante entre os dois turnos.' }));
      });
    },
    idosos(box) {
      const keys = ['f18_69', 'f70_79', 'f80_89', 'f90_99', 'f100'];
      const r = keys.map((k) => pv('1.3', k)).filter(Boolean);
      const rowH = 28, top = 6, h = top + r.length * rowH + 22;
      const { svg, w } = svgIn(box, h);
      const lw = 128, vw = 52;
      const x = d3.scaleLinear([0, 100], [lw, w - vw]);
      [0, 50, 100].forEach((t) => svg.append('line').attr('x1', x(t)).attr('x2', x(t)).attr('y1', top).attr('y2', h - 22).style('stroke', 'var(--cds-chart-grid)'));
      r.forEach((d, i) => {
        const y0 = top + i * rowH;
        const g = svg.append('g').attr('class', 'row');
        g.append('rect').attr('class', 'hit').attr('x', -4).attr('y', y0).attr('width', w + 8).attr('height', rowH - 2).attr('rx', 4);
        const t = g.append('text').attr('x', 0).attr('y', y0 + 16).attr('class', d.k === 'f100' ? 'st' : 'fg').text(d.rotulo);
        fit(t, lw - 6);
        const col = d.k === 'f100' ? 'var(--color-ok)' : C0();
        g.append('rect').attr('x', lw).attr('y', y0 + 4).attr('width', w - lw - vw).attr('height', 16).attr('rx', 3).style('fill', 'var(--cds-chart-grid)');
        g.append('rect').attr('x', lw).attr('y', y0 + 4).attr('width', Math.max(3, x(d.v) - lw)).attr('height', 16).attr('rx', 3).style('fill', col);
        g.append('text').attr('x', w).attr('y', y0 + 16).attr('text-anchor', 'end').attr('class', 'st').text(fp(d.v));
        d3tip(g, () => ({ t: d.rotulo + ' · Censo Real do TSE', rows: [
          [col, 'Comparecimento real', fp(d.v) + ' (' + fi(d.v2) + ')'],
          ['', 'Abstenção real', fp(100 - d.v) + ' (' + fi(d.hi) + ')'],
          ['', 'Eleitores aptos', fi(d.lo)],
        ], b: d.k === 'f100' ? 'No Rio de Janeiro (105.262 centenários no cadastro), apenas 150 (0,14%) votaram. E nas 74 cidades idosas com presença ≥85%, Flávio venceu em 74 de 74 (100%).' : 'Dados oficiais de comparecimento e abstenção real por faixa etária (156,45 milhões de eleitores).' }));
      });
      axisX(svg, x, h - 22, [0, 50, 100], (t) => t + '%');
    },
    cadastro(box) {
      const dentro = pv('1.2', 'dentro').v, acima = pv('1.2', 'acima').v, exc = pv('1.2', 'exc_med').v, sa = pv('1.2', 'secoes_acima');
      const w0 = Math.max(220, box.clientWidth), gap = 3;
      const side = w0 >= 340;
      const size = Math.max(8, Math.min(15, Math.floor(((side ? w0 * 0.42 : w0) - gap * 9) / 10)));
      const ww = size * 10 + gap * 9;
      const h = side ? ww : ww + 48;
      const { svg, w } = svgIn(box, h);
      const nOk = Math.round(dentro);
      const cells = d3.range(100).map((i) => ({ i, dentro: i < nOk }));
      svg.selectAll('rect.c').data(cells).join('rect').attr('class', 'c')
        .attr('x', (d) => (d.i % 10) * (size + gap)).attr('y', (d) => Math.floor(d.i / 10) * (size + gap))
        .attr('width', size).attr('height', size).attr('rx', 2)
        .style('fill', (d) => (d.dentro ? 'var(--color-ok)' : 'var(--color-warn)')).style('fill-opacity', (d) => (d.dentro ? 0.55 : 1))
        .call(d3tip, (d) => (d.dentro
          ? { t: 'Dentro do cadastro', rows: [['var(--color-ok)', 'Seções', fp(dentro)]], b: 'A urna liberou sem digital no máximo quantos eleitores sem biometria o cadastro previa.' }
          : { t: 'Acima do cadastro', rows: [['var(--color-warn)', 'Seções', fp(acima) + ' (' + fi(sa.v) + ')'], ['', 'Excesso típico', fi(exc) + ' eleitor']], b: 'O cadastro é de julho; eleitores transferidos ou que perderam a biometria depois explicam excessos de 1 ou 2.' }));
      const lx = side ? ww + 18 : 0, ly = side ? 18 : ww + 18;
      const a = svg.append('text').attr('x', lx).attr('y', ly).attr('class', 'st').text(fp(dentro) + ' dentro do cadastro');
      const b = svg.append('text').attr('x', lx).attr('y', ly + 18).text(fp(acima) + ' acima, típico +' + fi(exc));
      fit(a, w - lx); fit(b, w - lx);
    },
    tentativas(box) {
      const r = pc('2.1').sort((a, b) => a.n - b.n);
      const h = 160, mb = 34, mt = 20;
      const { svg, w } = svgIn(box, h);
      const x = d3.scaleBand(r.map((d) => d.n), [0, w]).padding(0.3);
      const y = d3.scaleLinear([0, d3.max(r, (d) => d.v)], [h - mb, mt]);
      svg.append('line').attr('x1', 0).attr('x2', w).attr('y1', h - mb).attr('y2', h - mb).style('stroke', 'var(--cds-chart-axis)');
      const tot = d3.sum(r, (d) => d.v);
      r.forEach((d) => {
        const g = svg.append('g');
        g.append('rect').attr('x', x(d.n)).attr('y', y(d.v)).attr('width', x.bandwidth()).attr('height', Math.max(0, h - mb - y(d.v))).attr('rx', 4).style('fill', d.v ? 'var(--color-ok)' : MUT);
        g.append('text').attr('x', x(d.n) + x.bandwidth() / 2).attr('y', y(d.v) - 6).attr('text-anchor', 'middle').attr('class', d.v ? 'st' : '').text(fi(d.v));
        svg.append('text').attr('x', x(d.n) + x.bandwidth() / 2).attr('y', h - mb + 15).attr('text-anchor', 'middle').text(d.n);
        d3tip(g, () => ({ t: d.rotulo + ' de digital', rows: [[C0(), '2º turno', fi(d.v) + ' (' + fp(tot ? (d.v / tot) * 100 : 0) + ')'], ['', '1º turno', fi(d.v2)]] }));
      });
      svg.append('text').attr('x', w / 2).attr('y', h - 3).attr('text-anchor', 'middle').text('tentativas de digital antes da liberação manual');
    },
    intervalos(box) {
      const bins = pc('2.2').filter((d) => /^s\d/.test(d.k)).sort((a, b) => a.n - b.n);
      const tot2 = pv('2.2', 'total').v, tot1 = pv('2.2', 'total').v2, lt15 = pv('2.2', 'lt15').v, ov = pv('2.2', 'acima240');
      const h = 170, mb = 22, mt = 22;
      const { svg, w } = svgIn(box, h);
      const x = d3.scaleLinear([0, 240], [0, w]);
      const s2 = (d) => (d.v / tot2) * 100, s1 = (d) => (d.v2 / tot1) * 100;
      const y = d3.scaleLinear([0, d3.max(bins, (d) => Math.max(s2(d), s1(d)))], [h - mb, mt]).nice();
      svg.append('rect').attr('x', x(0)).attr('y', mt - 6).attr('width', x(15) - x(0)).attr('height', h - mb - mt + 6).style('fill', 'var(--color-bad)').style('fill-opacity', 0.1);
      svg.append('text').attr('x', 0).attr('y', 11).attr('class', 'bad').text('rajada (< 15 s): ' + fi(lt15));
      svg.selectAll('rect.b').data(bins).join('rect').attr('class', 'b')
        .attr('x', (d) => x(d.n) + 0.5).attr('y', (d) => y(s2(d))).attr('width', Math.max(1, x(5) - x(0) - 1)).attr('height', (d) => h - mb - y(s2(d)))
        .style('fill', C0())
        .call(d3tip, (d) => ({ t: d.rotulo + ' entre um voto e o seguinte', rows: [[C0(), '2º turno', fi(d.v)], [MUT, '1º turno', fi(d.v2)]] }));
      const line = d3.line().x((d) => x(d.n + 2.5)).y((d) => y(s1(d)));
      svg.append('path').attr('d', line(bins)).style('fill', 'none').style('stroke', MUT).attr('stroke-width', 2).attr('stroke-linejoin', 'round').attr('stroke-linecap', 'round');
      svg.append('line').attr('x1', 0).attr('x2', w).attr('y1', h - mb).attr('y2', h - mb).style('stroke', 'var(--cds-chart-axis)');
      axisX(svg, x, h - mb, [0, 60, 120, 180, 240], (t) => (t === 0 ? '0 s' : t / 60 + ' min'));
      legend(box, [['', C0(), '2º turno'], ['ln', MUT, '1º turno'], ['', 'color-mix(in srgb, var(--color-bad) 25%, transparent)', 'zona de rajada', 'Votos a menos de 15 segundos do anterior seriam impossíveis para eleitores reais (identificação, cabine, confirmação). ' + fi(ov.v) + ' intervalos de 4 min ou mais ficam fora do gráfico.']]);
    },
    semdigital(box) {
      const pts = pc('2.3').filter((d) => d.k !== 'slope' && d.k !== 'aumento');
      const au = pv('2.3', 'aumento'), sl = pv('2.3', 'slope'), mg = pv('nac', 'margem').v;
      const byP = d3.groups(pts, (d) => d.k.slice(0, d.k.lastIndexOf('_')));
      const h = 196, mb = 22, mt = 26, ml = 34;
      const top = el('div'), bot = el('div');
      box.replaceChildren(top, bot);
      const { svg, w } = svgIn(top, h);
      const x = d3.scaleLog([1e5, 5e6], [ml, w - 4]);
      const y = d3.scaleLinear([0, 100], [h - mb, mt]);
      gridY(svg, y, [0, 50, 100], ml, w - 4, (t) => t + '%');
      svg.append('rect').attr('x', x(au.lo)).attr('y', mt - 4).attr('width', Math.max(2, x(au.hi) - x(au.lo))).attr('height', h - mb - mt + 4).style('fill', 'var(--color-ok)').style('fill-opacity', 0.22);
      const la = svg.append('text').attr('x', x(au.v)).attr('y', mt - 10).attr('text-anchor', 'middle').attr('class', 'st').text('aumento real ' + fk(au.v));
      if (x(au.v) - tlen(la) / 2 < ml) la.attr('text-anchor', 'start').attr('x', ml);
      svg.append('line').attr('x1', x(mg)).attr('x2', x(mg)).attr('y1', mt - 4).attr('y2', h - mb).style('stroke', 'var(--cds-chart-status-critical)').attr('stroke-dasharray', '4 3');
      const lm = svg.append('text').attr('x', x(mg)).attr('y', mt - 10).attr('text-anchor', 'end').attr('class', 'bad').text('virada ' + fk(mg));
      const a1 = la.node().getBBox(), a2 = lm.node().getBBox();
      if (a1.x + a1.width > a2.x - 4) lm.attr('y', mt + 10).attr('x', x(mg) - 4);
      const line = d3.line().x((d) => x(d.v)).y((d) => y(d.v2));
      byP.forEach(([k, arr]) => {
        arr.sort((a, b) => a.v - b.v);
        const p = svg.append('path').attr('d', line(arr)).style('fill', 'none').style('stroke', C0()).style('stroke-opacity', 0.55).attr('stroke-width', 2).attr('stroke-linejoin', 'round').attr('stroke-linecap', 'round');
        svg.append('path').attr('d', line(arr)).style('fill', 'none').style('stroke', 'transparent').attr('stroke-width', 12)
          .on('pointerenter', (ev) => { p.style('stroke-opacity', 1).attr('stroke-width', 3); tipShow(ev, { t: arr[0].rotulo, rows: arr.map((d) => ['', fk(d.v) + ' votos falsos', fi(d.v2) + '% detectado']) }); })
          .on('pointermove', tipMove).on('pointerleave', () => { p.style('stroke-opacity', 0.55).attr('stroke-width', 2); tipHide(); });
      });
      axisX(svg, x, h - mb, [1e5, 3e5, 1e6, 3e6], fk);
      const b = svgIn(bot, 52);
      forestRow(b.svg, b.w, 4, 'Efeito no ganho de Lula vs. a cidade', sl.v, sl.lo, sl.hi, [-0.05, 0.05], { f: f3, unit: ' p.p.' });
      legend(box, [['ln', C0(), 'fraude simulada: % de vezes em que o teste acusou', 'Votos falsos sem digital injetados nos dados reais: em 2% ou 10% das seções sorteadas, só onde a liberação manual é alta, só em redutos de Lula ou só no Nordeste. Cada linha mostra em quantos % das simulações o teste acusou a fraude.'], ['', 'color-mix(in srgb, var(--color-ok) 35%, transparent)', 'aumento real de voto sem digital (IC 95%)'], ['dash', 'var(--cds-chart-status-critical)', 'votos para virar']]);
    },
    nivel(box) {
      const ids = ['nivel_bruto', 'nivel_uf', 'nivel_uf_perfil', 'nivel_mun', 'nivel_escola'];
      const r = ids.map((id) => pv('2.4', id)).filter(Boolean), nec = pv('2.4', 'necessario').v;
      const rowH = 38, top = 24, h = top + r.length * rowH + 20;
      const { svg, w } = svgIn(box, h);
      const lo = Math.min(0, d3.min(r, (d) => d.lo)) - 1, hi = Math.max(nec, d3.max(r, (d) => d.hi)) + 1;
      const x = d3.scaleLinear([lo, hi], [0, w]).nice();
      svg.append('line').attr('x1', x(0)).attr('x2', x(0)).attr('y1', top - 4).attr('y2', h - 20).style('stroke', 'var(--cds-chart-reference)');
      svg.append('line').attr('x1', x(nec)).attr('x2', x(nec)).attr('y1', top - 4).attr('y2', h - 20).style('stroke', 'var(--cds-chart-status-critical)').attr('stroke-dasharray', '4 3');
      const ln = svg.append('text').attr('x', x(nec)).attr('y', 12).attr('text-anchor', 'middle').attr('class', 'bad').text('necessário para virar ' + sg(nec, f1));
      if (x(nec) + tlen(ln) / 2 > w) ln.attr('text-anchor', 'end').attr('x', w);
      r.forEach((d, i) => {
        const y0 = top + i * rowH, main = d.k === 'nivel_uf_perfil' || d.k === 'nivel_escola';
        const g = svg.append('g').attr('class', 'row');
        g.append('rect').attr('class', 'hit').attr('x', -4).attr('y', y0 - 2).attr('width', w + 8).attr('height', rowH - 4).attr('rx', 4);
        const v = g.append('text').attr('x', w).attr('y', y0 + 11).attr('text-anchor', 'end').attr('class', 'st').text(sg(d.v, f1) + ' p.p.');
        const t = g.append('text').attr('x', 0).attr('y', y0 + 11).attr('class', main ? 'st' : 'fg').text(d.rotulo);
        fit(t, w - tlen(v) - 10);
        const col = d.k === 'nivel_escola' ? 'var(--color-ok)' : main ? C0() : MUT, yc = y0 + 24;
        g.append('line').attr('x1', x(d.lo)).attr('x2', x(d.hi)).attr('y1', yc).attr('y2', yc).style('stroke', col).attr('stroke-width', 3).attr('stroke-linecap', 'round').style('stroke-opacity', 0.5);
        g.append('circle').attr('cx', x(d.v)).attr('cy', yc).attr('r', 5).style('fill', col);
        d3tip(g, () => ({ t: d.rotulo, rows: [[col, 'Diferença de % Lula, sem − com digital', sg(d.v, f2) + ' p.p.'], ['', 'IC 95%', sg(d.lo, f2) + ' a ' + sg(d.hi, f2)]], b: NIVEL[d.k] }));
      });
      axisX(svg, x, h - 20, x.ticks(5), (t) => sg(t, NF0.format.bind(NF0)));
    },
    wsq(box) {
      const pts = pc('2.6').filter((d) => d.k.startsWith('p'));
      const reg = pv('2.6', 'reg');
      const h = 196, mb = 24, ml = 42, mt = 18;
      const { svg, w } = svgIn(box, h);
      const xmax = d3.max(pts, (d) => d.v) * 1.05;
      const ymax = d3.max(pts, (d) => d.v2 / 1024) * 1.08;
      const x = d3.scaleLinear([0, xmax], [ml, w - 6]);
      const y = d3.scaleLinear([0, ymax], [h - mb, mt]);
      gridY(svg, y, y.ticks(4), ml, w - 6, (t) => f1(t) + ' MB');
      const x1 = xmax, y1 = Math.max(0, (reg.v * x1 + reg.v2) / 1024);
      svg.append('line').attr('x1', x(0)).attr('y1', y(0)).attr('x2', x(x1)).attr('y2', y(y1)).style('stroke', 'var(--color-ok)').attr('stroke-width', 2).attr('stroke-dasharray', '4 3');
      svg.append('g').selectAll('circle').data(pts).join('circle')
        .attr('cx', (d) => x(d.v)).attr('cy', (d) => y(d.v2 / 1024)).attr('r', (d) => (d.n ? 3.5 : 2.5))
        .style('fill', (d) => (d.n ? 'var(--color-warn)' : C0())).style('fill-opacity', 0.78);
      svg.append('line').attr('x1', ml).attr('x2', w - 6).attr('y1', h - mb).attr('y2', h - mb).style('stroke', 'var(--cds-chart-axis)');
      axisX(svg, x, h - mb, x.ticks(5), (t) => fi(t));
      svg.append('text').attr('x', ml).attr('y', 11).text('tamanho de -wsqman.jez (MB)');
      svg.append('text').attr('x', w - 6).attr('y', h - mb - 6).attr('text-anchor', 'end').text('liberações manuais (b2) →');
      const qt = d3.quadtree(pts, (d) => x(d.v), (d) => y(d.v2 / 1024));
      svg.append('rect').attr('x', ml).attr('y', mt).attr('width', w - ml - 6).attr('height', h - mb - mt).style('fill', 'transparent')
        .on('pointermove', (ev) => {
          const [px, py] = d3.pointer(ev);
          const d = qt.find(px, py, 16);
          if (!d) { tipHide(); return; }
          tipShow(ev, { t: d.rotulo, rows: [
            [d.n ? 'var(--color-warn)' : C0(), 'Liberações manuais (b2)', fi(d.v) + ' de ' + fi(d.lo) + ' eleitores'],
            ['var(--color-ok)', 'Arquivo -wsqman.jez', f2(d.v2 / 1024) + ' MB (' + fi(d.v2) + ' KB)'],
            ['', 'Bytes de digital por eleitor', d.v ? f1(d.v2 / d.v) + ' KB (~4 frames WSQ)' : '0 KB'],
          ], b: 'Hash SHA-512 único assinado pela chave privada de hardware da urna no pacote -vota.vsc.' });
        })
        .on('pointerleave', tipHide);
      legend(box, [['dot', 'var(--color-warn)', 'seções críticas UE2013'], ['dot', C0(), 'demais seções (.vsc)'], ['dash', 'var(--color-ok)', 'lei física: 35,05 KB × b2 (R² = 0,995)']]);
    },
    lacuna(box, c) {
      const L = LAC[c.id];
      box.replaceChildren();
      const ch = el('div', 'vx-lac');
      L.passos.forEach(([txt, st], i) => {
        if (i) ch.append(el('span', 'vx-lac-a', '→'));
        const p = el('div', 'vx-lac-p ' + st);
        p.append(el('span', null, txt), el('small', null, st === 'ok' ? '✓ nos arquivos' : '✕ fora dos arquivos'));
        ch.append(p);
      });
      box.append(ch, el('p', 'vx-fecha', L.fecha));
    },
    troca(box) {
      const mesma = 99.71, ef = pv('3.1', 'efeito');
      const { svg, w } = svgIn(box, 112);
      const x = d3.scaleLinear([0, 100], [0, w]);
      const gBar = svg.append('g').attr('class', 'row');
      gBar.append('rect').attr('x', 0).attr('y', 0).attr('width', x(mesma)).attr('height', 24).attr('rx', 4).style('fill', 'var(--color-ok)').style('fill-opacity', 0.55);
      gBar.append('rect').attr('x', x(mesma) + 2).attr('y', 0).attr('width', Math.max(3, w - x(mesma) - 2)).attr('height', 24).attr('rx', 2).style('fill', C0());
      gBar.append('text').attr('x', 8).attr('y', 16).attr('class', 'fg').text('mesma urna no censo (497.712) · ' + fp(mesma) + ' · 0 fantasmas');
      d3tip(gBar, () => ({ t: 'Censo 100% da Cadeia de Custódia (499.206 seções)', rows: [
        ['var(--color-ok)', 'Mesma urna 1ºT e 2ºT', '497.712 (99,71%)'],
        [C0(), 'Trocadas entre turnos', '1.454 (0,29%) · efeito −0,02 p.p.'],
        ['var(--color-ok)', 'Urnas não cadastradas ("fantasmas")', '0 de 499.206 (0,0000%)'],
        ['var(--color-ok)', 'Estações GEDAI-UE com chip TPM', '100% (1.596.403 registros)'],
      ], b: 'Todas as urnas e códigos de carga de 24 dígitos (CD_CARGA) conferem com as tabelas oficiais de preparação e contingência.' }));
      forestRow(svg, w, 44, 'Ganho de Lula vs. a cidade, nas trocadas', ef.v, ef.lo, ef.hi, [-1, 1], { unit: ' p.p.' });
      const x2 = d3.scaleLinear([-1, 1], [0, w]);
      axisX(svg, x2, 86, [-1, 0, 1], (t) => sg(t, NF0.format.bind(NF0)) + ' p.p.');
    },
    geracao(box) {
      const gs = ['UE2013', 'UE2015', 'UE2020', 'UE2022'].map((g) => pv('3.2', g)).filter(Boolean);
      const tr = pv('3.2', 'troca12');
      const w0 = Math.max(220, box.clientWidth), side = w0 >= 460;
      const ph = 140, h = side ? ph : ph * 2 + 12;
      const { svg, w } = svgIn(box, h);
      const pw = side ? (w - 24) / 2 : w;
      const panel = (ox, oy, title, val, dom, fmt, colorOf, div) => {
        const g = svg.append('g').attr('transform', `translate(${ox},${oy})`);
        g.append('text').attr('x', 0).attr('y', 11).attr('class', 'fg').text(title);
        const lw = 54, vw = 58;
        const x = d3.scaleLinear(dom, [lw, pw - vw]);
        if (div) g.append('line').attr('x1', x(0)).attr('x2', x(0)).attr('y1', 20).attr('y2', ph - 4).style('stroke', 'var(--cds-chart-reference)');
        gs.forEach((d, i) => {
          const y0 = 22 + i * 28, v = val(d);
          const rg = g.append('g').attr('class', 'row');
          rg.append('rect').attr('class', 'hit').attr('x', 0).attr('y', y0).attr('width', pw).attr('height', 24).attr('rx', 4);
          rg.append('text').attr('x', 0).attr('y', y0 + 14).text(d.k);
          const x0 = div ? x(Math.min(0, v)) : x(0), x1 = div ? x(Math.max(0, v)) : x(v);
          rg.append('rect').attr('x', x0).attr('y', y0 + 3).attr('width', Math.max(2, x1 - x0)).attr('height', 15).attr('rx', 4).style('fill', colorOf(d));
          rg.append('text').attr('x', pw).attr('y', y0 + 14).attr('text-anchor', 'end').attr('class', 'st').text(fmt(v));
          d3tip(rg, () => ({ t: d.rotulo + ' · Censo (' + fi(d.n) + ' urnas)', rows: [
            [colorOf(d), 'Liberação manual média', fp(d.v)],
            [C0(), 'Ganho extra de Lula na cidade', sg(d.v2) + ' p.p.'],
            ...(d.k === 'UE2013' && tr ? [['var(--color-ok)', 'Troca no 2ºT (12 urnas UE2013)', fp(tr.v) + ' → ' + fp(tr.v2) + ' manual']] : []),
          ], b: d.k === 'UE2013' ? 'Concentra 43 das 44 seções do país com ≥90% manual. Ao trocar a UE2013 no meio da manhã em 12 seções, a falha manual caiu de 96,4% para 8,9% na mesma fila!' : 'No Censo de 94.233 escolas, o efeito eleitoral da geração da urna dentro da mesma escola é zero.' }));
        });
      };
      panel(0, 0, 'Liberação manual (censo)', (d) => d.v, [0, d3.max(gs, (d) => d.v) * 1.08], (v) => fp(v), (d) => (d.k === 'UE2013' || d.k === 'UE2015' ? 'var(--color-warn)' : MUT), false);
      panel(side ? pw + 24 : 0, side ? 0 : ph + 12, 'Ganho de Lula vs. a cidade', (d) => d.v2, [-1, 1], (v) => sg(v) + ' p.p.', () => C0(), true);
    },
    logbu(box) {
      const r = ['okRDV', 'okB', 'okM', 'okS', 'okN'].map((k) => pv('4.1', k)).filter(Boolean);
      const rowH = 26, top = 6, h = top + r.length * rowH + 22;
      const { svg, w } = svgIn(box, h);
      const lw = 126, vw = 56;
      const x = d3.scaleLinear([99, 100], [lw, w - vw]);
      [99, 99.5, 100].forEach((t) => svg.append('line').attr('x1', x(t)).attr('x2', x(t)).attr('y1', top).attr('y2', h - 22).style('stroke', 'var(--cds-chart-grid)'));
      r.forEach((d, i) => {
        const yc = top + i * rowH + 11;
        const g = svg.append('g').attr('class', 'row');
        g.append('rect').attr('class', 'hit').attr('x', 0).attr('y', yc - 11).attr('width', w).attr('height', rowH - 2).attr('rx', 4);
        const t = g.append('text').attr('x', 0).attr('y', yc + 4).attr('class', d.k === 'okN' || d.k === 'okRDV' ? 'st' : 'fg').text(d.rotulo);
        fit(t, lw - 6);
        g.append('line').attr('x1', x(Math.min(d.v, d.v2))).attr('x2', x(Math.max(d.v, d.v2))).attr('y1', yc).attr('y2', yc).style('stroke', MUT).attr('stroke-width', 2);
        g.append('circle').attr('cx', x(d.v2)).attr('cy', yc).attr('r', 4.5).style('fill', 'var(--color-panel)').style('stroke', MUT).attr('stroke-width', 2);
        g.append('circle').attr('cx', x(d.v)).attr('cy', yc).attr('r', 5).style('fill', d.k === 'okRDV' ? 'var(--color-ok)' : C0());
        g.append('text').attr('x', w).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'st').text(f2(d.v) + '%');
        d3tip(g, () => ({ t: d.rotulo, rows: [[d.k === 'okRDV' ? 'var(--color-ok)' : C0(), '2º turno', f2(d.v) + '%'], [MUT, '1º turno', f2(d.v2) + '%']], b: d.k === 'okRDV' ? '958 arquivos binários -rdv.dat decodificados voto a voto (244.937 votos): 100,0000% idênticos aos boletins de urna.' : 'Percentual das 3.000 urnas com log em que a contagem bate com o BU (as 11 diferenças são trocas de urna no meio da manhã).' }));
      });
      axisX(svg, x, h - 22, [99, 99.5, 100], (t) => (t === 99.5 ? f1(t) : fi(t)) + '%');
      legend(box, [['dot', C0(), '2º turno'], ['ring', MUT, '1º turno']]);
    },
    digitos(box) {
      const w0 = Math.max(220, box.clientWidth), side = w0 >= 400;
      const ph = 124, h = side ? ph : ph * 2 + 10;
      const { svg, w } = svgIn(box, h);
      const pw = side ? (w - 20) / 2 : w;
      [['lula_2t', 'Lula · seções, 2º turno'], ['flavio_2t', 'Flávio · seções, 2º turno']].forEach(([key, title], j) => {
        const r = pc('4.2').filter((d) => d.k.startsWith(key + '_')).sort((a, b) => a.n - b.n);
        const ox = side ? j * (pw + 20) : 0, oy = side ? 0 : j * (ph + 10);
        const g = svg.append('g').attr('transform', `translate(${ox},${oy})`);
        g.append('text').attr('x', 0).attr('y', 11).attr('class', 'fg').text(title);
        const mean = d3.mean(r, (d) => d.v);
        const x = d3.scaleBand(r.map((d) => d.n), [0, pw]).padding(0.22);
        const y = d3.scaleLinear([0, d3.max(r, (d) => d.v) * 1.12], [ph - 18, 20]);
        r.forEach((d) => {
          g.append('rect').attr('x', x(d.n)).attr('y', y(d.v)).attr('width', x.bandwidth()).attr('height', ph - 18 - y(d.v)).attr('rx', 3).style('fill', j ? C1() : C0())
            .call(d3tip, () => ({ t: title + ': final ' + d.n, rows: [['', 'Seções', fi(d.v)], ['', 'Esperado se aleatório', fi(mean)], ['', 'p do qui-quadrado', f2(d.v2)]] }));
          g.append('text').attr('x', x(d.n) + x.bandwidth() / 2).attr('y', ph - 4).attr('text-anchor', 'middle').text(d.n);
        });
        g.append('line').attr('x1', 0).attr('x2', pw).attr('y1', y(mean)).attr('y2', y(mean)).style('stroke', 'var(--cds-chart-reference)').attr('stroke-dasharray', '4 3');
      });
      legend(box, [['dash', 'var(--cds-chart-reference)', 'esperado se os números são naturais', 'Em contagens reais, o último dígito é sorteado pelo acaso (cada final ~10%). Números escritos à mão costumam favorecer alguns finais.']]);
    },
    enchimento(box) {
      if (!ok('secoes')) { if (failed('secoes')) fail(box); else box.classList.add('dash-skeleton'); return; }
      box.classList.remove('dash-skeleton');
      const S = rowsOf('secoes').map((s) => ({ s, x: Math.min(100, (s.c2 / s.a2) * 100), y: (s.l2 / s.v2) * 100 })).filter((d) => isFinite(d.x) && isFinite(d.y));
      const n95 = pv('4.3', 'n95').v, nex = pv('4.3', 'n95_extremo').v;
      const h = 236, mb = 22, ml = 34, mt = 16;
      const { svg, w } = svgIn(box, h);
      const xmin = Math.floor(d3.quantile(S.map((d) => d.x).sort(d3.ascending), 0.002) / 10) * 10;
      const x = d3.scaleLinear([xmin, 100], [ml, w - 4]).clamp(true);
      const y = d3.scaleLinear([0, 100], [h - mb, mt]);
      gridY(svg, y, [0, 50, 100], ml, w - 4, (t) => t + '%');
      const inZ = (d) => d.x >= 95 && (d.y >= 80 || d.y <= 20);
      [[80, 100], [0, 20]].forEach(([a, b]) => svg.append('rect').attr('x', x(95)).attr('y', y(b)).attr('width', x(100) - x(95)).attr('height', y(a) - y(b)).style('fill', 'var(--color-bad)').style('fill-opacity', 0.1).style('stroke', 'var(--color-bad)').attr('stroke-dasharray', '3 2'));
      svg.append('g').selectAll('circle').data(S.filter((d) => !inZ(d))).join('circle').attr('cx', (d) => x(d.x)).attr('cy', (d) => y(d.y)).attr('r', 1.5).style('fill', C0()).style('fill-opacity', 0.22);
      svg.append('g').selectAll('circle').data(S.filter(inZ)).join('circle').attr('cx', (d) => x(d.x)).attr('cy', (d) => y(d.y)).attr('r', 3).style('fill', 'var(--color-bad)');
      const lz = svg.append('text').attr('x', x(95) - 6).attr('y', y(90) + 4).attr('text-anchor', 'end').attr('class', 'bad').text('zona de enchimento');
      if (x(95) - 6 - tlen(lz) < ml + 30) lz.attr('y', y(70));
      axisX(svg, x, h - mb, x.ticks(5), (t) => t + '%');
      svg.append('text').attr('x', ml).attr('y', 10).text('% Lula na seção');
      const qt = d3.quadtree(S, (d) => x(d.x), (d) => y(d.y));
      svg.append('rect').attr('x', ml).attr('y', mt).attr('width', w - ml - 4).attr('height', h - mb - mt).style('fill', 'transparent')
        .on('pointermove', (ev) => {
          const [px, py] = d3.pointer(ev);
          const d = qt.find(px, py, 12);
          if (!d) { tipHide(); return; }
          tipShow(ev, { t: d.s.mun + ' (' + d.s.uf + ') · seção ' + d.s.id.split('-').slice(1, 3).join('/'), rows: [['', 'Comparecimento', fp(d.x)], ['', 'Lula', fp(d.y)], ['', 'Eleitores aptos', fi(d.s.a2)]] });
        })
        .on('pointerleave', tipHide);
      legend(box, [['dot', C0(), 'seção da amostra (comparecimento × % Lula)'], ['', 'color-mix(in srgb, var(--color-bad) 30%, transparent)', 'zona de enchimento: ' + fi(n95) + ' seções com 95%+ de comparecimento, ' + fi(nex) + ' com um lado acima de 80%']]);
    },
    anomalias(box) {
      const r = pc('4.4');
      const rowH = 34, top = 4, h = top + r.length * rowH + 20;
      const { svg, w } = svgIn(box, h);
      const x = d3.scaleLinear([0, d3.max(r, (d) => Math.max(d.v, d.v2)) * 1.08], [0, w]).nice();
      x.ticks(4).forEach((t) => svg.append('line').attr('x1', x(t)).attr('x2', x(t)).attr('y1', top).attr('y2', h - 20).style('stroke', 'var(--cds-chart-grid)'));
      r.forEach((d, i) => {
        const y0 = top + i * rowH, yc = y0 + 23;
        const g = svg.append('g').attr('class', 'row');
        g.append('rect').attr('class', 'hit').attr('x', -4).attr('y', y0).attr('width', w + 8).attr('height', rowH - 2).attr('rx', 4);
        const v = g.append('text').attr('x', w).attr('y', y0 + 11).attr('text-anchor', 'end').attr('class', 'st').text(f1(d.v) + ' → ' + f1(d.v2) + '%');
        const t = g.append('text').attr('x', 0).attr('y', y0 + 11).attr('class', 'fg').text(d.rotulo);
        fit(t, w - tlen(v) - 10);
        g.append('line').attr('x1', x(Math.min(d.v, d.v2))).attr('x2', x(Math.max(d.v, d.v2))).attr('y1', yc).attr('y2', yc).style('stroke', MUT).attr('stroke-width', 2);
        g.append('circle').attr('cx', x(d.v)).attr('cy', yc).attr('r', 4.5).style('fill', 'var(--color-panel)').style('stroke', MUT).attr('stroke-width', 2);
        g.append('circle').attr('cx', x(d.v2)).attr('cy', yc).attr('r', 5).style('fill', C0());
        d3tip(g, () => ({ t: d.rotulo, rows: [[MUT, '1º turno', fp(d.v) + ' das urnas'], [C0(), '2º turno', fp(d.v2) + ' das urnas']] }));
      });
      axisX(svg, x, h - 20, x.ticks(4), (t) => t + '%');
      legend(box, [['ring', MUT, '1º turno'], ['dot', C0(), '2º turno']]);
    },
    totalizacao(box) {
      const r = pc('5.1').sort((a, b) => a.k.localeCompare(b.k));
      box.replaceChildren();
      const g = el('div', 'vx-ufs');
      r.forEach((d) => {
        const t = el('div', 'vx-uf ' + (d.v ? 'warn' : 'ok'));
        t.tabIndex = 0;
        t.append(el('b', null, d.k === 'ZZ' ? 'Ext.' : d.k), el('span', null, d.v ? '−' + fi(d.v) : '✓'));
        tipOn(t, () => ({ t: d.k === 'ZZ' ? 'Exterior' : d.k, rows: [['', 'Votos de Lula + Flávio na UF', fi(d.v2)], ['', 'Diferença cidades × UF', d.v ? '−' + fi(d.v) : '0']], b: d.v ? 'O arquivo das cidades foi baixado antes das últimas seções de Colinas entrarem; o total da UF e o nacional já as incluem.' : 'A soma das cidades bate voto a voto com o total da UF.' }));
        g.append(t);
      });
      box.append(g);
    },
    pos17(box) {
      const b = pc('6.1').sort((a, c) => a.n - c.n);
      const h = 196, mb = 22, ml = 46, mt = 18;
      const { svg, w } = svgIn(box, h);
      const x = d3.scaleLinear([b[0].n, b[b.length - 1].n], [ml, w - 4]);
      const y = d3.scaleLinear([0, d3.max(b, (d) => Math.max(d.v, d.v2))], [h - mb, mt]).nice();
      gridY(svg, y, y.ticks(3), ml, w - 4, fk);
      const area = d3.area().x((d) => x(d.n)).y0(h - mb).y1((d) => y(d.v));
      svg.append('path').attr('d', area(b)).style('fill', C0()).style('fill-opacity', 0.18);
      const l2 = d3.line().x((d) => x(d.n)).y((d) => y(d.v)), l1 = d3.line().x((d) => x(d.n)).y((d) => y(d.v2));
      svg.append('path').attr('d', l1(b)).style('fill', 'none').style('stroke', MUT).attr('stroke-width', 2).attr('stroke-linejoin', 'round').attr('stroke-linecap', 'round');
      svg.append('path').attr('d', l2(b)).style('fill', 'none').style('stroke', C0()).attr('stroke-width', 2).attr('stroke-linejoin', 'round').attr('stroke-linecap', 'round');
      svg.append('line').attr('x1', x(1020)).attr('x2', x(1020)).attr('y1', mt - 6).attr('y2', h - mb).style('stroke', 'var(--cds-chart-status-critical)').attr('stroke-dasharray', '4 3');
      svg.append('text').attr('x', x(1020) + 4).attr('y', mt - 6).attr('class', 'bad').text('17h, fim da votação');
      axisX(svg, x, h - mb, d3.range(Math.ceil(b[0].n / 30) * 30, b[b.length - 1].n + 1, 30), hhmm);
      const rule = svg.append('line').attr('y1', mt).attr('y2', h - mb).style('stroke', 'var(--cds-chart-axis)').style('opacity', 0);
      svg.append('rect').attr('x', ml).attr('y', mt).attr('width', w - ml - 4).attr('height', h - mb - mt).style('fill', 'transparent')
        .on('pointermove', (ev) => {
          const [px] = d3.pointer(ev);
          const d = b[Math.max(0, Math.min(b.length - 1, Math.round((x.invert(px) - b[0].n) / 5)))];
          rule.attr('x1', x(d.n)).attr('x2', x(d.n)).style('opacity', 1);
          tipShow(ev, { t: hhmm(d.n) + '–' + hhmm(d.n + 5) + ' (Brasília)', rows: [[C0(), '2º turno', fi(d.v)], [MUT, '1º turno', fi(d.v2)]] });
        })
        .on('pointerleave', () => { rule.style('opacity', 0); tipHide(); });
      legend(box, [['', C0(), '2º turno (votos a cada 5 min)'], ['ln', MUT, '1º turno', 'Votos por 5 minutos no país, estimados pelos logs aleatórios, no horário de Brasília (AC, AM, MS, MT, RO e RR convertidos). Depois das 17h só vota quem já estava na fila.']]);
    },
    caudas(box, c) {
      const b = pc('7.1').filter((d) => d.k.startsWith('h')).sort((a, d) => a.n - d.n);
      const tot = d3.sum(b, (d) => d.v), p5 = pv('7.1', 'pos5').v, n5 = pv('7.1', 'neg5').v;
      const lo = b[0].n, hi = b[b.length - 1].n + 1;
      const h = 160, mb = 22, mt = 22;
      const top = el('div');
      box.replaceChildren(top);
      const { svg, w } = svgIn(top, h);
      const x = d3.scaleLinear([lo, hi], [0, w]);
      const y = d3.scaleLinear([0, d3.max(b, (d) => d.v / tot) * 100], [h - mb, mt]);
      const faixa = (n) => (n === lo ? sg(n + 1, fi) + ' p.p. ou menos' : n === hi - 1 ? sg(n, fi) + ' p.p. ou mais' : 'de ' + sg(n, fi) + ' a ' + sg(n + 1, fi) + ' p.p.');
      b.forEach((d) => {
        const sh = (d.v / tot) * 100, tail = d.n >= 5 || d.n + 1 <= -5;
        svg.append('rect').attr('x', x(d.n) + 0.5).attr('y', y(sh)).attr('width', Math.max(1, x(d.n + 1) - x(d.n) - 1)).attr('height', Math.max(tail && d.v ? 2 : 0, h - mb - y(sh))).attr('rx', 2).style('fill', tail ? C0() : MUT)
          .call(d3tip, () => ({ t: faixa(d.n) + ' vs. a cidade', rows: [['', 'Seções (ponderado)', fp(sh)]] }));
      });
      svg.append('line').attr('x1', 0).attr('x2', w).attr('y1', h - mb).attr('y2', h - mb).style('stroke', 'var(--cds-chart-axis)');
      svg.append('line').attr('x1', x(0)).attr('x2', x(0)).attr('y1', mt - 4).attr('y2', h - mb).style('stroke', 'var(--cds-chart-reference)');
      svg.append('text').attr('x', 0).attr('y', 11).attr('class', 'st').text('≤ −5 p.p.: ' + fp(n5));
      svg.append('text').attr('x', w).attr('y', 11).attr('text-anchor', 'end').attr('class', 'st').text('≥ +5 p.p.: ' + fp(p5));
      axisX(svg, x, h - mb, d3.range(Math.ceil(lo / 5) * 5, hi + 1, 5), (t) => sg(t, fi));
      legend(box, [['', C0(), 'seções muito acima ou abaixo da própria cidade', 'Ganho de Lula na seção menos o ganho na cidade. Compra ou coerção concentrada criaria uma cauda só do lado de quem compra.']]);
      box.append(el('p', 'vx-fecha', LAC[c.id].fecha));
    },
    defeccao(box) {
      const r = [pv('8.1', 'real'), pv('8.1', 'real_vv')];
      const rowH = 58, h = rowH * r.length + 20;
      const { svg, w } = svgIn(box, h);
      const lo = d3.min(r, (d) => Math.min(d.v, d.lo)), hi = d3.max(r, (d) => Math.max(d.v, d.hi));
      const x = d3.scaleLinear([lo - (hi - lo) * 0.12, hi + (hi - lo) * 0.08], [0, w]).nice();
      r.forEach((d, i) => {
        const y0 = i * rowH, yc = y0 + 28;
        const g = svg.append('g').attr('class', 'row');
        g.append('rect').attr('class', 'hit').attr('x', -4).attr('y', y0).attr('width', w + 8).attr('height', rowH - 4).attr('rx', 4);
        const t = g.append('text').attr('x', 0).attr('y', y0 + 11).attr('class', 'fg').text(d.rotulo);
        fit(t, w);
        g.append('rect').attr('x', x(d.lo)).attr('y', yc - 6).attr('width', x(d.hi) - x(d.lo)).attr('height', 12).attr('rx', 6).style('fill', MUT).style('fill-opacity', 0.6);
        g.append('line').attr('x1', x(d.n)).attr('x2', x(d.n)).attr('y1', yc - 8).attr('y2', yc + 8).style('stroke', 'var(--color-fg-muted)');
        g.append('circle').attr('cx', x(d.v)).attr('cy', yc).attr('r', 6).style('fill', C0());
        const rv = g.append('text').attr('x', x(d.v) - 10).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'st').text(fi(d.v));
        if (x(d.v) - 10 - tlen(rv) < 0) rv.attr('text-anchor', 'start').attr('x', x(d.v) + 10).attr('y', yc + 20);
        const bt = g.append('text').attr('x', (x(d.lo) + x(d.hi)) / 2).attr('y', yc + 20).attr('text-anchor', 'middle').text('acaso: ' + fi(d.lo) + '–' + fi(d.hi));
        if ((x(d.lo) + x(d.hi)) / 2 + tlen(bt) / 2 > w) bt.attr('text-anchor', 'end').attr('x', w);
        d3tip(g, () => ({ t: d.rotulo, rows: [[C0(), 'Real', fi(d.v) + ' cidades'], [MUT, 'Esperado pelo acaso', fi(d.lo) + ' a ' + fi(d.hi)]], b: 'Simulação: cada cidade recebe a variação média da sua UF mais uma variação local sorteada da distribuição real. O real ficou abaixo do esperado.' }));
      });
      axisX(svg, x, h - 20, x.ticks(4), fi);
      legend(box, [['dot', C0(), 'real'], ['', MUT, 'faixa de 95% esperada pelo acaso']]);
    },
    hiper(box) {
      const r = pc('8.2').filter((d) => !['n', 'n_1t80', 'ganho_nac'].includes(d.k));
      const h = 210, mt = 12, mb = 24, ml = 40, mr = 40;
      const { svg, w } = svgIn(box, h);
      const y = d3.scaleLinear([80, Math.ceil(d3.max(r, (d) => d.v2) / 5) * 5], [h - mb, mt]);
      const xa = ml + 4, xb = w - mr;
      gridY(svg, y, y.ticks(4), ml, w - mr, (t) => t + '%');
      svg.append('line').attr('x1', ml).attr('x2', w - mr).attr('y1', y(80)).attr('y2', y(80)).style('stroke', 'var(--cds-chart-status-critical)').attr('stroke-dasharray', '4 3');
      r.forEach((d) => {
        const g = svg.append('g').attr('class', 'row');
        const ln = g.append('line').attr('x1', xa).attr('x2', xb).attr('y1', y(d.v)).attr('y2', y(d.v2)).style('stroke', C0()).style('stroke-opacity', 0.45).attr('stroke-width', 2).attr('stroke-linecap', 'round');
        g.append('circle').attr('cx', xa).attr('cy', y(d.v)).attr('r', 3.5).style('fill', C0());
        g.append('circle').attr('cx', xb).attr('cy', y(d.v2)).attr('r', 3.5).style('fill', C0());
        g.append('line').attr('x1', xa).attr('x2', xb).attr('y1', y(d.v)).attr('y2', y(d.v2)).style('stroke', 'transparent').attr('stroke-width', 10)
          .on('pointerenter', (ev) => { ln.style('stroke-opacity', 1); const gn = pv('8.2', 'ganho_nac'); tipShow(ev, { t: d.rotulo, rows: [['', '1º turno', fp(d.v)], [C0(), '2º turno', fp(d.v2)], ['', 'Ganho', sg(d.v2 - d.v, f1) + ' p.p.'], ...(gn ? [['', 'Ganho nacional', sg(gn.v, f1) + ' p.p.']] : [])] }); })
          .on('pointermove', tipMove).on('pointerleave', () => { ln.style('stroke-opacity', 0.45); tipHide(); });
      });
      svg.append('text').attr('x', xa).attr('y', h - 6).attr('text-anchor', 'start').text('1º turno');
      svg.append('text').attr('x', xb).attr('y', h - 6).attr('text-anchor', 'end').text('2º turno');
      legend(box, [['ln', C0(), r.length + ' cidades com 88%+ para Lula'], ['dash', 'var(--cds-chart-status-critical)', '80% já no 1º turno']]);
    },
    norte(box) {
      if (!ok('norte')) { if (failed('norte')) fail(box); else box.classList.add('dash-skeleton'); return; }
      box.classList.remove('dash-skeleton');
      const S = rowsOf('norte').filter((d) => isFinite(d.dT) && isFinite(d.dF));
      const h = 236, mb = 22, ml = 34, mt = 16;
      const { svg, w } = svgIn(box, h);
      const qx = S.map((d) => d.dT).sort(d3.ascending), qy = S.map((d) => d.dF).sort(d3.ascending);
      const x = d3.scaleLinear([Math.min(0, d3.quantile(qx, 0.003)), Math.max(0, d3.quantile(qx, 0.997))], [ml, w - 4]).nice().clamp(true);
      const y = d3.scaleLinear([Math.min(0, d3.quantile(qy, 0.003)), Math.max(0, d3.quantile(qy, 0.997))], [h - mb, mt]).nice().clamp(true);
      gridY(svg, y, y.ticks(4), ml, w - 4, (t) => sg(t, fi));
      svg.append('line').attr('x1', x(0)).attr('x2', x(0)).attr('y1', mt).attr('y2', h - mb).style('stroke', 'var(--cds-chart-reference)');
      svg.append('line').attr('x1', ml).attr('x2', w - 4).attr('y1', y(0)).attr('y2', y(0)).style('stroke', 'var(--cds-chart-reference)');
      const r = d3.scaleSqrt([0, d3.max(S, (d) => d.vv)], [1.5, 7]);
      svg.append('g').selectAll('circle').data(S).join('circle').attr('cx', (d) => x(d.dT)).attr('cy', (d) => y(d.dF)).attr('r', (d) => r(d.vv)).style('fill', C0()).style('fill-opacity', 0.35);
      axisX(svg, x, h - mb, x.ticks(5), (t) => sg(t, fi));
      svg.append('text').attr('x', ml).attr('y', 10).text('variação de % Flávio (p.p.)');
      svg.append('text').attr('x', w - 4).attr('y', h - mb - 6).attr('text-anchor', 'end').text('variação do comparecimento →');
      const qt = d3.quadtree(S, (d) => x(d.dT), (d) => y(d.dF));
      svg.append('rect').attr('x', ml).attr('y', mt).attr('width', w - ml - 4).attr('height', h - mb - mt).style('fill', 'transparent')
        .on('pointermove', (ev) => {
          const [px, py] = d3.pointer(ev);
          const d = qt.find(px, py, 12);
          if (!d) { tipHide(); return; }
          tipShow(ev, { t: d.municipio + ' (' + d.uf + ')', rows: [['', 'Comparecimento', sg(d.dT, f1) + ' p.p.'], ['', '% Flávio', sg(d.dF, f1) + ' p.p.'], ['', 'Votos válidos', fi(d.vv)]] });
        })
        .on('pointerleave', tipHide);
      legend(box, [['dot', C0(), 'município de AC, AM, AP, MA, PA, PI, RO, RR ou TO (tamanho = votos)']]);
    },

    rdvnulos(box) {
      const D = pc('4.5');
      const rowH = 26, top = 8, h = top + D.length * rowH + 22;
      const { svg, w } = svgIn(box, h);
      const ml = 195, mr = 46;
      const x = d3.scaleLinear([0, 100], [ml, w - mr]);
      gridX(svg, x, [0, 25, 50, 75, 100], top, h - 22, (t) => t + '%');
      D.forEach((d, i) => {
        const y0 = top + i * rowH, yc = y0 + rowH / 2, txt = d.rotulo || d.lbl;
        const col = d.k === 'gov_rn_22' ? C1() : d.k === 'pres_pbal_loc2' ? 'var(--color-ok)' : C0();
        const g = svg.append('g').attr('class', 'row').attr('tabindex', 0);
        g.append('rect').attr('class', 'hit').attr('x', 0).attr('y', y0 + 1).attr('width', w).attr('height', rowH - 2).attr('rx', 3);
        const lbl = g.append('text').attr('x', ml - 6).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'fg').text(txt);
        fit(lbl, ml - 10);
        g.append('rect').attr('x', x(0)).attr('y', yc - 6).attr('width', Math.max(2, x(d.v) - x(0))).attr('height', 12).attr('rx', 2).style('fill', col);
        g.append('text').attr('x', x(d.v) + 5).attr('y', yc + 4).attr('class', 'st').text(f1(d.v) + '%');
        d3tip(g, () => ({ t: txt, rows: [
          [col, '% dos votos nulos da tela', f1(d.v) + '%'],
          ['', 'Votos nulos com a dezena', fi(d.v2) + ' de ' + fi(d.lo) + ' nulos'],
        ], b: 'Extraído diretamente do campo VotoDigitado nos arquivos binários ASN.1 -rdv.dat (379 seções × 2 turnos em PB, AL e RN). Prova que a confusão 1ºT (Governador vs. Presidente) é 100% simétrica (nulo "13" em PB/AL e nulo "22" no RN) e cai 85,8% no 2ºT.' }));
      });
      legend(box, [['', C0(), 'confusão pró-13 ou nº local no 1ºT'], ['', 'var(--color-ok)', 'queda no 2ºT (−85,8%)'], ['', C1(), 'espelho no RN (nulo "22" para Governador)']]);
    },

    multicargo(box) {
      const D = pc('8.4');
      const rowH = 28, top = 8, h = top + D.length * rowH + 22;
      const { svg, w } = svgIn(box, h);
      const ml = 210, mr = 50;
      const x = d3.scaleLinear([0, 60], [ml, w - mr]);
      gridX(svg, x, [0, 15, 30, 45, 60], top, h - 22, (t) => t + '%');
      D.forEach((d, i) => {
        const y0 = top + i * rowH, yc = y0 + rowH / 2, txt = d.rotulo || d.lbl;
        const col = d.k === 'casado_flav_1t' ? C1() : C0();
        const g = svg.append('g').attr('class', 'row').attr('tabindex', 0);
        g.append('rect').attr('class', 'hit').attr('x', 0).attr('y', y0 + 1).attr('width', w).attr('height', rowH - 2).attr('rx', 3);
        const lbl = g.append('text').attr('x', ml - 6).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'fg').text(txt);
        fit(lbl, ml - 10);
        g.append('rect').attr('x', x(0)).attr('y', yc - 6).attr('width', Math.max(2, x(d.v) - x(0))).attr('height', 12).attr('rx', 2).style('fill', col);
        g.append('text').attr('x', x(d.v) + 5).attr('y', yc + 4).attr('class', 'st').text(f1(d.v) + '%');
        d3tip(g, () => ({ t: txt, rows: [
          [col, '% das seções', f1(d.v) + '%'],
          ['', 'Urnas (censo 100%)', fi(d.v2) + ' de ' + fi(d.lo) + ' seções'],
        ], b: 'Censo 100% multi-cargo (67,86 milhões de registros candidato×seção). Quando a soma Governador Direita + Lula ultrapassa 100% dos votos válidos da seção, é matematicamente obrigatório que o mesmo eleitor na mesma cabine tenha digitado os dois.' }));
      });
      legend(box, [['', C0(), 'voto casado Governador Direita + Lula (ou avanço Gov Direita c/ queda de Flávio)'], ['', C1(), 'voto casado Governador Esquerda + Flávio']]);
    },

    tetos(box) {
      const D = pc('8.5');
      const rowH = 28, top = 8, h = top + D.length * rowH + 22;
      const { svg, w } = svgIn(box, h);
      const ml = 215, mr = 50;
      const x = d3.scaleLinear([0, 75], [ml, w - mr]);
      gridX(svg, x, [0, 25, 50, 75], top, h - 22, (t) => t + '%');
      D.forEach((d, i) => {
        const y0 = top + i * rowH, yc = y0 + rowH / 2, txt = d.rotulo || d.lbl;
        const col = d.k === 'teto3_sec' ? 'var(--color-warn)' : 'var(--color-ok)';
        const g = svg.append('g').attr('class', 'row').attr('tabindex', 0);
        g.append('rect').attr('class', 'hit').attr('x', 0).attr('y', y0 + 1).attr('width', w).attr('height', rowH - 2).attr('rx', 3);
        const lbl = g.append('text').attr('x', ml - 6).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'fg').text(txt);
        fit(lbl, ml - 10);
        g.append('rect').attr('x', x(0)).attr('y', yc - 6).attr('width', Math.max(2, x(d.v) - x(0))).attr('height', 12).attr('rx', 2).style('fill', col);
        g.append('text').attr('x', x(d.v) + 5).attr('y', yc + 4).attr('class', 'st').text(f1(d.v) + '%');
        d3tip(g, () => ({ t: txt, rows: [
          [col, '% de unidades com excesso', f1(d.v) + '% (' + fi(d.lo) + ')'],
          ['', 'Excesso líquido de votos no país', '+' + fi(d.v2) + ' votos'],
          ['', '% da margem nacional (4,43M)', fp(d.hi)],
        ], b: 'Censo 100% de todas as 499.207 seções e 5.570 cidades. O excesso aparente ao nível de seção (+202,7k votos em 11,6% das seções) cai 82% quando agregado por município (+36,3k votos = 0,82% da margem), provando flutuação discreta hipergeométrica entre urnas vizinhas da mesma escola.' }));
      });
      legend(box, [['', 'var(--color-warn)', 'Teto 3 Ideológico (exclui virada de eleitores de Romeu Zema 1ºT)'], ['', 'var(--color-ok)', 'Tetos 1 e 2 (aritméticos): 82% desaparece ao somar por cidade (0,82% da margem)']]);
    },

    raepcd(box) {
      const D = pc('1.4');
      const rowH = 26, top = 8, h = top + D.length * rowH + 22;
      const { svg, w } = svgIn(box, h);
      const ml = 205, mr = 50;
      const x = d3.scaleLinear([0, 100], [ml, w - mr]);
      gridX(svg, x, [0, 25, 50, 75, 100], top, h - 22, (t) => t + '%');
      D.forEach((d, i) => {
        const y0 = top + i * rowH, yc = y0 + rowH / 2, txt = d.rotulo || d.lbl;
        const col = d.k === 'top1_transf' ? C1() : d.k === 'bio_1617' ? 'var(--color-ok)' : C0();
        const g = svg.append('g').attr('class', 'row').attr('tabindex', 0);
        g.append('rect').attr('class', 'hit').attr('x', 0).attr('y', y0 + 1).attr('width', w).attr('height', rowH - 2).attr('rx', 3);
        const lbl = g.append('text').attr('x', ml - 6).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'fg').text(txt);
        fit(lbl, ml - 10);
        g.append('rect').attr('x', x(0)).attr('y', yc - 6).attr('width', Math.max(2, x(d.v) - x(0))).attr('height', 12).attr('rx', 2).style('fill', col);
        g.append('text').attr('x', x(d.v) + 5).attr('y', yc + 4).attr('class', 'st').text(f2(d.v) + '%');
        d3tip(g, () => ({ t: txt, rows: [
          [col, 'Percentual no Censo 100%', f2(d.v) + '%'],
          ['', 'Contagem exata', fi(d.v2) + ' de ' + fi(d.lo)],
        ], b: 'Censo de 9,53 milhões de operações RAE, 2,49 milhões de transferências de domicílio e 1,97 milhão de eleitores PcD únicos. Novos títulos 2025/2026 têm 99,95% de biometria, cidades com pico de transferência votaram em Flávio (48/56) e eleitores PcD com dificuldade de voto tiveram 84,3% de abstenção.' }));
      });
      legend(box, [['', 'var(--color-ok)', 'biometria em novos jovens (99,95%)'], ['', C1(), 'vitórias de Flávio no Top 1% de transferências (48/56)'], ['', C0(), 'comparecimento real PcD (muito abaixo da média)']]);
    },

    gedai(box) {
      const D = pc('3.4');
      const rowH = 26, top = 8, h = top + D.length * rowH + 22;
      const { svg, w } = svgIn(box, h);
      const ml = 210, mr = 54;
      const x = d3.scaleLinear([0, 100], [ml, w - mr]);
      gridX(svg, x, [0, 25, 50, 75, 100], top, h - 22, (t) => t + '%');
      D.forEach((d, i) => {
        const y0 = top + i * rowH, yc = y0 + rowH / 2, txt = d.rotulo || d.lbl;
        const col = 'var(--color-ok)';
        const g = svg.append('g').attr('class', 'row').attr('tabindex', 0);
        g.append('rect').attr('class', 'hit').attr('x', 0).attr('y', y0 + 1).attr('width', w).attr('height', rowH - 2).attr('rx', 3);
        const lbl = g.append('text').attr('x', ml - 6).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'fg').text(txt);
        fit(lbl, ml - 10);
        g.append('rect').attr('x', x(0)).attr('y', yc - 6).attr('width', Math.max(2, x(d.v) - x(0))).attr('height', 12).attr('rx', 2).style('fill', col);
        g.append('text').attr('x', x(d.v) + 5).attr('y', yc + 4).attr('class', 'st').text('100,0%');
        d3tip(g, () => ({ t: txt, rows: [
          [col, 'Conformidade no Censo 100%', '100,0000%'],
          ['', 'Unidades validadas', fi(d.v2) + ' de ' + fi(d.lo)],
        ], b: 'Censo de 100% dos logs do GEDAI-UE nas 28 UFs (1ºT e 2ºT, 5,03 milhões de linhas). Todas as estações dos Cartórios Eleitorais rodaram exatamente o mesmo software oficial (8.23.0.0) e importaram a mesma imagem nacional da urna (o00000br-pu.jez 202608121843).' }));
      });
      legend(box, [['', 'var(--color-ok)', '100,0000% validado nas 28 UFs (4.333 estações GEDAI-UE e 5,03M linhas)']]);
    },

    exp2226(box) {
      const D = pc('3.5');
      const rowH = 26, top = 8, h = top + D.length * rowH + 22;
      const { svg, w } = svgIn(box, h);
      const ml = 210, mr = 58;
      const x = d3.scaleLinear([40, 65], [ml, w - mr]).clamp(true);
      gridX(svg, x, [40, 45, 50, 55, 60, 65], top, h - 22, (t) => t + '%');
      D.forEach((d, i) => {
        const y0 = top + i * rowH, yc = y0 + rowH / 2, txt = d.rotulo || d.lbl;
        const g = svg.append('g').attr('class', 'row').attr('tabindex', 0);
        g.append('rect').attr('class', 'hit').attr('x', 0).attr('y', y0 + 1).attr('width', w).attr('height', rowH - 2).attr('rx', 3);
        const lbl = g.append('text').attr('x', ml - 6).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'fg').text(txt);
        fit(lbl, ml - 10);
        g.append('line').attr('x1', x(d.v)).attr('x2', x(d.v2)).attr('y1', yc).attr('y2', yc).style('stroke', 'var(--cds-chart-axis)').attr('stroke-width', 2);
        g.append('circle').attr('cx', x(d.v)).attr('cy', yc).attr('r', 4).style('fill', MUT);
        g.append('circle').attr('cx', x(d.v2)).attr('cy', yc).attr('r', 4.5).style('fill', 'var(--color-ok)');
        g.append('text').attr('x', w - 2).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'st').text(sg(d.hi, f2) + ' p.p.');
        d3tip(g, () => ({ t: txt, rows: [
          ['', 'Seções pareadas (2022 × 2026)', fi(d.n)],
          [MUT, 'Lula 2ºT em 2022', f2(d.v) + '%'],
          ['var(--color-ok)', 'Lula 2ºT em 2026', f2(d.v2) + '%'],
          ['', 'Variação intra-município (2026 − 2022)', sg(d.lo, f2) + ' p.p.'],
          ['var(--color-ok)', 'Variação intra-escola (2026 − 2022)', sg(d.hi, f2) + ' p.p.'],
        ], b: 'Experimento Natural 2022×2026 em 461.219 seções pareadas (Frente 21). A substituição das urnas antigas (UE2009–2015) por urnas novas (UE2020/2022) produziu variação zero dentro da mesma escola (0,00 p.p.), e nas cidades <50k a diferença entre os grupos de seções persistiu idêntica mesmo quando todas passaram a usar UE2020/2022.' }));
      });
      legend(box, [['dot', MUT, '% Lula em 2022'], ['dot', 'var(--color-ok)', '% Lula em 2026 (texto à direita = efeito intra-escola)']]);
    },

    filatse(box) {
      const pts = pc('5.2').filter((d) => d.k.startsWith('p')).sort((a, b) => a.v - b.v);
      const lat = pv('5.2', 'lat');
      const h = 186, mb = 22, ml = 38, mt = 16;
      const { svg, w } = svgIn(box, h);
      const x = d3.scaleLinear([5, 100], [ml, w - 8]);
      const y = d3.scaleLinear([48.5, 52.5], [h - mb, mt]);
      gridY(svg, y, [49, 50, 51, 52], ml, w - 8, (t) => t + '%');
      svg.append('line').attr('x1', ml).attr('x2', w - 8).attr('y1', y(50)).attr('y2', y(50)).style('stroke', 'var(--cds-chart-reference)');
      const lEsp = d3.line().x((d) => x(d.v)).y((d) => y(d.lo));
      const lReal = d3.line().x((d) => x(d.v)).y((d) => y(d.v2));
      svg.append('path').attr('d', lEsp(pts)).style('fill', 'none').style('stroke', 'var(--color-ok)').attr('stroke-width', 2).attr('stroke-dasharray', '4 3');
      svg.append('path').attr('d', lReal(pts)).style('fill', 'none').style('stroke', C0()).attr('stroke-width', 2.5);
      svg.selectAll('circle.p').data(pts).join('circle').attr('class', 'p')
        .attr('cx', (d) => x(d.v)).attr('cy', (d) => y(d.v2)).attr('r', 3.5).style('fill', C0())
        .call(d3tip, (d) => ({ t: fi(d.v) + '% das seções totalizadas (' + d.rotulo + ')', rows: [
          [C0(), 'Lula 2ºT acumulado real', f2(d.v2) + '% (' + fi(d.n) + ' seções)'],
          ['var(--color-ok)', 'Esperado pelas mesmas seções no 1ºT + shift', f2(d.lo) + '%'],
          ['', 'Voto dessas mesmas seções no 1ºT', f2(d.hi) + '%'],
          ['', 'Fila mediana no servidor TSE (Lula vs Flávio)', (lat ? f1(lat.v) + ' s vs ' + f1(lat.v2) + ' s' : '24,0 s vs 24,0 s')],
        ], b: 'Censo dos 497.897 timestamps DT_RECEBIMENTO_BU_HOR_TSE e DT_PRIM_TOT_PARCIAL_HOR_TSE. Os primeiros 25% de seções tinham dado apenas 43,25% a Lula no 1ºT (−1,91 p.p. abaixo da média nacional), explicando 100% da curva.' }));
      axisX(svg, x, h - mb, [5, 25, 50, 75, 100], (t) => t + '%');
      legend(box, [['ln', C0(), 'curva acumulada real do 2ºT (497.897 seções)'], ['dash', 'var(--color-ok)', 'esperado pelas mesmas seções no 1ºT + shift nacional (fila TSE: 24,0 s vs 24,0 s)']]);
    },

    geofina(box) {
      const D = pc('7.2');
      const rowH = 26, top = 8, h = top + D.length * rowH + 22;
      const { svg, w } = svgIn(box, h);
      const ml = 210, mr = 52;
      const x = d3.scaleLinear([85, 100], [ml, w - mr]).clamp(true);
      gridX(svg, x, [85, 90, 95, 100], top, h - 22, (t) => t + '%');
      D.forEach((d, i) => {
        const y0 = top + i * rowH, yc = y0 + rowH / 2, txt = d.rotulo || d.lbl;
        const col = d.k === 'r2_escola' || d.k === 'gps_500m' ? 'var(--color-ok)' : C0();
        const g = svg.append('g').attr('class', 'row').attr('tabindex', 0);
        g.append('rect').attr('class', 'hit').attr('x', 0).attr('y', y0 + 1).attr('width', w).attr('height', rowH - 2).attr('rx', 3);
        const lbl = g.append('text').attr('x', ml - 6).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'fg').text(txt);
        fit(lbl, ml - 10);
        g.append('rect').attr('x', x(85)).attr('y', yc - 6).attr('width', Math.max(2, x(d.v) - x(85))).attr('height', 12).attr('rx', 2).style('fill', col);
        g.append('text').attr('x', x(d.v) + 5).attr('y', yc + 4).attr('class', 'st').text(f2(d.v) + '%');
        d3tip(g, () => ({ t: txt, rows: [
          [col, d.k === 'gps_500m' ? 'Correlação r (escolas <500m)' : 'Variância explicada (R²)', f2(d.v) + '%'],
          ['', 'Desvio-padrão residual (DP)', f2(d.v2) + ' p.p.'],
          ['', 'Unidades geográficas no Censo', fi(d.lo)],
        ], b: 'Censo geográfico de 497.897 seções e 94.056 escolas com coordenadas GPS (eleitorado_local_votacao_2026.zip, Frente 17). A escola e o 1º turno determinam 98,91% da votação de todas as urnas do Brasil.' }));
      });
      legend(box, [['', 'var(--color-ok)', 'vizinhança física GPS <500m (r = 94,0%) e efeito escola (R² = 98,91%)'], ['', C0(), 'progressão UF → Município → Bairro']]);
    },

    hist1426(box) {
      const D = pc('8.6');
      const rowH = 26, top = 8, h = top + D.length * rowH + 22;
      const { svg, w } = svgIn(box, h);
      const ml = 210, mr = 52;
      const x = d3.scaleLinear([80, 100], [ml, w - mr]).clamp(true);
      gridX(svg, x, [80, 85, 90, 95, 100], top, h - 22, (t) => t + '%');
      D.forEach((d, i) => {
        const y0 = top + i * rowH, yc = y0 + rowH / 2, txt = d.rotulo || d.lbl;
        const col = i < 3 ? 'var(--color-ok)' : C0();
        const g = svg.append('g').attr('class', 'row').attr('tabindex', 0);
        g.append('rect').attr('class', 'hit').attr('x', 0).attr('y', y0 + 1).attr('width', w).attr('height', rowH - 2).attr('rx', 3);
        const lbl = g.append('text').attr('x', ml - 6).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'fg').text(txt);
        fit(lbl, ml - 10);
        g.append('rect').attr('x', x(80)).attr('y', yc - 6).attr('width', Math.max(2, x(d.v) - x(80))).attr('height', 12).attr('rx', 2).style('fill', col);
        g.append('text').attr('x', x(d.v) + 5).attr('y', yc + 4).attr('class', 'st').text(f2(d.v) + '%');
        d3tip(g, () => ({ t: txt, rows: [
          [col, 'Correlação de Pearson (r)', f2(d.v) + '%'],
          ['', 'Variância explicada (R²)', f2(d.v2) + '%'],
          ['', 'Unidades pareadas no Censo', fi(d.lo)],
        ], b: 'Painel Longitudinal de 12 Anos (2014 × 2018 × 2022 × 2026 = 3.707.067 urnas nos 8 turnos, Frentes 21 e 22). O 2ºT de 2026 teve o menor número de seções 100% da série histórica (106 vs. 192 em 2014, 328 em 2018 e 143 em 2022), e a queda de presença no Norte (−1,81 p.p.) repete 2014 (−3,93 p.p.), 2018 (−3,53 p.p.) e 2022 (−1,99 p.p.).' }));
      });
      legend(box, [['', 'var(--color-ok)', 'persistência 2022 × 2026 (cidades r = 98,9%, escolas 98,2%, seções 97,3%)'], ['', C0(), 'persistência histórica 2014–2022 (3,71 milhões de urnas)']]);
    },

    ceft2t(box) {
      const D = pc('2.5');
      const rowH = 28, top = 8, h = top + D.length * rowH + 22;
      const { svg, w } = svgIn(box, h);
      const ml = 215, mr = 56;
      const x = d3.scaleLinear([0, 100], [ml, w - mr]).clamp(true);
      gridX(svg, x, [0, 25, 50, 75, 100], top, h - 22, (t) => t + '%');
      D.forEach((d, i) => {
        const y0 = top + i * rowH, yc = y0 + rowH / 2, txt = d.rotulo || d.lbl;
        const col = d.k === 'ccont_sub' ? C0() : 'var(--color-ok)';
        const g = svg.append('g').attr('class', 'row').attr('tabindex', 0);
        g.append('rect').attr('class', 'hit').attr('x', 0).attr('y', y0 + 1).attr('width', w).attr('height', rowH - 2).attr('rx', 3);
        const lbl = g.append('text').attr('x', ml - 6).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'fg').text(txt);
        fit(lbl, ml - 10);
        g.append('rect').attr('x', x(0)).attr('y', yc - 6).attr('width', Math.max(3, x(d.v) - x(0))).attr('height', 12).attr('rx', 2).style('fill', col);
        const valTxt = d.k === 'ccont_sub' ? f2(d.v) + '% (−0,27 p.p.)' : f2(d.v) + '%';
        g.append('text').attr('x', x(d.v) + 5).attr('y', yc + 4).attr('class', 'st').text(valTxt);
        d3tip(g, () => ({ t: txt, rows: [
          [col, 'Cobertura no Censo 2ºT', f2(d.v) + '%'],
          ['', 'Unidades auditadas', fi(d.v2) + ' de ' + fi(d.lo)],
          ...(d.k === 'csec_tit' ? [['', 'Lula 2ºT nas urnas titulares', f2(d.hi) + '%']] : []),
          ...(d.k === 'ccont_sub' ? [['var(--color-ok)', 'Efeito intra-cidade da troca de urna', sg(d.hi, f2) + ' p.p. (Lula 50,78%)']] : []),
        ], b: 'Censo de 100% da Tabela de Correspondência Efetivada do 2º Turno (CEFT_2t_261020261201, 499.207 seções) cruzada com CESP 2ºT (25/10/2026) e GEDAI-UE 2ºT. Zero urnas sem serial de hardware TPM; as 2.670 substituições usaram urnas de contingência oficiais e tiveram −0,27 p.p. para Lula na mesma cidade.' }));
      });
      legend(box, [['', 'var(--color-ok)', '100% validado no CEFT 2ºT (499.207 seções, 0 órfãs)'], ['', C0(), 'contingência CCONT (0,53% das seções; −0,27 p.p. intra-cidade)']]);
    },

    inflexao1719(box) {
      const D = pc('6.2');
      const rowH = 26, top = 8, h = top + D.length * rowH + 22;
      const { svg, w } = svgIn(box, h);
      const ml = 215, mr = 58;
      const x = d3.scaleLinear([35, 60], [ml, w - mr]).clamp(true);
      gridX(svg, x, [35, 40, 45, 50, 55, 60], top, h - 22, (t) => t + '%');
      svg.append('line').attr('x1', x(50)).attr('x2', x(50)).attr('y1', top).attr('y2', h - 22).style('stroke', 'var(--cds-chart-reference)');
      D.forEach((d, i) => {
        const y0 = top + i * rowH, yc = y0 + rowH / 2, txt = d.rotulo || d.lbl;
        const g = svg.append('g').attr('class', 'row').attr('tabindex', 0);
        g.append('rect').attr('class', 'hit').attr('x', 0).attr('y', y0 + 1).attr('width', w).attr('height', rowH - 2).attr('rx', 3);
        const lbl = g.append('text').attr('x', ml - 6).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'fg').text(txt);
        fit(lbl, ml - 10);
        const col = d.k === 'fuso_m4' ? C1() : 'var(--color-ok)';
        g.append('line').attr('x1', x(d.v)).attr('x2', x(d.v2)).attr('y1', yc).attr('y2', yc).style('stroke', 'var(--cds-chart-axis)').attr('stroke-width', 2);
        g.append('circle').attr('cx', x(d.v)).attr('cy', yc).attr('r', 4).style('fill', MUT);
        g.append('circle').attr('cx', x(d.v2)).attr('cy', yc).attr('r', 4.5).style('fill', col);
        g.append('text').attr('x', w - 2).attr('y', yc + 4).attr('text-anchor', 'end').attr('class', 'st').text(sg(d.lo, f2) + ' p.p.');
        d3tip(g, () => ({ t: txt, rows: [
          ['', 'Seções no Censo BWeb 2ºT', fi(d.n) + ' seções'],
          [MUT, 'Lula L/(L+F) nas mesmas seções no 1ºT', f2(d.v) + '%'],
          [col, 'Lula no 2ºT', f2(d.v2) + '%'],
          ['var(--color-ok)', 'Avanço de Lula (2ºT − 1ºT)', sg(d.lo, f2) + ' p.p.'],
          ...(d.k === 'prorrog_1900' ? [['', 'Excesso líquido de presença nas 2h extras', '+' + fi(d.hi) + ' eleitores (de 1,86M no dia todo)']] : []),
          ...(d.k === 'sp_cap_1900' ? [['', 'Avanço nas 25.202 seções <19h de SP Capital', '+' + f2(d.hi) + ' p.p. (maior que nas >=19h)']] : []),
          ...(d.k !== 'prorrog_1900' && d.k !== 'sp_cap_1900' ? [['', 'Saldo de votos 2ºT (Lula − Flávio)', sg(d.hi, fi) + ' votos']] : []),
        ], b: 'Censo de 100% dos Boletins de Urna do 2ºT (499.205 seções) pareados com o 1ºT. Todas as faixas de horário tiveram exatamente o mesmo avanço entre os turnos (+2,64 a +2,78 p.p.): a diferença entre <=17h00 e >17h00 vem 100% de misturar fusos UTC-4/-5 (15h/16h locais) com o fechamento normal das 17h01–17h15 no fuso de Brasília.' }));
      });
      legend(box, [['dot', MUT, '% Lula L/(L+F) já no 1ºT (mesmas seções)'], ['dot', 'var(--color-ok)', '% Lula no 2ºT (à direita = Δ 2ºT − 1ºT uniforme em +2,7 p.p.)'], ['dot', C1(), 'fuso UTC-4/-5/ZZ encerrado às 15h/16h locais']]);
    },
  };

  function drawProvas() {
    const body = document.getElementById('provas-body');
    if (pending(body, ['casos', 'provas'])) return;
    P.rows = rowsOf('provas');
    const casos = rowsOf('casos');
    const lg = document.getElementById('provas-leg');
    lg.replaceChildren();
    VERS.forEach((v) => { const s = el('span', 'vx-pill ' + COR[v], v); s.tabIndex = 0; tipOn(s, () => ({ t: v, b: VERED[v] }), true); lg.append(s); });
    Object.keys(FZ).forEach((k) => { const [, nome, tip] = FZ[k]; const s = el('span', 'vx-fz'); s.append(glyph(k), el('span', null, nome)); s.tabIndex = 0; tipOn(s, () => ({ t: nome, b: tip }), true); lg.append(s); });
    body.replaceChildren();
    const est = [...new Set(casos.map((c) => c.estagio))];
    est.forEach((s) => {
      const cs = casos.filter((c) => c.estagio === s);
      const hd = el('div', 'vx-sec');
      hd.id = 'etapa-' + s;
      hd.append(el('span', 'vx-sec-n', s), mark(el('span', 'vx-sec-t', cs[0].estagio_nome), 'casos', 'estagio_nome', 'id=' + cs[0].id), mark(el('span', 'vx-sec-q', cs[0].estagio_pergunta), 'casos', 'estagio_pergunta', 'id=' + cs[0].id));
      const grid = el('div', 'vx-proofs');
      body.append(hd, grid);
      cs.forEach((c) => {
        const card = el('article', 'vx-card vx-proof');
        card.id = 'caso-' + c.id.replace('.', '-');
        const h = el('div', 'vx-proof-h');
        const info = el('button', 'vx-info', 'i');
        info.setAttribute('aria-label', 'Detalhes técnicos de ' + c.id);
        tipOn(info, () => ({ t: c.id + ' · como foi testado', b: c.tecnico }), true);
        h.append(el('span', 'id', c.id), mark(el('h3', null, c.nome), 'casos', 'nome', 'id=' + c.id), info);
        const bd = el('div', 'vx-badges');
        const pill = mark(el('span', 'vx-pill ' + COR[c.veredito], c.veredito), 'casos', 'veredito', 'id=' + c.id);
        pill.tabIndex = 0;
        tipOn(pill, () => ({ t: c.veredito, b: VERED[c.veredito] }), true);
        const fz = el('span', 'vx-fz'); fz.append(glyph(c.forca), el('span', null, FZ[c.forca][1]));
        fz.tabIndex = 0;
        tipOn(fz, () => ({ t: FZ[c.forca][1], b: FZ[c.forca][2] }), true);
        bd.append(pill, fz);
        const fr = mark(el('p', 'vx-frase', c.frase), 'casos', 'frase', 'id=' + c.id);
        const viz = el('div', 'vx-viz');
        viz.dataset.source = c.visual === 'enchimento' ? 'provas secoes' : c.visual === 'norte' ? 'norte' : 'provas';
        card.append(h, bd, fr, viz);
        if (c.mede) {
          const rg = el('div', 'vx-regua');
          rg.tabIndex = 0;
          const l = el('div', 'vx-regua-l');
          l.append(el('span', null, 'Teto'), mark(el('b', null, fv(c.teto)), 'casos', 'teto', 'id=' + c.id), el('span', null, 'votos'),
            el('span', 'r', fp(c.pct) + (c.limiar === 'meia' ? ' da metade da margem' : ' da margem')));
          const bar = el('div', 'vx-bar');
          const i1 = el('i'); i1.style.width = Math.min(100, c.pct) + '%'; i1.style.background = 'color-mix(in srgb, ' + CV[COR[c.veredito]] + ' 35%, transparent)';
          const i2 = el('i'); i2.style.width = Math.min(100, c.pct_pt) + '%'; i2.style.background = CV[COR[c.veredito]];
          if (!(c.pct > 0)) { i1.style.minWidth = '0'; i2.style.minWidth = '0'; }
          bar.append(i1, i2);
          rg.append(l, bar);
          tipOn(rg, () => ({ t: 'Teto de ' + c.id, rows: [[CV[COR[c.veredito]], 'Teto (extremo do IC 95%)', fv(c.teto) + ' votos'], ...(c.teto_pt !== c.teto ? [['', 'Melhor estimativa', fv(c.teto_pt) + ' votos']] : []), ['var(--cds-chart-status-critical)', 'Necessário para virar', fi(c.limiar_votos)]], b: LIMIAR[c.limiar] }), true);
          card.append(rg);
        }
        grid.append(card);
        try { (VIS[c.visual] || (() => {}))(viz, c); } catch (e) { viz.replaceChildren(el('div', 'vx-fail', 'Não foi possível desenhar')); setTimeout(() => { throw e; }); }
      });
    });
  }

  // ---------- explorar ----------
  const PRESETS = ['nb_4', 'dnb_3', 'man_3', 'scad_3', 'urna_3', 'urna_0', 'troca_1', 'log_3', 'enc_2', 'reg_0', 'idade_3', 'esc_3', 'gov_0'];
  const setRecorte = (id) => dash.setParams({ recorte: id });
  document.getElementById('slice-clear').addEventListener('click', () => setRecorte('all'));

  function drawExplorar() {
    const body = document.getElementById('dims-body'), hero = document.getElementById('hero'), pre = document.getElementById('presets');
    const nameEl = document.getElementById('slice-name'), clr = document.getElementById('slice-clear');
    if (pending(body, ['cortes', 'dims'])) { hero.replaceChildren(); return; }
    const dims = rowsOf('dims'), cortes = rowsOf('cortes');
    const censoMap = new Map((ok('censo') ? rowsOf('censo') : []).map((r) => [r.k, r]));
    let f = dash.params().recorte || 'all';
    if (!cortes.some((r) => r.f === f)) f = 'all';
    const dimOf = new Map(dims.map((d) => [d.id, d]));
    const cur = dimOf.get(f);
    const censoCur = censoMap.get(f);
    const censoAll = censoMap.get('all');
    nameEl.replaceChildren();
    if (cur) nameEl.append(mark(el('span', null, cur.titulo), 'dims', 'titulo', 'id=' + f), el('span', null, ': '), mark(el('span', null, cur.rotulo), 'dims', 'rotulo', 'id=' + f));
    else nameEl.textContent = 'Brasil inteiro';
    clr.hidden = f === 'all';
    pre.replaceChildren();
    PRESETS.filter((id) => dimOf.has(id)).forEach((id) => {
      const d = dimOf.get(id);
      const b = el('button', 'vx-btn');
      b.setAttribute('aria-pressed', String(f === id));
      b.append(el('span', null, d.titulo + ': '), mark(el('span', null, d.rotulo), 'dims', 'rotulo', 'id=' + id));
      b.addEventListener('click', () => setRecorte(f === id ? 'all' : id));
      pre.append(b);
    });
    const rows = cortes.filter((r) => r.f === f);
    const me = rows.find((r) => r.t === 'all');
    // herói
    hero.replaceChildren();
    const W = 'f=' + f + '&t=all';
    const four = el('div', 'vx-hero4');
    hero.append(four);
    const tile = (label, parts, sub, tip) => {
      const k = el('div', 'vx-kpi'); k.tabIndex = 0;
      const v = el('span', 'vx-kpi-v'); parts.forEach((p) => v.append(p));
      k.append(el('span', 'vx-kpi-l', label), v);
      if (sub) k.append(el('span', 'vx-kpi-s', sub));
      if (tip) tipOn(k, tip);
      four.append(k);
      return k;
    };
    const m = (field, txt) => mark(el('span', null, txt), 'cortes', field, W);
    tile('Seções auditadas', [m('n', fi(me.n))], censoCur ? 'Censo 100%: ' + fi(censoCur.n) + ' seções' : 'de ' + fi(cortes.find((r) => r.f === 'all' && r.t === 'all').n) + ' sorteadas', () => ({
      t: 'Cobertura de seções (Amostra BU + Censo 100%)',
      rows: [
        ['', 'Amostra estratificada BUs/Logs', fi(me.n) + ' de 9.600 seções'],
        ...(censoCur ? [['var(--color-ok)', 'Censo 100% TSE (1ºT × 2ºT)', fi(censoCur.n) + ' de ' + fi(censoAll ? censoAll.n : 497508) + ' seções'], ['', 'Votos válidos 2ºT no Censo', fi(censoCur.vv2)]] : []),
      ],
      b: 'As variáveis físicas extraídas dentro dos arquivos de urna (biometria por eleitor, horário de encerramento, geração UE) vêm da amostra estratificada de 9.600 BUs; os totais de votos e recortes cadastrais/geográficos foram validados no Censo de 100% das 499.207 seções.',
    }));
    tile('Eleitorado representado', [m('pa', fp(me.pa))], censoCur ? 'Censo 100%: ' + fp(censoCur.pa) : null, () => ({
      t: 'Fração do eleitorado nacional',
      rows: [
        ['', 'Estimativa ponderada (amostra)', fp(me.pa)],
        ...(censoCur ? [['var(--color-ok)', 'Censo 100% (votos válidos 2ºT)', fp(censoCur.pa)]] : []),
      ],
      b: 'Parte do eleitorado do país que este recorte representa.',
    }));
    tile('Sem digital', [m('nb1', f1(me.nb1)), el('span', null, ' → '), m('nb2', f1(me.nb2) + '%')], '1º → 2º turno', () => ({ b: 'Votos de eleitores sem biometria cadastrada ou liberados manualmente pelo mesário (extraído dos BUs/logs), em % do comparecimento.' }));
    tile('Lula', [m('l1', f1(me.l1)), el('span', null, ' → '), m('l2', f1(me.l2) + '%')], censoCur ? 'Censo 100%: ' + f1(censoCur.l1) + ' → ' + f1(censoCur.l2) + '%' : '1º → 2º turno, votos válidos', () => ({
      t: 'Votação de Lula (1º → 2º turno)',
      rows: [
        ['', 'Na amostra ponderada', f1(me.l1) + '% → ' + f1(me.l2) + '% (' + sg(me.l2 - me.l1, f1) + ' p.p.)'],
        ...(censoCur ? [['var(--color-ok)', 'No Censo 100% (' + fi(censoCur.n) + ' seções)', f1(censoCur.l1) + '% → ' + f1(censoCur.l2) + '% (' + sg(censoCur.dl, f1) + ' p.p.)']] : []),
      ],
    }));
    const big = el('div', 'vx-kpi vx-big'); big.tabIndex = 0;
    const has0 = me.lo <= 0 && me.hi >= 0;
    const verd = el('span', 'vx-verd ' + (has0 || me.hi <= 0 ? 'ok' : 'warn'), has0 ? 'Igual à própria cidade, dentro do acaso' : me.hi <= 0 ? 'Sem ganho extra de Lula aqui' : 'Lula foi melhor aqui do que na própria cidade');
    const bv = el('span', 'vx-kpi-v'); bv.append(m('x', sg(me.x) + ' p.p.'));
    const fo = el('div', 'vx-forest');
    const teto = el('span', 'vx-kpi-s');
    const meia = pv('nac', 'meia') || (rowsOf('provas').find((r) => r.caso === 'nac' && r.k === 'meia'));
    teto.append(el('span', null, 'Teto de votos movidos neste recorte: '), m('teto', fi(me.teto)), el('span', null, meia ? ' · ' + fp((me.teto / meia.v) * 100) + ' da metade da margem' : ''));
    big.append(el('span', 'vx-kpi-l', 'Ganho extra de Lula vs. a própria cidade'), bv, verd, fo, teto);
    hero.append(big);
    tipOn(big, () => ({ t: 'Como ler', rows: [['', 'Estimativa', sg(me.x) + ' p.p.'], ['', 'IC 95%', sg(me.lo) + ' a ' + sg(me.hi)]], b: 'Para cada seção: (ganho de Lula do 1º para o 2º turno na seção) − (o mesmo na cidade inteira). Média ponderada pelo peso amostral × votos válidos. Zero = a seção votou como a própria cidade. Teto = extremo superior do intervalo × votos válidos do recorte.' }));
    const fsvg = svgIn(fo, 46);
    const dom0 = Math.max(1, Math.ceil(Math.max(Math.abs(me.lo), Math.abs(me.hi)) * 2) / 2);
    const fx = forestRow(fsvg.svg, fsvg.w, 2, null, me.x, me.lo, me.hi, [-dom0, dom0], { color: has0 || me.hi <= 0 ? 'var(--color-ok)' : 'var(--color-warn)' });
    axisX(fsvg.svg, fx.x, 22, [-dom0, 0, dom0], (t) => sg(t, f1));
    // cartões por dimensão
    body.replaceChildren();
    const groups = d3.groups(dims, (d) => d.grupo);
    const usable = rows.filter((r) => r.t !== 'all' && r.n >= 20);
    const ext = Math.max(1, d3.max(usable, (r) => Math.max(Math.abs(r.lo), Math.abs(r.hi))) || 1);
    const D = Math.min(3, Math.ceil(ext * 2) / 2);
    groups.forEach(([gname, gd]) => {
      const sec = el('div', 'vx-sec'); sec.append(el('span', 'vx-sec-t', gname));
      const grid = el('div', 'vx-dimgrid');
      body.append(sec, grid);
      d3.groups(gd, (d) => d.dim).forEach(([dim, cats]) => {
        const card = el('article', 'vx-card vx-dim');
        card.id = 'dim-' + dim;
        const hh = el('div', 'vx-card-h'); hh.append(mark(el('h3', 'vx-h', cats[0].titulo), 'dims', 'titulo', 'id=' + cats[0].id));
        const viz = el('div'); viz.dataset.source = 'cortes dims';
        card.append(hh, viz);
        grid.append(card);
        const items = cats.map((d) => ({ d, r: rows.find((r) => r.t === d.id) }));
        const rowH = 24, top = 4, h = top + items.length * rowH + 20;
        const { svg, w } = svgIn(viz, h);
        const nw = 40;
        let lw = 0;
        items.forEach((it) => { const t = svg.append('text').text(it.d.rotulo); lw = Math.max(lw, tlen(t)); t.remove(); });
        lw = Math.min(lw + 8, w * 0.45);
        const x = d3.scaleLinear([-D, D], [lw, w - nw]).clamp(true);
        svg.append('line').attr('x1', x(0)).attr('x2', x(0)).attr('y1', top).attr('y2', h - 20).style('stroke', 'var(--cds-chart-reference)');
        items.forEach((it, i) => {
          const y0 = top + i * rowH, yc = y0 + rowH / 2, r = it.r, sel = it.d.id === f;
          const cr = f === 'all' ? censoMap.get(it.d.id) : null;
          const g = svg.append('g').attr('class', 'row pick').attr('tabindex', 0).attr('role', 'button').attr('aria-pressed', String(sel)).attr('aria-label', it.d.titulo + ': ' + it.d.rotulo);
          g.append('rect').attr('class', 'hit').attr('x', -4).attr('y', y0 + 1).attr('width', w + 8).attr('height', rowH - 2).attr('rx', 4).style('fill', sel ? 'var(--cds-chart-grid)' : null);
          const t = g.append('text').attr('x', 0).attr('y', yc + 4).attr('class', sel ? 'st' : 'fg').text(it.d.rotulo);
          fit(t, lw - 8);
          g.append('text').attr('x', w).attr('y', yc + 4).attr('text-anchor', 'end').text(r ? fi(r.n) : '0');
          if (r && r.n >= 20) {
            const h0 = r.lo <= 0 && r.hi >= 0, col = h0 || r.hi <= 0 ? C0() : 'var(--color-warn)';
            g.append('line').attr('x1', x(r.lo)).attr('x2', x(r.hi)).attr('y1', yc).attr('y2', yc).style('stroke', col).attr('stroke-width', 3).attr('stroke-linecap', 'round').style('stroke-opacity', 0.45);
            g.append('circle').attr('cx', x(r.x)).attr('cy', yc).attr('r', 4.5).style('fill', col);
          } else if (r) {
            g.append('text').attr('x', x(0) + 6).attr('y', yc + 4).text('poucas seções');
          }
          d3tip(g, () => (r ? { t: it.d.titulo + ': ' + it.d.rotulo, rows: [
            ['', 'Seções na amostra BUs', fi(r.n)],
            ...(cr ? [['var(--color-ok)', 'Seções no Censo 100%', fi(cr.n) + ' (' + fp(cr.pa) + ' dos votos)']] : [['', 'Eleitorado', fp(r.pa)]]),
            ['', 'Sem digital 1º → 2º', f1(r.nb1) + ' → ' + f1(r.nb2) + '%'],
            ['', 'Lula 1º → 2º (amostra)', f1(r.l1) + ' → ' + f1(r.l2) + '%'],
            ...(cr ? [['var(--color-ok)', 'Lula 1º → 2º (Censo 100%)', f1(cr.l1) + ' → ' + f1(cr.l2) + '% (' + sg(cr.dl, f1) + ' p.p.)']] : []),
            [C0(), 'Ganho extra de Lula vs. cidade', sg(r.x) + ' p.p.'], ['', 'IC 95%', sg(r.lo) + ' a ' + sg(r.hi)], ['', 'Teto de votos movidos', fi(r.teto)]],
            b: sel ? 'Clique de novo para limpar o recorte.' : 'Clique para recortar tudo por esta categoria.' } : { t: it.d.rotulo, b: 'Nenhuma seção neste recorte.' }));
          g.on('click', () => { tipHide(); setRecorte(sel ? 'all' : it.d.id); })
            .on('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); setRecorte(sel ? 'all' : it.d.id); } });
        });
        axisX(svg, x, h - 20, [-D, 0, D], (t) => sg(t, f1));
      });
    });
  }

  // ---------- desenho ----------
  function draw() {
    fillMarks();
    if (tab === 'veredito') { drawMatriz(); drawRegua(); drawVirada(); }
    else if (tab === 'provas') drawProvas();
    else drawExplorar();
  }
  kpiTips();
  dash.onData(() => {
    draw();
    if (!opened && ok('casos') && ok('provas')) {
      opened = true;
      const named = location.hash.slice(1);
      if (named === 'provas' || named === 'explorar') show(named);
      else if (/^caso-\d+-\d+$/.test(named)) show('provas', named);
    }
  });
})();
