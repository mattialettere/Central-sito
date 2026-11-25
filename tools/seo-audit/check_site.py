#!/usr/bin/env python3
"""Controllo SEO/GEO offline di getcentral.net, sui file del repository.

Verifica, per ogni pagina .html pubblicata:
  - <title> presente (avviso se oltre 70 caratteri)
  - meta description presente (avviso se fuori da 70-170 caratteri)
  - canonical assoluto su https://getcentral.net, coerente con il percorso
  - un solo <h1> (le pagine noindex e i redirect sono esclusi)
  - hreflang reciproci: se A dichiara B, B deve dichiarare A
  - JSON-LD valido (si analizza come JSON)
  - link interni che puntano a file esistenti
  - immagini con attributo alt
Poi controlla che ogni URL della sitemap esista e che ogni pagina
indicizzabile sia nella sitemap, e che robots.txt dichiari la sitemap.

Uso, dalla radice del repository:
    python3 tools/seo-audit/check_site.py          # stampa il rapporto
    python3 tools/seo-audit/check_site.py --json   # rapporto in JSON

Esce con codice 1 se trova errori (non per i semplici avvisi).
Nessuna dipendenza esterna, nessuna richiesta di rete.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE = "https://getcentral.net"
ESCLUSI = {"docs", "tools", "reports", ".git", "node_modules"}


class Pagina(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = None
        self._in_title = False
        self._in_ld = False
        self._ld_buf: list[str] = []
        self.meta: dict[str, str] = {}
        self.canonical = None
        self.hreflang: dict[str, str] = {}
        self.h1 = 0
        self.ld: list[str] = []
        self.links: list[str] = []
        self.img_senza_alt: list[str] = []
        self.refresh = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
            self.title = ""
        elif tag == "meta":
            k = a.get("name") or a.get("property")
            if k:
                self.meta[k.lower()] = a.get("content", "")
            if (a.get("http-equiv") or "").lower() == "refresh":
                self.refresh = True
        elif tag == "link":
            rel = (a.get("rel") or "").lower()
            if rel == "canonical":
                self.canonical = a.get("href")
            elif rel == "alternate" and a.get("hreflang"):
                self.hreflang[a["hreflang"]] = a.get("href", "")
        elif tag == "h1":
            self.h1 += 1
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld = True
            self._ld_buf = []
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "img":
            if "alt" not in a:
                self.img_senza_alt.append(a.get("src", "?"))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._in_ld:
            self._in_ld = False
            self.ld.append("".join(self._ld_buf))

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_ld:
            self._ld_buf.append(data)


def url_di(path: pathlib.Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return SITE + "/" + rel[: -len("index.html")]
    return SITE + "/" + rel


def file_di(url: str) -> pathlib.Path | None:
    if not url.startswith(SITE):
        return None
    p = url[len(SITE):].split("#")[0].split("?")[0] or "/"
    if p.endswith("/"):
        p += "index.html"
    f = ROOT / p.lstrip("/")
    if f.exists():
        return f
    if (ROOT / (p.lstrip("/") + ".html")).exists():
        return ROOT / (p.lstrip("/") + ".html")
    return None


def pagine() -> list[pathlib.Path]:
    out = []
    for f in sorted(ROOT.rglob("*.html")):
        if ESCLUSI & set(f.relative_to(ROOT).parts):
            continue
        out.append(f)
    return out


def controlla() -> dict:
    errori: list[str] = []
    avvisi: list[str] = []
    dati: dict[str, Pagina] = {}
    indicizzabili: set[str] = set()

    for f in pagine():
        p = Pagina()
        p.feed(f.read_text(encoding="utf-8"))
        rel = f.relative_to(ROOT).as_posix()
        dati[url_di(f)] = p
        robots = p.meta.get("robots", "")
        noindex = "noindex" in robots or p.refresh
        if not noindex:
            indicizzabili.add(url_di(f))
        if not p.title or not p.title.strip():
            errori.append(f"{rel}: manca <title>")
        elif len(p.title) > 70 and not noindex:
            avvisi.append(f"{rel}: title lungo ({len(p.title)} caratteri)")
        if noindex:
            continue
        d = p.meta.get("description")
        if not d:
            errori.append(f"{rel}: manca meta description")
        elif not 70 <= len(d) <= 170:
            avvisi.append(f"{rel}: meta description di {len(d)} caratteri (consigliati 70-170)")
        if not p.canonical:
            errori.append(f"{rel}: manca canonical")
        elif p.canonical != url_di(f):
            errori.append(f"{rel}: canonical {p.canonical} diverso da {url_di(f)}")
        if p.h1 != 1:
            errori.append(f"{rel}: {p.h1} tag <h1> (deve essercene uno)")
        if "og:title" not in p.meta or "og:image" not in p.meta:
            avvisi.append(f"{rel}: Open Graph incompleto")
        for blocco in p.ld:
            try:
                json.loads(blocco)
            except json.JSONDecodeError as e:
                errori.append(f"{rel}: JSON-LD non valido ({e})")
        for src in p.img_senza_alt:
            errori.append(f"{rel}: immagine senza alt ({src})")
        for href in p.links:
            if href.startswith(("mailto:", "tel:", "#", "javascript:")):
                continue
            if href.startswith("http") and not href.startswith(SITE):
                continue
            assoluto = href if href.startswith("http") else (
                SITE + href if href.startswith("/") else url_di(f).rsplit("/", 1)[0] + "/" + href)
            if file_di(assoluto) is None:
                errori.append(f"{rel}: link interno rotto {href}")

    # hreflang reciproci
    for url, p in dati.items():
        for lang, alt in p.hreflang.items():
            if lang == "x-default" or alt == url:
                continue
            q = dati.get(alt)
            if q is None:
                errori.append(f"{url}: hreflang {lang} punta a {alt}, pagina inesistente")
            elif url not in q.hreflang.values():
                errori.append(f"{url}: hreflang {lang} -> {alt} non ricambiato")

    # sitemap
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    try:
        albero = ET.parse(ROOT / "sitemap.xml")
        in_sitemap = {e.text.strip() for e in albero.getroot().findall("s:url/s:loc", ns)}
    except ET.ParseError as e:
        errori.append(f"sitemap.xml non valida: {e}")
        in_sitemap = set()
    for u in sorted(in_sitemap):
        if file_di(u) is None:
            errori.append(f"sitemap: {u} non corrisponde a nessun file")
        elif u not in indicizzabili:
            avvisi.append(f"sitemap: {u} e' noindex o redirect")
    for u in sorted(indicizzabili - in_sitemap):
        avvisi.append(f"pagina indicizzabile assente dalla sitemap: {u}")

    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    if "Sitemap: https://getcentral.net/sitemap.xml" not in robots:
        errori.append("robots.txt non dichiara la sitemap")
    if re.search(r"(?mi)^User-agent:\s*\*\s*\nDisallow:\s*/\s*$", robots):
        errori.append("robots.txt blocca tutto il sito")

    return {"pagine": len(dati), "indicizzabili": len(indicizzabili),
            "in_sitemap": len(in_sitemap), "errori": errori, "avvisi": avvisi}


def main() -> int:
    r = controlla()
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"Pagine: {r['pagine']} · indicizzabili: {r['indicizzabili']} · in sitemap: {r['in_sitemap']}")
        print(f"Errori: {len(r['errori'])}")
        for e in r["errori"]:
            print("  ERRORE", e)
        print(f"Avvisi: {len(r['avvisi'])}")
        for a in r["avvisi"]:
            print("  avviso", a)
    return 1 if r["errori"] else 0


if __name__ == "__main__":
    sys.exit(main())
