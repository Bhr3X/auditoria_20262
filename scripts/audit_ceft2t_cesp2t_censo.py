#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import zipfile, csv, io, glob, os, json, hashlib
from collections import defaultdict, Counter

base_dir = "./data"
ceft_dir = os.path.join(base_dir, "ceft_2t")
cesp_dir = os.path.join(base_dir, "cesp_2t_2510")

# 1. Verify SHA-512 of all 28 CEFT_2t and 28 CESP_2t_2510
sha_ok_ceft = 0
for zp in sorted(glob.glob(os.path.join(ceft_dir, "CEFT_2t_*.zip"))):
    sp = zp + ".sha512"
    exp = open(sp, encoding="latin-1").read().split()[0].lower()
    act = hashlib.sha512(open(zp, "rb").read()).hexdigest().lower()
    if exp == act:
        sha_ok_ceft += 1

sha_ok_cesp = 0
for zp in sorted(glob.glob(os.path.join(cesp_dir, "CESP_2t_*.zip"))):
    sp = zp + ".sha512"
    exp = open(sp, encoding="latin-1").read().split()[0].lower()
    act = hashlib.sha512(open(zp, "rb").read()).hexdigest().lower()
    if exp == act:
        sha_ok_cesp += 1

print(f"SHA-512 verified: CEFT_2t={sha_ok_ceft}/28 | CESP_2t_2510={sha_ok_cesp}/28")

# 2. Load CESP_2t_2510 (CSEC and CCONT)
csec_loads = set()
ccont_loads = set()
n_csec = 0
n_ccont = 0
for zp in sorted(glob.glob(os.path.join(cesp_dir, "CESP_2t_*.zip"))):
    with zipfile.ZipFile(zp) as zf:
        for cn in zf.namelist():
            if cn.startswith("csec_") and cn.endswith(".csv"):
                with zf.open(cn) as f:
                    for r in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";"):
                        n_csec += 1
                        csec_loads.add((r["SG_UF"], r["NR_URNA_ESPERADA"], r["CD_CARGA_URNA_ESPERADA"], r["CD_FLASHCARD_URNA_ESPERADA"]))
            elif cn.startswith("ccont_") and cn.endswith(".csv"):
                with zf.open(cn) as f:
                    for r in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";"):
                        n_ccont += 1
                        ccont_loads.add((r["SG_UF"], r["NR_URNA_ESPERADA"], r["CD_CARGA_URNA_ESPERADA"], r["CD_FLASHCARD_URNA_ESPERADA"]))

print(f"CESP_2t (25/10): CSEC rows={n_csec:,} | CCONT rows={n_ccont:,}")

# 3. Parse CEFT_2t
ceft_secs = {}
tp_div_cnt = Counter()
orig_cnt = Counter()
status_cnt = Counter()
tpm_ok = 0

for zp in sorted(glob.glob(os.path.join(ceft_dir, "CEFT_2t_*.zip"))):
    with zipfile.ZipFile(zp) as zf:
        cn = [n for n in zf.namelist() if n.endswith(".csv")][0]
        with zf.open(cn) as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";"):
                key = (r["SG_UF"], r["CD_MUNICIPIO"], r["NR_ZONA"], r["NR_SECAO"])
                tp_div = (r.get("TP_DIVERGENCIA") or "").strip()
                orig = (r.get("DS_ORIGEM_VOTO") or "").strip()
                tp_div_cnt[tp_div] += 1
                orig_cnt[orig] += 1
                if r.get("NR_SRI_TPM_GERACAO_MIDIA") and r.get("NR_SRI_TPM_TRANSM_CORRESP"):
                    tpm_ok += 1
                u_esp = r["NR_URNA_ESPERADA"]
                c_esp = r["CD_CARGA_URNA_ESPERADA"]
                f_esp = r["CD_FLASHCARD_URNA_ESPERADA"]
                u_efe = r["NR_URNA_EFETIVADA"]
                c_efe = r["CD_CARGA_URNA_EFETIVADA"]
                f_efe = r["CD_FLASHCARD_URNA_EFETIVADA"]
                uf = r["SG_UF"]
                if (u_esp, c_esp, f_esp) == (u_efe, c_efe, f_efe):
                    st = "1_Exata_Titular_CSEC"
                elif (uf, u_efe, c_efe, f_efe) in ccont_loads:
                    st = "2_Contingencia_CCONT"
                elif (uf, u_efe, c_efe, f_efe) in csec_loads:
                    st = "3_Remanejada_CSEC"
                elif c_esp == c_efe:
                    st = "4_Mesma_Carga_Flash_ou_Urna_Trocada"
                else:
                    st = "5_Nova_Carga_Domingo_GEDAI"
                status_cnt[st] += 1
                ceft_secs[key] = (st, tp_div, u_efe, c_efe, f_efe)

print(f"Total CEFT_2t rows: {len(ceft_secs):,} | TPM 100% present: {tpm_ok:,}")
print("Status breakdown:", dict(status_cnt))
print("TP_DIVERGENCIA breakdown:", dict(tp_div_cnt))
print("DS_ORIGEM_VOTO breakdown:", dict(orig_cnt))
