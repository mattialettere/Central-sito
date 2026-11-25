#!/usr/bin/env python3
"""Rapporto settimanale o mensile dal registro del Central AI Visibility Monitor.

Uso:
    python tools/central-geo-monitor/report.py central-geo-monitor-AAAA-MM-GG.json
    python tools/central-geo-monitor/report.py export.json --giorni 30 > reports/monthly/2026-12.md

Legge il JSON esportato dalla pagina index.html (scheda "Importa / esporta")
e stampa un rapporto Markdown: quante risposte, quante menzioni, per
piattaforma e categoria, concorrenti, confronto con il periodo precedente.
Usa solo le verifiche registrate: non interroga nessun servizio.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import pathlib
import sys


def pct(a: int, b: int) -> str:
    return f"{round(100 * a / b)}%" if b else "–"


def riassunto(rows: list[dict]) -> dict:
    n = len(rows)
    return {
        "n": n,
        "menzioni": sum(r["esito"] != "assente" for r in rows),
        "raccomandazioni": sum(r["esito"] == "raccomandazione" for r in rows),
        "negative": sum(r["esito"] == "negativa" for r in rows),
        "fonte": sum(bool(r.get("fonte")) for r in rows),
        "sito": sum(bool(r.get("link_sito")) for r in rows),
        "store": sum(bool(r.get("link_store")) for r in rows),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("export", type=pathlib.Path)
    ap.add_argument("--giorni", type=int, default=7)
    ap.add_argument("--fino", default=dt.date.today().isoformat(), help="ultimo giorno incluso, AAAA-MM-GG")
    a = ap.parse_args()

    d = json.loads(a.export.read_text(encoding="utf-8"))
    domande = {q["id"]: q for q in d.get("domande", [])}
    fine = dt.date.fromisoformat(a.fino)
    inizio = fine - dt.timedelta(days=a.giorni - 1)
    prima = inizio - dt.timedelta(days=a.giorni)
    rows = [r for r in d.get("verifiche", []) if inizio.isoformat() <= r["data"] <= fine.isoformat()]
    prec = [r for r in d.get("verifiche", []) if prima.isoformat() <= r["data"] < inizio.isoformat()]

    s, sp = riassunto(rows), riassunto(prec)
    o = print
    o(f"# Central AI Visibility · {inizio} → {fine}\n")
    if not rows:
        o("Nessuna verifica registrata nel periodo. Il rapporto non contiene stime: servono verifiche manuali.")
        return 0
    o("| Indicatore | Periodo | Periodo precedente |")
    o("|---|---|---|")
    for k, label in [("n", "Risposte analizzate"), ("menzioni", "Menzioni di Central"),
                     ("raccomandazioni", "Raccomandazioni esplicite"), ("fonte", "Citazioni con fonte"),
                     ("sito", "Link a getcentral.net"), ("store", "Link agli store"), ("negative", "Negative / errate")]:
        extra = "" if k == "n" else f" ({pct(s[k], s['n'])})"
        extra_p = "" if k == "n" else f" ({pct(sp[k], sp['n'])})"
        o(f"| {label} | {s[k]}{extra} | {sp[k]}{extra_p} |")
    o("")
    for titolo, chiave in [("Per piattaforma", lambda r: r["piattaforma"]),
                           ("Per categoria", lambda r: domande.get(r["domanda_id"], {}).get("categoria", "?"))]:
        o(f"## {titolo}\n")
        o("| | Risposte | Menzioni |")
        o("|---|---|---|")
        g = collections.defaultdict(list)
        for r in rows:
            g[chiave(r)].append(r)
        for k in sorted(g):
            m = sum(x["esito"] != "assente" for x in g[k])
            o(f"| {k} | {len(g[k])} | {m} ({pct(m, len(g[k]))}) |")
        o("")
    c = collections.Counter(x for r in rows for x in r.get("concorrenti", []))
    if c:
        o("## Concorrenti citati\n")
        for k, v in c.most_common(15):
            o(f"- {k}: {v} risposte ({pct(v, len(rows))})")
        o("")
    neg = [r for r in rows if r["esito"] == "negativa"]
    if neg:
        o("## Risposte con errori su Central (da correggere con contenuti o PR)\n")
        for r in neg:
            q = domande.get(r["domanda_id"], {}).get("domanda", r["domanda_id"])
            o(f"- {r['data']} · {r['piattaforma']} · {q}: {r.get('note') or r.get('estratto', '')[:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
