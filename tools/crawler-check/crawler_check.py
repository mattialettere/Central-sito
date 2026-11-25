#!/usr/bin/env python3
"""Controllo dal vivo di getcentral.net come lo vedono i crawler.

Da lanciare dal PC (dal cloud il dominio non e' raggiungibile):
    python tools/crawler-check/crawler_check.py
    python tools/crawler-check/crawler_check.py --markdown > reports/weekly/crawler-AAAA-MM-GG.md

Per ogni user-agent (Googlebot, Bingbot, GPTBot, OAI-SearchBot, ClaudeBot,
Claude-SearchBot, PerplexityBot...) chiede la home e controlla codice HTTP,
redirect e se il testo principale c'e'. Poi controlla robots.txt, la
sitemap e che ogni URL della sitemap risponda 200, con title e canonical.

Limite importante: qui si imita solo l'user-agent. Se un firewall (per
esempio Cloudflare) blocca i bot veri in base all'indirizzo IP, questo
script non lo vede: per quello servono i log del server o gli strumenti
dei motori (Search Console, Bing Webmaster Tools).

Solo libreria standard. Nessun dato inviato a terzi oltre alle richieste
al sito stesso.
"""
from __future__ import annotations

import re
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET

SITE = "https://getcentral.net"
UA = {
    "Browser": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Bingbot": "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "OAI-SearchBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot",
    "ChatGPT-User": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot",
    "GPTBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.1; +https://openai.com/gptbot",
    "Claude-SearchBot": "Mozilla/5.0 (compatible; Claude-SearchBot/1.0; +https://www.anthropic.com)",
    "Claude-User": "Mozilla/5.0 (compatible; Claude-User/1.0; +https://www.anthropic.com)",
    "ClaudeBot": "Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)",
    "PerplexityBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
    "Applebot": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15 (Applebot/0.1; +http://www.apple.com/go/applebot)",
}
ROBOTS_TOKEN = {"Browser": "*", "Bingbot": "bingbot"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def get(url: str, ua: str, follow: bool = True, timeout: int = 20):
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8"})
    t = time.monotonic()
    try:
        with opener.open(req, timeout=timeout) as r:
            body = r.read(2_000_000).decode("utf-8", "replace")
            return r.status, r.geturl(), dict(r.headers), body, time.monotonic() - t
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location", url), dict(e.headers), "", time.monotonic() - t
    except Exception as e:  # rete, DNS, TLS
        return None, url, {}, str(e), time.monotonic() - t


def title_of(body: str) -> str:
    m = re.search(r"<title>(.*?)</title>", body, re.S | re.I)
    return " ".join(m.group(1).split()) if m else ""


def canonical_of(body: str) -> str:
    m = re.search(r'<link rel="canonical" href="([^"]+)"', body)
    return m.group(1) if m else ""


def main() -> int:
    md = "--markdown" in sys.argv
    out: list[str] = []
    problemi = 0
    p = out.append
    p(f"# Controllo crawler di {SITE} · {time.strftime('%Y-%m-%d %H:%M')}\n")

    # Redirect di base
    p("## Redirect\n")
    for u in ("http://getcentral.net/", "https://www.getcentral.net/", "http://www.getcentral.net/"):
        s, loc, h, _, _ = get(u, UA["Browser"], follow=False)
        p(f"- {u} → {s} {loc if s and 300 <= s < 400 else ''}")
    p("")

    # robots.txt
    s, _, _, robots, _ = get(SITE + "/robots.txt", UA["Browser"])
    robots_ok = s == 200
    if not robots_ok:
        problemi += 1
    p(f"## robots.txt: HTTP {s}\n")
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(robots.splitlines())

    # Home per user-agent
    p("## Home per user-agent\n")
    p("| Bot | robots.txt | HTTP | Tempo | Testo principale | Server / CDN |")
    p("|---|---|---|---|---|---|")
    for name, ua in UA.items():
        token = ROBOTS_TOKEN.get(name, name)
        allowed = rp.can_fetch(token, SITE + "/")
        s, final, h, body, dt = get(SITE + "/", ua)
        testo = "sì" if "<h1" in body and "Central" in body else "NO"
        cdn = h.get("Server", "") + (" · cf-ray" if "CF-RAY" in {k.upper() for k in h} else "")
        if s != 200 or testo != "sì":
            problemi += 1
        stato_robots = ("consentito" if allowed else "bloccato") if robots_ok else "non letto"
        p(f"| {name} | {stato_robots} | {s} | {dt:.1f}s | {testo} | {cdn} |")
    p("")

    # Sitemap
    s, _, _, sm, _ = get(SITE + "/sitemap.xml", UA["Googlebot"])
    p(f"## Sitemap: HTTP {s}\n")
    try:
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [e.text.strip() for e in ET.fromstring(sm).findall("s:url/s:loc", ns)]
    except ET.ParseError as e:
        p(f"Sitemap non leggibile: {e}")
        urls = []
        problemi += 1
    p("| URL | HTTP | Title | Canonical ok |")
    p("|---|---|---|---|")
    for u in urls:
        s, final, _, body, _ = get(u, UA["Googlebot"])
        can = canonical_of(body)
        ok = can == u
        if s != 200 or not ok:
            problemi += 1
        p(f"| {u} | {s} | {title_of(body)[:60]} | {'sì' if ok else 'NO (' + can + ')'} |")
    p("")
    p(f"**Problemi trovati: {problemi}**")

    text = "\n".join(out)
    if not md:
        text = re.sub(r"^#+ ", "", text, flags=re.M)
    print(text)
    return 1 if problemi else 0


if __name__ == "__main__":
    sys.exit(main())
