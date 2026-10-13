/* Menu mobile del sito: sotto i 1200px le voci dell'intestazione spariscono
   per mancanza di spazio, quindi qui si aggiunge un pulsante ☰ che apre un
   pannello con tutte le pagine (Funzioni, Aziende, White label, Segnala,
   Login...). Lo stesso file serve tutte le pagine in tutte le lingue: la
   lingua si legge da <html lang>. */
(function () {
  var lang = (document.documentElement.lang || 'it').slice(0, 2);
  var p = lang === 'en' ? '/en/' : lang === 'fr' ? '/fr/' : '/';
  var T = {
    it: { menu: 'Menu', close: 'Chiudi', home: 'Home', f: 'Funzioni', s: 'Sicurezza', v: 'Video', b: 'Aziende', r: 'Segnala un problema', pr: 'Privacy', login: 'Dashboard Login', dl: 'Scarica gratis su Google Play' },
    en: { menu: 'Menu', close: 'Close', home: 'Home', f: 'Features', s: 'Safety', v: 'Video', b: 'Business', r: 'Report a problem', pr: 'Privacy', login: 'Dashboard Login', dl: 'Get it free on Google Play' },
    fr: { menu: 'Menu', close: 'Fermer', home: 'Accueil', f: 'Fonctions', s: 'Sécurité', v: 'Vidéo', b: 'Entreprises', r: 'Signaler un problème', pr: 'Confidentialité', login: 'Tableau de bord', dl: 'Gratuit sur Google Play' }
  }[lang] || null;
  if (!T) return;

  var voci = [
    [T.home, p], [T.f, p + '#funzioni'], [T.s, p + '#sicurezza'], ['Central City', p + '#city'], [T.v, p + '#video'],
    [T.b, p + 'aziende.html'], ['White label', p + 'white-label.html'],
    null,
    [T.login, 'https://online.getcentral.net/guardian-dashboard/panel'],
    [T.r, p + 'segnala.html'], [T.pr, p + 'privacy.html']
  ];

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
    '.mm-sheet .mm-dl{margin-top:16px;border:0;border-radius:999px;text-align:center;color:#fff;background:linear-gradient(135deg,#F2854F,#E8613C);padding:16px}' +
    '@media (max-width:1200px){.mm-btn{display:inline-flex}}' +
    /* sul telefono Login e Segnala stanno nel menu: si liberano posto in testata */
    '@media (max-width:600px){.site-nav .nav-cta-alt,.site-nav .nav-report{display:none}.mm-btn{margin-left:4px;width:40px;height:40px}}' +
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
      if (i > 8) a.className = 'mm-small';
      if (v[1] === qui) a.setAttribute('aria-current', 'page');
      sheet.appendChild(a);
    });
    var dl = document.createElement('a');
    dl.className = 'mm-dl'; dl.textContent = T.dl; dl.target = '_blank'; dl.rel = 'noopener';
    dl.href = 'https://play.google.com/store/apps/details?id=net.getcentral.central';
    sheet.appendChild(dl);
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
