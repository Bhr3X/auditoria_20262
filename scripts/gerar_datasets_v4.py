# -*- coding: utf-8 -*-
"""Arquivos do painel visual MECE (ds4/). Depende de analise_v4_mece.py."""
import json, math, os
import numpy as np, pandas as pd

D = 'data/'; O = 'ds4/'
os.makedirs(O, exist_ok=True)
M = json.load(open(D+'mece_v4.json')); R3 = json.load(open(D+'robustez_v3.json')); P1 = json.load(open(D+'painel_dados.json'))
a = pd.read_pickle(D+'_amostra_v4.pkl')
both = pd.read_pickle(D+'_logs_v2.pkl')
NAC = M['nacional']; MARGEM = M['margem']; MEIA = M['meia_margem']
BR2 = json.load(open(D+'br_2t.json'))

def r(x, k=4):
    if x is None: return None
    if isinstance(x, (bool, np.bool_)): return bool(x)
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (float, np.floating)):
        if math.isnan(x) or math.isinf(x): return None
        return round(float(x), k)
    return x
def save(name, rows, k=4):
    rows = [{kk: r(v, k) for kk, v in row.items()} for row in rows]
    json.dump(rows, open(O+name+'.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print(f'{name:12s} {len(rows):6d} linhas {os.path.getsize(O+name+".json")/1e3:8.1f} KB')
def fi(x): return f'{int(round(x)):,}'.replace(',', '.')
def f1(x): return f'{x:.1f}'.replace('.', ',')
def f2(x): return f'{x:.2f}'.replace('.', ',')
def f3(x): return f'{x:.3f}'.replace('.', ',')
def sg(x, f=f2): return ('+' if x > 0 else '−' if x < 0 else '') + f(abs(x))
def mi(x): return f2(x/1e6) + ' mi'
def mil(x): return (fi(x/1e3) if x >= 10e3 else f1(x/1e3)) + ' mil'

c = {k: M[k] for k in M}
c11, c12, c23, c24, c31, c32, c41, c43, c44, c51, c61, c71 = (c[k] for k in ['c11','c12','c23','c24','c31','c32','c41','c43','c44','c51','c61','c71'])
li = c['logs_int']; att = c['att']; s1, s2, s3 = c['s1'], c['s2'], c['s3']; sal = c['saldo']
dig = c['c42']
from scipy.stats import chisquare
mun = pd.read_csv(D+'municipios_1t_2t.csv', dtype={'cd_mun': str}); mun = mun[mun.uf != 'ZZ'].copy()
mun['L1'] = mun.lula_1t/mun.vv_1t*100; mun['L2'] = mun.lula_2t/mun.vv_2t*100
GN = (mun.lula_2t.sum()/mun.vv_2t.sum()-mun.lula_1t.sum()/mun.vv_1t.sum())*100
hip = mun[mun.L2 >= 88].sort_values('L2', ascending=False)
lmin = float((hip.L2-hip.L1).min()); lmax = float((hip.L2-hip.L1).max()); n_acima_gn = int(((hip.L2-hip.L1) > GN).sum())
top_gn = hip.loc[(hip.L2-hip.L1).idxmax()]
NLOG2 = sum(1 for l in open(D+'amostra_aleatoria_logs.jsonl') if len(json.loads(l).get('t2', [])) > 0)
R3T = 3/NLOG2*NAC['comp2']          # regra de três: 0 urnas com o problema em NLOG2 sorteadas
DS = {}
for col in ['lula_2t', 'flavio_2t', 'lula_1t', 'flavio_1t']:
    v = a[col][a[col] >= 30].astype(int); cnt = np.bincount(v % 10, minlength=10)
    DS[col] = {'cont': cnt.tolist(), 'n': int(len(v)), 'p': float(chisquare(cnt).pvalue)}
nn = mun[mun.uf.isin(['AC','AM','AP','MA','PA','PI','RO','RR','TO'])]
corr_abs = float(np.corrcoef(nn.comp_2t/nn.aptos_2t-nn.comp_1t/nn.aptos_1t, nn.flavio_2t-nn.flavio_1t)[0, 1])
print('NLOG2', NLOG2, 'R3T', R3T, 'hiper', len(hip), lmin, lmax, n_acima_gn, top_gn.nm_mun, 'GN', GN, 'corr_abs', corr_abs, {k: round(v['p'], 3) for k, v in DS.items()})

EST = [('1', 'Cadastro', 'Quem pode votar'), ('2', 'Mesa', 'Quem é liberado para votar'), ('3', 'Urna', 'Como o voto é gravado'),
       ('4', 'Arquivos', 'Como o voto é contado'), ('5', 'Totalização', 'Como os votos são somados'), ('6', 'Horário', 'Quando se votou'),
       ('7', 'Eleitor', 'Por que o eleitor votou assim'), ('8', 'Sinais', 'Padrões apontados no resultado')]
E = {e[0]: e for e in EST}
casos = []
def add(id_, nome, ver, forca, frase, tecnico, visual, teto=None, teto_pt=None, limiar='margem', lo=None):
    est = id_.split('.')[0]
    L = MARGEM if limiar == 'margem' else MEIA
    casos.append({'id': id_, 'ordem': len(casos)+1, 'estagio': est, 'estagio_nome': E[est][1], 'estagio_pergunta': E[est][2],
                  'nome': nome, 'veredito': ver, 'forca': forca, 'frase': frase, 'tecnico': tecnico, 'visual': visual,
                  'teto': teto, 'teto_pt': teto_pt if teto_pt is not None else teto, 'teto_lo': lo,
                  'limiar': limiar, 'limiar_votos': L,
                  'pct': (teto/L*100) if teto is not None else None, 'pct_pt': ((teto_pt if teto_pt is not None else teto)/L*100) if teto is not None else None,
                  'mede': teto is not None})

add('1.1', 'Eleitores novos entre turnos', 'Excluído', 'direto',
    f"Eleitorado idêntico nos dois turnos: {fi(c11['aptos1'])}.",
    f"Total oficial de aptos do TSE: {fi(c11['aptos1'])} no 1º e {fi(c11['aptos2'])} no 2º turno. Na amostra de 9.600 seções, {f1(c11['secoes_ate1'])}% variaram no máximo 1 eleitor (soma {fi(c11['amostra_aptos1'])} → {fi(c11['amostra_aptos2'])}).",
    'aptos', teto=0)
add('1.2', 'Urna liberando mais "sem digital" que o cadastro', 'Excluído', 'estatístico',
    f"Cabe no cadastro em {f1(100-c12['pct_acima'])}% das seções; excesso típico de 1 eleitor.",
    f"Contador 'sem biometria' do boletim do 2º turno × eleitores sem biometria no perfil do eleitorado do TSE (julho/2026), na mesma seção. Excesso em {f1(c12['pct_acima'])}% das seções, mediana de {fi(c12['exc_med_secoes_acima'])} eleitor (o cadastro muda entre julho e outubro). Todo o excesso, expandido para o país: {fi(c12['votos_acima_pais'])} votos, teto mesmo se todos fossem falsos.",
    'cadastro', teto=c12['votos_acima_pais'])
n2m = sum(att['2'].values()); n1m = sum(att['1'].values()); q4_2 = att['2'].get('4', 0)
add('2.1', 'Liberação manual sem tentar a digital', 'Excluído', 'estatístico',
    f"{fi(q4_2)} de {fi(n2m)} liberações manuais tiveram as 4 tentativas.",
    f"Logs aleatórios de 3.000 urnas: para cada eleitor liberado manualmente, contamos os eventos 'Solicita digital. Tentativa'. 100% tiveram exatamente 4 tentativas antes da liberação, no 2º turno ({fi(q4_2)}) e no 1º ({fi(att['1'].get('4', 0))} de {fi(n1m)}). Zero na amostra não é zero no país: pela regra de três, até 3 em {fi(NLOG2)} urnas (0,1%) poderiam ter o problema sem aparecer, o que dá um teto conservador de {fi(R3T)} votos, contando todos os votos dessas urnas.",
    'tentativas', teto=R3T, teto_pt=0)
add('2.2', 'Rajada de votos (enchimento rápido)', 'Excluído', 'estatístico',
    f"Nenhum voto a menos de {li['2']['min']} segundos do anterior.",
    f"{fi(li['2']['n'])} intervalos entre votos consecutivos no 2º turno (3.000 urnas). Mínimo {li['2']['min']} s; {li['2']['lt15']} abaixo de 15 s. Mediana: {fi(li['2']['med_B'])} s com digital, {fi(li['2']['med_S'])} s sem cadastro, {fi(li['2']['med_M'])} s com liberação manual. Pela regra de três, até 0,1% das urnas poderia ter rajadas sem aparecer na amostra: teto conservador de {fi(R3T)} votos. O teste só vê votos em rajada; votos inseridos no ritmo normal apareceriam como eleitores a mais (1.1, 4.1) e como aumento de voto sem digital (2.3).",
    'intervalos', teto=R3T, teto_pt=0)
add('2.3', 'Voto sem digital inflando Lula no 2º turno', 'Excluído', 'estatístico',
    f"Aumento de {mi(c23['delta'])} votos sem digital (teto {mi(c23['hi'])}) e nenhum efeito no voto de Lula.",
    f"Aumento de votos sem digital do 1º para o 2º turno, expandido para o país pela amostra aleatória: {fi(c23['delta'])} (IC 95% {fi(c23['lo'])} a {fi(c23['hi'])}). Mesmo se todos fossem falsos e de Lula, seriam {f1(c23['hi']/MARGEM*100)}% da margem. Nas mesmas seções, +1 p.p. de voto sem digital muda o ganho de Lula vs. a própria cidade em {sg(c23['slope'], f3)} p.p. (p = {f2(c23['slope_p'])}). Fraude injetada nos dados reais é detectada a partir de 200 mil a 1 milhão de votos, conforme o padrão.",
    'semdigital', teto=c23['hi'], teto_pt=c23['delta'], lo=c23['lo'])
add('2.4', 'O mesmo esquema já no 1º turno', 'Improvável', 'indireto',
    f"Melhor estimativa {mi(c24['V_pt'])}; nem no extremo ({mi(c24['V_max'])}) vira.",
    f"Se o esquema existisse nos dois turnos, a comparação entre turnos não o veria. Teste de nível: diferença de % de Lula entre eleitores sem e com digital, mesma UF e mesmo perfil de idade e escolaridade: {sg(c24['d_obs'], f1)} p.p. (IC até {sg(c24['d_hi'], f1)}). Para virar seria preciso {sg(c24['d_nec'], f1)} p.p. No extremo do IC caberiam {mi(c24['V_max'])} votos falsos; chance de virar dentro do modelo: {f2(c24['p_virar']*100)}%. Essa chance não inclui o erro do próprio método (inferência ecológica, o teste mais fraco do painel), por isso o veredito é Improvável, não Excluído.",
    'nivel', teto=c24['V_max'], teto_pt=c24['V_pt'])
add('2.5', 'Digital de outra pessoa (biometria falsa)', 'Possível', 'fora',
    "Os arquivos só registram que a digital bateu com o cadastro.",
    "O log registra 'habilitação biométrica' quando a digital confere com a cadastrada. Detectar digital falsificada exige perícia nas digitais coletadas pelo TSE, que não estão nesta pasta. Nenhum indício nos dados, e nenhum teste possível com eles.",
    'lacuna')
add('3.1', 'Urna trocada entre os turnos', 'Excluído', 'estatístico',
    f"{f1(c31['pct_mesma'])}% usaram a mesma urna; as trocadas votaram igual.",
    f"{c31['n_troc']} das 9.600 seções da amostra trocaram de urna entre os turnos. Ganho de Lula vs. a própria cidade nelas: {sg(c31['est'])} p.p. (IC {sg(c31['est']-1.96*c31['se'])} a {sg(c31['est']+1.96*c31['se'])}; p = {f2(c31['p'])}). Teto: {fi(c31['teto'])} votos movidos.",
    'troca', teto=c31['teto'], limiar='meia')
add('3.2', 'Urnas antigas puxando voto', 'Excluído', 'estatístico',
    "UE2015 falham mais na digital, mas votam igual.",
    f"Censo do 1º turno: liberação manual de {f1(c32['manual']['UE2015'])}% nas UE2015, contra {f1(c32['manual']['UE2020'])}% nas UE2020 e {f1(c32['manual']['UE2022'])}% nas UE2022 (leitor mais antigo). Ganho de Lula vs. a própria cidade nas UE2015: {sg(c32['est'])} p.p. (IC {sg(c32['est']-1.96*c32['se'])} a {sg(c32['est']+1.96*c32['se'])}; p = {f2(c32['p'])}). Teto: {fi(c32['teto'])} votos movidos.",
    'geracao', teto=c32['teto'], limiar='meia')
add('3.3', 'Software trocando votos', 'Possível', 'fora',
    "Troca feita pelo programa só aparece em auditoria de código.",
    "Uma troca proporcional feita pelo programa, igual em todas as urnas, não deixa rastro estatístico. Os testes de forma deste painel (último dígito, persistência entre turnos) não acusam nada, mas não bastam. A prova vem do teste de integridade do TSE e da verificação de assinaturas do software, que não estão nesta pasta.",
    'lacuna')
v2 = c41['valid2']
add('4.1', 'Log da urna diferente do boletim', 'Excluído', 'estatístico',
    f"Bate em {f1(v2['okN'])}% das urnas; quase todas as diferenças são urnas substituídas.",
    f"Contagem de eleitores no log × comparecimento do boletim, 2º turno, 3.000 urnas: {f2(v2['okN'])}% iguais (digital {f2(v2['okB'])}%, manual {f2(v2['okM'])}%, sem cadastro {f2(v2['okS'])}%). As {c41['n_dif']} diferenças são logs com menos eleitores que o boletim: 10 delas são urnas que só começaram a gravar no meio da manhã e mudaram de urna entre os turnos (urna substituída; os primeiros eleitores ficaram no log da urna retirada), e 1 difere em 1 eleitor. Expandido para o país: {fi(c41['votos_dif_pais'])} votos, teto mesmo se todos fossem falsos.",
    'logbu', teto=c41['votos_dif_pais'])
add('4.2', 'Números fabricados no boletim', 'Excluído', 'estatístico',
    "Últimos dígitos dos boletins uniformes nos dois turnos.",
    f"Qui-quadrado do último dígito dos votos por seção na amostra (seções com 30+ votos no candidato): Lula 2º p = {f2(DS['lula_2t']['p'])}; Flávio 2º p = {f2(DS['flavio_2t']['p'])}; Lula 1º p = {f2(DS['lula_1t']['p'])}; Flávio 1º p = {f2(DS['flavio_1t']['p'])}. Nos totais municipais (sem o exterior): {f2(dig['lula2']['p'])} e {f2(dig['flavio2']['p'])}. Detecta números escritos à mão; não detecta troca proporcional (3.3). Cortes altos (100+) distorcem o teste, porque há mais seções com 100 do que com 109 votos.",
    'digitos')
add('4.3', 'Enchimento de urna', 'Excluído', 'estatístico',
    f"Só {f2(c43['pct_secoes_95'])}% das seções passaram de 95% de comparecimento.",
    f"Enchimento aparece como seções com comparecimento e % do vencedor perto de 100% ao mesmo tempo. Na amostra: {c43['n95']} seções com 95%+ de comparecimento, {c43['n95_extremo']} com um candidato acima de 80%. Votos acima de 95% de comparecimento, expandidos para o país: {fi(c43['votos_acima95_pais'])}.",
    'enchimento', teto=c43['votos_acima95_pais'])
add('4.4', 'Fluxo anômalo de eleitores no log', 'Excluído', 'estatístico',
    "Anomalias com a mesma frequência nos dois turnos.",
    f"Quedas de biometria e sequências sem digital que o acaso não explica (teste de permutação), sequências de liberação manual e de 'não pediu digital', agrupamento (runs): {f1(c44['pct1'])}% das urnas no 1º turno e {f1(c44['pct2'])}% no 2º. Nas {c44['n_so2']} urnas em que surgiram só no 2º, ganho de Lula vs. a própria cidade: {sg(c44['xdL'])} p.p. (IC {sg(c44['lo'])} a {sg(c44['hi'])}). Teto: {fi(c44['teto'])} votos movidos.",
    'anomalias', teto=c44['teto'], limiar='meia')
add('5.1', 'Soma diferente do total oficial', 'Excluído', 'direto',
    "Soma das UFs = total oficial, voto a voto.",
    f"Os 28 arquivos de UF do TSE (27 UFs + exterior, na pasta eleicoes) somam exatamente {fi(c51['soma_uf_lula'])} para Lula e {fi(c51['soma_uf_flavio'])} para Flávio, o total nacional. As cidades somam o total da UF em 27 de 28 arquivos; no RS faltam {c51['dif_rs']} votos porque o arquivo municipal foi baixado antes de 2 seções de Colinas entrarem. O total nacional ainda tem {fi(int(BR2['s']['snt']))} seções pendentes ({fi(int(BR2['e']['esnt']))} eleitores aptos).",
    'totalizacao', teto=0)
add('6.1', 'Votos depois do horário (prorrogação)', 'Excluído', 'estatístico',
    f"≈{mil(c61['v17_2'])} votos depois das 17h; no 1º turno, {mi(c61['v17_1'])}.",
    f"Logs aleatórios, horário de Brasília: {fi(c61['v17_2'])} votos após 17h00 no país (IC {fi(c61['lo2'])} a {fi(c61['hi2'])}), {fi(c61['v1705_2'])} após 17h05. No 1º turno, com filas maiores: {fi(c61['v17_1'])}. Seções encerradas após 17h15: {f1(c61['enc_t2'])}% no 2º turno e {f1(c61['enc_t1_censo'])}% no 1º (censo). A legalidade da prorrogação é questão jurídica, fora deste painel.",
    'pos17', teto=c61['hi2'], teto_pt=c61['v17_2'], lo=c61['lo2'])
add('7.1', 'Coerção ou compra de voto', 'Possível', 'fora',
    "Sem sinal: saltos extremos aparecem dos dois lados.",
    f"Coerção e compra de voto acontecem fora da urna: o eleitor real vota com a própria digital e os arquivos ficam normais. O rastro possível seria um salto de voto concentrado em poucas seções. Seções com ganho de Lula 10 p.p. acima da própria cidade: {f2(c71['pos10'])}%; 10 p.p. abaixo: {f2(c71['neg10'])}%. Simétrico, mas o dado não mede pressão sobre o eleitor.",
    'caudas')
add('8.1', 'Flávio perdeu votos em 939 cidades', 'Excluído', 'estatístico',
    f"O esperado pelo acaso era {fi(s1['sim'][0])} a {fi(s1['sim'][2])}.",
    f"Simulação: cada município recebe a variação média da sua UF mais uma variação local sorteada da distribuição real (500 sorteios). Faixa de 95%: {fi(s1['sim'][0])} a {fi(s1['sim'][2])} cidades com queda de Flávio; real: {fi(s1['real'])}. A queda absoluta é aritmética: Lula subiu 6,6 p.p. e Flávio 1,2 p.p. no país.",
    'defeccao')
add('8.2', '37 cidades com 88%+ para Lula', 'Excluído', 'direto',
    f"Todas já davam 80%+ a Lula no 1º turno.",
    f"Municípios com 88% ou mais para Lula no 2º turno: {len(hip)} ({s2['flavio']} para Flávio), todos com 80%+ já no 1º turno. É a concentração regional conhecida do sertão nordestino. O ganho nelas foi de {sg(lmin, f1)} a {sg(lmax, f1)} p.p.; só {n_acima_gn} ({top_gn.nm_mun.title()}, {sg(lmax, f1)}) ganhou mais que o ganho nacional de {sg(GN, f1)} p.p.",
    'hiper')
add('8.3', 'Comparecimento caiu no Norte; só Flávio perdeu', 'Excluído', 'estatístico',
    "Onde o comparecimento caiu mais, a fatia de Flávio não caiu mais.",
    f"{fi(s3['n'])} municípios das 9 UFs em que o comparecimento caiu (AC, AM, AP, MA, PA, PI, RO, RR, TO): correlação entre a variação de comparecimento e a variação da % de Flávio = {f2(s3['corr'])}. Em votos absolutos a correlação é {f2(corr_abs)}, como para qualquer candidato: onde menos gente vota, todos perdem votos. Por isso o teste usa a fatia.",
    'norte')
save('casos', casos)

# ============================================================ provas (dados das miniaturas)
pv = []
def P(caso, k, rot='', v=None, v2=None, lo=None, hi=None, n=None): pv.append({'caso': caso, 'k': k, 'rotulo': rot, 'v': v, 'v2': v2, 'lo': lo, 'hi': hi, 'n': n})
P('nac', 'margem', 'Margem de Lula', MARGEM); P('nac', 'secoes_pend', 'Seções pendentes na totalização', int(BR2['s']['snt']), int(BR2['s']['ts'])); P('nac', 'aptos_pend', 'Aptos nas seções pendentes', int(BR2['e']['esnt'])); P('nac', 'meia', 'Metade da margem', MEIA)
P('nac', 'lula2', 'Lula, 2º turno', NAC['lula2']); P('nac', 'flavio2', 'Flávio, 2º turno', NAC['flavio2'])
P('nac', 'lula1', 'Lula, 1º turno', NAC['lula1']); P('nac', 'flavio1', 'Flávio, 1º turno', NAC['flavio1'])
P('nac', 'pct_lula2', '% Lula 2º', NAC['lula2']/NAC['vv2']*100); P('nac', 'pct_flavio2', '% Flávio 2º', NAC['flavio2']/NAC['vv2']*100)
P('nac', 'fator1', 'Fator de expansão do 1º turno', NAC['comp1']/float((a.w*a.comp_1t).sum()))
P('nac', 'fator2', 'Fator de expansão do 2º turno', NAC['comp2']/float((a.w*a.comp_2t).sum()))
P('1.1', 't1', '1º turno', c11['aptos1']); P('1.1', 't2', '2º turno', c11['aptos2'])
P('1.2', 'dentro', 'Dentro do previsto pelo cadastro', 100-c12['pct_acima']); P('1.2', 'acima', 'Acima do cadastro', c12['pct_acima'])
P('1.2', 'exc_med', 'Excesso típico (eleitores)', c12['exc_med_secoes_acima']); P('1.2', 'secoes_acima', 'Seções acima', c12['secoes_acima'], None, n=c12['n'])
for k in range(0, 5): P('2.1', f'a{k}', f'{k} tentativas', att['2'].get(str(k), 0), att['1'].get(str(k), 0), n=k)
IB = list(range(0, 240, 5))
logs = [json.loads(l) for l in open(D+'amostra_aleatoria_logs.jsonl')]
h2 = np.zeros(len(IB)); h1 = np.zeros(len(IB)); ov = {1: 0, 2: 0}; tot = {1: 0, 2: 0}
for l in logs:
    for t, hh in ((2, h2), (1, h1)):
        d = np.array(l.get(f't{t}', []), dtype=np.int64)
        if len(d) > 1:
            d = d[1:]; hh += np.histogram(d[d < 240], np.arange(0, 245, 5))[0]; ov[t] += int((d >= 240).sum()); tot[t] += len(d)
for i, x in enumerate(IB): P('2.2', f's{x}', f'{x}–{x+5} s', h2[i], h1[i], n=x)
P('2.2', 'acima240', 'Intervalos de 4 min ou mais', ov[2], ov[1]); P('2.2', 'total', 'Intervalos medidos', tot[2], tot[1])
P('2.2', 'lt15', 'Abaixo de 15 s', li['2']['lt15'], li['1'].get('lt15'))
print('intervalos', tot, li['2']['n'], li['1']['n'], 'min hist', [IB[i] for i in range(len(IB)) if h2[i] > 0][:2])
P('2.2', 'min', 'Menor intervalo', li['2']['min'], li['1']['min'])
for p in R3['poder']: P('2.3', f"{p['padrao']}_{p['V']}", p['rotulo'], p['V'], p['poder'])
P('2.3', 'slope', 'Efeito no ganho de Lula vs. cidade (p.p. por p.p. sem digital)', c23['slope'], None, c23['slope']-1.96*c23['slope_se'], c23['slope']+1.96*c23['slope_se'])
P('2.3', 'aumento', 'Aumento de votos sem digital', c23['delta'], None, c23['lo'], c23['hi'])
for x in R3['nivel']: P('2.4', x['id'], x['rotulo'], x['est'], None, x['lo'], x['hi'])
P('2.4', 'necessario', 'Necessário para virar', c24['d_nec'])
P('3.1', 'mesma', 'Mesma urna', c31['pct_mesma']); P('3.1', 'efeito', 'Ganho de Lula vs. cidade nas trocadas', c31['est'], None, c31['est']-1.96*c31['se'], c31['est']+1.96*c31['se'])
for g in ['UE2015', 'UE2020', 'UE2022']: P('3.2', g, g, c32['manual'][g], c32['xdL'][g])
P('3.2', 'efeito', 'Ganho de Lula vs. cidade, UE2015', c32['est'], None, c32['est']-1.96*c32['se'], c32['est']+1.96*c32['se'])
for k, rot in [('okB', 'Digital'), ('okM', 'Manual'), ('okS', 'Sem cadastro'), ('okN', 'Total de eleitores')]: P('4.1', k, rot, v2[k], c41['valid1'][k])
for key, rot in [('lula_2t', 'Lula · 2º turno'), ('flavio_2t', 'Flávio · 2º turno')]:
    for dgt, cnt in enumerate(DS[key]['cont']): P('4.2', f'{key}_{dgt}', rot, cnt, DS[key]['p'], n=dgt)
for x in c44['anom']: P('4.4', x['id'], x['anomalia'], x['t1'], x['t2'])
tot = pd.read_csv(D+'_totalizacao_check.csv')
for x in tot.itertuples(): P('5.1', x.uf, x.uf, abs(x.d_lula)+abs(x.d_flavio), x.uf_lula+x.uf_flavio)
for x in c61['bins']: P('6.1', f"m{x['ini']}", '', x['t2'], x['t1'], n=x['ini'])
P('8.1', 'real', 'Cidades onde Flávio perdeu votos', s1['real'], None, s1['sim'][0], s1['sim'][2], n=s1['sim'][1])
P('8.1', 'real_vv', 'Perdeu votos mesmo com mais votos válidos', s1['real_vv'], None, s1['sim_vv'][0], s1['sim_vv'][2], n=s1['sim_vv'][1])
for h in c71['hist']: P('7.1', f"h{h['x']}", '', h['w'], None, n=h['x'])
for k, rot in [('pos10', '10 p.p.+ acima da cidade'), ('neg10', '10 p.p.+ abaixo da cidade'), ('pos5', '5 p.p.+ acima'), ('neg5', '5 p.p.+ abaixo')]: P('7.1', k, rot, c71[k], None, n=c71.get('n_'+k))
P('4.3', 'n95', 'Seções com 95%+ de comparecimento', c43['n95']); P('4.3', 'n95_extremo', 'Com um candidato acima de 80%', c43['n95_extremo'])
for x in hip.itertuples(): P('8.2', x.cd_mun, f"{x.nm_mun.title()} ({x.uf})", x.L1, x.L2)
P('8.2', 'ganho_nac', 'Ganho nacional de Lula (p.p.)', GN)
P('8.2', 'n', 'Municípios com 88%+', s2['n']); P('8.2', 'n_1t80', 'Já com 80%+ no 1º turno', s2['n_1t80'])
P('saldo', 'terceira', 'Votos dos outros candidatos no 1º turno', sal['terceira']); P('saldo', 'novos', 'Votos válidos a mais no 2º turno', sal['novos_validos'])
P('saldo', 'lula', 'Ganho de Lula', sal['d_lula']); P('saldo', 'flavio', 'Ganho de Flávio', sal['d_flavio'])
P('saldo', 'comp', 'Comparecimento a mais', sal['d_comp']); P('saldo', 'bn', 'Brancos e nulos a menos', -sal['d_bn'])
save('provas', pv)

# municípios do Norte (8.3)
m = pd.read_csv(D+'municipios_1t_2t.csv', dtype={'cd_mun': str})
x = m[m.uf.isin(['AC','AM','AP','MA','PA','PI','RO','RR','TO'])].copy()
x['dT'] = (x.comp_2t/x.aptos_2t-x.comp_1t/x.aptos_1t)*100; x['dF'] = (x.flavio_2t/x.vv_2t-x.flavio_1t/x.vv_1t)*100
save('norte', [{'cd': z.cd_mun, 'municipio': z.nm_mun.title(), 'uf': z.uf, 'dT': z.dT, 'dF': z.dF, 'vv': int(z.vv_2t)} for z in x.itertuples()], 3)

# ============================================================ seções (explorador)
mm = m.set_index(['uf', 'cd_mun'])
a['aptos_mun'] = [mm.aptos_2t.get((u, cdm), np.nan) for u, cdm in zip(a.uf, a.cd_mun)]
key = lambda d: d.uf+'|'+d.municipio.str.upper()+'|'+d.zona+'|'+d.secao
def fl(d, t):
    return (((d[f'pre{t}'] >= 60) & (d[f'drop{t}'] >= 15) & (d[f'p_drop{t}'] < 0.05)) | (d[f'p_streak{t}'] < 0.05) |
            (d[f'sstreak{t}'] >= 5) | (d[f'mstreak{t}'] >= 6) | (d[f'z{t}'] <= -2))
bk = both.assign(k=both.uf+'|'+both.municipio.str.upper()+'|'+both.zona+'|'+both.secao, f1=fl(both, 1), f2=fl(both, 2))
logst = {}
for z in bk.itertuples():
    logst[z.k] = 3 if (z.f2 and not z.f1) else (2 if z.f1 or z.f2 else 1)
a['k'] = a.uf+'|'+a.nm_mun.str.upper()+'|'+a.zona+'|'+a.secao
def cut(v, edges):
    if v is None or (isinstance(v, float) and math.isnan(v)): return None
    for i, e in enumerate(edges):
        if v < e: return i
    return len(edges)
DIMS = [
 ('reg', 'Onde', 'Região', ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']),
 ('porte', 'Onde', 'Tamanho da cidade', ['Capital', '100 mil+ eleitores', '20–100 mil', 'Até 20 mil']),
 ('forca', 'Onde', 'Lula no 1º turno, na cidade', ['Até 40%', '40–55%', '55%+']),
 ('gov', 'Onde', '2º turno para governador', ['Teve', 'Não teve']),
 ('nb', 'Biometria', 'Sem digital no 2º turno', ['Até 5%', '5–10%', '10–15%', '15–25%', '25%+']),
 ('dnb', 'Biometria', 'Sem digital, 1º → 2º', ['Caiu 1 p.p.+', 'Estável', 'Subiu 1–3 p.p.', 'Subiu 3 p.p.+']),
 ('man', 'Biometria', 'Liberação manual (2º)', ['Até 3%', '3–6%', '6–10%', '10%+']),
 ('scad', 'Biometria', 'Sem cadastro (2º)', ['Até 2%', '2–5%', '5–10%', '10%+']),
 ('urna', 'Urna', 'Geração da urna', ['UE2015', 'UE2020', 'UE2022']),
 ('troca', 'Urna', 'Urna entre turnos', ['Mesma', 'Trocada']),
 ('enc', 'Urna', 'Encerramento (2º)', ['Até 17h05', '17h05–17h15', 'Depois 17h15']),
 ('log', 'Urna', 'Log da urna', ['Sem log na amostra', 'Normal', 'Anomalia no 1º', 'Anomalia só no 2º']),
 ('idade', 'Eleitor', 'Eleitores com 70+', ['Até 5%', '5–9%', '9–15%', '15%+']),
 ('esc', 'Eleitor', 'Até fundamental incompleto', ['Até 20%', '20–30%', '30–43%', '43%+']),
 ('comp', 'Eleitor', 'Comparecimento (2º)', ['Até 75%', '75–80%', '80–85%', '85%+']),
 ('dcomp', 'Eleitor', 'Comparecimento, 1º → 2º', ['Caiu 2 p.p.+', 'Caiu até 2', 'Subiu até 2', 'Subiu 2 p.p.+']),
]
REGN = {'N': 0, 'NE': 1, 'CO': 2, 'SE': 3, 'S': 4}
GOV = {'AC', 'AM', 'DF', 'ES', 'RN', 'TO'}
URN = {'UE2015': 0, 'UE2020': 1, 'UE2022': 2}
rows = []
for z in a.itertuples():
    porte = 0 if z.capital == 's' else cut(z.aptos_mun, [20000, 100000])
    porte = 0 if z.capital == 's' else (1 if z.aptos_mun >= 100000 else (2 if z.aptos_mun >= 20000 else 3))
    dnb = z.dnb
    rows.append({
        'uf': z.uf, 'reg': REGN[z.reg], 'porte': porte, 'forca': cut(z.mL1, [40, 55]), 'gov': 0 if z.uf in GOV else 1,
        'nb': cut(z.nbp_2t, [5, 10, 15, 25]), 'dnb': 0 if dnb < -1 else (1 if dnb <= 1 else (2 if dnb < 3 else 3)),
        'man': cut(z.b2p_2t, [3, 6, 10]), 'scad': cut(z.b0p_2t, [2, 5, 10]), 'urna': URN.get(z.geracao, 1), 'troca': int(z.trocada),
        'enc': None if math.isnan(z.enc2) else (0 if z.enc2 <= 17*60+5 else (1 if z.enc2 <= 17*60+15 else 2)),
        'log': 0 if z.k not in logst else logst[z.k],
        'idade': cut(z.e70_p, [5, 9, 15]), 'esc': cut(z.baixa_esc_p, [20, 30, 43]),
        'comp': cut(z.T2, [75, 80, 85]), 'dcomp': cut(z.dT, [-2, 0, 2]),
        'w': z.w, 'a2': int(z.aptos_2t), 'c1': int(z.comp_1t), 'c2': int(z.comp_2t), 'v1': int(z.vv_1t), 'v2': int(z.vv_2t),
        'l1': int(z.lula_1t), 'l2': int(z.lula_2t), 'f2': int(z.flavio_2t), 'n1': int(z.nb_1t), 'n2': int(z.nb_2t),
        'b0': int(z.b0_2t), 'sc': z.semcad_n, 'x': z.xdL,
        'id': f"{z.uf}-{z.zona}-{z.secao}-{z.cd_mun}", 'mun': z.nm_mun.title()})
save('secoes', rows, 3)
dims = []
for i, (k, g, t, cats) in enumerate(DIMS):
    for j, cat in enumerate(cats): dims.append({'id': f'{k}_{j}', 'dim': k, 'grupo': g, 'titulo': t, 'ordem': i, 'cod': j, 'rotulo': cat})
ufs = sorted(a.uf.unique())
for j, u in enumerate(ufs): dims.append({'id': f'uf_{u}', 'dim': 'uf', 'grupo': 'UF', 'titulo': 'UF', 'ordem': len(DIMS), 'cod': j, 'rotulo': u})
save('dims', dims)
# conferências
sec = pd.DataFrame(rows)
for k, *_ in DIMS: print(k, sec[k].isna().sum(), sec[k].value_counts().sort_index().to_dict())
print('Σ', 'votos sem digital a mais (país)', ((sec.w*sec.n2).sum()*(NAC['comp2']/(a.w*a.comp_2t).sum()) - (sec.w*sec.n1).sum()*(NAC['comp1']/(a.w*a.comp_1t).sum())))
print('ok')
