#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import zipfile, csv, io, glob, os, json
from collections import defaultdict

bweb2_dir = "./data/bweb_2t"
bweb1_dir = "./data"

def load_bweb(pattern):
    secs = {}
    for zp in sorted(glob.glob(pattern)):
        with zipfile.ZipFile(zp) as zf:
            csv_name = [n for n in zf.namelist() if n.endswith(".csv")][0]
            with zf.open(csv_name) as f:
                rdr = csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";")
                for r in rdr:
                    if r["CD_CARGO_PERGUNTA"] != "1":
                        continue
                    key = (r["SG_UF"], r["CD_MUNICIPIO"], r["NR_ZONA"], r["NR_SECAO"])
                    s = secs.get(key)
                    if s is None:
                        s = {
                            "uf": r["SG_UF"], "mun": r["CD_MUNICIPIO"], "nm_mun": r["NM_MUNICIPIO"],
                            "zona": r["NR_ZONA"], "secao": r["NR_SECAO"],
                            "aptos": int(r["QT_APTOS"] or 0),
                            "comp": int(r["QT_COMPARECIMENTO"] or 0),
                            "nh": int(r["QT_ELEI_BIOM_SEM_HABILITACAO"] or 0),
                            "dt_ab": r["DT_ABERTURA"],
                            "dt_enc": r["DT_ENCERRAMENTO"],
                            "lula": 0, "flavio": 0, "branco": 0, "nulo": 0, "vv": 0
                        }
                        secs[key] = s
                    v = r["NR_VOTAVEL"]
                    q = int(r["QT_VOTOS"] or 0)
                    if v == "13": s["lula"] += q; s["vv"] += q
                    elif v == "22": s["flavio"] += q; s["vv"] += q
                    elif v == "95": s["branco"] += q
                    elif v == "96": s["nulo"] += q
                    else: s["vv"] += q
    return secs

sec2 = load_bweb(os.path.join(bweb2_dir, "bweb_2t_*.zip"))
sec1 = load_bweb(os.path.join(bweb1_dir, "bweb_1t_*_051020261403.zip"))
print(f"Loaded sec2: {len(sec2):,} | sec1: {len(sec1):,}")

tz_non_brt = {"AC", "AM", "RO", "RR", "MT", "MS", "ZZ"}
le17_sub = defaultdict(lambda: {"n": 0, "comp2": 0, "lula2": 0, "flavio2": 0, "comp1": 0, "lula1": 0, "flavio1": 0, "vv1": 0})

for k, s2 in sec2.items():
    s1 = sec1.get(k)
    dt = s2["dt_enc"] or ""
    parts = dt.split(" ")
    t_part = parts[1] if len(parts) > 1 else ""
    hhmm = t_part[:5]
    if not t_part:
        cat = "5_VAZIO"
    elif hhmm <= "17:00":
        if s2["uf"] in tz_non_brt:
            cat = "1a_<=17:00 (Fusos UTC-4/UTC-5/ZZ)"
        elif hhmm == "17:00":
            cat = "1b_==17:00:00 a 17:00:59 (UTC-3)"
        else:
            cat = "1c_<17:00:00 (UTC-3 100% aptos/relogio)"
    elif hhmm <= "17:15":
        cat = "2_17:01 a 17:15 (Encerramento normal)"
    elif hhmm <= "18:59":
        cat = "3_17:16 a 18:59"
    else:
        cat = "4_>=19:00 (Prorrogadas 19h)"
    st = le17_sub[cat]
    st["n"] += 1
    st["comp2"] += s2["comp"]
    st["lula2"] += s2["lula"]
    st["flavio2"] += s2["flavio"]
    if s1:
        st["comp1"] += s1["comp"]
        st["lula1"] += s1["lula"]
        st["flavio1"] += s1["flavio"]
        st["vv1"] += s1["vv"]

print("\n=== 1. DECOMPOSITION OF DT_ENCERRAMENTO (1T vs 2T IN EXACT SAME SECTIONS) ===")
for cat, st in sorted(le17_sub.items()):
    vv2 = st["lula2"] + st["flavio2"]
    lp2 = 100 * st["lula2"] / vv2 if vv2 else 0
    lp1_vv = 100 * st["lula1"] / st["vv1"] if st["vv1"] else 0
    fp1_vv = 100 * st["flavio1"] / st["vv1"] if st["vv1"] else 0
    l2_1t_two = 100 * st["lula1"] / (st["lula1"] + st["flavio1"]) if (st["lula1"] + st["flavio1"]) else 0
    n_s = st["n"]
    c1 = st["comp1"]
    c2 = st["comp2"]
    d2 = st["lula2"] - st["flavio2"]
    d1 = st["lula1"] - st["flavio1"]
    print(f"{cat:40s} | N={n_s:7,d} | Comp1T={c1:10,d} -> Comp2T={c2:10,d} ({c2-c1:+9,d}) | Lula1T(valid)={lp1_vv:5.2f}% / 1T(LvsF)={l2_1t_two:5.2f}% -> 2T={lp2:5.2f}% | Saldo1T={d1:+10,d} -> Saldo2T={d2:+10,d}")

print("\n=== 2. >=19:00 SECTIONS BY UF: 1T vs 2T IN THOSE EXACT SECTIONS ===")
uf_19 = defaultdict(lambda: {"n": 0, "c1": 0, "c2": 0, "l1": 0, "f1": 0, "vv1": 0, "l2": 0, "f2": 0, "muns": defaultdict(int), "enc1_19": 0})
for k, s2 in sec2.items():
    dt = s2["dt_enc"] or ""
    parts = dt.split(" ")
    t_part = parts[1] if len(parts) > 1 else ""
    if t_part[:5] >= "19:00":
        s1 = sec1.get(k)
        st = uf_19[s2["uf"]]
        st["n"] += 1
        st["c2"] += s2["comp"]
        st["l2"] += s2["lula"]
        st["f2"] += s2["flavio"]
        st["muns"][s2["nm_mun"]] += 1
        if s1:
            st["c1"] += s1["comp"]
            st["l1"] += s1["lula"]
            st["f1"] += s1["flavio"]
            st["vv1"] += s1["vv"]
            t1 = (s1["dt_enc"] or "").split(" ")
            if len(t1) > 1 and t1[1][:5] >= "19:00":
                st["enc1_19"] += 1

for uf, st in sorted(uf_19.items(), key=lambda x: x[1]["n"], reverse=True):
    vv2 = st["l2"] + st["f2"]
    lp2 = 100 * st["l2"] / vv2 if vv2 else 0
    l1_two = 100 * st["l1"] / (st["l1"] + st["f1"]) if (st["l1"] + st["flavio1"] if "flavio1" in st else (st["l1"] + st["f1"])) else 0
    lp1_vv = 100 * st["l1"] / st["vv1"] if st["vv1"] else 0
    n_s = st["n"]
    c1 = st["c1"]
    c2 = st["c2"]
    d2 = st["l2"] - st["f2"]
    top_muns = sorted(st["muns"].items(), key=lambda x: x[1], reverse=True)[:4]
    e19 = st["enc1_19"]
    print(f"{uf} | N={n_s:5,d} (1T>=19h:{e19:4,d}) | Comp1T={c1:8,d} -> Comp2T={c2:8,d} ({c2-c1:+7,d}) | Lula 1T(valid)={lp1_vv:5.2f}% / 1T(LvsF)={l1_two:5.2f}% -> 2T={lp2:5.2f}% | Saldo2T={d2:+8,d} | TopMuns: {top_muns}")

# 3. Check 17:00 vs 17:01-17:15 within the SAME municipality (UTC-3 only)
print("\n=== 3. WITHIN-MUNICIPALITY COMPARISON: ==17:00:xx vs 17:01-17:15 (UTC-3) ===")
mun_1700 = defaultdict(lambda: {"n0": 0, "l0": 0, "vv0": 0, "n1": 0, "l1": 0, "vv1": 0})
for k, s2 in sec2.items():
    if s2["uf"] in tz_non_brt:
        continue
    dt = s2["dt_enc"] or ""
    parts = dt.split(" ")
    t_part = parts[1] if len(parts) > 1 else ""
    hhmm = t_part[:5]
    vv = s2["lula"] + s2["flavio"]
    if vv == 0:
        continue
    m = mun_1700[(s2["uf"], s2["mun"])]
    if hhmm == "17:00":
        m["n0"] += 1; m["l0"] += s2["lula"]; m["vv0"] += vv
    elif "17:01" <= hhmm <= "17:15":
        m["n1"] += 1; m["l1"] += s2["lula"]; m["vv1"] += vv

w_diff_num = 0.0
w_diff_den = 0.0
for mk, m in mun_1700.items():
    if m["n0"] > 0 and m["n1"] > 0:
        p0 = 100.0 * m["l0"] / m["vv0"]
        p1 = 100.0 * m["l1"] / m["vv1"]
        w = m["vv0"] + m["vv1"]
        w_diff_num += w * (p1 - p0)
        w_diff_den += w
print(f"Within-municipality diff (17:01-17:15 minus 17:00:xx in UTC-3): {w_diff_num/w_diff_den:+.4f} p.p.")

# 4. Check Biometry NH (QT_ELEI_BIOM_SEM_HABILITACAO) 1T vs 2T across all 499,205 sections
tot_nh1 = sum(s["nh"] for s in sec1.values())
tot_c1 = sum(s["comp"] for s in sec1.values())
tot_nh2 = sum(s["nh"] for s in sec2.values())
tot_c2 = sum(s["comp"] for s in sec2.values())
print(f"\n=== 4. BIOMETRY NH 1T vs 2T CENSUS (499,205 SECTIONS) ===")
print(f"1T NH: {tot_nh1:,} / {tot_c1:,} ({100*tot_nh1/tot_c1:.2f}%)")
print(f"2T NH: {tot_nh2:,} / {tot_c2:,} ({100*tot_nh2/tot_c2:.2f}%) | Diff: {tot_nh2-tot_nh1:+,} ({100*tot_nh2/tot_c2 - 100*tot_nh1/tot_c1:+.2f} p.p.)")

# Check correlation and within-municipality slope of %Lula2T and d%Lula(2T-1T) vs %NH_2T and d%NH(2T-1T)
mun_secs = defaultdict(list)
for k, s2 in sec2.items():
    s1 = sec1.get(k)
    if not s1:
        continue
    vv2 = s2["lula"] + s2["flavio"]
    vv1 = s1["vv"]
    if vv2 > 0 and vv1 > 0 and s2["comp"] > 0 and s1["comp"] > 0:
        lp2 = 100.0 * s2["lula"] / vv2
        lp1 = 100.0 * s1["lula"] / vv1
        nh2 = 100.0 * s2["nh"] / s2["comp"]
        nh1 = 100.0 * s1["nh"] / s1["comp"]
        mun_secs[(s2["uf"], s2["mun"])].append((lp2, lp2 - lp1, nh2, nh2 - nh1))

# Demean by municipality
s_x2, s_xy_lvl, s_xy_dl = 0.0, 0.0, 0.0
s_dx2, s_dxy_dl = 0.0, 0.0
for mk, arr in mun_secs.items():
    if len(arr) < 2:
        continue
    n = len(arr)
    m_lp2 = sum(x[0] for x in arr) / n
    m_dlp = sum(x[1] for x in arr) / n
    m_nh2 = sum(x[2] for x in arr) / n
    m_dnh = sum(x[3] for x in arr) / n
    for lp2, dlp, nh2, dnh in arr:
        x = nh2 - m_nh2
        dx = dnh - m_dnh
        s_x2 += x * x
        s_xy_lvl += x * (lp2 - m_lp2)
        s_xy_dl += x * (dlp - m_dlp)
        s_dx2 += dx * dx
        s_dxy_dl += dx * (dlp - m_dlp)

print(f"Within-municipality slope of %Lula_2T on %NH_2T (per +10pp NH): {10.0 * s_xy_lvl / s_x2:+.4f} p.p.")
print(f"Within-municipality slope of d%Lula(2T-1T) on %NH_2T (per +10pp NH): {10.0 * s_xy_dl / s_x2:+.4f} p.p.")
print(f"Within-municipality slope of d%Lula(2T-1T) on d%NH(2T-1T) (per +10pp dNH): {10.0 * s_dxy_dl / s_dx2:+.4f} p.p.")

# 5. Check the 106 unanimous sections (100% Lula) and 6,899 >90% sections in 1T vs 2T
u100_l, u100_f = [], []
gt90_l, gt90_f = [], []
for k, s2 in sec2.items():
    vv2 = s2["lula"] + s2["flavio"]
    if vv2 == 0:
        continue
    lp2 = 100.0 * s2["lula"] / vv2
    fp2 = 100.0 * s2["flavio"] / vv2
    s1 = sec1.get(k)
    if s2["lula"] == vv2:
        u100_l.append((s2, s1))
    if s2["flavio"] == vv2:
        u100_f.append((s2, s1))
    if lp2 > 90.0:
        gt90_l.append((s2, s1))
    if fp2 > 90.0:
        gt90_f.append((s2, s1))

print(f"\n=== 5. UNANIMOUS & >90% SECTIONS (CENSUS 499,205) ===")
print(f"100% Lula: {len(u100_l)} sections (total votes: {sum(x[0]['lula'] for x in u100_l):,}) | 1T Lula in these exact 106 sections: {100*sum(x[1]['lula'] for x in u100_l if x[1])/sum(x[1]['vv'] for x in u100_l if x[1]):.2f}% of all 1T candidates ({100*sum(x[1]['lula'] for x in u100_l if x[1])/sum(x[1]['lula']+x[1]['flavio'] for x in u100_l if x[1]):.2f}% Lula vs Flavio in 1T)")
print(f"100% Flavio: {len(u100_f)} sections (total votes: {sum(x[0]['flavio'] for x in u100_f):,})")
print(f">90% Lula: {len(gt90_l)} sections (total net margin: {sum(x[0]['lula']-x[0]['flavio'] for x in gt90_l):,}) | 1T Lula in these exact 6,899 sections: {100*sum(x[1]['lula'] for x in gt90_l if x[1])/sum(x[1]['vv'] for x in gt90_l if x[1]):.2f}% of all 1T candidates ({100*sum(x[1]['lula'] for x in gt90_l if x[1])/sum(x[1]['lula']+x[1]['flavio'] for x in gt90_l if x[1]):.2f}% Lula vs Flavio in 1T) | Mean NH_2T: {100*sum(x[0]['nh'] for x in gt90_l)/sum(x[0]['comp'] for x in gt90_l):.2f}% vs 1T NH: {100*sum(x[1]['nh'] for x in gt90_l if x[1])/sum(x[1]['comp'] for x in gt90_l if x[1]):.2f}%")
print(f">90% Flavio: {len(gt90_f)} sections (total net margin: {sum(x[0]['flavio']-x[0]['lula'] for x in gt90_f):,})")
