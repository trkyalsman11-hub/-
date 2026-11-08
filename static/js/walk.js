/* الدخول إلى البيت مع التمرير: الصورة تقترب من باب الفيلا ثم يظهر المجلس.
   التمرير نفسه طبيعي (لا نتحكم به)، ونحرّك الصور فقط حسب موضعه.
   مع «تقليل الحركة» أو بدون JavaScript تبقى الواجهة الثابتة كما هي. */
(function () {
  var walk = document.querySelector('[data-walk]');
  if (!walk || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var out = walk.querySelector('.walk-out img'), inside = walk.querySelector('.walk-in img'),
      panel = walk.querySelector('.walk-panel'), welcome = walk.querySelector('.walk-welcome'),
      hint = walk.querySelector('.walk-hint'), stage = walk.querySelector('.walk-stage');
  document.documentElement.classList.add('walk-on');
  if (inside.loading === 'lazy') inside.loading = 'eager';

  var doorX = parseFloat(out.dataset.doorX), doorY = parseFloat(out.dataset.doorY);
  var clamp = function (v) { return v < 0 ? 0 : v > 1 ? 1 : v; };
  var span = function (p, a, b) { return clamp((p - a) / (b - a)); };
  var ease = function (t) { return t * t * (3 - 2 * t); };   // smoothstep
  var easeIn = function (t) { return t * t * t; };

  /* موضع الباب داخل الصورة بعد قصّها بـ object-fit: cover */
  function placeOrigin() {
    var W = stage.clientWidth, H = stage.clientHeight, w = out.naturalWidth || 1672, h = out.naturalHeight || 941;
    var s = Math.max(W / w, H / h), dw = w * s, dh = h * s;
    var pos = getComputedStyle(out).objectPosition.split(' ');
    var px = parseFloat(pos[0]) / 100, py = parseFloat(pos[1] || '50%') / 100;
    var x = (W - dw) * px + doorX * dw, y = (H - dh) * py + doorY * dh;
    // على الشاشات الضيقة قد يقع الباب خارج الإطار؛ نُبقي نقطة الاقتراب داخله حتى لا تنكشف الخلفية
    x = Math.min(W * 0.9, Math.max(W * 0.1, x)); y = Math.min(H * 0.85, Math.max(H * 0.15, y));
    out.style.transformOrigin = x.toFixed(1) + 'px ' + y.toFixed(1) + 'px';
  }

  var ticking = false;
  function frame() {
    ticking = false;
    var r = walk.getBoundingClientRect(), total = walk.offsetHeight - innerHeight;
    var p = total > 0 ? clamp(-r.top / total) : 0;
    // 1) نقترب من الباب
    var zoom = easeIn(span(p, 0.08, 0.7));
    out.style.transform = 'scale(' + (1 + zoom * 4.2).toFixed(4) + ')';
    out.style.opacity = (1 - ease(span(p, 0.56, 0.72))).toFixed(3);
    out.style.filter = 'brightness(' + (1 - 0.35 * ease(span(p, 0.45, 0.68))).toFixed(3) + ')';
    // 2) ندخل المجلس
    var enter = ease(span(p, 0.56, 0.95));
    inside.style.opacity = ease(span(p, 0.56, 0.74)).toFixed(3);
    inside.style.transform = 'scale(' + (1.25 - 0.25 * enter).toFixed(4) + ')';
    // النصوص: لوحة البداية تختفي، ورسالة الترحيب تظهر في نفس المكان
    var a = ease(span(p, 0.03, 0.2));
    panel.style.opacity = (1 - a).toFixed(3);
    panel.style.transform = 'translateY(' + (-30 * a).toFixed(1) + 'px)';
    panel.style.visibility = a > 0.98 ? 'hidden' : 'visible';
    var b = ease(span(p, 0.78, 0.92));
    welcome.style.opacity = b.toFixed(3);
    welcome.style.transform = 'translateY(' + (24 * (1 - b)).toFixed(1) + 'px)';
    welcome.style.visibility = b < 0.02 ? 'hidden' : 'visible';
    hint.style.opacity = (1 - span(p, 0, 0.06)).toFixed(3);
  }
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(frame); } }
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', function () { placeOrigin(); onScroll(); });
  if (!out.complete) out.addEventListener('load', function () { placeOrigin(); frame(); });
  placeOrigin(); frame();
})();
