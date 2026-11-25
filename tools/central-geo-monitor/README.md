# Central AI Visibility Monitor

Strumento locale per registrare se e come i motori AI (ChatGPT, Claude, Gemini, Perplexity, Google AI Overviews, Microsoft Copilot) parlano di Central. Non è pubblicato sul sito: `_config.yml` esclude `tools/`.

## Principio: solo verifiche vere

Il monitor non interroga nessuna AI da solo e non stima nulla. Ogni riga del registro è una domanda fatta davvero da una persona, con la risposta osservata. Così:

- nessuna API a pagamento, nessuna chiave, nessuna violazione dei termini d'uso delle piattaforme;
- nessun risultato simulato: se una piattaforma non è stata verificata, non compare.

Le API ufficiali di alcune piattaforme permetterebbero di automatizzare, ma sono a pagamento e le loro risposte spesso differiscono da quelle che vede un utente nell'app. Se un giorno servirà, va deciso e autorizzato a parte.

## Come si usa

1. Apri `index.html` con un doppio clic (funziona offline, nel browser).
2. Scheda **Nuova verifica**: scegli piattaforma e domanda, fai la domanda sulla piattaforma (meglio senza login o senza cronologia, così la risposta non dipende dalle tue conversazioni), poi registra l'esito:
   - **Mancata menzione**: Central non compare.
   - **Menzione negativa o con errori**: Central compare ma con informazioni sbagliate (es. "ha le videochiamate"). Annota l'errore nelle note: indica cosa correggere su sito e directory.
   - **Menzione del marchio**: compare in un elenco o di passaggio.
   - **Raccomandazione esplicita**: viene consigliata per quella domanda.
   - Poi le spunte: citazione con fonte, link diretto a getcentral.net, link agli store; posizione nell'elenco e concorrenti citati.
3. Scheda **Dashboard**: percentuale di menzioni, raccomandazioni, link, concorrenti, per piattaforma, categoria e mese.
4. Scheda **Importa / esporta**: esporta JSON (backup completo) e CSV (per Excel / Fogli). Il JSON si può reimportare su un altro computer.

I dati restano nel browser (localStorage) finché non li esporti. Esporta dopo ogni sessione.

## Ritmo consigliato

- Una sessione ogni 2 settimane: le 27 domande dell'archivio su 3 piattaforme (ChatGPT, Perplexity, Gemini) sono circa 80 verifiche, 60-90 minuti.
- Una volta al mese anche Claude, Copilot e Google AI Overviews (cerca su Google la domanda e guarda se compare il riquadro AI).
- Le risposte AI cambiano molto da una volta all'altra: conta l'andamento su più settimane, non la singola risposta.

## Rapporto

```
python tools/central-geo-monitor/report.py central-geo-monitor-AAAA-MM-GG.json --giorni 7  > reports/weekly/AAAA-MM-GG.md
python tools/central-geo-monitor/report.py central-geo-monitor-AAAA-MM-GG.json --giorni 30 > reports/monthly/AAAA-MM.md
```

Confronta il periodo con quello precedente ed elenca le risposte con errori su Central.

## File

- `index.html`: l'applicazione (HTML + JS, nessuna dipendenza, nessuna richiesta di rete).
- `domande.json`: archivio iniziale delle domande per categoria (già incluso nella pagina; se lo modifichi, rigenera la pagina o aggiungi le domande dalla scheda "Domande").
- `report.py`: rapporto Markdown dal JSON esportato.

Strumenti collegati: `tools/crawler-check/crawler_check.py` (risposte del sito ai bot, da lanciare dal PC) e `tools/seo-audit/check_site.py` (controllo offline dei file).
