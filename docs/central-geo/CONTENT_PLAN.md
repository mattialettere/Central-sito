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

Le pagine "prodotto" della fase 1 coprono invece le domande commerciali: app SOS, chat crittografata, alternativa a Life360, funzioni, FAQ.

## In coda (dalla lista del master prompt)

Da scrivere solo se c'è qualcosa di utile e diverso da dire. Accorpati dove si sovrapponevano.

| Priorità | Tema | Note |
|---|---|---|
| Alta | Come condividere la posizione in sicurezza (e quando smettere) | Riprende la sezione della pagina famiglia; valutare se basta quella |
| Alta | Lavoratori isolati: strumenti per chi lavora da solo | Pubblico B2B; servono fonti normative verificate (D.Lgs. 81/2008) prima di scrivere |
| Alta | Versioni inglesi delle 5 guide | Dopo aver misurato le visite delle versioni italiane |
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
3. Link nell'indice `tools/pagine/contenuti/it/guide-indice.html`.
4. `python3 tools/pagine/build_pages.py` e aggiungere l'URL a `sitemap.xml`.
5. `python3 tools/seo-audit/check_site.py` deve restare senza errori nuovi.
