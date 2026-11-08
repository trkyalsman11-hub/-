/* منصة بناء وتأثيث — مشهد ثلاثي الأبعاد تفاعلي (WebGL / Three.js r160)
   «من المخطط إلى المفتاح»: البيت يُبنى أمام الزائر على 5 مراحل.
   - لا يعتمد على التمرير (لا scroll-jacking)، ويُتحكَّم به بأزرار المراحل وزر الإيقاف.
   - مع «تقليل الحركة» يظهر البيت مكتملًا مباشرة بلا دوران تلقائي.
   - إن تعذّر WebGL تبقى الرسمة SVG الأصلية كما هي. */
import * as THREE from '../vendor/three/three.module.min.js';
import { OrbitControls } from '../vendor/three/OrbitControls.js';

const root = document.querySelector('[data-house3d]');
if (root) init(root).catch((e) => console.warn('house3d:', e));

function webglOK() {
  try { const c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')); }
  catch { return false; }
}

async function init(root) {
  if (!webglOK()) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = matchMedia('(hover: hover) and (pointer: fine)').matches;
  const stage = root.querySelector('.scene3d-stage');
  const buttons = [...root.querySelectorAll('[data-step]')];
  const playBtn = root.querySelector('[data-play]');
  const live = root.querySelector('[data-live]');
  const STAGES = buttons.map((b) => b.dataset.label);

  /* ───── المُصيِّر ───── */
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.domElement.setAttribute('role', 'img');
  renderer.domElement.setAttribute('aria-label', 'مجسم ثلاثي الأبعاد لبيت نجدي يُبنى على مراحل، من المخطط الهندسي حتى التسليم');
  stage.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 200);
  camera.position.set(25, 19.5, 27);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0.2, 3.2, 0);
  controls.enableZoom = false;          // لا نلتقط عجلة الفأرة حتى لا نعطّل تمرير الصفحة
  controls.enablePan = false;
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.minPolarAngle = 0.55;
  controls.maxPolarAngle = 1.25;
  controls.autoRotateSpeed = 0.55;
  controls.enabled = finePointer;       // على اللمس نترك السحب لتمرير الصفحة
  controls.update();

  /* ───── الإضاءة ───── */
  const hemi = new THREE.HemisphereLight(0xf4f3ef, 0xb9a888, 1.25);
  scene.add(hemi);
  const sun = new THREE.DirectionalLight(0xffffff, 2.4);
  sun.position.set(12, 20, 9);
  sun.castShadow = true;
  const sm = finePointer ? 2048 : 1024;
  sun.shadow.mapSize.set(sm, sm);
  Object.assign(sun.shadow.camera, { left: -14, right: 14, top: 14, bottom: -14, near: 1, far: 60 });
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.03;
  scene.add(sun);
  const warm = new THREE.PointLight(0xffb468, 0, 14, 1.6);
  warm.position.set(1.5, 2.2, 4.2);
  scene.add(warm);

  /* ───── الخامات (ألوان الهوية) ───── */
  const M = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.85, metalness: 0, ...o });
  const mat = {
    slab: M(0xe7e3da), slabSide: M(0xd2ccbf),
    sand: M(0xf0e7d6, { roughness: 1 }),
    plaster: M(0xefe4d0, { roughness: 0.95 }),
    plasterDark: M(0xdcc9a8),
    concrete: M(0xc3c8cf, { roughness: 0.9 }),
    wood: M(0x9e6e3b, { roughness: 0.7 }),
    woodLight: M(0xbf8a52, { roughness: 0.7 }),
    window: M(0x1a2a42, { roughness: 0.35, emissive: new THREE.Color(0xffb86b), emissiveIntensity: 0 }),
    orange: M(0xe8833a, { roughness: 0.55 }),
    ink: M(0x0f1e33, { roughness: 0.6 }),
    blue: M(0x1f4fa3, { roughness: 0.8 }),
    green: M(0x1f7a4d, { roughness: 0.8, side: THREE.DoubleSide }),
    greenDark: M(0x17603c, { roughness: 0.8, side: THREE.DoubleSide }),
    trunk: M(0x8a6a48, { roughness: 1 }),
    water: M(0x4a78c9, { roughness: 0.15, metalness: 0.1 }),
  };
  const edgeMat = new THREE.LineBasicMaterial({ color: 0x0f1e33, transparent: true, opacity: 0.16 });

  /* أداة: صندوق قاعدته عند y */
  function box(w, h, d, m, x, y, z, { edges = false, shadow = true } = {}) {
    const g = new THREE.BoxGeometry(w, h, d);
    g.translate(0, h / 2, 0);
    const mesh = new THREE.Mesh(g, m);
    mesh.position.set(x, y, z);
    mesh.castShadow = shadow;
    mesh.receiveShadow = true;
    if (edges) mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(g), edgeMat));
    return mesh;
  }

  /* عناصر تظهر بالتدريج: كل عنصر له مرحلة وتأخير وطريقة ظهور */
  const reveals = [];
  const reveal = (obj, step, { delay = 0, dur = 0.6, mode = 'rise', parent = scene } = {}) => {
    parent.add(obj);
    obj.userData.base = { y: obj.position.y, s: obj.scale.clone() };
    reveals.push({ obj, step, delay, dur, mode });
    return obj;
  };

  /* ───── القاعدة والأرض (ثابتة) ───── */
  const slab = box(17, 0.7, 17, [mat.slabSide, mat.slabSide, mat.slab, mat.slabSide, mat.slabSide, mat.slabSide], 0, -0.7, 0, { shadow: false });
  slab.material = [mat.slabSide, mat.slabSide, mat.slab, mat.slabSide, mat.slabSide, mat.slabSide];
  slab.add(new THREE.LineSegments(new THREE.EdgesGeometry(slab.geometry), edgeMat));
  scene.add(slab);
  const yard = box(15.6, 0.04, 15.6, mat.sand, 0, 0, 0, { shadow: false });
  scene.add(yard);

  /* ───── المرحلة 1: المخطط الهندسي (أزرق المخطط بخطوط بيضاء) ───── */
  const plan = new THREE.Group();
  const paper = new THREE.Mesh(new THREE.PlaneGeometry(14, 11), new THREE.MeshStandardMaterial({ color: 0x1f4fa3, roughness: 0.9, transparent: true, opacity: 0 }));
  paper.rotation.x = -Math.PI / 2; paper.position.set(0.4, 0.06, 0); paper.receiveShadow = true;
  plan.add(paper);
  const gridPts = [];
  for (let i = -7; i <= 7; i += 0.7) { gridPts.push(i + 0.4, 0.07, -5.5, i + 0.4, 0.07, 5.5); }
  for (let j = -5.5; j <= 5.5; j += 0.7) { gridPts.push(-6.6, 0.07, j, 7.4, 0.07, j); }
  const gridGeo = new THREE.BufferGeometry(); gridGeo.setAttribute('position', new THREE.Float32BufferAttribute(gridPts, 3));
  const gridMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0 });
  plan.add(new THREE.LineSegments(gridGeo, gridMat));
  // جدران المسقط (الكتلة الرئيسية + المجلس + جدار داخلي)
  const wallLines = [];
  const rect = (x1, z1, x2, z2) => wallLines.push(x1, .08, z1, x2, .08, z1, x2, .08, z1, x2, .08, z2, x2, .08, z2, x1, .08, z2, x1, .08, z2, x1, .08, z1);
  rect(-4.5, -3.2, 2.5, 2.3); rect(2.5, -1.8, 6.3, 2.8);
  wallLines.push(-1, .08, -3.2, -1, .08, 2.3, -4.5, .08, -0.4, -1, .08, -0.4);
  const wallGeo = new THREE.BufferGeometry(); wallGeo.setAttribute('position', new THREE.Float32BufferAttribute(wallLines, 3));
  const planLineMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0 });
  plan.add(new THREE.LineSegments(wallGeo, planLineMat));
  // قوس الباب بالبرتقالي (من الشعار)
  const arc = []; for (let a = 0; a <= 24; a++) { const t = (a / 24) * Math.PI / 2; arc.push(new THREE.Vector3(-1.75 + Math.cos(t) * 1.3, 0.09, 2.3 - Math.sin(t) * 1.3 + 0)); }
  const arcMat = new THREE.LineBasicMaterial({ color: 0xe8833a, transparent: true, opacity: 0 });
  plan.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(arc), arcMat));
  scene.add(plan);
  const planMats = [[paper.material, 1], [gridMat, 0.22], [planLineMat, 1], [arcMat, 1]];

  /* ───── المرحلة 2: الهيكل الإنشائي ───── */
  const H1 = 3.1, H2 = 6.2, HS = 3.4;
  const cols = [[-4.3, -3], [-1, -3], [2.3, -3], [-4.3, 2.1], [-1, 2.1], [2.3, 2.1], [2.7, -1.6], [6.1, -1.6], [2.7, 2.6], [6.1, 2.6]];
  cols.forEach(([x, z], i) => {
    const tall = x < 2.5;
    reveal(box(0.32, tall ? H2 : HS, 0.32, mat.concrete, x, 0, z), 1, { delay: i * 0.04, dur: 0.5 });
  });
  reveal(box(7.0, 0.2, 5.5, mat.concrete, -1, H1 - 0.2, -0.45), 1, { delay: 0.35, mode: 'scale' });
  reveal(box(7.0, 0.2, 5.5, mat.concrete, -1, H2 - 0.2, -0.45), 1, { delay: 0.45, mode: 'scale' });
  reveal(box(3.8, 0.2, 4.6, mat.concrete, 4.4, HS - 0.2, 0.5), 1, { delay: 0.5, mode: 'scale' });

  /* ───── المرحلة 3: البناء (الجدران) + الرافعة ───── */
  const main = box(7.0, H2, 5.5, mat.plaster, -1, 0, -0.45, { edges: true });
  reveal(main, 2, { dur: 0.75 });
  const majlis = box(3.8, HS, 4.6, mat.plaster, 4.4, 0, 0.5, { edges: true });
  reveal(majlis, 2, { delay: 0.15, dur: 0.7 });
  // سور الحوش بفتحة بوابة
  [[-7.4, -7.4, 14.8, 0.25], [-7.4, -7.4, 0.25, 14.8], [7.15, -7.4, 0.25, 14.8], [-7.4, 7.15, 5.6, 0.25], [1.8, 7.15, 5.6, 0.25]]
    .forEach(([x, z, w, d], i) => reveal(box(w, 1.25, d, mat.plaster, x + w / 2, 0, z + d / 2, { edges: true }), 2, { delay: 0.25 + i * 0.05, dur: 0.5 }));

  // الرافعة البرتقالية: تصعد مع البناء وتنزل عند التسليم
  const crane = new THREE.Group();
  crane.position.set(-6.2, 0, -5.8);
  crane.add(box(0.5, 0.35, 0.5, mat.ink, 0, 0, 0));
  for (let k = 0; k < 4; k++) {
    const [dx, dz] = [[-0.16, -0.16], [0.16, -0.16], [-0.16, 0.16], [0.16, 0.16]][k];
    crane.add(box(0.07, 10, 0.07, mat.orange, dx, 0.35, dz));
  }
  for (let y = 1; y < 10; y += 0.9) crane.add(box(0.4, 0.05, 0.4, mat.orange, 0, y, 0, { shadow: false }));
  const jib = box(10, 0.28, 0.32, mat.orange, 3.4, 10.2, 0); crane.add(jib);
  crane.add(box(1.0, 0.7, 0.8, mat.ink, -2.2, 9.8, 0)); // ثقل الموازنة
  crane.add(box(0.7, 0.7, 0.7, mat.blue, 0.1, 9.5, 0.45)); // الكابينة
  const cable = box(0.03, 4.6, 0.03, mat.ink, 6.6, 5.6, 0, { shadow: false }); crane.add(cable);
  crane.add(box(0.36, 0.3, 0.36, mat.orange, 6.6, 5.3, 0));
  scene.add(crane);

  /* ───── المرحلة 4: الواجهات النجدية ───── */
  // حزام بين الدورين وإطار السطح
  reveal(box(7.12, 0.22, 5.62, mat.plasterDark, -1, H1 - 0.1, -0.45), 3, { mode: 'scale' });
  reveal(box(3.92, 0.18, 4.72, mat.plasterDark, 4.4, HS - 0.05, 0.5), 3, { mode: 'scale', delay: 0.05 });
  // الشرفات المثلثة على حواف الأسطح
  const triShape = new THREE.Shape(); triShape.moveTo(-0.22, 0); triShape.lineTo(0.22, 0); triShape.lineTo(0, 0.5); triShape.closePath();
  const triGeo = new THREE.ExtrudeGeometry(triShape, { depth: 0.16, bevelEnabled: false }); triGeo.translate(0, 0, -0.08);
  let crIdx = 0;
  function crenellate(cx, cz, w, d, top, step = 0.62) {
    const add = (x, z, rotY) => {
      const m = new THREE.Mesh(triGeo, mat.plaster); m.castShadow = true; m.receiveShadow = true;
      m.position.set(x, top, z); m.rotation.y = rotY;
      reveal(m, 3, { delay: 0.1 + (crIdx++ % 40) * 0.012, dur: 0.35, mode: 'pop' });
    };
    for (let x = cx - w / 2 + 0.3; x <= cx + w / 2 - 0.2; x += step) { add(x, cz + d / 2 - 0.08, 0); add(x, cz - d / 2 + 0.08, 0); }
    for (let z = cz - d / 2 + 0.3; z <= cz + d / 2 - 0.2; z += step) { add(cx + w / 2 - 0.08, z, Math.PI / 2); add(cx - w / 2 + 0.08, z, Math.PI / 2); }
  }
  crenellate(-1, -0.45, 7.0, 5.5, H2);
  crenellate(4.4, 0.5, 3.8, 4.6, HS);
  // النوافذ (تضيء عند التسليم) وفتحات التهوية المثلثة
  const winFront = [[-3.6, 0.8], [-2.1, 0.8], [0.6, 0.8], [1.8, 0.8], [-3.6, 3.9], [-2.1, 3.9], [-0.25, 3.9], [1.4, 3.9]];
  winFront.forEach(([x, y], i) => {
    reveal(box(0.62, 1.15, 0.14, mat.window, x, y, 2.33, { shadow: false }), 3, { delay: 0.2 + i * 0.03, mode: 'pop' });
    reveal(box(0.8, 0.12, 0.2, mat.wood, x, y - 0.1, 2.36, { shadow: false }), 3, { delay: 0.22 + i * 0.03, mode: 'pop' });
  });
  [[2.58, 3.9, -1.9], [2.58, 3.9, -0.3], [2.58, 3.9, 1.2]].forEach(([x, y, z], i) =>
    reveal(box(0.14, 1.15, 0.62, mat.window, x, y, z, { shadow: false }), 3, { delay: 0.3 + i * 0.03, mode: 'pop' }));
  [[3.5, 1.0], [5.2, 1.0]].forEach(([x, y], i) =>
    reveal(box(0.62, 1.2, 0.14, mat.window, x, y, 2.83, { shadow: false }), 3, { delay: 0.35 + i * 0.04, mode: 'pop' }));
  const vent = new THREE.ExtrudeGeometry(triShape, { depth: 0.1, bevelEnabled: false });
  [-3.6, -2.1, -0.25, 1.4].forEach((x, i) => {
    const v = new THREE.Mesh(vent, mat.ink); v.scale.set(0.7, 0.55, 1); v.position.set(x, 5.35, 2.3);
    reveal(v, 3, { delay: 0.45 + i * 0.03, mode: 'pop' });
  });
  // باب نجدي خشبي بإطار
  reveal(box(1.5, 2.45, 0.16, mat.plasterDark, -0.8, 0, 2.31), 3, { delay: 0.25, mode: 'pop' });
  reveal(box(1.2, 2.2, 0.18, mat.wood, -0.8, 0, 2.34), 3, { delay: 0.3, mode: 'pop' });
  reveal(box(0.1, 0.1, 0.06, mat.orange, -0.45, 1.05, 2.45, { shadow: false }), 3, { delay: 0.4, mode: 'pop' });
  // البوابة
  reveal(box(1.9, 1.15, 0.12, mat.woodLight, 0.85, 0, 7.27), 3, { delay: 0.4, mode: 'pop' });

  /* ───── المرحلة 5: التأثيث والتسليم ───── */
  function palm(x, z, h, rot) {
    const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = rot;
    const segs = 7;
    for (let i = 0; i < segs; i++) {
      const r = 0.2 - i * 0.012;
      const s = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.92, r, h / segs, 8), mat.trunk);
      s.position.set(Math.sin(i * 0.25) * 0.08, (i + 0.5) * (h / segs), 0); s.castShadow = true; g.add(s);
    }
    const leafGeo = new THREE.PlaneGeometry(0.55, 2.6, 1, 6);
    const pos = leafGeo.attributes.position;
    for (let i = 0; i < pos.count; i++) { const yy = pos.getY(i); pos.setZ(i, -Math.pow((yy + 1.3) / 2.6, 2) * 0.9); pos.setX(i, pos.getX(i) * (1 - Math.abs(yy) / 1.6)); }
    leafGeo.computeVertexNormals(); leafGeo.translate(0, 1.3, 0);
    for (let i = 0; i < 9; i++) {
      const l = new THREE.Mesh(leafGeo, i % 2 ? mat.green : mat.greenDark);
      l.position.y = h; l.rotation.set(-1.0 - (i % 3) * 0.15, (i / 9) * Math.PI * 2, 0, 'YXZ'); l.castShadow = true; g.add(l);
    }
    return g;
  }
  reveal(palm(5.4, 5.3, 4.6, 0.3), 4, { dur: 0.7, mode: 'grow' });
  reveal(palm(-5.6, 5.6, 3.8, 1.2), 4, { delay: 0.12, dur: 0.7, mode: 'grow' });
  reveal(palm(-6, -2.5, 4.2, 2), 4, { delay: 0.2, dur: 0.7, mode: 'grow' });
  // جلسة خارجية في الحوش (أزرق الهوية) وطاولة
  reveal(box(2.6, 0.32, 0.7, mat.blue, 3.6, 0, 4.6), 4, { delay: 0.2, mode: 'pop' });
  reveal(box(0.7, 0.32, 1.9, mat.blue, 2.65, 0, 5.55), 4, { delay: 0.25, mode: 'pop' });
  reveal(box(0.9, 0.36, 0.9, mat.woodLight, 3.8, 0, 5.6), 4, { delay: 0.3, mode: 'pop' });
  // نافورة صغيرة
  reveal(box(1.6, 0.3, 1.6, mat.plasterDark, -3.2, 0, 4.8), 4, { delay: 0.3, mode: 'pop' });
  reveal(box(1.2, 0.08, 1.2, mat.water, -3.2, 0.26, 4.8, { shadow: false }), 4, { delay: 0.35, mode: 'pop' });
  // ممر حجري للباب
  for (let i = 0; i < 4; i++) reveal(box(1.1, 0.06, 0.7, mat.slab, -0.8 + i * 0.45, 0, 3.1 + i * 1.0, { shadow: false }), 4, { delay: 0.1 + i * 0.05, mode: 'pop' });
  // المفتاح البرتقالي يطفو عند الباب
  const key = new THREE.Group();
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.26, 0.08, 12, 28), mat.orange);
  const shaft = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.11, 0.11), mat.orange); shaft.position.x = 0.55;
  const tooth = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.22, 0.11), mat.orange); tooth.position.set(0.76, -0.12, 0);
  key.add(ring, shaft, tooth); key.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  key.position.set(-0.6, 3.0, 3.6);
  reveal(key, 4, { delay: 0.45, dur: 0.5, mode: 'pop' });

  /* ───── منطق المراحل ───── */
  const clamp01 = (v) => Math.min(1, Math.max(0, v));
  const ease = (t) => 1 - Math.pow(1 - t, 3);
  const backOut = (t) => { const c = 1.6; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
  const at = (p, step, delay = 0, dur = 1) => clamp01((p - step - delay) / dur);

  let progress = reduce ? 5 : 0;      // 0 → 5
  let target = progress;
  const sunWhite = new THREE.Color(0xffffff), sunGold = new THREE.Color(0xffd7a8);

  function apply(p) {
    const planA = ease(at(p, 0, 0, 0.8)) * (1 - ease(at(p, 2, 0, 0.6)));
    planMats.forEach(([m, max]) => { m.opacity = planA * max; });
    plan.visible = planA > 0.001;
    for (const r of reveals) {
      const t = at(p, r.step, r.delay, r.dur);
      const { obj } = r; const b = obj.userData.base;
      obj.visible = t > 0.001;
      if (!obj.visible) continue;
      if (r.mode === 'rise') obj.scale.set(b.s.x, b.s.y * Math.max(0.001, ease(t)), b.s.z);
      else if (r.mode === 'scale') { const e = ease(t); obj.scale.set(b.s.x * e, b.s.y, b.s.z * e); }
      else if (r.mode === 'grow') { const e = backOut(t); obj.scale.set(b.s.x * e, b.s.y * e, b.s.z * e); }
      else { const e = backOut(t); obj.scale.set(b.s.x * e, b.s.y * e, b.s.z * e); }
    }
    const cv = ease(at(p, 2, 0, 0.7)) * (1 - ease(at(p, 4, 0, 0.6)));
    crane.visible = cv > 0.001; crane.position.y = -(1 - cv) * 11;
    jib.rotation.y = (1 - cv) * 0.8 + Math.sin(p * 1.3) * 0.15;
    const glow = ease(at(p, 4, 0.2, 0.8));
    mat.window.emissiveIntensity = glow * 1.15;
    warm.intensity = glow * 26;
    sun.color.copy(sunWhite).lerp(sunGold, glow * 0.55);
    hemi.intensity = 1.25 - glow * 0.2;
  }

  /* ───── الواجهة: الأزرار والتشغيل ───── */
  let playing = !reduce;
  let autoplay = !reduce;
  function setPlaying(v) {
    playing = v;
    playBtn.setAttribute('aria-pressed', String(!v));
    playBtn.querySelector('span').textContent = v ? 'إيقاف الحركة' : 'تشغيل الحركة';
    controls.autoRotate = v && progress >= 4.999;
    if (!v) autoplay = false;
    wake();
  }
  function current() { return Math.min(4, Math.max(0, Math.ceil(target) - 1)); }
  function syncButtons() {
    const c = current();
    buttons.forEach((b, i) => { b.setAttribute('aria-pressed', String(i === c)); b.classList.toggle('done', i < c); });
    live.textContent = `المرحلة ${c + 1} من 5: ${STAGES[c]}`;
  }
  function goTo(step, instant = false) {
    target = step + 1;
    if (instant || reduce) progress = target;
    syncButtons(); wake();
  }
  buttons.forEach((b, i) => b.addEventListener('click', () => { autoplay = false; goTo(i); }));
  playBtn.addEventListener('click', () => setPlaying(!playing));
  if (reduce) { playBtn.hidden = true; }

  /* ───── الحجم والحلقة ───── */
  function resize() {
    const w = stage.clientWidth, h = stage.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.fov = w < 480 ? 33 : 30;
    camera.updateProjectionMatrix();
    wake();
  }
  new ResizeObserver(resize).observe(stage);

  let visible = true, raf = 0, last = performance.now(), interacting = false;
  controls.addEventListener('start', () => { interacting = true; controls.autoRotate = false; wake(); });
  controls.addEventListener('end', () => { interacting = false; setTimeout(() => { controls.autoRotate = playing && progress >= 4.999; wake(); }, 2500); });
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible) wake(); }, { threshold: 0.05 }).observe(stage);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) wake(); });

  function tick(now) {
    raf = 0;
    const dt = Math.min(0.05, (now - last) / 1000); last = now;
    if (autoplay && playing && Math.abs(progress - target) < 0.02 && target < 5) { target = Math.min(5, Math.floor(target + 1)); syncButtons(); }
    const speed = autoplay ? 0.75 : 1.6;               // مراحل في الثانية
    const diff = target - progress;
    if (Math.abs(diff) > 0.0005) progress += Math.sign(diff) * Math.min(Math.abs(diff), speed * dt);
    else progress = target;
    if (progress >= 4.999 && playing && !interacting && !controls.autoRotate) controls.autoRotate = true;
    if (progress >= 4.999) key.rotation.y += dt * 1.2;
    apply(progress);
    const moving = controls.update();
    renderer.render(scene, camera);
    const busy = Math.abs(target - progress) > 0.0005 || controls.autoRotate || interacting || moving || (progress >= 4.999 && playing);
    if (busy && visible && !document.hidden) wake();
  }
  function wake() { if (!raf) { last = performance.now(); raf = requestAnimationFrame(tick); } }

  /* إظهار المشهد بدل الرسمة الثابتة */
  root.classList.add('is-3d');
  resize();
  if (reduce) goTo(4, true); else { syncButtons(); setPlaying(true); }
  apply(progress); renderer.render(scene, camera);
}
