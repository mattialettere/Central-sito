/* Menu mobile del sito: sotto i 1200px le voci dell'intestazione spariscono
   per mancanza di spazio, quindi qui si aggiunge un pulsante ☰ che apre un
   pannello con tutte le pagine (Funzioni, Aziende, White label, Segnala,
   Login...). Lo stesso file serve tutte le pagine in tutte le lingue: la
   lingua si legge da <html lang>. */
(function () {
  var lang = (document.documentElement.lang || 'it').slice(0, 2);
  var p = lang === 'en' ? '/en/' : lang === 'fr' ? '/fr/' : '/';
  var T = {
    it: { menu: 'Menu', close: 'Chiudi', home: 'Home', sos: 'SOS ed emergenze', chat: 'Chat crittografata', faq: 'Domande frequenti', g: 'Guide', f: 'Funzioni', s: 'Sicurezza', v: 'Video', b: 'Aziende', r: 'Segnala un problema', pr: 'Privacy', login: 'Dashboard Login', dlI: 'Scarica per iPhone', dlA: 'Scarica per Android' },
    en: { menu: 'Menu', close: 'Close', home: 'Home', sos: 'SOS and emergencies', chat: 'Encrypted chat', faq: 'FAQ', g: 'Guides', f: 'Features', s: 'Safety', v: 'Video', b: 'Business', r: 'Report a problem', pr: 'Privacy', login: 'Dashboard Login', dlI: 'Download for iPhone', dlA: 'Download for Android' },
    fr: { menu: 'Menu', close: 'Fermer', home: 'Accueil', f: 'Fonctions', s: 'Sécurité', v: 'Vidéo', b: 'Entreprises', r: 'Signaler un problème', pr: 'Confidentialité', login: 'Tableau de bord', dlI: 'Télécharger pour iPhone', dlA: 'Télécharger pour Android' }
  }[lang] || null;
  if (!T) return;

  var APPS = 'https://apps.apple.com/app/id6826663138';
  var PLAY = 'https://play.google.com/store/apps/details?id=net.getcentral.central';

  // In italiano e in inglese ogni voce porta a una pagina vera (meglio per
  // chi cerca su Google e per i motori AI); in francese le pagine dedicate
  // non esistono ancora, quindi restano le sezioni della home.
  var voci = {
    it: [[T.home, '/'], [T.f, '/funzionalita.html'], [T.s, '/sicurezza-famiglia.html'], [T.sos, '/app-sos-emergenza.html'],
      [T.chat, '/chat-crittografata.html'], ['Central City', '/central-city.html'], [T.v, '/#video'],
      [T.b, '/aziende.html'], ['White label', '/white-label.html'], null,
      [T.faq, '/domande-frequenti.html'], [T.g, '/guide/'], null],
    en: [[T.home, '/en/'], [T.f, '/en/features.html'], [T.s, '/en/family-safety.html'], [T.sos, '/en/sos-emergency-app.html'],
      [T.chat, '/en/encrypted-chat.html'], ['Central City', '/en/central-city.html'], [T.v, '/en/#video'],
      [T.b, '/en/aziende.html'], ['White label', '/en/white-label.html'], null,
      [T.faq, '/en/faq.html'], [T.g, '/en/guides/'], null]
  }[lang] || [
    [T.home, p], [T.f, p + '#funzioni'], [T.s, p + '#sicurezza'], ['Central City', p + '#city'], [T.v, p + '#video'],
    [T.b, p + 'aziende.html'], ['White label', p + 'white-label.html'], null
  ];
  voci = voci.concat([
    [T.login, 'https://online.getcentral.net/guardian-dashboard/panel'],
    [T.r, p + 'segnala.html'], [T.pr, p + 'privacy.html']
  ]);
  var primaPiccola = voci.length - 2; // Segnala e Privacy in corpo minore

  var css = '' +
    '.mm-btn{display:none;flex:none;width:42px;height:42px;margin-left:8px;border-radius:14px;border:1px solid #F1E3DA;background:#fff;cursor:pointer;align-items:center;justify-content:center;padding:0;-webkit-tap-highlight-color:transparent}' +
    '.mm-btn span,.mm-btn span:before,.mm-btn span:after{display:block;width:18px;height:2px;border-radius:2px;background:#2B211D;position:relative;transition:transform .2s,background .2s}' +
    '.mm-btn span:before,.mm-btn span:after{content:"";position:absolute;left:0}.mm-btn span:before{top:-6px}.mm-btn span:after{top:6px}' +
    '.mm-open .mm-btn span{background:transparent}.mm-open .mm-btn span:before{transform:translateY(6px) rotate(45deg)}.mm-open .mm-btn span:after{transform:translateY(-6px) rotate(-45deg)}' +
    '.mm-panel{position:fixed;left:0;right:0;top:var(--mm-top,64px);bottom:0;z-index:999;background:rgba(43,33,29,.35);opacity:0;visibility:hidden;transition:opacity .2s,visibility .2s}' +
    '.mm-open .mm-panel{opacity:1;visibility:visible}' +
    '.mm-sheet{background:#FFF8F3;border-bottom:1px solid #F1E3DA;box-shadow:0 20px 40px rgba(70,30,10,.15);padding:10px 18px 22px;max-height:100%;overflow:auto;transform:translateY(-8px);transition:transform .2s}' +
    '.mm-open .mm-sheet{transform:none}' +
    '.mm-sheet a{display:block;padding:14px 6px;font:600 17px/1.2 Inter,system-ui,sans-serif;color:#2B211D;text-decoration:none;border-bottom:1px solid #F3E7DF}' +
    '.mm-sheet a:active{color:#D8481E}.mm-sheet a[aria-current="page"]{color:#D8481E}' +
    '.mm-sheet hr{border:0;height:10px;margin:0}' +
    '.mm-sheet .mm-small{font-size:15px;font-weight:500;color:#6B5C54}' +
    '.mm-sheet .mm-dl{margin-top:12px;border:0;border-radius:999px;text-align:center;color:#fff;background:linear-gradient(135deg,#F2854F,#E8613C);padding:16px}' +
    '@media (max-width:1200px){.mm-btn{display:inline-flex}}' +
    /* sul telefono Login e Segnala stanno nel menu: si liberano posto in testata */
    '@media (max-width:600px){.site-nav .nav-cta-alt:not(.nav-login),.site-nav .nav-report{display:none}.mm-btn{margin-left:4px;width:40px;height:40px}}' +
    /* sul telefono resta "Registrati / Login", subito a destra di Scarica; le azioni si accostano al menu */
    '@media (max-width:600px){.site-nav .nav-actions{margin-left:auto;gap:6px}.site-nav .nav-cta{order:1}.site-nav .nav-login{order:2}}' +
    '.site-nav .nav-login .mobile-label{line-height:1.12;text-align:center}' +
    '@media (max-width:600px){.site-nav .nav-login{display:inline-flex;align-items:center;padding:4px 10px;min-height:34px;font-size:11px;white-space:nowrap}.site-nav .nav-login .mobile-label{display:block}}' +
    '@media (max-width:400px){.site-nav .wrap{gap:8px}.site-nav .nav-actions{gap:4px}.site-nav .nav-cta{padding:8px 8px;font-size:11px}.site-nav .nav-login{padding:4px 7px}}' +
    /* pagina privacy: i pulsanti "Torna al sito" e "Scarica" sono nel menu */
    '@media (max-width:700px){header .wrap.nav{flex-wrap:nowrap}header .wrap.nav .nav-links{flex-wrap:nowrap;margin-left:auto}header .wrap.nav .nav-links .btn{display:none}}' +
    'body.mm-lock{overflow:hidden}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  function init() {
    var header = document.querySelector('header');
    if (!header) return;
    var riga = header.querySelector('.wrap') || header;

    var btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'mm-btn';
    btn.setAttribute('aria-label', T.menu); btn.setAttribute('aria-expanded', 'false'); btn.setAttribute('aria-controls', 'mm-panel');
    btn.innerHTML = '<span></span>';
    riga.appendChild(btn);

    var panel = document.createElement('div');
    panel.className = 'mm-panel'; panel.id = 'mm-panel';
    var sheet = document.createElement('nav');
    sheet.className = 'mm-sheet'; sheet.setAttribute('aria-label', T.menu);
    var qui = location.pathname.replace(/index\.html$/, '');
    voci.forEach(function (v, i) {
      if (!v) { sheet.appendChild(document.createElement('hr')); return; }
      var a = document.createElement('a'); a.textContent = v[0]; a.href = v[1];
      if (i >= primaPiccola) a.className = 'mm-small';
      if (v[1] === qui) a.setAttribute('aria-current', 'page');
      sheet.appendChild(a);
    });
    [[T.dlI, APPS], [T.dlA, PLAY]].forEach(function (d) {
      var dl = document.createElement('a');
      dl.className = 'mm-dl'; dl.textContent = d[0]; dl.target = '_blank'; dl.rel = 'noopener';
      dl.href = d[1];
      sheet.appendChild(dl);
    });

    // "Scarica" in testata: su iPhone/iPad porta all'App Store, su Android a
    // Google Play; sul computer resta il collegamento alla sezione con entrambi.
    var store = /iPhone|iPad|iPod/.test(navigator.userAgent) ||
      (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1) ? APPS :
      /Android/i.test(navigator.userAgent) ? PLAY : null;
    if (store) {
      Array.prototype.forEach.call(document.querySelectorAll('.site-nav a.nav-cta[href$="#scarica"]'), function (a) {
        a.href = store; a.target = '_blank'; a.rel = 'noopener';
      });
    }
    panel.appendChild(sheet);
    document.body.appendChild(panel);

    function apri(si) {
      var r = header.getBoundingClientRect();
      document.documentElement.style.setProperty('--mm-top', Math.max(0, r.bottom) + 'px');
      document.documentElement.classList.toggle('mm-open', si);
      document.body.classList.toggle('mm-lock', si);
      btn.setAttribute('aria-expanded', si ? 'true' : 'false');
      btn.setAttribute('aria-label', si ? T.close : T.menu);
    }
    btn.addEventListener('click', function () { apri(!document.documentElement.classList.contains('mm-open')); });
    panel.addEventListener('click', function (e) {
      // tocco fuori dal foglio oppure su un collegamento: si chiude
      if (e.target === panel || e.target.tagName === 'A') apri(false);
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') apri(false); });
    window.addEventListener('resize', function () { if (window.innerWidth > 1200) apri(false); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
