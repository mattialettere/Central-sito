#!/usr/bin/env python3
"""Genera le pagine di approfondimento di getcentral.net (IT + EN).

Il testo di ogni pagina sta in tools/pagine/contenuti/<lingua>/<chiave>.html
(solo il corpo, in HTML semplice). Qui stanno l'intestazione comune, i
metadati, i dati strutturati e il piè di pagina, cosi' che tutte le pagine
abbiano la stessa identita' (titolo, canonical, hreflang, Open Graph, JSON-LD)
senza copiarla a mano.

Uso, dalla radice del repository:
    python3 tools/pagine/build_pages.py

Riscrive i file .html nella radice e in en/. Non tocca le altre pagine.
Nessuna dipendenza esterna.
"""
from __future__ import annotations

import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTENUTI = pathlib.Path(__file__).resolve().parent / "contenuti"
SITE = "https://getcentral.net"
APP_STORE = "https://apps.apple.com/app/id6826663138"
PLAY = "https://play.google.com/store/apps/details?id=net.getcentral.central"
DASHBOARD = "https://online.getcentral.net/guardian-dashboard/panel"
CRYPTO_REPO = "https://github.com/mattialettere/central-crypto"
# Data dell'ultima revisione dei testi: compare nella pagina, nel JSON-LD e
# nella sitemap. Aggiornala quando cambi un contenuto.
AGGIORNATO = "2026-11-24"

# Ordine = ordine nel menu "Guide" a fondo pagina.
PAGES = [
    {
        "key": "funzionalita",
        "it": {
            "path": "/funzionalita.html",
            "nav": "Tutte le funzioni",
            "title": "Funzionalità di Central: chat cifrata, SOS, Viaggia sicuro e community",
            "desc": "Tutte le funzioni di Central per iPhone e Android: chat cifrata, chiamate vocali, SOS, check-in, Viaggia sicuro, zone sicure e community. Cosa è gratis e cosa no.",
            "eyebrow": "Funzionalità",
            "h1": "Tutto quello che fa Central, <em>funzione per funzione</em>",
            "lead": "Central unisce tre cose che di solito stanno in app diverse: una chat privata cifrata end-to-end, strumenti di sicurezza personale e uno spazio social solo con i tuoi contatti. Qui trovi l'elenco completo, con quello che è gratis e quello che richiede un piano.",
            "img": "/assets/funzioni/gruppi.webp",
            "img_alt": "Chat di gruppo di Central con la lavagna condivisa",
        },
        "en": {
            "path": "/en/features.html",
            "nav": "All features",
            "title": "Central features: encrypted chat, SOS, Safe Trip and community",
            "desc": "Every Central feature on iPhone and Android: encrypted chat, voice calls, SOS, check-in, Safe Trip, safe zones and communities. What is free and what needs a plan.",
            "eyebrow": "Features",
            "h1": "Everything Central does, <em>feature by feature</em>",
            "lead": "Central brings together three things that usually live in separate apps: a private, end-to-end encrypted chat, personal safety tools and a social space shared only with your contacts. Here is the full list, with what is free and what needs a plan.",
            "img": "/assets/funzioni/gruppi.webp",
            "img_alt": "Central group chat with the shared whiteboard",
        },
    },
    {
        "key": "sos",
        "it": {
            "path": "/app-sos-emergenza.html",
            "nav": "App SOS per le emergenze",
            "title": "App SOS per emergenze: come funziona l'SOS di Central",
            "desc": "L'SOS di Central invia posizione, batteria e un video di 30 secondi ai contatti di emergenza. Come attivarlo su iPhone e Android e quanti contatti puoi avere.",
            "eyebrow": "SOS ed emergenze",
            "h1": "L'SOS di Central: <em>come funziona</em> e quando usarlo",
            "lead": "Un SOS su smartphone serve a una cosa sola: far sapere subito a persone di fiducia che hai bisogno di aiuto e dove sei. Questa pagina spiega come lo fa Central, passo per passo, e cosa resta compito dei numeri di emergenza.",
            "img": "/assets/funzioni/sos.webp",
            "img_alt": "Schermata SOS di Central con il pulsante di emergenza e i contatti",
        },
        "en": {
            "path": "/en/sos-emergency-app.html",
            "nav": "SOS emergency app",
            "title": "SOS emergency app: how Central's SOS works on iPhone and Android",
            "desc": "Central's SOS sends location, battery and a 30-second video to your emergency contacts. How to trigger it on iPhone and Android and how many contacts you can add.",
            "eyebrow": "SOS and emergencies",
            "h1": "Central's SOS: <em>how it works</em> and when to use it",
            "lead": "A phone SOS has one job: letting people you trust know right away that you need help and where you are. This page explains, step by step, how Central does it and what remains the job of emergency services.",
            "img": "/assets/funzioni/sos.webp",
            "img_alt": "Central SOS screen with the emergency button and contacts",
        },
    },
    {
        "key": "chat",
        "it": {
            "path": "/chat-crittografata.html",
            "nav": "Chat crittografata",
            "title": "Chat crittografata end-to-end: come Central protegge i messaggi",
            "desc": "Cos'è la crittografia end-to-end e come la usa Central: X25519, AES-256-GCM, chiavi sul telefono e codice open source. Con i limiti detti apertamente.",
            "eyebrow": "Chat privata",
            "h1": "Chat crittografata end-to-end: <em>cosa protegge davvero</em>",
            "lead": "Una chat è privata quando solo chi scrive e chi legge possono aprire i messaggi. Qui spieghiamo cosa vuol dire crittografia end-to-end, come è fatta in Central e, con la stessa chiarezza, cosa non copre.",
            "img": "/assets/funzioni/chat.webp",
            "img_alt": "Chat cifrata end-to-end di Central con messaggi, foto e vocali",
        },
        "en": {
            "path": "/en/encrypted-chat.html",
            "nav": "Encrypted chat",
            "title": "End-to-end encrypted chat: how Central protects your messages",
            "desc": "What end-to-end encryption means and how Central uses it: X25519, AES-256-GCM, keys on the phone and open source code. With its limits stated openly.",
            "eyebrow": "Private chat",
            "h1": "End-to-end encrypted chat: <em>what it really protects</em>",
            "lead": "A chat is private when only the sender and the recipients can open the messages. Here we explain what end-to-end encryption means, how Central implements it and, just as clearly, what it does not cover.",
            "img": "/assets/funzioni/chat.webp",
            "img_alt": "Central end-to-end encrypted chat with messages, photos and voice notes",
        },
    },
    {
        "key": "famiglia",
        "it": {
            "path": "/sicurezza-famiglia.html",
            "nav": "Sicurezza della famiglia",
            "title": "Sicurezza della famiglia senza tracciamento continuo | Central",
            "desc": "Proteggere la famiglia senza controllarla di continuo: check-in, Viaggia sicuro, zone sicure e SOS. Central, l'alternativa europea e privata a Life360.",
            "eyebrow": "Famiglia e posizione",
            "h1": "Sicurezza della famiglia, <em>senza tracciamento continuo</em>",
            "lead": "Molte app per la famiglia mostrano a tutti dove si trovano tutti, sempre. Central parte da un'idea diversa: la posizione si condivide quando c'è un motivo, con persone scelte, e chi è seguito lo sa e può dire di no.",
            "img": "/assets/funzioni/viaggio.webp",
            "img_alt": "Viaggia sicuro di Central: tragitto sulla mappa e orario di arrivo previsto",
        },
        "en": {
            "path": "/en/family-safety.html",
            "nav": "Family safety",
            "title": "Family safety app without constant tracking | Central",
            "desc": "Keep your family safe without watching them all the time: check-in, Safe Trip, safe zones and SOS. Central, the private European alternative to Life360.",
            "eyebrow": "Family and location",
            "h1": "Family safety, <em>without constant tracking</em>",
            "lead": "Many family apps show everyone where everyone is, all the time. Central starts from a different idea: location is shared when there is a reason, with people you choose, and the person being followed knows it and can say no.",
            "img": "/assets/funzioni/viaggio.webp",
            "img_alt": "Central Safe Trip: route on the map and expected arrival time",
        },
    },
    {
        "key": "faq",
        "it": {
            "path": "/domande-frequenti.html",
            "nav": "Domande frequenti",
            "title": "Domande frequenti su Central: prezzi, iPhone, crittografia, SOS e dati",
            "desc": "Risposte verificate su Central: è gratis? Funziona su iPhone e Android? Come funzionano crittografia, SOS e posizione? Dove sono i dati?",
            "eyebrow": "Domande frequenti",
            "h1": "Domande frequenti su <em>Central</em>",
            "lead": "Risposte brevi e verificate sulla versione attuale dell'app. Se qualcosa non è chiaro, scrivici a info@getcentral.net.",
            "img": "/assets/funzioni/privacy.webp",
            "img_alt": "Privacy di Central: niente pubblicità, cifratura e server in Europa",
        },
        "en": {
            "path": "/en/faq.html",
            "nav": "FAQ",
            "title": "Central FAQ: pricing, iPhone, encryption, SOS and data",
            "desc": "Verified answers about Central: is it free? Does it work on iPhone and Android? How do encryption, SOS and location work? Where is the data stored?",
            "eyebrow": "FAQ",
            "h1": "Frequently asked questions about <em>Central</em>",
            "lead": "Short, verified answers based on the current version of the app. If something is unclear, write to info@getcentral.net.",
            "img": "/assets/funzioni/privacy.webp",
            "img_alt": "Central privacy: no ads, encryption and servers in Europe",
        },
    },
]

T = {
    "it": {
        "home": "/", "skip": "Vai al contenuto", "brand_label": "Central, pagina iniziale",
        "nav": [("Funzioni", "/funzionalita.html"), ("SOS", "/app-sos-emergenza.html"),
                ("Chat cifrata", "/chat-crittografata.html"), ("Famiglia", "/sicurezza-famiglia.html"),
                ("Domande", "/domande-frequenti.html"), ("Aziende", "/aziende.html")],
        "report": ("Segnala", "/segnala.html"), "login": ("Dashboard Login", "Registrati<br>Login", "Registrati / Login"),
        "download": "Scarica", "dl_ios": "Scarica per iPhone", "dl_android": "Scarica per Android",
        "updated": "Aggiornato il", "crumb_home": "Home", "guides": "Guide",
        "cta_h": "Scarica Central, è gratis",
        "cta_p": "Su App Store per iPhone e su Google Play per Android. Le funzioni di sicurezza essenziali sono gratuite.",
        "store_a": "Scarica su App Store", "store_g": "Scarica su Google Play",
        "footer_nav": "Piè di pagina", "privacy": ("Privacy", "/privacy.html"), "press": ("Stampa", "/stampa.html"),
        "biz": ("Aziende", "/aziende.html"), "locale": "it_IT", "lang_tag": "it-IT", "months": None,
    },
    "en": {
        "home": "/en/", "skip": "Skip to content", "brand_label": "Central, home page",
        "nav": [("Features", "/en/features.html"), ("SOS", "/en/sos-emergency-app.html"),
                ("Encrypted chat", "/en/encrypted-chat.html"), ("Family", "/en/family-safety.html"),
                ("FAQ", "/en/faq.html"), ("Business", "/en/aziende.html")],
        "report": ("Report", "/en/segnala.html"), "login": ("Dashboard Login", "Sign up<br>Login", "Sign up / Login"),
        "download": "Download", "dl_ios": "Download for iPhone", "dl_android": "Download for Android",
        "updated": "Updated on", "crumb_home": "Home", "guides": "Guides",
        "cta_h": "Get Central, it's free",
        "cta_p": "On the App Store for iPhone and on Google Play for Android. The essential safety features are free.",
        "store_a": "Download on the App Store", "store_g": "Get it on Google Play",
        "footer_nav": "Footer", "privacy": ("Privacy", "/en/privacy.html"), "press": ("Press (IT)", "/stampa.html"),
        "biz": ("Business", "/en/aziende.html"), "locale": "en_GB", "lang_tag": "en", "months": None,
    },
}

MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
           "agosto", "settembre", "ottobre", "novembre", "dicembre"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]


def data_leggibile(lang: str, iso: str) -> str:
    y, m, d = (int(x) for x in iso.split("-"))
    if lang == "it":
        return f"{d} {MESI_IT[m - 1]} {y}"
    return f"{d} {MONTHS_EN[m - 1]} {y}"


def strip_tags(s: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", s)


def faq_items(body: str) -> list[tuple[str, str]]:
    """Estrae domande e risposte dai <details> della pagina FAQ, per il JSON-LD.

    Il JSON-LD deve dire esattamente quello che la pagina mostra: per questo
    si legge dal corpo invece di tenere una seconda copia del testo.
    """
    import re
    out = []
    for m in re.finditer(r"<details[^>]*>\s*<summary>(.*?)</summary>(.*?)</details>", body, re.S):
        q = " ".join(strip_tags(m.group(1)).split())
        a = " ".join(strip_tags(m.group(2)).split())
        out.append((html.unescape(q), html.unescape(a)))
    return out


def jsonld(page: dict, lang: str, body: str) -> str:
    p = page[lang]
    url = SITE + p["path"]
    t = T[lang]
    graph: list[dict] = [
        {
            "@type": "WebPage" if page["key"] != "faq" else ["WebPage", "FAQPage"],
            "@id": url + "#webpage",
            "url": url,
            "name": strip_tags(p["h1"]),
            "headline": p["title"],
            "description": p["desc"],
            "inLanguage": t["lang_tag"],
            "isPartOf": {"@id": SITE + "/#website"},
            "about": {"@id": SITE + "/#app"},
            "publisher": {"@id": SITE + "/#org"},
            "primaryImageOfPage": SITE + p["img"],
            "dateModified": AGGIORNATO,
            "breadcrumb": {"@id": url + "#breadcrumb"},
        },
        {
            "@type": "BreadcrumbList",
            "@id": url + "#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": t["crumb_home"], "item": SITE + t["home"]},
                {"@type": "ListItem", "position": 2, "name": p["nav"], "item": url},
            ],
        },
        # Organization e app ripetute in forma breve: ogni pagina deve essere
        # comprensibile da sola, anche da chi non legge la home.
        {
            "@type": "Organization",
            "@id": SITE + "/#org",
            "name": "Central",
            "url": SITE + "/",
            "logo": SITE + "/assets/favicon-512.png",
            "email": "info@getcentral.net",
        },
        {
            "@type": "MobileApplication",
            "@id": SITE + "/#app",
            "name": "Central: chat e sicurezza",
            "alternateName": "Central",
            "operatingSystem": "iOS, Android",
            "applicationCategory": "CommunicationApplication",
            "url": SITE + "/",
            "downloadUrl": [APP_STORE, PLAY],
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
            "publisher": {"@id": SITE + "/#org"},
        },
    ]
    if page["key"] == "faq":
        graph[0]["mainEntity"] = [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faq_items(body)
        ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1)


def render(page: dict, lang: str) -> str:
    p = page[lang]
    other = "en" if lang == "it" else "it"
    t = T[lang]
    url = SITE + p["path"]
    body = (CONTENUTI / lang / f"{page['key']}.html").read_text(encoding="utf-8")
    e = html.escape
    nav = "\n".join(
        f'      <a href="{href}"{" aria-current=\"page\"" if href == p["path"] else ""}>{label}</a>'
        for label, href in t["nav"]
    )
    guide_links = " · ".join(
        f'<a href="{pg[lang]["path"]}">{pg[lang]["nav"]}</a>' for pg in PAGES
    )
    it_path, en_path = page["it"]["path"], page["en"]["path"]
    lang_switch = (
        f'<a href="{it_path}" hreflang="it" lang="it"{" aria-current=\"true\"" if lang == "it" else ""}>IT</a>'
        f'<a href="{en_path}" hreflang="en" lang="en"{" aria-current=\"true\"" if lang == "en" else ""}>EN</a>'
    )
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(p["title"])}</title>
<meta name="description" content="{e(p["desc"])}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#EA5B2E">
<meta name="apple-itunes-app" content="app-id=6826663138">
<link rel="alternate" hreflang="it" href="{SITE}{it_path}">
<link rel="alternate" hreflang="en" href="{SITE}{en_path}">
<link rel="alternate" hreflang="x-default" href="{SITE}{it_path}">

<meta property="og:type" content="article">
<meta property="og:site_name" content="Central">
<meta property="og:locale" content="{t["locale"]}">
<meta property="og:locale:alternate" content="{T[other]["locale"]}">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{e(p["title"])}">
<meta property="og:description" content="{e(p["desc"])}">
<meta property="og:image" content="{SITE}/assets/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(p["img_alt"])}">
<meta property="article:modified_time" content="{AGGIORNATO}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(p["title"])}">
<meta name="twitter:description" content="{e(p["desc"])}">
<meta name="twitter:image" content="{SITE}/assets/og-image.jpg">

<link rel="preload" href="/assets/fonts/fredoka-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/inter-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css">
<link rel="stylesheet" href="/assets/lang.css">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png">
<link rel="icon" type="image/png" sizes="192x192" href="/assets/favicon-192.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<script type="application/ld+json">
{jsonld(page, lang, body)}
</script>
</head>
<body>
<a class="skip" href="#contenuto">{t["skip"]}</a>

<header class="site-nav site-nav-wide">
  <div class="wrap">
    <a class="brand" href="{t["home"]}" aria-label="{t["brand_label"]}"><img src="/assets/central-logo.png" alt="" width="34" height="34" class="mark-img"><span class="brand-font">Central</span></a>
    <nav class="nav-links" aria-label="{t["guides"]}">
{nav}
    </nav>
    <div class="nav-actions">
      <div class="lang-switch" role="navigation" aria-label="Lingua · Language">{lang_switch}</div>
      <a class="nav-report" href="{t["report"][1]}">{t["report"][0]}</a>
      <a class="nav-cta-alt nav-login" aria-label="{t["login"][2]}" href="{DASHBOARD}"><span class="desktop-label">{t["login"][0]}</span><span class="mobile-label">{t["login"][1]}</span></a>
      <a class="nav-cta" href="#scarica">{t["download"]}</a>
    </div>
  </div>
</header>

<main id="contenuto">
<section class="hero guide-hero">
  <div class="wrap">
    <div>
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{t["home"]}">{t["crumb_home"]}</a> <span aria-hidden="true">›</span> <span aria-current="page">{p["nav"]}</span></nav>
      <div class="eyebrow">{p["eyebrow"]}</div>
      <h1>{p["h1"]}</h1>
      <p class="lead">{p["lead"]}</p>
      <div class="actions" style="margin-top:24px">
        <a class="btn-primary" href="{APP_STORE}" target="_blank" rel="noopener">{t["dl_ios"]}</a>
        <a class="btn-primary" href="{PLAY}" target="_blank" rel="noopener">{t["dl_android"]}</a>
      </div>
      <p class="updated">{t["updated"]} <time datetime="{AGGIORNATO}">{data_leggibile(lang, AGGIORNATO)}</time></p>
    </div>
    <div class="hero-visual">
      <img src="{p["img"]}" width="480" height="960" alt="{e(p["img_alt"])}" fetchpriority="high">
    </div>
  </div>
</section>

<section class="guide">
  <div class="wrap prose">
{body.rstrip()}
  </div>
</section>

<section id="scarica" style="padding-top:20px">
  <div class="wrap">
    <div class="cta-band">
      <div>
        <h2>{t["cta_h"]}</h2>
        <p>{t["cta_p"]}</p>
      </div>
      <div class="actions">
        <a class="btn-white" href="{APP_STORE}" target="_blank" rel="noopener">{t["store_a"]}</a>
        <a class="btn-white" href="{PLAY}" target="_blank" rel="noopener">{t["store_g"]}</a>
      </div>
    </div>
  </div>
</section>
</main>

<footer>
  <div class="wrap">
    <a class="brand" href="{t["home"]}"><img src="/assets/central-logo.png" alt="" width="26" height="26" class="mark-img mark-img-sm"><span class="brand-font">Central</span></a>
    <div class="tag-line">You are Central. · <a href="mailto:info@getcentral.net">info@getcentral.net</a></div>
    <nav class="links" aria-label="{t["footer_nav"]}">
      <a href="{t["biz"][1]}">{t["biz"][0]}</a>
      <a href="{DASHBOARD}">Dashboard</a>
      <a href="{t["press"][1]}">{t["press"][0]}</a>
      <a href="{t["privacy"][1]}">{t["privacy"][0]}</a>
      <a href="{APP_STORE}" target="_blank" rel="noopener">App Store</a>
      <a href="{PLAY}" target="_blank" rel="noopener">Google Play</a>
    </nav>
    <p class="guide-links">{t["guides"]}: {guide_links}</p>
  </div>
</footer>
<script>
/* Contatore visite di Central: niente cookie, nessun servizio esterno. */
(function(){{try{{if(navigator.doNotTrack==="1"||window.doNotTrack==="1")return;var q=new URLSearchParams(location.search);var d=JSON.stringify({{path:location.pathname,referrer:document.referrer,utm_source:q.get("utm_source"),utm_campaign:q.get("utm_campaign")}});var u="https://api.getcentral.net/site/hit";if(navigator.sendBeacon){{navigator.sendBeacon(u,new Blob([d],{{type:"text/plain"}}));}}else{{fetch(u,{{method:"POST",body:d,keepalive:true,mode:"no-cors"}});}}}}catch(e){{}}}})();
</script>
<script src="/assets/menu.js" defer></script>
</body>
</html>
"""


def main() -> None:
    for page in PAGES:
        for lang in ("it", "en"):
            out = ROOT / page[lang]["path"].lstrip("/")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(page, lang), encoding="utf-8")
            print("scritto", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
