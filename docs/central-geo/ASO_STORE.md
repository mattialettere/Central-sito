# App Store Optimization: proposte per App Store e Google Play

Aggiornato: 24 novembre 2026 · Fase 3 del progetto "Central GEO Engine"

**Niente è stato cambiato sugli store.** I testi attuali stanno in `central-apple/.github/store/scheda.json` e si pubblicano con i workflow Codemagic "Scheda App Store" / "Scheda Google Play", che lancia mattia. Qui sotto ci sono solo proposte, con il conteggio dei caratteri già verificato.

## 1. Diagnosi dei testi attuali

| Campo | Oggi (IT) | Osservazione |
|---|---|---|
| Nome | Central: chat e sicurezza | Buono: contiene "chat" e "sicurezza", disambigua il nome. Non cambiarlo (rinominare costa posizionamento). |
| Sottotitolo (iOS, 30) | Chat privata, mappa e SOS | "chat" è già nel nome: parola sprecata. Manca "famiglia", centrale nel posizionamento contro Life360. |
| Parole chiave (iOS, 100) | chat,messaggi,famiglia,posizione,sos,cifrata,amici,gruppi,viaggio,zone,mappa,città,gioco,chiamate | Apple indicizza già nome e sottotitolo: "chat", "sos" e "mappa" qui sono ripetizioni che non aggiungono nulla. Mancano "emergenza", "anziani", "privacy". |
| Descrizione | — | Scrive "Viaggio sicuro", nell'app la funzione si chiama "Viaggia sicuro": allineare. Non cita il check-in "Sto bene", che è un motivo forte per le famiglie con anziani. |
| Testo promozionale (170) | Chat cifrate…, Central City… | Mescola sicurezza e gioco; per chi cerca sicurezza familiare la parte City distrae. Si può cambiare in ogni momento senza nuova versione. |

Regole Apple da rispettare: niente nomi di altre app o marchi nelle parole chiave (quindi niente "life360" o "whatsapp"), niente prezzi o "gratis" nel nome, niente affermazioni non vere.

## 2. Proposta App Store

### Italiano

| Campo | Proposta | Caratteri |
|---|---|---|
| Sottotitolo | Chat cifrata, SOS e famiglia | 28 / 30 |
| Parole chiave | messaggi,posizione,emergenza,amici,gruppi,viaggio,zone,città,chiamate,anziani,allarme,privacy,gioco | 99 / 100 |
| Testo promozionale | Chat cifrate end-to-end e SOS con posizione per chi ami. La posizione si condivide solo durante un viaggio, in una zona concordata o in un'emergenza. Niente pubblicità. | 168 / 170 |

Descrizione: tenere quella attuale con tre ritocchi:

1. "Viaggio sicuro" → "Viaggia sicuro" (nome nell'app).
2. Aggiungere nella sezione sulla posizione: "• Check-in "Sto bene": un tocco al giorno; se la conferma non arriva, chi ti vuole bene riceve un avviso."
3. Prima riga più chiara per chi arriva dalla ricerca: "Central unisce chat cifrata end-to-end e strumenti di sicurezza per la famiglia, senza seguirti di continuo."

### Inglese (en-US)

| Campo | Proposta | Caratteri |
|---|---|---|
| Sottotitolo | Encrypted chat, SOS & family | 28 / 30 |
| Parole chiave | messenger,location,emergency,friends,groups,trip,geofence,privacy,calls,alert,elderly,city,game | 95 / 100 |
| Testo promozionale | End-to-end encrypted chats and an SOS with your location for the people you love. Location is shared only on a trip, in an agreed zone or in an emergency. No ads. | 162 / 170 |

Descrizione: "Safe trip" → "Safe Trip" (nome nell'app) e la stessa riga sul check-in: "• "I'm OK" check-in: one tap a day; if it doesn't arrive, the people who care about you get an alert."

## 3. Proposta Google Play

Google Play non ha campo parole chiave: conta il testo di titolo, descrizione breve e descrizione lunga.

| Campo | Proposta IT | Proposta EN |
|---|---|---|
| Titolo (30) | Central: chat e sicurezza (invariato, 25) | Central: Chat & Safety (invariato, 22) |
| Descrizione breve (80) | Chat cifrate, SOS con posizione, check-in e viaggi sicuri. Niente pubblicità. (77) | Encrypted chats, SOS with location, check-in and Safe Trip. No ads, ever. (73) |

Descrizione lunga: stessi ritocchi della versione iOS. Ripetere in modo naturale 2-3 volte "chat cifrata", "SOS", "famiglia", "posizione": Google la usa per capire l'app, ma penalizza le liste di parole chiave.

## 4. Screenshot

Gli screenshot attuali (`/mnt/project-files/ios/screenshot-store/`: chat, sicurezza, viaggio/perimetro, SOS, invita, City) coprono bene le funzioni. Due suggerimenti:

- Il primo screenshot è quello che conta di più nei risultati di ricerca: valutare di mettere per primo quello su sicurezza/SOS con un titolo tipo "La posizione solo quando serve", che è il vero elemento distintivo.
- Aggiungere uno screenshot del check-in "Sto bene" per il pubblico "genitori anziani".

## 5. Coerenza con sito e AI

Nome, descrizione breve e fatti devono essere identici su store, sito (`llms.txt`, JSON-LD) e schede directory. Quando i motori AI trovano la stessa descrizione in più fonti, la riportano con più fiducia. I testi brevi di riferimento sono in `DIGITAL_PR_PLAN.md` §3.

## 6. Come applicare (solo mattia)

1. Copiare i campi scelti in `.github/store/scheda.json` (repo central-apple), in una PR.
2. Lanciare i workflow "Scheda App Store" e "Scheda Google Play" da Codemagic.
3. Il testo promozionale iOS si aggiorna subito; sottotitolo e parole chiave richiedono l'invio di una nuova versione.
4. Dopo 4 settimane confrontare impressioni e conversioni in App Store Connect (Analytics) e Play Console (Acquisizione).
