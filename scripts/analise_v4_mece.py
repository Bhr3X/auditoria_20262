# -*- coding: utf-8 -*-
"""Painel visual MECE — calcula, a partir dos dados brutos da pasta, o veredito e o teto de votos de cada hipótese,
os dados de cada prova visual e a base de seções do explorador (crossfilter).
Depende de analise_v2.py (data/_amostra_v2.pkl) e analise_logs_v2.py (data/_logs_v2.pkl, data/_logs_all_v2.pkl).
Grava data/mece_v4.json (resumo) e a pasta ds4/ (arquivos do painel)."""
import json, math, os
from collections import Counter
import numpy as np, pandas as pd
import statsmodels.formula.api as smf

D = 'data/'; O = 'ds4/'
os.makedirs(O, exist_ok=True)
WEST_AM = {'AMATURÁ','ATALAIA DO NORTE','BENJAMIN CONSTANT','EIRUNEPÉ','ENVIRA','GUAJARÁ','IPIXUNA','ITAMARATI','JUTAÍ','SÃO PAULO DE OLIVENÇA','TABATINGA'}
def tz(uf, mun=''):
    m = str(mun).upper().strip()
    if uf == 'PE' and m == 'FERNANDO DE NORONHA': return -1
    if uf == 'AC' or (uf == 'AM' and m in WEST_AM): return 2
    if uf in ('AM','MS','MT','RO','RR'): return 1
    return 0
REGN = {'N': 'Norte', 'NE': 'Nordeste', 'CO': 'Centro-Oeste', 'SE': 'Sudeste', 'S': 'Sul'}

a = pd.read_pickle(D+'_amostra_v2.pkl')
both = pd.read_pickle(D+'_logs_v2.pkl'); S = pd.read_pickle(D+'_logs_all_v2.pkl')
P2 = json.load(open(D+'painel_v2.json')); LG = json.load(open(D+'logs_v2.json')); R3 = json.load(open(D+'robustez_v3.json'))
P1 = json.load(open(D+'painel_dados.json'))
m = pd.read_csv(D+'municipios_1t_2t.csv', dtype={'cd_mun': str})
br1 = json.load(open(D+'br_1t.json')); br2 = json.load(open(D+'br_2t.json'))
def cands(b):
    c = {}
    for ag in b['carg'][0]['agr']:
        for p in ag['par']:
            for cd in p['cand']: c[cd['n']] = int(cd['vap'])
    return c
c1, c2 = cands(br1), cands(br2)
NAC = {'aptos1': int(br1['e']['te']), 'aptos2': int(br2['e']['te']), 'comp1': int(br1['e']['c']), 'comp2': int(br2['e']['c']),
       'vv1': int(br1['v']['vv']), 'vv2': int(br2['v']['vv']), 'lula1': c1['13'], 'flavio1': c1['22'], 'lula2': c2['13'], 'flavio2': c2['22'],
       'bn1': int(br1['v']['vb'])+int(br1['v']['tvn']), 'bn2': int(br2['v']['vb'])+int(br2['v']['tvn'])}
MARGEM = NAC['lula2']-NAC['flavio2']
MEIA = MARGEM/2
OUT = {'nacional': NAC, 'margem': MARGEM, 'meia_margem': MEIA}
a['ww'] = a.w*a.vv_2t
a['cdm'] = a.uf+a.cd_mun
def fitc(f, d, coef):
    r = smf.wls(f, data=d, weights=d.ww).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(d.cdm)[0]})
    return float(r.params[coef]), float(r.bse[coef]), float(r.pvalues[coef])

# ============================================================ 1.1 eleitores novos entre turnos
OUT['c11'] = {'aptos1': NAC['aptos1'], 'aptos2': NAC['aptos2'], 'diff': NAC['aptos2']-NAC['aptos1'],
              'amostra_aptos1': int(a.aptos_1t.sum()), 'amostra_aptos2': int(a.aptos_2t.sum()),
              'secoes_iguais': float((a.aptos_1t == a.aptos_2t).mean()*100), 'secoes_ate1': float(((a.aptos_2t-a.aptos_1t).abs() <= 1).mean()*100)}
print('1.1', OUT['c11'])

# ============================================================ 1.2 urna "sem cadastro" acima do cadastro
a['semcad_n'] = (a.semcad_p/100*a.aptos_2t)
a['exc_b0'] = (a.b0_2t-a.semcad_n)
ok = a.semcad_n.notna()
exc = a.loc[ok, 'exc_b0'].clip(lower=0)
OUT['c12'] = {'n': int(ok.sum()), 'secoes_acima': int((a.loc[ok, 'exc_b0'] > 0).sum()), 'pct_acima': float((a.loc[ok, 'exc_b0'] > 0).mean()*100),
              'votos_acima_pais': float((exc*a.loc[ok, 'w']).sum()),
              'b0_sobre_cad_med': float(np.average((a.b0_2t/a.semcad_n.replace(0, np.nan)).dropna(), weights=a.loc[(a.semcad_n > 0), 'w'])),
              'corr': float(np.corrcoef(a.loc[ok, 'b0_2t'], a.loc[ok, 'semcad_n'])[0, 1]),
              'aptos_vs_perfil_corr': float(np.corrcoef(a.loc[ok, 'aptos_2t'], a.loc[ok, 'eleitores'])[0, 1]),
              'exc_med_secoes_acima': float(a.loc[ok & (a.exc_b0 > 0), 'exc_b0'].median()),
              'b0_total_pais': float((a.b0_2t*a.w).sum()), 'semcad_esperado_pais': float((a.semcad_n*a.w).sum()),
              'pct_b0_do_cadastro': float((a.b0_2t*a.w).sum()/(a.semcad_n*a.w).sum()*100)}
# mesma conta só onde o perfil tem o mesmo eleitorado da seção (sem agregação de seções)
cl = ok & ((a.eleitores-a.aptos_2t).abs() <= 2)
OUT['c12']['n_limpas'] = int(cl.sum()); OUT['c12']['acima_limpas'] = int((a.loc[cl, 'b0_2t'] > (a.loc[cl, 'semcad_p']/100*a.loc[cl, 'eleitores']).round()+0).sum())
print('1.2', OUT['c12'])
print(a.loc[ok & (a.exc_b0 > 0), ['uf','nm_mun','zona','secao','aptos_2t','eleitores','semcad_n','b0_2t','comp_2t']].sort_values('b0_2t').tail(8).to_string())

# ============================================================ logs: intervalos e tentativas
logs = [json.loads(l) for l in open(D+'amostra_aleatoria_logs.jsonl')]
A = {f'{r.uf}|{r.cd_mun}|{r.zona}|{r.secao}': r for r in a.itertuples()}
nlog_uf = Counter(l['uf'] for l in logs)
des = json.load(open(D+'amostra_aleatoria_desenho.json'))
N_uf = {k.upper(): v['N'] for k, v in des['por_uf'].items()}
IB = list(range(0, 305, 5))
hist = {1: np.zeros(len(IB)-1), 2: np.zeros(len(IB)-1)}
mins = {1: [], 2: []}; byt = {1: {'B': [], 'M': [], 'S': []}, 2: {'B': [], 'M': [], 'S': []}}
fast = {1: Counter(), 2: Counter()}
att = {1: Counter(), 2: Counter()}
n_int = {1: 0, 2: 0}
pos = {t: np.zeros(36) for t in (1, 2)}  # 16:30..19:30 em blocos de 5 min (BRT)
for l in logs:
    r = A.get(f"{l['uf']}|{l['cd_mun']}|{l['zona']}|{l['secao']}")
    off = tz(l['uf'], r.nm_mun if r is not None else '')*3600
    wl = N_uf[l['uf']]/nlog_uf[l['uf']]
    for t in (1, 2):
        d = np.array(l.get(f't{t}', []), dtype=np.int64); y = l.get(f'y{t}', ''); at = l.get(f'a{t}', '')
        if len(d) < 2: continue
        iv = d[1:]; ty = np.array(list(y))[1:]
        n_int[t] += len(iv)
        hist[t] += np.histogram(np.clip(iv, 0, 299.9), IB)[0]
        mins[t].append(int(iv.min()))
        for k in ('B', 'M', 'S'): byt[t][k].extend(iv[ty == k].tolist())
        fast[t]['lt10'] += int((iv < 10).sum()); fast[t]['lt15'] += int((iv < 15).sum()); fast[t]['lt20'] += int((iv < 20).sum())
        fast[t]['lt15_w'] += float((iv < 15).sum()*wl)
        for c, k in zip(y, at):
            if c == 'M': att[t][int(k)] += 1
        ts = (np.cumsum(d)+off)/60.0
        idx = np.floor((ts-(16*60+30))/5).astype(int)
        sel = (idx >= 0) & (idx < 36)
        pos[t] += np.bincount(idx[sel], minlength=36)*wl
OUT['logs_int'] = {t: {'n': n_int[t], 'min': int(min(mins[t])), 'lt10': fast[t]['lt10'], 'lt15': fast[t]['lt15'], 'lt20': fast[t]['lt20'],
                       'lt15_pais': fast[t]['lt15_w'],
                       'med_B': float(np.median(byt[t]['B'])), 'med_M': float(np.median(byt[t]['M'])), 'med_S': float(np.median(byt[t]['S']))} for t in (1, 2)}
OUT['att'] = {t: dict(sorted(att[t].items())) for t in (1, 2)}
print('intervalos', OUT['logs_int']); print('tentativas M', OUT['att'])

# ============================================================ 2.3 / 2.4 voto sem digital (robustez_v3)
te = R3['teto']; nt = R3['nivel_teto']
OUT['c23'] = {'delta': te['delta'], 'lo': te['lo'], 'hi': te['hi'], 'nb1': te['nb1'], 'nb2': te['nb2'],
              'slope': R3['obs']['xdL_mun']['est'], 'slope_se': R3['obs']['xdL_mun']['se'], 'slope_p': R3['obs']['xdL_mun']['p'],
              'v95_max': max(p['V95'] for p in R3['posterior']), 'v95_min': min(p['V95'] for p in R3['posterior'])}
OUT['c24'] = {'d_obs': nt['d_obs'], 'd_hi': nt['d_hi'], 'd_nec': nt['d_necessaria'], 'V_max': nt['V_max'], 'p_virar': nt['p_virar'],
              'V_pt': nt['d_obs']/((1-0.5179)*100)*te['nb2']}
print('2.3', OUT['c23'], '2.4', OUT['c24'])

# ============================================================ 3.1 urna trocada / 3.2 urna antiga
a['trocada'] = (a.urna_1t != a.urna_2t).astype(int)
b, se, p = fitc('xdL ~ trocada', a, 'trocada')
V = float((a.w*a.vv_2t)[a.trocada == 1].sum())
OUT['c31'] = {'pct_mesma': float(100-np.average(a.trocada, weights=a.w)*100), 'n_troc': int(a.trocada.sum()), 'est': b, 'se': se, 'p': p,
              'V': V, 'teto': max(0.0, b+1.96*se)/100*V}
a['antiga'] = (a.geracao == 'UE2015').astype(int)
b, se, p = fitc('xdL ~ antiga', a, 'antiga')
V = float((a.w*a.vv_2t)[a.antiga == 1].sum())
gen = {g['geracao']: g for g in P2['geracao']}
OUT['c32'] = {'est': b, 'se': se, 'p': p, 'V': V, 'teto': max(0.0, b+1.96*se)/100*V,
              'manual': {k: gen[k]['manual_1t'] for k in gen}, 'manual2': {k: gen[k]['manual_2t'] for k in gen}, 'xdL': {k: gen[k]['xdL'] for k in gen}}
print('3.1', OUT['c31'], '3.2', OUT['c32'])

# ============================================================ 4.1 log x boletim
Sx = S.merge(a[['uf','zona','secao','comp_2t','comp_1t']].assign(municipio=a.nm_mun.str.title()), on=['uf','municipio','zona','secao'], how='left')
mis = Sx[(Sx.n2 > 0)]
dif = (mis.comp_2t-mis.n2).abs()
OUT['c41'] = {'valid2': LG['valid2'], 'valid1': LG['valid1'], 'n': int(len(mis)), 'n_dif': int((dif > 0).sum()), 'votos_dif_amostra': int(dif.sum()),
              'votos_dif_pais': float((dif*mis.w).sum()), 'dif_max': int(dif.max())}
print('4.1', OUT['c41'])

# ============================================================ 4.2 último dígito (municípios, painel v1)
OUT['c42'] = P1['ultimo_digito']
# ============================================================ 4.3 enchimento de urna
hi95 = a.T2 >= 95
OUT['c43'] = {'pct_secoes_95': float(np.average(hi95, weights=a.w)*100), 'n95': int(hi95.sum()),
              'n95_extremo': int((hi95 & ((a.L2 >= 80) | (a.L2 <= 20))).sum()),
              'votos_acima95_pais': float((a.w*(a.comp_2t-0.95*a.aptos_2t).clip(lower=0)).sum()),
              'pct_secoes_90': float(np.average(a.T2 >= 90, weights=a.w)*100)}
print('4.3', OUT['c43'])

# ============================================================ 4.4 fluxo anômalo no log, só no 2º turno
def flags(d, t):
    return (((d[f'pre{t}'] >= 60) & (d[f'drop{t}'] >= 15) & (d[f'p_drop{t}'] < 0.05)) | (d[f'p_streak{t}'] < 0.05) |
            (d[f'sstreak{t}'] >= 5) | (d[f'mstreak{t}'] >= 6) | (d[f'z{t}'] <= -2))
f1, f2 = flags(both, 1), flags(both, 2)
so2 = both[f2 & ~f1]
wv = so2.w*so2.vv2
mu = float(np.average(so2.xdL, weights=wv)); sd = float(np.sqrt(np.average((so2.xdL-mu)**2, weights=wv)/len(so2)))
V = float((so2.w*so2.vv2).sum())
OUT['c44'] = {'pct1': float(np.average(f1, weights=both.w)*100), 'pct2': float(np.average(f2, weights=both.w)*100), 'n_so2': int(len(so2)),
              'xdL': mu, 'lo': mu-1.96*sd, 'hi': mu+1.96*sd, 'V': V, 'teto': max(0.0, mu+1.96*sd)/100*V, 'anom': LG['anomalias']}
print('4.4', {k: v for k, v in OUT['c44'].items() if k != 'anom'})

# ============================================================ 5.1 totalização (UF x municípios x nacional, conferido no computador do usuário)
tot = pd.read_csv(D+'_totalizacao_check.csv') if os.path.exists(D+'_totalizacao_check.csv') else None
OUT['c51'] = None
if tot is not None:
    OUT['c51'] = {'soma_uf_lula': int(tot.uf_lula.sum()), 'soma_uf_flavio': int(tot.uf_flavio.sum()), 'br_lula': NAC['lula2'], 'br_flavio': NAC['flavio2'],
                  'ufs_iguais': int(((tot.d_lula == 0) & (tot.d_flavio == 0)).sum()), 'ufs': int(len(tot)),
                  'dif_rs': int(abs(tot.d_lula).sum()+abs(tot.d_flavio).sum())}
    print('5.1', OUT['c51'])

# ============================================================ 6.1 votos depois das 17h (Brasília)
d17 = LG['depois17']
rng17 = np.random.default_rng(11); bt = {1: [], 2: []}
grp17 = [g for _, g in S.groupby('uf')]
for _ in range(500):
    bs = pd.concat([g.sample(len(g), replace=True, random_state=int(rng17.integers(1e9))) for g in grp17])
    for t in (1, 2): bt[t].append(float((bs[f'after17_{t}'].fillna(0)*bs.w).sum()))
for t in (1, 2):
    d17[str(t)]['lo'] = float(np.percentile(bt[t], 2.5)); d17[str(t)]['hi'] = float(np.percentile(bt[t], 97.5))
OUT['c61'] = {'v17_2': d17['2']['votos_pais'], 'lo2': d17['2']['lo'], 'hi2': d17['2']['hi'], 'v1705_2': d17['2']['votos_pais_1705'],
              'v17_1': d17['1']['votos_pais'], 'lo1': d17['1']['lo'], 'hi1': d17['1']['hi'], 'pct2': d17['2']['pct'],
              'bins': [{'ini': 16*60+30+5*i, 't1': float(pos[1][i]), 't2': float(pos[2][i])} for i in range(36)],
              'enc_t1_censo': P2['enc_nac']['t1_censo'], 'enc_t2': P2['enc_nac']['t2_amostra']}
print('6.1', {k: v for k, v in OUT['c61'].items() if k != 'bins'})

# ============================================================ 7.1 coerção / compra (caudas do ganho vs. cidade)
xb = np.arange(-15, 16, 1)
h = np.histogram(a.xdL.clip(-14.99, 14.99), xb, weights=a.w)[0]
OUT['c71'] = {'pos10': float(np.average(a.xdL >= 10, weights=a.w)*100), 'neg10': float(np.average(a.xdL <= -10, weights=a.w)*100),
              'pos5': float(np.average(a.xdL >= 5, weights=a.w)*100), 'neg5': float(np.average(a.xdL <= -5, weights=a.w)*100),
              'n_pos10': int((a.xdL >= 10).sum()), 'n_neg10': int((a.xdL <= -10).sum()),
              'hist': [{'x': int(xb[i]), 'w': float(h[i])} for i in range(len(h))]}
print('7.1', {k: v for k, v in OUT['c71'].items() if k != 'hist'})

# ============================================================ sinais apontados no resultado
q = P1['queda_absoluta']
mb = m[m.uf != 'ZZ'].copy()
nove = ['AC','AM','AP','MA','PA','PI','RO','RR','TO']
x = mb[mb.uf.isin(nove)].copy()
x['dT'] = (x.comp_2t/x.aptos_2t-x.comp_1t/x.aptos_1t)*100
x['dF'] = (x.flavio_2t/x.vv_2t-x.flavio_1t/x.vv_1t)*100
OUT['s1'] = {'real': q['real_F'], 'sim': q['sim_F'], 'real_vv': q['real_F_vvsobe'], 'sim_vv': q['sim_F_vvsobe']}
OUT['s2'] = {'n': P1['hiper']['lula_n'], 'n_1t80': P1['hiper']['lula_n_1t85'], 'flavio': P1['hiper']['flavio_n'], 'lista': P1['hiper']['lula']}
OUT['s3'] = {'corr': float(np.corrcoef(x.dT, x.dF)[0, 1]), 'n': int(len(x))}
print('sinais', OUT['s1'], OUT['s3'])

# ============================================================ explicação: o saldo do 2º turno
pool = (NAC['vv1']-NAC['lula1']-NAC['flavio1'])+(NAC['vv2']-NAC['vv1'])
OUT['saldo'] = {'terceira': NAC['vv1']-NAC['lula1']-NAC['flavio1'], 'novos_validos': NAC['vv2']-NAC['vv1'], 'pool': pool,
                'd_lula': NAC['lula2']-NAC['lula1'], 'd_flavio': NAC['flavio2']-NAC['flavio1'],
                'd_comp': NAC['comp2']-NAC['comp1'], 'd_bn': NAC['bn2']-NAC['bn1']}
print('saldo', OUT['saldo'])
a.to_pickle(D+'_amostra_v4.pkl')
json.dump(OUT, open(D+'mece_v4.json', 'w'), ensure_ascii=False, default=float)
print('ok')
