# Digital PR e reputazione online

Aggiornato: 24 novembre 2026 · Fase 3 del progetto "Central GEO Engine"

Obiettivo: far sì che fonti indipendenti parlino di Central in modo corretto. I motori AI si fidano molto di più di una recensione su un sito tecnologico, di una scheda su una directory o di una discussione su Reddit che del sito ufficiale. Ogni menzione esterna con il nome completo, il link a getcentral.net e i link agli store aiuta anche a distinguere Central dalle molte app omonime.

Regole fisse: niente recensioni comprate o false, niente account finti, niente scambi di link, niente spam. Ogni invio lo fa mattia, a mano, dal proprio account.

## 1. Cosa esiste già (da riusare, non rifare)

| Materiale | Dove |
|---|---|
| Comunicato stampa, video di lancio, screenshot, logo | https://getcentral.net/stampa.html |
| 10 email a testate tech italiane (bozze, non inviate al 20/11) | Gmail centralmattia, oggetto "Central: …" |
| Schede AlternativeTo e European Alternatives (EN) | `/mnt/project-files/post/alternativeto-scheda.md` |
| Post Reddit di lancio (3 varianti EN) | `/mnt/project-files/post/reddit-lancio-app-store.md` |
| Risposta Reddit sulla privacy della posizione | `/mnt/project-files/post/reddit-risposta-privacy-posizione.md` |
| Post indie dev su Central City | `/mnt/project-files/post/central-city-indie-dev.md` |
| Repository crypto open source | https://github.com/mattialettere/central-crypto |

**Prima azione consigliata:** inviare le 10 bozze alle testate già preparate (dopo averle rilette) e pubblicare le due schede directory. È lavoro già fatto che oggi non produce nulla.

## 2. Dove presentare Central

### Directory e liste di alternative (impatto alto, sforzo basso)

| Sito | Perché | Stato |
|---|---|---|
| alternativeto.net | Molto citato dai motori AI per le domande "alternative a X". Scheda come alternativa a Life360 | Testo pronto |
| european-alternatives.eu | Pubblico "compra europeo", coerente con il posizionamento | Testo pronto |
| europeanpurpose.com | Ha una pagina "European Alternatives to Life360" | Da proporre |
| switching.software | Lista curata di alternative etiche; valuta progetti con codice aperto, Central lo è solo per la crittografia: chiedere, non insistere | Da valutare |
| Product Hunt | Lancio internazionale; meglio preparare un giorno di lancio con screenshot e video | Da preparare |

### Testate tech italiane

Già in bozza: HDblog, Tutto Android, Punto Informatico, HWUpgrade, MondoMobileWeb, TuttoTech, TecnoAndroid, iPhone Live, iPhone Country, Libero Tecnologia. Solo modulo di contatto: iSpazio, Macitynet, SmartWorld/AndroidWorld.

Aggiunte possibili (contatti da cercare sui siti, non inventati): siti su privacy e sicurezza digitale, rubriche "app della settimana" dei quotidiani, portali startup come StartupItalia.

### Community (con trasparenza)

| Dove | Come |
|---|---|
| r/BuyFromEU, r/iosapps, r/androidapps, r/SideProject | Post già pronti. Dire sempre che sei lo sviluppatore e che usi strumenti AI (decisione del 19/11) |
| Hacker News "Show HN" | Per il repository central-crypto: chiedere una revisione della crittografia, dichiarando subito i limiti (niente forward secrecy). Pubblico tecnico, utile per la credibilità |
| Indie Hackers | Storia dello sviluppatore indipendente |
| Forum di genitori, gruppi per caregiver | Solo rispondendo a domande pertinenti, mai post promozionali non richiesti |

### Wikidata / Wikipedia

Non ora. Le voci su app poco coperte dalla stampa vengono cancellate e una voce scritta dal produttore viola le regole sul conflitto di interessi. Se ne riparla dopo articoli indipendenti su testate riconosciute.

## 3. Testi pronti

### Descrizione breve (IT, ~150 caratteri)
Central: chat e sicurezza è l'app italiana gratuita con chat cifrata end-to-end, SOS, check-in e Viaggia sicuro. Posizione condivisa solo quando serve.

### Short description (EN, ~150 characters)
Central: Chat & Safety is a free Italian app with end-to-end encrypted chat, SOS, check-in and Safe Trip. Location is shared only when it matters.

### Descrizione estesa (IT)
Central è un'app gratuita per iPhone e Android, sviluppata in Italia in modo indipendente, che unisce una chat cifrata end-to-end con strumenti di sicurezza personale e familiare. A differenza delle app di localizzazione continua, Central condivide la posizione solo per un motivo preciso: durante un viaggio con Viaggia sicuro, all'uscita da una zona concordata o in un SOS. L'SOS invia ai contatti di emergenza posizione, batteria e, se avviato dall'app, un video di 30 secondi; su iPhone si avvia anche con Siri. Il check-in "Sto bene" avvisa i familiari se una conferma non arriva. Messaggi, foto e file sono cifrati con X25519 e AES-256-GCM e il codice crittografico è open source. Central non ha pubblicità; i piani Plus e Premium aumentano contatti, zone e storico.

### Scheda prodotto (fatti verificati)

| Voce | Valore |
|---|---|
| Nome | Central: chat e sicurezza (EN: Central: Chat & Safety) |
| Sito | https://getcentral.net |
| Store | App Store id6826663138 · Google Play net.getcentral.central |
| Piattaforme | iOS, Android, pannello web |
| Lingue | iOS: IT, EN · Android: IT, EN, ES, DE, FR, SQ |
| Prezzo | Gratis; abbonamenti Plus e Premium in app |
| Pubblicità | Nessuna |
| Crittografia | X25519 + AES-256-GCM, chiavi di gruppo AES-256, file AES-GCM; codice open source Apache-2.0; nessuna forward secrecy |
| Chiamate | Solo vocali, DTLS-SRTP |
| SOS | Posizione, batteria, video 30 s dall'app; Siri e Centro di Controllo su iPhone; widget e riquadro rapido su Android; non chiama il 112 |
| Server | Railway regione UE (azienda USA); file su Scaleway (Francia) |
| Contatto | info@getcentral.net |

Da non scrivere mai: videochiamate, SOS con tasto volume, "sicurezza garantita", "anonimo", certificazioni, numeri di download o voti non verificati, funzioni 2.0 nascoste (Live Activity, widget) prima di marzo, allerte Protezione Civile prima che la 1.9.1 sia pubblica.

### Email proposta di recensione (IT)

Oggetto: Central, chat cifrata e SOS senza localizzazione continua: proposta di prova

> Buongiorno,
>
> sono Mattia, lo sviluppatore indipendente di Central, un'app italiana gratuita per iPhone e Android che unisce chat cifrata end-to-end e strumenti di sicurezza personale: SOS con posizione e video, check-in "Sto bene", Viaggia sicuro e zone concordate.
>
> La differenza rispetto alle app di localizzazione familiare è che Central non segue nessuno di continuo: la posizione parte solo durante un viaggio, all'uscita da una zona o in un SOS. Il codice crittografico è pubblico e i limiti (per esempio l'assenza di forward secrecy) sono scritti sul sito.
>
> Se vi interessa provarla, posso attivarvi un periodo di Premium per la recensione. Materiale stampa, video e screenshot: https://getcentral.net/stampa.html
>
> Grazie per l'attenzione,
> Mattia
> info@getcentral.net

Nota: un accesso Premium gratuito per la prova è normale (si può dare con i codici offerta di App Store e Google Play, o con il regalo di abbonamento se il backend lo consente); chiedere una recensione positiva o pagarla no.

### Review pitch (EN)

Subject: Central: encrypted chat and SOS without 24/7 location tracking

> Hi,
>
> I'm Mattia, the independent developer of Central, a free iPhone and Android app from Italy that combines end-to-end encrypted chat with personal safety tools: SOS with location and video, an "I'm OK" check-in, Safe Trip and agreed safe zones.
>
> Unlike family locator apps, Central never tracks anyone continuously: location is shared only during a trip, when leaving a zone or in an SOS. The crypto code is open source and its limits (for example, no forward secrecy yet) are documented on the website.
>
> Happy to give you Premium access for a review. Press kit: https://getcentral.net/stampa.html
>
> Best,
> Mattia
> info@getcentral.net

## 4. Recensioni sugli store

Le valutazioni contano per l'ASO e per come le AI descrivono un'app. Metodi consentiti:

- Richiesta di valutazione nativa (SKStoreReviewController su iOS, In-App Review API su Android) dopo un momento positivo, per esempio un viaggio concluso bene. Verificato il 24/11: oggi non è nel codice dell'app. Aggiungerla è una modifica all'app (Android + iPhone) da approvare a parte.
- Rispondere a tutte le recensioni, anche negative, con calma e nel merito.
- Mai incentivi in cambio di recensioni (vietato da Apple e Google), mai recensioni di amici o account propri.

## 5. Misurare

- Menzioni: ricerca periodica di "Central: chat e sicurezza" e "getcentral.net" (Google Alerts è gratuito).
- Link in ingresso: Search Console, sezione Link, quando sarà verificata.
- Citazioni nelle risposte AI: Central AI Visibility Monitor (`tools/central-geo-monitor/`).
