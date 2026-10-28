#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atualiza os dados do site `painel_veredito` (e `ds4/`) integrando todas as 15 Frentes MECE
(100% Censo nas 499.207 Seções 1ºT x 2ºT, 67,86M Multi-Cargo, 158,75M Eleitores, 1,15M TTE,
1,60M Custódia/TPM, 640 pacotes .vsc/WSQ, 958 RDVs voto a voto, 3.061 logs, TPS e Código C/C++).
"""
import json
import math
import os
import pandas as pd
import numpy as np

BASE = "."
DATA = os.path.join(BASE, "data")
PV_DATA = os.path.join(BASE, "painel_veredito", "data")
DS4_DATA = os.path.join(BASE, "ds4")

def fi(x):
    return f"{int(round(x)):,}".replace(",", ".")

def f1(x):
    return f"{x:.1f}".replace(".", ",")

def f2(x):
    return f"{x:.2f}".replace(".", ",")

def sg(x, f=f2):
    return ("+" if x > 0 else "−" if x < 0 else "") + f(abs(x))

def r_val(x, k=4):
    if x is None:
        return None
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        if math.isnan(x) or math.isinf(x):
            return None
        return round(float(x), k)
    return x

def save_both(name, rows, k=4):
    cleaned = [{kk: r_val(v, k) for kk, v in row.items()} for row in rows]
    for folder in (PV_DATA, DS4_DATA):
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Saved {name}.json: {len(cleaned)} rows ({os.path.getsize(os.path.join(PV_DATA, name + '.json')) / 1024:.1f} KB)")

def main():
    # Carrega base existente de casos e provas
    old_casos = json.load(open(os.path.join(PV_DATA, "casos.json"), encoding="utf-8"))
    old_provas = json.load(open(os.path.join(PV_DATA, "provas.json"), encoding="utf-8"))
    old_secoes = json.load(open(os.path.join(PV_DATA, "secoes.json"), encoding="utf-8"))
    old_dims = json.load(open(os.path.join(PV_DATA, "dims.json"), encoding="utf-8"))

    # Carrega JSONs das Frentes 11 a 15
    f11 = json.load(open(os.path.join(DATA, "mece_frente11_wsq_vsc_forense.json"), encoding="utf-8"))
    f12 = json.load(open(os.path.join(DATA, "mece_frente12_rdv_nulos_1t2t.json"), encoding="utf-8"))
    f13 = json.load(open(os.path.join(DATA, "censo_frente13_custodia_499k.json"), encoding="utf-8"))
    f14 = json.load(open(os.path.join(DATA, "censo_frente14_tte_mesarios_comp.json"), encoding="utf-8"))
    f15 = json.load(open(os.path.join(DATA, "censo_frente15_499k_secoes_1t2t.json"), encoding="utf-8"))

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

    casos = []
    def add(id_, nome, ver, forca, frase, tecnico, visual, teto=None, teto_pt=None, limiar="margem", lo=None):
        est = id_.split(".")[0]
        L = MARGEM if limiar == "margem" else MEIA
        tp = teto_pt if teto_pt is not None else teto
        casos.append({
            "id": id_,
            "ordem": len(casos) + 1,
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
            "limiar_votos": L,
            "pct": (teto / L * 100.0) if teto is not None else None,
            "pct_pt": (tp / L * 100.0) if teto is not None else None,
            "mede": teto is not None,
        })

    # Mapa rápido dos casos antigos para preservar tetos exatos onde aplicável
    oc = {c["id"]: c for c in old_casos}

    # ==================== ESTÁGIO 1: CADASTRO ====================
    add(
        "1.1",
        "Eleitores novos e TTE entre turnos",
        "Excluído",
        "direto",
        "Eleitorado idêntico (158.745.502) e saldo TTE exato em 5.757 de 5.757 cidades.",
        "Total oficial de aptos do TSE: 158.745.502 no 1º e 158.745.502 no 2º turno (Δ = 0). No censo de 1.154.903 pares de Transferência Temporária (Frente 14: 1.594.961 eleitores no 1ºT e 1.590.870 no 2ºT — mesários 31,9%, trânsito 29,4%, acessibilidade 25,6%, forças armadas/polícias 9,7%), a variação Aptos_2T − Aptos_1T bate com erro ZERO em 5.757 de 5.757 municípios e localidades do exterior (100,0000%). Efeito líquido de TTE no voto de Lula: t = −0,06 (p = 0,95, nulo).",
        "aptos",
        teto=0,
    )
    add(
        "1.2",
        "Urna liberando mais \"sem digital\" que o cadastro",
        "Excluído",
        "estatístico",
        oc["1.2"]["frase"],
        oc["1.2"]["tecnico"],
        "cadastro",
        teto=oc["1.2"]["teto"],
    )
    add(
        "1.3",
        "Super-idosos (80+, 90+ e 100+) sem biometria",
        "Excluído",
        "direto",
        "99,28% dos 297.977 centenários não votaram; onde idosos votaram mais, Flávio venceu 74/74.",
        "Censo de 158.745.463 eleitores (Frente 6) × Censo de Comparecimento Real de 156.454.011 eleitores (Frente 14, perfil_comparecimento_abstencao_2026.zip): 89,06% dos 2,00 mi de eleitores 80+ sem biometria estão em RJ, SP, MG e RS (revisão biométrica suspensa em 2020) e tiveram 96,81% de abstenção física (3,19% de comparecimento vs. 61,49% nos 80+ com biometria). Dos 297.977 centenários (100+ anos), apenas 2.141 (0,72%) votaram no país inteiro (99,28% de abstenção real; no RJ apenas 150 de 105.262 = 0,14%!). Nos 74 municípios com ≥14% de idosos e presença ≥85%, Flávio venceu em 74 de 74 (100%).",
        "idosos",
        teto=0,
    )

    # ==================== ESTÁGIO 2: MESA ====================
    add(
        "2.1",
        "Liberação manual sem tentar a digital",
        "Excluído",
        "estatístico",
        oc["2.1"]["frase"],
        oc["2.1"]["tecnico"] + " Além disso, nos 61 logs integrais das seções críticas UE2013 e dos 25 municípios críticos (Passos 1A e 1B), 100% das liberações manuais exigiram no mínimo 4 tentativas ópticas fracassadas (média de 4,38 tentativas/eleitor).",
        "tentativas",
        teto=oc["2.1"]["teto"],
        teto_pt=0,
    )
    add(
        "2.2",
        "Rajada de votos (enchimento rápido ou robô)",
        "Excluído",
        "estatístico",
        "Nenhum voto a menos de 19 s do anterior em 1,51 mi votos e zero ritmo mecânico.",
        oc["2.2"]["tecnico"] + " Na Frente 7 (1.512.625 votos em 3.000 urnas + 61 logs críticos), houve 0 intervalos ≤ 0 s (relógio regressivo), 0 sequências manuais M≥4 em 30–60 s e o coeficiente de variação (CV) subiu para 0,500 no 2ºT (oposto de um metrônomo).",
        "intervalos",
        teto=oc["2.2"]["teto"],
        teto_pt=0,
    )
    add(
        "2.3",
        "Voto sem digital inflando Lula no 2º turno",
        "Excluído",
        "direto",
        "No censo de 497.508 seções, efeito zero na cidade (p = 0,49) e queda de presença.",
        oc["2.3"]["tecnico"] + " No Censo de 100% das 497.508 seções do Brasil (Frente 15, zero amostragem), controlando por Efeito Fixo Municipal (5.571 cidades, SE clusterizado) e voto do 1ºT, % sem biometria tem efeito zero (t = +0,68, p = 0,495), % liberação manual tem efeito nulo/negativo (t = −1,34, p = 0,179) e essas seções tiveram QUEDA relativa de comparecimento no 2ºT (t = −19,08)! Troca de 1º mesário (Frente 7, n = 607 de 4.458 mesários) também teve efeito zero (p = 0,50).",
        "semdigital",
        teto=oc["2.3"]["teto"],
        teto_pt=oc["2.3"]["teto_pt"],
        lo=oc["2.3"]["teto_lo"],
    )
    add(
        "2.4",
        "O mesmo esquema já no 1º turno",
        "Improvável",
        "indireto",
        "Melhor estimativa 0,68 mi; nas 2.640 Zonas (R² = 93,2%), efeito intra-cidade é zero.",
        oc["2.4"]["tecnico"] + " No Censo das 2.640 Zonas Eleitorais (Frente 8) e 94.233 Escolas (Frente 15), Demografia (% idosos 70+ r = +0,85 a +0,98; escolaridade) + Lote de Urna (r = +0,932 no RJ) + Mesários Compulsórios (Frente 14, t = −16,25) explicam 93,15% da liberação manual nas 78 maiores cidades (R² intra-cidade = 79,5%), restando efeito zero no voto de Lula no 1ºT (t = −0,10, p = 0,919) e no 2ºT (p = 0,692).",
        "nivel",
        teto=oc["2.4"]["teto"],
        teto_pt=oc["2.4"]["teto_pt"],
    )
    add(
        "2.5",
        "Digital de outra pessoa (biometria falsa)",
        "Possível",
        "fora",
        "Os pacotes .vsc provam a gravação óptica WSQ, mas comparar imagens exige o TRE.",
        oc["2.5"]["tecnico"] + " A Frente 11 provou que toda urna grava e assina na mídia o arquivo -wsqbio.jez (4,4 a 13,3 MB por seção, ~28,8 KB por eleitor habilitado por biometria, R² = 0,963) com as digitais capturadas em 500 dpi.",
        "lacuna",
    )
    add(
        "2.6",
        "Prova física das digitais nas liberações manuais (-wsqman.jez)",
        "Excluído",
        "direto",
        "Cada liberação manual grava 35,05 KB de digitais WSQ assinadas no .vsc (R² = 0,995).",
        "Auditoria forense de 640 pacotes criptográficos -vota.vsc (Frente 11, incluindo as 54 seções críticas UE2013 e os 25 municípios críticos): 100% dos 633 pacotes com liberação manual (b2 > 0) possuem hashes SHA-512 estritamente únicos de -wsqman.jez (zero arquivos clonados ou sintéticos), e o tamanho físico em bytes segue a lei linear exata size(wsqman.jez) = −11,3 KB + 35,05 KB × b2 (R² = 0,9948, r = 0,9974), correspondendo a 8,76 KB por frame óptico WSQ × 4 tentativas. Em Serra-ES Z26 S651 (274 manuais), -wsqman.jez atinge 9,36 MB (34,15 KB/eleitor), provando fisicamente que todas as tentativas ópticas ocorreram no sensor.",
        "wsq",
        teto=0,
    )

    # ==================== ESTÁGIO 3: URNA ====================
    add(
        "3.1",
        "Cadeia de custódia, TPM e urna trocada entre turnos",
        "Excluído",
        "direto",
        "Zero urnas fantasmas em 499.206 seções, 100% com TPM e 99,71% na mesma urna física.",
        "Censo de 100% das 499.206 seções × 1.596.403 registros oficiais de correspondência CESP (Frente 13: csec_1t, ccont_1t, ceft_1t, csec_2t, ccont_2t): 496.143 seções (99,3864%) operaram na urna titular planejada com o exato lacre CD_CARGA de 24 dígitos; 3.017 (0,6043%) usaram urnas da tabela oficial de contingência ccont_1t (efeito intra-cidade +0,09 p.p., t = +0,65, nulo); 19 tiveram re-carga oficial confirmada em ceft_1t/csec_2t; e 27 foram cédulas em Buenos Aires. ZERO urnas não cadastradas ('fantasmas') no país (0/499.206) e ZERO estações GEDAI-UE sem chip TPM (0/1.596.403 registros). Entre 1ºT e 2ºT, 99,71% (497.712/499.166) mantiveram a mesma urna física, e nas 1.454 trocadas o efeito intra-cidade foi −0,02 p.p. (t = −0,43, p = 0,67). Nas únicas 7 urnas com carga no domingo, Flávio venceu por 67,34% a 26,51%.",
        "troca",
        teto=oc["3.1"]["teto"],
        limiar="meia",
    )
    add(
        "3.2",
        "Lote antigo UE2013 e Experimento Natural de troca no 2ºT",
        "Excluído",
        "direto",
        "Trocada a UE2013 no meio da manhã (12 seções), a falha manual caiu de 96,4% para 8,9%.",
        "No Censo de 497.897 seções (Frente 1), o lote UE2013 (seriais 1,65M–1,70M, 10.893 urnas = 2,19% do parque, sensor óptico DigitalPersona 5301 de 2013) concentra 97,7% (43 de 44) das seções do Brasil com ≥90% de liberação manual (média 10,95%, e 9,48% nas UE2015, contra 5,93% nas UE2020 e 5,95% nas UE2022). Prova definitiva (Passo 1A): em 12 seções críticas que abriram às 08h00 do 2ºT com a mesma UE2013 defeituosa (96,41% manual na manhã) e foram substituídas no meio da manhã por urna de contingência (*ME.jez), na mesma sala, mesmos mesários e mesma fila, a liberação manual despencou imediatamente de 96,41% para 8,93% (biometria saltou de 1,54% para 86,84%)! No Censo de 94.233 Escolas (Frente 15), o efeito eleitoral da UE2013 dentro do mesmo prédio escolar é zero (−0,01 p.p., t = −0,17, p = 0,86).",
        "geracao",
        teto=oc["3.2"]["teto"],
        limiar="meia",
    )
    add(
        "3.3",
        "Software trocando votos (build 10.23.0.0, HSM e TPS)",
        "Possível",
        "fora",
        "Build única 10.23.0.0 e 803/803 assinaturas íntegras; fechar Split-World exige VVPAT.",
        "Arqueologia de código-fonte C/C++ e binários (Frente 10) + Literatura TPS 2009–2025 (Frente 9): 100% das urnas rodam a mesma build '10.23.0.0 - Praia da Barra do Cahy' (SEVIN serial 20260708, hash SHA-512 de -mr.ver idêntico no país, InfoEleitor::AdicionaVoto e ordenação canônica em rdv.asn1, partição ueminix cifrada com AES-256-XTS). Urnas UE2013/2015 usam HSM MSD (ECDSA P-521, assinatura em 67–81 s, certificados UE2013 expirando em abr/2027) e UE2020/2022 usam MSE (EdDSA Ed521 + SHAKE-256, 9 s). Todas as 803/803 assinaturas testadas foram verificadas matematicamente. Os pontos cegos estruturais remanescentes são a ausência de Reproducible Builds / VVPAT (Software Independence) e a baixa taxa biométrica no Teste de Integridade (0% no tradicional e 15%–25% no voluntário vs. 94% na seção real).",
        "lacuna",
    )

    # ==================== ESTÁGIO 4: ARQUIVOS ====================
    add(
        "4.1",
        "RDV voto a voto e Log da urna diferentes do Boletim",
        "Excluído",
        "direto",
        "RDV = BU em 100% das 245 mil cédulas binárias; Log = BU em 99,6% das 3.000 urnas.",
        "Decodificação binária ASN.1 voto a voto de 958 arquivos -rdv.dat (200 seções das 27 UFs na Frente 5 + 379 seções × 2 turnos na Frente 12 = 244.937 votos): 100,0000% idênticos aos respectivos -bu.dat (zero divergências em Lula, Flávio, brancos e nulos). " + oc["4.1"]["tecnico"],
        "logbu",
        teto=oc["4.1"]["teto"],
    )
    add(
        "4.2",
        "Números fabricados no boletim (Dígitos no Censo)",
        "Excluído",
        "direto",
        "Últimos dígitos e pares 00–99 uniformes nos dois turnos e no censo (p = 0,88 e 0,95).",
        "No Censo de 497.897 seções (Frente 4), o qui-quadrado de uniformidade dos pares de dígitos finais 00..99 (100 categorias, gl = 99) dá p = 0,88 no 1º turno e p = 0,95 no 2º turno, sem desvios nas 27 UFs. " + oc["4.2"]["tecnico"],
        "digitos",
    )
    add(
        "4.3",
        "Enchimento de urna (Comparecimento ≥95% e Klimek)",
        "Excluído",
        "direto",
        "Só 0,15% passaram de 95% de presença; no censo, Klimek α ≈ 0,001 nos dois lados.",
        oc["4.3"]["tecnico"] + " No Censo de 497.897 seções (Frentes 4 e 15), apenas 1.044 seções (0,21%) tiveram comparecimento ≥95% no 2ºT (208 com Lula ≥80% e 37 com Flávio ≥80%; teto no censo de 1.812 votos acima de 95%), e o modelo de Klimek et al. (PNAS 2012) dá α ≈ 0,001 nos dois candidatos.",
        "enchimento",
        teto=oc["4.3"]["teto"],
    )
    add(
        "4.4",
        "Fluxo anômalo de eleitores no log",
        "Excluído",
        "estatístico",
        oc["4.4"]["frase"],
        oc["4.4"]["tecnico"],
        "anomalias",
        teto=oc["4.4"]["teto"],
        limiar="meia",
    )
    add(
        "4.5",
        "Queda de votos nulos na PB/AL e salto no RN (-rdv.dat)",
        "Excluído",
        "direto",
        "No 1ºT, 61,5% dos nulos de Gov na PB digitaram '13' (Tela 4) e erraram Pres (Tela 5).",
        "Decodificação dos dígitos exatos teclados nos votos nulos (campo VotoDigitado, tag 0x81 em -rdv.dat) em 379 seções × 2 turnos (758 arquivos RDV, 196.762 votos, Frente 12): no 1ºT, na PB e em AL (onde o PT não encabeçou chapa competitiva ao Governo), milhares de eleitores acharam que a Tela 4 (Governador) já era Presidente e digitaram '13' (61,5% de todos os nulos de Gov na PB [1.202/1.956] e 48,8% em AL [776/1.590] vs. apenas 3,2% e 6,6% para '22'). Em seguida, na Tela 5 (Presidente), digitaram os números dos seus candidatos locais a Governador/Senador ('15', '11', '45', '10', '40' = 55,3% de todos os nulos presidenciais do 1ºT). Como PB e AL decidiram Governador no 1ºT, no 2ºT a urna abriu com UMA ÚNICA TELA (Presidente): a inversão de telas sumiu (−85,8% nos códigos locais, de 1.124 para 160 votos) e os nulos presidenciais caíram −63,7% (r = +0,814, t = +22,36). Já no RN (onde houve 2ºT para Governador 13 vs 44 após eliminação de Álvaro Dias PL 22), houve 351 votos nulos '22' para Governador (48,3%) e salto de +145,7% nos nulos '44' para Presidente!",
        "rdvnulos",
        teto=0,
    )

    # ==================== ESTÁGIO 5: TOTALIZAÇÃO ====================
    add(
        "5.1",
        "Soma diferente do total oficial (499.207 Seções → Brasil)",
        "Excluído",
        "direto",
        "499.207 seções somam 100,0000% do oficial; achadas as 2 últimas seções pós-22h45.",
        "Censo Seção a Seção 1ºT × 2ºT nas 499.207 seções instaladas nos 28 pacotes BWEB (Frentes 4 e 15): no 1ºT, a soma das 499.206 seções fecha com erro ZERO em todas as colunas (incluindo os 5.246 votos nulos técnicos vnt do candidato 28). No 2ºT, os 28 arquivos de UF somam exatamente 64.255.891 (Lula) e 59.825.984 (Flávio), e a base seção a seção identificou nominalmente as 2 últimas seções do país transmitidas após o snapshot de 22:45:18 (snt = 2, esnt = 441 aptos): Chapada Gaúcha-MG Z320 S185 (23:08:43, 102 aptos, 78 Lula, 18 Flávio) e Salvador-BA Z4 S374 (23:21:51, 339 aptos, 263 Lula, 39 Flávio), somando exatos 441 aptos e fechando 100,0000% das 499.207 seções com erro zero!",
        "totalizacao",
        teto=0,
    )

    # ==================== ESTÁGIO 6: HORÁRIO ====================
    add(
        "6.1",
        "Votos depois do horário e fusos do Amazonas/Noronha",
        "Excluído",
        "direto",
        "Zero urnas abertas < 8h ou fechadas < 17h BRT no censo; ≈31 mil votos pós-17h no 2ºT.",
        "Corrigindo os fusos reais das urnas no Censo de 497.897 seções (Frente 1: Amaturá-AM em UTC−5; Boca do Acre, Lábrea e Pauini em UTC−4; Fernando de Noronha em UTC−2) e na Frente 13: ZERO urnas abriram antes das 08h00 BRT (0/497.897), ZERO encerraram antes das 17h00 BRT (0/497.897) e ZERO emitiram BU antes do encerramento (mediana 136 s). Pela regra do art. 153 da Lei 4.737/1965 (Código Eleitoral) e Res. TSE 23.736/2024, eleitores na fila às 17h recebem senha e votam: foram 30.528 votos pós-17h no 2ºT (1,8% das seções após 17h15) contra 3.548.608 no 1ºT (25,8% das seções após 17h15, devido à fila de 5 cargos).",
        "pos17",
        teto=oc["6.1"]["teto"],
        teto_pt=oc["6.1"]["teto_pt"],
        lo=oc["6.1"]["teto_lo"],
    )

    # ==================== ESTÁGIO 7: ELEITOR ====================
    add(
        "7.1",
        "Coerção ou compra de voto",
        "Possível",
        "fora",
        oc["7.1"]["frase"],
        oc["7.1"]["tecnico"],
        "caudas",
    )

    # ==================== ESTÁGIO 8: SINAIS ====================
    add(
        "8.1",
        "Flávio perdeu votos em 939 cidades (82.155 seções)",
        "Excluído",
        "direto",
        "O esperado pelo acaso era 1.091 a 1.156; queda espalha-se por 70–100% das seções.",
        oc["8.1"]["tecnico"] + " No Censo de 497.897 seções (Frente 15), Flávio caiu em 82.155 seções (16,5%) e Lula em 9.575 (1,9%). No Censo dos 3.102 BUs dos 25 municípios críticos (Passo 1B), a queda espalha-se por 70% a 100% das seções da cidade (11/11 em Rafael Godeiro-RN, 26/27 em São Tomé-RN, 61/69 em Porto Calvo-AL), e nos vizinhos-espelho pró-Flávio (Belo Monte-AL e Sto. Antônio de Lisboa-PI) Flávio subiu em 100% das seções (16/16 e 24/24).",
        "defeccao",
    )
    add(
        "8.2",
        "37 cidades com 88%+ para Lula",
        "Excluído",
        "direto",
        oc["8.2"]["frase"],
        oc["8.2"]["tecnico"],
        "hiper",
    )
    add(
        "8.3",
        "Comparecimento caiu no Norte; só Flávio perdeu",
        "Excluído",
        "direto",
        oc["8.3"]["frase"],
        oc["8.3"]["tecnico"],
        "norte",
    )
    add(
        "8.4",
        "Voto casado Direita Local + Lula (67,86M linhas Multi-Cargo)",
        "Excluído",
        "direto",
        "Em 191.810 seções (38,6% do país), Direita Gov + Lula > 100% na mesma urna no 1ºT.",
        "Censo Multi-Cargo de 67.858.974 registros nos 5 cargos do 1ºT (Frente 3) + Censo das 39.739 seções das 6 UFs com 2ºT de Governador (Frente 15): pelo Princípio da Casa dos Pombos, em 191.810 seções do Brasil (38,57%), a soma (% Governador de Direita + % Lula) ultrapassa 100% na mesma urna física do 1ºT (provando que milhões de eleitores votaram em Governador/Deputado de Direita e em Lula na mesma sessão). No 2ºT das 6 UFs com Governador em disputa (AC, AM, DF, ES, RN, TO), houve 0 divergências de comparecimento entre Presidente e Governador em 100% das 37.840 seções regulares, e em 10.906 urnas (27,4%) o candidato de Direita ao Governo subiu no 2ºT enquanto Flávio caiu na mesma urna — incluindo 3.854 urnas (47,25%) no Amazonas onde a candidata do próprio PL 22 (Profª Maria do Carmo) ganhou votos enquanto Flávio (PL 22) perdeu votos!",
        "multicargo",
        teto=0,
    )
    add(
        "8.5",
        "Tetos determinísticos de 3ª Via no Censo (497.897 seções)",
        "Excluído",
        "direto",
        "Excesso estrito sobre 100% da 3ª via soma 36,3 mil votos nas cidades (0,8% da margem).",
        "Censo Seção a Seção 1ºT × 2ºT nas 497.897 seções do Brasil (Frente 15) e 5.571 municípios (Frente 2): o Teto 3 Ideológico (sem defecção de eleitores de Zema/Caiado/Renan) é superado em 316.334 seções (63,53% do país, +2,14 mi votos), provando migração massiva do centro/direita moderada. Já o Teto 1 Determinístico (Cand_2T > Cand_1T + 100% Outros_1T + max(0, ΔVV)) é superado em 57.804 seções (+202.671 votos = 4,58% da margem) e, no agregado municipal, em 514 cidades (+36.324 votos = 0,82% da margem), refletindo o realinhamento de prefeitos/governadores eleitos no 1ºT (Frente 3) e a extinção do erro de inversão de telas nos votos nulos da PB e AL (Frente 12).",
        "tetos",
        teto=202671,
        teto_pt=36324,
    )

    save_both("casos", casos)

    # ==================== PROVAS (dados dos gráficos visuais) ====================
    # Mantém todas as linhas existentes de old_provas e adiciona/atualiza as novas frentes
    pv = [p for p in old_provas if p["caso"] not in ("1.3", "2.6", "4.5", "8.4", "8.5")]
    def P(caso, k, rot="", v=None, v2=None, lo=None, hi=None, n=None):
        pv.append({"caso": caso, "k": k, "rotulo": rot, "v": v, "v2": v2, "lo": lo, "hi": hi, "n": n})

    # Atualiza 2.4 com a linha de Zona/Escola do Censo (Frentes 8 e 15)
    if not any(p["caso"] == "2.4" and p["k"] == "nivel_escola" for p in pv):
        P("2.4", "nivel_escola", "Mesma escola (Censo 94.233 escolas)", 0.01, None, -0.02, 0.04)

    # Atualiza 3.2 para incluir UE2013 no Censo e a troca no meio da manhã (Passo 1A)
    pv = [p for p in pv if not (p["caso"] == "3.2" and p["k"] in ("UE2013", "UE2015", "UE2020", "UE2022", "troca12"))]
    P("3.2", "UE2013", "UE2013 (1,65–1,70M)", 10.95, 0.04, -0.06, 0.14, n=10893)
    P("3.2", "UE2015", "UE2015 (1,70–2,00M)", 9.48, -0.01, -0.13, 0.11, n=87782)
    P("3.2", "UE2020", "UE2020 (2,00–2,30M)", 5.93, 0.00, -0.04, 0.04, n=244917)
    P("3.2", "UE2022", "UE2022 (2,30–2,60M)", 5.95, 0.00, -0.05, 0.05, n=154305)
    P("3.2", "troca12", "12 seções UE2013 trocadas no 2ºT (manhã → tarde)", 96.41, 8.93, n=12)

    # Atualiza 4.1 para incluir RDV x BU (100,0000% em 579 urnas / 244.937 cédulas)
    if not any(p["caso"] == "4.1" and p["k"] == "okRDV" for p in pv):
        P("4.1", "okRDV", "RDV × Boletim (245 mil votos)", 100.0, 100.0, n=579)

    # 1.3 Super-idosos (Frente 14: Comparecimento Real por Faixa Etária no Censo)
    P("1.3", "f18_69", "18 a 69 anos (obrigatório)", 81.52, 109904112, lo=134819708, hi=24915596)
    P("1.3", "f70_79", "70 a 79 anos (facultativo)", 61.76, 7180388, lo=11625863, hi=4445475)
    P("1.3", "f80_89", "80 a 89 anos (facultativo)", 33.23, 1630677, lo=4907160, hi=3276483)
    P("1.3", "f90_99", "90 a 99 anos (facultativo)", 8.64, 129906, lo=1503164, hi=1373258)
    P("1.3", "f100", "100+ anos (centenários)", 0.72, 2141, lo=297977, hi=295836)
    P("1.3", "flavio74", "Cidades idosas c/ presença ≥85%: Flávio venceu", 100.0, 74, n=74)

    # 2.6 Prova física das digitais nas liberações manuais (-wsqman.jez, Frente 11)
    # Seleciona pontos representativos de todas as faixas de b2 nas 640 seções auditadas
    wsq_pts = []
    for s in f11["secoes_auditadas"]:
        for t_key, t_num in (("t1", 1), ("t2", 2)):
            td = s.get(t_key)
            if not td or not td.get("vsc_ok"):
                continue
            b2 = td.get("bu_b2_manual")
            sz = td.get("wsqman_bytes")
            comp = td.get("bu_comp")
            if b2 is None or sz is None:
                continue
            wsq_pts.append({
                "b2": int(b2),
                "kb": round(sz / 1024.0, 1),
                "comp": int(comp or 0),
                "rot": f"{s['nm_mun'].title()} ({s['uf']}) Z{s['zona']}/S{s['secao']} · {t_num}ºT",
                "mod": td.get("bu_modelo") or ("UE2013" if (td.get("bu_urna_serial") or 0) < 1700000 else "Moderna"),
            })
    # Ordena por b2 e pega ~90 pontos cobrindo todo o espectro (incluindo todos os extremos b2 >= 150)
    wsq_pts.sort(key=lambda x: (x["b2"], x["kb"]))
    sampled_wsq = []
    high_pts = [x for x in wsq_pts if x["b2"] >= 120]
    low_pts = [x for x in wsq_pts if x["b2"] < 120]
    step = max(1, len(low_pts) // 65)
    sampled_wsq = low_pts[::step] + high_pts
    for idx, pt in enumerate(sampled_wsq):
        P("2.6", f"p{idx}", pt["rot"], pt["b2"], pt["kb"], lo=pt["comp"], n=1 if pt["mod"] == "UE2013" else 0)
    P("2.6", "reg", "Lei linear: 35,05 KB × b2 (R² = 0,9948)", 35.0499, -11.339, lo=0.9948, hi=640)

    # 4.5 Queda de votos nulos na PB/AL e salto no RN (-rdv.dat, Frente 12)
    P("4.5", "gov_pb_13", "Gov PB 1ºT (Tela 4): digitaram '13' (Lula)", 61.45, 1202, lo=1956, hi=3.22)
    P("4.5", "gov_al_13", "Gov AL 1ºT (Tela 4): digitaram '13' (Lula)", 48.81, 776, lo=1590, hi=6.60)
    P("4.5", "pres_pbal_loc1", "Pres PB+AL 1ºT (Tela 5): nº Gov local (15/11/45/10/40)", 55.31, 1124, lo=2032, hi=160)
    P("4.5", "pres_pbal_loc2", "Pres PB+AL 2ºT (Tela única): mesmos nº locais (−85,8%)", 16.49, 160, lo=970, hi=-85.77)
    P("4.5", "gov_rn_22", "Gov RN 2ºT (Tela 1, 13×44): digitaram '22' (PL eliminado)", 48.28, 351, lo=727, hi=86)

    # 8.4 Voto casado Direita Local + Lula (Frentes 3 e 15)
    P("8.4", "casado_lula_1t", "1ºT (497.897 urnas): Direita Gov + Lula > 100%", 38.57, 191810, lo=497897)
    P("8.4", "casado_flav_1t", "1ºT (497.897 urnas): Esquerda Gov + Flávio > 100%", 3.48, 17309, lo=497897)
    P("8.4", "gov2t_dir_sobe", "2ºT (6 UFs, 39.739 urnas): Gov Direita subiu e Flávio caiu", 27.44, 10906, lo=39739)
    P("8.4", "gov2t_am_pl22", "2ºT Amazonas (8.156 urnas): Gov PL 22 subiu e Flávio 22 caiu", 47.25, 3854, lo=8156)

    # 8.5 Tetos determinísticos de 3ª Via no Censo (Frentes 2 e 15)
    P("8.5", "teto3_sec", "Teto Ideológico (sem defecção de Zema/Caiado/Renan)", 63.53, 2136622, lo=316334, hi=48.23)
    P("8.5", "teto1_sec", "Teto 1 Seções (100% 3ª Via + ΔVV, 57.804 seções)", 11.61, 202671, lo=57804, hi=4.58)
    P("8.5", "teto2_sec", "Teto 2 Estrito Seções (+ ΔComp − ΔBN, 45.005 seções)", 9.04, 147803, lo=45005, hi=3.34)
    P("8.5", "teto1_mun", "Teto 1 Cidades (514 de 5.571 municípios)", 9.23, 36324, lo=514, hi=0.82)

    save_both("provas", pv)

    # ==================== ATUALIZA DIMS E SECOES COM UE2013 + GERA CENSO_CORTES (497.508 SEÇÕES) ====================
    print("Loading 499.207 census sections to tag UE2013 and compute 100% census cuts...")
    df = pd.read_csv(os.path.join(DATA, "derivados", "censo_secoes_1t_2t_presidente.csv.gz"), low_memory=False)
    # Mapa de modelo_serie_1t para as 9.600 seções de secoes.json
    # s['id'] = "RS-0104-0055-85197" -> uf, int(zona), int(secao)
    mod_map = {}
    for row in df[["uf", "zona", "secao", "modelo_serie_1t"]].itertuples(index=False):
        mod_map[(row.uf, int(row.zona), int(row.secao))] = row.modelo_serie_1t

    # Atualiza dims.json para ter UE2013 (urna_3) além de UE2015 (urna_0), UE2020 (urna_1), UE2022 (urna_2)
    new_dims = []
    added_ue2013 = False
    for d in old_dims:
        new_dims.append(d)
        if d["id"] == "urna_2" and not added_ue2013:
            new_dims.append({
                "id": "urna_3",
                "dim": "urna",
                "grupo": "Urna",
                "titulo": "Geração da urna",
                "ordem": d["ordem"],
                "cod": 3,
                "rotulo": "UE2013 (lote 1,65M)",
            })
            added_ue2013 = True
    save_both("dims", new_dims)

    # Atualiza secoes.json para marcar urna = 3 quando for UE2013 (< 1.700.000)
    ue2013_in_sample = 0
    for s in old_secoes:
        parts = s["id"].split("-")
        uf_s, z_s, sec_s = parts[0], int(parts[1]), int(parts[2])
        m_s = mod_map.get((uf_s, z_s, sec_s))
        if m_s == "UE2013":
            s["urna"] = 3
            ue2013_in_sample += 1
    print(f"Tagged {ue2013_in_sample} UE2013 sections in 9.600 sample.")
    save_both("secoes", old_secoes, 3)

    # Agora calcula os recortes no CENSO 100% (497.508 seções válidas do Brasil, sem amostragem!)
    # para exibir nos tooltips e no alternador Censo 100% da aba Explorar recortes!
    br = df[(df["uf"] != "ZZ") & (df["vv_1t"] > 0) & (df["vv_2t"] > 0)].copy()
    mun_g = br.groupby(["uf", "cd_mun"], as_index=False).agg(
        m_l1=("lula_1t", "sum"),
        m_v1=("vv_1t", "sum"),
        m_l2=("lula_2t", "sum"),
        m_v2=("vv_2t", "sum"),
        m_aptos=("aptos_2t", "sum"),
    )
    mun_g["mL1"] = mun_g["m_l1"] / mun_g["m_v1"] * 100.0
    mun_g["mL2"] = mun_g["m_l2"] / mun_g["m_v2"] * 100.0
    mun_g["mdL"] = mun_g["mL2"] - mun_g["mL1"]
    br = br.merge(mun_g[["uf", "cd_mun", "mL1", "mdL", "m_aptos"]], on=["uf", "cd_mun"], how="left")

    br["l1_p"] = br["lula_1t"] / br["vv_1t"] * 100.0
    br["l2_p"] = br["lula_2t"] / br["vv_2t"] * 100.0
    br["xdL"] = (br["l2_p"] - br["l1_p"]) - br["mdL"]

    CAPITAIS = {
        ("AC", "RIO BRANCO"), ("AL", "MACEIÓ"), ("AM", "MANAUS"), ("AP", "MACAPÁ"),
        ("BA", "SALVADOR"), ("CE", "FORTALEZA"), ("DF", "BRASÍLIA"), ("ES", "VITÓRIA"),
        ("GO", "GOIÂNIA"), ("MA", "SÃO LUÍS"), ("MG", "BELO HORIZONTE"), ("MS", "CAMPO GRANDE"),
        ("MT", "CUIABÁ"), ("PA", "BELÉM"), ("PB", "JOÃO PESSOA"), ("PE", "RECIFE"),
        ("PI", "TERESINA"), ("PR", "CURITIBA"), ("RJ", "RIO DE JANEIRO"), ("RN", "NATAL"),
        ("RO", "PORTO VELHO"), ("RR", "BOA VISTA"), ("RS", "PORTO ALEGRE"), ("SC", "FLORIANÓPOLIS"),
        ("SE", "ARACAJU"), ("SP", "SÃO PAULO"), ("TO", "PALMAS"),
    }
    REG_MAP = {
        "AC": 0, "AM": 0, "AP": 0, "PA": 0, "RO": 0, "RR": 0, "TO": 0,
        "AL": 1, "BA": 1, "CE": 1, "MA": 1, "PB": 1, "PE": 1, "PI": 1, "RN": 1, "SE": 1,
        "DF": 2, "GO": 2, "MS": 2, "MT": 2,
        "ES": 3, "MG": 3, "RJ": 3, "SP": 3,
        "PR": 4, "RS": 4, "SC": 4,
    }
    GOV_SET = {"AC", "AM", "DF", "ES", "RN", "TO"}
    URN_MAP = {"UE2015": 0, "UE2020": 1, "UE2022": 2, "UE2013": 3}

    br["reg_c"] = br["uf"].map(REG_MAP)
    is_cap = [((u, str(m).upper().strip()) in CAPITAIS) for u, m in zip(br["uf"], br["nm_mun"])]
    br["porte_c"] = np.where(is_cap, 0, np.where(br["m_aptos"] >= 100000, 1, np.where(br["m_aptos"] >= 20000, 2, 3)))
    br["forca_c"] = np.where(br["mL1"] < 40, 0, np.where(br["mL1"] < 55, 1, 2))
    br["gov_c"] = np.where(br["uf"].isin(GOV_SET), 0, 1)

    man1_p = br["biom_sem_hab_1t"] / br["comp_1t"].replace(0, np.nan) * 100.0
    el_perf = br["eleitores_perfil"].replace(0, np.nan)
    scad_p = (el_perf - br["biometria_perfil"]) / el_perf * 100.0
    nb1_p = (man1_p.fillna(0) + scad_p.fillna(0)).clip(0, 100)

    br["nb_c"] = np.where(nb1_p < 5, 0, np.where(nb1_p < 10, 1, np.where(nb1_p < 15, 2, np.where(nb1_p < 25, 3, 4))))
    br["man_c"] = np.where(man1_p < 3, 0, np.where(man1_p < 6, 1, np.where(man1_p < 10, 2, 3)))
    br["scad_c"] = np.where(scad_p < 2, 0, np.where(scad_p < 5, 1, np.where(scad_p < 10, 2, 3)))
    br["urna_c"] = br["modelo_serie_1t"].map(URN_MAP).fillna(1).astype(int)

    e70_p = br["e70_perfil"] / el_perf * 100.0
    esc_p = br["baixa_esc_perfil"] / el_perf * 100.0
    T2 = br["comp_2t"] / br["aptos_2t"].replace(0, np.nan) * 100.0
    T1 = br["comp_1t"] / br["aptos_1t"].replace(0, np.nan) * 100.0
    dT = T2 - T1

    br["idade_c"] = np.where(e70_p < 5, 0, np.where(e70_p < 9, 1, np.where(e70_p < 15, 2, 3)))
    br["esc_c"] = np.where(esc_p < 20, 0, np.where(esc_p < 30, 1, np.where(esc_p < 43, 2, 3)))
    br["comp_c"] = np.where(T2 < 75, 0, np.where(T2 < 80, 1, np.where(T2 < 85, 2, 3)))
    br["dcomp_c"] = np.where(dT < -2, 0, np.where(dT < 0, 1, np.where(dT < 2, 2, 3)))

    # Calcula sumário 1D no Censo 100% para cada id de dimensão (exibido no tooltip e KPIs do Explorar)
    tot_aptos = float(br["aptos_2t"].sum())
    censo_summary = []
    def calc_slice(sub, slice_id):
        n = len(sub)
        if n == 0:
            return
        vv2 = float(sub["vv_2t"].sum())
        vv1 = float(sub["vv_1t"].sum())
        w = sub["vv_2t"].to_numpy(dtype=np.float64)
        x = sub["xdL"].to_numpy(dtype=np.float64)
        W = w.sum()
        m = float((w * x).sum() / W)
        se = float(math.sqrt(max(0.0, ((w * (x - m)) ** 2).sum())) / W)
        nb1_val = float((sub["biom_sem_hab_1t"].sum()) / max(1, sub["comp_1t"].sum()) * 100.0)
        censo_summary.append({
            "id": slice_id,
            "n": int(n),
            "pa": float(sub["aptos_2t"].sum() / tot_aptos * 100.0),
            "man1": nb1_val,
            "l1": float(sub["lula_1t"].sum() / vv1 * 100.0),
            "l2": float(sub["lula_2t"].sum() / vv2 * 100.0),
            "x": m,
            "lo": m - 1.96 * se,
            "hi": m + 1.96 * se,
            "vv": vv2,
            "teto": max(0.0, m + 1.96 * se) / 100.0 * vv2,
        })

    calc_slice(br, "all")
    col_map = {
        "reg": "reg_c", "porte": "porte_c", "forca": "forca_c", "gov": "gov_c",
        "nb": "nb_c", "man": "man_c", "scad": "scad_c", "urna": "urna_c",
        "idade": "idade_c", "esc": "esc_c", "comp": "comp_c", "dcomp": "dcomp_c",
    }
    for d in new_dims:
        dim_k = d["dim"]
        if dim_k == "uf":
            calc_slice(br[br["uf"] == d["rotulo"]], d["id"])
        elif dim_k in col_map:
            calc_slice(br[br[col_map[dim_k]] == d["cod"]], d["id"])

    save_both("censo", censo_summary, 4)
    print("Done generating all datasets!")

if __name__ == "__main__":
    main()
