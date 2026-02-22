// ================================================
//  ALKEBULAN TECH - Protection Code Source v1.0
//  Bloque : clic droit, DevTools, Ctrl+U/S/P/F12
//  Detecte : DevTools ouvert, debugger actif
//  Alerte : son + overlay + rapport serveur
// ================================================
(function () {
  'use strict';

  // ── 1. BLOQUER CLIC DROIT ──────────────────────
  document.addEventListener('contextmenu', function (e) {
    e.preventDefault();
    e.stopPropagation();
    showWarning('clic_droit');
    return false;
  }, true);

  // ── 2. BLOQUER RACCOURCIS CLAVIER ─────────────
  document.addEventListener('keydown', function (e) {
    var ctrl  = e.ctrlKey || e.metaKey;
    var shift = e.shiftKey;
    var key   = (e.key || '').toLowerCase();
    var code  = e.code || '';

    if (ctrl  && key === 'u')                    { stop(e, 'Ctrl+U');          return; }
    if (ctrl  && key === 's')                    { stop(e, 'Ctrl+S');          return; }
    if (ctrl  && key === 'p')                    { stop(e, 'Ctrl+P');          return; }
    if (ctrl  && key === 'a')                    { stop(e, 'Ctrl+A');          return; }
    if (key   === 'f12' || code === 'F12')       { stop(e, 'F12');             return; }
    if (ctrl  && shift && key === 'i')           { stop(e, 'DevTools_I');      return; }
    if (ctrl  && shift && key === 'j')           { stop(e, 'DevTools_J');      return; }
    if (ctrl  && shift && key === 'c')           { stop(e, 'DevTools_C');      return; }
    if (ctrl  && shift && key === 'k')           { stop(e, 'DevTools_K');      return; }
    if (ctrl  && code  === 'F5')                 { stop(e, 'Ctrl+F5');         return; }
  }, true);

  function stop(e, type) {
    e.preventDefault();
    e.stopPropagation();
    showWarning(type);
  }

  // ── 3. DESACTIVER SELECTION TEXTE ─────────────
  document.addEventListener('selectstart', function (e) {
    if (!['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
      e.preventDefault();
    }
  });

  // ── 4. DESACTIVER DRAG ────────────────────────
  document.addEventListener('dragstart', function (e) {
    e.preventDefault();
  });

  // ── 5. DESACTIVER COPIER / COUPER ─────────────
  document.addEventListener('copy', function (e) {
    e.clipboardData.setData('text/plain', '');
    e.preventDefault();
  });
  document.addEventListener('cut', function (e) {
    e.clipboardData.setData('text/plain', '');
    e.preventDefault();
  });

  // ── 6. DETECTION DEVTOOLS (taille fenetre) ─────
  var devOpen = false;
  setInterval(function () {
    var wD = window.outerWidth  - window.innerWidth;
    var hD = window.outerHeight - window.innerHeight;
    if (wD > 160 || hD > 160) {
      if (!devOpen) {
        devOpen = true;
        reportAttempt('devtools_ouvert');
        showWarning('devtools_ouvert');
      }
    } else {
      devOpen = false;
    }
  }, 1000);

  // ── 7. DETECTION DEBUGGER (timing) ────────────
  setInterval(function () {
    var t0 = performance.now();
    /* jshint ignore:start */
    debugger;
    /* jshint ignore:end */
    if (performance.now() - t0 > 100) {
      reportAttempt('debugger_actif');
    }
  }, 4000);

  // ── 8. BLOQUER IMPRESSION (CSS) ───────────────
  var noprint = document.createElement('style');
  noprint.innerHTML = '@media print { body { display:none !important; visibility:hidden !important; } }';
  document.head.appendChild(noprint);

  // ── 9. NEUTRALISER LA CONSOLE ─────────────────
  (function () {
    var noop = function () {};
    var methods = ['log','warn','error','info','debug','table','dir','trace','group','groupEnd'];
    methods.forEach(function (m) {
      try { console[m] = noop; } catch (x) {}
    });
  })();

  // ── 10. DESACTIVER VIEW-SOURCE URL ────────────
  // Detecte si quelqu'un tape view-source: dans l'URL
  if (window.location.protocol === 'view-source:') {
    window.location.href = 'about:blank';
  }

  // ────────────────────────────────────────────────
  //  ALERTE VISUELLE
  // ────────────────────────────────────────────────
  function showWarning(type) {
    playAlertSound();
    reportAttempt(type);
    if (document.getElementById('_sec_overlay')) return;

    var el = document.createElement('div');
    el.id = '_sec_overlay';
    el.style.cssText = [
      'position:fixed', 'top:0', 'left:0', 'width:100%', 'height:100%',
      'background:rgba(8,6,14,0.97)', 'z-index:2147483647',
      'display:flex', 'align-items:center', 'justify-content:center',
      'flex-direction:column', 'gap:16px',
      'font-family:Rajdhani,Arial,sans-serif',
      'user-select:none'
    ].join(';');

    el.innerHTML = '<div style="font-size:56px">&#128274;</div>'
      + '<div style="color:#00BFFF;font-size:26px;font-weight:700;letter-spacing:3px;text-transform:uppercase">'
      + 'Acces Refuse'
      + '</div>'
      + '<div style="color:#C8C8E0;font-size:14px;max-width:400px;text-align:center;line-height:1.7">'
      + 'Cette action est protegee par <strong style="color:#00BFFF">ALKEBULAN TECH</strong>.<br>'
      + 'Toute tentative est enregistree et signalée par email.'
      + '</div>'
      + '<div style="font-size:11px;color:#8A8AA3;letter-spacing:2px;text-transform:uppercase">'
      + 'Type : ' + type
      + '</div>'
      + '<button id="_sec_close" style="margin-top:12px;padding:12px 32px;'
      + 'background:#00BFFF;color:#08060E;border:none;'
      + 'font-family:Rajdhani,Arial,sans-serif;font-size:14px;'
      + 'font-weight:700;letter-spacing:2px;text-transform:uppercase;cursor:pointer;">'
      + 'Fermer'
      + '</button>';

    document.body.appendChild(el);
    document.getElementById('_sec_close').addEventListener('click', function () {
      var o = document.getElementById('_sec_overlay');
      if (o) o.parentNode.removeChild(o);
    });
  }

  // ────────────────────────────────────────────────
  //  SON D'ALERTE  (Web Audio API)
  // ────────────────────────────────────────────────
  function playAlertSound() {
    try {
      var AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      var ctx  = new AudioCtx();
      var osc  = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = 'square';
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(220, ctx.currentTime + 0.4);
      gain.gain.setValueAtTime(0.4, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.5);
    } catch (e) {}
  }

  // ────────────────────────────────────────────────
  //  RAPPORT VERS SERVEUR
  // ────────────────────────────────────────────────
  function reportAttempt(type) {
    var payload = JSON.stringify({
      type:      type,
      url:       window.location.href,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent
    });

    // Methode 1 : fetch (moderne)
    try {
      fetch('/api/security-alert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload,
        keepalive: true
      });
    } catch (e) {}

    // Methode 2 : sendBeacon (tres fiable, meme en fermeture de page)
    try {
      var blob = new Blob([payload], { type: 'application/json' });
      navigator.sendBeacon('/api/security-alert', blob);
    } catch (e) {}

    // Methode 3 : pixel image beacon (fallback universel)
    try {
      var img = new Image();
      img.src = '/api/ping?t=' + encodeURIComponent(type) + '&ts=' + Date.now();
    } catch (e) {}
  }

})();
