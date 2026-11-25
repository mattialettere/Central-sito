# Piano editoriale GEO / SEO

Aggiornato: 24 novembre 2026 · Fase 2 del progetto "Central GEO Engine"

## Scelta: pochi articoli ottimi invece di 20 in serie

Il master prompt chiedeva 20 articoli. Ne abbiamo pubblicati 5 (più l'indice delle guide) e messo gli altri in coda. Il motivo: Google valuta i contenuti "creati per i motori di ricerca" in serie come di bassa qualità (linee guida su contenuti utili e affidabili), e un sito giovane con molti articoli simili rischia più di quanto guadagna. Meglio aggiungere 1-2 guide al mese, ciascuna verificata.

## Regole per ogni guida

- Risponde a una domanda reale, utile anche a chi non userà mai Central.
- Risposta "In breve" in apertura (2-4 righe): è il formato che i motori AI citano più volentieri.
- Fonti ufficiali linkate (Apple, Google, Commissione UE, EFF, Signal…), controllate prima di pubblicare.
- Central compare solo dove pertinente, con funzioni verificate nel codice.
- Niente statistiche senza fonte, niente consigli medici o legali specifici.
- Data di pubblicazione e di aggiornamento visibili e nel JSON-LD (`Article`).
- Autore: l'organizzazione Central. Non inventiamo firme personali; se mattia vuole firmare, si aggiunge una pagina autore vera.

## Pubblicate (fase 2)

| URL | Keyword principale | Secondarie | Intento |
|---|---|---|---|
| /guide/contatti-di-emergenza-smartphone.html | contatti di emergenza smartphone | cartella clinica iphone, informazioni emergenza android, app sos | Informativo / pratico |
| /guide/cosa-comunicare-in-emergenza.html | cosa dire al 112 | informazioni da dare in emergenza, 112 where are u | Informativo |
| /guide/genitore-anziano-che-vive-da-solo.html | anziano che vive da solo sicurezza | check-in anziani, app per anziani soli | Informativo / commerciale leggero |
| /guide/tornare-a-casa-da-soli-la-sera.html | tornare a casa da soli la sera | app tragitto sicuro, condividere posizione tragitto | Informativo / commerciale leggero |
| /guide/chat-cifrata-domande-da-fare.html | chat cifrata | app messaggistica privata, forward secrecy, metadati | Informativo / confronto |

## Pubblicate (fase 5, 25 novembre 2026)

| URL | Keyword principale | Note |
|---|---|---|
| /en/guides/ + 5 traduzioni | emergency contacts phone, what to say 112, elderly parent living alone, walking home at night, encrypted chat | Versioni inglesi delle 5 guide, con hreflang reciproci e sitemap |
| /guide/condividere-la-posizione-in-sicurezza.html · /en/guides/share-location-safely.html | condividere posizione / share location safely | Fonti: Apple (105104, Controllo di sicurezza), Google Maps Help, WhatsApp FAQ |
| /guide/lavoratori-isolati-sicurezza.html · /en/guides/lone-worker-safety.html | lavoratori isolati / lone worker safety | Fonti: HSE (lone working, INDG73), D.Lgs. 81/2008 testo coordinato INL. Il testo degli articoli non è citato alla lettera: non è stato possibile leggerlo dal cloud, si citano solo i titoli verificati (art. 28, Sezione VI) |

Le pagine "prodotto" della fase 1 coprono invece le domande commerciali: app SOS, chat crittografata, alternativa a Life360, funzioni, FAQ.

## In coda (dalla lista del master prompt)

Da scrivere solo se c'è qualcosa di utile e diverso da dire. Accorpati dove si sovrapponevano.

| Priorità | Tema | Note |
|---|---|---|
| Media | Come proteggere i dati personali sullo smartphone | Fonti: Garante privacy, ENISA |
| Media | Differenze tra messaggistica privata e social network | |
| Media | Community private: come funzionano e come moderarle | |
| Media | Come riconoscere un'app affidabile | In parte già nella guida sulle chat cifrate |
| Bassa | Gestire i gruppi di comunicazione (famiglia, sport, condominio) | |
| Bassa | Prepararsi a un'emergenza in famiglia (piano familiare) | Fonti: Protezione Civile; collegabile alle allerte quando la 1.9.1 è pubblica |
| Bassa | Identità digitale: proteggerla | |

## Come si aggiunge una guida

1. Metadati in `tools/pagine/articoli.json` (path in `/guide/`, title ≤ 70 caratteri, description 70-170).
2. Corpo in `tools/pagine/contenuti/it/<key>.html`.
3. Link negli indici `tools/pagine/contenuti/it/guide-indice.html` e `tools/pagine/contenuti/en/guide-indice.html` (per la versione inglese: chiave `en` in `articoli.json` e corpo in `contenuti/en/<key>.html`).
4. `python3 tools/pagine/build_pages.py` e aggiungere l'URL a `sitemap.xml`.
5. `python3 tools/seo-audit/check_site.py` deve restare senza errori nuovi.
