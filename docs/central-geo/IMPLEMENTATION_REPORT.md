# Central GEO Engine: rapporto di implementazione

Data: 24 novembre 2026 · Tutto in una sola PR su central-sito (#6), con un commit per fase.

Nessun deploy, nessuna modifica agli store, all'app o al backend. Il sito cambia solo quando mattia fa il merge della PR (GitHub Pages pubblica `main`).

## Attività completate

| Fase | Cosa | File |
|---|---|---|
| 1. Audit | Stato del sito, risposte HTTP, presenza pubblica, verifica delle funzioni sul codice, priorità | `docs/central-geo/AUDIT_CENTRAL_GEO.md` |
| 1. Tecnico | robots.txt con crawler di ricerca e di addestramento separati; sitemap; llms.txt; `_config.yml` che esclude docs/tools/reports/main.py | `robots.txt`, `sitemap.xml`, `llms.txt`, `_config.yml` |
| 1. Pagine | 5 pagine IT + 5 EN con hreflang, JSON-LD, risposta "In breve", fonti | `funzionalita.html`, `app-sos-emergenza.html`, `chat-crittografata.html`, `sicurezza-famiglia.html`, `domande-frequenti.html` e `en/…` |
| 1. Home | Piano gratuito 2/2/1, dati e fornitori, nome app nel JSON-LD, link alle pagine nuove | `index.html`, `en/index.html`, `fr/index.html` |
| 2. Contenuti | Sezione Guide con 5 articoli e indice; piano editoriale | `guide/…`, `docs/central-geo/CONTENT_PLAN.md` |
| 3. Digital PR | Canali, testi pronti, scheda prodotto, email di proposta | `docs/central-geo/DIGITAL_PR_PLAN.md` |
| 3. ASO | Diagnosi e proposte per App Store e Google Play (non applicate) | `docs/central-geo/ASO_STORE.md` |
| 4. Monitor | Registro manuale delle risposte AI con dashboard, export CSV/JSON, rapporti | `tools/central-geo-monitor/` |
| 4. Automazione | Controllo offline dei file e controllo dal vivo dei crawler | `tools/seo-audit/check_site.py`, `tools/crawler-check/crawler_check.py`, `reports/` |
| — | Generatore delle pagine | `tools/pagine/build_pages.py`, `tools/pagine/contenuti/`, `tools/pagine/articoli.json` |

## Fase 5 (25 novembre 2026, dopo il merge della PR #6)

- Doppio H1 delle privacy corretto (il titolo dentro la scheda diventa H2), meta description di privacy, segnala, aziende, white label e video riportate a 70-170 caratteri, title delle home sotto i 70.
- Versioni inglesi delle 5 guide in `/en/guides/`, con hreflang reciproci, indice inglese e link nel piè di pagina.
- Due guide nuove IT+EN: condividere la posizione in sicurezza; lavoratori isolati.
- Sitemap e llms.txt aggiornati. Nessuna modifica ad app, backend o store.

## Test effettuati

- `check_site.py`: 41 pagine, 39 indicizzabili, tutte in sitemap; 0 errori nuovi (restano i 3 doppi H1 delle privacy, presenti anche su main).
- Sitemap XML valida; JSON-LD di ogni pagina valido.
- Rendering con Chromium a 390 px e 1280 px: nessuno scroll orizzontale.
- Monitor: inserimento di due verifiche di prova, dashboard, export CSV (solo in un browser di test, nessun dato salvato nel repository).
- `report.py` su un export di prova; `crawler_check.py` eseguito ma il dominio non è raggiungibile dal cloud: va lanciato dal PC.

## Correzioni rispetto alle istruzioni iniziali

- Il **video SOS di 30 secondi esiste** (pulsante nell'app, widget Android). Senza video da Siri, Centro di Controllo e riquadro rapido.
- L'**SOS con il tasto volume non esiste più**: sostituito dal riquadro delle impostazioni rapide.
- Il numero di contatti dipende dal piano: 2 gratis, 5 Plus, illimitati Premium.
- Posizionamento: alternativa europea e privata a Life360. WhatsApp compare solo come domanda nelle FAQ, con una risposta onesta.
- 20 articoli → 5 di qualità più una lista in coda (motivo in `CONTENT_PLAN.md`).

## Problemi residui

1. ~~Doppio H1 nelle pagine privacy~~ e ~~meta description fuori misura~~: corretti nella fase 5 (25/11), `check_site.py` ora dà 0 errori e 0 avvisi su 51 pagine.
2. Pannello Guardian: senza JS mostra solo il testo di cancellazione account (P2, backend).
3. Indicizzazione reale e risposte HTTP ai bot non verificate (serve Search Console e il PC).

## Attività che richiedono intervento umano

1. **Rivedere e fare il merge della PR #6.**
2. ~~Scelta sui crawler di addestramento~~: confermata il 25/11, restano consentiti.
3. Google Search Console e Bing Webmaster Tools: verificare il dominio e inviare la sitemap.
4. Lanciare `python tools/crawler-check/crawler_check.py` dal PC e dire se il dominio passa da Cloudflare.
5. Inviare le 10 bozze alle testate e pubblicare le schede AlternativeTo / European Alternatives.
6. Mandare gli URL dei profili Instagram e YouTube per `sameAs`.
7. Decidere se applicare le proposte ASO (PR su `scheda.json` in central-apple, poi workflow Codemagic).
8. Prima sessione del monitor (circa un'ora), poi ogni due settimane.

## Istruzioni per il deploy

Il sito è su GitHub Pages dal branch `main`. Il merge della PR #6 pubblica tutto in pochi minuti. Dopo il merge:

1. Aprire https://getcentral.net/funzionalita.html, /en/features.html e /guide/ per un controllo a vista.
2. Verificare che https://getcentral.net/main.py e /docs/central-geo/AUDIT_CENTRAL_GEO.md rispondano 404 (escluse da `_config.yml`).
3. Inviare la sitemap in Search Console e Bing.

Per modificare una pagina in futuro: cambiare il testo in `tools/pagine/contenuti/…`, lanciare `python3 tools/pagine/build_pages.py` e `python3 tools/seo-audit/check_site.py`, aprire una PR.
