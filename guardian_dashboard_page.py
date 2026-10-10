"""Pannello web di Central — login, chat cifrate, monitoraggio, privacy.

Perche vanilla JS e non un frontend separato
─────────────────────────────────────────────
Il pannello parla con le stesse API JSON gia esposte per l'app mobile
(/auth/login, /chats, /groups, /guardian-dashboard/...): non serve build
step, bundler o un secondo deploy. Il backend serve direttamente questa
pagina, come gia fa per le pagine di condivisione in routers/share.py.

Perche stringhe concatenate e non una f-string
───────────────────────────────────────────────
La versione precedente era una f-string: ogni graffa di JavaScript andava
raddoppiata. Con poche righe di script si regge; con la crittografia lato
browser diventa una fonte inesauribile di errori invisibili — una graffa
dimenticata non da errore Python, da JavaScript rotto in produzione. Qui
il codice JS e una stringa normale e si legge come si scrive.

Dove sta la crittografia
────────────────────────
Tutta nel browser, in _JS_CRYPTO. Il server non vede mai niente in chiaro,
esattamente come con l'app: la chiave privata X25519 arriva dal backup
cifrato (GET /users/me/key-backup) e si apre con la passphrase di recupero
che l'utente digita qui e che non lascia mai la pagina.

  • chat 1:1 → ECDH X25519 con la chiave pubblica dell'altro, SHA-256
  • gruppi   → busta della chiave di gruppo, aperta con lo stesso ECDH
  • media    → formato CEMD (vedi MediaCrypto.kt): HKDF dal salt nel file

Perche la passphrase non viene mai salvata
───────────────────────────────────────────
Ne in localStorage ne in sessionStorage: resta in memoria finche la scheda
e aperta. Un pannello web e piu esposto di un telefono — sessioni lasciate
aperte, computer condivisi — e la chiave privata E2E e l'unica cosa che
non deve mai poter essere ripescata da chi si siede dopo.
"""

# Sezione Community: stile e script in un file a parte.
from dashboard_community import JS_COMMUNITY, STYLE_COMMUNITY

_STYLE = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body {
  margin: 0; font-family: -apple-system, system-ui, Roboto, sans-serif;
  background: linear-gradient(#FFF8F3, #FCE7DA); color: #2B211D;
  min-height: 100vh;
}
/* ═══════════════════════════════════════════════════════════════════
   GUSCIO A BARRA LATERALE
   Sostituisce le schede in cima: con dieci sezioni le schede
   diventavano una fila illeggibile, e su uno schermo largo — che e
   il posto dove questo pannello viene usato davvero — la colonna a
   sinistra e spazio che c'e gia e non toglie nulla al contenuto.
   ═══════════════════════════════════════════════════════════════════ */
.shell { display: flex; min-height: 100vh; align-items: stretch; }

.sidebar { width: 232px; flex: none; background: #fff;
  border-right: 1px solid #F0E6E0; display: flex; flex-direction: column;
  position: sticky; top: 0; height: 100vh; }
.sidebar-brand { display: flex; align-items: center; gap: 9px;
  padding: 20px 18px 18px; font-weight: 700; font-size: 16px; }
.brand-mark { width: 28px; height: 28px; border-radius: 8px; flex: none;
  background: linear-gradient(135deg, #F07E2B, #E8590C); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 15px; }
.sidebar-nav { flex: 1; overflow-y: auto; padding: 0 10px; }
.nav-item { display: flex; align-items: center; gap: 10px; width: 100%;
  background: none; border: none; text-align: left; cursor: pointer;
  padding: 9px 11px; margin-bottom: 2px; border-radius: 10px;
  font-size: 14px; color: #6B5D57; font-family: inherit; }
.nav-item:hover { background: #FBF3EE; }
.nav-item.active { background: #FDEDE2; color: #D2600F; font-weight: 600; }
.nav-ico { width: 18px; text-align: center; flex: none; }
.nav-badge { margin-left: auto; background: #E8590C; color: #fff;
  border-radius: 9px; padding: 1px 7px; font-size: 11px; font-weight: 700; }
.sidebar-user { border-top: 1px solid #F0E6E0; padding: 14px 16px;
  display: flex; align-items: center; gap: 10px; }
.su-avatar { width: 34px; height: 34px; border-radius: 50%; flex: none;
  background: #EFE1D9; color: #9A7460; display: flex; align-items: center;
  justify-content: center; font-weight: 700; font-size: 12px;
  object-fit: cover; }
.su-name { font-size: 13.5px; font-weight: 600; line-height: 1.2; }
.su-role { font-size: 11.5px; color: #A9968D; }
.su-exit { margin-left: auto; background: none; border: none; cursor: pointer;
  color: #A9968D; font-size: 17px; }

.main { flex: 1; min-width: 0; }
.main-head { display: flex; align-items: center; gap: 14px;
  padding: 18px 26px; border-bottom: 1px solid #F0E6E0; background: #fff;
  position: sticky; top: 0; z-index: 20; }
.main-title { font-size: 19px; font-weight: 700; margin: 0; }
.main-sub { font-size: 12.5px; color: #A9968D; margin-top: 1px; }
.main-actions { margin-left: auto; display: flex; align-items: center; gap: 9px; }
.main-body { padding: 22px 26px 44px; }

/* ── Riquadri dei numeri ─────────────────────────────────────────── */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(178px, 1fr));
  gap: 14px; margin-bottom: 18px; }
/* Oltre i 1500px i riquadri smettono di allargarsi e si affiancano tutti
   su una riga: un numero di due cifre dentro una scheda larga mezzo
   schermo e spazio sprecato, non leggibilita. */
@media (min-width: 1500px) {
  .kpis { grid-template-columns: repeat(4, minmax(200px, 1fr)); max-width: 1100px; }
}
.kpi { background: #fff; border: 1px solid #F0E6E0; border-radius: 14px;
  padding: 15px 17px; }
.kpi-label { font-size: 12.5px; font-weight: 600; margin-bottom: 6px; }
.kpi-value { font-size: 31px; font-weight: 800; line-height: 1; }
.kpi-foot { font-size: 12px; color: #A9968D; margin-top: 5px; }
.kpi-blue  .kpi-label { color: #2563EB; } .kpi-blue  .kpi-value { color: #2563EB; }
.kpi-amber .kpi-label { color: #D97706; } .kpi-amber .kpi-value { color: #D97706; }
.kpi-red   .kpi-label { color: #DC2626; } .kpi-red   .kpi-value { color: #DC2626; }
.kpi-green .kpi-label { color: #16A34A; } .kpi-green .kpi-value { color: #16A34A; }

/* ── Griglia della panoramica ────────────────────────────────────── */
.grid-2 { display: grid; grid-template-columns: 1.55fr 1fr; gap: 16px;
  margin-bottom: 16px; align-items: start; }
/* Su schermi larghi la mappa prende piu spazio e la colonna laterale
   resta a misura di testo: allargarla oltre non aggiunge niente. */
@media (min-width: 1500px) {
  .grid-2 { grid-template-columns: minmax(0, 2.2fr) minmax(320px, 380px); }
}
.panel { background: #fff; border: 1px solid #F0E6E0; border-radius: 14px;
  overflow: hidden; }
.panel-head { padding: 13px 16px; border-bottom: 1px solid #F5EAE3;
  font-size: 13.5px; font-weight: 700; display: flex; align-items: center; gap: 8px; }
.panel-body { padding: 14px 16px; }
.panel-body.flush { padding: 0; }
.panel-link { margin-left: auto; font-size: 12.5px; font-weight: 600;
  color: #E8590C; cursor: pointer; background: none; border: none;
  font-family: inherit; }

#live-map { height: 340px; width: 100%; background: #F3EDE9;
  transition: height .25s ease; }

/* ── Mappa ingrandita ─────────────────────────────────────────────── */
/* Esce dalla colonna e occupa tutta la larghezza della griglia: sotto
   restano visibili l'elenco dei viaggi e i riquadri dei check-in, cosi
   ingrandire non fa perdere il contesto. */
.panel-head-click { cursor: pointer; user-select: none; }
.panel-head-click:hover { background: #FDF6F1; }
.map-espandi { margin-left: auto; font-size: 12px; font-weight: 600;
  color: #E8590C; }
.mappa-grande { grid-column: 1 / -1; }
.mappa-grande #live-map { height: min(72vh, 720px); }
.map-note { padding: 10px 16px; font-size: 12px; color: #A9968D;
  border-top: 1px solid #F5EAE3; }

/* ── Selezione e archiviazione degli avvisi ──────────────────────── */
.sel-bar { display: flex; align-items: center; gap: 12px; padding: 9px 16px;
  border-bottom: 1px solid #F5EAE3; font-size: 13px; color: #6B5D57; }
.sel-all { display: flex; align-items: center; gap: 7px; cursor: pointer; }
.azioni-bar { display: flex; align-items: center; gap: 10px; padding: 10px 16px;
  background: #FDF3EC; border-bottom: 1px solid #F5EAE3; font-size: 13px;
  font-weight: 600; }
.azioni-bar > span { margin-right: auto; }
.alert-check { margin-top: 6px; flex: none; width: 16px; height: 16px; cursor: pointer; }
.alert-archiviato { opacity: .52; }

/* ── Elenco degli avvisi ─────────────────────────────────────────── */
.alert-item { display: flex; gap: 11px; padding: 12px 16px;
  border-bottom: 1px solid #F5EAE3; align-items: flex-start; }
.alert-item:last-child { border-bottom: none; }
.alert-ico { width: 30px; height: 30px; border-radius: 9px; flex: none;
  display: flex; align-items: center; justify-content: center; font-size: 14px; }
.ai-red   { background: #FEE9E7; }
.ai-amber { background: #FDF0E0; }
.alert-main { min-width: 0; flex: 1; }
.alert-kind { font-size: 13.5px; font-weight: 700; }
.alert-kind.red { color: #DC2626; } .alert-kind.amber { color: #D97706; }
.alert-who { font-size: 13px; margin-top: 1px; }
.alert-where { font-size: 12px; color: #A9968D; }
.alert-time { font-size: 12px; color: #A9968D; flex: none;
  white-space: nowrap; min-width: 92px; text-align: right; }

/* ── Barra di avanzamento ────────────────────────────────────────── */
.prog-head { display: flex; align-items: baseline; gap: 8px;
  font-size: 13.5px; margin-bottom: 9px; }
.prog-pct { margin-left: auto; font-weight: 700; }
.prog-track { height: 8px; background: #F1E7E1; border-radius: 5px; overflow: hidden; }
.prog-fill { height: 100%; background: linear-gradient(90deg, #F59E0B, #16A34A);
  border-radius: 5px; transition: width .4s ease; }

/* ── Righe persona ───────────────────────────────────────────────── */
.pl-row { display: flex; align-items: center; gap: 10px; padding: 10px 16px;
  border-bottom: 1px solid #F5EAE3; font-size: 13.5px; }
.pl-row:last-child { border-bottom: none; }
.pl-when { margin-left: auto; color: #A9968D; font-size: 12.5px; flex: none; }

@media (max-width: 900px) {
  .shell { display: block; }
  .sidebar { position: static; width: auto; height: auto;
    border-right: none; border-bottom: 1px solid #F0E6E0; }
  .sidebar-nav { display: flex; overflow-x: auto; padding: 0 8px 8px; }
  .nav-item { flex: none; margin: 0 2px; }
  .nav-item span:not(.nav-ico):not(.nav-badge) { display: none; }
  .sidebar-user { display: none; }
  .grid-2 { grid-template-columns: 1fr; }
  .main-body { padding: 16px 14px 40px; }
}

/* ── Visore immagini a tutto schermo ──────────────────────────────── */
.visore { position: fixed; inset: 0; z-index: 9999; background: rgba(24,18,15,.92);
  display: flex; align-items: center; justify-content: center; padding: 34px; }
.visore img { max-width: 100%; max-height: 100%; object-fit: contain;
  border-radius: 6px; box-shadow: 0 18px 50px rgba(0,0,0,.5); }
.visore-chiudi { position: absolute; top: 16px; right: 20px; background: none;
  border: none; color: #fff; font-size: 38px; line-height: 1; cursor: pointer;
  opacity: .8; font-family: inherit; }
.visore-chiudi:hover { opacity: 1; }

/* ── Dispositivi ──────────────────────────────────────────────────── */
.dev-row { display: flex; align-items: center; gap: 12px; padding: 11px 0;
  border-bottom: 1px solid #F5EAE3; }
.dev-row:last-child { border-bottom: none; }
.dev-off { opacity: .55; }
.dev-info { min-width: 0; flex: 1; }
.dev-name { font-weight: 600; font-size: 14.5px; }
.dev-meta { color: #A9968D; font-size: 12.5px; margin-top: 2px; }
.dev-tag { display: inline-block; margin-left: 7px; font-size: 11px;
  font-weight: 600; background: #F3DED2; color: #9A7460;
  padding: 2px 7px; border-radius: 7px; vertical-align: middle; }
.dev-tag-off { background: #EDE9E7; color: #8C7A72; }
.dev-btn { background: #fff; color: #D93025; border: 1px solid #F0C4BF;
  border-radius: 8px; padding: 7px 13px; font-size: 13px; font-weight: 600;
  cursor: pointer; flex: none; }
.dev-btn:hover { background: #FFF3F2; }

/* ── Intestazione della cronologia e stampa ───────────────────────── */
.tl-head { display: flex; align-items: flex-start; gap: 12px;
  justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; }
.tl-actions { display: flex; gap: 7px; flex: none; }
.tl-actions button, .tl-actions select {
  background: #fff; border: 1px solid #E3D5CC; border-radius: 8px;
  padding: 6px 11px; font-size: 13px; color: #57534E; cursor: pointer; }
.tl-actions button:hover { background: #FAF3EE; }

@media print {
  /* Stampa della sola cronologia: il resto della pagina — schede,
     riquadri, barra delle schede — sparisce. Un foglio destinato a
     un fascicolo non deve portarsi dietro l'interfaccia. */
  .no-print, .topbar, .tabs, .refresh-note { display: none !important; }
  body.printing-timeline #app > * { display: none !important; }
  body.printing-timeline #tab-body,
  body.printing-timeline #app,
  body.printing-timeline #timeline-box,
  body.printing-timeline #timeline-card { display: block !important; }
  body.printing-timeline #tab-body > *:not(#timeline-box) { display: none !important; }
  .card { box-shadow: none; border: 1px solid #ddd; break-inside: avoid; }
  .tl-day { break-inside: avoid; }
}

/* ── Riquadro allarmi per persona ─────────────────────────────────── */
.sos-wrap { margin-top: 10px; }
.sos-toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.sos-toggle { background: none; border: none; cursor: pointer; font-family: inherit;
  font-size: 13.5px; font-weight: 700; color: #B8271D; padding: 4px 0;
  display: flex; align-items: center; gap: 7px; }
.sos-freccia { display: inline-block; transition: transform .18s ease; }
.sos-freccia.chiusa { transform: rotate(-90deg); }
.sos-check { width: 15px; height: 15px; margin-right: 7px; cursor: pointer;
  vertical-align: middle; }
.tutela-cliccabile { cursor: pointer; border-radius: 8px; }
.tutela-cliccabile:hover { background: #FBF3EE; }
.persona-evidenziata { outline: 2px solid #E8590C; outline-offset: 3px;
  transition: outline-color 1.2s ease; }

/* ── Presa in carico degli allarmi ────────────────────────────────── */
.ack-box { margin-top: 10px; padding-top: 10px; border-top: 1px solid #F3C6C0; }
.ack-empty { font-size: 12.5px; color: #B08078; font-style: italic; margin-bottom: 8px; }
.ack-row { display: flex; gap: 7px; align-items: flex-start; font-size: 13px;
  padding: 4px 0; color: #2E6B45; }
.ack-check { flex: none; font-weight: 700; }
.ack-when { color: #A9968D; font-size: 12px; }
.ack-note { display: block; color: #57534E; font-style: italic; margin-top: 2px; }
.ack-btn { margin-top: 8px; background: #D93025; color: #fff; border: none;
  border-radius: 8px; padding: 9px 16px; font-size: 14px; font-weight: 600;
  cursor: pointer; }
.ack-btn:hover { background: #B8271D; }
.ack-btn:disabled { background: #C9B4AE; cursor: default; }

/* ── Riquadri di riepilogo e cronologia ───────────────────────────── */
.tutela-row { display: flex; align-items: center; gap: 10px; padding: 7px 0;
  border-bottom: 1px solid #F5EAE3; font-size: 14px; }
.tutela-row:last-child { border-bottom: none; }
.tutela-dot { width: 9px; height: 9px; border-radius: 50%; flex: none; }
.tutela-name { font-weight: 600; }
.tutela-state { margin-left: auto; font-size: 13px; }
.tutela-seen { color: #A9968D; font-size: 12px; min-width: 96px; text-align: right; }
.alarm-card { border: 1px solid #F3C6C0; background: #FFF6F5; }

.tl-day { margin-bottom: 16px; }
.tl-day-label { font-size: 12px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .04em; color: #A9968D; margin: 0 0 6px; }
.tl-row { display: flex; align-items: center; gap: 9px; padding: 6px 0;
  border-bottom: 1px solid #F8F0EB; font-size: 13.5px; }
.tl-row:last-child { border-bottom: none; }
.tl-time { color: #A9968D; font-size: 12px; min-width: 40px; flex: none; }
.tl-icon { flex: none; }
.tl-avatar { width: 24px; height: 24px; border-radius: 50%; flex: none;
  object-fit: cover; }
.tl-initials { display: inline-flex; align-items: center; justify-content: center;
  background: #F3DED2; color: #9A7460; font-size: 10px; font-weight: 700; }
.tl-text { min-width: 0; }
.tl-detail { color: #8C7A72; display: block; font-size: 12.5px; }

@media (max-width: 560px) {
  .tutela-seen { display: none; }
  .tl-detail { display: inline; margin-left: 4px; }
}
.legal-footer { max-width: 860px; margin: 0 auto; padding: 0 16px 32px;
  text-align: center; font-size: 12.5px; color: #8C7A72; }
.legal-footer a { color: #8C7A72; text-decoration: none; margin: 0 6px; }
.legal-footer a:hover { text-decoration: underline; }
.wrap { max-width: 860px; margin: 0 auto; padding: 24px 16px 64px; }

/* Il pannello vive dentro lo stesso .wrap delle pagine legali, che e
   largo 860px perche una colonna di testo piu larga di cosi si legge
   male. Per una dashboard quella misura e sbagliata al contrario: su un
   monitor da 27 pollici lasciava due terzi di schermo vuoti e schiacciava
   le schede in colonne cosi strette da mandare a capo una parola per riga.

   :has() distingue i due casi senza toccare il JS: quando dentro c'e la
   shell del pannello, il limite di larghezza sparisce. */
.wrap:has(.shell) { max-width: none; padding: 0; }
.card { background: #FFFCFA; border-radius: 20px; padding: 22px;
  box-shadow: 0 10px 40px rgba(180,110,70,.14); margin-bottom: 16px; }
h1 { font-size: 22px; margin: 0 0 4px; }
h2 { font-size: 16px; margin: 0 0 10px; }
.sub { color: #8C7A72; font-size: 13.5px; margin-bottom: 20px; }
label { display: block; font-size: 13px; color: #8C7A72; margin: 14px 0 6px; }
input[type=email], input[type=password], input[type=text], input[type=number], select.campo {
  width: 100%; padding: 12px 14px; border-radius: 12px; border: 1.5px solid #F1E3DA;
  font-size: 15px; background: #FFFCFA; font-family: inherit;
}
input:focus { outline: none; border-color: #EA5B2E; }
button.primary {
  width: 100%; margin-top: 20px; padding: 13px; border: none; border-radius: 14px;
  background: #EA5B2E; color: white; font-size: 15px; font-weight: 600; cursor: pointer;
}
button.primary:hover { background: #DE5218; }
button.primary:disabled { opacity: .55; cursor: default; }
button.ghost { border: 1.5px solid #F1E3DA; background: none; color: #6B5C54;
  padding: 9px 14px; border-radius: 12px; font-size: 13.5px; cursor: pointer; }
button.ghost:hover { border-color: #EA5B2E; color: #EA5B2E; }
.error-box { background: #FDEBEB; color: #C0392B; border-radius: 10px; padding: 10px 14px;
  font-size: 13.5px; margin-top: 14px; }
.info-box { background: #E3F5EC; color: #2E8B5C; border-radius: 10px; padding: 10px 14px;
  font-size: 13.5px; margin-top: 14px; }
.warn-box { background: #FDF3DA; color: #96690F; border-radius: 10px; padding: 10px 14px;
  font-size: 13px; margin-top: 12px; }
/* Scheda Aziende (solo moderatori). */
.org-form textarea, .org-form input[type=date] {
  width: 100%; padding: 12px 14px; border-radius: 12px; border: 1.5px solid #F1E3DA;
  font-size: 15px; background: #FFFCFA; font-family: inherit; box-sizing: border-box; resize: vertical;
}
.org-form textarea:focus, .org-form input[type=date]:focus { outline: none; border-color: #EA5B2E; }
.org-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; align-items: end; }
.org-btn { width: 100%; padding: 12px 14px; }
.org-danger:hover { border-color: #C0392B; color: #C0392B; }
.org-pill { font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 999px; }
.org-on { background: #E3F5EC; color: #2E8B5C; }
.org-warn { background: #FDF3DA; color: #96690F; }
.org-off { background: #F4EFE9; color: #8C7A72; }
.org-group { margin-top: 16px; }
.org-group-title { font-weight: 700; font-size: 14px; margin-bottom: 4px; }
.org-member { display: flex; gap: 10px; align-items: center; padding: 8px 0; border-bottom: 1px solid #F1E3DA; }
.org-member:last-child { border-bottom: none; }
.org-email { font-weight: 600; font-size: 14px; overflow-wrap: anywhere; }
.org-add { margin-top: 18px; padding-top: 4px; border-top: 1px solid #F1E3DA; }
.org-edit { margin-top: 16px; }
.vs-periodo { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }
.vs-periodo .vs-on { border-color: #EA5B2E; color: #EA5B2E; font-weight: 600; }
.vs-tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }
.vs-tiles .card { margin-bottom: 0; }
.vs-big { font-size: 30px; font-weight: 700; margin: 4px 0; font-variant-numeric: tabular-nums; }
.vs-tiles + .card { margin-top: 16px; }
.vs-leg { display: inline-block; width: 10px; height: 10px; border-radius: 3px; vertical-align: middle; margin-right: 4px; }
.vs-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
.vs-grid .card { margin-bottom: 0; }
.vs-righe { display: flex; flex-direction: column; gap: 6px; }
.vs-riga { position: relative; display: flex; justify-content: space-between; gap: 10px; padding: 7px 10px; font-size: 13.5px; }
.vs-barra { position: absolute; left: 0; top: 0; bottom: 0; background: #FCE6DA; border-radius: 8px; z-index: 0; }
.vs-nome, .vs-val { position: relative; z-index: 1; }
.vs-nome { overflow-wrap: anywhere; }
.vs-val { white-space: nowrap; font-variant-numeric: tabular-nums; font-weight: 600; }
.org-edit summary { cursor: pointer; font-weight: 600; color: #6B5C54; font-size: 14px; }
.topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.logout { color: #8C7A72; font-size: 13px; text-decoration: underline; cursor: pointer; border: none; background: none; }
.empty { text-align: center; color: #8C7A72; padding: 40px 20px; }
.muted { color: #8C7A72; font-size: 12.5px; }

.tabs { display: flex; gap: 6px; background: #F6EDE7; padding: 5px; border-radius: 14px; margin-bottom: 18px; }
.tabs button { flex: 1; padding: 10px; border: none; background: none; border-radius: 10px;
  font-size: 14px; font-weight: 600; color: #8C7A72; cursor: pointer; font-family: inherit; }
.tabs button.active { background: #FFFCFA; color: #2B211D; box-shadow: 0 2px 8px rgba(180,110,70,.12); }

.person { display: flex; gap: 14px; align-items: flex-start; }
.avatar { width: 46px; height: 46px; border-radius: 50%; background: #FDE4D5; color: #B4502C;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px;
  flex-shrink: 0; position: relative; overflow: hidden; }
.avatar img { width: 100%; height: 100%; object-fit: cover; }
.dot { width: 10px; height: 10px; border-radius: 50%; position: absolute; bottom: 0; right: 0;
  border: 2px solid #FFFCFA; }
.dot.online { background: #3FB27F; } .dot.offline { background: #C9BBB2; }
.person-name { font-weight: 700; font-size: 16px; }
.person-meta { color: #8C7A72; font-size: 12.5px; margin-top: 1px; }

.badges { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.badge { display: inline-flex; align-items: center; gap: 5px; border-radius: 999px;
  padding: 5px 12px; font-size: 12.5px; font-weight: 600; }
.badge.ok { background: #E3F5EC; color: #2E8B5C; }
.badge.warn { background: #FDF3DA; color: #B4832C; }
.badge.danger { background: #FDEBEB; color: #C0392B; }
.badge.neutral { background: #F1E9E3; color: #8C7A72; }

.trail { margin-top: 12px; border-top: 1px solid #F1E3DA; padding-top: 10px; }
.trail-item { display: flex; justify-content: space-between; font-size: 12.5px; color: #6B5C54; padding: 3px 0; }
.refresh-note { text-align: center; color: #B4A69C; font-size: 11.5px; margin-top: 8px; }

.sos-card { border: 2px solid #F3C9C2; border-radius: 14px; margin-top: 12px; overflow: hidden; }
.sos-head { background: #C0392B; color: white; padding: 7px 12px; font-size: 12.5px;
  font-weight: 700; display: flex; justify-content: space-between; }
.sos-body { padding: 12px; font-size: 13px; color: #4A3F3A; }
.sos-body a { color: #C0392B; font-weight: 600; }
.sos-body video { width: 100%; border-radius: 10px; margin-top: 10px; background: #000; }

/* ── Chat ─────────────────────────────────────────────────────────── */
/* Impianto simile a WhatsApp Web: elenco stretto e fisso a sinistra,
   conversazione che si prende tutto il resto.

   L'altezza e legata alla finestra e non a una percentuale del contenuto:
   con 68vh la conversazione occupava due terzi dello schermo e sotto
   restava una fascia vuota. calc() parte dall'altezza reale e sottrae
   testata e margini, cosi il riquadro arriva in fondo qualunque sia il
   monitor. */
.chat-layout { display: flex; gap: 0; align-items: stretch;
  height: calc(100vh - 190px); min-height: 480px; }
.chat-list { width: 340px; flex-shrink: 0; overflow-y: auto;
  border-right: 1px solid #F0E6E0; padding-right: 12px; }
.chat-item { display: flex; gap: 11px; align-items: center; padding: 10px; border-radius: 12px; cursor: pointer; }
.chat-item:hover { background: #FBF1EA; }
.chat-item.active { background: #FDE4D5; }
.chat-item .avatar { width: 40px; height: 40px; font-size: 14px; }
.chat-title { font-weight: 600; font-size: 14px; }
.chat-preview { color: #8C7A72; font-size: 12px; margin-top: 1px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 240px; }
.chat-panel { flex: 1; min-width: 0; display: flex; flex-direction: column;
  padding-left: 18px; }
.chat-permesso:empty { display: none; }
.perm-riga { display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  background: #FFF6EF; border: 1px solid #F0E6E0; border-radius: 10px;
  padding: 8px 12px; margin-bottom: 10px; font-size: 13px; color: #6B564E; }
.msgs-wrap { flex: 1; position: relative; min-height: 0; display: flex; }
.msgs { flex: 1; overflow-y: auto; padding: 4px 2px 10px; display: flex; flex-direction: column; gap: 8px; }
.giu-btn { position: absolute; right: 14px; bottom: 14px; width: 38px; height: 38px;
  border-radius: 50%; border: 1px solid #F0E6E0; background: #fff; color: #D2600F;
  font-size: 17px; cursor: pointer; box-shadow: 0 2px 10px rgba(0,0,0,.12);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; pointer-events: none; transition: opacity .18s; }
.giu-btn.visibile { opacity: 1; pointer-events: auto; }
/* 78% su una conversazione larga produceva righe lunghissime, faticose da
   seguire con l'occhio. Il limite in caratteri tiene la riga leggibile
   qualunque sia la larghezza della finestra, e la percentuale continua a
   valere sugli schermi stretti. */
.bubble { max-width: min(78%, 46em); padding: 9px 13px; border-radius: 16px;
  font-size: 14px; line-height: 1.4; word-wrap: break-word; }
.bubble.mine { align-self: flex-end; background: #EA5B2E; color: white; border-bottom-right-radius: 5px; }
.bubble.theirs { align-self: flex-start; background: #F4EBE5; color: #2B211D; border-bottom-left-radius: 5px; }
.bubble .time { display: block; font-size: 10.5px; opacity: .65; margin-top: 4px; }
.bubble img, .bubble video { max-width: 100%; border-radius: 10px; display: block; }
.bubble audio { width: 230px; }
.bubble .locked { font-style: italic; opacity: .75; }
.bubble .sondaggio-domanda { font-weight: 600; margin-bottom: 6px; }
.bubble .sondaggio-riga { margin: 5px 0; font-size: 13px; }
.bubble .sondaggio-barra { height: 5px; border-radius: 3px; background: rgba(0,0,0,.12); margin-top: 3px; overflow: hidden; }
.bubble.mine .sondaggio-barra { background: rgba(255,255,255,.3); }
.bubble .sondaggio-barra > span { display: block; height: 100%; background: currentColor; opacity: .7; }
.bubble .sondaggio-nota { font-size: 11.5px; opacity: .75; margin-top: 6px; }
.reazioni { display: flex; flex-wrap: wrap; gap: 4px; margin-top: -2px; margin-bottom: 4px; }
.reazioni span { background: #fff; border: 1px solid #EADFD8; border-radius: 12px; padding: 1px 8px; font-size: 13px; color: #2B211D; }
.bubble-wrap { display: flex; flex-direction: column; }
.bubble-wrap.mine { align-items: flex-end; }
.bubble-wrap.theirs { align-items: flex-start; }
.chat-head:empty { display: none; }
.chat-head { display: flex; align-items: center; gap: 10px; padding-bottom: 10px;
  margin-bottom: 8px; border-bottom: 1px solid #F1E3DA; }
.chat-head-nome { flex: 1; font-weight: 700; font-size: 15px; }
.chat-head-mappa { padding: 7px 12px; font-size: 13px; }
.card-mappa { display: flex; gap: 10px; align-items: center; border: none; background: none;
  color: inherit; font: inherit; text-align: left; cursor: pointer; padding: 0; }
.card-mappa-ico { font-size: 22px; }
.card-mappa-apri { font-size: 12.5px; text-decoration: underline; opacity: .85; }
.chat-item .chat-testo { flex: 1; min-width: 0; }
.chat-item.non-letta .chat-title { font-weight: 700; }
.chat-nonletti { background: #EA5B2E; color: #fff; border-radius: 999px; font-size: 11px;
  font-weight: 700; min-width: 20px; height: 20px; padding: 0 6px; display: flex;
  align-items: center; justify-content: center; flex-shrink: 0; }
.chat-panel { position: relative; }
.allegati:empty { display: none; }
.allegati { border: 1px solid #F0E6E0; background: #FFF9F5; border-radius: 12px;
  padding: 8px 10px; margin-top: 10px; display: flex; flex-direction: column; gap: 6px; }
.allegato { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.allegato-nome { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.allegato-dim { color: #8C7A72; font-size: 12px; flex-shrink: 0; }
.allegato-x { border: none; background: none; color: #8C7A72; font-size: 18px; cursor: pointer; padding: 0 4px; }
.allegati-azioni { display: flex; align-items: center; gap: 8px; justify-content: flex-end;
  border-top: 1px solid #F0E6E0; padding-top: 6px; }
.allegati-stato { flex: 1; color: #6B564E; font-size: 12px; }
.primary-sm { padding: 6px 16px; border: none; border-radius: 10px; background: #EA5B2E;
  color: #fff; font-weight: 600; cursor: pointer; font-size: 13px; }
.primary-sm:disabled, .allegati .ghost:disabled { opacity: .5; cursor: default; }
.composer .attach-btn { padding: 0 12px; background: #F4EBE5; color: #6B564E; font-size: 18px; }
.drop-velo { position: absolute; inset: 0; display: none; align-items: center; justify-content: center;
  background: rgba(234, 91, 46, .08); border: 2px dashed #EA5B2E; border-radius: 14px;
  color: #D2600F; font-weight: 600; font-size: 15px; pointer-events: none; z-index: 5; }
.drop-velo.visibile { display: flex; }
.composer { display: flex; gap: 8px; padding-top: 12px; border-top: 1px solid #F1E3DA; }
.composer input { flex: 1; }
.composer button { padding: 0 20px; border: none; border-radius: 12px; background: #EA5B2E;
  color: white; font-weight: 600; cursor: pointer; font-size: 14px; }
.composer button:disabled { opacity: .5; cursor: default; }
@media (max-width: 720px) {
  .chat-layout { flex-direction: column; height: auto; }
  .chat-list { width: 100%; max-height: 240px;
    border-right: none; border-bottom: 1px solid #F0E6E0; padding-right: 0; }
  .chat-panel { padding-left: 0; }
}

/* ── Privacy ──────────────────────────────────────────────────────── */
.danger-zone { border: 1.5px solid #F5D5D0; }
.danger-zone h2 { color: #C0392B; }
.danger-zone p, .privacy-block p { font-size: 13px; color: #8C7A72; margin: 0 0 14px; }
.privacy-block { border-top: 1px solid #F1E3DA; padding-top: 18px; margin-top: 18px; }
button.danger-outline {
  border: 1.5px solid #C0392B; color: #C0392B; background: none;
  padding: 10px 16px; border-radius: 12px; font-size: 13.5px; font-weight: 600; cursor: pointer;
}
button.danger-outline:hover { background: #FDEBEB; }

/* ── Moderazione ──────────────────────────────────────────────────── */
.report-card { border: 1.5px solid #F1E3DA; border-radius: 14px; padding: 14px; margin-bottom: 12px; }
.report-card.urgent { border-color: #E8A9A0; background: #FFF7F6; }
.report-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
.report-reason { font-weight: 700; font-size: 14px; }
.report-meta { color: #8C7A72; font-size: 12px; }
.snapshot { background: #F6EDE7; border-radius: 10px; padding: 10px 12px; margin-top: 10px;
  font-size: 13px; white-space: pre-wrap; word-break: break-word; max-height: 220px; overflow-y: auto; }
.snapshot img, .snapshot video { max-width: 100%; border-radius: 8px; }
.unverified { background: #FDF3DA; color: #96690F; border-radius: 8px; padding: 8px 10px;
  font-size: 12px; margin-top: 10px; }
.report-actions { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
.report-actions button { padding: 8px 14px; border-radius: 10px; font-size: 12.5px; font-weight: 600;
  cursor: pointer; border: 1.5px solid #F1E3DA; background: none; color: #6B5C54; }
.report-actions button.remove { border-color: #C0392B; color: #C0392B; }
.report-actions button:hover { border-color: #EA5B2E; color: #EA5B2E; }
/* Pulsanti piccoli nelle righe di elenco (editor perimetri). */
.btn-mini { border: 1.5px solid #F1E3DA; background: #FFFCFA; color: #6B5C54;
  border-radius: 8px; padding: 4px 10px; font-size: 12.5px; cursor: pointer;
  margin-left: 6px; }
.btn-mini:hover { border-color: #EA5B2E; color: #EA5B2E; }
.pill { display: inline-block; border-radius: 999px; padding: 3px 10px; font-size: 11.5px; font-weight: 700; }
.pill.red { background: #FDEBEB; color: #C0392B; }
.pill.grey { background: #F1E9E3; color: #8C7A72; }

/* Pallino con la foto di chi viaggia: bordo nel colore del suo tragitto. */
.pin-persona { position: relative; width: 46px; height: 56px; }
.pin-persona-foto { width: 42px; height: 42px; border-radius: 50%; border: 3px solid var(--colore);
  background: #FDE4D5; color: #D2600F; font-weight: 700; font-size: 14px; overflow: hidden;
  display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,.25); }
.pin-persona-foto img { width: 100%; height: 100%; object-fit: cover; }
.pin-persona::after { content: ''; position: absolute; left: 50%; top: 44px; transform: translateX(-50%);
  border: 7px solid transparent; border-top: 10px solid var(--colore); border-bottom: 0; }
/* Passeggiata: piedino in un tondo bianco sul bordo del pallino, per
   distinguerla a colpo d'occhio da un viaggio verso una meta. */
.pin-persona-badge { position: absolute; right: -4px; top: -4px; width: 20px; height: 20px;
  border-radius: 50%; background: #fff; border: 2px solid var(--colore);
  display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 4px rgba(0,0,0,.25); }
.pin-persona-badge svg { width: 12px; height: 12px; }
.viaggio-foto { width: 26px; height: 26px; border-radius: 50%; border: 2px solid; overflow: hidden;
  display: inline-flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700;
  color: #D2600F; background: #FDE4D5; flex-shrink: 0; margin-right: 8px; }
.viaggio-foto img { width: 100%; height: 100%; object-fit: cover; }

/* ── Mappa personalizzata ─────────────────────────────────────────── */
.mp-overlay { position: fixed; inset: 0; z-index: 1500; background: rgba(43,33,29,.45);
  display: flex; align-items: center; justify-content: center; padding: 24px; }
.mp-finestra { background: #FFFCFA; border-radius: 18px; width: 100%; max-width: 1400px; height: 100%;
  max-height: 900px; display: flex; flex-direction: column; overflow: hidden;
  box-shadow: 0 10px 40px rgba(0,0,0,.25); }
.mp-testa { display: flex; align-items: center; gap: 12px; padding: 14px 18px; border-bottom: 1px solid #F0E6E0; }
.mp-titolo { font-weight: 700; font-size: 16px; }
.mp-sub { color: #8C7A72; font-size: 12.5px; }
.mp-azioni { margin-left: auto; display: flex; gap: 8px; }
.mp-azioni .ghost { padding: 7px 12px; font-size: 13px; }
.mp-disattiva { color: #C0392B !important; }
.mp-chiudi { border: none; background: none; font-size: 26px; line-height: 1; color: #8C7A72; cursor: pointer; padding: 0 4px; }
.mp-corpo { flex: 1; display: flex; min-height: 0; }
.mp-mappa-box { flex: 1; position: relative; min-width: 0; }
#mp-mappa { position: absolute; inset: 0; }
.mp-lato { width: 340px; flex-shrink: 0; border-left: 1px solid #F0E6E0; overflow-y: auto; padding: 14px; }
.mp-lato:empty { display: none; }
.mp-velo { position: absolute; inset: 0; display: none; align-items: center; justify-content: center;
  background: rgba(255,252,250,.94); z-index: 1000; padding: 20px; }
.mp-velo.visibile { display: flex; }
.mp-velo-box { max-width: 460px; text-align: center; }
.mp-velo-box h3 { margin: 0 0 8px; font-size: 18px; }
.mp-velo-box p { color: #4A3F3A; font-size: 14px; margin: 0 0 8px; }
.mp-velo-azioni { display: flex; gap: 10px; justify-content: center; margin-top: 16px; flex-wrap: wrap; }
.mp-nota { color: #8C7A72; font-size: 12.5px; margin: 6px 0; }
.mp-cerca { position: relative; }
.mp-cerca input { padding: 10px 12px; font-size: 14px; }
.mp-risultati { margin-top: 4px; }
.mp-risultato { padding: 8px 10px; font-size: 13px; border-radius: 8px; cursor: pointer; }
.mp-risultato:hover { background: #FBF1EA; }
.mp-aiuto { font-size: 12.5px; color: #6B564E; background: #FFF6EF; border-radius: 10px; padding: 8px 10px; margin: 10px 0; }
.mp-sezione { font-size: 11.5px; font-weight: 700; color: #D2600F; text-transform: uppercase;
  letter-spacing: .04em; margin: 16px 0 6px; }
.mp-voce { display: flex; gap: 10px; padding: 8px; border-radius: 10px; cursor: pointer; }
.mp-voce:hover { background: #FBF1EA; }
.mp-voce-ico { font-size: 18px; }
.mp-voce-testo { display: flex; flex-direction: column; min-width: 0; font-size: 13.5px; }
.mp-voce-testo span { color: #8C7A72; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mp-vuoto { color: #A9968D; font-size: 12.5px; padding: 4px 8px; }
.mp-in-corso { color: #E2562B; }
.mp-modulo h3 { margin: 0 0 6px; font-size: 16px; }
.mp-modulo label { display: block; font-size: 12.5px; color: #8C7A72; margin: 12px 0 5px; }
.mp-modulo input[type=text], .mp-modulo input[type=datetime-local], .mp-modulo textarea {
  width: 100%; padding: 10px 12px; border-radius: 10px; border: 1.5px solid #F1E3DA; font-size: 14px;
  font-family: inherit; background: #fff; }
.mp-modulo input[type=range] { width: 100%; padding: 0; border: none; background: none; }
.mp-modulo input[type=file] { font-size: 13px; padding: 0; border: none; background: none; }
.mp-fumetto { font-size: 13px; min-width: 200px; }
.mp-fumetto p { margin: 6px 0; white-space: pre-wrap; }
.mp-fumetto-foto img { width: 100%; border-radius: 8px; margin: 6px 0; display: block; }
.mp-fumetto-azioni { display: flex; gap: 10px; align-items: center; margin-top: 8px; }
.mp-fumetto-azioni .ghost { padding: 5px 10px; font-size: 12.5px; }
.mp-link-rosso { border: none; background: none; color: #C0392B; cursor: pointer; font-size: 12.5px; padding: 0; text-decoration: underline; }
.mp-scelta { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
.mp-scelta .ghost { text-align: left; }
.mp-tondo { width: 44px; height: 44px; border-radius: 50%; border: 3px solid #EA5B2E; overflow: hidden;
  background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,.25); }
.mp-tondo img { width: 100%; height: 100%; object-fit: cover; }
.mp-galleria { position: fixed; inset: 0; z-index: 2000; background: rgba(24,18,15,.6);
  display: flex; align-items: center; justify-content: center; padding: 30px; }
.mp-galleria-box { background: #FFFCFA; border-radius: 16px; width: 100%; max-width: 900px; max-height: 100%;
  display: flex; flex-direction: column; overflow: hidden; }
.mp-foto-griglia { padding: 16px; overflow-y: auto; display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.mp-foto { margin: 0; }
.mp-foto img { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 10px; cursor: zoom-in; display: block; }
.mp-foto figcaption { font-size: 12px; color: #4A3F3A; margin-top: 4px; }
.mp-foto figcaption span { color: #A9968D; display: block; }
@media (max-width: 820px) {
  .mp-overlay { padding: 0; }
  .mp-finestra { border-radius: 0; max-height: none; }
  .mp-corpo { flex-direction: column; }
  .mp-lato { width: 100%; max-height: 40%; border-left: none; border-top: 1px solid #F0E6E0; }
}

.modal-backdrop {
  display: none; position: fixed; inset: 0; background: rgba(43,33,29,.45);
  align-items: center; justify-content: center; z-index: 999; padding: 20px;
}
.modal-box { background: #FFFCFA; border-radius: 18px; padding: 26px; max-width: 420px; width: 100%; }
.modal-box h2 { font-size: 17px; color: #C0392B; margin: 0 0 10px; }
.modal-box p { font-size: 13.5px; color: #4A3F3A; margin: 0 0 6px; }
.modal-box ul { font-size: 13px; color: #6B5C54; margin: 8px 0 16px; padding-left: 18px; }
.modal-box label { display: block; font-size: 12.5px; color: #8C7A72; margin: 12px 0 5px; }
.modal-box input { width: 100%; padding: 11px 13px; border-radius: 10px; border: 1.5px solid #F1E3DA; font-size: 14px; }
.modal-box input:focus { outline: none; border-color: #C0392B; }
.modal-actions { display: flex; gap: 10px; margin-top: 18px; }
.modal-actions button { flex: 1; padding: 11px; border-radius: 12px; font-size: 13.5px; font-weight: 600; cursor: pointer; border: none; }
.btn-cancel { background: #F1E9E3; color: #6B5C54; }
.btn-danger { background: #C0392B; color: white; }
.btn-danger:disabled { opacity: .55; cursor: default; }
"""

_MODALS = """
<div class="modal-backdrop" id="delete-modal-backdrop">
  <div class="modal-box">
    <h2>Eliminare definitivamente l'account?</h2>
    <p>Questa azione &egrave; <strong>immediata e irreversibile</strong>. Verranno cancellati per sempre:</p>
    <ul>
      <li>Tutte le chat e i messaggi</li>
      <li>Foto, video e altri media caricati</li>
      <li>Dati di posizione, viaggi e perimetri di sicurezza</li>
      <li>Contatti SOS, community, lavagne e ogni altro dato collegato all'account</li>
    </ul>
    <p class="muted">Se ti serve una copia dei tuoi dati, scaricala <strong>prima</strong>: dopo non sar&agrave; pi&ugrave; possibile.</p>
    <label>Scrivi ELIMINA per confermare</label>
    <input type="text" id="delete-confirm-text" autocomplete="off" placeholder="ELIMINA">
    <label>La tua password</label>
    <input type="password" id="delete-password" autocomplete="current-password">
    <div class="error-box" id="delete-error" style="display:none; margin-top:10px;"></div>
    <div class="modal-actions">
      <button class="btn-cancel" onclick="closeDeleteModal()">Annulla</button>
      <button class="btn-danger" id="delete-confirm-btn" onclick="confirmDeleteAccount()">Elimina definitivamente</button>
    </div>
  </div>
</div>
"""

# ─────────────────────────────────────────────────────────────────────────
# Crittografia lato browser
# ─────────────────────────────────────────────────────────────────────────
#
# Rifa esattamente quello che fanno CryptoManager.kt, KeyManager.kt e
# MediaCrypto.kt sull'app. Se un giorno uno dei due lati cambia formato,
# l'altro smette di leggere: i punti in cui i due devono restare allineati
# sono segnalati nei commenti qui sotto.

_JS_CRYPTO = r"""
const enc = new TextEncoder();
const dec = new TextDecoder();

function b64ToBytes(s) {
  const bin = atob(s.replace(/-/g, '+').replace(/_/g, '/'));
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function bytesToB64(bytes) {
  let bin = '';
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
  }
  return btoa(bin);
}

function toHex(bytes) {
  return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}

function concatBytes(a, b) {
  const out = new Uint8Array(a.length + b.length);
  out.set(a, 0); out.set(b, a.length);
  return out;
}

async function sha256(bytes) {
  return new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
}

// ── X25519 ────────────────────────────────────────────────────────────
// Prima si prova WebCrypto, che nei browser recenti lo supporta in modo
// nativo. Dove non c'e si carica @noble/curves: senza fallback il
// pannello resterebbe inutilizzabile su un browser aggiornato di un anno
// fa, e chi ci arriva sta magari cercando di scaricare i propri dati.
let nobleX25519 = null;

async function ecdh(privBytes, pubBytes) {
  try {
    // La chiave privata grezza va incapsulata in PKCS#8: il prefisso e
    // fisso per X25519 (RFC 8410), cambia solo il corpo di 32 byte.
    const prefix = new Uint8Array([
      0x30, 0x2e, 0x02, 0x01, 0x00, 0x30, 0x05, 0x06, 0x03, 0x2b, 0x65, 0x6e,
      0x04, 0x22, 0x04, 0x20,
    ]);
    const pkcs8 = concatBytes(prefix, privBytes);
    const privKey = await crypto.subtle.importKey('pkcs8', pkcs8, 'X25519', false, ['deriveBits']);
    const pubKey = await crypto.subtle.importKey('raw', pubBytes, 'X25519', false, []);
    return new Uint8Array(await crypto.subtle.deriveBits({ name: 'X25519', public: pubKey }, privKey, 256));
  } catch (e) {
    if (!nobleX25519) {
      // Servita dal nostro dominio, non da una rete di distribuzione
      // esterna. Questo codice gira nella pagina in cui viene digitata la
      // frase di recupero: se qualcuno potesse sostituirlo, si porterebbe
      // via la chiave privata aggirando la cifratura senza toccare il
      // server e senza lasciare traccia. Un file che serviamo noi ha la
      // stessa fiducia del resto della pagina.
      const mod = await import('/static/x25519.js');
      nobleX25519 = mod.x25519;
    }
    return nobleX25519.getSharedSecret(privBytes, pubBytes);
  }
}

// Il segreto ECDH passa per SHA-256 prima di diventare chiave AES: e cosi
// anche in KeyManager.deriveSharedSecret, e i due devono coincidere byte
// per byte o non si legge piu niente.
async function sharedKeyFrom(privBytes, publicKeyB64) {
  return sha256(await ecdh(privBytes, b64ToBytes(publicKeyB64)));
}

// ── AES-256-GCM ───────────────────────────────────────────────────────
// Tink (lato Android) produce [iv][ciphertext][tag] e l'app spedisce iv e
// ciphertext+tag separati, in base64. Qui si rimontano nello stesso modo.

async function aesKey(rawKey, usage) {
  return crypto.subtle.importKey('raw', rawKey, 'AES-GCM', false, [usage]);
}

async function aesDecrypt(rawKey, iv, ciphertext, aad) {
  const params = { name: 'AES-GCM', iv, tagLength: 128 };
  if (aad) params.additionalData = aad;
  return new Uint8Array(await crypto.subtle.decrypt(params, await aesKey(rawKey, 'decrypt'), ciphertext));
}

async function aesEncrypt(rawKey, plaintext) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = new Uint8Array(await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv, tagLength: 128 }, await aesKey(rawKey, 'encrypt'), plaintext,
  ));
  return { iv, ciphertext: ct };
}

// ── Backup della chiave privata ───────────────────────────────────────
// PBKDF2-HMAC-SHA256, 210.000 iterazioni: identico a KeyManager.kt. Un
// numero diverso qui produrrebbe una chiave diversa e un "passphrase
// errata" impossibile da diagnosticare.
const PBKDF2_ITERATIONS = 210000;

async function keyFromPassphrase(passphrase, salt) {
  const material = await crypto.subtle.importKey(
    'raw', enc.encode(passphrase), 'PBKDF2', false, ['deriveBits'],
  );
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' }, material, 256,
  );
  return new Uint8Array(bits);
}

// ── Media cifrati — formato CEMD ──────────────────────────────────────
// "CEMD" | versione(1) | keyId(4) | salt(16) | iv(12) | ciphertext+tag
// Vedi MediaCrypto.kt: header come AAD, chiave del file derivata con HKDF.
const MEDIA_HEADER_SIZE = 37;

async function mediaKeyId(rawKey) {
  const digest = await sha256(concatBytes(enc.encode('central-media-key-id'), rawKey));
  return toHex(digest.slice(0, 4));
}

async function deriveFileKey(baseKey, salt) {
  const material = await crypto.subtle.importKey('raw', baseKey, 'HKDF', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'HKDF', hash: 'SHA-256', salt, info: enc.encode('central-media-v1') }, material, 256,
  );
  return new Uint8Array(bits);
}

function isEncryptedMediaUrl(url) {
  return !!url && url.indexOf('/enc/') !== -1;
}

/** Scarica un media e, se e cifrato, lo apre. Ritorna un URL usabile in un tag. */
async function resolveMedia(url, explicitKeyB64) {
  if (!url) return null;
  if (!isEncryptedMediaUrl(url)) return url;          // pubblico o precedente alla cifratura
  if (mediaCache.has(url)) return mediaCache.get(url);

  // Prima si prova la strada diretta: costa zero al nostro server ed e la
  // piu veloce. Se il browser la blocca — lo spazio di archiviazione sta su
  // un altro dominio e puo rifiutare le richieste che arrivano da qui — si
  // passa dal rele. Era questo il motivo per cui nel pannello arrivava solo
  // il testo: la richiesta falliva in silenzio e la bolla restava ferma su
  // "Caricamento".
  let buf = null;
  try {
    const res = await fetch(url);
    if (res.ok) buf = new Uint8Array(await res.arrayBuffer());
  } catch (e) { /* bloccata dal browser: si prova il rele */ }

  if (!buf) {
    try {
      const res = await apiRaw('/api/media/proxy?url=' + encodeURIComponent(url));
      if (!res.ok) return null;
      buf = new Uint8Array(await res.arrayBuffer());
    } catch (e) {
      return null;
    }
  }

  if (buf.length < MEDIA_HEADER_SIZE) return null;

  const header = buf.slice(0, MEDIA_HEADER_SIZE);
  if (String.fromCharCode(header[0], header[1], header[2], header[3]) !== 'CEMD') {
    // Sta sotto enc/ ma non e nel nostro formato: lo si serve com'e
    // invece di buttarlo via.
    const raw = URL.createObjectURL(new Blob([buf]));
    mediaCache.set(url, raw);
    return raw;
  }

  const keyIdHex = toHex(header.slice(5, 9));
  const salt = header.slice(9, 25);
  const iv = header.slice(25, 37);
  const baseKey = explicitKeyB64 ? b64ToBytes(explicitKeyB64) : state.mediaKeys.get(keyIdHex);
  if (!baseKey) return null;

  try {
    const fileKey = await deriveFileKey(baseKey, salt);
    const plain = await aesDecrypt(fileKey, iv, buf.slice(MEDIA_HEADER_SIZE), header);
    const objectUrl = URL.createObjectURL(new Blob([plain]));
    mediaCache.set(url, objectUrl);
    return objectUrl;
  } catch (e) {
    return null;
  }
}

/** Ogni chiave di conversazione calcolata serve anche ad aprire i suoi media. */
async function registerMediaKey(rawKey) {
  if (!rawKey) return;
  state.mediaKeys.set(await mediaKeyId(rawKey), rawKey);
}

function hexToBytes(hex) {
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = parseInt(hex.substr(i * 2, 2), 16);
  return out;
}

/**
 * Cifra un file nel formato CEMD, identico a MediaCrypto.encryptStream.
 *
 * Deve coincidere byte per byte con l'app: un file mandato dal computer
 * viene aperto dal telefono di chi lo riceve, e qualunque differenza
 * (ordine dei campi, info dell'HKDF, header non passato come AAD) lo
 * renderebbe illeggibile senza nessun errore utile da mostrare.
 *
 *   "CEMD" | versione 1 | keyId(4) | salt(16) | iv(12) | ciphertext+tag
 *
 * WebCrypto accoda il tag GCM al ciphertext come fa Java: il risultato si
 * concatena all'header cosi com'e.
 */
async function cifraMedia(baseKey, plain) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));

  const header = new Uint8Array(MEDIA_HEADER_SIZE);
  header.set([0x43, 0x45, 0x4D, 0x44], 0);   // "CEMD"
  header[4] = 1;                              // versione
  header.set(hexToBytes(await mediaKeyId(baseKey)), 5);
  header.set(salt, 9);
  header.set(iv, 25);

  const fileKey = await deriveFileKey(baseKey, salt);
  const ct = new Uint8Array(await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv, tagLength: 128, additionalData: header },
    await aesKey(fileKey, 'encrypt'),
    plain,
  ));
  return concatBytes(header, ct);
}
"""

# ─────────────────────────────────────────────────────────────────────────
# Applicazione
# ─────────────────────────────────────────────────────────────────────────

_JS_APP = r"""
const $ = (sel, root = document) => root.querySelector(sel);

const state = {
  token: sessionStorage.getItem('central_token') || null,
  me: null,
  // Chiave privata X25519. Solo in memoria: chiudendo la scheda sparisce,
  // e chi si siede dopo davanti allo stesso computer non la ritrova.
  priv: null,
  chats: [],
  activeChatId: null,
  chatKeys: new Map(),    // chatId -> Map(version -> Uint8Array)
  mediaKeys: new Map(),   // keyId esadecimale -> Uint8Array
  tab: 'panoramica',
  // Elenco delle persone seguite, non l'oggetto intero della risposta: lo
  // leggono il guscio (per il numero sugli avvisi), la panoramica, la
  // mappa e le sezioni check-in e perimetri.
  overview: null,
  // La scheda Moderazione compare solo a chi e moderatore. Non e una
  // misura di sicurezza — quella sta sul server, che risponde 404 a
  // chiunque altro — ma non ha senso mostrare a tutti una scheda che per
  // loro sarebbe vuota.
  isModerator: false,
};
const mediaCache = new Map();
let refreshTimer = null;
let chatTimer = null;
let sosSeen = new Map();
let sosBaselineReady = false;
// Ultimo messaggio gia visto per conversazione: serve a distinguere un
// messaggio nuovo da un semplice ricaricamento della stessa lista.
let lastSeenMessageId = new Map();
// Eventi della cronologia gia notificati, per non riproporre lo stesso
// avviso a ogni giro di aggiornamento.
let timelineSeen = new Set();
let timelineBaselineReady = false;
// Chiavi degli avvisi archiviati da questo controllore, come le rimanda il
// server: senza, ricaricando la pagina tornerebbero tutti in cima.
let archiviati = new Set();
// Selezione corrente nella scheda Avvisi. Vive solo finche la scheda e
// aperta: una selezione che sopravvive a un cambio di sezione porta ad
// archiviare cose che non si stavano piu guardando.
let avvisiSelezionati = new Set();
let mostraArchiviati = false;

// ── Rete ──────────────────────────────────────────────────────────────
async function api(path, options = {}) {
  const opts = Object.assign({}, options);
  opts.headers = Object.assign({ 'Authorization': 'Bearer ' + state.token }, options.headers || {});
  if (opts.body && !opts.headers['Content-Type']) opts.headers['Content-Type'] = 'application/json';
  const res = await fetch(path, opts);
  if (res.status === 401) { logout(); throw new Error('Sessione scaduta'); }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    // "Errore 500" da solo non dice a chi guarda ne cosa e successo ne
    // quale chiamata sia fallita: con dieci sezioni che pescano da
    // endpoint diversi, e la differenza fra sapere dove guardare e
    // provare a caso. Il percorso finisce nel messaggio, il corpo
    // completo nella console.
    console.error('Chiamata fallita', path, res.status, body);
    const dettaglio = body.detail || body.message || '';
    throw new Error(
      dettaglio
        ? dettaglio + ' (' + res.status + ' su ' + path + ')'
        : 'Errore ' + res.status + ' su ' + path
    );
  }
  return res.status === 204 ? null : res.json();
}

/**
 * Come api(), ma restituisce la risposta grezza invece del JSON.
 *
 * Serve ai media: sono byte cifrati, non un oggetto da interpretare, e
 * passarli da res.json() li distruggerebbe.
 */
async function apiRaw(path, options = {}) {
  const opts = Object.assign({}, options);
  opts.headers = Object.assign({ 'Authorization': 'Bearer ' + state.token }, options.headers || {});
  const res = await fetch(path, opts);
  if (res.status === 401) { logout(); throw new Error('Sessione scaduta'); }
  return res;
}

function escapeHtml(s) {
  const d = document.createElement('div'); d.textContent = s === null || s === undefined ? '' : s;
  return d.innerHTML;
}

/**
 * Data e ora di un avviso, con la data scritta a parole quando e recente.
 *
 * L'elenco mostrava solo l'ora: con allarmi sparsi su settimane diverse
 * "12:10" e "23:45" sembravano dello stesso giorno, e l'elenco diventava
 * illeggibile proprio dove serviva capire cosa fosse ancora attuale.
 *
 * "Oggi" e "Ieri" invece della data servono a distinguere in un colpo
 * d'occhio cio che richiede attenzione adesso da cio che e storia: e la
 * domanda che ci si pone guardando questa schermata.
 */
function fmtQuando(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const ora = d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' });
  const oggi = new Date();
  const ieri = new Date(); ieri.setDate(oggi.getDate() - 1);
  const stessoGiorno = (a, b) => a.toDateString() === b.toDateString();

  if (stessoGiorno(d, oggi)) return 'Oggi ' + ora;
  if (stessoGiorno(d, ieri)) return 'Ieri ' + ora;

  // Oltre l'anno solare corrente si aggiunge l'anno: senza, un allarme di
  // dicembre scorso e uno di dicembre prossimo sarebbero indistinguibili.
  const opzioni = { day: '2-digit', month: 'short' };
  if (d.getFullYear() !== oggi.getFullYear()) opzioni.year = 'numeric';
  return d.toLocaleDateString('it-IT', opzioni) + ' \u00b7 ' + ora;
}

function fmtDayLabel(iso) {
  const d = new Date(iso);
  const oggi = new Date();
  const ieri = new Date(); ieri.setDate(oggi.getDate() - 1);
  const same = (a, b) => a.toDateString() === b.toDateString();
  if (same(d, oggi)) return 'Oggi';
  if (same(d, ieri)) return 'Ieri';
  return d.toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long' });
}

function initials(name) {
  return (name || '?').trim().split(/\s+/).slice(0, 2).map(w => (w[0] || '').toUpperCase()).join('');
}

function fmtTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' });
}

function fmtDateTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString('it-IT', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
}

// ── Login e sblocco della cifratura ───────────────────────────────────
function renderLogin(errorMsg, infoMsg) {
  document.title = 'Central — Area personale';
  $('#app').innerHTML = `
    <div class="card" style="margin-top:56px;">
      <h1>Area personale Central</h1>
      <div class="sub">Le tue chat, gli allarmi che ricevi e i tuoi dati personali.</div>
      <form id="login-form">
        <label>Email</label>
        <input type="email" id="email" required autocomplete="username">
        <label>Password</label>
        <input type="password" id="password" required autocomplete="current-password">
        ${infoMsg ? `<div class="info-box">${escapeHtml(infoMsg)}</div>` : ''}
        ${errorMsg ? `<div class="error-box">${escapeHtml(errorMsg)}</div>` : ''}
        <button class="primary" type="submit" id="login-btn">Accedi</button>
      </form>
    </div>`;
  $('#login-form').addEventListener('submit', onLogin);
}

async function onLogin(e) {
  e.preventDefault();
  const btn = $('#login-btn');
  btn.disabled = true; btn.textContent = 'Accesso in corso…';
  try {
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: $('#email').value.trim(), password: $('#password').value }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      // detail puo' essere una frase o {code, message} (troppi tentativi,
      // email da confermare): senza questo si leggeva "[object Object]".
      const d = body.detail;
      throw new Error((typeof d === 'string' ? d : d && d.message) || 'Credenziali non valide');
    }
    const data = await res.json();
    state.token = data.access_token;
    sessionStorage.setItem('central_token', state.token);
    requestNotificationPermission();
    await boot();
  } catch (err) {
    renderLogin(err.message || 'Errore di accesso. Riprova.');
  }
}

function logout() {
  sessionStorage.removeItem('central_token');
  state.token = null; state.priv = null; state.me = null;
  state.chatKeys.clear(); state.mediaKeys.clear(); mediaCache.clear();
  if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null; }
  if (chatTimer) { clearInterval(chatTimer); chatTimer = null; }
  fermaSorveglianzaChat();
  allegatiInAttesa = [];
  state.chats = []; state.activeChatId = null;
  renderLogin(null);
}

/**
 * Apre la chiave privata E2E a partire dal backup cifrato sul server.
 * La passphrase resta in questa funzione: non viene salvata da nessuna
 * parte, e per rileggere le chat dopo un ricaricamento va reinserita.
 */
async function unlockE2E(passphrase) {
  const backup = await api('/users/me/key-backup');
  if (!backup || !backup.key_backup_blob) {
    throw new Error('Nessun backup della chiave trovato. Apri l\'app Central e imposta la passphrase di recupero, poi torna qui.');
  }
  const salt = b64ToBytes(backup.key_backup_salt);
  const iv = b64ToBytes(backup.key_backup_iv);
  const blob = b64ToBytes(backup.key_backup_blob);
  const aes = await keyFromPassphrase(passphrase, salt);
  let priv;
  try {
    priv = await aesDecrypt(aes, iv, blob);
  } catch (e) {
    throw new Error('Passphrase errata.');
  }
  state.priv = priv;
}

// ── Chiavi di conversazione ───────────────────────────────────────────
//
// 1:1  → ECDH con la chiave pubblica dell'altro.
// gruppo → buste da /groups/{id}/keys, ognuna cifrata con l'ECDH fra noi
//          e chi ha creato quella versione. Si tengono tutte le versioni:
//          i messaggi precedenti a una rotazione restano chiusi con la
//          chiave di allora.
async function chatKeys(chat) {
  if (state.chatKeys.has(chat.id)) return state.chatKeys.get(chat.id);
  const versions = new Map();

  if (chat.type === 'group') {
    const envelopes = await api('/groups/' + chat.id + '/keys?since_version=0');
    for (const env of envelopes) {
      if (!env.encrypted_by_public_key) continue;
      try {
        const wrapKey = await sharedKeyFrom(state.priv, env.encrypted_by_public_key);
        const groupKey = await aesDecrypt(wrapKey, b64ToBytes(env.iv), b64ToBytes(env.encrypted_key));
        versions.set(env.key_version, groupKey);
        await registerMediaKey(groupKey);
      } catch (e) { /* busta non apribile: le altre versioni restano valide */ }
    }
  } else if (chat.other_user && chat.other_user.public_key) {
    const key = await sharedKeyFrom(state.priv, chat.other_user.public_key);
    versions.set(0, key);
    await registerMediaKey(key);
  }

  state.chatKeys.set(chat.id, versions);
  return versions;
}

function pickKey(versions, keyVersion) {
  if (!versions || versions.size === 0) return null;
  if (keyVersion && versions.has(keyVersion)) return versions.get(keyVersion);
  if (versions.has(0)) return versions.get(0);
  // Gruppo con la versione del messaggio mancante: si tenta con la piu
  // alta che abbiamo, meglio di un rifiuto secco.
  return versions.get(Math.max(...versions.keys()));
}

async function decryptText(versions, msg) {
  if (msg.type === 'call' || msg.type === 'system') return msg.content;
  if (!msg.content || !msg.iv) return msg.content;
  const key = pickKey(versions, msg.key_version);
  if (!key) return null;
  try {
    return dec.decode(await aesDecrypt(key, b64ToBytes(msg.iv), b64ToBytes(msg.content)));
  } catch (e) {
    return null;
  }
}
"""

_JS_UI = r"""
// ── Struttura generale ────────────────────────────────────────────────
//
// Barra laterale invece delle schede in cima. Con dieci sezioni le schede
// diventavano una fila illeggibile; e su uno schermo largo — che e il posto
// dove questo pannello viene usato davvero, non su un telefono — la colonna
// a sinistra usa spazio che c'e gia e non toglie nulla al contenuto.

const SEZIONI = [
  { id: 'panoramica', ico: '\u25EB', nome: 'Panoramica',   titolo: 'Panoramica',            sub: 'Tutto quello che serve, in tempo reale' },
  { id: 'chat',       ico: '\u2709', nome: 'Chat',         titolo: 'Chat',                  sub: 'Le tue conversazioni, decifrate qui nel browser' },
  { id: 'community',  ico: '\u2766', nome: 'Community',    titolo: 'Community',             sub: 'Bacheche, eventi e gestione delle tue community' },
  { id: 'persone',    ico: '\u25CB', nome: 'Persone',      titolo: 'Persone',               sub: 'Chi segui e come sta adesso' },
  { id: 'avvisi',     ico: '\u26A0', nome: 'Avvisi',       titolo: 'Avvisi',                sub: 'Segnalazioni che richiedono attenzione' },
  { id: 'storia',     ico: '\u21BB', nome: 'Storia eventi',titolo: 'Storia eventi',         sub: 'Cronologia con filtri, stampa ed esportazione' },
  { id: 'checkin',    ico: '\u2713', nome: 'Check-in',     titolo: 'Check-in',              sub: 'Conferme di oggi e scadenze in arrivo' },
  { id: 'geofence',   ico: '\u2299', nome: 'Perimetri',    titolo: 'Perimetri di sicurezza',sub: 'Aree concordate e ultimi passaggi' },
  { id: 'devices',    ico: '\u25AF', nome: 'Dispositivi',  titolo: 'Dispositivi',           sub: 'Sessioni attive e disconnessione d\'emergenza' },
  { id: 'privacy',    ico: '\u2913', nome: 'Esporta dati', titolo: 'Privacy e dati',        sub: 'Esporta o elimina il tuo account' },
  { id: 'settings',   ico: '\u2699', nome: 'Impostazioni', titolo: 'Impostazioni',          sub: 'Notifiche, cifratura e documenti' },
  // Riservate a chi modera: stanno qui dentro per avere titolo e
  // sottotitolo in testata come tutte le altre, ma vengono escluse
  // dall'elenco della barra laterale e disegnate a parte piu sotto.
  { id: 'moderation',    ico: '\u2691', nome: 'Moderazione', titolo: 'Moderazione', sub: 'Segnalazioni da esaminare e verifiche di consenso' },
  { id: 'announcements', ico: '\u2605', nome: 'Annunci',     titolo: 'Annunci',     sub: 'Messaggi mostrati a tutti all\'apertura dell\'app' },
  { id: 'gifts',         ico: '\u2665', nome: 'Regala abbonamento', titolo: 'Regala abbonamento', sub: 'Mesi di Plus o Premium in regalo, che si sommano ai giorni già regalati' },
  { id: 'visite',        ico: '\u2197', nome: 'Visite sito', titolo: 'Visite al sito', sub: 'Visitatori, pagine viste e provenienza di getcentral.net' },
  { id: 'aziende',       ico: '\u25A3', nome: 'Aziende', titolo: 'Aziende', sub: 'Piano Base o Completo per controllori e operatori di un\'azienda cliente, email ai referenti' },
];

function sezioneCorrente() {
  return SEZIONI.find(x => x.id === state.tab) || SEZIONI[0];
}

/**
 * Numero rosso accanto a "Avvisi" nella barra laterale.
 *
 * Sta li e non solo dentro la panoramica perche resta visibile da
 * qualunque sezione: chi sta guardando la cronologia deve accorgersi che e
 * appena arrivato un SOS senza dover tornare indietro a controllare.
 */
function contaAvvisi() {
  // Conta solo quelli non archiviati, cosi il numero rosso si azzera
  // quando si e finito di occuparsene. Prima contava tutto e restava li
  // per sempre: un numero che non cambia mai smette di essere letto, e a
  // quel punto tanto vale non averlo.
  return raccogliAvvisi(state.overview || [], false).length;
}

function renderShell(inner) {
  const sez = sezioneCorrente();
  const avvisi = contaAvvisi();
  const me = state.me;
  const avatar = me && me.avatar_url
    ? `<img class="su-avatar" src="${escapeHtml(me.avatar_url)}" alt="">`
    : `<span class="su-avatar">${escapeHtml(initials(me ? me.name : '?'))}</span>`;

  $('#app').innerHTML = `
    <div class="shell">
      <aside class="sidebar">
        <div class="sidebar-brand">
          <span class="brand-mark">C</span> Central Guardian
        </div>
        <nav class="sidebar-nav">
          ${SEZIONI.filter(x => x.id !== 'moderation' && x.id !== 'announcements' && x.id !== 'gifts' && x.id !== 'aziende' && x.id !== 'visite').map(x => `
            <button class="nav-item ${state.tab === x.id ? 'active' : ''}"
                    onclick="switchTab('${x.id}')">
              <span class="nav-ico">${x.ico}</span><span>${escapeHtml(x.nome)}</span>
              ${x.id === 'avvisi' && avvisi ? `<span class="nav-badge">${avvisi}</span>` : ''}
              ${x.id === 'chat' ? `<span class="nav-badge" id="badge-chat" style="${totaleNonLetti() ? '' : 'display:none'}">${totaleNonLetti() > 99 ? '99+' : totaleNonLetti()}</span>` : ''}
            </button>`).join('')}
          ${state.isModerator ? `
            <button class="nav-item ${state.tab === 'moderation' ? 'active' : ''}"
                    onclick="switchTab('moderation')">
              <span class="nav-ico">\u2691</span><span>Moderazione</span>
            </button>
            <button class="nav-item ${state.tab === 'announcements' ? 'active' : ''}"
                    onclick="switchTab('announcements')">
              <span class="nav-ico">\u2605</span><span>Annunci</span>
            </button>
            <button class="nav-item ${state.tab === 'gifts' ? 'active' : ''}"
                    onclick="switchTab('gifts')">
              <span class="nav-ico">\u2665</span><span>Regala abbonamento</span>
            </button>
            <button class="nav-item ${state.tab === 'aziende' ? 'active' : ''}"
                    onclick="switchTab('aziende')">
              <span class="nav-ico">\u25A3</span><span>Aziende</span>
            </button>
            <button class="nav-item ${state.tab === 'visite' ? 'active' : ''}"
                    onclick="switchTab('visite')">
              <span class="nav-ico">\u2197</span><span>Visite sito</span>
            </button>` : ''}
        </nav>
        <div class="sidebar-user">
          ${avatar}
          <div>
            <div class="su-name">${escapeHtml(me ? me.name : '')}</div>
            <div class="su-role">Referente</div>
          </div>
          <button class="su-exit" onclick="logout()" title="Esci">\u23FB</button>
        </div>
      </aside>

      <main class="main">
        <header class="main-head">
          <div>
            <h1 class="main-title">${escapeHtml(sez.titolo)}</h1>
            <div class="main-sub">${escapeHtml(sez.sub)}</div>
          </div>
          <div class="main-actions">
            ${('Notification' in window && Notification.permission !== 'granted')
              ? `<button class="dev-btn" onclick="requestNotificationPermission()">Attiva notifiche</button>`
              : ''}
          </div>
        </header>
        <div class="main-body" id="tab-body">${inner}</div>
      </main>
    </div>`;
}

function switchTab(tab) {
  state.tab = tab;
  if (chatTimer) { clearInterval(chatTimer); chatTimer = null; }
  // La mappa va smontata a mano: Leaflet tiene agganciati listener sulla
  // finestra, e lasciarne una per ogni cambio di sezione riempirebbe la
  // memoria in una pagina che resta aperta tutto il giorno.
  resetLiveMap();

  switch (tab) {
    case 'panoramica': renderPanoramica(); break;
    case 'chat':       renderChatTab(); break;
    case 'community':  renderCommunityTab(); break;
    case 'persone':    renderGuardianTab(); break;
    case 'avvisi':     renderAvvisiTab(); break;
    case 'storia':     renderStoriaTab(); break;
    case 'checkin':    renderCheckinTab(); break;
    case 'geofence':   renderGeofenceTab(); break;
    case 'devices':    renderDevicesTab(); break;
    case 'moderation': renderModerationTab(); break;
    case 'announcements': renderAnnouncementsTab(); break;
    case 'gifts':      renderGiftsTab(); break;
    case 'aziende':    renderAziendeTab(); break;
    case 'visite':     renderVisiteTab(); break;
    case 'settings':   renderSettingsTab(); break;
    default:           renderPrivacyTab();
  }
}

// ── Tab: chat ─────────────────────────────────────────────────────────
function renderChatTab() {
  // Solo la chat richiede lo sblocco: le altre sezioni mostrano stati e
  // orari, che il server conosce gia e non sono cifrati. Chiedere la frase
  // di recupero per vedere quanti check-in mancano sarebbe un ostacolo
  // senza motivo.
  if (!state.priv) { renderUnlock(); return; }
  renderShell('<div class="card"><div class="empty">Carico le conversazioni…</div></div>');
  loadChats();
}

function renderUnlock(errorMsg) {
  renderShell(`
    <div class="card">
      <h2>Sblocca le tue conversazioni</h2>
      <p class="sub">I messaggi sono cifrati end-to-end: nemmeno il server pu&ograve; leggerli.
      Per aprirli qui serve la passphrase di recupero che hai scelto nell'app.</p>
      <form id="unlock-form">
        <label>Passphrase di recupero</label>
        <input type="password" id="passphrase" autocomplete="off" autofocus>
        ${errorMsg ? `<div class="error-box">${escapeHtml(errorMsg)}</div>` : ''}
        <button class="primary" type="submit" id="unlock-btn">Sblocca</button>
      </form>
      <div class="warn-box">La passphrase non viene salvata: resta in questa scheda finch&eacute; &egrave; aperta.
      Se ricarichi la pagina te la richiediamo. Su un computer non tuo, chiudi la scheda quando hai finito.</div>
    </div>`);
  $('#unlock-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = $('#unlock-btn');
    btn.disabled = true; btn.textContent = 'Sblocco…';
    try {
      await unlockE2E($('#passphrase').value);
      renderChatTab();
    } catch (err) {
      renderUnlock(err.message);
    }
  });
}

/**
 * Ultimo messaggio gia segnalato per ogni chat, per non ripetere lo stesso
 * avviso a ogni giro di ricarico.
 */
const ultimoSegnalato = new Map();

/** True finche non si e finito il primo controllo delle chat. */
let primaListaChat = true;

/** Ricarico periodico dell'elenco chat, attivo su TUTTE le sezioni. */
let sorveglianzaChat = null;
const INTERVALLO_SORVEGLIANZA_MS = 10000;

/**
 * Avvisa il browser dei messaggi nuovi, come WhatsApp Web.
 *
 * PERCHE' GIRA SU TUTTE LE SEZIONI
 *
 * Prima l'avviso partiva solo dalla conversazione aperta, e solo stando
 * nella sezione Chat: l'elenco delle conversazioni non veniva mai
 * ricaricato, quindi un messaggio in un'altra chat — o mentre si guardava
 * la Panoramica — non produceva niente. Ora l'elenco si rilegge ogni dieci
 * secondi da qualunque sezione, e ogni conversazione ha il suo avviso.
 *
 * QUANDO NON AVVISA
 *
 * - al primo controllo dopo l'accesso: ci sono gia venti conversazioni con
 *   il loro ultimo messaggio, e venti avvisi per messaggi vecchi di giorni
 *   sarebbero solo rumore;
 * - per i propri messaggi (anche quelli scritti dal telefono);
 * - per la conversazione che si sta guardando, con la scheda in primo
 *   piano: il messaggio si vede gia.
 *
 * Il permesso non si chiede da soli: la richiesta aperta senza un gesto e
 * quella che quasi tutti negano d'istinto, e una volta negata il browser
 * non la ripropone piu. Si usa solo un permesso gia concesso; per
 * concederlo ci sono i pulsanti "Attiva notifiche".
 */
function avvisaMessaggiNuovi(chats) {
  const permesso = ('Notification' in window) && Notification.permission === 'granted';
  let suonare = false;

  for (const c of chats) {
    const ultimo = c.last_message;
    if (!ultimo) continue;

    const gia = ultimoSegnalato.get(c.id);
    ultimoSegnalato.set(c.id, ultimo.id);

    if (primaListaChat || gia === ultimo.id) continue;
    if (state.me && ultimo.sender_id === state.me.id) continue;

    const staGuardando = document.visibilityState === 'visible'
      && state.tab === 'chat' && c.id === state.activeChatId;
    if (staGuardando) continue;

    suonare = true;
    if (!permesso) continue;

    // Il testo NON finisce nella notifica: e cifrato, e decifrarlo qui
    // significherebbe mostrarlo in una finestra di sistema che resta a
    // schermo anche quando ti alzi dal computer. Il nome della chat e il
    // tipo di messaggio bastano a decidere se tornare al pannello.
    //
    // Il tag e per conversazione: dieci messaggi dalla stessa persona
    // sostituiscono la stessa notifica invece di impilarne dieci.
    const nonLetti = c.unread_count > 1 ? ` (${c.unread_count} non letti)` : '';
    const avviso = new Notification(chatTitle(c), {
      body: anteprimaDi(ultimo) + nonLetti,
      tag: 'central-chat-' + c.id,
      renotify: true,
      icon: document.querySelector('link[rel=icon]')?.href,
    });
    avviso.onclick = () => {
      window.focus();
      apriChatDaNotifica(c.id);
      avviso.close();
    };
  }

  // Suono solo se la pagina non e davanti agli occhi o si e in un'altra
  // conversazione: con il pannello in primo piano il messaggio si vede.
  if (suonare) suonoMessaggio();
  primaListaChat = false;
}

/** Porta alla conversazione toccata nella notifica, anche se bloccata. */
function apriChatDaNotifica(chatId) {
  state.activeChatId = chatId;
  if (state.tab === 'chat' && state.priv) {
    openChat(chatId);
  } else {
    // renderChatTab chiede la frase di recupero se serve, poi loadChats
    // apre la conversazione gia scelta in activeChatId.
    switchTab('chat');
  }
}

/**
 * Due note brevi e basse, generate al volo: nessun file audio da servire.
 * Diverse dal suono dell'SOS (una nota sola, piu acuta e piu forte), cosi
 * un messaggio non si confonde mai con un allarme.
 */
function suonoMessaggio() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    [[660, 0], [880, 0.12]].forEach(([freq, quando]) => {
      const osc = ctx.createOscillator(); const gain = ctx.createGain();
      osc.connect(gain); gain.connect(ctx.destination);
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.06, ctx.currentTime + quando);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + quando + 0.18);
      osc.start(ctx.currentTime + quando);
      osc.stop(ctx.currentTime + quando + 0.2);
    });
  } catch (e) { /* audio non disponibile o bloccato: l'avviso visivo basta */ }
}

/** Totale dei non letti, per il titolo della scheda e la barra laterale. */
function totaleNonLetti() {
  return (state.chats || []).reduce((n, c) => n + (c.unread_count || 0), 0);
}

/**
 * Titolo della scheda con i non letti, come "(3) Central": e l'unica cosa
 * che si vede di un pannello lasciato aperto dietro altre finestre. Il
 * titolo dell'SOS ha la precedenza e non viene sovrascritto.
 */
function aggiornaIndicatoriNonLetti() {
  const n = totaleNonLetti();
  if (!document.title.startsWith('\u{1F198}')) {
    document.title = (n ? `(${n}) ` : '') + 'Central \u2014 Area personale';
  }
  const badge = document.getElementById('badge-chat');
  if (badge) {
    badge.textContent = n > 99 ? '99+' : String(n);
    badge.style.display = n ? '' : 'none';
  }
}

/** Rilegge l'elenco chat: avvisi, contatori e, se aperta, la colonna a sinistra. */
async function controllaChat() {
  if (!state.token) return;
  try {
    const chats = await api('/chats/');
    state.chats = chats;
    avvisaMessaggiNuovi(chats);
    aggiornaIndicatoriNonLetti();
    if (state.tab === 'chat') aggiornaElencoChat();
  } catch (e) { /* rete assente: si riprova al giro dopo */ }
}

function avviaSorveglianzaChat() {
  if (sorveglianzaChat) return;
  controllaChat();
  // Con la scheda in secondo piano da diversi minuti Chrome e gli altri
  // browser rallentano i timer fino a una volta al minuto: l'avviso puo
  // arrivare con quel ritardo. E' un limite del browser, non del server.
  sorveglianzaChat = setInterval(controllaChat, INTERVALLO_SORVEGLIANZA_MS);
}

function fermaSorveglianzaChat() {
  if (sorveglianzaChat) { clearInterval(sorveglianzaChat); sorveglianzaChat = null; }
  ultimoSegnalato.clear();
  primaListaChat = true;
}

/**
 * Segna letta la conversazione aperta, anche sul server.
 *
 * Cosi il contatore torna a zero anche sul telefono: leggere dal computer
 * e leggere, e ritrovarsi sull'app gli stessi messaggi segnati come nuovi
 * obbligherebbe a riaprirli per niente.
 */
async function segnaLetta(chatId) {
  if (!chatId || document.visibilityState !== 'visible') return;
  const chat = (state.chats || []).find(c => c.id === chatId);
  if (chat && !chat.unread_count) return;
  try {
    await api('/chats/' + chatId + '/read', { method: 'POST' });
    if (chat) chat.unread_count = 0;
    aggiornaIndicatoriNonLetti();
    if (state.tab === 'chat') aggiornaElencoChat();
  } catch (e) { /* non blocca la lettura */ }
}

// Tornando sulla scheda si segna letta la conversazione che era aperta.
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && state.tab === 'chat' && state.activeChatId) {
    segnaLetta(state.activeChatId);
  }
});

async function chiediPermessoNotifiche() {
  if (!('Notification' in window)) return;
  await Notification.requestPermission();
  renderChatLayout();
}

async function loadChats() {
  try {
    state.chats = await api('/chats/');
    avvisaMessaggiNuovi(state.chats);
    aggiornaIndicatoriNonLetti();
    renderChatLayout();
    // Se si arriva da una notifica, activeChatId e gia la conversazione
    // toccata: si apre quella, non la prima dell'elenco.
    const scelta = state.chats.find(c => c.id === state.activeChatId);
    if (scelta) openChat(scelta.id);
    else if (state.chats.length) openChat(state.chats[0].id);
  } catch (err) {
    renderShell(`<div class="card"><div class="error-box">${escapeHtml(err.message)}</div></div>`);
  }
}

/**
 * Immagine della conversazione, con le iniziali come ripiego.
 *
 * Il CSS per l'immagine dentro il cerchio esisteva gia (.avatar img), ma
 * nessuno la passava: l'elenco disegnava sempre e solo le iniziali, anche
 * quando l'avatar_url arrivava insieme al resto della chat. Con venti
 * conversazioni due lettere su fondo pesca si somigliano tutte, e
 * riconoscere una persona diventa un esercizio di lettura invece che un
 * colpo d'occhio.
 *
 * onerror rimette le iniziali se l'immagine non si carica: senza, un file
 * cancellato dal server lascerebbe un cerchio vuoto, che e peggio delle
 * iniziali.
 */
function chatAvatar(chat) {
  const url = chat.type === 'group'
    ? chat.avatar_url
    : (chat.other_user && chat.other_user.avatar_url) || chat.avatar_url;
  const iniziali = escapeHtml(initials(chatTitle(chat)));
  if (!url) return iniziali;
  return `<img src="${escapeHtml(url)}" alt="" onerror="this.replaceWith('${iniziali}')">`;
}

function chatTitle(chat) {
  if (chat.type === 'group') return chat.name || 'Gruppo';
  return chat.other_user ? chat.other_user.name : 'Conversazione';
}

/**
 * Riga per concedere il permesso alle notifiche del browser.
 *
 * Compare solo se il permesso non e ne concesso ne negato: una volta
 * negato il browser non lo richiede piu, e lasciare un pulsante che non
 * puo funzionare sarebbe solo una promessa mancata.
 */
function bannerPermessoNotifiche() {
  if (!('Notification' in window) || Notification.permission !== 'default') return '';
  return `<div class="perm-riga">
            Vuoi un avviso del browser quando arriva un messaggio?
            <button class="ghost" onclick="chiediPermessoNotifiche()">Attiva</button>
          </div>`;
}

function htmlElencoChat() {
  return state.chats.map(c => `
    <div class="chat-item ${c.id === state.activeChatId ? 'active' : ''} ${c.unread_count ? 'non-letta' : ''}" onclick="openChat('${c.id}')">
      <div class="avatar">${chatAvatar(c)}</div>
      <div class="chat-testo">
        <div class="chat-title">${escapeHtml(chatTitle(c))}</div>
        <div class="chat-preview">${c.last_message ? fmtTime(c.last_message.timestamp) : ''}</div>
      </div>
      ${c.unread_count ? `<span class="chat-nonletti">${c.unread_count > 99 ? '99+' : c.unread_count}</span>` : ''}
    </div>`).join('');
}

/**
 * Aggiorna SOLO la colonna delle conversazioni.
 *
 * Ridisegnare tutto il riquadro a ogni controllo cancellerebbe il testo
 * che si sta scrivendo e gli allegati in attesa di invio.
 */
function aggiornaElencoChat() {
  const lista = document.querySelector('.chat-list');
  if (!lista) return;
  lista.innerHTML = htmlElencoChat() || '<div class="empty">Nessuna conversazione.</div>';
}

function renderChatLayout() {
  const items = htmlElencoChat();

  renderShell(`
    <div class="card">
      <div class="chat-layout">
        <div class="chat-list">${items || '<div class="empty">Nessuna conversazione.</div>'}</div>
        <div class="chat-panel">
          <div class="chat-head" id="chat-head"></div>
          <div class="chat-permesso" id="chat-permesso">${bannerPermessoNotifiche()}</div>
          <div class="msgs-wrap">
            <div class="msgs" id="msgs" onscroll="aggiornaPulsanteFondo()"><div class="empty">Scegli una conversazione</div></div>
            <button class="giu-btn" id="giu-btn" onclick="vaiInFondo()"
                    title="Vai all'ultimo messaggio" aria-label="Vai all'ultimo messaggio">&#8595;</button>
          </div>
          <div class="allegati" id="allegati"></div>
          <div class="composer">
            <button class="attach-btn" id="attach-btn" disabled onclick="scegliFile()"
                    title="Allega file dal computer" aria-label="Allega file">&#128206;</button>
            <input type="file" id="file-input" multiple hidden>
            <input type="text" id="composer-input" placeholder="Scrivi un messaggio…" disabled>
            <button id="send-btn" disabled onclick="sendMessage()">Invia</button>
          </div>
          <div class="drop-velo" id="drop-velo">Rilascia qui i file da inviare</div>
        </div>
      </div>
    </div>
    <div class="refresh-note">I messaggi vengono decifrati nel tuo browser: il server non li vede mai in chiaro.</div>`);

  const input = $('#composer-input');
  if (input) {
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMessage(); });
    // Incolla un'immagine (per esempio uno screenshot) direttamente nel
    // campo di testo, come nelle chat da computer.
    input.addEventListener('paste', (e) => {
      const files = [...(e.clipboardData?.files || [])];
      if (files.length) { e.preventDefault(); fileScelti(files); }
    });
  }
  const fileInput = $('#file-input');
  if (fileInput) {
    fileInput.addEventListener('change', () => { fileScelti(fileInput.files); fileInput.value = ''; });
  }
  collegaTrascinamento();
  disegnaAllegati();
}

async function openChat(chatId) {
  if (state.activeChatId !== chatId) allegatiInAttesa = [];
  state.activeChatId = chatId;
  renderChatLayout();
  $('#composer-input').disabled = false;
  $('#send-btn').disabled = false;
  $('#attach-btn').disabled = false;
  const chat = state.chats.find(c => c.id === chatId);
  const testa = $('#chat-head');
  if (testa && chat) {
    // Stesso posto dell'app: la mappa della conversazione si apre dal
    // pulsante in alto, oltre che dalle card in chat.
    testa.innerHTML = `
      <div class="chat-head-nome">${escapeHtml(chatTitle(chat))}</div>
      <button class="ghost chat-head-mappa" onclick="apriMappaPersonalizzata('${escapeHtml(chat.id)}')"
              title="Mappa personalizzata della conversazione">&#128205; Mappa personalizzata</button>`;
  }
  await loadMessages();
  segnaLetta(chatId);
  if (chatTimer) clearInterval(chatTimer);
  // Niente WebSocket: il pannello e una vista di consultazione, e un
  // polling ogni cinque secondi costa molto meno di una seconda
  // implementazione del protocollo realtime da tenere allineata.
  chatTimer = setInterval(() => { if (state.tab === 'chat') loadMessages(true); }, 5000);
}

async function loadMessages(silent) {
  const chat = state.chats.find(c => c.id === state.activeChatId);
  if (!chat) return;
  try {
    const versions = await chatKeys(chat);
    const messages = await api('/chats/' + chat.id + '/messages?limit=50');
    const box = $('#msgs');
    if (!box) return;

    const rows = [];
    for (const msg of messages) {
      rows.push(await renderBubble(chat, versions, msg));
    }
    // Messaggi nuovi arrivati da altri, rispetto al giro precedente.
    // Il confronto e sull'id dell'ultimo messaggio e non sul conteggio:
    // cancellandone uno il conteggio puo restare uguale mentre in fondo
    // ne e comparso un altro.
    // L'avviso NON parte da qui: se ne occupa controllaChat per tutte le
    // conversazioni, e farlo anche qui produrrebbe due notifiche per lo
    // stesso messaggio. Qui si segna solo la lettura di quello che e
    // appena comparso nella conversazione aperta.
    const ultimo = messages.length ? messages[messages.length - 1] : null;
    const precedente = lastSeenMessageId.get(chat.id);
    if (silent && ultimo && precedente && ultimo.id !== precedente
        && state.me && ultimo.sender_id !== state.me.id) {
      chat.unread_count = Math.max(chat.unread_count || 0, 1);
      segnaLetta(chat.id);
    }
    if (ultimo) lastSeenMessageId.set(chat.id, ultimo.id);

    // Si misura PRIMA di riscrivere il contenuto: dopo, l'altezza e gia
    // cambiata e la distanza dal fondo non vorrebbe piu dire niente.
    //
    // Il ricarico gira ogni cinque secondi e prima finiva sempre con un
    // salto in fondo: chi stava leggendo i messaggi vecchi veniva
    // riportato all'ultimo ogni cinque secondi, e doveva ricominciare a
    // scorrere. La soglia dei 120px e la tolleranza per chi e "in fondo"
    // ma non esattamente a zero, cosa normale con le bolle di altezza
    // diversa e i media che si caricano dopo.
    const eraInFondo = box.scrollHeight - box.scrollTop - box.clientHeight < 120;

    box.innerHTML = rows.join('') || '<div class="empty">Nessun messaggio.</div>';

    // Aprendo la conversazione si va in fondo comunque: li si vuole vedere
    // l'ultimo messaggio, non riprendere da dove si era rimasti.
    if (!silent || eraInFondo) {
      box.scrollTop = box.scrollHeight;
    }
    aggiornaPulsanteFondo();

    await hydrateMedia(box);
  } catch (err) {
    if (!silent) {
      const box = $('#msgs');
      if (box) box.innerHTML = `<div class="error-box">${escapeHtml(err.message)}</div>`;
    }
  }
}

/** Durata di una chiamata in forma leggibile: 324 diventa 5:24. */
function fmtDurata(secondi) {
  const m = Math.floor(secondi / 60);
  const s = String(Math.floor(secondi % 60)).padStart(2, '0');
  return m >= 60
    ? `${Math.floor(m / 60)}:${String(m % 60).padStart(2, '0')}:${s}`
    : `${m}:${s}`;
}

/**
 * Mostra il pulsante di ritorno in fondo solo quando serve davvero.
 *
 * Tenerlo sempre visibile significherebbe un bottone che non fa niente
 * appoggiato sopra l'ultimo messaggio, proprio dove si guarda di piu.
 */
function aggiornaPulsanteFondo() {
  const box = document.getElementById('msgs');
  const btn = document.getElementById('giu-btn');
  if (!box || !btn) return;
  const distanza = box.scrollHeight - box.scrollTop - box.clientHeight;
  btn.classList.toggle('visibile', distanza > 200);
}

function vaiInFondo() {
  const box = document.getElementById('msgs');
  if (!box) return;
  // Scorrimento animato e non salto secco: cosi si capisce di essere stati
  // portati in fondo, invece di ritrovarsi in un punto diverso senza aver
  // visto il movimento.
  box.scrollTo({ top: box.scrollHeight, behavior: 'smooth' });
}

async function renderBubble(chat, versions, msg) {
  const mine = state.me && msg.sender_id === state.me.id;
  const cls = mine ? 'bubble mine' : 'bubble theirs';
  // Messaggio a tempo: si dice quando sparira, come nell'app.
  const scade = msg.expires_at ? ` &middot; &#9203; sparisce alle ${fmtTime(msg.expires_at)}` : '';
  const time = `<span class="time">${fmtTime(msg.timestamp)}${scade}</span>`;
  let body;

  if (msg.media_url) {
    // Il media viene risolto dopo, in hydrateMedia: costruire qui il tag
    // significherebbe tenere il rendering bloccato sul download.
    body = `<div class="media-slot" data-url="${escapeHtml(msg.media_url)}" data-kind="${escapeHtml(msg.type)}">
              <span class="locked">Caricamento…</span></div>`;
    const caption = await decryptText(versions, msg);
    if (caption && msg.type === 'file') {
      const parsed = safeJson(caption);
      if (parsed && parsed.fileName) body += `<div style="font-size:12px;margin-top:6px;">${escapeHtml(parsed.fileName)}</div>`;
    }
  } else if (msg.type === 'location') {
    const raw = await decryptText(versions, msg);
    const loc = safeJson(raw);
    body = loc && loc.lat != null
      ? `📍 <a href="https://www.openstreetmap.org/?mlat=${loc.lat}&mlon=${loc.lng}#map=16/${loc.lat}/${loc.lng}" target="_blank" rel="noopener">Posizione condivisa</a>`
      : '<span class="locked">Posizione non leggibile</span>';
  } else if (msg.type === 'sos') {
    const raw = await decryptText(versions, msg);
    const sos = safeJson(raw);
    body = sos ? `🆘 <strong>Allarme SOS</strong> · batteria ${escapeHtml(sos.battery_pct)}%` : '🆘 <strong>Allarme SOS</strong>';

  // I tipi qui sotto non sono testo: il loro contenuto e un oggetto JSON
  // che descrive un evento. Senza un ramo dedicato finivano nel caso
  // generale, che li mostrava cosi com'erano — righe di parentesi graffe
  // con dentro un identificativo, illeggibili e per giunta con un id
  // interno esposto a schermo.
  //
  // L'app li disegna come schede; qui basta una riga che dica cosa e
  // successo. Il pannello serve a leggere una conversazione, non a
  // rigiocarci dentro: la mappa di un viaggio e la scheda della bacheca
  // stanno nell'app, e riprodurle qui sarebbe una seconda versione da
  // tenere allineata per sempre.
  } else if (msg.type === 'call') {
    const chiamata = safeJson(await decryptText(versions, msg)) || {};
    const durata = Number(chiamata.duration_seconds || 0);
    // Una chiamata senza durata non e "0 secondi": e una chiamata che
    // nessuno ha risposto, ed e proprio l'informazione che interessa.
    body = durata > 0
      ? `📞 <strong>Chiamata</strong> · ${fmtDurata(durata)}`
      : (chiamata.status === 'missed' || chiamata.status === 'declined'
          ? '📞 <strong>Chiamata senza risposta</strong>'
          : '📞 <strong>Chiamata</strong>');

  } else if (msg.type === 'poll') {
    // Sondaggio: domanda e risposte sono cifrate nel messaggio, i voti
    // arrivano in chiaro come numeri di risposta. Qui si leggono i
    // risultati; si vota dall'app.
    const p = safeJson(await decryptText(versions, msg));
    if (p && Array.isArray(p.options)) {
      const conteggi = p.options.map(() => 0);
      const votanti = new Set();
      for (const v of (msg.poll_votes || [])) {
        votanti.add(v.user_id);
        for (const o of (v.options || [])) if (o >= 0 && o < conteggi.length) conteggi[o]++;
      }
      const totale = votanti.size;
      const righe = p.options.map((testo, i) => {
        const perc = totale ? Math.round(conteggi[i] * 100 / totale) : 0;
        return `<div class="sondaggio-riga">${escapeHtml(testo)} &middot; ${conteggi[i]}
                  <div class="sondaggio-barra"><span style="width:${perc}%"></span></div></div>`;
      }).join('');
      const stato = msg.poll_closed_at ? 'Sondaggio chiuso' : 'Si vota dall\'app';
      body = `&#128202; <div class="sondaggio-domanda">${escapeHtml(p.question || 'Sondaggio')}</div>${righe}
              <div class="sondaggio-nota">${totale} ${totale === 1 ? 'voto' : 'voti'} &middot; ${stato}</div>`;
    } else {
      body = '<span class="locked">Sondaggio non leggibile</span>';
    }

  } else if (msg.type === 'trip') {
    body = '🧭 <strong>Viaggia Sicuro</strong> · segui il percorso dall\'app';

  } else if (msg.type === 'board') {
    // Il contenuto della card e in chiaro (id e tipo, niente di scritto
    // dall'utente) e dice se si tratta di una nota o di una mappa. Prima
    // tutte comparivano come "Nota condivisa", anche le mappe.
    const card = safeJson(msg.content) || {};
    if (card.kind === 'map') {
      const cosa = card.event === 'updated' ? 'aggiornata' : 'creata';
      body = `<button class="card-mappa" onclick="apriMappaPersonalizzata('${escapeHtml(chat.id)}')">
                <span class="card-mappa-ico">&#128205;</span>
                <span><strong>Mappa personalizzata</strong> &middot; ${cosa}<br>
                <span class="card-mappa-apri">Apri la mappa &rarr;</span></span>
              </button>`;
    } else {
      body = '📋 <strong>Nota condivisa</strong> · aprila dall\'app';
    }

  } else if (msg.type === 'media_share') {
    const condiviso = safeJson(await decryptText(versions, msg));
    body = condiviso && condiviso.caption
      ? `🖼️ <strong>Foto condivisa</strong> · ${escapeHtml(condiviso.caption)}`
      : '🖼️ <strong>Foto condivisa</strong>';

  } else if (msg.type === 'system') {
    // I messaggi di servizio non appartengono a nessuno dei due: mostrarli
    // come bolla arancione a destra li farebbe sembrare scritti da chi
    // guarda.
    const testo = await decryptText(versions, msg);
    return `<div class="bubble theirs" style="align-self:center;background:#F6EFEA;color:#8C7A72;font-size:12.5px;">
              ${testo ? escapeHtml(testo) : 'Aggiornamento della conversazione'}${time}</div>`;

  } else {
    const text = await decryptText(versions, msg);
    body = text !== null && text !== undefined
      ? escapeHtml(text)
      : '<span class="locked">Messaggio non decifrabile</span>';
  }

  // Reazioni: emoji cifrate come il testo, contate dopo la decifratura.
  const reazioni = new Map();
  for (const r of (msg.reactions || [])) {
    const emoji = await decryptText(versions, { type: 'reaction', content: r.content, iv: r.iv, key_version: r.key_version });
    if (!emoji) continue;
    reazioni.set(emoji, (reazioni.get(emoji) || 0) + 1);
  }
  const striscia = reazioni.size
    ? `<div class="reazioni">${[...reazioni].map(([e, n]) => `<span>${escapeHtml(e)}${n > 1 ? ' ' + n : ''}</span>`).join('')}</div>`
    : '';
  if (!striscia) return `<div class="${cls}">${body}${time}</div>`;
  return `<div class="bubble-wrap ${mine ? 'mine' : 'theirs'}"><div class="${cls}">${body}${time}</div>${striscia}</div>`;
}

/**
 * Testo da mostrare nella notifica del browser.
 *
 * Deliberatamente generico e MAI il contenuto decifrato del messaggio.
 * Una notifica compare sullo schermo bloccato e davanti a chiunque passi
 * accanto al computer: mettere li dentro il testo di una conversazione
 * cifrata annullerebbe, sul piu banale dei canali, la protezione costruita
 * su tutto il resto.
 */
function anteprimaDi(msg) {
  switch (msg.type) {
    case 'image': case 'media_share': return 'Ha inviato una foto';
    case 'video': return 'Ha inviato un video';
    case 'audio': return 'Ha inviato un messaggio vocale';
    case 'file': return 'Ha inviato un file';
    case 'location': return 'Ha condiviso la posizione';
    case 'poll': return 'Ha creato un sondaggio';
    case 'sos': return 'Allarme SOS';
    case 'call': return 'Chiamata';
    case 'trip': return 'Viaggia Sicuro';
    case 'board': return (safeJson(msg.content) || {}).kind === 'map'
      ? 'Mappa personalizzata aggiornata' : 'Nota condivisa';
    default: return 'Nuovo messaggio';
  }
}

function safeJson(raw) {
  if (!raw) return null;
  try { return JSON.parse(raw); } catch (e) { return null; }
}

/** Scarica e decifra i media delle bolle gia disegnate. */
async function hydrateMedia(root) {
  const slots = root.querySelectorAll('.media-slot');
  for (const slot of slots) {
    const url = slot.getAttribute('data-url');
    const kind = slot.getAttribute('data-kind');
    const resolved = await resolveMedia(url);
    if (!resolved) {
      slot.innerHTML = '<span class="locked">Media non disponibile</span>';
      continue;
    }
    if (kind === 'image' || kind === 'media_share') {
      // Cliccabile: l'anteprima dentro la bolla e larga poche centinaia
      // di pixel, e su uno schermo da computer guardare una foto in
      // quello spazio non ha molto senso.
      slot.innerHTML = `<img src="${resolved}" alt="" class="zoomabile" style="cursor:zoom-in;">`;
      const img = slot.querySelector('img');
      img.addEventListener('click', () => apriVisore(resolved));
    } else if (kind === 'video') {
      slot.innerHTML = `<video src="${resolved}" controls></video>`;
    } else if (kind === 'audio') {
      slot.innerHTML = `<audio src="${resolved}" controls></audio>`;
    } else {
      slot.innerHTML = `<a href="${resolved}" download style="color:inherit;">📎 Scarica allegato</a>`;
    }
  }
}

/**
 * Visore a tutto schermo per le immagini della chat.
 *
 * L'indirizzo e un blob creato in memoria dai byte gia decifrati: non
 * riporta al file cifrato e non esce dalla pagina. Chiudendo il visore
 * resta valido finche dura la scheda, quindi riaprire la stessa foto non
 * la riscarica.
 *
 * Non si apre in una scheda nuova di proposito: sarebbe una finestra con
 * dentro il contenuto decifrato di una conversazione privata, e resterebbe
 * aperta anche dopo aver chiuso il pannello.
 */
function apriVisore(src) {
  const vecchio = document.getElementById('visore');
  if (vecchio) vecchio.remove();

  const box = document.createElement('div');
  box.id = 'visore';
  box.className = 'visore';
  box.innerHTML = `
    <button class="visore-chiudi" title="Chiudi (Esc)">&times;</button>
    <img src="${src}" alt="">`;

  const chiudi = () => {
    box.remove();
    document.removeEventListener('keydown', suTasto);
  };
  const suTasto = (e) => { if (e.key === 'Escape') chiudi(); };

  // Il clic chiude solo se colpisce lo sfondo: cliccare sull'immagine
  // mentre la si guarda non deve farla sparire.
  box.addEventListener('click', (e) => { if (e.target === box) chiudi(); });
  box.querySelector('.visore-chiudi').addEventListener('click', chiudi);
  document.addEventListener('keydown', suTasto);

  document.body.appendChild(box);
}

async function sendMessage() {
  const input = $('#composer-input');
  const text = input.value.trim();
  if (!text) return;
  const chat = state.chats.find(c => c.id === state.activeChatId);
  if (!chat) return;

  const btn = $('#send-btn');
  btn.disabled = true; input.disabled = true;
  try {
    const versions = await chatKeys(chat);
    // Nei gruppi si cifra con la versione corrente dichiarata dalla chat,
    // la stessa che usa l'app: usarne una vecchia renderebbe il messaggio
    // leggibile a chi e appena stato tolto dal gruppo.
    const version = chat.type === 'group' ? (chat.key_version || Math.max(...versions.keys())) : null;
    const key = pickKey(versions, version);
    if (!key) throw new Error('Chiave della conversazione non disponibile');

    const { iv, ciphertext } = await aesEncrypt(key, enc.encode(text));
    await api('/chats/' + chat.id + '/messages', {
      method: 'POST',
      body: JSON.stringify({
        type: 'text',
        content: bytesToB64(ciphertext),
        iv: bytesToB64(iv),
        key_version: version,
      }),
    });
    input.value = '';
    await loadMessages();
  } catch (err) {
    alert(err.message);
  } finally {
    btn.disabled = false; input.disabled = false; input.focus();
  }
}

// ── Allegati dal computer ─────────────────────────────────────────────
//
// Stesso percorso dell'app, passo per passo, cosi il telefono di chi
// riceve apre il file come se l'avesse mandato un altro telefono:
//   1. il file si cifra QUI, nel browser, con la chiave della conversazione
//      (formato CEMD, vedi cifraMedia): al server arriva solo ciphertext;
//   2. si carica su /api/media/upload con encrypted=true;
//   3. si manda il messaggio con il media_url. Per i documenti nome,
//      dimensione e tipo viaggiano in un JSON cifrato come il testo, gli
//      stessi campi di FileContent nell'app.
//
// Prima di partire i file restano in una fila visibile sopra il campo di
// testo: un file trascinato per sbaglio nella finestra sbagliata non deve
// finire in una conversazione senza una conferma.

const MAX_ALLEGATO_BYTES = 50 * 1024 * 1024;   // come MAX_SIZE_BYTES in media.py
let allegatiInAttesa = [];
let invioAllegatiInCorso = false;

/** Tipo del messaggio, come lo manda l'app per lo stesso file. */
function tipoMessaggioPer(file) {
  const t = (file.type || '').toLowerCase();
  if (['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(t)) return 'image';
  if (['video/mp4', 'video/webm', 'video/quicktime'].includes(t)) return 'video';
  return 'file';
}

function fmtDimensione(byte) {
  if (byte < 1024) return byte + ' B';
  if (byte < 1024 * 1024) return (byte / 1024).toFixed(0) + ' KB';
  return (byte / (1024 * 1024)).toFixed(1).replace('.', ',') + ' MB';
}

function scegliFile() {
  if (invioAllegatiInCorso) return;
  const input = $('#file-input');
  if (input) input.click();
}

function fileScelti(lista) {
  if (!state.activeChatId || invioAllegatiInCorso) return;
  const troppoGrandi = [];
  for (const f of [...(lista || [])]) {
    if (f.size > MAX_ALLEGATO_BYTES) { troppoGrandi.push(f.name); continue; }
    if (f.size === 0) continue;
    allegatiInAttesa.push(f);
  }
  if (troppoGrandi.length) {
    alert('Non inviati perche superano i 50 MB:\n' + troppoGrandi.join('\n'));
  }
  disegnaAllegati();
}

function rimuoviAllegato(indice) {
  if (invioAllegatiInCorso) return;
  allegatiInAttesa.splice(indice, 1);
  disegnaAllegati();
}

function annullaAllegati() {
  if (invioAllegatiInCorso) return;
  allegatiInAttesa = [];
  disegnaAllegati();
}

function disegnaAllegati(stato) {
  const box = document.getElementById('allegati');
  if (!box) return;
  if (!allegatiInAttesa.length) { box.innerHTML = ''; return; }
  const righe = allegatiInAttesa.map((f, i) => `
    <div class="allegato">
      <span class="allegato-ico">${tipoMessaggioPer(f) === 'image' ? '&#128247;' : tipoMessaggioPer(f) === 'video' ? '&#127916;' : '&#128196;'}</span>
      <span class="allegato-nome" title="${escapeHtml(f.name)}">${escapeHtml(f.name)}</span>
      <span class="allegato-dim">${fmtDimensione(f.size)}</span>
      ${invioAllegatiInCorso ? '' : `<button class="allegato-x" onclick="rimuoviAllegato(${i})" title="Togli">&times;</button>`}
    </div>`).join('');
  box.innerHTML = `
    ${righe}
    <div class="allegati-azioni">
      <span class="allegati-stato">${escapeHtml(stato || (allegatiInAttesa.length === 1 ? '1 file pronto' : allegatiInAttesa.length + ' file pronti'))}</span>
      <button class="ghost" onclick="annullaAllegati()" ${invioAllegatiInCorso ? 'disabled' : ''}>Annulla</button>
      <button class="primary-sm" onclick="inviaAllegati()" ${invioAllegatiInCorso ? 'disabled' : ''}>Invia</button>
    </div>`;
}

/** Trascinare file sul riquadro della conversazione li mette in fila. */
function collegaTrascinamento() {
  const pannello = document.querySelector('.chat-panel');
  const velo = document.getElementById('drop-velo');
  if (!pannello || !velo) return;
  let profondita = 0;
  const haFile = (e) => [...(e.dataTransfer?.types || [])].includes('Files');
  pannello.addEventListener('dragenter', (e) => {
    if (!haFile(e) || !state.activeChatId) return;
    e.preventDefault(); profondita++; velo.classList.add('visibile');
  });
  pannello.addEventListener('dragover', (e) => { if (haFile(e)) e.preventDefault(); });
  pannello.addEventListener('dragleave', () => {
    profondita = Math.max(0, profondita - 1);
    if (!profondita) velo.classList.remove('visibile');
  });
  pannello.addEventListener('drop', (e) => {
    if (!haFile(e)) return;
    e.preventDefault(); profondita = 0; velo.classList.remove('visibile');
    fileScelti(e.dataTransfer.files);
  });
}

async function inviaAllegati() {
  if (invioAllegatiInCorso || !allegatiInAttesa.length) return;
  const chat = state.chats.find(c => c.id === state.activeChatId);
  if (!chat) return;

  invioAllegatiInCorso = true;
  const totale = allegatiInAttesa.length;
  let inviati = 0;
  try {
    const versions = await chatKeys(chat);
    // Stessa scelta della chiave dei messaggi di testo: nei gruppi la
    // versione corrente, altrimenti chi e appena uscito leggerebbe il file.
    const version = chat.type === 'group' ? (chat.key_version || Math.max(...versions.keys())) : null;
    const key = pickKey(versions, version);
    if (!key) throw new Error('Chiave della conversazione non disponibile');
    await registerMediaKey(key);

    while (allegatiInAttesa.length) {
      const file = allegatiInAttesa[0];
      disegnaAllegati(`Invio ${inviati + 1} di ${totale}: cifratura…`);
      const cifrato = await cifraMedia(key, new Uint8Array(await file.arrayBuffer()));

      disegnaAllegati(`Invio ${inviati + 1} di ${totale}: caricamento…`);
      const form = new FormData();
      form.append('file', new Blob([cifrato], { type: 'application/octet-stream' }), 'upload.bin');
      form.append('encrypted', 'true');
      const res = await apiRaw('/api/media/upload', { method: 'POST', body: form });
      if (!res.ok) {
        const corpo = await res.json().catch(() => ({}));
        throw new Error((corpo.detail || 'Caricamento non riuscito') + ' (' + file.name + ')');
      }
      const { media_url } = await res.json();

      const tipo = tipoMessaggioPer(file);
      const messaggio = { type: tipo, media_url, key_version: version, content: null, iv: null };
      if (tipo === 'file') {
        const meta = JSON.stringify({
          fileName: file.name,
          file_size: file.size,
          mime_type: file.type || 'application/octet-stream',
        });
        const { iv, ciphertext } = await aesEncrypt(key, enc.encode(meta));
        messaggio.content = bytesToB64(ciphertext);
        messaggio.iv = bytesToB64(iv);
      }
      await api('/chats/' + chat.id + '/messages', {
        method: 'POST',
        body: JSON.stringify(messaggio),
      });

      // Il file in chiaro e gia qui: lo si mostra senza riscaricarlo e
      // ridecifrarlo.
      mediaCache.set(media_url, URL.createObjectURL(file));
      allegatiInAttesa.shift();
      inviati++;
    }
    await loadMessages();
  } catch (err) {
    alert(err.message + (inviati ? `\n\nInviati ${inviati} di ${totale}; gli altri restano in fila.` : ''));
  } finally {
    invioAllegatiInCorso = false;
    disegnaAllegati();
  }
}
"""

_JS_GUARDIAN = r"""
// ── Tab: guardiano ────────────────────────────────────────────────────
function requestNotificationPermission() {
  if (!('Notification' in window)) return;
  if (Notification.permission === 'default') Notification.requestPermission();
}

/** Notifica del browser per un evento di sicurezza diverso dal SOS. */
function notifyTimelineEvent(titolo, corpo) {
  if (!('Notification' in window) || Notification.permission !== 'granted') return;
  const n = new Notification(titolo, { body: corpo, tag: 'central-ev-' + Date.now() });
  n.onclick = () => { window.focus(); n.close(); };
}

function notifyNewSos(personName) {
  const body = personName + ' ha attivato un allarme SOS';
  if ('Notification' in window && Notification.permission === 'granted') {
    const n = new Notification('🆘 Allarme SOS', { body, requireInteraction: true, tag: 'central-sos-' + Date.now() });
    n.onclick = () => { window.focus(); n.close(); };
  }
  // Segnale sonoro anche senza permesso desktop: un beep generato al volo,
  // nessun file audio da servire.
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator(); const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    osc.start(); osc.stop(ctx.currentTime + 0.35);
  } catch (e) { /* audio non disponibile, non blocca nulla */ }
  document.title = '🆘 Nuovo SOS — Central';
}

function renderGuardianTab() {
  renderShell('<div class="card"><div class="empty">Carico lo stato…</div></div>');
  loadOverview();
  // L'aggiornamento continua su tutte le sezioni che mostrano lo stato,
  // non solo su una: un avviso che arriva mentre si guarda la cronologia
  // deve comunque comparire nel numero rosso della barra laterale.
  if (!refreshTimer) refreshTimer = setInterval(() => {
    // 'geofence' non c'e piu: quella sezione ha i suoi dati e, soprattutto,
    // e un editor. Ridisegnarla ogni quindici secondi mentre si posiziona
    // un'area rifarebbe la mappa da zero, riportando l'inquadratura al
    // punto di partenza e svuotando il campo del nome a meta digitazione.
    if (['panoramica', 'persone', 'avvisi', 'checkin'].includes(state.tab)) loadOverview();
  }, 15000);
}

async function loadOverview() {
  try {
    const data = await api('/guardian-dashboard/overview');
    state.overview = data.monitored || [];
    archiviati = new Set(data.dismissed_alert_keys || []);
    detectNewSos(data.monitored || []);
    // Ogni sezione che vive su questi dati si ridisegna da sola: prima
    // loadOverview conosceva un solo modo di mostrarli, e chiamandola da
    // un'altra sezione la sostituiva con l'elenco delle persone.
    switch (state.tab) {
      case 'panoramica': disegnaPanoramica(); break;
      case 'avvisi':     disegnaAvvisi(); break;
      case 'checkin':    disegnaCheckin(); break;
      default:           renderOverview(data);
    }
  } catch (err) {
    renderShell(`<div class="card"><div class="error-box">${escapeHtml(err.message)}</div></div>`);
  }
}

function detectNewSos(monitored) {
  // Al primo caricamento si registra solo la situazione di partenza:
  // notificare allarmi gia presenti prima di aprire il pannello sarebbe
  // fuorviante — un "nuovo" allarme vecchio di giorni.
  if (!sosBaselineReady) {
    monitored.forEach(p => sosSeen.set(p.user_id, (p.last_sos_events || []).length));
    sosBaselineReady = true;
    return;
  }
  monitored.forEach(p => {
    const count = (p.last_sos_events || []).length;
    const prev = sosSeen.has(p.user_id) ? sosSeen.get(p.user_id) : count;
    if (count > prev) notifyNewSos(p.name);
    sosSeen.set(p.user_id, count);
  });
}

function checkInBadge(c) {
  if (!c || !c.scheduled) return '<span class="badge neutral">Check-in non pianificato</span>';
  if (c.checked_in) return `<span class="badge ok">✓ Check-in fatto ${c.checked_in_at ? 'alle ' + fmtTime(c.checked_in_at) : ''}</span>`;
  return `<span class="badge warn">⏳ Check-in atteso entro le ${escapeHtml(c.deadline_time || '')}</span>`;
}

function geofenceBadge(g) {
  if (!g || !g.has_active_zone) return '<span class="badge neutral">Nessun perimetro attivo</span>';
  const inside = g.last_event_type !== 'exit';
  const label = g.last_event_type
    ? (inside ? `Dentro «${escapeHtml(g.zone_name)}»` : `Fuori da «${escapeHtml(g.zone_name)}»`)
    : `Nel perimetro «${escapeHtml(g.zone_name)}», nessun evento oggi`;
  return `<span class="badge ${inside ? 'ok' : 'warn'}">${label}</span>`;
}

function tripBadge(t) {
  if (!t) return '';
  const label = t.status === 'active'
    ? `In viaggio${t.last_update_at ? ' · agg. ' + fmtTime(t.last_update_at) : ''}`
    : t.status;
  return `<span class="badge warn">🧭 ${escapeHtml(label)}</span>`;
}

function renderTrail(trail) {
  if (!trail || !trail.length) return '';
  const rows = trail.slice(-6).reverse().map(p => `
    <div class="trail-item">
      <span>${p.event_type === 'enter' ? '↩︎ Rientro nel perimetro' : '↪︎ Uscita dal perimetro'}</span>
      <span>${fmtTime(p.created_at)}</span>
    </div>`).join('');
  return `<div class="trail">${rows}</div>`;
}

/**
 * Chi si sta occupando dell'allarme, e il pulsante per prenderlo in carico.
 *
 * E' la parte piu importante della scheda dopo l'allarme stesso. Un SOS
 * arriva a cinque persone insieme e nessuna sa cosa stiano facendo le
 * altre: senza questo blocco ognuna presume che qualcun altro abbia gia
 * chiamato, e il rischio che non chiami nessuno cresce col numero dei
 * destinatari — l'opposto di quello che ci si aspetta scegliendone cinque.
 */
function bloccoPresaInCarico(e) {
  const presi = e.acknowledged_by || [];
  const ioCiSono = state.me && presi.some(a => a.guardian_id === state.me.id);

  const righe = presi.map(a => `
    <div class="ack-row">
      <span class="ack-check">✔︎</span>
      <span><strong>${escapeHtml(a.name)}</strong> se ne sta occupando
        <span class="ack-when">· ${escapeHtml(fmtDateTime(a.created_at))}</span>
        ${a.note ? `<span class="ack-note">${escapeHtml(a.note)}</span>` : ''}
      </span>
    </div>`).join('');

  // Nessun gesto per annullare: chi ha detto di occuparsene non deve poter
  // sparire dall'elenco con un clic, perche gli altri hanno gia smesso di
  // muoversi contando su quella riga. Se cambia idea, lo dice.
  const pulsante = ioCiSono ? '' : `
    <button class="ack-btn" onclick="prendiInCarico('${escapeHtml(e.id)}')">
      Me ne occupo io
    </button>`;

  const nessuno = presi.length ? '' :
    '<div class="ack-empty">Nessuno se ne sta ancora occupando</div>';

  return `<div class="ack-box" data-ack="${escapeHtml(e.id)}">${nessuno}${righe}${pulsante}</div>`;
}

/**
 * Registra la presa in carico e ricarica subito.
 *
 * Il pulsante si disabilita prima della chiamata: in emergenza si preme
 * due volte per istinto, e un doppio invio manderebbe due notifiche
 * identiche agli altri contatti proprio mentre stanno decidendo cosa fare.
 */
async function prendiInCarico(messageId) {
  const box = document.querySelector(`[data-ack="${messageId}"]`);
  const btn = box ? box.querySelector('.ack-btn') : null;
  if (btn) { btn.disabled = true; btn.textContent = 'Invio…'; }
  try {
    const nota = prompt('Vuoi aggiungere una nota per gli altri contatti? (facoltativa)\nEsempio: "sto andando", "l\'ho sentita al telefono"');
    await api('/guardian-dashboard/sos/' + encodeURIComponent(messageId) + '/ack', {
      method: 'POST',
      body: JSON.stringify({ note: nota || null }),
    });
    await loadOverview();
  } catch (err) {
    alert(err.message);
    if (btn) { btn.disabled = false; btn.textContent = 'Me ne occupo io'; }
  }
}

// Persone la cui sezione allarmi e' stata richiusa. Chiusa e non aperta e'
// lo stato che si ricorda: con dieci allarmi a testa la pagina diventa
// lunghissima, e chi richiude vuole che resti richiuso anche dopo
// l'aggiornamento automatico dei quindici secondi.
let sosChiusi = new Set();
// Allarmi selezionati nella scheda persona, per persona.
let sosSelezionati = new Set();

function alternaSos(userId) {
  if (sosChiusi.has(userId)) sosChiusi.delete(userId); else sosChiusi.add(userId);
  loadOverview();
}

function segnaSos(chiave, scelto) {
  if (scelto) sosSelezionati.add(chiave); else sosSelezionati.delete(chiave);
  aggiornaAzioniSos(chiave.split('|')[0]);
}

function aggiornaAzioniSos(userId) {
  const barra = document.getElementById('sos-azioni-' + userId);
  if (!barra) return;
  const n = Array.from(sosSelezionati).filter(k => k.startsWith(userId + '|')).length;
  barra.style.display = n ? 'flex' : 'none';
  const et = document.getElementById('sos-conta-' + userId);
  if (et) et.textContent = n + (n === 1 ? ' allarme selezionato' : ' allarmi selezionati');
}

function selezionaTuttiSos(userId, scelto) {
  const persona = (state.overview || []).find(x => x.user_id === userId);
  if (!persona) return;
  (persona.last_sos_events || []).forEach(e => {
    const k = userId + '|sos:' + e.id;
    if (scelto) sosSelezionati.add(k); else sosSelezionati.delete(k);
  });
  loadOverview();
}

/** Archivia gli allarmi selezionati di una persona. */
async function archiviaSosPersona(userId) {
  const scelti = Array.from(sosSelezionati).filter(k => k.startsWith(userId + '|'));
  if (!scelti.length) return;
  const keys = scelti.map(k => k.split('|')[1]);

  keys.forEach(k => archiviati.add(k));
  scelti.forEach(k => sosSelezionati.delete(k));
  loadOverview();

  try {
    await api('/guardian-dashboard/alerts/dismiss', {
      method: 'POST', body: JSON.stringify({ keys }),
    });
  } catch (err) {
    keys.forEach(k => archiviati.delete(k));
    loadOverview();
    alert('Archiviazione non riuscita: ' + err.message);
  }
}

function personCard(p) {
  const av = p.avatar_url ? `<img src="${escapeHtml(p.avatar_url)}" alt="">` : escapeHtml(initials(p.name));

  // Gli allarmi archiviati escono dalla scheda: e' il senso
  // dell'archiviazione, e vederli qui dopo averli tolti dagli Avvisi
  // renderebbe il gesto incomprensibile.
  const eventi = (p.last_sos_events || []).filter(e => !archiviati.has('sos:' + e.id));
  const chiuso = sosChiusi.has(p.user_id);
  const scelti = Array.from(sosSelezionati).filter(k => k.startsWith(p.user_id + '|')).length;
  const tuttiScelti = eventi.length > 0 && eventi.every(e => sosSelezionati.has(p.user_id + '|sos:' + e.id));

  const sosBlocco = eventi.length ? `
    <div class="sos-wrap">
      <div class="sos-toolbar">
        <button class="sos-toggle" onclick="alternaSos('${escapeHtml(p.user_id)}')">
          <span class="sos-freccia ${chiuso ? 'chiusa' : ''}">\u25BE</span>
          ${eventi.length} ${eventi.length === 1 ? 'allarme SOS' : 'allarmi SOS'}
        </button>
        ${chiuso ? '' : `
          <label class="sel-all" style="margin-left:auto;">
            <input type="checkbox" ${tuttiScelti ? 'checked' : ''}
                   onchange="selezionaTuttiSos('${escapeHtml(p.user_id)}', this.checked)">
            Seleziona tutti
          </label>`}
      </div>

      <div id="sos-azioni-${escapeHtml(p.user_id)}" class="azioni-bar"
           style="display:${scelti && !chiuso ? 'flex' : 'none'};">
        <span id="sos-conta-${escapeHtml(p.user_id)}">${scelti} selezionati</span>
        <button class="ack-btn" style="background:#8C7A72;"
                onclick="archiviaSosPersona('${escapeHtml(p.user_id)}')">Archivia selezionati</button>
      </div>

      ${chiuso ? '' : eventi.map(e => `
        <div class="sos-card" data-sos="${escapeHtml(e.id)}" data-person="${escapeHtml(p.user_id)}">
          <div class="sos-head">
            <span>
              <input type="checkbox" class="sos-check"
                     ${sosSelezionati.has(p.user_id + '|sos:' + e.id) ? 'checked' : ''}
                     onchange="segnaSos('${escapeHtml(p.user_id)}|sos:${escapeHtml(e.id)}', this.checked)">
              🆘 ALLARME SOS
            </span>
            <span>${fmtDateTime(e.timestamp)}</span>
          </div>
          <div class="sos-body">Contenuto cifrato — sblocca la cifratura per vedere posizione, batteria e video.</div>
          ${bloccoPresaInCarico(e)}
        </div>`).join('')}
    </div>` : '';

  return `
    <div class="card" id="persona-${escapeHtml(p.user_id)}">
      <div class="person">
        <div class="avatar">${av}<span class="dot ${p.is_online ? 'online' : 'offline'}"></span></div>
        <div style="flex:1;">
          <div class="person-name">${escapeHtml(p.name)}</div>
          <div class="person-meta">${p.is_online ? 'Online ora' : (p.last_seen ? 'Ultimo accesso ' + fmtDateTime(p.last_seen) : '')}</div>
          <div class="badges">${checkInBadge(p.check_in)}${geofenceBadge(p.geofence)}${tripBadge(p.active_trip)}</div>
          ${sosBlocco}
          ${renderTrail(p.geofence_trail_today)}
        </div>
      </div>
    </div>`;
}

function renderOverview(data) {
  document.title = 'Central — Area personale';
  const list = data.monitored || [];
  const cards = list.length
    ? list.map(personCard).join('')
    : '<div class="card"><div class="empty">Nessuno ti ha ancora aggiunto come guardiano o contatto SOS.</div></div>';

  const unlockNote = state.priv
    ? ''
    : '<div class="warn-box">Gli allarmi SOS sono cifrati: apri la scheda Chat e inserisci la passphrase di recupero per vederne il contenuto.</div>';

  renderShell(`
    ${unlockNote}
    ${riquadroSottoTutela(list)}
    ${riquadroAllarmi(list)}
    ${cards}
    <div id="timeline-box"><div class="card"><div class="empty">Carico la cronologia…</div></div></div>
    <div class="refresh-note">
      Aggiornato ogni 15 secondi
      ${('Notification' in window && Notification.permission !== 'granted')
        ? ' · <a href="#" onclick="requestNotificationPermission();return false;" style="color:#EA5B2E;">attiva le notifiche desktop</a>'
        : ''}
    </div>`);

  if (state.priv) decorateSosCards(list);
  loadTimeline();
}

/**
 * Riepilogo di tutte le persone che seguo.
 *
 * Sotto ci sono gia le schede dettagliate, una per persona, ed e li che si
 * va a guardare un caso specifico. Ma con otto persone quelle schede sono
 * otto schermate: la domanda "e tutto a posto?" richiedeva di scorrerle
 * una per una. Questo riquadro risponde in un colpo d'occhio, e le schede
 * restano per quando la risposta e no.
 */
/**
 * Porta alla scheda della persona indicata.
 *
 * Scorrimento morbido piu un'evidenziazione che svanisce: senza, saltando
 * in mezzo a nove schede identiche non si capisce quale sia quella
 * appena raggiunta.
 */
function vaiAPersona(userId) {
  const card = document.getElementById('persona-' + userId);
  if (!card) return;
  card.scrollIntoView({ behavior: 'smooth', block: 'start' });
  card.classList.add('persona-evidenziata');
  setTimeout(() => card.classList.remove('persona-evidenziata'), 1800);
}

function riquadroSottoTutela(list) {
  if (!list.length) return '';

  const righe = list.map(p => {
    // Il pallino riassume lo stato peggiore fra quelli attivi: un allarme
    // copre tutto il resto, perche se c'e un SOS non interessa sapere che
    // il check-in di stamattina era regolare.
    let stato = 'ok', testo = 'Nessuna segnalazione';
    const ci = p.check_in, gf = p.geofence, tp = p.active_trip;

    if ((p.last_sos_events || []).length) {
      stato = 'alarm'; testo = 'Allarme SOS';
    } else if (tp && tp.status === 'overdue') {
      stato = 'alarm'; testo = 'Viaggio scaduto';
    } else if (gf && gf.last_event_type === 'exit') {
      stato = 'warn'; testo = 'Fuori dall\'area concordata';
    } else if (ci && ci.scheduled && !ci.checked_in) {
      // In attesa e non allarme: finche la scadenza non e passata, non
      // aver ancora confermato e la normalita, non un problema. Dipingerlo
      // di rosso ogni mattina insegnerebbe a ignorare il rosso.
      stato = 'warn';
      testo = ci.deadline_time ? 'Check-in atteso entro le ' + ci.deadline_time : 'Check-in in attesa';
    } else if (tp && tp.status === 'active') {
      stato = 'warn'; testo = 'In viaggio';
    } else if (ci && ci.checked_in) {
      testo = ci.checked_in_at ? 'Ha confermato alle ' + fmtTime(ci.checked_in_at) : 'Ha confermato oggi';
    } else if (gf && gf.last_event_type === 'enter') {
      testo = 'Nell\'area concordata';
    }

    const colore = stato === 'alarm' ? '#D93025' : (stato === 'warn' ? '#E08A1E' : '#2E9E5B');
    const presenza = p.is_online ? 'in linea' : (p.last_seen ? 'visto ' + fmtDateTime(p.last_seen) : '');

    // Cliccabile: con nove persone la scheda di dettaglio puo stare a
    // due schermate di distanza, e cercarla scorrendo vanifica il senso
    // stesso di un riepilogo.
    return `<div class="tutela-row tutela-cliccabile" onclick="vaiAPersona('${escapeHtml(p.user_id)}')">
      <span class="tutela-dot" style="background:${colore}"></span>
      <span class="tutela-name">${escapeHtml(p.name)}</span>
      <span class="tutela-state" style="color:${colore}">${escapeHtml(testo)}</span>
      <span class="tutela-seen">${escapeHtml(presenza)}</span>
    </div>`;
  }).join('');

  return `<div class="card">
    <h3 style="margin:0 0 4px;">Sotto la mia tutela</h3>
    <div class="muted" style="margin-bottom:10px;">${list.length} ${list.length === 1 ? 'persona' : 'persone'}</div>
    ${righe}
  </div>`;
}

/**
 * Allarmi ricevuti, raccolti in un posto solo.
 *
 * Erano visibili unicamente dentro la scheda della singola persona: per
 * accorgersene bisognava gia sospettare a chi guardare. Un allarme e
 * l'informazione piu urgente del pannello e deve stare in alto, prima di
 * tutto il resto.
 */
function riquadroAllarmi(list) {
  const allarmi = [];
  list.forEach(p => (p.last_sos_events || []).forEach(ev => {
    allarmi.push({ nome: p.name, quando: ev.timestamp, id: ev.id, userId: p.user_id });
  }));
  if (!allarmi.length) return '';

  allarmi.sort((a, b) => new Date(b.quando) - new Date(a.quando));
  const righe = allarmi.slice(0, 10).map(a => `
    <div class="tutela-row tutela-cliccabile" onclick="vaiAPersona('${escapeHtml(a.userId)}')">
      <span class="tutela-dot" style="background:#D93025"></span>
      <span class="tutela-name">${escapeHtml(a.nome)}</span>
      <span class="tutela-state" style="color:#D93025">Allarme SOS</span>
      <span class="tutela-seen">${escapeHtml(fmtDateTime(a.quando))}</span>
    </div>`).join('');

  return `<div class="card alarm-card">
    <h3 style="margin:0 0 4px;">🆘 Allarmi ricevuti</h3>
    <div class="muted" style="margin-bottom:10px;">
      Il dettaglio di ciascun allarme — posizione, batteria, video — sta nella
      scheda della persona, qui sotto.
    </div>
    ${righe}
  </div>`;
}

// ── Scheda: dispositivi ───────────────────────────────────────────────
//
// Perche il posto giusto e proprio il browser: la disconnessione di
// emergenza esiste per quando il telefono e stato perso o rubato. In quel
// momento l'app non ce l'hai piu — hai un computer. Finora la funzione
// viveva solo dentro l'app, cioe l'unico posto in cui, nel caso per cui e
// stata costruita, non puoi arrivare.

function renderDevicesTab() {
  renderShell('<div class="card"><div class="empty">Carico i dispositivi…</div></div>');
  loadDevices();
}

async function loadDevices() {
  try {
    const devices = await api('/devices/');
    renderShell(renderDevices(devices));
  } catch (err) {
    renderShell(`<div class="card"><div class="error-box">${escapeHtml(err.message)}</div></div>`);
  }
}

function renderDevices(devices) {
  const attivi = devices.filter(d => !d.revoked_at);
  const revocati = devices.filter(d => d.revoked_at);

  const riga = (d) => {
    const nome = d.name || (d.platform ? 'Dispositivo ' + d.platform : 'Dispositivo');
    const visto = d.last_seen_at ? 'ultimo accesso ' + fmtDateTime(d.last_seen_at) : 'mai usato';
    const revocato = !!d.revoked_at;
    return `<div class="dev-row ${revocato ? 'dev-off' : ''}">
      <div class="dev-info">
        <div class="dev-name">
          ${escapeHtml(nome)}
          ${d.is_current ? '<span class="dev-tag">questa sessione</span>' : ''}
          ${revocato ? '<span class="dev-tag dev-tag-off">disconnesso</span>' : ''}
        </div>
        <div class="dev-meta">
          ${escapeHtml(d.platform || 'piattaforma sconosciuta')}
          ${d.app_version ? ' · versione ' + escapeHtml(d.app_version) : ''}
          · ${escapeHtml(visto)}
        </div>
      </div>
      ${(!revocato && !d.is_current)
        ? `<button class="dev-btn" onclick="disconnettiDispositivo('${escapeHtml(d.id)}','${escapeHtml(nome).replace(/'/g, "&#39;")}')">Disconnetti</button>`
        : ''}
    </div>`;
  };

  return `
    <div class="card">
      <h3 style="margin:0 0 4px;">Dispositivi collegati</h3>
      <div class="muted" style="margin-bottom:12px;">
        Se hai perso un telefono o te l'hanno rubato, disconnettilo da qui:
        chi lo ha in mano perde subito l'accesso al tuo account. Ti verra
        chiesta la password, perche e l'unica cosa che tu hai e chi ha il
        telefono no.
      </div>
      ${attivi.map(riga).join('') || '<div class="empty">Nessun dispositivo attivo.</div>'}
    </div>
    ${revocati.length ? `<div class="card">
      <h3 style="margin:0 0 10px;">Disconnessi in precedenza</h3>
      ${revocati.map(riga).join('')}
    </div>` : ''}`;
}

/**
 * Disconnessione di emergenza di un dispositivo.
 *
 * Due passaggi di conferma di proposito, ed e l'unica funzione del
 * pannello dove ne metto due. Il gesto e irreversibile per chi lo subisce
 * — quel telefono dovra rifare l'accesso da capo — e viene compiuto in un
 * momento di agitazione, che e esattamente quando si clicca sulla riga
 * sbagliata.
 */
async function disconnettiDispositivo(deviceId, nome) {
  if (!confirm('Disconnettere "' + nome + '"?\n\nChi ha quel dispositivo perdera subito l\'accesso al tuo account e dovra rifare l\'accesso con la tua password.')) return;

  const password = prompt('Conferma con la tua password:');
  if (!password) return;

  try {
    await api('/devices/' + encodeURIComponent(deviceId) + '/revoke', {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
    await loadDevices();
  } catch (err) {
    alert(err.message);
  }
}

// ══════════════════════════════════════════════════════════════════════
// MAPPA IN TEMPO REALE
// ══════════════════════════════════════════════════════════════════════
//
// Leaflet e le sue immagini sono serviti dal nostro dominio, come la
// libreria di crittografia: in una pagina dove si digita la frase di
// recupero, ogni script caricato da un servizio esterno e qualcuno che
// potrebbe sostituirlo con del codice che se la porta via.
//
// Le posizioni sono cifrate e si aprono solo qui nel browser, con la
// chiave ricavata dalla frase di recupero. Senza sblocco la mappa resta
// vuota: non e un limite tecnico da aggirare, e il funzionamento
// previsto — il server quelle coordinate non le ha mai viste.

let liveMap = null;
// Cosa c'era sulla mappa al giro precedente: serve a reinquadrare solo
// quando compare qualcosa di nuovo, non a ogni aggiornamento.
let firmaMappa = '';
let liveMarkers = [];
let leafletPronto = false;
// Inquadratura da riprendere quando la mappa viene ricostruita dopo un
// ridisegno della pagina.
let vistaPrecedente = null;
// Mappa ingrandita: si ricorda, altrimenti il ridisegno automatico ogni
// quindici secondi la rimpicciolirebbe sotto le mani di chi la sta usando.
let mappaGrande = false;
// Ultimi dati disegnati, per poter reinquadrare quando si ingrandisce
// senza rifare tutte le chiamate e le decifrature.
let ultimiPunti = [];
let ultimiViaggi = [];

async function caricaLeaflet() {
  if (leafletPronto) return;
  // Si aspettano ENTRAMBI, foglio di stile compreso. Aspettare il solo
  // script sembra sufficiente ma non lo e: senza il CSS di Leaflet gia
  // applicato, le tessere vengono posizionate con regole che non esistono
  // ancora e la mappa resta un rettangolo grigio, senza alcun errore.
  await Promise.all([
    new Promise((ok, ko) => {
      const css = document.createElement('link');
      css.rel = 'stylesheet'; css.href = '/static/leaflet.css';
      css.onload = ok; css.onerror = () => ko(new Error('Stile mappa non caricato'));
      document.head.appendChild(css);
    }),
    new Promise((ok, ko) => {
      const js = document.createElement('script');
      js.src = '/static/leaflet.js';
      js.onload = ok; js.onerror = () => ko(new Error('Mappa non disponibile'));
      document.head.appendChild(js);
    }),
  ]);
  leafletPronto = true;
}

/**
 * Spillo degli allarmi SOS, disegnato invece che caricato.
 *
 * Gli spilli predefiniti di Leaflet sono tre file PNG. Non si vedevano —
 * al loro posto comparivano i rettangoli dell'immagine rotta — e per una
 * mappa che deve mostrare dove si trova qualcuno in emergenza dipendere da
 * un file che puo non arrivare e un rischio inutile.
 *
 * Un disegno vettoriale scritto qui dentro non puo mancare, si adatta a
 * qualunque densita di schermo e pesa meno di una richiesta in rete.
 */
function spilloSos() {
  return L.divIcon({
    className: '',
    html: `<svg width="30" height="40" viewBox="0 0 30 40" xmlns="http://www.w3.org/2000/svg">
      <path d="M15 39C15 39 28 23.5 28 14A13 13 0 1 0 2 14c0 9.5 13 25 13 25z"
            fill="#DC2626" stroke="#fff" stroke-width="2.5"/>
      <text x="15" y="19" text-anchor="middle" font-size="13" font-weight="700"
            fill="#fff" font-family="system-ui,sans-serif">!</text>
    </svg>`,
    iconSize: [30, 40],
    // La punta dello spillo, non il centro: e quella che indica il luogo.
    iconAnchor: [15, 39],
    popupAnchor: [0, -34],
  });
}

/**
 * Ingrandisce la mappa a tutta larghezza, e la riporta indietro.
 *
 * Nella colonna della panoramica la mappa e larga poco piu di trecento
 * pixel: bastano a dire "c'e qualcuno da quelle parti", non a leggere una
 * via. Ed e la lettura della via che serve quando si guarda un allarme.
 *
 * Non e una finestra a tutto schermo di proposito: cosi restano visibili
 * l'elenco dei viaggi sotto e i riquadri accanto, e non si perde il
 * contesto per guardare una cosa sola.
 */
function alternaMappaGrande() {
  const pannello = document.getElementById('pannello-mappa');
  if (!pannello) return;

  mappaGrande = !mappaGrande;
  pannello.classList.toggle('mappa-grande', mappaGrande);

  const etichetta = document.getElementById('map-espandi');
  if (etichetta) etichetta.textContent = mappaGrande ? 'Riduci \u2921' : 'Ingrandisci \u2922';

  // Leaflet non si accorge da solo che il riquadro ha cambiato dimensione:
  // senza questo, la mappa resterebbe disegnata sulle misure vecchie, con
  // metà area grigia. L'attesa lascia finire la transizione CSS.
  setTimeout(() => {
    if (!liveMap) return;
    liveMap.invalidateSize();
    // Reinquadra sui punti: ingrandire per poi dover ricentrare a mano
    // sarebbe mezzo servizio.
    const coords = estremiDi(ultimiPunti, ultimiViaggi);
    if (coords.length) {
      liveMap.fitBounds(L.latLngBounds(coords).pad(0.25));
      if (liveMap.getZoom() > 16) liveMap.setZoom(16);
    }
  }, 260);
}

function destroyLiveMap() {
  if (liveMap) { liveMap.remove(); liveMap = null; }
  liveMarkers = [];
}

/** Chiude la mappa e dimentica l'inquadratura: si usa cambiando sezione. */
function resetLiveMap() {
  destroyLiveMap();
  vistaPrecedente = null;
}

/**
 * Raccoglie le posizioni che questo browser e in grado di decifrare.
 *
 * Due sorgenti: l'ultima posizione di un viaggio in corso e quella
 * allegata a un allarme SOS. Sono le uniche coordinate che esistono nel
 * sistema — il perimetro non ne produce, segnala solo l'attraversamento —
 * e per entrambe la chiave e ricavabile da chi sta guardando.
 */
async function raccogliPosizioni() {
  const list = state.overview || [];
  const punti = [];
  if (!state.priv) return punti;

  for (const p of list) {
    if (!p.public_key) continue;
    let key;
    try { key = await sharedKeyFrom(state.priv, p.public_key); } catch (e) { continue; }

    for (const ev of (p.last_sos_events || [])) {
      // Gli allarmi archiviati escono anche dalla mappa: archiviare
      // significa "me ne sono occupato", e uno spillo rosso che resta li
      // continuerebbe a chiedere attenzione per qualcosa di gia chiuso.
      // Restano consultabili in Storia eventi, dove il dato non sparisce.
      if (archiviati.has('sos:' + ev.id)) continue;
      if (!ev.content || !ev.iv) continue;
      try {
        const sos = safeJson(dec.decode(await aesDecrypt(key, b64ToBytes(ev.iv), b64ToBytes(ev.content))));
        if (sos && sos.lat && sos.lng) {
          punti.push({ nome: p.name, lat: sos.lat, lng: sos.lng,
                       tipo: 'SOS', quando: ev.timestamp });
        }
      } catch (e) { /* busta non apribile: si salta */ }
    }
  }
  return punti;
}

// ── Viaggi in corso ───────────────────────────────────────────────────
//
// CHI PUO VEDERLI
//
// Non i contatti di emergenza: i controllori del singolo viaggio, cioe
// le persone che il viaggiatore ha scelto una per una al momento di
// partire. Sono due elenchi distinti, e volutamente: essere il contatto
// SOS di qualcuno significa poter ricevere un suo allarme, non seguirlo
// ogni volta che esce di casa.
//
// Il permesso non lo decide questo codice. Il server risponde solo con i
// viaggi per cui esiste una busta indirizzata a chi chiede, e senza quella
// busta non ci sarebbe comunque nulla da decifrare: anche se la risposta
// arrivasse per errore, resterebbe illeggibile. E la stessa regola che
// vale nell'app, applicata dallo stesso endpoint.

/**
 * Apre la chiave di un viaggio a partire dalla propria busta.
 *
 * La busta e chiusa con il segreto condiviso fra me e il viaggiatore:
 * serve la SUA chiave pubblica, non la mia.
 */
async function chiaveViaggio(trip) {
  if (!trip.my_encrypted_key || !trip.my_key_iv) return null;
  const pub = trip.traveler && trip.traveler.public_key;
  if (!pub) return null;
  try {
    const shared = await sharedKeyFrom(state.priv, pub);
    return await aesDecrypt(shared, b64ToBytes(trip.my_key_iv), b64ToBytes(trip.my_encrypted_key));
  } catch (e) {
    return null;
  }
}

/**
 * Viaggi che sto sorvegliando, con tragitto e destinazione decifrati.
 *
 * La traccia si chiede solo per i viaggi ancora in corso: su uno concluso
 * si mostra l'ultimo punto e basta, e scaricare il percorso di ogni
 * viaggio delle ultime 24 ore a ogni aggiornamento sarebbe una richiesta
 * al server ogni quindici secondi per informazioni che non cambiano piu.
 */
async function raccogliViaggi() {
  if (!state.priv) return [];

  let attivi;
  try {
    attivi = await api('/trips/active');
  } catch (e) {
    return [];
  }

  // Solo quelli attivi o scaduti senza conferma: sono i viaggi ancora "in
  // corso", cioe quelli per cui ha senso guardare dove e la persona adesso.
  // I conclusi da poco restano nell'app e nella Storia eventi.
  const miei = attivi.filter(t => !t.i_am_traveler
    && (t.status === 'active' || t.status === 'overdue'));
  const out = [];

  for (const trip of miei) {
    const key = await chiaveViaggio(trip);
    if (!key) continue;

    let destinazione = null;
    try {
      destinazione = safeJson(dec.decode(
        await aesDecrypt(key, b64ToBytes(trip.destination_iv), b64ToBytes(trip.destination_encrypted))
      ));
    } catch (e) { /* destinazione non apribile: il tragitto resta utile */ }

    const inCorso = trip.status === 'active' || trip.status === 'overdue';
    let tracciato = [];
    if (inCorso) {
      try {
        const grezzi = await api('/trips/' + encodeURIComponent(trip.id) + '/positions');
        for (const pos of grezzi) {
          try {
            const pt = safeJson(dec.decode(
              await aesDecrypt(key, b64ToBytes(pos.payload_iv), b64ToBytes(pos.payload_encrypted))
            ));
            // L'orario viene dalla risposta e non dalla busta: serve a
            // capire dove il tracciato ha un buco, e il server quel dato lo
            // conosce gia.
            if (pt && pt.lat && pt.lng) {
              tracciato.push({
                lat: pt.lat, lng: pt.lng,
                quando: Date.parse(pos.recorded_at) || 0,
              });
            }
          } catch (e) { /* punto illeggibile: si salta, la linea prosegue */ }
        }
      } catch (e) { /* traccia non disponibile */ }
    }

    let ultimo = null;
    if (trip.last_position) {
      try {
        const pt = safeJson(dec.decode(await aesDecrypt(
          key, b64ToBytes(trip.last_position.payload_iv),
          b64ToBytes(trip.last_position.payload_encrypted)
        )));
        if (pt && pt.lat && pt.lng) {
          ultimo = { lat: pt.lat, lng: pt.lng, quando: trip.last_position.recorded_at };
        }
      } catch (e) { /* niente */ }
    }

    out.push({
      id: trip.id,
      nome: trip.traveler ? trip.traveler.name : 'Utente',
      avatar: trip.traveler ? trip.traveler.avatar_url : null,
      stato: trip.status,
      destinazione,
      passeggiata: trip.mode === 'walk',
      tracciato,
      ultimo,
      etaAt: trip.eta_at,
      deadlineAt: trip.deadline_at,
    });
  }
  return out;
}

/**
 * Divide il tracciato dove c'e stata un'interruzione.
 *
 * Le posizioni partono ogni quaranta secondi circa: cinque minuti fra due
 * punti consecutivi non sono un ritardo, sono un buco. La soglia e
 * generosa apposta — il risparmio energetico del telefono puo diradare i
 * rilevamenti anche con la rete presente, e spezzare a ogni rallentamento
 * darebbe un tratteggio che non racconta niente.
 *
 * Un punto senza orario non spezza mai: meglio una linea continua di una
 * spezzata a caso perche una data non si e lasciata interpretare.
 */
const BUCO_MS = 5 * 60 * 1000;

function segmentiDi(tracciato) {
  if (!tracciato || tracciato.length < 2) return [];

  const segmenti = [];
  let corrente = [tracciato[0]];

  for (let i = 1; i < tracciato.length; i++) {
    const prima = tracciato[i - 1];
    const ora = tracciato[i];
    const orariNoti = prima.quando > 0 && ora.quando > 0;

    if (orariNoti && (ora.quando - prima.quando) > BUCO_MS) {
      segmenti.push(corrente);
      corrente = [ora];
    } else {
      corrente.push(ora);
    }
  }
  segmenti.push(corrente);

  // Un segmento con un punto solo non e una linea: si scarta.
  return segmenti.filter(s => s.length > 1);
}

// Un colore per viaggio: con tre persone in movimento insieme, tre linee
// dello stesso colore sulla stessa mappa non si distinguono piu. Il primo e
// quello dell'app (#E8613C), cosi con un viaggio solo la mappa e identica.
const COLORI_VIAGGIO = ['#E8613C', '#2563EB', '#7C3AED', '#0891B2', '#BE185D'];

function coloreViaggio(v, i) {
  return v.stato === 'overdue' ? '#DC2626' : COLORI_VIAGGIO[i % COLORI_VIAGGIO.length];
}

/**
 * Pallino con la foto della persona, come il segnaposto dell'app
 * (TravelerPin): tondo, bordo nel colore del suo tragitto, punta in basso
 * sul punto esatto. Senza foto, le iniziali.
 *
 * L'immagine e l'avatar pubblico del profilo, non un media cifrato: si
 * carica direttamente, e se non arriva restano le iniziali.
 */
const ICONA_PASSEGGIATA = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"
  stroke-linecap="round" stroke-linejoin="round"><circle cx="13" cy="4" r="2"/>
  <path d="M7 21l3-7 3 2v5M10 14l1-5 4 3 3 1M8 10l3-1"/></svg>`;

function pallinoPersona(nome, avatarUrl, colore, passeggiata) {
  const iniziali = escapeHtml(initials(nome));
  const dentro = avatarUrl
    ? `<img src="${escapeHtml(avatarUrl)}" alt="" onerror="this.replaceWith(document.createTextNode('${iniziali}'))">`
    : iniziali;
  const badge = passeggiata
    ? `<span class="pin-persona-badge" style="color:${colore}" title="Passeggiata">${ICONA_PASSEGGIATA}</span>`
    : '';
  return L.divIcon({
    className: '',
    html: `<div class="pin-persona" style="--colore:${colore}">
             <div class="pin-persona-foto">${dentro}</div>${badge}
           </div>`,
    iconSize: [46, 56],
    iconAnchor: [23, 55],
    popupAnchor: [0, -50],
  });
}

/** Segnalino della destinazione: spillo con bandierina, nel colore del viaggio. */
function segnalinoDestinazione(colore) {
  return L.divIcon({
    className: '',
    html: `<svg width="30" height="40" viewBox="0 0 30 40" xmlns="http://www.w3.org/2000/svg">
      <path d="M15 39C15 39 28 23.5 28 14A13 13 0 1 0 2 14c0 9.5 13 25 13 25z"
            fill="${colore}" stroke="#fff" stroke-width="2.5"/>
      <path d="M11 8v12M11 8h8l-2 3 2 3h-8" stroke="#fff" stroke-width="2"
            fill="none" stroke-linejoin="round" stroke-linecap="round"/>
    </svg>`,
    iconSize: [30, 40],
    iconAnchor: [15, 39],
    popupAnchor: [0, -34],
    tooltipAnchor: [12, -24],
  });
}

function disegnaViaggi(viaggi) {
  viaggi.forEach((v, i) => {
    const colore = coloreViaggio(v, i);

    // Una linea per segmento, non una sola che attraversa i buchi.
    //
    // Senza rete le posizioni non arrivano, e al ritorno della connessione
    // il punto nuovo veniva unito al precedente con una retta: chilometri
    // tagliati da un segmento che nessuno ha percorso. Chi guarda poteva
    // concludere "e passata di li", che e falso — e in una funzione di
    // sicurezza un'informazione sbagliata e peggio di una mancante.
    // Stesso spessore e stessa regola dell'app (TripMapScreen).
    segmentiDi(v.tracciato).forEach(segmento => {
      const linea = L.polyline(segmento.map(p => [p.lat, p.lng]), {
        color: colore, weight: 4.5, opacity: .9, lineJoin: 'round', lineCap: 'round',
      }).addTo(liveMap);
      linea.bindPopup('Tragitto di ' + escapeHtml(v.nome));
      liveMarkers.push(linea);
    });

    // Segnalino della destinazione, con l'indirizzo in un'etichetta al
    // passaggio del mouse e nel fumetto.
    if (v.destinazione && v.destinazione.lat && v.destinazione.lng) {
      const indirizzo = v.destinazione.label || 'Punto scelto sulla mappa';
      const meta = L.marker([v.destinazione.lat, v.destinazione.lng], {
        icon: segnalinoDestinazione(colore), zIndexOffset: 500,
      }).addTo(liveMap);
      meta.bindTooltip(escapeHtml(indirizzo), { direction: 'right' });
      meta.bindPopup(
        '<strong>Arrivo di ' + escapeHtml(v.nome) + '</strong><br>' +
        escapeHtml(indirizzo) +
        (v.etaAt ? '<br>Arrivo previsto entro le ' + escapeHtml(fmtTime(v.etaAt)) : '')
      );
      liveMarkers.push(meta);
    }

    const posizione = v.ultimo || (v.tracciato.length
      ? v.tracciato[v.tracciato.length - 1]
      : null);

    if (posizione) {
      const persona = L.marker([posizione.lat, posizione.lng], {
        icon: pallinoPersona(v.nome, v.avatar, colore, v.passeggiata), zIndexOffset: 1000,
      }).addTo(liveMap);
      const etichetta = v.passeggiata
        ? (v.stato === 'overdue' ? 'Passeggiata scaduta senza conferma di rientro' : 'In passeggiata')
        : (v.stato === 'overdue' ? 'Viaggio scaduto senza conferma di arrivo' : 'In viaggio');
      persona.bindTooltip(escapeHtml(v.nome) + (v.passeggiata ? ' \u00b7 passeggiata' : ''), { direction: 'top', offset: [0, -50] });
      persona.bindPopup(
        '<strong>' + escapeHtml(v.nome) + '</strong><br>' + escapeHtml(etichetta) +
        (v.passeggiata && v.etaAt ? '<br>Rientro previsto entro le ' + escapeHtml(fmtTime(v.etaAt)) : '') +
        (!v.passeggiata && v.destinazione && v.destinazione.label ? '<br>Verso: ' + escapeHtml(v.destinazione.label) : '') +
        (posizione.quando ? '<br>Ultima posizione: ' + escapeHtml(fmtDateTime(posizione.quando)) : '')
      );
      liveMarkers.push(persona);
    }
  });
}

/**
 * Elenco dei viaggi seguiti, sotto la mappa.
 *
 * La mappa dice dove; questo dice entro quando. Con piu viaggi insieme il
 * pallino colorato accanto al nome e l'unico modo per capire quale linea
 * appartiene a chi.
 */
function listaViaggi(viaggi) {
  if (!viaggi.length) return '';
  return viaggi.map((v, i) => {
    const colore = coloreViaggio(v, i);
    const stato = v.passeggiata
      ? (v.stato === 'overdue' ? 'Passeggiata scaduta' : 'In passeggiata')
      : (v.stato === 'overdue' ? 'Scaduto senza conferma' : 'In viaggio');
    const senzaPosizione = !v.ultimo && !v.tracciato.length
      ? ' \u00b7 in attesa della prima posizione' : '';
    const foto = v.avatar
      ? `<img src="${escapeHtml(v.avatar)}" alt="">`
      : escapeHtml(initials(v.nome));
    return `<div class="pl-row">
      <span class="viaggio-foto" style="border-color:${colore}">${foto}</span>
      <span>${escapeHtml(v.nome)}</span>
      <span style="font-size:12.5px;color:${colore};margin-left:10px;">${escapeHtml(stato)}</span>
      <span class="pl-when">
        ${v.passeggiata ? 'Passeggiata \u00b7 '
          : v.destinazione && v.destinazione.label
          ? escapeHtml(v.destinazione.label) + ' \u00b7 ' : ''}
        ${v.etaAt ? 'entro le ' + escapeHtml(fmtTime(v.etaAt)) : ''}${senzaPosizione}
      </span>
    </div>`;
  }).join('');
}

/** Tutte le coordinate disegnate, per inquadrare la mappa. */
function estremiDi(punti, viaggi) {
  const coords = punti.map(p => [p.lat, p.lng]);
  viaggi.forEach(v => {
    coords.push(...v.tracciato.map(p => [p.lat, p.lng]));
    if (v.ultimo) coords.push([v.ultimo.lat, v.ultimo.lng]);
    if (v.destinazione && v.destinazione.lat) coords.push([v.destinazione.lat, v.destinazione.lng]);
  });
  return coords;
}

async function montaLiveMap() {
  const nota = document.getElementById('map-note');
  const box = document.getElementById('live-map');
  if (!box) return;

  if (!state.priv) {
    box.style.display = 'none';
    if (nota) nota.innerHTML =
      'Le posizioni sono cifrate. <a href="#" onclick="switchTab(\'chat\');return false;">Sblocca la cifratura</a> per vederle sulla mappa.';
    return;
  }

  try {
    await caricaLeaflet();
  } catch (e) {
    if (nota) nota.textContent = 'Mappa non disponibile: ' + e.message;
    return;
  }

  const [punti, viaggi] = await Promise.all([raccogliPosizioni(), raccogliViaggi()]);

  // Mentre si decifrava, la panoramica puo essere stata ridisegnata (lo fa
  // due volte di fila all'apertura: dati in memoria, poi dati freschi). Il
  // riquadro di questa chiamata non e piu nella pagina: se si creasse la
  // mappa li dentro, Leaflet calcolerebbe l'inquadratura su un riquadro di
  // misura zero e la chiamata successiva erediterebbe quello zoom
  // sbagliato — con tutto schiacciato in un punto sull'Italia intera. Se ne
  // occupa la chiamata piu recente.
  if (!document.body.contains(box)) return;

  // La panoramica si ridisegna da capo ogni quindici secondi, e con essa
  // sparisce il riquadro a cui Leaflet era agganciato. La variabile pero
  // restava valorizzata, quindi il ramo "if (!liveMap)" veniva saltato e
  // la mappa non si riagganciava mai al riquadro nuovo: da li in poi un
  // rettangolo grigio, senza errori da nessuna parte.
  if (liveMap && !document.body.contains(liveMap.getContainer())) {
    vistaPrecedente = { centro: liveMap.getCenter(), zoom: liveMap.getZoom() };
    destroyLiveMap();
  }

  const primaVolta = !liveMap;

  if (!liveMap) {
    liveMap = L.map(box, { zoomControl: true, attributionControl: true });
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap',
    }).addTo(liveMap);
    // Si riprende l'inquadratura di prima, se c'era: dopo ogni
    // aggiornamento automatico l'utente si ritroverebbe altrimenti la
    // mappa riportata al punto di partenza mentre la stava guardando.
    if (vistaPrecedente) {
      liveMap.setView(vistaPrecedente.centro, vistaPrecedente.zoom);
    } else {
      // Vista iniziale sull'Italia: senza, una mappa senza punti si apre
      // sull'oceano e sembra rotta.
      liveMap.setView([42.5, 12.5], 5);
    }
  }

  liveMarkers.forEach(m => liveMap.removeLayer(m));
  liveMarkers = [];

  punti.forEach(pt => {
    const m = L.marker([pt.lat, pt.lng], { icon: spilloSos() }).addTo(liveMap);
    m.bindPopup(
      '<strong>' + escapeHtml(pt.nome) + '</strong><br>' +
      escapeHtml(pt.tipo) + ' \u00b7 ' + escapeHtml(fmtDateTime(pt.quando))
    );
    liveMarkers.push(m);
  });

  disegnaViaggi(viaggi);

  // L'inquadratura automatica solo alla prima apertura e quando non c'era
  // una vista da riprendere: rifarla a ogni aggiornamento strapperebbe la
  // mappa di mano a chi sta guardando un punto preciso.
  //
  // Si reinquadra anche quando compare qualcosa di nuovo — un viaggio
  // appena partito, un SOS appena arrivato: e proprio quello che chi guarda
  // deve vedere, e lasciarlo fuori dall'inquadratura lo nasconderebbe.
  const coords = estremiDi(punti, viaggi);
  const firma = viaggi.map(v => v.id).concat(punti.map(p => p.lat + ',' + p.lng)).sort().join('|');
  const novita = firma !== firmaMappa && firma.split('|').some(x => x && !firmaMappa.split('|').includes(x));
  if (coords.length && ((primaVolta && !vistaPrecedente) || novita)) {
    liveMap.fitBounds(L.latLngBounds(coords).pad(0.25));
    if (liveMap.getZoom() > 15) liveMap.setZoom(15);
  }
  firmaMappa = firma;

  ultimiPunti = punti;
  ultimiViaggi = viaggi;

  const box2 = document.getElementById('viaggi-lista');
  if (box2) box2.innerHTML = listaViaggi(viaggi);

  // Leaflet calcola le dimensioni al momento della creazione: se il
  // riquadro e stato disegnato un istante prima, le trova a zero e mostra
  // una mappa grigia. Un ricalcolo dopo il disegno risolve.
  setTimeout(() => liveMap && liveMap.invalidateSize(), 60);

  if (nota) {
    const pezzi = [];
    const passeggiate = viaggi.filter(v => v.passeggiata).length;
    const versoMeta = viaggi.length - passeggiate;
    if (versoMeta) {
      pezzi.push(versoMeta + (versoMeta === 1 ? ' viaggio sicuro in corso' : ' viaggi sicuri in corso'));
    }
    if (passeggiate) {
      pezzi.push(passeggiate + (passeggiate === 1 ? ' passeggiata in corso' : ' passeggiate in corso'));
    }
    if (punti.length) {
      pezzi.push(punti.length + (punti.length === 1 ? ' allarme SOS' : ' allarmi SOS'));
    }
    nota.innerHTML = pezzi.length
      ? escapeHtml(pezzi.join(' \u00b7 ')) +
        ' \u2014 <span style="opacity:.75;">foto: dov\'&egrave; ora \u00b7 linea: tragitto \u00b7 segnalino: arrivo</span>'
      : 'Nessuna posizione da mostrare: compaiono qui gli allarmi SOS e i viaggi sicuri in corso che stai seguendo.';
  }
}

// ══════════════════════════════════════════════════════════════════════
// PANORAMICA
// ══════════════════════════════════════════════════════════════════════

function renderPanoramica() {
  renderShell('<div class="panel"><div class="panel-body"><div class="empty">Carico…</div></div></div>');
  if (state.overview) disegnaPanoramica();
  loadOverview();
  loadTimeline();
}

/** Numeri in cima: quello che si guarda per primo entrando. */
function calcolaIndicatori(list) {
  let online = 0, avvisi = 0, sosOggi = 0, ciFatti = 0, ciAttesi = 0;
  const oggi = new Date().toDateString();

  list.forEach(p => {
    if (p.is_online) online++;
    (p.last_sos_events || []).forEach(e => {
      avvisi++;
      if (new Date(e.timestamp).toDateString() === oggi) sosOggi++;
    });
    if (p.geofence && p.geofence.last_event_type === 'exit') avvisi++;
    if (p.active_trip && p.active_trip.status === 'overdue') avvisi++;
    if (p.check_in && p.check_in.scheduled) {
      ciAttesi++;
      if (p.check_in.checked_in) ciFatti++; else avvisi++;
    }
  });
  return { online, totali: list.length, avvisi, sosOggi, ciFatti, ciAttesi };
}

function disegnaPanoramica() {
  const list = state.overview || [];
  const k = calcolaIndicatori(list);
  const pct = k.ciAttesi ? Math.round((k.ciFatti / k.ciAttesi) * 100) : 0;

  $('#tab-body').innerHTML = `
    <div class="kpis">
      <div class="kpi kpi-blue">
        <div class="kpi-label">Persone online</div>
        <div class="kpi-value">${k.online}</div>
        <div class="kpi-foot">su ${k.totali} seguite</div>
      </div>
      <div class="kpi kpi-amber">
        <div class="kpi-label">Avvisi attivi</div>
        <div class="kpi-value">${k.avvisi}</div>
        <div class="kpi-foot">${k.avvisi ? 'da gestire' : 'nessuno'}</div>
      </div>
      <div class="kpi kpi-red">
        <div class="kpi-label">SOS oggi</div>
        <div class="kpi-value">${k.sosOggi}</div>
        <div class="kpi-foot">${k.sosOggi ? 'richiedono attenzione' : 'nessuno'}</div>
      </div>
      <div class="kpi kpi-green">
        <div class="kpi-label">Check-in confermati</div>
        <div class="kpi-value">${k.ciFatti}</div>
        <div class="kpi-foot">${k.ciAttesi ? 'su ' + k.ciAttesi + ' attesi oggi' : 'nessuno previsto'}</div>
      </div>
    </div>

    <div class="grid-2">
      <div class="panel" id="pannello-mappa">
        <div class="panel-head panel-head-click" onclick="alternaMappaGrande()">
          Mappa in tempo reale
          <span class="map-espandi" id="map-espandi">Ingrandisci \u2922</span>
        </div>
        <div class="panel-body flush"><div id="live-map"></div></div>
        <div class="map-note" id="map-note">Carico le posizioni…</div>
        <div id="viaggi-lista"></div>
      </div>
      <div class="panel">
        <div class="panel-head">
          Avvisi recenti
          <button class="panel-link" onclick="switchTab('avvisi')">Vedi tutti \u2192</button>
        </div>
        <div class="panel-body flush" id="avvisi-recenti"></div>
      </div>
    </div>

    <div class="grid-2">
      <div class="panel">
        <div class="panel-head">Check-in di oggi</div>
        <div class="panel-body">
          <div class="prog-head">
            <span>${k.ciFatti} / ${k.ciAttesi} completati</span>
            <span class="prog-pct">${pct}%</span>
          </div>
          <div class="prog-track"><div class="prog-fill" style="width:${pct}%"></div></div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-head">Prossimi check-in attesi</div>
        <div class="panel-body flush" id="prossimi-checkin"></div>
      </div>
    </div>`;

  // Lo stato ingrandito sopravvive al ridisegno automatico.
  if (mappaGrande) {
    const pannello = document.getElementById('pannello-mappa');
    if (pannello) pannello.classList.add('mappa-grande');
    const etichetta = document.getElementById('map-espandi');
    if (etichetta) etichetta.textContent = 'Riduci \u2921';
  }

  $('#avvisi-recenti').innerHTML = listaAvvisi(list, 4, false);
  $('#prossimi-checkin').innerHTML = listaProssimiCheckin(list);
  montaLiveMap();
}

// ── Avvisi ────────────────────────────────────────────────────────────

/**
 * Tutti gli avvisi in un elenco solo, ordinati per ora.
 *
 * Prima erano sparsi: gli SOS dentro la scheda della persona, le uscite
 * dall'area nella sua cronologia, i check-in mancati da nessuna parte. Per
 * accorgersene bisognava gia sapere chi guardare, che e il contrario di
 * quello che serve a chi sorveglia venti persone.
 */
function raccogliAvvisi(list, includiArchiviati) {
  const out = [];
  // La data di oggi entra nella chiave dei check-in: archiviare quello di
  // stamattina non deve nascondere quello di domani.
  const oggi = new Date().toISOString().slice(0, 10);

  list.forEach(p => {
    (p.last_sos_events || []).forEach(e => out.push({
      chiave: 'sos:' + e.id,
      tipo: 'SOS attivo', gravita: 'red', ico: '\u26A0',
      nome: p.name, dove: 'Allarme inviato dall\'app', quando: e.timestamp,
      preso: (e.acknowledged_by || []).length > 0,
      chi: (e.acknowledged_by || [])[0],
    }));
    if (p.geofence && p.geofence.last_event_type === 'exit') out.push({
      chiave: 'geofence:' + p.user_id + ':' + (p.geofence.last_event_at || ''),
      tipo: 'Uscita dal perimetro', gravita: 'amber', ico: '\u2299',
      nome: p.name, dove: 'Area concordata',
      quando: p.geofence.last_event_at || p.last_seen,
    });
    if (p.check_in && p.check_in.scheduled && !p.check_in.checked_in) out.push({
      chiave: 'checkin:' + p.user_id + ':' + oggi,
      tipo: 'Check-in non confermato', gravita: 'amber', ico: '\u2713',
      nome: p.name,
      dove: p.check_in.deadline_time ? 'Atteso entro le ' + p.check_in.deadline_time : 'In attesa',
      quando: null,
    });
    if (p.active_trip && p.active_trip.status === 'overdue') out.push({
      // Lo stato del viaggio nel riepilogo non porta l'id del viaggio, solo
      // stato e ultimo aggiornamento. La chiave usa persona + istante
      // dell'ultimo aggiornamento: identifica lo stesso viaggio scaduto in
      // modo stabile, e un viaggio successivo che scadesse avrebbe un
      // istante diverso, quindi un avviso nuovo.
      chiave: 'trip:' + p.user_id + ':' + (p.active_trip.last_update_at || ''),
      tipo: 'Viaggio scaduto', gravita: 'red', ico: '\u23F0',
      nome: p.name, dove: 'Nessuna conferma di arrivo',
      quando: p.active_trip.deadline_at,
    });
  });

  out.forEach(a => { a.archiviato = archiviati.has(a.chiave); });
  out.sort((a, b) => new Date(b.quando || 0) - new Date(a.quando || 0));
  return includiArchiviati ? out : out.filter(a => !a.archiviato);
}

function listaAvvisi(list, limite, selezionabile) {
  const avvisi = raccogliAvvisi(list, selezionabile && mostraArchiviati);
  if (!avvisi.length) {
    const testo = mostraArchiviati
      ? 'Nessun avviso, nemmeno fra gli archiviati.'
      : 'Nessun avviso. Va tutto bene.';
    return `<div class="panel-body"><div class="empty">${testo}</div></div>`;
  }
  return (limite ? avvisi.slice(0, limite) : avvisi).map(a => `
    <div class="alert-item ${a.archiviato ? 'alert-archiviato' : ''}">
      ${selezionabile ? `
        <input type="checkbox" class="alert-check" data-key="${escapeHtml(a.chiave)}"
               ${avvisiSelezionati.has(a.chiave) ? 'checked' : ''}
               onchange="segnaAvviso('${escapeHtml(a.chiave)}', this.checked)">` : ''}
      <span class="alert-ico ai-${a.gravita}">${a.ico}</span>
      <span class="alert-main">
        <span class="alert-kind ${a.gravita}">${escapeHtml(a.tipo)}</span>
        <div class="alert-who">${escapeHtml(a.nome)}</div>
        <div class="alert-where">${escapeHtml(a.dove)}</div>
        ${a.preso && a.chi
          ? `<div class="alert-where" style="color:#2E6B45;">\u2714 ${escapeHtml(a.chi.name)} se ne sta occupando</div>`
          : ''}
        ${a.archiviato ? '<div class="alert-where" style="font-style:italic;">Archiviato</div>' : ''}
      </span>
      <span class="alert-time">${a.quando ? escapeHtml(fmtQuando(a.quando)) : ''}</span>
    </div>`).join('');
}

function segnaAvviso(chiave, scelto) {
  if (scelto) avvisiSelezionati.add(chiave); else avvisiSelezionati.delete(chiave);
  aggiornaBarraSelezione();
}

function aggiornaBarraSelezione() {
  const barra = document.getElementById('barra-selezione');
  if (!barra) return;
  const n = avvisiSelezionati.size;
  barra.style.display = n ? 'flex' : 'none';
  const etichetta = document.getElementById('conta-selezione');
  if (etichetta) etichetta.textContent = n + (n === 1 ? ' avviso selezionato' : ' avvisi selezionati');
}

function selezionaTuttiAvvisi(scelto) {
  const visibili = raccogliAvvisi(state.overview || [], mostraArchiviati);
  visibili.forEach(a => {
    if (scelto) avvisiSelezionati.add(a.chiave); else avvisiSelezionati.delete(a.chiave);
  });
  disegnaAvvisi();
}

/**
 * Archivia gli avvisi selezionati.
 *
 * L'elenco si aggiorna subito, senza aspettare la risposta: il gesto e
 * sicuro e reversibile, e far attendere mezzo secondo per ogni riga
 * archiviata renderebbe faticoso proprio il caso in cui serve, cioe fare
 * ordine dopo giorni di avvisi accumulati.
 */
async function archiviaSelezionati() {
  const keys = Array.from(avvisiSelezionati);
  if (!keys.length) return;

  keys.forEach(k => archiviati.add(k));
  avvisiSelezionati.clear();
  disegnaAvvisi();
  renderShell(document.getElementById('tab-body').innerHTML);
  disegnaAvvisi();

  try {
    await api('/guardian-dashboard/alerts/dismiss', {
      method: 'POST', body: JSON.stringify({ keys }),
    });
  } catch (err) {
    // Rimessi in evidenza: se il server non ha registrato l'archiviazione,
    // lasciarli nascosti nella pagina significherebbe farli riapparire al
    // prossimo caricamento senza che nessuno capisca perche.
    keys.forEach(k => archiviati.delete(k));
    disegnaAvvisi();
    alert('Archiviazione non riuscita: ' + err.message);
  }
}

/** Riporta in evidenza quelli selezionati fra gli archiviati. */
async function ripristinaSelezionati() {
  const keys = Array.from(avvisiSelezionati);
  if (!keys.length) return;

  keys.forEach(k => archiviati.delete(k));
  avvisiSelezionati.clear();
  disegnaAvvisi();

  try {
    await api('/guardian-dashboard/alerts/restore', {
      method: 'POST', body: JSON.stringify({ keys }),
    });
  } catch (err) {
    keys.forEach(k => archiviati.add(k));
    disegnaAvvisi();
    alert('Operazione non riuscita: ' + err.message);
  }
}

function alternaArchiviati() {
  mostraArchiviati = !mostraArchiviati;
  avvisiSelezionati.clear();
  disegnaAvvisi();
}

function renderAvvisiTab() {
  renderShell('<div class="panel"><div class="panel-body"><div class="empty">Carico…</div></div></div>');
  if (state.overview) disegnaAvvisi();
  loadOverview();
}

function disegnaAvvisi() {
  const list = state.overview || [];
  const visibili = raccogliAvvisi(list, mostraArchiviati);
  const tuttiScelti = visibili.length > 0 && visibili.every(a => avvisiSelezionati.has(a.chiave));

  $('#tab-body').innerHTML = `
    <div class="panel">
      <div class="panel-head">
        ${mostraArchiviati ? 'Tutti gli avvisi, archiviati compresi' : 'Avvisi da gestire'}
        <button class="panel-link" onclick="alternaArchiviati()">
          ${mostraArchiviati ? 'Nascondi gli archiviati' : 'Mostra anche gli archiviati'}
        </button>
      </div>

      <div class="sel-bar">
        <label class="sel-all">
          <input type="checkbox" ${tuttiScelti ? 'checked' : ''}
                 onchange="selezionaTuttiAvvisi(this.checked)">
          Seleziona tutti
        </label>
        <button class="panel-link" onclick="switchTab('persone')">Apri le schede persona \u2192</button>
      </div>

      <div id="barra-selezione" class="azioni-bar" style="display:none;">
        <span id="conta-selezione"></span>
        ${mostraArchiviati
          ? `<button class="dev-btn" onclick="ripristinaSelezionati()">Rimetti in evidenza</button>`
          : ''}
        <button class="ack-btn" style="background:#8C7A72;" onclick="archiviaSelezionati()">
          Archivia selezionati
        </button>
      </div>

      <div class="panel-body flush">${listaAvvisi(list, null, true)}</div>
    </div>
    <div class="map-note" style="border:none;padding-left:0;">
      Archiviare toglie l'avviso da qui e dal numero rosso, ma non cancella
      nulla: l'evento resta in <a href="#" onclick="switchTab('storia');return false;">Storia
      eventi</a>, e vale solo per te — gli altri contatti continuano a vederlo.
      Per prendere in carico un allarme SOS e vederne posizione, batteria e
      video, apri la scheda della persona.
    </div>`;

  aggiornaBarraSelezione();
}

// ── Check-in ──────────────────────────────────────────────────────────

function listaProssimiCheckin(list) {
  const attesi = list.filter(p => p.check_in && p.check_in.scheduled && !p.check_in.checked_in);
  if (!attesi.length) {
    return '<div class="panel-body"><div class="empty">Nessun check-in in attesa.</div></div>';
  }
  return attesi.map(p => `
    <div class="pl-row">
      <span class="tutela-dot" style="background:#D97706"></span>
      <span>${escapeHtml(p.name)}</span>
      <span class="pl-when">${p.check_in.deadline_time ? 'Entro le ' + escapeHtml(p.check_in.deadline_time) : 'In attesa'}</span>
    </div>`).join('');
}

function renderCheckinTab() {
  renderShell('<div class="panel"><div class="panel-body"><div class="empty">Carico…</div></div></div>');
  if (state.overview) disegnaCheckin();
  loadOverview();
}

function disegnaCheckin() {
  const list = (state.overview || []).filter(p => p.check_in && p.check_in.scheduled);
  const fatti = list.filter(p => p.check_in.checked_in);
  const pct = list.length ? Math.round((fatti.length / list.length) * 100) : 0;

  const righe = list.map(p => {
    const ok = p.check_in.checked_in;
    return `<div class="pl-row">
      <span class="tutela-dot" style="background:${ok ? '#16A34A' : '#D97706'}"></span>
      <span>${escapeHtml(p.name)}</span>
      <span style="color:${ok ? '#16A34A' : '#D97706'};font-size:12.5px;margin-left:10px;">
        ${ok ? 'Confermato' : 'In attesa'}
      </span>
      <span class="pl-when">
        ${ok
          ? (p.check_in.checked_in_at ? 'alle ' + escapeHtml(fmtTime(p.check_in.checked_in_at)) : '')
          : (p.check_in.deadline_time ? 'entro le ' + escapeHtml(p.check_in.deadline_time) : '')}
      </span>
    </div>`;
  }).join('');

  $('#tab-body').innerHTML = `
    <div class="panel" style="margin-bottom:16px;">
      <div class="panel-head">Avanzamento di oggi</div>
      <div class="panel-body">
        <div class="prog-head">
          <span>${fatti.length} / ${list.length} confermati</span>
          <span class="prog-pct">${pct}%</span>
        </div>
        <div class="prog-track"><div class="prog-fill" style="width:${pct}%"></div></div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-head">Dettaglio per persona</div>
      <div class="panel-body flush">
        ${righe || '<div class="panel-body"><div class="empty">Nessun check-in concordato.</div></div>'}
      </div>
    </div>`;
}

// ── Perimetri ─────────────────────────────────────────────────────────

function renderGeofenceTab() {
  renderShell('<div class="panel"><div class="panel-body"><div class="empty">Carico\u2026</div></div></div>');
  caricaPerimetri();
}

// Stato dell'editor: persona scelta, area in disegno, mappa.
//
// Vive fuori dalle funzioni di disegno perche la sezione si ridisegna a ogni
// aggiornamento della panoramica: se centro e raggio stessero dentro,
// l'area che l'utente sta posizionando sparirebbe da sola dopo pochi
// secondi, che e il modo piu sicuro di far detestare uno strumento.
let gfStato = {
  dati: null,
  linkScelto: null,
  centro: null,
  raggio: 500,
  mappa: null,
  cerchi: [],
};

async function caricaPerimetri() {
  try {
    gfStato.dati = await api('/guardian-dashboard/geofence/zones');
  } catch (e) {
    $('#tab-body').innerHTML = '<div class="panel"><div class="panel-body">' +
      '<div class="empty">Perimetri non disponibili: ' + escapeHtml(e.message) + '</div></div></div>';
    return;
  }
  if (!gfStato.linkScelto && gfStato.dati.length) {
    gfStato.linkScelto = gfStato.dati[0].link_id;
  }
  disegnaGeofence();
}

function gfPersonaScelta() {
  return (gfStato.dati || []).find(p => p.link_id === gfStato.linkScelto) || null;
}

function disegnaGeofence() {
  const dati = gfStato.dati || [];

  if (!dati.length) {
    $('#tab-body').innerHTML = `
      <div class="panel">
        <div class="panel-head">Perimetri di sicurezza</div>
        <div class="panel-body">
          <div class="empty">Nessun collegamento per i perimetri.<br>
          Le aree si concordano con chi ti ha designato dall'app.</div>
        </div>
      </div>`;
    return;
  }

  const persona = gfPersonaScelta();

  const opzioni = dati.map(p =>
    `<option value="${escapeHtml(p.link_id)}" ${p.link_id === gfStato.linkScelto ? 'selected' : ''}>
       ${escapeHtml(p.name)}</option>`
  ).join('');

  const zone = (persona && persona.zones) || [];
  const righeZone = zone.map(z => {
    const attiva = z.status === 'active';
    const colore = attiva ? '#16A34A' : '#D97706';
    const stato = attiva
      ? 'Attiva'
      : (z.awaiting_my_response ? 'Proposta da confermare' : 'In attesa della sua conferma');
    const azioni = attiva
      ? `<button class="btn-mini" onclick="gfRevoca('${z.id}')">Revoca</button>`
      : (z.awaiting_my_response
          ? `<button class="btn-mini" onclick="gfAccetta('${z.id}')">Accetta</button>
             <button class="btn-mini" onclick="gfRifiuta('${z.id}')">Rifiuta</button>`
          : '');
    return `<div class="pl-row">
      <span class="tutela-dot" style="background:${colore}"></span>
      <span>${escapeHtml(z.name)}</span>
      <span style="color:${colore};font-size:12.5px;margin-left:10px;">${stato}</span>
      <span style="color:#6B7280;font-size:12.5px;margin-left:10px;">
        raggio ${z.radius_meters} m</span>
      <span class="pl-when">${azioni}</span>
    </div>`;
  }).join('');

  $('#tab-body').innerHTML = `
    <div class="panel">
      <div class="panel-head">Perimetri di sicurezza</div>
      <div class="panel-body">
        <label style="font-size:13px;color:#6B7280;">Persona</label>
        <select id="gf-persona" style="margin-left:8px;">${opzioni}</select>
        <div id="gf-map" style="height:420px;margin-top:12px;border-radius:10px;"></div>
        <div class="map-note" style="border:none;padding-left:0;">
          Clicca sulla mappa per posizionare il centro, poi regola il raggio.
        </div>
        <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:8px;">
          <input id="gf-nome" placeholder="Nome area (es. Casa)" maxlength="60" style="min-width:180px;">
          <label style="font-size:13px;color:#6B7280;">Raggio</label>
          <input id="gf-raggio" type="range" min="100" max="5000" step="50"
                 value="${gfStato.raggio}" style="width:220px;">
          <span id="gf-raggio-val" style="font-size:13px;">${gfStato.raggio} m</span>
          <button class="btn-mini" id="gf-proponi">Proponi area</button>
        </div>
        <div id="gf-esito" style="margin-top:8px;font-size:13px;"></div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-head">Aree di ${escapeHtml(persona ? persona.name : '')}</div>
      <div class="panel-body flush">
        ${righeZone || '<div class="panel-body"><div class="empty">Nessuna area concordata.</div></div>'}
      </div>
    </div>
    <div class="map-note" style="border:none;padding-left:0;">
      Nessuna area entra in vigore senza la conferma dell'altra parte: da qui
      si propone, la persona monitorata accetta dall'app. Massimo 5 aree fra
      attive e proposte. Riproporre un nome gi\u00e0 in uso sposta quell'area
      invece di crearne una seconda.
    </div>`;

  $('#gf-persona').onchange = (e) => {
    gfStato.linkScelto = e.target.value;
    gfStato.centro = null;
    disegnaGeofence();
  };
  $('#gf-raggio').oninput = (e) => {
    gfStato.raggio = parseInt(e.target.value, 10);
    $('#gf-raggio-val').textContent = gfStato.raggio + ' m';
    gfAggiornaDisegno();
  };
  $('#gf-proponi').onclick = gfProponi;

  montaMappaPerimetri();
}

async function montaMappaPerimetri() {
  const box = document.getElementById('gf-map');
  if (!box) return;
  try {
    await caricaLeaflet();
  } catch (e) {
    box.textContent = 'Mappa non disponibile: ' + e.message;
    return;
  }

  // La mappa si ricrea a ogni ridisegno della sezione: il riquadro di prima
  // non esiste piu, e riusare l'oggetto vecchio lascia un rettangolo grigio
  // (lo stesso inciampo gia visto sulla live map della panoramica).
  gfStato.mappa = L.map(box, { zoomControl: true });
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18, attribution: '&copy; OpenStreetMap',
  }).addTo(gfStato.mappa);

  const persona = gfPersonaScelta();
  const zone = (persona && persona.zones) || [];

  if (zone.length) {
    gfStato.mappa.setView([zone[0].center_lat, zone[0].center_lng], 14);
  } else {
    gfStato.mappa.setView([42.5, 12.5], 5);
  }

  gfStato.mappa.on('click', (ev) => {
    gfStato.centro = { lat: ev.latlng.lat, lng: ev.latlng.lng };
    gfAggiornaDisegno();
  });

  gfAggiornaDisegno();
}

/** Ridisegna le aree esistenti e quella in preparazione. */
function gfAggiornaDisegno() {
  if (!gfStato.mappa) return;
  gfStato.cerchi.forEach(c => gfStato.mappa.removeLayer(c));
  gfStato.cerchi = [];

  const persona = gfPersonaScelta();
  ((persona && persona.zones) || []).forEach(z => {
    const attiva = z.status === 'active';
    const c = L.circle([z.center_lat, z.center_lng], {
      radius: z.radius_meters,
      color: attiva ? '#16A34A' : '#D97706',
      // Le proposte tratteggiate, le attive piene: si distinguono a colpo
      // d'occhio anche da chi non legge la legenda.
      dashArray: attiva ? null : '6 6',
      fillOpacity: 0.12,
    }).addTo(gfStato.mappa);
    c.bindPopup('<strong>' + escapeHtml(z.name) + '</strong><br>' +
      (attiva ? 'Attiva' : 'Proposta') + ' \u00b7 ' + z.radius_meters + ' m');
    gfStato.cerchi.push(c);
  });

  if (gfStato.centro) {
    const nuovo = L.circle([gfStato.centro.lat, gfStato.centro.lng], {
      radius: gfStato.raggio,
      color: '#E2562B',
      fillOpacity: 0.18,
    }).addTo(gfStato.mappa);
    gfStato.cerchi.push(nuovo);
  }
}

function gfEsito(testo, errore) {
  const box = document.getElementById('gf-esito');
  if (box) {
    box.textContent = testo;
    box.style.color = errore ? '#B91C1C' : '#16A34A';
  }
}

async function gfProponi() {
  const persona = gfPersonaScelta();
  if (!persona) return;
  const nome = ($('#gf-nome').value || '').trim();
  if (!nome) { gfEsito('Dai un nome all\'area (es. Casa).', true); return; }
  if (!gfStato.centro) { gfEsito('Clicca sulla mappa per scegliere il centro.', true); return; }

  try {
    await api('/geofence/links/' + persona.link_id + '/zones', {
      method: 'POST',
      body: JSON.stringify({
        name: nome,
        center_lat: gfStato.centro.lat,
        center_lng: gfStato.centro.lng,
        radius_meters: gfStato.raggio,
      }),
    });
    gfStato.centro = null;
    gfEsito('Area proposta: ora tocca a ' + persona.name + ' accettarla dall\'app.', false);
    await caricaPerimetri();
  } catch (e) {
    gfEsito(e.message, true);
  }
}

async function gfAzioneZona(zoneId, percorso, messaggio) {
  try {
    await api('/geofence/zones/' + zoneId + '/' + percorso, { method: 'POST' });
    gfEsito(messaggio, false);
    await caricaPerimetri();
  } catch (e) {
    gfEsito(e.message, true);
  }
}

function gfAccetta(id) { gfAzioneZona(id, 'accept', 'Area accettata.'); }
function gfRifiuta(id) { gfAzioneZona(id, 'decline', 'Proposta rifiutata.'); }
function gfRevoca(id)  { gfAzioneZona(id, 'revoke', 'Area revocata.'); }

// ── Impostazioni ──────────────────────────────────────────────────────

function renderSettingsTab() {
  const notif = ('Notification' in window) ? Notification.permission : 'non supportate';
  const sbloccato = !!state.priv;

  renderShell(`
    <div class="panel" style="margin-bottom:16px;">
      <div class="panel-head">Notifiche del browser</div>
      <div class="panel-body">
        <p class="sub" style="margin-top:0;">
          Stato attuale: <strong>${escapeHtml(notif === 'granted' ? 'attive' : notif === 'denied' ? 'bloccate' : notif === 'default' ? 'non ancora attivate' : notif)}</strong>.
          Ricevi un avviso per ogni messaggio nuovo in qualunque conversazione e per gli
          allarmi, anche mentre guardi un'altra sezione o un'altra finestra. Arrivano solo
          mentre questa scheda &egrave; aperta: il browser non pu&ograve; avvisarti a pagina chiusa.
          Con la scheda in secondo piano da molto tempo, il browser pu&ograve; ritardarli fino a un minuto.
        </p>
        ${notif === 'denied'
          ? '<p class="sub">Le hai bloccate in passato: per riattivarle clicca il lucchetto accanto all\'indirizzo del sito e consenti le notifiche, poi ricarica la pagina.</p>'
          : notif === 'granted' ? '' :
          '<button class="dev-btn" onclick="requestNotificationPermission()">Attiva le notifiche</button>'}
      </div>
    </div>

    <div class="panel" style="margin-bottom:16px;">
      <div class="panel-head">Cifratura</div>
      <div class="panel-body">
        <p class="sub" style="margin-top:0;">
          ${sbloccato
            ? 'Sbloccata in questa scheda. La frase di recupero resta solo in memoria e sparisce chiudendo o ricaricando la pagina.'
            : 'Non sbloccata. Senza la frase di recupero i messaggi e gli allarmi restano illeggibili anche qui.'}
        </p>
        ${sbloccato ? '' : '<button class="dev-btn" onclick="switchTab(\'chat\')">Sblocca ora</button>'}
      </div>
    </div>

    <div class="panel">
      <div class="panel-head">Documenti</div>
      <div class="panel-body">
        <p class="sub" style="margin-top:0;">
          <a href="/legal/dashboard-privacy" target="_blank" rel="noopener">Informativa privacy</a> \u00b7
          <a href="/legal/cookies" target="_blank" rel="noopener">Informativa cookie</a> \u00b7
          <a href="/legal/terms" target="_blank" rel="noopener">Termini</a>
        </p>
      </div>
    </div>`);
}

// ── Storia eventi ─────────────────────────────────────────────────────

function renderStoriaTab() {
  renderShell('<div id="timeline-box"><div class="panel"><div class="panel-body"><div class="empty">Carico la cronologia…</div></div></div></div>');
  loadTimeline();
}

// ── Cronologia degli ultimi giorni ────────────────────────────────────

const TIMELINE_GIORNI = 5;

const TIMELINE_STILI = {
  sos:            { icona: '🆘', colore: '#D93025', titolo: 'Allarme SOS' },
  check_in:       { icona: '✅', colore: '#2E9E5B', titolo: 'Check-in confermato' },
  trip_arrived:   { icona: '🏁', colore: '#2E9E5B', titolo: 'Arrivato a destinazione' },
  trip_aborted:   { icona: '↩️', colore: '#8C7A72', titolo: 'Viaggio interrotto' },
  trip_overdue:   { icona: '⏰', colore: '#D93025', titolo: 'Viaggio scaduto' },
  geofence_exit:  { icona: '📤', colore: '#E08A1E', titolo: 'Uscito dall\'area' },
  geofence_enter: { icona: '📥', colore: '#2E9E5B', titolo: 'Rientrato nell\'area' },
};

async function loadTimeline() {
  const box = document.getElementById('timeline-box');
  if (!box) return;
  try {
    const data = await api('/guardian-dashboard/timeline?days=' + timelineGiorni);
    const eventi = data.events || [];
    timelineUltima = eventi;
    notificaEventiNuovi(eventi);
    box.innerHTML = renderTimeline(eventi, data.days);
  } catch (err) {
    // La cronologia e un di piu: se non arriva, il pannello deve restare
    // utilizzabile. Un errore qui non puo oscurare gli allarmi in corso,
    // che sono l'informazione per cui questa pagina esiste.
    box.innerHTML = `<div class="card"><div class="muted">Cronologia non disponibile: ${escapeHtml(err.message)}</div></div>`;
  }
}

/**
 * Avvisa degli eventi comparsi da quando la pagina e aperta.
 *
 * Come per gli SOS, il primo caricamento serve solo a registrare il punto
 * di partenza: annunciare come "nuovi" eventi di tre giorni fa, appena si
 * apre il pannello, sarebbe fuorviante e farebbe perdere fiducia in tutti
 * gli avvisi successivi.
 *
 * Gli allarmi SOS non passano di qui: hanno gia il loro avviso, con suono
 * e permanenza a schermo, e notificarli due volte li renderebbe piu
 * confusi anziche piu evidenti.
 */
function notificaEventiNuovi(eventi) {
  if (!timelineBaselineReady) {
    eventi.forEach(e => timelineSeen.add(e.id));
    timelineBaselineReady = true;
    return;
  }
  eventi.forEach(e => {
    if (timelineSeen.has(e.id)) return;
    timelineSeen.add(e.id);
    if (e.kind === 'sos') return;
    const stile = TIMELINE_STILI[e.kind];
    if (!stile) return;
    notifyTimelineEvent(stile.icona + ' ' + stile.titolo, e.name + ' — ' + (e.detail || ''));
  });
}

function renderTimeline(eventi, giorni) {
  if (!eventi.length) {
    return `<div class="card">
      <h3 style="margin:0 0 4px;">Ultimi ${giorni} giorni</h3>
      <div class="empty">Nessun evento registrato in questo periodo.</div>
    </div>`;
  }

  // Raggruppati per giorno: un elenco piatto di quaranta righe con la data
  // ripetuta accanto a ognuna si legge molto peggio di cinque blocchi.
  const perGiorno = new Map();
  eventi.forEach(e => {
    const chiave = new Date(e.occurred_at).toDateString();
    if (!perGiorno.has(chiave)) perGiorno.set(chiave, []);
    perGiorno.get(chiave).push(e);
  });

  const blocchi = [];
  for (const [, lista] of perGiorno) {
    const righe = lista.map(e => {
      const stile = TIMELINE_STILI[e.kind] || { icona: '•', colore: '#8C7A72', titolo: 'Evento' };
      const avatar = e.avatar_url
        ? `<img class="tl-avatar" src="${escapeHtml(e.avatar_url)}" alt="">`
        : `<span class="tl-avatar tl-initials">${escapeHtml(initials(e.name))}</span>`;
      return `<div class="tl-row">
        <span class="tl-time">${escapeHtml(fmtTime(e.occurred_at))}</span>
        <span class="tl-icon">${stile.icona}</span>
        ${avatar}
        <span class="tl-text">
          <strong>${escapeHtml(e.name)}</strong>
          <span style="color:${stile.colore};"> · ${escapeHtml(stile.titolo)}</span>
          ${e.detail ? `<span class="tl-detail">${escapeHtml(e.detail)}</span>` : ''}
        </span>
      </div>`;
    }).join('');

    blocchi.push(`<div class="tl-day">
      <div class="tl-day-label">${escapeHtml(fmtDayLabel(lista[0].occurred_at))}</div>
      ${righe}
    </div>`);
  }

  return `<div class="card" id="timeline-card">
    <div class="tl-head">
      <div>
        <h3 style="margin:0 0 4px;">Ultimi ${giorni} giorni</h3>
        <div class="muted">
          Allarmi, conferme di check-in, esiti dei viaggi e passaggi di area,
          con chi li ha generati.
        </div>
      </div>
      <div class="tl-actions no-print">
        <select id="tl-days" onchange="cambiaPeriodo(this.value)">
          <option value="5"${giorni === 5 ? ' selected' : ''}>5 giorni</option>
          <option value="7"${giorni === 7 ? ' selected' : ''}>7 giorni</option>
          <option value="14"${giorni === 14 ? ' selected' : ''}>14 giorni</option>
          <option value="30"${giorni === 30 ? ' selected' : ''}>30 giorni</option>
          <option value="90"${giorni === 90 ? ' selected' : ''}>90 giorni</option>
          <option value="365"${giorni === 365 ? ' selected' : ''}>1 anno</option>
        </select>
        <button onclick="stampaCronologia()">Stampa</button>
        <button onclick="scaricaCronologia()">Scarica CSV</button>
      </div>
    </div>
    ${blocchi.join('')}
  </div>`;
}

let timelineGiorni = TIMELINE_GIORNI;
let timelineUltima = [];

function cambiaPeriodo(giorni) {
  timelineGiorni = parseInt(giorni, 10) || TIMELINE_GIORNI;
  loadTimeline();
}

/**
 * Stampa la sola cronologia.
 *
 * Non e una comodita: un'azienda che usa Central per la tutela dei
 * lavoratori isolati deve poter DIMOSTRARE di averlo fatto. "Ha confermato
 * ogni giorno per tre mesi" su carta e cio che serve davanti a un
 * ispettorato o a un'assicurazione, e nessuno lo produce da uno schermo di
 * telefono.
 *
 * La stampa passa dal browser invece che da un PDF generato dal server:
 * i contenuti degli allarmi sono decifrati QUI e in nessun altro posto,
 * quindi un PDF costruito sul server non potrebbe contenerli comunque.
 */
function stampaCronologia() {
  document.body.classList.add('printing-timeline');
  window.print();
  setTimeout(() => document.body.classList.remove('printing-timeline'), 500);
}

/**
 * Esporta la cronologia in CSV.
 *
 * Il contenuto degli allarmi resta fuori: e cifrato, e un foglio di
 * calcolo che gira per posta elettronica e l'ultimo posto in cui deve
 * finire. Nel file ci sono data, persona e tipo di evento — cioe quello
 * che serve a dimostrare che il controllo e avvenuto, senza portarsi
 * dietro cosa e stato detto.
 */
function scaricaCronologia() {
  const righe = [['Data e ora', 'Persona', 'Evento', 'Dettaglio']];
  timelineUltima.forEach(e => {
    const stile = TIMELINE_STILI[e.kind] || { titolo: e.kind };
    righe.push([fmtDateTime(e.occurred_at), e.name, stile.titolo, e.detail || '']);
  });

  const csv = righe.map(r => r.map(c => {
    const v = (c === null || c === undefined) ? '' : String(c);
    // Le virgolette raddoppiate sono la fuga prevista dal formato: un nome
    // con una virgola dentro spezzerebbe altrimenti la riga in due colonne.
    return '"' + v.replace(/"/g, '""') + '"';
  }).join(',')).join('\r\n');

  // Il segno iniziale serve a Excel per riconoscere la codifica: senza,
  // le lettere accentate arrivano illeggibili, ed e la prima cosa che si
  // nota aprendo il file.
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'central-cronologia-' + new Date().toISOString().slice(0, 10) + '.csv';
  a.click();
  URL.revokeObjectURL(a.href);
}

/**
 * Apre gli allarmi SOS ricevuti.
 *
 * Non e una scorciatoia per leggere le conversazioni di chi si monitora:
 * un SOS e un messaggio indirizzato al guardiano e cifrato con la chiave
 * fra lui e chi lo ha inviato. Qui si apre solo quello, con la stessa
 * chiave che userebbe la sua app — nient'altro di quella chat.
 */
async function decorateSosCards(list) {
  for (const person of list) {
    if (!person.public_key) continue;
    let key;
    try {
      key = await sharedKeyFrom(state.priv, person.public_key);
      await registerMediaKey(key);
    } catch (e) { continue; }

    for (const event of person.last_sos_events || []) {
      const card = document.querySelector(`[data-sos="${event.id}"] .sos-body`);
      if (!card) continue;
      let sos = null;
      try {
        if (event.content && event.iv) {
          sos = safeJson(dec.decode(await aesDecrypt(key, b64ToBytes(event.iv), b64ToBytes(event.content))));
        }
      } catch (e) { /* resta il testo di fallback */ }

      if (!sos) { card.textContent = 'Contenuto non decifrabile con questa chiave.'; continue; }

      const position = (sos.lat != null && sos.lng != null)
        ? `<a href="https://www.openstreetmap.org/?mlat=${sos.lat}&mlon=${sos.lng}#map=16/${sos.lat}/${sos.lng}" target="_blank" rel="noopener">Apri la posizione sulla mappa</a>`
        : '<strong>Posizione non disponibile</strong> — il GPS non era attivo o raggiungibile';

      card.innerHTML = `
        <div>🔋 Batteria al ${escapeHtml(sos.battery_pct)}%</div>
        <div style="margin-top:6px;">📍 ${position}</div>
        ${event.media_url ? '<div class="sos-video" style="margin-top:6px;">Carico il video…</div>' : ''}`;

      if (event.media_url) {
        // La chiave del video sta dentro il JSON appena aperto (campo mk):
        // lo stesso file va a piu contatti, quindi non e cifrato con la
        // chiave di una singola chat.
        const resolved = await resolveMedia(event.media_url, sos.mk);
        const slot = card.querySelector('.sos-video');
        if (slot) {
          slot.innerHTML = resolved
            ? `<video src="${resolved}" controls></video>`
            : 'Video non disponibile.';
        }
      }
    }
  }
}
"""

_JS_MAPPE = r"""
// ══════════════════════════════════════════════════════════════════════
// MAPPE PERSONALIZZATE
// ══════════════════════════════════════════════════════════════════════
//
// La stessa mappa della conversazione che c'e nell'app (MapBoardScreen):
// punti d'interesse e ritrovi, cifrati con la chiave della chat. Si apre
// dalla card in chat o dal pulsante in alto nella conversazione.
//
// STESSE REGOLE DELL'APP
//
// - Una mappa per conversazione, chat 1:1 e gruppi senza differenze.
// - Non nasce da sola: alla prima apertura si chiede se crearla.
// - Si puo disattivare senza perdere niente, e riattivare.
// - Conta nelle mappe personalizzate del piano di chi la attiva: la regola
//   la applica il server (services/custom_maps.py), qui si mostra l'esito.
//
// FORMATI
//
// Devono coincidere byte per byte con l'app, o il telefono non legge quello
// che si scrive da qui:
// - punto:   elemento type="place", payload {lat, lng, title, description,
//            mediaUrl} cifrato come il testo (BoardPayload);
// - ritrovo: payload {lat, lng, radius, title, description, media_url}
//            (MapEventPayload: la copertina e "media_url", non "mediaUrl");
// - immagini: formato CEMD con la chiave della chat (cifraMedia).
//
// COSA NON SI PUO FARE DA QUI
//
// Dichiararsi presenti a un ritrovo e aggiungere foto alla sua cartella:
// la presenza la decide il telefono confrontando la propria posizione con
// l'area, e un computer non e "sul posto". La galleria invece si guarda.

const mp = {
  chatId: null,
  chat: null,
  board: null,
  vista: null,          // 'caricamento' | 'da_creare' | 'disattivata' | 'bloccata' | 'attiva' | 'errore'
  punti: [],
  eventi: [],
  mappa: null,
  livelli: [],
  timer: null,
  cercaTimer: null,
  segnaposto: null,     // punto scelto con un clic, in attesa di una scelta
  limite: null,         // mappe previste dal piano, per i testi
  inCorso: false,
};

const MP_ERRORI_STATO = ['map_inactive', 'map_locked', 'map_missing', 'map_exists'];

/** Come api(), ma non lancia: restituisce esito, codice e corpo. */
async function apiEsito(path, options = {}) {
  const opts = Object.assign({}, options);
  opts.headers = Object.assign({ 'Authorization': 'Bearer ' + state.token }, options.headers || {});
  if (opts.body && !(opts.body instanceof FormData) && !opts.headers['Content-Type']) {
    opts.headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(path, opts);
  if (res.status === 401) { logout(); throw new Error('Sessione scaduta'); }
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  return { ok: res.ok, status: res.status, data };
}

/** Frase leggibile da un esito fallito, compreso il limite del piano. */
function mpMessaggio(esito, predefinito) {
  const d = esito && esito.data && esito.data.detail;
  if (esito && esito.status === 402 && d && d.error === 'paywall') {
    const piano = d.required_plan_label || 'un piano superiore';
    return d.limit
      ? `Hai raggiunto il limite di ${d.limit} ${d.limit === 1 ? 'mappa personalizzata attiva' : 'mappe personalizzate attive'} del tuo abbonamento. ` +
        `Disattiva un'altra mappa oppure passa a ${piano} dall'app (Profilo → Impostazioni → Abbonamento).`
      : `Questa funzione è inclusa nel piano ${piano}.`;
  }
  if (d && typeof d === 'object' && d.message) return d.message;
  if (typeof d === 'string') return d;
  return predefinito;
}

function mpCodice(esito) {
  const d = esito && esito.data && esito.data.detail;
  return d && typeof d === 'object' ? d.code : null;
}

/** Chiave corrente della conversazione e versione, come per i messaggi. */
async function mpChiave() {
  const versions = await chatKeys(mp.chat);
  const version = mp.chat.type === 'group'
    ? (mp.chat.key_version || (versions.size ? Math.max(...versions.keys()) : null))
    : null;
  const key = pickKey(versions, version);
  if (!key) throw new Error('Chiave della conversazione non disponibile');
  await registerMediaKey(key);
  return { versions, version, key };
}

/** Cifra un oggetto JSON come i messaggi: {payload_encrypted, payload_iv}. */
async function mpCifraJson(key, oggetto) {
  // Senza i campi vuoti, come fa Gson nell'app.
  const pulito = {};
  Object.entries(oggetto).forEach(([k, v]) => { if (v !== null && v !== undefined && v !== '') pulito[k] = v; });
  const { iv, ciphertext } = await aesEncrypt(key, enc.encode(JSON.stringify(pulito)));
  return { payload_encrypted: bytesToB64(ciphertext), payload_iv: bytesToB64(iv) };
}

async function mpDecifraJson(versions, keyVersion, cipherB64, ivB64) {
  const key = pickKey(versions, keyVersion);
  if (!key || !cipherB64 || !ivB64) return null;
  try {
    return safeJson(dec.decode(await aesDecrypt(key, b64ToBytes(ivB64), b64ToBytes(cipherB64))));
  } catch (e) {
    return null;
  }
}

// ── Apertura e chiusura ───────────────────────────────────────────────

async function apriMappaPersonalizzata(chatId) {
  if (!state.priv) { switchTab('chat'); return; }
  const chat = (state.chats || []).find(c => c.id === chatId);
  if (!chat) return;

  chiudiMappa();
  mp.chatId = chatId;
  mp.chat = chat;

  const box = document.createElement('div');
  box.id = 'mp-overlay';
  box.className = 'mp-overlay';
  box.innerHTML = `
    <div class="mp-finestra">
      <div class="mp-testa">
        <div>
          <div class="mp-titolo">Mappa personalizzata</div>
          <div class="mp-sub">${escapeHtml(chatTitle(chat))}</div>
        </div>
        <div class="mp-azioni" id="mp-azioni"></div>
        <button class="mp-chiudi" onclick="chiudiMappa()" title="Chiudi (Esc)">&times;</button>
      </div>
      <div class="mp-corpo">
        <div class="mp-mappa-box"><div id="mp-mappa"></div>
          <div class="mp-velo" id="mp-velo"></div></div>
        <aside class="mp-lato" id="mp-lato"></aside>
      </div>
    </div>`;
  document.body.appendChild(box);
  document.addEventListener('keydown', mpTasto);

  try {
    await caricaLeaflet();
  } catch (e) {
    mpVelo('errore', 'Mappa non disponibile: ' + e.message);
    return;
  }

  mp.mappa = L.map('mp-mappa', { zoomControl: true });
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '&copy; OpenStreetMap',
  }).addTo(mp.mappa);
  mp.mappa.setView([42.5, 12.5], 5);
  mp.mappa.on('click', (e) => mpSceltaSulPunto(e.latlng));
  setTimeout(() => mp.mappa && mp.mappa.invalidateSize(), 60);

  mpLimitePiano();
  await mpCarica(true);
  // Stesso ritmo delle altre sezioni: un punto aggiunto dal telefono di un
  // altro partecipante compare qui senza ricaricare.
  mp.timer = setInterval(() => { if (mp.vista === 'attiva' && !mp.inCorso) mpCarica(false); }, 20000);
}

function chiudiMappa() {
  if (mp.timer) { clearInterval(mp.timer); mp.timer = null; }
  if (mp.mappa) { mp.mappa.remove(); mp.mappa = null; }
  document.removeEventListener('keydown', mpTasto);
  const box = document.getElementById('mp-overlay');
  if (box) box.remove();
  Object.assign(mp, { chatId: null, chat: null, board: null, vista: null, punti: [], eventi: [],
                      livelli: [], segnaposto: null, inCorso: false });
}

function mpTasto(e) {
  if (e.key !== 'Escape') return;
  // Esc chiude prima la galleria o il modulo aperto, poi la mappa.
  const galleria = document.getElementById('mp-galleria');
  if (galleria) { galleria.remove(); return; }
  if (document.querySelector('.mp-modulo')) { mpDisegnaLato(); return; }
  chiudiMappa();
}

/** Mappe previste dal piano: serve solo al testo della conferma. */
async function mpLimitePiano() {
  try {
    const diritti = await api('/billing/entitlements');
    mp.limite = diritti && diritti.quotas ? diritti.quotas.custom_maps : null;
    if (mp.vista === 'da_creare' || mp.vista === 'disattivata') mpDisegnaStato();
  } catch (e) { /* il testo resta generico */ }
}

function mpTestoQuota() {
  if (mp.limite === -1) return 'Il tuo abbonamento include mappe personalizzate illimitate.';
  if (mp.limite === 1) return 'Occuperà l\'unica mappa personalizzata inclusa nel tuo abbonamento.';
  if (mp.limite > 1) return `Occuperà una delle ${mp.limite} mappe personalizzate incluse nel tuo abbonamento.`;
  return 'Occuperà una delle mappe personalizzate incluse nel tuo abbonamento.';
}

// ── Stato della mappa ─────────────────────────────────────────────────

async function mpCarica(inquadra) {
  if (!mp.chatId) return;
  if (inquadra) mpVelo('caricamento', 'Carico la mappa…');

  const lista = await apiEsito('/boards/chat/' + encodeURIComponent(mp.chatId) + '?kind=map');
  if (!mp.chatId) return;
  if (!lista.ok) { mpVelo('errore', mpMessaggio(lista, 'Mappa non disponibile')); return; }

  mp.board = (lista.data || [])[0] || null;
  if (!mp.board) { mp.vista = 'da_creare'; mpPulisci(); mpDisegnaStato(); return; }
  if (mp.board.state === 'inactive') { mp.vista = 'disattivata'; mpPulisci(); mpDisegnaStato(); return; }
  if (mp.board.state === 'locked') { mp.vista = 'bloccata'; mpPulisci(); mpDisegnaStato(); return; }

  mp.vista = 'attiva';
  try {
    const { versions } = await mpChiave();
    const [dettaglio, eventi] = await Promise.all([
      apiEsito('/boards/' + encodeURIComponent(mp.board.id)),
      apiEsito('/map-events/chat/' + encodeURIComponent(mp.chatId)),
    ]);
    // Lo stato puo essere cambiato fra le due chiamate: un altro
    // partecipante l'ha disattivata, un downgrade l'ha bloccata.
    if (!dettaglio.ok) {
      if (MP_ERRORI_STATO.includes(mpCodice(dettaglio)) || dettaglio.status === 402) return mpCarica(inquadra);
      mpVelo('errore', mpMessaggio(dettaglio, 'Punti non caricati'));
      return;
    }

    mp.punti = [];
    for (const el of (dettaglio.data.elements || [])) {
      const pl = await mpDecifraJson(versions, el.key_version, el.payload_encrypted, el.payload_iv);
      // Senza coordinate un elemento non e collocabile: si salta, come
      // nell'app, invece di disegnarlo a caso.
      if (pl && typeof pl.lat === 'number' && typeof pl.lng === 'number') {
        mp.punti.push({ id: el.id, autore: el.author_id, aggiornato: el.updated_at, tipo: el.type, ...pl });
      }
    }

    mp.eventi = [];
    if (eventi.ok) {
      for (const ev of (eventi.data || [])) {
        const pl = await mpDecifraJson(versions, ev.key_version, ev.payload_encrypted, ev.payload_iv) || {};
        mp.eventi.push({ ...ev, pl });
      }
    }

    mpVelo(null);
    mpDisegnaMappa(inquadra);
    mpDisegnaAzioni();
    if (!document.querySelector('.mp-modulo')) mpDisegnaLato();
  } catch (e) {
    mpVelo('errore', e.message);
  }
}

function mpPulisci() {
  mp.punti = []; mp.eventi = [];
  if (mp.mappa) mp.livelli.forEach(l => mp.mappa.removeLayer(l));
  mp.livelli = [];
}

/** Velo sopra la mappa: caricamento, errore, o stato non attivo. */
function mpVelo(tipo, testo, htmlAzioni) {
  const velo = document.getElementById('mp-velo');
  if (!velo) return;
  if (!tipo) { velo.className = 'mp-velo'; velo.innerHTML = ''; return; }
  velo.className = 'mp-velo visibile';
  velo.innerHTML = `<div class="mp-velo-box">
      ${tipo === 'caricamento' ? '<div class="empty">' + escapeHtml(testo) + '</div>' : testo}
      ${htmlAzioni || ''}
    </div>`;
}

/** Prima creazione, mappa disattivata o bloccata dal piano. */
function mpDisegnaStato() {
  mpDisegnaAzioni();
  mpDisegnaLato();
  const indietro = '<button class="ghost" onclick="chiudiMappa()">Torna alla conversazione</button>';

  if (mp.vista === 'da_creare') {
    mpVelo('stato', `<h3>Creare la mappa?</h3>
      <p>Questa conversazione non ha ancora una mappa personalizzata. Creandola, tutti i
      partecipanti potranno aggiungere punti e ritrovi, dall'app e da qui.</p>
      <p class="mp-nota">${escapeHtml(mpTestoQuota())}</p>`,
      `<div class="mp-velo-azioni">${indietro}
         <button class="primary-sm" id="mp-crea" onclick="mpCrea()">Crea mappa</button></div>`);
  } else if (mp.vista === 'disattivata') {
    mpVelo('stato', `<h3>Mappa disattivata</h3>
      <p>La mappa di questa conversazione è spenta. Punti, ritrovi e foto sono conservati
      e tornano riattivandola.</p>
      <p class="mp-nota">${escapeHtml(mpTestoQuota())}</p>`,
      `<div class="mp-velo-azioni">${indietro}
         <button class="primary-sm" id="mp-attiva" onclick="mpAttiva()">Riattiva mappa</button></div>`);
  } else if (mp.vista === 'bloccata') {
    const mia = state.me && mp.board && mp.board.active_by === state.me.id;
    mpVelo('stato', mia
      ? `<h3>Limite di mappe raggiunto</h3>
         <p>Hai più mappe attive di quelle previste dal tuo abbonamento, e questa è oltre
         il limite. Disattiva un'altra mappa oppure passa a un piano superiore dall'app per
         tornare a usarla. Il contenuto non è stato cancellato.</p>`
      : `<h3>Mappa bloccata</h3>
         <p>Questa mappa supera il numero di mappe previsto dall'abbonamento di chi l'ha
         attivata. Puoi riattivarla tu: occuperà una mappa del tuo abbonamento.</p>`,
      `<div class="mp-velo-azioni">${indietro}
         ${mia ? '<button class="ghost" onclick="mpCarica(true)">Riprova</button>'
               : '<button class="primary-sm" id="mp-attiva" onclick="mpAttiva()">Riattiva a mio nome</button>'}
       </div>`);
  }
}

function mpErroreVelo(testo) {
  const box = document.querySelector('.mp-velo-box');
  if (!box) { alert(testo); return; }
  let err = box.querySelector('.error-box');
  if (!err) { err = document.createElement('div'); err.className = 'error-box'; box.appendChild(err); }
  err.textContent = testo;
}

async function mpCrea() {
  if (mp.inCorso) return;
  mp.inCorso = true;
  const btn = document.getElementById('mp-crea');
  if (btn) { btn.disabled = true; btn.textContent = 'Creazione…'; }
  try {
    const { key, version } = await mpChiave();
    // Il titolo e cifrato come tutto il resto ma non viene mai mostrato:
    // serve solo perche il server lo richiede. Stesso testo dell'app.
    const { iv, ciphertext } = await aesEncrypt(key, enc.encode('Mappa personalizzata'));
    const esito = await apiEsito('/boards/chat/' + encodeURIComponent(mp.chatId), {
      method: 'POST',
      body: JSON.stringify({
        title_encrypted: bytesToB64(ciphertext), title_iv: bytesToB64(iv),
        key_version: version, kind: 'map', position: 0,
      }),
    });
    if (!esito.ok && mpCodice(esito) !== 'map_exists') {
      mpErroreVelo(mpMessaggio(esito, 'Mappa non creata'));
      if (btn) { btn.disabled = false; btn.textContent = 'Crea mappa'; }
      return;
    }
    await mpCarica(true);
  } catch (e) {
    mpErroreVelo(e.message);
    if (btn) { btn.disabled = false; btn.textContent = 'Crea mappa'; }
  } finally {
    mp.inCorso = false;
  }
}

async function mpAttiva() {
  if (mp.inCorso || !mp.board) return;
  mp.inCorso = true;
  const btn = document.getElementById('mp-attiva');
  if (btn) { btn.disabled = true; btn.textContent = 'Riattivazione…'; }
  try {
    const esito = await apiEsito('/boards/' + encodeURIComponent(mp.board.id) + '/activate', { method: 'POST' });
    if (!esito.ok) {
      mpErroreVelo(mpMessaggio(esito, 'Mappa non riattivata'));
      if (btn) { btn.disabled = false; btn.textContent = 'Riprova'; }
      return;
    }
    await mpCarica(true);
  } finally {
    mp.inCorso = false;
  }
}

async function mpDisattiva() {
  if (!mp.board || mp.inCorso) return;
  const ok = confirm(
    'Disattivare la mappa?\n\n' +
    'Non sarà più usabile da nessun partecipante e non conterà più tra le mappe del tuo abbonamento.\n\n' +
    'Punti, ritrovi e foto NON vengono cancellati: tornano tutti riattivando la mappa.'
  );
  if (!ok) return;
  mp.inCorso = true;
  try {
    const esito = await apiEsito('/boards/' + encodeURIComponent(mp.board.id) + '/deactivate', { method: 'POST' });
    if (!esito.ok) { alert(mpMessaggio(esito, 'Mappa non disattivata')); return; }
    mp.board = esito.data;
    mp.vista = 'disattivata';
    mpPulisci();
    mpDisegnaStato();
  } finally {
    mp.inCorso = false;
  }
}

function mpDisegnaAzioni() {
  const box = document.getElementById('mp-azioni');
  if (!box) return;
  if (mp.vista !== 'attiva') { box.innerHTML = ''; return; }
  box.innerHTML = `
    <button class="ghost" onclick="mpCarica(false)" title="Aggiorna">&#8635; Aggiorna</button>
    ${mp.board && mp.board.can_deactivate
      ? '<button class="ghost mp-disattiva" onclick="mpDisattiva()">Disattiva mappa</button>' : ''}`;
}

// ── Disegno sulla mappa ───────────────────────────────────────────────

function mpSpillo(colore, simbolo) {
  return L.divIcon({
    className: '',
    html: `<svg width="30" height="40" viewBox="0 0 30 40" xmlns="http://www.w3.org/2000/svg">
      <path d="M15 39C15 39 28 23.5 28 14A13 13 0 1 0 2 14c0 9.5 13 25 13 25z"
            fill="${colore}" stroke="#fff" stroke-width="2.5"/>
      <text x="15" y="19" text-anchor="middle" font-size="12" fill="#fff"
            font-family="system-ui,sans-serif">${simbolo || ''}</text>
    </svg>`,
    iconSize: [30, 40], iconAnchor: [15, 39], popupAnchor: [0, -34],
  });
}

/** Punto con foto: tondo con dentro l'immagine, come nell'app. */
function mpTondoFoto(src) {
  return L.divIcon({
    className: '',
    html: `<div class="mp-tondo"><img src="${src}" alt=""></div>`,
    iconSize: [44, 44], iconAnchor: [22, 22], popupAnchor: [0, -20],
  });
}

function mpDisegnaMappa(inquadra) {
  if (!mp.mappa) return;
  mp.livelli.forEach(l => mp.mappa.removeLayer(l));
  mp.livelli = [];
  const coords = [];

  // Ritrovi: area sul terreno (il cerchio di Leaflet e in metri, quindi
  // resta fedele a ogni zoom come il poligono dell'app) e segnaposto al
  // centro, cartella se la cartella condivisa e gia aperta.
  mp.eventi.forEach(ev => {
    const p = ev.pl;
    if (typeof p.lat !== 'number' || typeof p.lng !== 'number') return;
    const colore = ev.in_corso ? '#E2562B' : '#9CA3AF';
    if (p.radius) {
      const area = L.circle([p.lat, p.lng], {
        radius: p.radius, color: colore, weight: 1.5,
        fillColor: colore, fillOpacity: ev.in_corso ? 0.16 : 0.08,
        // Senza, il clic sull'area arriverebbe anche alla mappa e aprirebbe
        // "cosa vuoi aggiungere qui?" sopra la scheda del ritrovo.
        bubblingMouseEvents: false,
      }).addTo(mp.mappa);
      area.on('click', () => mpApriRitrovo(ev.id));
      mp.livelli.push(area);
    }
    const m = L.marker([p.lat, p.lng], {
      icon: mpSpillo(ev.in_corso ? '#E2562B' : '#8C7A72', ev.folder_opened_at ? '&#128193;' : '&#9733;'),
      zIndexOffset: 200,
    }).addTo(mp.mappa);
    m.on('click', () => mpApriRitrovo(ev.id));
    m.bindTooltip(escapeHtml(p.title || 'Ritrovo'));
    mp.livelli.push(m);
    coords.push([p.lat, p.lng]);
  });

  // Percorsi: linea colorata sul terreno, con fumetto come i punti.
  mp.punti.filter(mpEPercorso).forEach(pt => {
    const tratto = pt.route.map(p => [p[0], p[1]]);
    const linea = L.polyline(tratto, { color: mpColorePercorso(pt), weight: 5, opacity: 0.9 }).addTo(mp.mappa);
    linea.bindTooltip(escapeHtml(pt.title || 'Percorso'));
    linea.bindPopup(() => mpFumettoPercorso(pt), { maxWidth: 280 });
    linea._mpId = pt.id;
    mp.livelli.push(linea);
    tratto.forEach(c => coords.push(c));
  });

  // Punti d'interesse: tondo con la foto se c'e, spillo altrimenti.
  mp.punti.filter(pt => !mpEPercorso(pt)).forEach(pt => {
    const m = L.marker([pt.lat, pt.lng], { icon: mpSpillo('#EA5B2E', '') }).addTo(mp.mappa);
    m.bindTooltip(escapeHtml(pt.title || 'Punto'));
    m.bindPopup(() => mpFumettoPunto(pt), { maxWidth: 280 });
    m._mpId = pt.id;
    mp.livelli.push(m);
    coords.push([pt.lat, pt.lng]);
    if (pt.mediaUrl) {
      resolveMedia(pt.mediaUrl).then(src => {
        if (src && mp.mappa && mp.mappa.hasLayer(m)) m.setIcon(mpTondoFoto(src));
      });
    }
  });

  if (inquadra && coords.length) {
    mp.mappa.fitBounds(L.latLngBounds(coords).pad(0.2));
    if (mp.mappa.getZoom() > 16) mp.mappa.setZoom(16);
  }
}

/** Percorso disegnato nell'app: elemento "route" con almeno due tappe. */
function mpEPercorso(pt) {
  return pt.tipo === 'route' && Array.isArray(pt.route) && pt.route.length >= 2 &&
    pt.route.every(p => Array.isArray(p) && typeof p[0] === 'number' && typeof p[1] === 'number');
}

/** Colore del percorso: solo #RRGGBB, altrimenti quello predefinito. */
function mpColorePercorso(pt) {
  return /^#[0-9a-fA-F]{6}$/.test(pt.color || '') ? pt.color : '#2E7DD7';
}

function mpDistanzaPercorso(pt) {
  let m = 0;
  for (let i = 1; i < pt.route.length; i++) {
    m += L.latLng(pt.route[i - 1][0], pt.route[i - 1][1]).distanceTo(L.latLng(pt.route[i][0], pt.route[i][1]));
  }
  return m < 1000 ? Math.round(m) + ' m' : (m / 1000).toFixed(1).replace('.', ',') + ' km';
}

function mpFumettoPercorso(pt) {
  const div = document.createElement('div');
  div.className = 'mp-fumetto';
  div.innerHTML = `
    <strong>${escapeHtml(pt.title || 'Percorso')}</strong>
    <div class="mp-nota">${escapeHtml(mpDistanzaPercorso(pt))} · ${pt.route.length} tappe</div>
    ${pt.description ? `<p>${escapeHtml(pt.description)}</p>` : ''}
    <div class="mp-fumetto-azioni">
      ${mpPuoEliminare(pt) ? `<button class="mp-link-rosso" onclick="mpEliminaPunto('${escapeHtml(pt.id)}')">Elimina</button>` : ''}
    </div>`;
  return div;
}

function mpPuoEliminare(pt) {
  // Stessa regola del server (_can_delete_element): i propri punti, e
  // tutti per chi ha creato la mappa. Gli amministratori del gruppo li
  // accetta il server anche se qui il pulsante non compare.
  if (!state.me) return false;
  return pt.autore === state.me.id || !pt.autore || (mp.board && mp.board.created_by === state.me.id);
}

function mpFumettoPunto(pt) {
  const div = document.createElement('div');
  div.className = 'mp-fumetto';
  div.innerHTML = `
    <strong>${escapeHtml(pt.title || 'Punto d\'interesse')}</strong>
    ${pt.description ? `<p>${escapeHtml(pt.description)}</p>` : ''}
    ${pt.mediaUrl ? '<div class="mp-fumetto-foto"><span class="locked">Caricamento…</span></div>' : ''}
    <div class="mp-fumetto-azioni">
      <a href="https://www.openstreetmap.org/directions?to=${pt.lat}%2C${pt.lng}" target="_blank" rel="noopener">Indicazioni</a>
      ${mpPuoEliminare(pt) ? `<button class="mp-link-rosso" onclick="mpEliminaPunto('${escapeHtml(pt.id)}')">Elimina</button>` : ''}
    </div>`;
  if (pt.mediaUrl) {
    resolveMedia(pt.mediaUrl).then(src => {
      const slot = div.querySelector('.mp-fumetto-foto');
      if (slot) slot.innerHTML = src
        ? `<img src="${src}" alt="" style="cursor:zoom-in" onclick="apriVisore('${src}')">`
        : '<span class="locked">Immagine non disponibile</span>';
    });
  }
  return div;
}

async function mpEliminaPunto(id) {
  if (!confirm('Eliminare questo punto dalla mappa per tutti i partecipanti?')) return;
  const esito = await apiEsito('/boards/' + encodeURIComponent(mp.board.id) + '/elements/' + encodeURIComponent(id),
                               { method: 'DELETE' });
  if (!esito.ok) {
    alert(mpMessaggio(esito, 'Punto non eliminato'));
    if (MP_ERRORI_STATO.includes(mpCodice(esito))) mpCarica(true);
    return;
  }
  mp.mappa.closePopup();
  mp.punti = mp.punti.filter(p => p.id !== id);
  mpDisegnaMappa(false);
  mpDisegnaLato();
}

// ── Pannello laterale: ricerca, elenco, moduli ────────────────────────

/**
 * Leaflet non si accorge da solo che il riquadro ha cambiato larghezza:
 * quando il pannello laterale compare o sparisce, la mappa restava con le
 * misure vecchie e un clic al centro finiva centinaia di chilometri piu in
 * la. Si ricalcola dopo ogni cambio del pannello.
 */
function mpRicalcolaMisure() {
  if (mp.mappa) setTimeout(() => mp.mappa && mp.mappa.invalidateSize(), 0);
}

function mpDisegnaLato() {
  const lato = document.getElementById('mp-lato');
  if (!lato) return;
  mpRicalcolaMisure();
  if (mp.vista !== 'attiva') { lato.innerHTML = ''; return; }

  const fmtPeriodo = ev => `${fmtDateTime(ev.starts_at)} → ${fmtDateTime(ev.ends_at)}`;
  const eventi = mp.eventi.map(ev => `
    <div class="mp-voce" onclick="mpApriRitrovo('${escapeHtml(ev.id)}')">
      <span class="mp-voce-ico">${ev.folder_opened_at ? '&#128193;' : '&#9733;'}</span>
      <span class="mp-voce-testo"><strong>${escapeHtml(ev.pl.title || 'Ritrovo')}</strong>
        <span>${ev.in_corso ? '<b class="mp-in-corso">In corso</b> · ' : ''}${escapeHtml(fmtPeriodo(ev))}</span></span>
    </div>`).join('');
  const percorsi = mp.punti.filter(mpEPercorso).map(pt => `
    <div class="mp-voce" onclick="mpVaiAlPunto('${escapeHtml(pt.id)}')">
      <span class="mp-voce-ico">&#12336;</span>
      <span class="mp-voce-testo"><strong>${escapeHtml(pt.title || 'Percorso')}</strong>
        <span>${escapeHtml(mpDistanzaPercorso(pt))}</span></span>
    </div>`).join('');
  const soloPunti = mp.punti.filter(pt => !mpEPercorso(pt));
  const punti = soloPunti.map(pt => `
    <div class="mp-voce" onclick="mpVaiAlPunto('${escapeHtml(pt.id)}')">
      <span class="mp-voce-ico">&#128205;</span>
      <span class="mp-voce-testo"><strong>${escapeHtml(pt.title || 'Punto d\'interesse')}</strong>
        ${pt.description ? `<span>${escapeHtml(pt.description)}</span>` : ''}</span>
    </div>`).join('');

  lato.innerHTML = `
    <div class="mp-cerca">
      <input type="text" id="mp-cerca" placeholder="Cerca un indirizzo o un luogo…" autocomplete="off">
      <div class="mp-risultati" id="mp-risultati"></div>
    </div>
    <div class="mp-aiuto">Fai clic sulla mappa per aggiungere un punto d'interesse o creare un ritrovo.</div>
    <div class="mp-sezione">Ritrovi (${mp.eventi.length})</div>
    ${eventi || '<div class="mp-vuoto">Nessun ritrovo.</div>'}
    <div class="mp-sezione">Punti d'interesse (${soloPunti.length})</div>
    ${punti || '<div class="mp-vuoto">Nessun punto. Fai clic sulla mappa per aggiungerne uno.</div>'}
    ${percorsi ? `<div class="mp-sezione">Percorsi (${mp.punti.length - soloPunti.length})</div>${percorsi}
      <div class="mp-aiuto">I percorsi si disegnano dall'app.</div>` : ''}`;

  const input = document.getElementById('mp-cerca');
  input.addEventListener('input', () => mpCercaIndirizzo(input.value));
}

/**
 * Ricerca indirizzi con Nominatim (OpenStreetMap).
 *
 * L'app usa Mapbox con la chiave dell'app, che nel browser non c'e. La
 * mappa qui e gia OpenStreetMap, quindi lo e anche la ricerca. Le regole
 * d'uso di Nominatim chiedono al massimo una richiesta al secondo: si
 * cerca solo quando si smette di scrivere, e mai sotto i tre caratteri.
 *
 * Cosa si cerca finisce a OpenStreetMap, come le tessere della mappa; i
 * punti e i ritrovi della conversazione no, quelli restano cifrati.
 */
function mpCercaIndirizzo(testo) {
  if (mp.cercaTimer) clearTimeout(mp.cercaTimer);
  const box = document.getElementById('mp-risultati');
  if (!box) return;
  if ((testo || '').trim().length < 3) { box.innerHTML = ''; return; }
  mp.cercaTimer = setTimeout(async () => {
    box.innerHTML = '<div class="mp-vuoto">Cerco…</div>';
    try {
      const b = mp.mappa.getBounds();
      const url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&limit=6&accept-language=it'
        + '&q=' + encodeURIComponent(testo.trim())
        + '&viewbox=' + [b.getWest(), b.getNorth(), b.getEast(), b.getSouth()].join(',');
      const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
      const risultati = res.ok ? await res.json() : [];
      mp.risultati = risultati;
      box.innerHTML = risultati.length
        ? risultati.map((r, i) => `<div class="mp-risultato" onclick="mpScegliRisultato(${i})">${escapeHtml(r.display_name)}</div>`).join('')
        : '<div class="mp-vuoto">Nessun risultato.</div>';
    } catch (e) {
      box.innerHTML = '<div class="mp-vuoto">Ricerca non disponibile.</div>';
    }
  }, 900);
}

function mpScegliRisultato(i) {
  const r = (mp.risultati || [])[i];
  if (!r) return;
  const box = document.getElementById('mp-risultati');
  if (box) box.innerHTML = '';
  const latlng = L.latLng(parseFloat(r.lat), parseFloat(r.lon));
  mp.mappa.setView(latlng, 17);
  mpSceltaSulPunto(latlng, r.display_name);
}

function mpVaiAlPunto(id) {
  const pt = mp.punti.find(p => p.id === id);
  if (!pt) return;
  if (mpEPercorso(pt)) {
    mp.mappa.fitBounds(L.latLngBounds(pt.route.map(p => [p[0], p[1]])).pad(0.2));
  } else {
    mp.mappa.setView([pt.lat, pt.lng], Math.max(mp.mappa.getZoom(), 16));
  }
  const m = mp.livelli.find(l => l._mpId === id);
  if (m) m.openPopup();
}

/** Clic sulla mappa: come la pressione prolungata dell'app, si chiede cosa creare. */
function mpSceltaSulPunto(latlng, etichetta) {
  if (mp.vista !== 'attiva' || !mp.mappa) return;
  mp.segnaposto = { lat: latlng.lat, lng: latlng.lng, etichetta: etichetta || '' };
  const div = document.createElement('div');
  div.className = 'mp-fumetto';
  div.innerHTML = `
    ${etichetta ? `<div class="mp-nota">${escapeHtml(etichetta)}</div>` : ''}
    <strong>Cosa vuoi aggiungere qui?</strong>
    <div class="mp-scelta">
      <button class="ghost" onclick="mpModuloPunto()">&#128205; Punto d'interesse</button>
      <button class="ghost" onclick="mpModuloRitrovo()">&#9733; Ritrovo</button>
    </div>`;
  L.popup({ maxWidth: 260 }).setLatLng(latlng).setContent(div).openOn(mp.mappa);
}

function mpModuloPunto() {
  if (!mp.segnaposto) return;
  mp.mappa.closePopup();
  const lato = document.getElementById('mp-lato');
  lato.innerHTML = `
    <div class="mp-modulo">
      <h3>Nuovo punto d'interesse</h3>
      <label>Titolo</label>
      <input type="text" id="mp-p-titolo" maxlength="120" value="${escapeHtml(mp.segnaposto.etichetta.split(',')[0] || '')}">
      <label>Descrizione</label>
      <textarea id="mp-p-descr" rows="4" maxlength="1000" placeholder="Indicazioni, orari, note…"></textarea>
      <label>Immagine (facoltativa)</label>
      <input type="file" id="mp-p-foto" accept="image/jpeg,image/png,image/webp">
      <div class="mp-nota">L'immagine viene cifrata nel browser con la chiave della conversazione.</div>
      <div class="error-box" id="mp-errore" style="display:none"></div>
      <div class="mp-velo-azioni">
        <button class="ghost" onclick="mpDisegnaLato()">Annulla</button>
        <button class="primary-sm" id="mp-salva" onclick="mpSalvaPunto()">Salva punto</button>
      </div>
    </div>`;
  document.getElementById('mp-p-titolo').focus();
}

function mpModuloRitrovo() {
  if (!mp.segnaposto) return;
  mp.mappa.closePopup();
  // Inizio proposto: adesso, arrotondato al quarto d'ora successivo.
  const inizio = new Date(Math.ceil(Date.now() / 900000) * 900000);
  const locale = new Date(inizio.getTime() - inizio.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  const lato = document.getElementById('mp-lato');
  lato.innerHTML = `
    <div class="mp-modulo">
      <h3>Nuovo ritrovo</h3>
      <label>Nome del ritrovo</label>
      <input type="text" id="mp-r-titolo" maxlength="120">
      <label>Descrizione</label>
      <textarea id="mp-r-descr" rows="3" maxlength="1000"></textarea>
      <label>Inizio</label>
      <input type="datetime-local" id="mp-r-inizio" value="${locale}">
      <label>Durata: <b id="mp-r-ore-v">4 ore</b></label>
      <input type="range" id="mp-r-ore" min="1" max="48" value="4"
             oninput="document.getElementById('mp-r-ore-v').textContent = this.value + (this.value === '1' ? ' ora' : ' ore')">
      <label>Area: <b id="mp-r-raggio-v">300 m</b></label>
      <input type="range" id="mp-r-raggio" min="100" max="2000" step="50" value="300"
             oninput="document.getElementById('mp-r-raggio-v').textContent = this.value + ' m'; mpAnteprimaArea()">
      <label>Copertina (facoltativa)</label>
      <input type="file" id="mp-r-foto" accept="image/jpeg,image/png,image/webp">
      <div class="mp-nota">Per dichiararsi presenti e aggiungere foto alla cartella del ritrovo si usa l'app, sul posto.</div>
      <div class="error-box" id="mp-errore" style="display:none"></div>
      <div class="mp-velo-azioni">
        <button class="ghost" onclick="mpAnnullaRitrovo()">Annulla</button>
        <button class="primary-sm" id="mp-salva" onclick="mpSalvaRitrovo()">Crea ritrovo</button>
      </div>
    </div>`;
  mpAnteprimaArea();
  document.getElementById('mp-r-titolo').focus();
}

/** Cerchio tratteggiato mentre si sceglie il raggio del ritrovo. */
function mpAnteprimaArea() {
  if (mp.anteprima) { mp.mappa.removeLayer(mp.anteprima); mp.anteprima = null; }
  const r = document.getElementById('mp-r-raggio');
  if (!r || !mp.segnaposto) return;
  mp.anteprima = L.circle([mp.segnaposto.lat, mp.segnaposto.lng], {
    radius: parseInt(r.value, 10), color: '#E2562B', dashArray: '6 6', weight: 2, fillOpacity: 0.08,
  }).addTo(mp.mappa);
}

function mpAnnullaRitrovo() {
  if (mp.anteprima) { mp.mappa.removeLayer(mp.anteprima); mp.anteprima = null; }
  mpDisegnaLato();
}

function mpErroreModulo(testo) {
  const e = document.getElementById('mp-errore');
  if (e) { e.style.display = ''; e.textContent = testo; } else alert(testo);
  const btn = document.getElementById('mp-salva');
  if (btn) { btn.disabled = false; btn.textContent = btn.dataset.testo || btn.textContent; }
}

/** Cifra e carica un'immagine con la chiave della chat. */
async function caricaFileCifrato(key, file) {
  if (file.size > MAX_ALLEGATO_BYTES) throw new Error('Il file supera i 50 MB');
  const cifrato = await cifraMedia(key, new Uint8Array(await file.arrayBuffer()));
  const form = new FormData();
  form.append('file', new Blob([cifrato], { type: 'application/octet-stream' }), 'upload.bin');
  form.append('encrypted', 'true');
  const res = await apiRaw('/api/media/upload', { method: 'POST', body: form });
  if (!res.ok) {
    const corpo = await res.json().catch(() => ({}));
    throw new Error((corpo.detail || 'Caricamento non riuscito') + ' (' + file.name + ')');
  }
  const { media_url } = await res.json();
  // Il file in chiaro e gia qui: lo si mostra senza riscaricarlo.
  mediaCache.set(media_url, URL.createObjectURL(file));
  return media_url;
}

async function mpSalvaPunto() {
  if (mp.inCorso || !mp.segnaposto) return;
  const titolo = document.getElementById('mp-p-titolo').value.trim();
  const descrizione = document.getElementById('mp-p-descr').value.trim();
  const foto = document.getElementById('mp-p-foto').files[0];
  if (!titolo) { mpErroreModulo('Dai un titolo al punto.'); return; }

  const btn = document.getElementById('mp-salva');
  btn.dataset.testo = btn.textContent; btn.disabled = true; btn.textContent = 'Salvataggio…';
  mp.inCorso = true;
  try {
    const { key, version } = await mpChiave();
    let mediaUrl = null;
    if (foto) {
      try { mediaUrl = await caricaFileCifrato(key, foto); }
      catch (e) {
        // Come nell'app: il punto si salva comunque, senza foto, dopo che
        // si sono scritti titolo e descrizione.
        alert('Immagine non caricata: ' + e.message + '\nIl punto viene salvato senza.');
      }
    }
    const cifrato = await mpCifraJson(key, {
      lat: mp.segnaposto.lat, lng: mp.segnaposto.lng,
      title: titolo, description: descrizione, mediaUrl,
    });
    const esito = await apiEsito('/boards/' + encodeURIComponent(mp.board.id) + '/elements', {
      method: 'POST',
      body: JSON.stringify({
        id: crypto.randomUUID(), type: 'place',
        x: 0, y: 0, width: 0, height: 0, rotation: 0, z_index: 0,
        ...cifrato, key_version: version,
      }),
    });
    if (!esito.ok) {
      mpErroreModulo(mpMessaggio(esito, 'Punto non salvato'));
      if (MP_ERRORI_STATO.includes(mpCodice(esito))) mpCarica(true);
      return;
    }
    mp.segnaposto = null;
    await mpCarica(false);
    mpDisegnaLato();
    mpVaiAlPunto(esito.data.id);
  } catch (e) {
    mpErroreModulo(e.message);
  } finally {
    mp.inCorso = false;
  }
}

async function mpSalvaRitrovo() {
  if (mp.inCorso || !mp.segnaposto) return;
  const titolo = document.getElementById('mp-r-titolo').value.trim();
  const descrizione = document.getElementById('mp-r-descr').value.trim();
  const inizioLocale = document.getElementById('mp-r-inizio').value;
  const ore = parseInt(document.getElementById('mp-r-ore').value, 10);
  const raggio = parseInt(document.getElementById('mp-r-raggio').value, 10);
  const foto = document.getElementById('mp-r-foto').files[0];
  if (!titolo) { mpErroreModulo('Dai un nome al ritrovo.'); return; }
  const inizio = new Date(inizioLocale);
  if (!inizioLocale || isNaN(inizio.getTime())) { mpErroreModulo('Scegli data e ora di inizio.'); return; }
  const fine = new Date(inizio.getTime() + ore * 3600000);

  const btn = document.getElementById('mp-salva');
  btn.dataset.testo = btn.textContent; btn.disabled = true; btn.textContent = 'Creazione…';
  mp.inCorso = true;
  try {
    const { key, version } = await mpChiave();
    let copertina = null;
    if (foto) {
      try { copertina = await caricaFileCifrato(key, foto); }
      catch (e) { alert('Copertina non caricata: ' + e.message + '\nIl ritrovo viene creato senza.'); }
    }
    const cifrato = await mpCifraJson(key, {
      lat: mp.segnaposto.lat, lng: mp.segnaposto.lng, radius: raggio,
      title: titolo, description: descrizione, media_url: copertina,
    });
    const esito = await apiEsito('/map-events/chat/' + encodeURIComponent(mp.chatId), {
      method: 'POST',
      body: JSON.stringify({ ...cifrato, key_version: version,
                             starts_at: inizio.toISOString(), ends_at: fine.toISOString() }),
    });
    if (!esito.ok) {
      mpErroreModulo(mpMessaggio(esito, 'Ritrovo non creato'));
      if (MP_ERRORI_STATO.includes(mpCodice(esito))) mpCarica(true);
      return;
    }
    if (mp.anteprima) { mp.mappa.removeLayer(mp.anteprima); mp.anteprima = null; }
    mp.segnaposto = null;
    await mpCarica(false);
    mpDisegnaLato();
    mpApriRitrovo(esito.data.id);
  } catch (e) {
    mpErroreModulo(e.message);
  } finally {
    mp.inCorso = false;
  }
}

// ── Ritrovo: scheda e galleria ────────────────────────────────────────

function mpApriRitrovo(id) {
  const ev = mp.eventi.find(e => e.id === id);
  if (!ev || !mp.mappa) return;
  const p = ev.pl;
  const mio = state.me && ev.created_by === state.me.id;
  const div = document.createElement('div');
  div.className = 'mp-fumetto';
  div.innerHTML = `
    ${p.media_url ? '<div class="mp-fumetto-foto"><span class="locked">Caricamento…</span></div>' : ''}
    <strong>${escapeHtml(p.title || 'Ritrovo')}</strong>
    ${ev.in_corso ? ' <b class="mp-in-corso">In corso</b>' : ''}
    ${p.description ? `<p>${escapeHtml(p.description)}</p>` : ''}
    <div class="mp-nota">${escapeHtml(fmtDateTime(ev.starts_at))} → ${escapeHtml(fmtDateTime(ev.ends_at))}
      ${p.radius ? ' · area ' + Math.round(p.radius) + ' m' : ''}</div>
    <div class="mp-nota">${ev.presenti} presenti · ${ev.foto} foto${ev.folder_opened_at ? ' · cartella aperta' : ''}</div>
    <div class="mp-fumetto-azioni">
      <button class="ghost" onclick="mpGalleria('${escapeHtml(ev.id)}')">&#128193; Galleria</button>
      ${mio && ev.in_corso ? `<button class="mp-link-rosso" onclick="mpChiudiRitrovo('${escapeHtml(ev.id)}')">Chiudi ritrovo</button>` : ''}
    </div>
    ${ev.in_corso ? '<div class="mp-nota">Per dichiararti presente e aggiungere foto usa l\'app sul posto.</div>' : ''}`;
  if (p.media_url) {
    resolveMedia(p.media_url).then(src => {
      const slot = div.querySelector('.mp-fumetto-foto');
      if (slot) slot.innerHTML = src ? `<img src="${src}" alt="">` : '';
    });
  }
  if (typeof p.lat === 'number') {
    L.popup({ maxWidth: 300 }).setLatLng([p.lat, p.lng]).setContent(div).openOn(mp.mappa);
  }
}

async function mpChiudiRitrovo(id) {
  if (!confirm('Chiudere il ritrovo in anticipo? La raccolta di foto si ferma per tutti; la cartella e le foto restano.')) return;
  const esito = await apiEsito('/map-events/' + encodeURIComponent(id) + '/close', { method: 'POST' });
  if (!esito.ok) { alert(mpMessaggio(esito, 'Ritrovo non chiuso')); return; }
  mp.mappa.closePopup();
  await mpCarica(false);
}

async function mpGalleria(id) {
  const ev = mp.eventi.find(e => e.id === id);
  if (!ev) return;
  const vecchia = document.getElementById('mp-galleria');
  if (vecchia) vecchia.remove();
  const box = document.createElement('div');
  box.id = 'mp-galleria';
  box.className = 'mp-galleria';
  box.innerHTML = `<div class="mp-galleria-box">
      <div class="mp-testa"><div class="mp-titolo">${escapeHtml(ev.pl.title || 'Ritrovo')} · galleria</div>
        <button class="mp-chiudi" onclick="document.getElementById('mp-galleria').remove()">&times;</button></div>
      <div class="mp-foto-griglia" id="mp-foto"><div class="empty">Carico le foto…</div></div>
    </div>`;
  box.addEventListener('click', (e) => { if (e.target === box) box.remove(); });
  document.body.appendChild(box);

  const esito = await apiEsito('/map-events/' + encodeURIComponent(id) + '/photos');
  const griglia = document.getElementById('mp-foto');
  if (!griglia) return;
  if (!esito.ok) { griglia.innerHTML = `<div class="error-box">${escapeHtml(mpMessaggio(esito, 'Galleria non caricata'))}</div>`; return; }
  const foto = esito.data || [];
  if (!foto.length) { griglia.innerHTML = '<div class="empty">Ancora nessuna foto in questa cartella.</div>'; return; }

  const { versions } = await mpChiave();
  griglia.innerHTML = foto.map((f, i) => `<figure class="mp-foto" id="mp-foto-${i}">
      <span class="locked">Caricamento…</span></figure>`).join('');
  foto.forEach(async (f, i) => {
    const slot = document.getElementById('mp-foto-' + i);
    const src = await resolveMedia(f.media_url);
    const didascalia = await mpDecifraJson(versions, f.key_version, f.payload_encrypted, f.payload_iv);
    if (!slot) return;
    slot.innerHTML = (src ? `<img src="${src}" alt="" onclick="apriVisore('${src}')">` : '<span class="locked">Non disponibile</span>')
      + `<figcaption>${escapeHtml((didascalia && didascalia.caption) || '')} <span>${escapeHtml(fmtDateTime(f.created_at))}</span></figcaption>`;
  });
}

Object.assign(window, {
  apriMappaPersonalizzata, chiudiMappa, mpCarica, mpCrea, mpAttiva, mpDisattiva,
  mpEliminaPunto, mpVaiAlPunto, mpScegliRisultato, mpModuloPunto, mpModuloRitrovo,
  mpAnteprimaArea, mpAnnullaRitrovo, mpSalvaPunto, mpSalvaRitrovo, mpDisegnaLato,
  mpApriRitrovo, mpChiudiRitrovo, mpGalleria, apriVisore,
});
"""

_JS_MODERATION = r"""
// ── Tab: moderazione ──────────────────────────────────────────────────
const REASON_LABELS = {
  harassment: 'Molestie, insulti o minacce',
  hate: 'Odio o discriminazione',
  sexual: 'Contenuti sessuali',
  violence: 'Violenza',
  child_safety: 'Sicurezza dei minori',
  self_harm: 'Autolesionismo o suicidio',
  spam: 'Spam o truffa',
  impersonation: 'Impersonificazione',
  other: 'Altro',
};

const TYPE_LABELS = {
  user: 'Profilo',
  community_post: 'Post di community',
  community_comment: 'Commento di community',
  gallery_media: 'Foto della galleria',
  gallery_comment: 'Commento su una foto',
  chat_user: 'Persona (da una chat)',
  chat_message: 'Messaggio di chat',
  chat_media: 'Media di chat',
};

// ── Tab: annunci ──────────────────────────────────────────────────────
//
// Da qui si scrive il messaggio che tutti gli utenti trovano aprendo l'app.
// Il testo va a finire in una finestra sopra la lista chat, una volta sola
// per persona: chi l'ha letto non se lo rivede addosso al prossimo avvio.
//
// PERCHE IL CORPO E TESTO E NON HTML
//
// Questo pannello e aperto a chi modera, non solo a chi ha scritto l'app.
// Accettare HTML significherebbe accettare uno script, e quello script
// finirebbe dentro una finestra mostrata a tutti gli utenti. L'app rende il
// corpo come testo; per l'immagine e il collegamento ci sono due campi
// dedicati, che non passano da qui.

function renderAnnouncementsTab() {
  renderShell('<div class="card"><div class="empty">Carico gli annunci…</div></div>');
  loadAnnouncements();
}

async function loadAnnouncements() {
  try {
    const items = await api('/announcements/admin');
    renderAnnouncements(items);
  } catch (err) {
    renderShell(`<div class="card"><div class="error-box">${escapeHtml(err.message)}</div></div>`);
  }
}

function statoAnnuncio(a) {
  if (!a.active) return { testo: 'Spento', colore: '#9aa0a6' };
  const ora = new Date();
  if (a.starts_at && new Date(a.starts_at) > ora) return { testo: 'Programmato', colore: '#c58b00' };
  if (a.ends_at && new Date(a.ends_at) <= ora) return { testo: 'Scaduto', colore: '#9aa0a6' };
  return { testo: 'In corso', colore: '#1f9d55' };
}

function renderAnnouncements(items) {
  const righe = items.length ? items.map(a => {
    const st = statoAnnuncio(a);
    const periodo = [
      a.starts_at ? 'dal ' + new Date(a.starts_at).toLocaleString('it-IT') : null,
      a.ends_at ? 'al ' + new Date(a.ends_at).toLocaleString('it-IT') : null,
    ].filter(Boolean).join(' ') || 'senza scadenza';

    return `
      <div class="card" style="margin-bottom:12px;">
        <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
          <strong style="flex:1;">${escapeHtml(a.title)}</strong>
          <span style="color:${st.colore}; font-weight:600;">${st.testo}</span>
        </div>
        <p style="white-space:pre-wrap; margin:10px 0;">${escapeHtml(a.body)}</p>
        ${a.image_url ? `<img src="${escapeHtml(a.image_url)}" alt="" style="max-width:220px; border-radius:8px; display:block; margin-bottom:8px;">` : ''}
        ${a.link_url ? `<div class="muted">Pulsante: ${escapeHtml(a.link_label || 'Apri')} &rarr; ${escapeHtml(a.link_url)}</div>` : ''}
        <div class="muted" style="margin-top:8px;">
          ${periodo} &middot; letto da ${a.seen_count} ${a.seen_count === 1 ? 'persona' : 'persone'}
        </div>
        <div style="margin-top:12px; display:flex; gap:8px;">
          <button class="ghost" onclick="toggleAnnouncement('${a.id}', ${a.active ? 'false' : 'true'})">
            ${a.active ? 'Spegni' : 'Accendi'}
          </button>
          <button class="ghost" onclick="deleteAnnouncement('${a.id}')">Elimina</button>
        </div>
      </div>`;
  }).join('') : '<div class="empty">Nessun annuncio.</div>';

  renderShell(`
    <div class="card">
      <h2 style="margin-top:0;">Nuovo annuncio</h2>
      <p class="muted" style="margin-top:0;">
        Compare all'apertura dell'app a chi non l'ha ancora visto. Ogni persona lo
        vede una volta sola: per una comunicazione diversa serve un annuncio nuovo,
        non la modifica di questo.
      </p>

      <label>Titolo</label>
      <input type="text" id="ann-title" maxlength="120" autocomplete="off">

      <label style="margin-top:10px; display:block;">Messaggio</label>
      <textarea id="ann-body" rows="5" style="width:100%;"></textarea>

      <label style="margin-top:10px; display:block;">Immagine (URL, facoltativa)</label>
      <input type="url" id="ann-image" autocomplete="off" placeholder="https://…">

      <label style="margin-top:10px; display:block;">Collegamento (facoltativo)</label>
      <input type="url" id="ann-link" autocomplete="off" placeholder="https://…">

      <label style="margin-top:10px; display:block;">Testo del pulsante</label>
      <input type="text" id="ann-link-label" maxlength="60" autocomplete="off" placeholder="Scopri di più">

      <div style="display:flex; gap:16px; flex-wrap:wrap; margin-top:10px;">
        <div>
          <label style="display:block;">Inizio (facoltativo)</label>
          <input type="datetime-local" id="ann-start">
        </div>
        <div>
          <label style="display:block;">Fine (facoltativa)</label>
          <input type="datetime-local" id="ann-end">
        </div>
      </div>

      <label style="margin-top:12px; display:block;">
        <input type="checkbox" id="ann-active" checked> Pubblica subito
      </label>

      <button style="margin-top:12px;" onclick="saveAnnouncement()">Crea annuncio</button>
      <div id="ann-result" style="margin-top:12px;"></div>
    </div>

    <h2 style="margin:20px 0 12px;">Annunci pubblicati</h2>
    ${righe}
  `);
}

/**
 * I campi datetime-local danno un orario SENZA fuso ("2026-09-01T09:00").
 * Mandarlo cosi al server, che ragiona in UTC, sposterebbe l'annuncio di
 * due ore rispetto a quello che chi lo scrive ha letto sullo schermo: una
 * promozione programmata per le nove partirebbe alle undici. new Date() lo
 * interpreta nel fuso del browser e toISOString() lo converte, che e'
 * esattamente il passaggio mancante.
 */
function orarioLocaleInIso(id) {
  const valore = document.getElementById(id).value;
  return valore ? new Date(valore).toISOString() : null;
}

async function saveAnnouncement() {
  const box = document.getElementById('ann-result');
  const title = document.getElementById('ann-title').value.trim();
  const body = document.getElementById('ann-body').value.trim();

  if (!title || !body) {
    box.innerHTML = '<div class="error-box">Titolo e messaggio sono obbligatori.</div>';
    return;
  }

  try {
    await api('/announcements/admin', {
      method: 'POST',
      body: JSON.stringify({
        title,
        body,
        image_url: document.getElementById('ann-image').value.trim() || null,
        link_url: document.getElementById('ann-link').value.trim() || null,
        link_label: document.getElementById('ann-link-label').value.trim() || null,
        active: document.getElementById('ann-active').checked,
        starts_at: orarioLocaleInIso('ann-start'),
        ends_at: orarioLocaleInIso('ann-end'),
      }),
    });
    loadAnnouncements();
  } catch (err) {
    box.innerHTML = `<div class="error-box">${escapeHtml(err.message)}</div>`;
  }
}

async function toggleAnnouncement(id, active) {
  try {
    await api('/announcements/admin/' + id, {
      method: 'PATCH',
      body: JSON.stringify({ active }),
    });
    loadAnnouncements();
  } catch (err) {
    alert(err.message);
  }
}

async function deleteAnnouncement(id) {
  // Spegnere e eliminare fanno cose diverse e la conferma lo dice: chi
  // vuole solo fermare una comunicazione non deve perderne i numeri.
  if (!confirm('Eliminare l\'annuncio? Spariscono anche le letture registrate. Per fermarlo senza perdere nulla, usa Spegni.')) return;
  try {
    await api('/announcements/admin/' + id, { method: 'DELETE' });
    loadAnnouncements();
  } catch (err) {
    alert(err.message);
  }
}

function renderModerationTab() {
  renderShell('<div class="card"><div class="empty">Carico la coda…</div></div>');
  loadQueue();
}

async function loadQueue(showAll) {
  try {
    const reports = await api('/reports/queue?only_pending=' + (showAll ? 'false' : 'true'));
    renderQueue(reports, showAll);
  } catch (err) {
    renderShell(`<div class="card"><div class="error-box">${escapeHtml(err.message)}</div></div>`);
  }
}

function renderQueue(reports, showAll) {
  const cards = reports.length
    ? reports.map(reportCard).join('')
    : '<div class="empty">Nessuna segnalazione da esaminare.</div>';

  renderShell(`
    <div class="card">
      <h2 style="margin-top:0;">Verifica di un consenso</h2>
      <p class="muted" style="margin-top:0;">
        Serve quando qualcuno contesta di non aver mai accettato l'informativa. Dopo la
        chiusura di un account l'email nel registro &egrave; un'impronta e non si pu&ograve;
        cercare a occhio: qui viene ricalcolata.
      </p>
      <label>Email dichiarata dalla persona</label>
      <input type="email" id="consent-email" autocomplete="off">
      <button class="ghost" style="margin-top:12px;" onclick="checkConsent()">Verifica</button>
      <div id="consent-result" style="margin-top:12px;"></div>
    </div>

    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <h2 style="margin:0;">Coda di moderazione</h2>
        <button class="ghost" onclick="loadQueue(${showAll ? 'false' : 'true'})">
          ${showAll ? 'Solo da esaminare' : 'Mostra anche chiuse'}
        </button>
      </div>
      <p class="muted" style="margin-top:0;">
        Le urgenti sono in cima. Il numero accanto alla persona segnalata dice quante
        segnalazioni ha gi&agrave; ricevuto in totale: &egrave; la differenza fra un episodio
        e un comportamento.
      </p>
      ${cards}
    </div>`);
}

function reportCard(r) {
  const urgent = r.is_urgent;
  const type = TYPE_LABELS[r.content_type] || r.content_type;
  const reason = REASON_LABELS[r.reason] || r.reason;

  // Cosa si vede dipende da dove arriva la segnalazione. Su un contenuto
  // pubblico c'e il contenuto vero, estratto dal server. Su una chat c'e
  // la copia che ha allegato chi segnala, e va detto: la stessa cifratura
  // che impedisce di leggere il messaggio impedisce di provare che sia
  // mai esistito.
  let body = '';
  if (r.evidence_url) {
    const isVideo = /\.(mp4|webm|mov|3gp)$/i.test(r.evidence_url);
    body += `<div class="snapshot">${isVideo
      ? `<video src="${escapeHtml(r.evidence_url)}" controls></video>`
      : `<img src="${escapeHtml(r.evidence_url)}" alt="Contenuto segnalato">`}</div>`;
  }
  if (r.content_snapshot) {
    body += `<div class="snapshot">${escapeHtml(r.content_snapshot)}</div>`;
  }
  if (!body) {
    body = '<div class="snapshot muted">Nessuna copia del contenuto disponibile.</div>';
  }

  const unverified = r.snapshot_source === 'reporter'
    ? `<div class="unverified">
         Copia fornita da chi segnala, non verificabile. Il contenuto originale &egrave;
         cifrato end-to-end e il server non lo ha mai avuto in chiaro: non &egrave; possibile
         confermare che sia autentico. Valutala come una testimonianza, non come una prova —
         e pesa il numero di segnalazioni ricevute dalla stessa persona prima di decidere.
       </div>`
    : '';

  const canRemove = ['community_post', 'community_comment', 'gallery_media', 'gallery_comment']
    .includes(r.content_type);

  return `
    <div class="report-card ${urgent ? 'urgent' : ''}">
      <div class="report-head">
        <div>
          <div class="report-reason">${urgent ? '⚠️ ' : ''}${escapeHtml(reason)}</div>
          <div class="report-meta">${escapeHtml(type)} · ${fmtDateTime(r.created_at)}</div>
        </div>
        <div>
          ${r.target_report_count > 1
            ? `<span class="pill red">${r.target_report_count} segnalazioni su questa persona</span>`
            : '<span class="pill grey">prima segnalazione</span>'}
          ${r.status !== 'pending' ? `<span class="pill grey">${escapeHtml(r.status)}</span>` : ''}
        </div>
      </div>
      ${r.note ? `<div class="report-meta" style="margin-top:8px;">Nota di chi segnala: ${escapeHtml(r.note)}</div>` : ''}
      ${body}
      ${unverified}
      ${r.moderator_note ? `<div class="report-meta" style="margin-top:8px;">Decisione: ${escapeHtml(r.moderator_note)}</div>` : ''}
      ${r.status === 'pending' ? `
      <div class="report-actions">
        ${canRemove ? `<button class="remove" onclick="removeContent('${r.id}')">Rimuovi il contenuto</button>` : ''}
        <button onclick="closeReport('${r.id}', 'actioned')">Provvedimento preso</button>
        <button onclick="closeReport('${r.id}', 'dismissed')">Nessuna violazione</button>
      </div>` : ''}
    </div>`;
}

async function checkConsent() {
  const email = $('#consent-email').value.trim();
  const box = $('#consent-result');
  if (!email) { box.innerHTML = '<div class="muted">Inserisci un indirizzo email.</div>'; return; }

  box.innerHTML = '<div class="muted">Verifico…</div>';
  try {
    // POST e non GET: l'email sta nel corpo. In un URL finirebbe nella
    // cronologia del browser e nei log del server, che e l'ultimo posto
    // dove lasciare l'indirizzo di chi sta esercitando un diritto.
    const res = await api('/reports/consent-check', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });

    if (!res.found) {
      box.innerHTML = `<div class="warn-box">
        Nessun consenso registrato per questo indirizzo. Attenzione: significa
        &laquo;non risulta&raquo;, non &laquo;non ha mai acconsentito&raquo; — un registro
        pu&ograve; essere stato eliminato per scadenza dei 5 anni.
      </div>`;
      return;
    }

    const rows = res.proofs.map(p => `
      <div class="report-card">
        <div class="report-head">
          <div>
            <div class="report-reason">Accettato il ${fmtDateTime(p.accepted_at)}</div>
            <div class="report-meta">
              Informativa v${escapeHtml(p.privacy_version)} ·
              Termini v${escapeHtml(p.terms_version)} ·
              ${escapeHtml(p.action)}
            </div>
          </div>
          <span class="pill ${p.minimized ? 'grey' : 'red'}">
            ${p.minimized ? 'record minimizzato' : 'account attivo'}
          </span>
        </div>
      </div>`).join('');

    box.innerHTML = `
      <div class="info-box">Consenso trovato: ${res.proofs.length} registrazione/i.</div>
      ${rows}
      <div class="muted" style="margin-top:8px;">
        I record contrassegnati come minimizzati appartengono ad account chiusi: di essi
        restano solo versione, data e azione. Nome, indirizzo IP e user agent sono stati
        cancellati alla chiusura dell'account.
      </div>`;
  } catch (err) {
    box.innerHTML = `<div class="error-box">${escapeHtml(err.message)}</div>`;
  }
}

async function closeReport(id, status) {
  // La motivazione non e facoltativa nella sostanza: una coda svuotata
  // senza motivazioni non e un processo di moderazione, ed e la prima cosa
  // che manca quando qualcuno chiede come vengono trattate le segnalazioni.
  const note = prompt('Motivazione della decisione (resta agli atti):');
  if (note === null) return;
  try {
    await api('/reports/' + id, {
      method: 'PATCH',
      body: JSON.stringify({ status, moderator_note: note }),
    });
    await loadQueue();
  } catch (err) {
    alert(err.message);
  }
}

async function removeContent(id) {
  if (!confirm('Rimuovere il contenuto segnalato? L\'azione non è reversibile.')) return;
  try {
    await api('/reports/content/' + id, { method: 'DELETE' });
    await loadQueue();
  } catch (err) {
    alert(err.message);
  }
}
"""

_JS_PRIVACY = r"""
// ── Tab: privacy e dati ───────────────────────────────────────────────
function renderPrivacyTab() {
  renderShell(`
    <div class="card">
      <h2>I tuoi dati</h2>
      <p>Scarica una copia completa dei dati collegati al tuo account: profilo, consensi,
      conversazioni, galleria, contatti di emergenza, perimetri, check-in e viaggi.
      &Egrave; il diritto di accesso e di portabilit&agrave; (GDPR art. 15 e 20).</p>
      <div class="privacy-block" style="border:none;padding:0;margin:0;">
        <label>Conferma la tua password</label>
        <input type="password" id="export-password" autocomplete="current-password">
        <button class="ghost" id="export-btn" style="margin-top:14px;" onclick="downloadExport()">Scarica i miei dati (JSON)</button>
        <div id="export-status" class="muted" style="margin-top:10px;"></div>
      </div>
      <div class="warn-box">
        Se hai sbloccato la cifratura, i messaggi vengono decifrati qui nel browser e il file
        che scarichi &egrave; leggibile. Altrimenti il file arriva comunque completo, ma con i
        contenuti ancora cifrati: nessuno pu&ograve; consegnarli in chiaro, nemmeno il server,
        perch&eacute; la chiave &egrave; solo tua.
      </div>
    </div>

    <div class="card danger-zone">
      <h2>Elimina l'account</h2>
      <p>Cancellazione definitiva (GDPR art. 17): chat, media, dati di posizione e ogni altro
      dato collegato vengono eliminati subito e senza possibilit&agrave; di recupero.</p>
      <button class="danger-outline" onclick="openDeleteModal()">Elimina il mio account</button>
    </div>`);
}

async function downloadExport() {
  const btn = $('#export-btn');
  const status = $('#export-status');
  const password = $('#export-password').value;
  if (!password) { status.textContent = 'Inserisci la password per continuare.'; return; }

  btn.disabled = true; status.textContent = 'Preparo l\'export…';
  try {
    // POST e non GET: la password sta nel corpo, e in un URL finirebbe
    // nella cronologia del browser e nei log del server.
    const data = await api('/guardian-dashboard/export', {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
    $('#export-password').value = '';

    if (state.priv) {
      status.textContent = 'Decifro le conversazioni…';
      await decryptExport(data);
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    // Il JSON e il formato che serve alla portabilita (art. 20); il testo
    // leggibile serve all'accesso (art. 15), che chiede una forma
    // comprensibile per una persona, non per un programma.
    if (state.priv) downloadReadableTranscript(data);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'central-dati-personali.json';
    a.click();
    URL.revokeObjectURL(url);
    status.textContent = 'Export scaricato.';
  } catch (err) {
    status.textContent = 'Errore: ' + err.message;
  } finally {
    btn.disabled = false;
  }
}

/**
 * Aggiunge a ogni messaggio il campo `content_decifrato`.
 *
 * Il ciphertext resta nel file accanto al testo: un export che sostituisse
 * i dati originali con la propria interpretazione non sarebbe piu una
 * copia dei dati, e chi volesse riverificarlo con la propria chiave non
 * potrebbe piu.
 */
async function decryptExport(data) {
  for (const entry of data.chat || []) {
    const chat = entry.chat || {};
    const others = (entry.partecipanti || []).filter(p => p.user_id !== (state.me && state.me.id));
    let versions = new Map();

    try {
      if (chat.type === 'group') {
        const envelopes = await api('/groups/' + chat.id + '/keys?since_version=0');
        for (const env of envelopes) {
          if (!env.encrypted_by_public_key) continue;
          try {
            const wrapKey = await sharedKeyFrom(state.priv, env.encrypted_by_public_key);
            versions.set(env.key_version, await aesDecrypt(wrapKey, b64ToBytes(env.iv), b64ToBytes(env.encrypted_key)));
          } catch (e) { /* busta non apribile */ }
        }
      } else if (others.length && others[0].public_key) {
        versions.set(0, await sharedKeyFrom(state.priv, others[0].public_key));
      }
    } catch (e) { /* chat non apribile: i messaggi restano cifrati */ }

    for (const msg of entry.messaggi || []) {
      msg.content_decifrato = await decryptText(versions, msg);
    }
  }
}

/** Trascrizione leggibile delle conversazioni, accanto al JSON. */
function downloadReadableTranscript(data) {
  const lines = ['CENTRAL — LE MIE CONVERSAZIONI', 'Esportate il ' + new Date().toLocaleString('it-IT'), ''];
  const myId = state.me ? state.me.id : null;

  for (const entry of data.chat || []) {
    const chat = entry.chat || {};
    const names = new Map((entry.partecipanti || []).map(p => [p.user_id, p.name]));
    const title = chat.type === 'group'
      ? (chat.name || 'Gruppo')
      : ((entry.partecipanti || []).filter(p => p.user_id !== myId).map(p => p.name)[0] || 'Conversazione');

    lines.push('══════════════════════════════════════');
    lines.push(title);
    lines.push('══════════════════════════════════════');
    for (const msg of entry.messaggi || []) {
      const who = msg.sender_id === myId ? 'Io' : (names.get(msg.sender_id) || msg.sender_id);
      const when = new Date(msg.timestamp).toLocaleString('it-IT');
      let body = msg.content_decifrato;
      if (body === null || body === undefined) {
        body = msg.media_url ? '[' + msg.type + ' allegato]' : '[contenuto non decifrabile]';
      }
      lines.push('[' + when + '] ' + who + ': ' + body);
    }
    if (entry.messaggi_troncati) lines.push('… conversazione troncata: solo i messaggi piu recenti.');
    lines.push('');
  }

  const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'central-conversazioni.txt'; a.click();
  URL.revokeObjectURL(url);
}

// ── Cancellazione account ─────────────────────────────────────────────
// Stessa operazione disponibile in app (Profilo → Impostazioni → Elimina account): stesso
// endpoint, stessa richiesta di password. Qui in piu la conferma testuale,
// proprio perche un browser e piu facile da usare per sbaglio.
function openDeleteModal() {
  $('#delete-modal-backdrop').style.display = 'flex';
  $('#delete-password').value = '';
  $('#delete-confirm-text').value = '';
  $('#delete-error').textContent = '';
  $('#delete-error').style.display = 'none';
  $('#delete-confirm-text').focus();
}

function closeDeleteModal() {
  $('#delete-modal-backdrop').style.display = 'none';
}

async function confirmDeleteAccount() {
  const password = $('#delete-password').value;
  const confirmText = $('#delete-confirm-text').value.trim().toUpperCase();
  const errBox = $('#delete-error');
  errBox.textContent = ''; errBox.style.display = 'none';

  function showError(msg) { errBox.textContent = msg; errBox.style.display = 'block'; }

  if (confirmText !== 'ELIMINA') { showError('Scrivi ELIMINA per confermare.'); return; }
  if (!password) { showError('Inserisci la password.'); return; }

  const btn = $('#delete-confirm-btn');
  btn.disabled = true; btn.textContent = 'Eliminazione…';
  try {
    const res = await fetch('/users/me', {
      method: 'DELETE',
      headers: { 'Authorization': 'Bearer ' + state.token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || 'Impossibile eliminare l\'account');
    }
    closeDeleteModal();
    sessionStorage.removeItem('central_token');
    state.token = null; state.priv = null;
    if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null; }
    if (chatTimer) { clearInterval(chatTimer); chatTimer = null; }
    renderLogin(null, 'Il tuo account è stato eliminato definitivamente. Tutti i dati, le chat, i media e le posizioni sono stati cancellati.');
  } catch (err) {
    btn.disabled = false; btn.textContent = 'Elimina definitivamente';
    showError(err.message);
  }
}

// ── Avvio ─────────────────────────────────────────────────────────────
//
// Lo script e un modulo ES (serve al fallback X25519, che si carica con un
// import dinamico), quindi le funzioni non finiscono automaticamente su
// window e gli onclick scritti nell'HTML non le troverebbero. Si espone
// esplicitamente solo quello che l'HTML chiama.
Object.assign(window, {
  logout,
  switchTab,
  loadQueue,
  checkConsent,
  closeReport,
  removeContent,
  openChat,
  sendMessage,
  requestNotificationPermission,
  downloadExport,
  openDeleteModal,
  closeDeleteModal,
  confirmDeleteAccount,

  // Aggiunte insieme alle sezioni nuove. Dimenticarle qui non produce
  // nessun errore visibile: il pulsante semplicemente non fa niente, e in
  // console compare un "is not defined" che nessuno va a cercare se non
  // sospetta gia il problema. Chi aggiunge un onclick nell'HTML deve
  // ricordarsi di passare da qui.
  prendiInCarico,
  disconnettiDispositivo,
  cambiaPeriodo,
  stampaCronologia,
  scaricaCronologia,
  segnaAvviso,
  selezionaTuttiAvvisi,
  archiviaSelezionati,
  ripristinaSelezionati,
  alternaArchiviati,
  vaiAPersona,
  alternaSos,
  segnaSos,
  selezionaTuttiSos,
  archiviaSosPersona,
  alternaMappaGrande,

  // Chat.
  vaiInFondo,
  aggiornaPulsanteFondo,
  chiediPermessoNotifiche,
  scegliFile,
  rimuoviAllegato,
  annullaAllegati,
  inviaAllegati,

  // Scheda Annunci.
  saveAnnouncement,
  toggleAnnouncement,
  deleteAnnouncement,

  // Scheda Regala abbonamento.
  regalaAbbonamento,
});

// ── Tab: regala abbonamento ───────────────────────────────────────────
//
// Email, piano e mesi: il server trova l'account, aggiunge i giorni a quelli
// gia regalati (o li mette in coda dietro un periodo pagato) e manda una
// notifica a chi lo riceve. Un mese vale 30 giorni, come nelle immagini
// della promozione per i creator.

function renderGiftsTab() {
  renderShell(`
    <div class="card" style="max-width:560px;">
      <h2 style="margin-top:0;">Nuovo regalo</h2>
      <label>Email dell'account</label>
      <input type="email" id="gift-email" autocomplete="off" placeholder="nome@esempio.it">
      <div style="display:flex; gap:14px;">
        <div style="flex:1;">
          <label>Abbonamento</label>
          <select id="gift-plan" class="campo">
            <option value="premium">Premium</option>
            <option value="plus">Plus</option>
          </select>
        </div>
        <div style="width:140px;">
          <label>Mesi</label>
          <input type="number" id="gift-months" min="1" max="24" value="1">
        </div>
      </div>
      <label>Nota (facoltativa, la vedi solo tu)</label>
      <input type="text" id="gift-note" maxlength="200" autocomplete="off" placeholder="Es. video TikTok di @nome">
      <button class="primary" id="gift-btn" onclick="regalaAbbonamento()">Regala</button>
      <div id="gift-result"></div>
    </div>
    <h2 style="margin:20px 0 12px;">Ultimi regali</h2>
    <div id="gift-list"><div class="card"><div class="empty">Carico…</div></div></div>
  `);
  caricaRegali();
}

function rigaRegalo(g) {
  const piano = g.plan === 'premium' ? 'Premium' : 'Plus';
  const mesi = g.months === 1 ? '1 mese' : g.months + ' mesi';
  return `
    <div class="card" style="margin-bottom:10px; padding:16px 20px;">
      <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
        <strong style="flex:1;">${escapeHtml(g.name || g.email)}</strong>
        <span style="font-weight:700; color:#EA5B2E;">${piano} · ${mesi}</span>
      </div>
      <div class="muted" style="margin-top:6px;">
        ${escapeHtml(g.email)} · regalato il ${new Date(g.created_at).toLocaleDateString('it-IT')}
        · attivo fino al ${new Date(g.expires_at).toLocaleDateString('it-IT')}
      </div>
      ${g.note ? `<div class="muted" style="margin-top:4px;">${escapeHtml(g.note)}</div>` : ''}
    </div>`;
}

async function caricaRegali() {
  const box = document.getElementById('gift-list');
  if (!box) return;
  try {
    const righe = await api('/billing/gifts');
    box.innerHTML = righe.length ? righe.map(rigaRegalo).join('')
      : '<div class="card"><div class="empty">Nessun regalo ancora.</div></div>';
  } catch (err) {
    box.innerHTML = `<div class="error-box">${escapeHtml(err.message)}</div>`;
  }
}

async function regalaAbbonamento() {
  const box = document.getElementById('gift-result');
  const btn = document.getElementById('gift-btn');
  const email = document.getElementById('gift-email').value.trim();
  const plan = document.getElementById('gift-plan').value;
  const months = parseInt(document.getElementById('gift-months').value, 10);
  const note = document.getElementById('gift-note').value.trim();

  if (!email || !email.includes('@')) {
    box.innerHTML = '<div class="error-box">Scrivi l\'email dell\'account.</div>';
    return;
  }
  if (!Number.isInteger(months) || months < 1 || months > 24) {
    box.innerHTML = '<div class="error-box">I mesi vanno da 1 a 24.</div>';
    return;
  }
  const piano = plan === 'premium' ? 'Premium' : 'Plus';
  const mesi = months === 1 ? '1 mese' : months + ' mesi';
  if (!confirm(`Regalare ${mesi} di ${piano} a ${email}?`)) return;

  btn.disabled = true;
  box.innerHTML = '';
  try {
    const g = await api('/billing/gifts', {
      method: 'POST',
      body: JSON.stringify({ email, plan, months, note }),
    });
    const extra = g.converted_days
      ? ` I ${g.converted_days} giorni di Plus che aveva sono diventati ${piano}.` : '';
    box.innerHTML = `<div class="info-box">Fatto: ${escapeHtml(g.name || g.email)} ha ${piano} fino al
      ${new Date(g.expires_at).toLocaleDateString('it-IT')}.${extra} Gli abbiamo mandato una notifica.</div>`;
    document.getElementById('gift-email').value = '';
    document.getElementById('gift-note').value = '';
    caricaRegali();
  } catch (err) {
    box.innerHTML = `<div class="error-box">${escapeHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false;
  }
}

// ── Tab: aziende ─────────────────────────────────────────────────────────
//
// Un'azienda cliente con il suo livello (Base = tutti Plus, Completo = tutti
// Premium), la data di fine scritta in fattura e l'elenco delle email per
// ruolo. Il piano vale per chi ha un account con quelle email, anche se si
// registra dopo: non c'e' niente da rinnovare persona per persona.

const ORG_RUOLI = [
  { id: 'referente',   nome: 'Referenti',   uno: 'Referente',   aiuto: 'Contatto amministrativo: riceve per email attivazione, rinnovo e promemoria 7 giorni prima della scadenza. Nessun piano.' },
  { id: 'controllore', nome: 'Controllori', uno: 'Controllore', aiuto: 'Ricevono SOS e avvisi e usano questo pannello. Mandano in automatico l\'invito di tutela a ogni operatore.' },
  { id: 'operatore',   nome: 'Operatori',   uno: 'Operatore',   aiuto: 'Chi lavora da solo ed è seguito. Riceve gli inviti dei controllori e li accetta nell\'app.' },
];
const ORG_PIANI = { plus: 'Plus', premium: 'Premium', free: 'solo email' };

function oggiPiu(giorni) {
  const d = new Date(); d.setDate(d.getDate() + giorni);
  return d.toISOString().slice(0, 10);
}

function renderAziendeTab() {
  renderShell(`
    <div class="card org-form" style="max-width:720px;">
      <h2 style="margin-top:0;">Nuova azienda</h2>
      <label for="org-name">Nome dell'azienda</label>
      <input type="text" id="org-name" maxlength="120" autocomplete="off" placeholder="Es. Pulizie Rossi S.r.l.">
      <div class="org-row">
        <div>
          <label for="org-tier">Piano</label>
          <select id="org-tier" class="campo">
            <option value="completo">Completo · Premium</option>
            <option value="base">Base · Plus</option>
          </select>
        </div>
        <div>
          <label for="org-until">Valido fino al (compreso)</label>
          <input type="date" id="org-until" value="${oggiPiu(30)}">
        </div>
        <div>
          <label for="org-seats">Posti operatore</label>
          <input type="number" id="org-seats" min="1" placeholder="Senza limite">
        </div>
      </div>
      ${ORG_RUOLI.map(r => `
        <label for="org-new-${r.id}">${r.nome} <span class="muted">· ${escapeHtml(r.aiuto)}</span></label>
        <textarea id="org-new-${r.id}" rows="2" placeholder="Una o più email, separate da virgola o a capo"></textarea>
      `).join('')}
      <label for="org-note">Nota (facoltativa, la vedi solo tu)</label>
      <input type="text" id="org-note" maxlength="300" autocomplete="off" placeholder="Es. fattura 12/2026, prova gratuita">
      <button class="primary" id="org-btn" onclick="creaAzienda()">Crea azienda</button>
      <div id="org-result"></div>
    </div>
    <h2 style="margin:20px 0 12px;">Aziende</h2>
    <div id="org-list"><div class="card"><div class="empty">Carico…</div></div></div>
  `);
  caricaAziende();
}

function statoAzienda(o) {
  if (!o.active) return '<span class="org-pill org-off">Sospesa</span>';
  if (!o.valid) return '<span class="org-pill org-off">Scaduta</span>';
  const giorni = Math.ceil((new Date(o.expires_at) - new Date()) / 86400000);
  if (giorni <= 7) return `<span class="org-pill org-warn">Scade tra ${giorni} ${giorni === 1 ? 'giorno' : 'giorni'}</span>`;
  return '<span class="org-pill org-on">Attiva</span>';
}

function schedaAzienda(o) {
  const posti = o.seats ? `${o.operators} / ${o.seats} posti operatore` : `${o.operators} operatori`;
  const gruppi = ORG_RUOLI.map(r => {
    const membri = o.members.filter(m => m.role === r.id);
    return `
      <div class="org-group">
        <div class="org-group-title">${r.nome} <span class="muted">· ${ORG_PIANI[o.plans[r.id]] || ''} · ${membri.length}</span></div>
        ${membri.length ? membri.map(m => `
          <div class="org-member">
            <div style="flex:1; min-width:0;">
              <div class="org-email">${escapeHtml(m.email)}</div>
              <div class="muted">${m.registered
                ? 'Account attivo' + (m.name ? ' · ' + escapeHtml(m.name) : '')
                : 'Nessun account: il piano si attiva quando si registra con questa email'}</div>
            </div>
            <button class="ghost" onclick="togliMembro('${o.id}','${m.id}')">Togli</button>
          </div>`).join('') : '<div class="muted" style="padding:6px 0;">Nessuno.</div>'}
      </div>`;
  }).join('');

  return `
    <div class="card" id="org-${o.id}">
      <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
        <strong style="flex:1; font-size:16px;">${escapeHtml(o.name)}</strong>
        <span style="font-weight:700; color:#EA5B2E;">${escapeHtml(o.tier_label)}</span>
        ${statoAzienda(o)}
      </div>
      <div class="muted" style="margin-top:6px;">
        Valido fino al ${new Date(o.valid_until + 'T12:00:00').toLocaleDateString('it-IT')} · ${posti}
        ${o.note ? ' · ' + escapeHtml(o.note) : ''}
      </div>

      ${gruppi}

      <div class="org-form org-add">
        <label for="org-${o.id}-emails">Aggiungi persone</label>
        <textarea id="org-${o.id}-emails" rows="2" placeholder="Una o più email, separate da virgola o a capo"></textarea>
        <div class="org-row">
          <div>
            <select id="org-${o.id}-role" class="campo" aria-label="Ruolo">
              ${ORG_RUOLI.map(r => `<option value="${r.id}" ${r.id === 'operatore' ? 'selected' : ''}>${r.uno}</option>`).join('')}
            </select>
          </div>
          <div><button class="ghost org-btn" onclick="aggiungiMembri('${o.id}')">Aggiungi</button></div>
        </div>
      </div>

      <details class="org-edit">
        <summary>Rinnova o modifica</summary>
        <div class="org-form">
          <div class="org-row">
            <div>
              <label for="org-${o.id}-tier">Piano</label>
              <select id="org-${o.id}-tier" class="campo">
                <option value="completo" ${o.tier === 'completo' ? 'selected' : ''}>Completo · Premium</option>
                <option value="base" ${o.tier === 'base' ? 'selected' : ''}>Base · Plus</option>
              </select>
            </div>
            <div>
              <label for="org-${o.id}-until">Valido fino al</label>
              <input type="date" id="org-${o.id}-until" value="${o.valid_until}">
            </div>
            <div>
              <label for="org-${o.id}-seats">Posti operatore</label>
              <input type="number" id="org-${o.id}-seats" min="0" value="${o.seats || ''}" placeholder="Senza limite">
            </div>
          </div>
          <div class="org-row" style="margin-top:14px;">
            <div><button class="ghost org-btn" onclick="salvaAzienda('${o.id}')">Salva</button></div>
            <div><button class="ghost org-btn" onclick="sospendiAzienda('${o.id}', ${o.active ? 'false' : 'true'})">${o.active ? 'Sospendi' : 'Riattiva'}</button></div>
            <div><button class="ghost org-btn org-danger" onclick="eliminaAzienda('${o.id}')">Elimina</button></div>
          </div>
        </div>
      </details>
      <div id="org-${o.id}-msg"></div>
    </div>`;
}

let aziendeCache = [];

async function caricaAziende() {
  const box = document.getElementById('org-list');
  if (!box) return;
  try {
    aziendeCache = await api('/organizations');
    box.innerHTML = aziendeCache.length ? aziendeCache.map(schedaAzienda).join('')
      : '<div class="card"><div class="empty">Nessuna azienda ancora.</div></div>';
  } catch (err) {
    box.innerHTML = `<div class="error-box">${escapeHtml(err.message)}</div>`;
  }
}

function riepilogoAggiunte(r) {
  const parti = [];
  if (r.added.length) parti.push(`${r.added.length} aggiunt${r.added.length === 1 ? 'a' : 'e'}`);
  if (r.updated.length) parti.push(`${r.updated.length} con ruolo cambiato`);
  if (r.unchanged.length) parti.push(`${r.unchanged.length} già presenti`);
  let testo = parti.join(', ') || 'Nessuna email nuova';
  if (r.invalid.length) testo += `. Email non valide, saltate: ${r.invalid.map(escapeHtml).join(', ')}`;
  return testo + '.';
}

async function creaAzienda() {
  const box = document.getElementById('org-result');
  const btn = document.getElementById('org-btn');
  const name = document.getElementById('org-name').value.trim();
  const tier = document.getElementById('org-tier').value;
  const until = document.getElementById('org-until').value;
  const seatsTxt = document.getElementById('org-seats').value.trim();
  const note = document.getElementById('org-note').value.trim();
  if (name.length < 2) { box.innerHTML = '<div class="error-box">Scrivi il nome dell\'azienda.</div>'; return; }
  if (!until) { box.innerHTML = '<div class="error-box">Scegli fino a quando vale il piano.</div>'; return; }
  const members = ORG_RUOLI
    .map(r => ({ role: r.id, emails: document.getElementById('org-new-' + r.id).value.trim() }))
    .filter(m => m.emails.length >= 3);

  btn.disabled = true; box.innerHTML = '';
  try {
    const o = await api('/organizations', {
      method: 'POST',
      body: JSON.stringify({
        name, tier, valid_until: until, note: note || null,
        seats: seatsTxt ? parseInt(seatsTxt, 10) : null, members,
      }),
    });
    box.innerHTML = `<div class="info-box">Creata: ${escapeHtml(o.name)}, piano ${escapeHtml(o.tier_label)} fino al
      ${new Date(o.valid_until + 'T12:00:00').toLocaleDateString('it-IT')}, ${o.members.length} persone.
      Chi ha già un account ha ricevuto una notifica, gli operatori anche gli inviti dei controllori,
      i referenti l'email di conferma.</div>`;
    ['org-name', 'org-seats', 'org-note'].concat(ORG_RUOLI.map(r => 'org-new-' + r.id))
      .forEach(id => { document.getElementById(id).value = ''; });
    caricaAziende();
  } catch (err) {
    box.innerHTML = `<div class="error-box">${escapeHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false;
  }
}

function messaggioAzienda(id, html, errore) {
  const box = document.getElementById(`org-${id}-msg`);
  if (box) box.innerHTML = `<div class="${errore ? 'error-box' : 'info-box'}">${html}</div>`;
}

async function aggiornaScheda(id, testo) {
  await caricaAziende();
  if (testo) messaggioAzienda(id, testo, false);
}

async function aggiungiMembri(id) {
  const emails = document.getElementById(`org-${id}-emails`).value.trim();
  const role = document.getElementById(`org-${id}-role`).value;
  if (emails.length < 3) { messaggioAzienda(id, 'Scrivi almeno un\'email.', true); return; }
  try {
    const r = await api(`/organizations/${id}/members`, {
      method: 'POST', body: JSON.stringify({ emails, role }),
    });
    await aggiornaScheda(id, riepilogoAggiunte(r));
  } catch (err) {
    messaggioAzienda(id, escapeHtml(err.message), true);
  }
}

async function togliMembro(id, memberId) {
  const o = aziendeCache.find(x => x.id === id);
  const m = o && o.members.find(x => x.id === memberId);
  if (!confirm(`Togliere ${m ? m.email : 'questa persona'} da ${o ? o.name : 'questa azienda'}? Perde subito il piano aziendale.`)) return;
  try {
    await api(`/organizations/${id}/members/${memberId}`, { method: 'DELETE' });
    await aggiornaScheda(id, 'Persona tolta.');
  } catch (err) {
    messaggioAzienda(id, escapeHtml(err.message), true);
  }
}

async function salvaAzienda(id) {
  const tier = document.getElementById(`org-${id}-tier`).value;
  const until = document.getElementById(`org-${id}-until`).value;
  const seatsTxt = document.getElementById(`org-${id}-seats`).value.trim();
  if (!until) { messaggioAzienda(id, 'Scegli la data di fine.', true); return; }
  try {
    await api(`/organizations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ tier, valid_until: until, seats: seatsTxt ? parseInt(seatsTxt, 10) : 0 }),
    });
    await aggiornaScheda(id, 'Modifiche salvate.');
  } catch (err) {
    messaggioAzienda(id, escapeHtml(err.message), true);
  }
}

async function sospendiAzienda(id, attiva) {
  const o = aziendeCache.find(x => x.id === id);
  if (!attiva && !confirm(`Sospendere ${o ? o.name : 'questa azienda'}? Tutte le sue persone tornano subito al loro piano personale.`)) return;
  try {
    await api(`/organizations/${id}`, { method: 'PATCH', body: JSON.stringify({ active: attiva }) });
    await aggiornaScheda(id, attiva ? 'Azienda riattivata.' : 'Azienda sospesa.');
  } catch (err) {
    messaggioAzienda(id, escapeHtml(err.message), true);
  }
}

async function eliminaAzienda(id) {
  const o = aziendeCache.find(x => x.id === id);
  if (!confirm(`Eliminare ${o ? o.name : 'questa azienda'} e il suo elenco di persone? Per una pausa usa "Sospendi".`)) return;
  try {
    await api(`/organizations/${id}`, { method: 'DELETE' });
    await caricaAziende();
  } catch (err) {
    messaggioAzienda(id, escapeHtml(err.message), true);
  }
}

Object.assign(window, {
  creaAzienda, aggiungiMembri, togliMembro, salvaAzienda, sospendiAzienda, eliminaAzienda,
});

// ── Tab: visite al sito ──────────────────────────────────────────────────
//
// Numeri del contatore di getcentral.net (routers/site_analytics.py):
// visitatori diversi, pagine viste, da dove arrivano. Senza cookie: un
// visitatore e' "la stessa persona nello stesso giorno".

let visiteGiorni = 30;

function renderVisiteTab() {
  renderShell(`
    <div class="vs-periodo" role="group" aria-label="Periodo">
      ${[7, 30, 90, 365].map(d => `<button class="ghost ${d === visiteGiorni ? 'vs-on' : ''}" onclick="cambiaPeriodoVisite(${d})">${d === 365 ? '1 anno' : d + ' giorni'}</button>`).join('')}
    </div>
    <div id="vs-body"><div class="card"><div class="empty">Carico…</div></div></div>
  `);
  caricaVisite();
}

function cambiaPeriodoVisite(d) {
  visiteGiorni = d;
  renderVisiteTab();
}

function vsNum(n) { return Number(n || 0).toLocaleString('it-IT'); }

function vsGrafico(serie) {
  const W = 720, H = 180, P = 28;
  const max = Math.max(1, ...serie.map(s => s.pageviews));
  const bw = (W - P) / serie.length;
  const barre = serie.map((s, i) => {
    const x = P + i * bw;
    const hp = (s.pageviews / max) * (H - 30);
    const hv = (s.visitors / max) * (H - 30);
    const titolo = `${new Date(s.day + 'T12:00:00').toLocaleDateString('it-IT')}: ${s.visitors} visitatori, ${s.pageviews} pagine`;
    return `<g><title>${escapeHtml(titolo)}</title>
      <rect x="${x + bw * 0.12}" y="${H - 20 - hp}" width="${bw * 0.76}" height="${hp}" rx="2" fill="#F8C9B2"></rect>
      <rect x="${x + bw * 0.28}" y="${H - 20 - hv}" width="${bw * 0.44}" height="${hv}" rx="2" fill="#EA5B2E"></rect></g>`;
  }).join('');
  const passo = Math.max(1, Math.ceil(serie.length / 8));
  const etichette = serie.map((s, i) => i % passo ? '' :
    `<text x="${P + i * bw + bw / 2}" y="${H - 4}" font-size="10" text-anchor="middle" fill="#8C7A72">${new Date(s.day + 'T12:00:00').toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })}</text>`).join('');
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Visitatori e pagine viste per giorno">
    <text x="0" y="12" font-size="10" fill="#8C7A72">${vsNum(max)}</text>
    <line x1="${P}" y1="${H - 20}" x2="${W}" y2="${H - 20}" stroke="#F1E3DA"></line>
    ${barre}${etichette}</svg>`;
}

function vsTabella(titolo, righe, vuoto) {
  if (!righe.length) return `<div class="card"><h2 style="margin-top:0">${titolo}</h2><div class="muted">${vuoto}</div></div>`;
  const max = Math.max(...righe.map(r => r.visitors || r.pageviews));
  return `<div class="card"><h2 style="margin-top:0">${titolo}</h2>
    <div class="vs-righe">${righe.map(r => `
      <div class="vs-riga">
        <div class="vs-barra" style="width:${Math.max(4, ((r.visitors || r.pageviews) / max) * 100)}%"></div>
        <span class="vs-nome">${escapeHtml(r.name)}</span>
        <span class="vs-val">${vsNum(r.visitors)} <span class="muted">· ${vsNum(r.pageviews)} pag.</span></span>
      </div>`).join('')}</div></div>`;
}

const VS_DISPOSITIVI = { mobile: 'Telefono', desktop: 'Computer', tablet: 'Tablet' };

async function caricaVisite() {
  const box = document.getElementById('vs-body');
  if (!box) return;
  try {
    const s = await api('/site/stats?days=' + visiteGiorni);
    const pagPerVis = s.visitors ? (s.pageviews / s.visitors).toFixed(1).replace('.', ',') : '0';
    box.innerHTML = `
      <div class="vs-tiles">
        <div class="card vs-tile"><div class="muted">Visitatori</div><div class="vs-big">${vsNum(s.visitors)}</div><div class="muted">oggi ${vsNum(s.today.visitors)}</div></div>
        <div class="card vs-tile"><div class="muted">Pagine viste</div><div class="vs-big">${vsNum(s.pageviews)}</div><div class="muted">oggi ${vsNum(s.today.pageviews)}</div></div>
        <div class="card vs-tile"><div class="muted">Pagine per visitatore</div><div class="vs-big">${pagPerVis}</div><div class="muted">ultimi ${s.days} giorni</div></div>
      </div>
      <div class="card"><h2 style="margin-top:0">Andamento</h2>
        <div class="muted" style="margin-bottom:8px"><span class="vs-leg" style="background:#EA5B2E"></span>visitatori &nbsp; <span class="vs-leg" style="background:#F8C9B2"></span>pagine viste</div>
        ${vsGrafico(s.series)}</div>
      <div class="vs-grid">
        ${vsTabella('Provenienza', s.sources, 'Nessuna visita nel periodo.')}
        ${vsTabella('Pagine più viste', s.pages.map(p => ({ ...p, name: p.name === '/' ? 'Home' : p.name })), 'Nessuna visita nel periodo.')}
        ${vsTabella('Dispositivi', s.devices.map(d => ({ ...d, name: VS_DISPOSITIVI[d.name] || d.name })), 'Nessuna visita nel periodo.')}
        ${vsTabella('Campagne (utm_campaign)', s.campaigns, 'Aggiungi ?utm_source=instagram&utm_campaign=nome ai link che condividi per vederle qui.')}
      </div>
      <p class="muted" style="margin-top:4px">Senza cookie e senza salvare indirizzi IP: un visitatore è la stessa persona nello stesso giorno, e chi torna il giorno dopo conta di nuovo. La provenienza è quella della prima pagina vista.</p>`;
  } catch (err) {
    box.innerHTML = `<div class="error-box">${escapeHtml(err.message)}</div>`;
  }
}

Object.assign(window, { cambiaPeriodoVisite });

// Rete di sicurezza per la dimenticanza descritta sopra: in fase di
// sviluppo elenca in console gli onclick dell'HTML che non trovano una
// funzione esposta. Costa una scansione del documento a ogni disegno e
// non cambia nulla per chi usa il pannello, ma trasforma un pulsante muto
// in una riga di log che dice esattamente cosa manca.
function verificaHandler() {
  document.querySelectorAll('[onclick],[onchange]').forEach(el => {
    const codice = el.getAttribute('onclick') || el.getAttribute('onchange') || '';
    const nome = (codice.match(/^([A-Za-z_$][\w$]*)\s*\(/) || [])[1];
    if (nome && typeof window[nome] !== 'function') {
      console.warn('Handler non esposto su window:', nome, el);
    }
  });
}
window.verificaHandler = verificaHandler;

async function boot() {
  try {
    state.me = await api('/users/me');
  } catch (err) {
    return; // api() ha gia riportato al login su 401
  }
  // Se la coda risponde, sei moderatore. A chi non lo e il server risponde
  // 404: la coda non deve nemmeno risultare esistente.
  try {
    await api('/reports/queue?only_pending=true');
    state.isModerator = true;
  } catch (e) {
    state.isModerator = false;
  }
  // Si entra dalla panoramica, non dalla chat: chi apre questo pannello
  // vuole prima sapere se c'e qualcosa che non va, e solo dopo mettersi a
  // leggere i messaggi.
  switchTab('panoramica');
  // Messaggi nuovi e non letti, da qualunque sezione.
  avviaSorveglianzaChat();
}

if (state.token) { requestNotificationPermission(); boot(); } else { renderLogin(null); }
"""


# ─────────────────────────────────────────────────────────────────────
# PIEDE DI PAGINA CON I DOCUMENTI
# ─────────────────────────────────────────────────────────────────────
#
# Fuori dal contenitore #app di proposito: quel div viene riscritto da capo
# a ogni cambio di scheda, e il piede di pagina finirebbe cancellato al
# primo clic.
#
# Deve restare visibile anche PRIMA dell'accesso. Un'informativa
# raggiungibile solo da chi e gia entrato arriva dopo il momento in cui
# serviva: l'art. 13 GDPR chiede che le informazioni siano fornite al
# momento della raccolta dei dati, e la raccolta comincia dalla schermata
# di accesso.
#
# Nessun banner cookie: il pannello non usa cookie, e l'unico dato
# archiviato nel browser — il segno di sessione — ricade nell'esenzione
# per gli strumenti strettamente necessari (art. 122 Codice Privacy,
# art. 5(3) direttiva 2002/58/CE). Chiedere un consenso non dovuto
# abitua le persone a cliccare "accetto" senza leggere, che e l'opposto
# dello scopo per cui quei banner esistono.
_FOOTER = (
    '<footer class="legal-footer">'
    '<a href="/legal/dashboard-privacy" target="_blank" rel="noopener">Privacy</a>'
    '<span aria-hidden="true">\u00b7</span>'
    '<a href="/legal/cookies" target="_blank" rel="noopener">Cookie</a>'
    '<span aria-hidden="true">\u00b7</span>'
    '<a href="/legal/terms" target="_blank" rel="noopener">Termini</a>'
    '<span aria-hidden="true">\u00b7</span>'
    '<a href="/legal/delete-account" target="_blank" rel="noopener">Elimina account</a>'
    '</footer>\n'
)

PAGE_HTML = (
    '<!doctype html>\n'
    '<html lang="it">\n'
    '<head>\n'
    '<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    '<title>Central — Area personale</title>\n'
    # Icona del sito: il logo dell'app, ritagliato del margine bianco e
    # ridotto a 64px, incorporato come PNG in base64. Sta dentro l'HTML e
    # non in /static perche cosi non puo mancare, non serve una rotta e
    # non lascia un 404 nella scheda del browser.
    '<link rel="icon" type="image/png" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAYU0lEQVR42mV6e7Bd5XXfb63v2/s87vtKVxISCAggY2HAYAyBGuMxOC7YxjYdktSOXdtgE3dqM5lM3Xriju3GdsaTNGlnOtM0TWObTkxIS4CQGmrCw8Y8JSHebxBEssyVBNK997z3/tavf3zf3udcW6PR6J57ztnfY631e6wlZobJP2Z0TgDrrXL/i3bwVRw7hEGfIQAUCAgBaCSpBACSIEHAKBPfRJIUIUnADATiOwExwgAByfrNIMTAej0ibLRkcZOecqq+/Sy3YQkAyxLeCcePkPEG4gOds9W3whP38eUnsHZMaBAVUcTPGEFCVFk9idUiGJdV/UDA4n8FRsYPxh2SgvSpiX9FKCytXglImCGQRszMyJnn+A98yB23DfG5ks6q2kD8JtXw1E/twR+huyJ5E+rj89LhxWcTBAQEQUr8LQkBxNKDhUgrTrcqJCXuJ74H49tAPAuRuNVq9ZD4ZgAUKUoO+my19cMfzy6/EmYgRbXeAEFQpbj3Juz9ieQtUWchKMfRUMeGEGnPRkCF6byZNkkxiMWfqtM1gCaMaxXSBNC4VBBGVKEYty0QQGAU0kihxl0gBFtblUsuzT/7uxpvQMQDoFGcK++9CY/dJ+1Z0hBCXIQAMhHTSM+IEUog0CRuT+oQZ4qdmFHxh7hcUADG76xWDYwTCZp+qvMqHRzJGLEyN8977xqBjWv/DUIAoDQT58onf4rH75OpOVoQoxgVEKYLpZFmVSgLoBJPN1BIMUoggsWzjJ+AGSzAKIRULxJGWNytQGJWpNMBSEuXZoRZTLsYoUAKUYxKmVvAvXeP7rxdnIOZiqqtHLaHbkdjChaUkPXFJJ2AEZbKjsZvDQIKg6WoRbV0AmYpB6ROSQAUUknQaEarrjhGJiAxKkgRqozrE2AxOOO+EQKmpu3W/x3eOAjnFCJh793S74k6rUtHfGpcR0inmAqIBdKMAQxqllKNRmO8OhCiKgKYoShYjFCMUBZiABQiBGiBFlISGM2MVcCIiKSSQaTIHJ9C2qT30u0Ud94uImprR/nyU8gaCMFidtcnE2/DjGYaF5q2ZErE9JUUFQQIFQlBBj1011iUzBqcW+DiEuc3oNk2Gvs9dLoyGkEVIgBhQWCStgWSZhZvNaWDiKSaWeUOyBDQaNre3eGtI95efxbdNWQNmkldbWIhk5ipqaCQlq4xFVaxqhRSFOWQw5HNLuD0d8j2k3XzNszOSaMJpzByNGJnlYeW7bVX8dLzcmgZomg0qtM2SbWaAKgiqTqbjKsxYakCiBHey+qx8ORebwdflZRdhhrh4h7G1QSMN0NJGJQqNKEqJHsdbtwi77pId54tC4siihBgAcEggBfkDZ2dwwkn4bxfZ6djLz5rD/xUXn4JmYf3CIESMV4gmFhJ3FGVKCqxHkAoohDYS897HDtCETFLUV6tb3z28TsCBTW4VrekimJEUb73n+uF75PpWSmGGAzICRSTKpEjExGRzLtzz9ezzgm7Hw3/91Y9dlTabQSLS+T40CAiVArJGKSpfiPFkioPveEx6kvEtHTqkFgEq8emcEplMEGnxLMfDWx2UT76CX/q2zHosdehCEjNc8lziEON0lDAbDTicMgyIHQh4i96j562o/zhDfL8M5iaZggExIBJqpP+n+6E9fLNAEW368VqdgCIECY12lfcQYxmKaskBps66fXCluPdJ7+g84vorEJVBNpswmfDQ8u9F1/ov/pqceQIhgPxuVtYaJ60vbXj9NYJJ4gxdLtQQafj5hfki9cXN/xP7H5IpmakLCugA4wiUoO8KEkRyOTaUBQekRTW+Glpk2OOGcwmETFC/WBQbljyv3Odm5ljvxcfpdNzvVdeevP22/uP7eJbbzoGdT5WxdLQNXJ6qnHGOxY+dOXsue/icACSRSGq2WeuHY2GePwxaU/RQqw1AqXZOBSrWEw3A4lp48WIQGikpmmDkXuJRXCMESXjCmtWeu+u/qybneegDxFxDiK/uOF7q7fdkg377dmZfNOSupiUaT0WQjkcDXc/svzII6vvv3TL5z7vZ6at3xdSRLNPXzM6tOyW30CWV4yadbpJWnTcgERQBAiBcsxdWeEXU1wZJzhjAmOIhH5PPvBhf+LJ7PcgIt6Hovinb3+re+MNM+3G7HGbp6bbea65d1nmcq+5d7mXVu7a7ebspqX5jYvhnrv2f/Urg58fdK02jShH2m67j10dhKBVUT8WKtWqAVBBiUloBEQloRU0AS3FqIYU9XUgMVJKsX6PJ53mL7iE3Q5URcSMP//ud7j30bnjt7VaecNLnvs893nDZ3n66/PMZT7PXJZpnvuZrVsah39x8Btf6x9a1maDwYRwO3eG6TmEsqqGIK0qLYZJfg4hNC5PE3mquENkMmZGo7AiERXjFdKC6cWXqvfpclrt5e//pT752OzWzZlDnmc+z1zunHfq1DlRFVVxAnWq3ufe57nPnbQ3LDaPHln+T38cAJ2e7r/+2sr3/8qOvGmiiTvSRCigiFAEGnGVVrHumBaeKf7jLiselvhh1IGV5hLBsI9t292OnTbok/RTUyt7Hh3edef85iWn4jLnVEVFVFIVr6Fax7TNR7pTlK0Ni/bqS298+z/S+eHje6dAvzhPs1TVSRIiVR1GrT9ZKU6Q8InHm4kBwWq5FAUUE6QnTh+GI5xxjrZa7KyJqpVh9e9ubuZOvfMuHjhEpOJcFZeMPN8iuwIAUahTF6y9MDd65skQwuz0tM9zEUDAig4nzhK/zVIFBEUmSKyvJVxVcWv1mOIeVh1ACJbl7pQdHBUw6nRr7emn+fLzzflZVVGnGsFcMV5FqidWCTeKCARqAqfIvZbBL87FMqOAqla1J5aaeIIBlCqGqxugUCQpsrh2mTAIpCZDpIBiMFEOhza3mC1tRlFQhOr7e3blNJ9nTiEKCGJa15ACAlG5VpIqhaKDRpZJp5Xulci2Iw+eEOqROP6SQoEkcuAJiplQa+oWV0BLEjCpPsJGIy5slFYbgwFEwnAQXn2x2cwVVJGkGPpdEGi2EpgI0O/SAvIWVGCkCIYDjkbImvCZOII65museGTF58HKzKkwWCQer8XKrmNNva5gVadl8ZMCo5UlZ+fUe4LiHLtdHD2qeaZCUUiE+4su5fuvMOfBEgorC77z3bj8KpudY1HACYuRnXo6PvKbdvwJUo7UaZIG+FURSEhc/ZjbSTQvMGZ8HoZaPnOszRMBAQ3Gms5JoxlREaI27MtwqOoAQJXDPj74sewjvw1gtHGz3fwDoMAZ52Wf/bL4vDztjPDnfyLDgttOyK65Xmfnw/kXl3/2h9JdgfqK3gomuWgtNScYNWuhk7ibxPqQyqhUsJVCn1aV5Cqmq+iM/EA0qkeBgBZk4xaFKEw2bTEDihIbNjnf0mKgm7aY9wgjm5l1swva77kNG8pGk0VZ+3MCTnJvcoJTTjCxyt1ICOYjYCdkrgCtCkDI+DXCaP1eLVG10dBGg4OOiIeRLuvdeUsxtyB53rv5xlYZ0GgMHryn2Lo9P/7Etdtuaq2tSrsZnn969Y5bGmee27v/bnfwAFoNhjreK4NsohBNuogkI7bE841b8fFXUns+qMT7BGzEAkIRW1mBmUAYgrTbMjfP3ioBCUF8pm8cXPnu142Y8iLTLSF8p9v5b3+6Itpi0NlpC+bIzg+/tyo/aISyMTcX83wd4akQgClbq8K4PlEqcQhvRjUmwIv7s6R/xnJMYBbEOTu8zMFAnJNQSrvtTzyZ+18hmtGtyJvN+SwnKSoKCpk18tnM00ydAw0QdW56btqCOZdV9HYc7rGCCzABhZiQ5fFtWitCqGg0mGjpjREKEcxCiEEv9etZZoeXi8PL4n00LPIzz7Zk28SaAefU+8gkkkPiFN47rdBZAKVlzglNYIhxrxqtPqnyLflLdfQmgmbr04PkmKNEkmRgxLQxgxj7S86h2xs+94zkOQAOBvnOM7HleBsORCq3lzZ2jmsVakkZjmk9TBBSNShH7KyhLBlhTSX5gHG5jCFsUumZusKDsYAbJCLgBOWAuJjmqNIjEgH1brD70VAWUEEo3cxM9v7fKHsDioAhUQ/UmB+pjdToHllkBVUQCIqCm46TS34jTE1bpydliJ9XjaEQF6WJF1a1djK2fKqPdb5U3lGqCZOFzMy3Wv3nnuk/99z0zjOs12On23rvpZ1HH7R9L/iZaVqooif6C4y6Fr9U3CMzFIiKGf3Vn8rPPD8cOlA++Vi46w68eQTqKiL6ywkA1uZJBDRq5M9WL7qi2pz0jdOSIM55K1f/4VZG/CRVtfWZ68LUrPUHEMcQoYOTQfyrlYRCeB9WjsnFl2U7z+Kxw9qealx2Fc69wLo9RHSq4udXIDrRQtZGbSLPVolG+6X8gRiEiJZAY252uPuRYz/7qbanAHA4zI87vvHF3y+zBvt9qsdEx2msVydTUxTq7OhRnn1+4198Av0BnIqgfPNA/8EHkDdZccgJ9l/t2yiVSklwVNE1whjdJYKMXnkEx2gpRjqhoqoN7976u/8ThkOoQJX9bv620xu/9wdhaQtXVwihc/UVVK2AqK6U4hiCra7igoubX7g+WhYIpUzNvHXbLaN9r9JnDJPVRiY4KSuCZ5JsFCqsUpK1tZ9McIoFREeilnAQUfUq7W3bJM/ShtWx281OPLn5lW/isg8HClfXMCoAgSigpJqBRg4H1lmz6Tn3qetan/+yqrIsGILOLxx94P7VW252M7NWBq5DIak3Y4wucK0MCINPvRar+QjHbSzUPa+xlouFZeqsd6pzVr0C5zkcukaz9Ylryve8v3zkfnv2SRxZZn8Q+yjiHNtTOPFkd/a7s/MvcguL7HVjYXDzC2vPPP3Gn/7JTJ4752o0Zt22krq8RV9UYzM11h2fuFFFgYRjFiUUSVU3dqsgomLBzc40TjuVoxFEo70PUQhYjlAM/XHH+at/x3p9O3KIRw+j14MK2jO6cbNs2CB5A4OeddYAiKqbXzy269GD3/3OVCga0zMekppfCTdkDEZVCYg/CusyysTYaiKd7mRcQDlW6EKUhdt2ot+81YZDkJpn0mqhKKACs9DvcTCQwUCc88dtw/Hbk6FjYChRjDgcxKVru20hHLzxr4/8rxtmct+YmnIK52KYVqS/QkSpeoLJJUPSk4KxJmbVC4l8SCZpN2mJBEBYFHrqDm01JZTw2fDw4WM/ue/wXT/O5ue3/tYnZk47BSSHQxaFRXVW9SkgIqqu2USjwdHo6K5dyzfeWDz11MzCfLOVe1XnXXXIcd2KKgcw2XBax67NExAa6GKl0aoZWZMps0pikxChaLbzHWbo7N179IH713btCocOee9GIbyy65Gpd//6wnvfO3P66fnionq/TmuRNhz0lpdXH3/i2H33DJ9+quX8/KaNmUruVNVJ3fHGZHNgncEY4TmJztiQ6n33q3LgdfVZqkUwSZsLk0MASeABNhqNjj9xdaU7eOE5tTJvt32zGWOsHBX91bVRoCxuyLaf0Nh2Qr5hozabIK3fHR4+PHr99eGB/bKy2mjkrdmZzHvv1KuoiFOVdegJjI1oSdzZCDiRdJRSlrJxo0/WfXR+MKZ51ctVI1sA0sxEHV56IR+VzcUFVVWp7oqg02arUZY26veLp5/s7d3TscTxVNU757Os2WxkW5acqhNRlUxVVcc0pi701OgL14hWyV7DJP00eqGmkYzY94RgDEAaW8E1JCphYDY15VpWmXsiItH/ieCbOW3kM5yZCsYx+KgqVGkAnUQTSQVw0AnyN66eKtUhpqNjJY+tst6T2+JJA4noQ1aZXl9EQgapmjuqYgaBr3o6sYRRE4nTpCxIgdeqHQ9BvydZJlkeuxeJa1ZipSJtrLsoBKjRhx7zANQOp41xWjE2/FBJh0leHB0kSJQ+quJc0hCqog4icE5EI85IdEidc1nm88w7l3nvc9e44iPZKac5mvPOiQgUqgKXMlZVYglK4gY2Khpf+rJeeKF1u4SiGmao6KCkukYqODFSkALJZD33FVpYWwn9HvtddtZAwikHPeutYjDk6iphEp9dFFxb4bCHbgf9njgnAnY6jSuvkhO225HDKAqIgMa1NfS76PUEwuHQVldsMGSni34PIga6LVtlatqKEGc/Jq0GCkximwB+3MKwRCUmjVmIoCwsz/1vftK/fSdKK3Y9Eu6/F6OhO+8C/77LtD1dvvjc6PZbMBxKCNiyNb/iI7ptO1aPDf7x/9kTe7BxU+vz/1qBxiWXZudfUNx3nz38AGbnso9elb3z3HL/gcH/+HN30q/lV3xINy2xPxj86A7b+xhUORohmFAme55iUqm7ZBcp1veg0r6snvFgIPLrrtcLL+k+9FD/lZftlNPCoC/vuqBxzZcGL7+y+g+34rSd+WevC8OBLSw0/+3XuPWEzj13jTq99vX/Xs44O6x1evv2kRwcOtx79vlwbNWKMvutT2aXXd55+OHhSy9xWPCkkwqztVtuG+zb1/7Sl/Frp3IwSN38sQ03bv5NwJl4qE6409XJB4MIVNjryrnn6Y63rX719/W1faGRB++hyK74aP9n95a33ayzs8N7fjxz7fX9xe/p286g96tf/wM/6HVuu0W++Uf5ZZf3du0Kf3uTved9Yc/u8Pe36pbNmJ3Pzzpn7Yd/Pfrbv8kWFly7Xd5xhz34sFtaGr35Zuuii93pbx/tfTyabiZwaV4gzUrUUBdbfV6mpmEWu5QyduHTzbAMbmmzHT6sR464zZsBoChD5sVn+ek7/de+IerYH/bv/RFX13R6lkeOZKTbuCRvvcVfHJTtJ0Kdm54REdee4tImNJs0MATpdf38gs7OhW6n8clP5e+7pDh0GJ2u5J5mE+Yux4ZvxcqiSYEQZGbay5atfGLP5NSRTECKOB9ef725davsOD3s3YN2S9tTXF1jp1P0+ivf+bo3Mm+4xXldXaVInPzTomSAiDCUBBBKqFIQ3noTupGNZlwizdgfYGlz68or3/z2d4q77sLc3Mb//heiDgCtNDOG1F0XrJuxiwNcsvk4LzvOCHf9qAKysWZO7KHRLJ99pn/fvTP/7j8UD98vc/OW54M/+lb3ph/O/N5XNn7jW/baPn/eBaP9r/f/8JvSaOr0dMUFDc2mTE1DnIyK0fPPT//2vxzt2DHavavYvUtnZ5FlMFK9rXWKX7wxd9XHilNOkVNOybZtHzpHQqdnJMsTClUjGjLhMQbQ7zzDfeM//xfb/RBWV2TsEtdDeQlDR3t2Dw7u1y3HlUePje7+Rzl2DMvL3d27MD+PhQ39x/YM//5WF0KgFG8sy759sc0RjOXPD+DAAfXZ6JlnyrKQhcXixRexvFyUwV54UdbW4D36g97jT8imJWxa6v/sgcHePeHAARw5UoLliy/h6DF6NwF4Cfxphtm56c98Towc3n5z+JsfyOw8iwJmScTVDgtAQeh0QlkA8HkDzSZU0R+EXs9UBHDNFvIMwxGLQtvtOL4Zhn0G03ZbABSh6PUYgms0pNFkt6t5A97HhpkNR6Hfo1GyTARQr81G6HQlyzTLuc5rik0Bx5WV/Mqr5r7wRbEQbNDvf/0rcvgQfMYQJrrkE00hjUQbRhMbT6KkkzETo6gaiDh+BRHnY2ct2YwRYkMQgzgXKUwq8fG3nBh0JMW5+LV1eyk+jCoIAXlj/s/+q9+4pCC1PZV9+trq+KVqupIWG60KA4tgZWBZSlkRLgNDYFlaUUYQtECEKFAVFJaBZUj9ISPLYEUZaYwFo43FNs2sLC2EOEuXJk9DwPoGAavhVut0W//qmmxpE8wUqizL/Mxz3KevLdfWQDIiQz1FGdJIW8K4qN5MqldURRPd4rpBoYrdSfyL1MHU1JuouH5FanXSGZmQs2NfjCpwGt56q3HV1VMf+KCVZSSXlgY8nevfefvo+38pomg2YSGNak5MOFscAlWpew3rB2NZufwyeXZcP8Q05gWV52RYJ+ErYS71IwiIcygK63abH7969vO/KyEwviOEkIxfC+L88MnHB3/1F3ztFcmbyHOIiEo9hVB5Q0KaiK7vhCZ3IA6OrVt1PU5dtV1SK8Zq942Ts13Cai68yhwUhXV7smFx6lOfm/rg5ahWT1Is2NiKCUG8t0F/+OM7Rz+52/b/E4pSvIPTCuOkftoES0mtndQTqsDeUkaNtyECQz1/M2nZQlQmtXskrHHaVlR0w8b8wn/WvvLj2abNrFZf0bsQYjGRSg2I9wBsNCyeeap8+smwfz9XV1gUiKMhdTMz3XVlIkrUI+N7iuExYW5XXZDaGkniJ029Tga/iIg6TE/p1uPzd5zZOPc8v7gBAMoSzk0m2f8HIycXnv3t7BkAAAAASUVORK5CYII=">\n'
    '<style>' + _STYLE + STYLE_COMMUNITY + '</style>\n'
    '</head>\n'
    '<body>\n'
    '<div class="wrap" id="app"></div>\n'
    + _FOOTER
    + _MODALS +
    # type="module" serve al fallback X25519: l'import dinamico di
    # @noble/curves e un modulo ES e in uno script classico non parte.
    '<script type="module">\n'
    + _JS_CRYPTO + _JS_APP + _JS_UI + _JS_GUARDIAN + _JS_MAPPE + _JS_MODERATION + _JS_PRIVACY + JS_COMMUNITY +
    '\n</script>\n'
    '</body>\n'
    '</html>\n'
)
