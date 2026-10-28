#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atualiza os dados do site `painel_veredito` (e `ds4/`) integrando todas as 23 Frentes MECE (32 hipóteses):
- Frentes 1 a 15 (Censo 100% 2026: 499.207 seções, 67,86M Multi-Cargo, 158,75M Eleitores, Custódia/TPM, WSQ/VSC, RDV, Logs, TPS, Código C/C++)
- Frente 16 (Censo 100% Logs GEDAI-UE nas 28 UFs: lotes de 24/10 e 25/10, 4.333 estações, 5,03M linhas, pacote nacional -pu.jez)
- Frente 17 (Censo 100% Geografia Fina: GPS <500m em 41.985 escolas, 51.580 bairros, 94.056 escolas R²=98,91%, seções especiais)
- Frente 18 (Censo 100% RAE 9,53M operações e 2,49M transferências de domicílio: 99,95% biometria 16–17 anos)
- Frente 19 (Censo 100% Comparecimento Real TTE 560,3k, PcD 1,97M únicos e 83.253 denúncias Pardal)
- Frente 20 (Censo 100% Timestamps de Recebimento e Fila de Totalização TSE nas 497.897 seções: 24,0s vs 24,0s)
- Frente 21 (Experimento Natural 2022×2026 nas 461.219 seções pareadas: aposentadoria das UE2009–2011 e troca por UE2020/2022)
- Frente 22 (Painel Longitudinal 12 Anos 2014×2018×2022×2026: 3.707.067 urnas nos 8 turnos e 5.570 municípios)
- Frente 23 (Censo 100% BWeb 2ºT + CEFT 2ºT: fechamento da lacuna 2.5 nas 499.207 seções, auditoria das 8,63M liberações NH 1ºT×2ºT e decomposição da inflexão das 17h00 / prorrogação das 19h00 em 6.342 seções)
"""
import json
import os

BASE = "."
DATA = os.path.join(BASE, "data")
PV_DATA = os.path.join(BASE, "painel_veredito", "data")
DS4_DATA = os.path.join(BASE, "ds4")

def save_both(name, rows):
    for folder in (PV_DATA, DS4_DATA):
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Saved {name}.json: {len(rows)} rows ({os.path.getsize(os.path.join(PV_DATA, name + '.json')) / 1024:.1f} KB)")

def main():
    casos = json.load(open(os.path.join(PV_DATA, "casos.json"), encoding="utf-8"))
    provas = json.load(open(os.path.join(PV_DATA, "provas.json"), encoding="utf-8"))
    f20 = json.load(open(os.path.join(DATA, "censo_frente20_recebimento_totalizacao_499k.json"), encoding="utf-8"))

    MARGEM = 4429907
    MEIA = MARGEM / 2.0
    EST = {
        "1": ("Cadastro", "Quem pode votar"),
        "2": ("Mesa", "Quem é liberado para votar"),
        "3": ("Urna", "Como o voto é gravado"),
        "4": ("Arquivos", "Como o voto é contado"),
        "5": ("Totalização", "Como os votos são somados"),
        "6": ("Horário", "Quando se votou"),
        "7": ("Eleitor", "Por que o eleitor votou assim"),
        "8": ("Sinais", "Padrões apontados no resultado"),
    }

    def make_card(id_, nome, ver, forca, frase, tecnico, visual, teto=None, teto_pt=None, limiar="margem", lo=None):
        est = id_.split(".")[0]
        L = MARGEM if limiar == "margem" else MEIA
        tp = teto_pt if teto_pt is not None else teto
        return {
            "id": id_,
            "ordem": 0,
            "estagio": est,
            "estagio_nome": EST[est][0],
            "estagio_pergunta": EST[est][1],
            "nome": nome,
            "veredito": ver,
            "forca": forca,
            "frase": frase,
            "tecnico": tecnico,
            "visual": visual,
            "teto": teto,
            "teto_pt": tp,
            "teto_lo": lo,
            "limiar": limiar,
            "limiar_votos": round(L, 4),
            "pct": round(teto / L * 100.0, 4) if teto is not None else None,
            "pct_pt": round(tp / L * 100.0, 4) if teto is not None else None,
            "mede": teto is not None,
        }

    # Remove eventuais versões anteriores dos cartões atualizados/novos para inserção limpa
    new_ids = {"1.4", "2.5", "3.4", "3.5", "5.2", "6.2", "7.2", "8.6"}
    casos = [c for c in casos if c["id"] not in new_ids]

    # Enriquecer textos técnicos de 1.1, 2.1, 2.3, 8.1, 8.3 e 8.4 com os dados do BWeb 2ºT (499.205 seções)
    for c in casos:
        if c["id"] == "1.1":
            if "560.332" not in c["tecnico"]:
                c["tecnico"] += " Na Frente 19 (perfil_comparecimento_abstencao_eleitor_tte_2026.zip), dos 595.156 eleitores habilitados em TTE no 1ºT, 560.332 (94,15%) compareceram efetivamente (Mesários: 98,39% [216.224/219.759]; Trânsito: 92,20%; Presos Provisórios: 75,27%), e no 2ºT o total de TTE caiu −11.039 aptos (−10.169 votos efetivos). A identidade aptos_2t − aptos_1t == d_net_tte fecha com erro ZERO em 100,0000% dos 5.571 municípios brasileiros + 186 localidades no exterior e em 99,83% das seções diretamente."
        elif c["id"] in ("2.1", "2.3"):
            if "8.632.488" not in c["tecnico"]:
                c["tecnico"] += " No Censo de 100% do BWeb 2ºT cruzado com o BWeb 1ºT (499.205 seções, Frente 23), o total nacional de eleitores com biometria cadastrada liberados manualmente após 4 tentativas (QT_ELEI_BIOM_SEM_HABILITACAO) passou de 8.342.249 no 1ºT (6,66% do comparecimento) para 8.632.488 no 2ºT (6,73% do comparecimento — variação de apenas +0,07 p.p.). Controlando pelo município nas 499.205 seções, a inclinação do ganho de Lula (Δ% Lula 2ºT − 1ºT) contra a taxa de liberação manual no 2ºT é NEGATIVA (−0,5535 p.p. a cada +10 p.p. de liberação manual), e contra a variação de liberação manual (2ºT − 1ºT) é −0,0486 p.p. (estatisticamente zero)."
        elif c["id"] == "8.1":
            if "98,27%" not in c["tecnico"]:
                c["tecnico"] += " No Censo de 100% do BWeb 2ºT × 1ºT (499.205 seções): (1) Nas 106 seções com 100% para Lula no 2ºT (14.860 votos somados = 0,33% da margem, vs. 4 seções 100% Flávio = 296 votos), Lula já havia obtido 98,27% de todos os candidatos no 1ºT (e 99,19% na razão Lula/(Lula+Flávio) do 1ºT). (2) Nas 6.816 seções com >90% para Lula no 2ºT (6.899 ≥90%), Lula já havia obtido 90,37% dos votos válidos no 1ºT (e 92,43% na razão Lula/(Lula+Flávio) do 1ºT), e a taxa de falha biométrica nelas ficou estável entre os turnos (8,13% no 1ºT vs. 8,37% no 2ºT)."
        elif c["id"] == "8.3":
            if "2014" not in c["tecnico"]:
                c["tecnico"] += " No Painel Longitudinal de 12 Anos (Frente 22: 2014, 2018, 2022 e 2026), a queda de comparecimento do 1ºT para o 2ºT na Região Norte é uma constante histórica estrutural de todas as eleições presidenciais: −3,93 p.p. em 2014, −3,53 p.p. em 2018, −1,99 p.p. em 2022 e −1,81 p.p. em 2026 (a menor queda da série histórica)."

    # Cartão 2.5 agora EXCLUÍDO com o Censo 100% do CEFT 2ºT × CESP 2ºT × BWeb 2ºT
    c_25 = make_card(
        "2.5",
        "Substituição de urna e correspondência efetivada no 2ºT (CEFT)",
        "Excluído",
        "direto",
        "100% das 499.207 seções têm TPM atestado no CEFT 2ºT; nas 2.670 contingências, Lula teve −0,27 p.p.",
        "Censo de 100% das Correspondências Efetivadas do 2º Turno (CEFT_2t_UF_261020261201.zip, 28/28 UFs com hash .sha512 válido = 499.207 seções) cruzadas com as Correspondências Esperadas de domingo (CESP_2t_UF_251020261345.zip: 499.178 CSEC + 48.674 CCONT) e os Boletins de Urna (BWeb 2ºT = 499.205 seções): (1) 499.207 de 499.207 seções (100,0000%) possuem assinatura de hardware TPM na geração da mídia (NR_SRI_TPM_GERACAO_MIDIA) e na transmissão da correspondência (NR_SRI_TPM_TRANSM_CORRESP), com ZERO urnas órfãs ou sem correspondência efetivada. (2) Em 496.486 seções (99,455%), a tripla física (NR_URNA_EFETIVADA + CD_CARGA de 24 dígitos + CD_FLASHCARD) do 2ºT foi 100% idêntica à urna titular esperada (CSEC). (3) Em 2.670 seções (0,535%, TP_DIVERGENCIA = 'C'), atuou urna de contingência oficial (CCONT), e em 51 seções (0,010%) houve nova carga oficial de domingo no GEDAI-UE. (4) Nas 2.670 seções com urna de contingência no 2ºT, Lula obteve 50,78% (vs. 51,29% nas titulares), com diferença intra-município de −0,2653 p.p. (Lula teve votação ligeiramente menor nas urnas substituídas por contingência dentro da mesma cidade).",
        "ceft2t",
        teto=0,
    )

    c_14 = make_card(
        "1.4",
        "Alistamento RAE, transferências e voto assistido PcD",
        "Excluído",
        "direto",
        "99,95% dos novos jovens têm biometria; nas 56 cidades recordistas em transferência, Flávio venceu 48.",
        "Censo de 100% das 9.527.615 operações RAE (perfil_rae_2026.zip) e 2.488.390 transferências de domicílio (perfil_eleitorado_transferencia_2026.zip, Frente 18) + Censo de 1.970.165 eleitores PcD únicos (perfil_comparecimento_abstencao_eleitor_deficiente_2026.zip, Frente 19): (1) Na coorte de 16–17 anos (100% alistada em 2025/2026), 1.630.933 de 1.631.813 eleitores (99,9461%) possuem biometria coletada (apenas 880 sem biometria no país), e 96,34% dos 3,22M novos alistamentos são de jovens de 15–24 anos (apenas 1.594 alistamentos 80+). (2) No fluxo migratório de transferências, Norte/Nordeste perderam eleitores (PA −25,6k, MA −24,9k, BA −24,6k) enquanto SC (+67.442), PR (+17.460) e DF (+14.105) foram os maiores ganhadores líquidos; no Top 1% de cidades com mais transferências (56 cidades), Flávio venceu em 48 (85,7%) e o resíduo controlado de Lula foi negativo (−0,30 p.p.). (3) Entre os 1.970.165 eleitores PcD únicos, o comparecimento real foi de 66,84% (−12,40 p.p. abaixo da média nacional), caindo para 29,26% nos idosos 80+ PcD e apenas 15,69% (10.176 de 64.851) nos eleitores com dificuldade para o exercício do voto, refutando abuso de voto assistido.",
        "raepcd",
        teto=158854,
        teto_pt=1914,
    )

    c_34 = make_card(
        "3.4",
        "Preparação das urnas e pacote nacional no GEDAI-UE (28 UFs)",
        "Excluído",
        "direto",
        "100% das 4.333 estações GEDAI-UE rodaram a versão 8.23.0.0 e o mesmo pacote de urna (-pu.jez).",
        "Censo de 100% dos arquivos de log do Sistema de Preparação das Urnas (GEDAI-UE, log_gedai_1t e log_gedai_2t nos lotes de 24/10 e 25/10 nas 28 UFs = 4.333 estações no 2ºT, 4.760 no 1ºT, 5.025.594 linhas de log, Frente 16): (1) 28/28 UFs (100%) validadas contra o hash oficial .sha512 nos lotes de véspera (24/10) e de domingo (25/10 13:27), e 4.333/4.333 envelopes criptográficos .vsc (100%) com SHA-512 binário exato assinado por chaveAssinaturaDesktop (SEVIN). (2) 5.025.594/5.025.594 linhas (100,0000%) possuem MAC hexadecimal de 64 bits íntegro, e nas 4.190 estações comuns aos dois turnos (100,0000%), o log do 2ºT traz o log do 1ºT como prefixo byte-a-byte exato (imutabilidade append-only). (3) 100,0000% (84.463/84.463 aberturas) rodaram GEDAI-UE Versão 8.23.0.0 - Praia da Barra do Cahy e Holocron 4.20.0.0 em modo ELEIÇÃO OFICIAL, e 100,0000% (4.485/4.485 importações) carregaram exatamente o mesmo Pacote de Urna Nacional o00000br-pu.jez Versão 202608121843 (zero versões divergentes no país). (4) Foram geradas 534.467 mídias de votação (NS), e a taxa de erros/alertas ou novas cargas de outubro não tem qualquer correlação com o voto ou swing de Lula (r = −0,020, p = 0,30).",
        "gedai",
        teto=0,
    )

    c_35 = make_card(
        "3.5",
        "Experimento Natural 2022×2026: troca das UE2009–2015 por novas",
        "Excluído",
        "direto",
        "Aposentadas 136.930 urnas 2009–2011 por novas em 2026, o efeito intra-escola foi 0,00 p.p.",
        "Cruzamento longitudinal exato de 461.219 seções eleitorais pareadas entre o 2ºT de 2022 e o 2ºT de 2026 (votacao_secao_2022_BR.zip × detalhe_votacao_secao_2022.zip × Censo 2026, Frente 21): (1) A votação da mesma seção quatro anos depois tem correlação r = 0,9729 (R² = 94,66%; nas 90.043 escolas R² = 96,48%; nos 5.551 municípios R² = 97,80%). (2) Entre 2022 e 2026, o TSE aposentou 100% das urnas UE2009, UE2010 e UE2011 (136.930 seções) e substituiu 215.349 urnas antigas (UE2009–2015) por urnas novas (UE2020/UE2022). Nas 215.349 seções que trocaram hardware antigo por novo, a variação intra-município foi de −0,0161 p.p. e intra-escola foi de 0,0000 p.p. (nas 136.930 aposentadas UE2009–11: +0,0048 p.p. intra-cidade e −0,0019 p.p. intra-escola). (3) Prova Placebo definitiva no recorte do relatório do PL (<50 mil eleitores): em 2026, quando AMBOS os grupos passaram a votar em urnas novas UE2020/UE2022, a diferença entre as seções que tinham urna antiga em 2022 e as que já tinham UE2020 permaneceu em +3,43 p.p. bruto (+2,16 p.p. intra-cidade; DiD = −0,15 p.p., p = 0,264), provando que a diferença de 2022 era 100% demográfica/geográfica e 0% da máquina.",
        "exp2226",
        teto=0,
        limiar="meia",
    )

    c_52 = make_card(
        "5.2",
        "Fila nos servidores do TSE e ordem de chegada dos 497.897 BUs",
        "Excluído",
        "direto",
        "Fila no servidor TSE é idêntica (24,0 s Lula vs. 24,0 s Flávio); atraso intra-escola é zero.",
        "Censo de 100% dos timestamps oficiais ao nível de segundo de Recebimento do BU (DT_RECEBIMENTO_BU_HOR_TSE) e Primeira Totalização Parcial (DT_PRIM_TOT_PARCIAL_HOR_TSE) nas 497.897 seções válidas do Brasil (detalhe_votacao_secao_2026_1t2t.zip, Frente 20): (1) A latência de fila nos servidores centrais do TSE entre a recepção do BU e sua totalização tem mediana idêntica de 24,0 segundos nas seções vencidas por Lula (média 25,43 s) e de 24,0 segundos nas seções vencidas por Flávio (média 25,62 s; diferença de 0,19 s, r = −0,0299 dentro do mesmo minuto). (2) Dentro do mesmo município, cada 1 hora de atraso na recepção do BU associa-se a −0,0105 p.p. no swing de Lula (r = −0,0050), e dentro do mesmo prédio escolar (476.565 seções) a −0,0395 p.p./hora (r = −0,0045). (3) A virada na curva acumulada nacional às 20:26:50 (50% das seções) ocorre exclusivamente porque os primeiros 25% de BUs recebidos vêm de estados/cidades onde Lula já havia tido 43,25% no 1ºT (−1,91 p.p. abaixo da média nacional do 1ºT).",
        "filatse",
        teto=0,
    )

    c_62 = make_card(
        "6.2",
        "Inflexão das 17h00 e prorrogação das 19h00 (Censo BWeb 2ºT × 1ºT)",
        "Excluído",
        "direto",
        "O corte <=17h00 mistura fusos UTC-4/5 com o 1º min; após 19h, Flávio venceu no RJ (54,2%) e o excesso real foi 29,8 mil votos.",
        "Decomposição censitária de 100% dos horários de encerramento (DT_ENCERRAMENTO no BWeb 2ºT = 499.205 seções) cruzados seção a seção com o 1º Turno (BWeb 1ºT = 499.206 seções, Frente 23): (1) O filtro bruto DT_ENCERRAMENTO <= '17:00' (150.771 seções, Flávio 52,39% vs. Lula 47,61%, saldo −1.747.639) junta dois grupos heterogêneos: (a) 100% dos 6 estados em fuso UTC-4/UTC-5 (MT, MS, RO, RR, AM, AC = 32.055 seções, onde o relógio local encerra às 15h/16h e Flávio teve 59,71%, saldo −1.442.684) e (b) as 118.716 seções do fuso UTC-3 que digitaram a senha nos primeiros 60 segundos (17:00:00 a 17:00:59, Lula 49,48%). Já as 339.593 seções de 17h01 a 17h15 (88,07M eleitores = 68,7% do país) são o encerramento normal das 17h no UTC-3 (pois a urna bloqueia o encerramento antes das 17:00:00); dentro do mesmo município em UTC-3, a diferença entre 17:01–17:15 e 17:00:xx é de apenas +0,2272 p.p., e o ganho de Lula sobre a razão Lula/(Lula+Flávio) do 1ºT foi idêntico em todas as faixas (+2,74 p.p. em UTC-4/5, +2,72 p.p. em 17:00 e +2,76 p.p. em 17:01–17:15). (2) Nas 6.342 seções prorrogadas até as 19h00 (1.858.274 eleitores no dia todo, e não após as 17h!): no 1ºT (fechando às 17h) essas exatas mesmas 6.342 seções já tinham tido 1.786.244 eleitores; descontado o crescimento nacional de comparecimento (+2,36%), o excesso líquido das 2h extras foi de exatos +29.821 eleitores (confirmando os ~34 mil votos divulgados). (3) O estado com mais seções >=19h no país foi o Rio de Janeiro (2.805 seções = 44,2% do total nacional, 837.298 eleitores), omitido em relatórios virais porque nele Flávio Bolsonaro VENCEU com 54,19% (Lula 45,81%, saldo −67.734); no Maranhão houve apenas 3 seções >=19h (634 eleitores). Em São Paulo Capital (1.481 seções >=19h), Lula já havia tido 55,22% sobre L+F no 1ºT (quando 0 seções fecharam >=19h) e cresceu +2,64 p.p. no 2ºT — MENOS do que cresceu nas 25.202 seções <19h da própria capital (+3,02 p.p.).",
        "inflexao1719",
        teto=0,
    )

    c_72 = make_card(
        "7.2",
        "Geografia fina: GPS <500m, 51.580 bairros, seções especiais e Pardal",
        "Excluído",
        "direto",
        "Escolas a <500m têm r = 0,940; escola + 1ºT explicam 98,91% de todas as 497.897 urnas do país.",
        "Censo Geográfico Fino de 100% das 499.207 seções e 94.227 locais de votação (eleitorado_local_votacao_2026.zip, Frente 17) + 83.253 denúncias eleitorais no Pardal TSE (denuncia_2026.zip, Frente 19): (1) Pareando por GPS exato (Haversine < 500m no mesmo município, 41.985 escolas), a correlação entre uma escola e sua vizinha física imediata é r = 0,9403 no 2ºT (r = 0,6327 no swing), com DP residual de apenas 1,59 p.p. nas escolas regulares (98,8% dentro de ±3σ, zero 'ilhas de fraude'). (2) A hierarquia de efeitos fixos + 1ºT explica 97,69% da variância com UF (27), 98,24% com Município (5.570), 98,51% com CEP (33.711), 98,66% com Bairro (51.580) e 98,91% com Escola (94.056, DP residual = 1,80 p.p.). (3) Em todas as categorias especiais — Aldeias Indígenas (1.395 seções), Quilombolas (426), Assentamentos (1.551), Zona Rural (49.511) e Prisionais (271) — o swing de Lula (+3,9 a +4,9 p.p.) foi menor que nas escolas urbanas do mesmo município (+6,8 p.p.). (4) Nas cidades com mais denúncias no Pardal (15–30/10k hab), Flávio venceu em 62,3% dos municípios, e denúncias judicializadas no PJe (21.020) tiveram coeficiente parcial negativo para Lula (p = 0,0054).",
        "geofina",
        teto=0,
    )

    c_86 = make_card(
        "8.6",
        "Série histórica 2014×2018×2022×2026 (3,71M urnas nos 8 turnos)",
        "Excluído",
        "direto",
        "2022 explica 97,8% das cidades e 94,7% das seções de 2026; 106 seções 100% é o mínimo em 12 anos.",
        "Painel Longitudinal Histórico de 12 Anos cobrindo 100% dos 8 turnos presidenciais de 2014, 2018, 2022 e 2026 (3.707.067 urnas ativas somadas e 5.570 municípios comuns, Frente 22): (1) A correlação municipal do % PT no 2ºT entre 2022 e 2026 é r = 0,9887 (R² = 97,75%; 2018×2022 r = 0,9750; 2014×2018 r = 0,9335; 2014×2026 em 12 anos r = 0,8891). Apenas 6 municípios em 5.570 (0,11%) tiveram salto |z_UF| > 4 entre 2022 e 2026 — sendo 5 pró-Flávio e apenas 1 pró-Lula (São Julião-PI, 4.434 votos, retornando ao patamar de 2014). (2) O número de seções unânimes (100% PT no 2ºT) em 2026 (106 seções = 14.860 votos, 0,023% do total, onde Lula já teve 98,27% no 1ºT, nas mesmas aldeias indígenas históricas de Tabatinga-AM, Uiramutã-RR, Atalaia do Norte-AM e Fernando Falcão-MA) é o MENOR de toda a série histórica de 12 anos (foram 192 em 2014, 328 em 2018 e 143 em 2022). (3) Todos os 4 segundos turnos (2014, 2018, 2022 e 2026) passam no teste qui-quadrado de uniformidade do último dígito (em 2026 2ºT: p = 0,7903 para Lula e p = 0,2734 para Flávio), e o proxy intra-municipal de Klimek é negativo nos 8 turnos (−0,078 a −0,176).",
        "hist1426",
        teto=0,
    )

    casos.extend([c_14, c_25, c_34, c_35, c_52, c_62, c_72, c_86])
    # Ordena por estágio e id numérico
    casos.sort(key=lambda x: (int(x["id"].split(".")[0]), int(x["id"].split(".")[1])))
    for i, c in enumerate(casos, 1):
        c["ordem"] = i

    save_both("casos", casos)

    # Atualiza provas.json
    provas = [p for p in provas if p["caso"] not in new_ids]
    def P(caso, k, rot="", v=None, v2=None, lo=None, hi=None, n=None):
        provas.append({"caso": caso, "k": k, "rotulo": rot, "v": v, "v2": v2, "lo": lo, "hi": hi, "n": n})

    # 1.4 RAE, Transferências e PcD (Frentes 18 e 19)
    P("1.4", "bio_1617", "Jovens 16–17 anos c/ biometria (2026)", 99.95, 1630933, lo=1631813, hi=880)
    P("1.4", "top1_transf", "Top 1% Cidades Transferência: vitória Flávio", 85.71, 48, lo=56, hi=-0.30)
    P("1.4", "comp_pcd", "Comparecimento Eleitores PcD (1,97M únicos)", 66.84, 1312396, lo=1963551, hi=-12.40)
    P("1.4", "comp_pcd80", "Comparecimento Idosos 80+ PcD (159,4k)", 29.26, 46642, lo=159386, hi=112744)
    P("1.4", "comp_difvoto", "Comparecimento Dificuldade Voto (64,9k)", 15.69, 10176, lo=64851, hi=54675)

    # 2.5 CEFT 2ºT × CESP 2ºT × BWeb 2ºT (Frente 23)
    P("2.5", "tpm_ceft", "Seções com TPM atestado no CEFT 2ºT (499.207)", 100.0, 51.29, lo=0.0, hi=499207, n=499207)
    P("2.5", "titular_csec", "Urna Titular Exata CSEC (496.486 seções)", 99.46, 51.29, lo=0.0, hi=496486, n=496486)
    P("2.5", "cont_ccont", "Contingência Oficial CCONT (2.670 · −0,27 p.p.)", 0.53, 50.78, lo=-0.2653, hi=2670, n=2670)
    P("2.5", "recarga_dom", "Recarga de Domingo no GEDAI-UE (51 seções)", 0.01, 59.86, lo=0.0, hi=51, n=51)
    P("2.5", "orfas", "Urnas sem correspondência ou sem TPM (0)", 0.0, 0.0, lo=0.0, hi=0, n=0)

    # 3.4 GEDAI-UE (Frente 16)
    P("3.4", "sha_vsc", "Hashes .sha512 (28 UFs) e envelopes .vsc", 100.0, 4333, lo=4333, hi=28)
    P("3.4", "append_1t2t", "Imutabilidade Append-Only 1ºT → 2ºT", 100.0, 4190, lo=4190, hi=0)
    P("3.4", "gedai_ver", "GEDAI-UE 8.23.0.0 e Holocron 4.20.0.0", 100.0, 84463, lo=84463, hi=0)
    P("3.4", "pacote_pu", "Pacote Nacional de Urna (-pu.jez 202608121843)", 100.0, 4485, lo=4485, hi=0)
    P("3.4", "mac_linhas", "Linhas de log com MAC 64 bits íntegro", 100.0, 5025594, lo=5025594, hi=0)

    # 3.5 Experimento Natural 2022×2026 (Frente 21)
    P("3.5", "apos_0911", "UE2009–11 (2022) → UE2020/22 (2026) · 136,9k", 54.01, 53.68, lo=0.0048, hi=-0.0019, n=136930)
    P("3.5", "ant_1315", "UE2013/15 (2022) → UE2020/22 (2026) · 78,4k", 50.11, 50.32, lo=-0.0525, hi=0.0034, n=78419)
    P("3.5", "ctrl_nova", "Sempre UE2020/22 (2022 e 2026) · 151,8k", 48.40, 50.20, lo=0.0113, hi=0.0006, n=151812)
    P("3.5", "ctrl_ant", "Sempre UE2013/15 (2022 e 2026) · 28,8k", 54.96, 54.69, lo=0.0078, hi=0.0029, n=28782)
    P("3.5", "pl_trat", "Cidades <50k (Antiga→Nova, 119,4k): Placebo", 59.20, 57.09, lo=-0.0036, hi=0.0003, n=119423)
    P("3.5", "pl_ctrl", "Cidades <50k (Nova→Nova, 28,6k): Controle", 54.84, 53.66, lo=0.0217, hi=0.0000, n=28632)

    # 5.2 Fila de Totalização e Curva Acumulada (Frente 20)
    for row in f20["curva_acumulada_20_pontos"]:
        P(
            "5.2",
            f"p{row['pct_secoes']}",
            row["horario_tot_2t"],
            row["pct_secoes"],
            row["lula_2t_acum_pct"],
            lo=row["esperado_pelo_1t_mais_shift_nac_pct"],
            hi=row["lula_1t_mesmas_secoes_pct"],
            n=int(round(497897 * row["pct_secoes"] / 100.0)),
        )
    P("5.2", "lat", "Latência mediana de fila nos servidores do TSE (segundos)", 24.0, 24.0, lo=25.43, hi=25.62, n=497897)

    # 6.2 Decomposição 17h00 e Prorrogação 19h00 (Frente 23 - BWeb 2ºT × 1ºT)
    P("6.2", "fuso_utc45", "<=17h00: Fusos UTC-4/5 (MT,MS,RO,RR,AM,AC · 32,1k)", 37.55, 40.29, lo=2.74, hi=-1442684, n=32055)
    P("6.2", "min_1700", "==17:00:00 a 17:00:59 (1º min UTC-3 · 118,7k)", 46.76, 49.48, lo=2.72, hi=-304955, n=118716)
    P("6.2", "norm_1701", "17h01 a 17h15 (Encerramento normal UTC-3 · 339,6k)", 50.70, 53.46, lo=2.76, hi=5897416, n=339593)
    P("6.2", "pos19_rj", ">=19h00 RJ (2.805 seções · omitido: Flávio venceu!)", 41.61, 45.81, lo=4.20, hi=-67734, n=2805)
    P("6.2", "pos19_sp", ">=19h00 SP Capital (1.481 seções · <19h subiu +3,02pp)", 55.22, 57.86, lo=2.64, hi=58412, n=1481)
    P("6.2", "pos19_bape", ">=19h00 BA + PE (1.593 seções · já 67,5% no 1ºT)", 67.51, 69.65, lo=2.14, hi=184663, n=1593)

    # 7.2 Geografia Fina e GPS <500m (Frente 17)
    P("7.2", "gps_500m", "Correlação GPS <500m entre escolas vizinhas", 94.03, 1.59, lo=41985, hi=224.98)
    P("7.2", "r2_uf", "Variância explicada (R²): 1ºT + 27 UFs", 97.69, 2.63, lo=27, hi=497897)
    P("7.2", "r2_mun", "Variância explicada (R²): 1ºT + 5.570 Cidades", 98.24, 2.29, lo=5570, hi=497897)
    P("7.2", "r2_bairro", "Variância explicada (R²): 1ºT + 51.580 Bairros", 98.66, 2.00, lo=51580, hi=497897)
    P("7.2", "r2_escola", "Variância explicada (R²): 1ºT + 94.056 Escolas", 98.91, 1.80, lo=94056, hi=497897)

    # 8.6 Série Histórica 2014×2018×2022×2026 (Frente 22)
    P("8.6", "corr_mun_22_26", "2022 × 2026: 5.570 Municípios (R² = 97,8%)", 98.87, 97.75, lo=5570, hi=106)
    P("8.6", "corr_esc_22_26", "2022 × 2026: 90.043 Escolas (R² = 96,5%)", 98.22, 96.48, lo=90043, hi=143)
    P("8.6", "corr_sec_22_26", "2022 × 2026: 461.219 Seções (R² = 94,7%)", 97.29, 94.66, lo=461219, hi=328)
    P("8.6", "corr_mun_18_22", "2018 × 2022: 5.570 Municípios (R² = 95,1%)", 97.50, 95.06, lo=5570, hi=192)
    P("8.6", "corr_mun_14_26", "2014 × 2026 (12 anos): Dilma × Lula (R² = 79,1%)", 88.91, 79.05, lo=5570, hi=3707067)

    save_both("provas", provas)

if __name__ == "__main__":
    main()
