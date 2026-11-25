# Audit SEO / GEO di getcentral.net

Data: 24 novembre 2026 · Fase 1 del progetto "Central GEO Engine"
Repository: `mattialettere/central-sito` (branch `claude/project-thread-9rvzho`)

Questo documento non viene pubblicato sul sito: `_config.yml` esclude `docs/`.

Legenda dello stato delle verifiche:

- **Verificato**: controllato direttamente (codice, file, risposta HTTP).
- **Non verificato**: plausibile ma non controllabile da qui.
- **Non rilevato**: cercato e non trovato.
- **Dato non disponibile**: serve un accesso che non abbiamo (es. Search Console).

---

## 1. Situazione iniziale

### 1.1 Tecnologia del sito

| Voce | Stato | Dettaglio |
|---|---|---|
| Framework | Verificato | HTML statico scritto a mano, nessun build. CSS in `assets/site.css`, un solo JS (`assets/menu.js`) per il menu mobile. |
| Hosting | Verificato | GitHub Pages con dominio personalizzato (`CNAME` = getcentral.net). Nessun workflow in `.github/`: pubblicazione dal branch, quindi passa da Jekyll. |
| Lingue | Verificato | IT (radice), EN (`/en/`), FR (`/fr/`). |
| Rendering JS | Verificato | Tutti i testi sono nell'HTML: nessun contenuto dipende da JavaScript. Ottimo per i crawler AI, che spesso non eseguono JS. |
| Font | Verificato | Ospitati in locale (`assets/fonts/`), con `font-display: swap` e preload. |
| Analytics | Verificato | Contatore proprio senza cookie verso `api.getcentral.net/site/hit`, rispetta Do Not Track. |
| File estraneo | Verificato | `main.py` è il file principale del backend FastAPI, finito nel repo del sito. Era pubblicato su getcentral.net/main.py. Ora escluso dalla pubblicazione (vedi §5); valuta di cancellarlo dal repo. |

### 1.2 Pagine (prima di questa fase)

25 pagine HTML, 23 indicizzabili, tutte e 23 nella sitemap. Home, aziende, white label, privacy e segnala esistono in IT/EN/FR; 7 pagine video per settore e l'area stampa solo in IT; `beta.html` e `404.html` sono noindex.

### 1.3 Risposte HTTP del sito pubblicato

Controllate con uno strumento di lettura web il 24/11/2026:

| URL | Stato |
|---|---|
| https://getcentral.net/ | Verificato: 200, HTML leggibile senza JS |
| https://getcentral.net/robots.txt | Verificato: 200, `User-agent: * Allow: /` + sitemap |
| https://getcentral.net/sitemap.xml | Verificato: 200, XML valido |
| https://getcentral.net/en/ | Verificato: 200 |
| https://getcentral.net/stampa.html | Verificato: 200 |
| Risposte per user-agent dei bot (403, Cloudflare) | Non verificato: dal cloud il dominio non è raggiungibile con curl e il PC era spento. GitHub Pages non usa Cloudflare di suo; se il DNS passa da Cloudflare con "Bot Fight Mode" attivo, i crawler AI potrebbero ricevere 403. Da controllare (§7). |
| Redirect http → https, www → apex | Non verificato (stessa ragione). |

### 1.4 Metadati e dati strutturati (home)

Già buoni prima di questa fase: title e description per lingua, canonical, Open Graph e Twitter Card completi, hreflang IT/EN/FR/x-default reciproci, meta `apple-itunes-app`, JSON-LD con Organization, WebSite, MobileApplication (prezzo 0, nessun voto inventato), VideoObject e FAQPage.

### 1.5 Presenza pubblica

| Canale | Stato | Note |
|---|---|---|
| App Store | Verificato | "Central: chat e sicurezza", id6826663138, live dal 18/11/2026. |
| Google Play | Verificato | net.getcentral.central. |
| Indicizzazione Google / Bing | Dato non disponibile | Serve Search Console / Bing Webmaster Tools (§7). Che una pagina si apra nel browser non dice che sia indicizzata. |
| Ricerca del marchio | Non rilevato | Una ricerca web per "getcentral.net Central app" restituisce solo altre app chiamate "Central" (chiese, news, CentralNow…). Il nome è molto comune: serve disambiguare sempre con "Central: chat e sicurezza", il dominio e i link agli store. |
| Directory (AlternativeTo, European Alternatives) | Non verificato | Testi pronti in `/post/alternativeto-scheda.md` del progetto; non sappiamo se le schede sono state pubblicate. europeanpurpose.com ha una pagina "European Alternatives to Life360": candidatura utile. |
| Siti tech / stampa | Non verificato | Area stampa online; 10 bozze a testate preparate il 20/11, esito non noto. |
| Social | Non verificato | Instagram e YouTube attivi (video qSCHFZCdRO0), URL dei profili non noti: non sono in `sameAs`. |
| Codice crypto pubblico | Verificato | github.com/mattialettere/central-crypto (Apache-2.0). |
| Pannello Guardian | Verificato | online.getcentral.net/guardian-dashboard/panel risponde 200, ma senza JS l'unico testo visibile è la finestra "Eliminare definitivamente l'account?" e il titolo "Central — Area personale". Per un crawler è una pagina confusa (§3, P2). |

---

## 2. Verifica delle funzioni sul codice

Il master prompt e la prima risposta in chat contenevano alcune affermazioni da controllare. Esito sul codice di `central-apple` e `central-backend` (main del 24/11/2026):

| Affermazione | Esito | Dove |
|---|---|---|
| Video di emergenza nell'SOS | **Esiste.** L'SOS dall'app (Android e iPhone) e dal widget Android registra 30 secondi di video dalla fotocamera frontale, annullabile nei primi 3 s, cifrato e inviato con l'allerta. Da Siri, Centro di Controllo e riquadro rapido Android parte senza video. | `SosCaptureActivity.kt`, `IosSos.kt`, `SosRepository.kt` |
| SOS con sequenza del tasto volume | **Non esiste più.** Il codice dice che è stato sostituito dal riquadro delle Impostazioni rapide perché su molti OEM i tasti non arrivano all'app. Non va citato come funzione; le pagine lo spiegano. | `GuardianCards.kt` (commento su `SosVolumeCard`) |
| Fino a 5 contatti | **Dipende dal piano**: Gratis 2, Plus 5, Premium illimitati (gratis alzato da 1 a 2 il 24/11). Stessi numeri per i Guardian; zone sicure 1/3/illimitate. | `services/plans.py` |
| Videochiamate | **Non esistono.** Solo chiamate vocali, cifrate DTLS-SRTP (WebRTC). | `legal_content.py` §3.1 |
| Batteria nell'SOS | Esiste. | `SosRepository.kt`, `IosSos.kt` |
| Viaggia sicuro fino a 5 persone | Esiste (`MAX_WATCHERS = 5`). | `SharedTripStartViewModel.kt` |
| Server | Railway regione UE (azienda USA); file su Scaleway fr-par; FCM, APNs, Mapbox, Resend, Metered USA/globali. | `services/media.py`, `legal_content.py` |
| Contatti SOS via email senza app, Piano Famiglia | Nel backend dal 24/11, ma l'app che li usa non è ancora rilasciata: **non citati** nelle pagine. | `services/sos_external.py`, `services/family.py` |
| Live Activity, widget 2.0 | Nascosti fino a marzo: **non citati**. | decisione del 21/11 |
| Allerte Protezione Civile / INGV | In arrivo con la 1.9.1: **non citate** finché non è pubblica. | |

---

## 3. Problemi individuati e priorità

P1 = alto impatto, P2 = medio, P3 = basso.

| # | Pri | Problema | Soluzione | Stato |
|---|---|---|---|---|
| 1 | P1 | Una sola pagina vera (la home): nessuna pagina risponde a domande specifiche ("app SOS", "chat crittografata", "alternativa a Life360"). I motori AI citano pagine che rispondono a una domanda precisa. | 5 pagine di approfondimento IT + EN, ognuna con risposta breve in apertura. | **Fatto** |
| 2 | P1 | Piano gratuito scritto male nella home IT/EN/FR (1 contatto e 1 Guardian, perimetri solo Plus) dopo l'aumento a 2/2/1 del 24/11. | Testi corretti nelle tre lingue. | **Fatto** |
| 3 | P1 | Nome ambiguo: "Central" coincide con decine di app. | JSON-LD con `name` "Central: chat e sicurezza" e `alternateName` "Central"; stesso nome in tutte le pagine nuove. | **Fatto** (serve anche fuori dal sito, §7) |
| 4 | P1 | FAQ "Dove sono i dati?" diceva solo "server in Europa", ma push, mappe ed email sono di fornitori USA e Railway è un'azienda USA. Rischio di affermazione non accurata. | Risposta precisa nelle tre lingue (home) e nelle pagine nuove. | **Fatto** |
| 5 | P2 | robots.txt generico: non distingue crawler di ricerca e di addestramento, la scelta non è documentata. | Gruppi espliciti con commenti (§4). | **Fatto**, scelta confermata il 25/11 |
| 6 | P2 | `main.py` (backend) e in futuro `docs/`, `tools/` pubblicati sul sito. | `_config.yml` con `exclude`. | **Fatto** |
| 7 | P2 | Nessun `llms.txt`. Non è uno standard ufficiale e nessun motore garantisce di leggerlo, ma costa poco e riassume i fatti verificati. | `/llms.txt` in inglese. | **Fatto** |
| 8 | P2 | Pannello Guardian: per i crawler mostra solo il testo di cancellazione account. | Nel backend: `<meta name="robots" content="noindex">` sul pannello oppure un titolo/descrizione e un `<noscript>` che spieghi cos'è. Non toccato (backend fuori dal perimetro di questa PR). | Da fare, serve ok |
| 9 | P2 | `sameAs` dell'organizzazione senza profili social. | Aggiungere Instagram, YouTube, AlternativeTo quando avremo gli URL esatti. Aggiunto il repo central-crypto. | Parziale |
| 10 | P3 | Privacy IT/EN/FR hanno due `<h1>` (uno nell'intestazione, uno nella scheda). | Trasformare il secondo in titolo non h1. Non toccato: testo legale, modifica minima da fare insieme a una revisione dell'informativa. | Da fare |
| 11 | P3 | Alcune meta description fuori misura (aziende, white label, video, privacy, segnala). | Accorciare o allungare nella prossima fase. | Da fare |
| 12 | P3 | Pagine video e stampa solo in italiano, senza hreflang. | Va bene così finché non esistono traduzioni. | — |
| 13 | P3 | FAQPage: dal 2023 Google mostra i risultati arricchiti FAQ quasi solo per siti governativi e sanitari. | Il markup resta valido e utile ad altri motori; nessun beneficio garantito su Google. | Informativo |

Performance e Core Web Vitals: il sito è leggero (HTML 10-35 KB per pagina, immagini WebP con width/height, font locali con preload, un solo script defer). Non ho misure di campo (CrUX) né Lighthouse sul sito pubblicato: **dato non disponibile**. Responsive verificato su 390 px e 1280 px per le pagine nuove (nessuno scroll orizzontale).

Accessibilità: link "vai al contenuto", `alt` su tutte le immagini (verificato dallo script), contrasti del tema esistente, `aria-current` su lingua e pagina attiva, tabelle con `scope`.

---

## 4. Crawler AI e robots.txt

Fonti consultate il 24/11/2026: documentazione bot di OpenAI (developers.openai.com/api/docs/bots), Anthropic (support.claude.com, articolo 8896518), Google (crawler comuni), Perplexity (docs.perplexity.ai/guides/bots).

| Bot | Azienda | Scopo | Nel nuovo robots.txt |
|---|---|---|---|
| Googlebot | Google | Ricerca, anche AI Overviews e AI Mode | Consentito |
| Google-Extended | Google | Solo un token: uso dei contenuti per addestrare Gemini. Non influisce su Search né AI Overviews. | Consentito |
| Bingbot | Microsoft | Ricerca Bing, e quindi Copilot | Consentito |
| Applebot / Applebot-Extended | Apple | Ricerca Siri/Spotlight / addestramento | Consentito / consentito |
| OAI-SearchBot | OpenAI | Risultati di ChatGPT search | Consentito |
| ChatGPT-User | OpenAI | Visite su richiesta di un utente; OpenAI dice che robots.txt "potrebbe non applicarsi" | Consentito |
| GPTBot | OpenAI | Addestramento | Consentito |
| Claude-SearchBot | Anthropic | Qualità dei risultati di ricerca | Consentito |
| Claude-User | Anthropic | Visite su richiesta di un utente | Consentito |
| ClaudeBot | Anthropic | Addestramento | Consentito |
| PerplexityBot | Perplexity | Indice di ricerca, non addestramento | Consentito |
| Perplexity-User | Perplexity | Visite su richiesta; in genere ignora robots.txt | Consentito |
| CCBot | Common Crawl | Archivio aperto usato da molti modelli | Consentito |

**Scelta sui crawler di addestramento: confermata da mattia il 25/11/2026 (consentiti).** Prima di questa PR il sito permetteva già tutto a tutti (`User-agent: * Allow: /`), compresi i crawler di addestramento. La PR rende la regola esplicita e **non cambia il comportamento attuale**. Raccomando di lasciarli consentiti: il sito contiene solo testi pubblici di presentazione, nessun dato degli utenti, e l'obiettivo è che i modelli conoscano Central. Se preferisci bloccarli basta cambiare `Allow: /` in `Disallow: /` nel gruppo 2: ricerca e AI Overviews non ne risentono.

---

## 5. Interventi completati in questa fase

File nuovi:

- `funzionalita.html`, `app-sos-emergenza.html`, `chat-crittografata.html`, `sicurezza-famiglia.html`, `domande-frequenti.html`
- `en/features.html`, `en/sos-emergency-app.html`, `en/encrypted-chat.html`, `en/family-safety.html`, `en/faq.html`
- `llms.txt`, `_config.yml`
- `tools/pagine/build_pages.py` + `tools/pagine/contenuti/{it,en}/*.html`: generatore delle pagine. I testi si modificano nei file `contenuti`, poi `python3 tools/pagine/build_pages.py`.
- `tools/seo-audit/check_site.py`: controllo offline (title, description, canonical, h1, hreflang reciproci, JSON-LD, link interni, alt, sitemap, robots).
- `docs/central-geo/AUDIT_CENTRAL_GEO.md` (questo file).

File modificati:

- `index.html`, `en/index.html`, `fr/index.html`: piano gratuito 2/2/1, tag "Gratis: 1 zona" sui perimetri, risposta sui dati, nome app e `sameAs` nel JSON-LD, link alle pagine nuove nel piè di pagina (IT/EN).
- `robots.txt`: gruppi espliciti (§4).
- `sitemap.xml`: 10 URL nuovi con hreflang, lastmod aggiornato per le home.
- `assets/site.css`: stili delle pagine di approfondimento (in coda, non tocca gli stili esistenti).

Ogni pagina nuova ha: title e description unici, un solo H1, H2/H3 ordinati, risposta "In breve" in apertura (formato facile da citare per un motore AI), canonical, hreflang IT/EN/x-default, Open Graph e Twitter Card, JSON-LD WebPage + BreadcrumbList + Organization + MobileApplication (FAQPage sulla pagina FAQ, generato dal testo visibile), data di aggiornamento visibile, link interni, link agli store e fonti esterne autorevoli (Apple, Google, Commissione UE sul 112, EFF, Signal).

Cose che le pagine non fanno, di proposito: nessun voto, numero di download o recensione; nessuna certificazione; nessuna "sicurezza assoluta"; nessun confronto con dati di altre aziende; limiti della crittografia scritti in chiaro (metadati, niente forward secrecy, non anonimo).

Test: `python3 tools/seo-audit/check_site.py` → 35 pagine, 33 indicizzabili, tutte in sitemap, 0 errori nuovi (restano i 3 doppi H1 delle privacy, già presenti su main). Rendering controllato con Chromium a 390 e 1280 px.

---

## 6. Interventi necessari nelle fasi successive

1. **Contenuti (fase 2)**: 5-6 articoli di guida approfonditi (non 20 in serie), con fonti, nella stessa struttura generata.
2. **Digital PR e ASO (fase 3)**: riusare area stampa, `scheda.json` e i testi in `/post/`; elenco directory e testate; testi store IT/EN pronti da copiare.
3. **AI Visibility Monitor (fase 4)**: strumento separato dal sito, con verifiche manuali registrate, senza API a pagamento e senza simulare risultati.
4. P2/P3 della tabella §3 rimasti aperti.

## 7. Cose che richiedono accesso a servizi esterni (solo mattia)

1. **Google Search Console**: verificare la proprietà getcentral.net (record DNS TXT o file HTML), inviare `sitemap.xml`, controllare "Pagine" e richiedere l'indicizzazione delle 10 pagine nuove.
2. **Bing Webmaster Tools**: importare da Search Console e inviare la sitemap (Bing alimenta Copilot e in parte altri motori). Valutare IndexNow.
3. **DNS / Cloudflare**: dire se il dominio passa da Cloudflare. Se sì, verificare che "Bot Fight Mode" o le regole AI non blocchino i bot consentiti.
4. **Profili social**: mandare gli URL esatti di Instagram, YouTube e di eventuali schede su AlternativeTo / European Alternatives per `sameAs`.
5. **Pannello Guardian**: ok per aggiungere `noindex` o un titolo descrittivo nel backend (P2 #8).
6. ~~Scelta robots.txt sui crawler di addestramento~~: confermata il 25/11 (consentiti).
