# Rapporti

Cartella esclusa dalla pubblicazione (`_config.yml`).

- `weekly/`: rapporti settimanali (crawler e AI Visibility Monitor).
- `monthly/`: rapporti mensili.

Routine settimanale consigliata (10 minuti, dal PC con il repository):

```
python tools/seo-audit/check_site.py
python tools/crawler-check/crawler_check.py --markdown > reports/weekly/crawler-AAAA-MM-GG.md
```

I rapporti si salvano in una PR come ogni altra modifica. Nessuno script pubblica o modifica il sito da solo.
