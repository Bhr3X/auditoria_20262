# Veredito do 2º turno — auditoria visual MECE (23 Frentes · Censo 100% BWeb/CEFT 2ºT + Série Histórica 2014–2026)

Painel estático que testa, uma a uma, **32 hipóteses de fraude** (**23 frentes MECE**) no 2º turno presidencial de 2026 (Lula × Flávio Bolsonaro) e no painel histórico de 12 anos (`2014 × 2018 × 2022 × 2026`), organizadas de forma MECE pelas 8 etapas da eleição: cadastro, mesa, urna, arquivos, totalização, horário, eleitor e sinais apontados no resultado.

Cada hipótese recebe um veredito visual com gráfico interativo D3 e botão **i** (tooltip) com a prova técnica completa:

- **Excluído (29)**: os dados descartam (o que a hipótese exige não aparece, ou caberia em muito menos votos do que os necessários para virar).
- **Improvável (1)**: o teste disponível tem margem de erro ampla, mas o efeito pontual é próximo de zero.
- **Possível (2)**: os arquivos públicos não alcançam a hipótese; fecha com outra perícia física.
- **Provável (0)**: os dados apontam. Nenhuma hipótese ficou aqui.

## Páginas

- **Veredito**: placar (30 hipóteses medidas pelos dados + 2 lacunas físicas), quadro MECE interativo (etapa × veredito), teto de votos de cada hipótese contra os votos necessários para virar, e a virada do 1º para o 2º turno.
- **Provas, caso a caso**: um cartão visual por hipótese (32 cartões), com o gráfico D3 que sustenta o veredito. Todos os detalhes técnicos, regressões e contagens exatas do Censo 100% ficam nos **tooltips** e no botão **i**.
- **Explorar recortes**: escolha qualquer grupo de seções (biometria, geração de urna `UE2013..UE2022`, região, perfil do eleitor, governador eleito, UF) e veja se Lula ganhou ali mais do que na própria cidade — com números da amostra física de BUs e do **Censo 100% (499.205 seções em BWeb 2ºT)** nos tooltips.

## Estrutura

```
index.html   página (HTML + CSS)
vx.js        gráficos e cálculos (d3 v7)
shim.js      carrega data/*.json e roda os cálculos
data/        casos (32), provas (400), secoes (9.600), dims (87), norte (954), censo (75)
scripts/     analise_v4_mece.py, gerar_datasets_v4.py, update_site_veredito_22frentes.py, audit_relatorio_pericial_bweb2t.py e audit_ceft2t_cesp2t_censo.py
```

Para ver localmente: `python3 -m http.server` nesta pasta e abra `http://localhost:8000`.

Para publicar no GitHub Pages: Settings → Pages → Deploy from a branch → `main` / raiz.

## Fontes e método

Censo de 100% da totalização e cadastro do TSE em 2026 (**499.207 seções** pareadas 1ºT × 2ºT, **5.570 municípios**, **2.637 zonas**, **94.056 escolas com GPS**, **51.580 bairros**, **158,75 milhões de eleitores**, **9,53 milhões de operações RAE**, **2,49 milhões de transferências de domicílio**, **560.332 eleitores em TTE**, **1,97 milhão de eleitores PcD**, **5,03 milhões de linhas de log `GEDAI-UE` com 4.333 envelopes `.vsc`**, **67,86 milhões de registros multi-cargo**, **1,60 milhão de registros de custódia/TPM**), combinado com o **Experimento Natural Longitudinal `2022 × 2026`** (**461.219 seções pareadas**, incluindo **215.349 seções** onde urnas `UE2009–2015` foram substituídas por `UE2020/UE2022`), o **Painel Histórico de 12 Anos `2014 × 2018 × 2022 × 2026`** (**3.707.067 urnas** nos 8 turnos presidenciais) e a amostra aleatória estratificada por UF de **9.600 boletins de urna**, **3.000 logs**, **958 arquivos binários `-rdv.dat`** e **640 tabelas `.vsc` / `-wsqman.jez`**. Horários convertidos para Brasília. Intervalos de confiança de 95%.
