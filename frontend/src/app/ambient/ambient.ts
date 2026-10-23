// Ambient "library" background: a gilded orrery of meshed gears, a pendulum, and dust motes in
// window light, drawn on a fixed canvas behind the app. Rebuilt from the prototype's ambient.js
// (library mode only; the campfire mode was not taken). lib/flare speeds the gears and throws
// sparks while Quillbert works.

import { FLARE_EVENT } from "../../lib/flare";

type Ctx = CanvasRenderingContext2D;
type Point = [number, number];
type Spark = { x: number; y: number; vx: number; vy: number; r: number; heat: number; cool: number };
type Mote = { x: number; y: number; vx: number; vy: number; r: number; seed: number };
type Orrery = {
  ring1: HTMLCanvasElement;
  face1: HTMLCanvasElement;
  g2: HTMLCanvasElement;
  g3: HTMLCanvasElement;
  arcA: HTMLCanvasElement;
  arcB: HTMLCanvasElement;
  dots: { x: number; y: number; r: number; tw: number }[];
  hang: { dx: number; len: number; r: number; d: number }[];
};


const TAU = Math.PI * 2;
const rand = (a: number, b: number) => a + Math.random() * (b - a);
const gauss = () => (Math.random() + Math.random() + Math.random() - 1.5) / 1.5;

function hash(x: number, y: number, s: number) {
  let h = x * 374761393 + y * 668265263 + s * 982451653;
  h = (h ^ (h >>> 13)) * 1274126177;
  return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
}

function noise(x: number, y: number, s: number) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  const a = hash(xi, yi, s), b = hash(xi + 1, yi, s), c = hash(xi, yi + 1, s), d = hash(xi + 1, yi + 1, s);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}

// Spark colour: white-gold, then orange, then deep red as it cools.
function sparkColor(h: number, a: number) {
  let r: number, g: number, b: number;
  if (h > 0.7) {
    const t = (h - 0.7) / 0.3;
    r = 255; g = 190 + 55 * t; b = 110 + 110 * t;
  } else if (h > 0.35) {
    const t = (h - 0.35) / 0.35;
    r = 245 + 10 * t; g = 110 + 80 * t; b = 40 + 70 * t;
  } else {
    const t = h / 0.35;
    r = 150 + 95 * t; g = 40 + 70 * t; b = 25 + 15 * t;
  }
  return `rgba(${r | 0},${g | 0},${b | 0},${a})`;
}

// ---------- pre-rendered gear layers ----------

function gild(g: Ctx, w: number, h: number, dark: boolean) {
  const gr = g.createLinearGradient(0, 0, w, h);
  if (dark) {
    gr.addColorStop(0, "#f7dca4"); gr.addColorStop(0.45, "#d9a85a"); gr.addColorStop(0.7, "#f0c87e"); gr.addColorStop(1, "#a8733a");
  } else {
    gr.addColorStop(0, "#6e4a22"); gr.addColorStop(0.5, "#8f6432"); gr.addColorStop(1, "#5c3c1a");
  }
  return gr;
}

// Knock random specks out of a layer so the gilt looks worn.
function wear(g: Ctx, w: number, h: number, amt: number) {
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalCompositeOperation = "destination-out";
  const n = Math.round(w * h * amt);
  for (let i = 0; i < n; i++) {
    g.fillStyle = `rgba(0,0,0,${0.25 + Math.random() * 0.6})`;
    const r = Math.random() * 1.4 + 0.3;
    g.fillRect(Math.random() * w, Math.random() * h, r, r);
  }
  g.restore();
}

function layerFor(R: number, dpr: number, dark: boolean): [HTMLCanvasElement, Ctx] {
  const c = document.createElement("canvas");
  c.width = c.height = Math.ceil(R * 2 * dpr) + 4;
  const g = c.getContext("2d")!;
  g.translate(c.width / 2, c.height / 2);
  g.scale(dpr, dpr);
  g.lineCap = "round";
  g.lineJoin = "round";
  g.strokeStyle = g.fillStyle = gild(g, R, R, dark);
  return [c, g];
}

function ring(g: Ctx, r: number, lw: number, a: number) {
  g.globalAlpha = a;
  g.lineWidth = lw;
  g.beginPath();
  g.arc(0, 0, r, 0, TAU);
  g.stroke();
}

function ticks(g: Ctx, r0: number, r1: number, n: number, lw: number, a: number, every: number, r1b?: number) {
  g.globalAlpha = a;
  for (let i = 0; i < n; i++) {
    const t = (i / n) * TAU, big = every && i % every === 0;
    g.lineWidth = big ? lw * 1.8 : lw;
    const rr = big && r1b ? r1b : r1;
    g.beginPath();
    g.moveTo(Math.cos(t) * r0, Math.sin(t) * r0);
    g.lineTo(Math.cos(t) * rr, Math.sin(t) * rr);
    g.stroke();
  }
}

function teeth(g: Ctx, r: number, n: number, depth: number, a: number) {
  g.globalAlpha = a;
  g.beginPath();
  const s = TAU / n;
  const p = (t: number, rr: number): Point => [Math.cos(t) * rr, Math.sin(t) * rr];
  for (let i = 0; i < n; i++) {
    const t0 = i * s;
    const A = p(t0, r), B = p(t0 + s * 0.18, r + depth), C = p(t0 + s * 0.5, r + depth), D = p(t0 + s * 0.68, r);
    if (i === 0) g.moveTo(...A);
    else g.lineTo(...A);
    g.lineTo(...B);
    g.lineTo(...C);
    g.lineTo(...D);
    g.arc(0, 0, r, t0 + s * 0.68, t0 + s, false);
  }
  g.closePath();
  g.stroke();
}

function rays(g: Ctx, r0: number, r1: number, n: number, a: number, jitter: number) {
  g.globalAlpha = a;
  for (let i = 0; i < n; i++) {
    const t = (i / n) * TAU, L = r1 - Math.random() * jitter;
    g.lineWidth = i % 4 === 0 ? 1.4 : 0.8;
    g.beginPath();
    g.moveTo(Math.cos(t) * r0, Math.sin(t) * r0);
    g.lineTo(Math.cos(t) * L, Math.sin(t) * L);
    g.stroke();
  }
}

// Glyphs drawn at an angle around a circle.
function lettering(g: Ctx, glyphs: string[], r: number, offset: number) {
  g.textAlign = "center";
  g.textBaseline = "middle";
  glyphs.forEach((glyph, i) => {
    const t = (i / glyphs.length) * TAU + offset;
    g.save();
    g.globalAlpha = 0.88;
    g.translate(Math.cos(t) * r, Math.sin(t) * r);
    g.rotate(t + Math.PI / 2);
    g.fillText(glyph, 0, 0);
    g.restore();
  });
}

function clockRing(R: number, n: number, dpr: number, dark: boolean) {
  const [c, g] = layerFor(R * 1.12, dpr, dark);
  teeth(g, R, n, R * 0.055, 0.95);
  ring(g, R * 0.96, 1.2, 0.7);
  ring(g, R * 0.93, 0.8, 0.45);
  ticks(g, R * 0.93, R * 0.885, 240, 0.6, 0.55, 20, R * 0.86);
  wear(g, c.width, c.height, 0.02);
  return c;
}

function clockFace(R: number, dpr: number, dark: boolean) {
  const [c, g] = layerFor(R, dpr, dark);
  ring(g, R * 0.84, 1.6, 0.85);
  ring(g, R * 0.82, 0.7, 0.5);
  g.font = `600 ${Math.round(R * 0.1)}px Newsreader, Georgia, serif`;
  lettering(g, ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"], R * 0.71, -Math.PI / 2);
  ring(g, R * 0.6, 1, 0.55);
  ticks(g, R * 0.6, R * 0.57, 60, 0.6, 0.5, 5, R * 0.55);
  rays(g, R * 0.16, R * 0.46, 48, 0.32, R * 0.08);
  ring(g, R * 0.34, 0.8, 0.45);
  ring(g, R * 0.13, 1.4, 0.8);
  ring(g, R * 0.05, 1.2, 0.9);
  // Moon-phase window.
  g.globalAlpha = 0.75;
  g.lineWidth = 1.1;
  g.beginPath();
  g.arc(0, R * 0.3, R * 0.11, Math.PI, 0);
  g.closePath();
  g.stroke();
  g.globalAlpha = 0.5;
  g.beginPath();
  g.arc(-R * 0.03, R * 0.27, R * 0.04, 0, TAU);
  g.fill();
  wear(g, c.width, c.height, 0.025);
  return c;
}

function astrolabe(R: number, n: number, dpr: number, dark: boolean) {
  const [c, g] = layerFor(R * 1.12, dpr, dark);
  teeth(g, R, n, R * 0.08, 0.95);
  ring(g, R * 0.94, 1.3, 0.8);
  ring(g, R * 0.8, 0.8, 0.5);
  g.font = `${Math.round(R * 0.09)}px Newsreader, Georgia, serif`;
  lettering(g, [..."ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"], R * 0.87, 0);
  // Star web.
  const pts = Array.from({ length: 9 }, (_, i): Point => {
    const t = (i / 9) * TAU + 0.3;
    return [Math.cos(t) * R * 0.74, Math.sin(t) * R * 0.74];
  });
  g.globalAlpha = 0.35;
  g.lineWidth = 0.7;
  g.beginPath();
  pts.forEach((p, i) => {
    g.moveTo(...p);
    g.lineTo(...pts[(i + 4) % 9]);
  });
  g.stroke();
  // Three sub-dials.
  for (let i = 0; i < 3; i++) {
    const t = (i / 3) * TAU - Math.PI / 2;
    g.save();
    g.translate(Math.cos(t) * R * 0.42, Math.sin(t) * R * 0.42);
    ring(g, R * 0.15, 1.2, 0.85);
    ring(g, R * 0.1, 0.7, 0.5);
    g.globalAlpha = 0.6;
    g.beginPath();
    g.arc(0, 0, R * 0.05, 0, TAU);
    g.fill();
    g.restore();
  }
  ring(g, R * 0.24, 1, 0.6);
  ring(g, R * 0.07, 1.4, 0.9);
  g.globalAlpha = 0.55;
  g.lineWidth = 1;
  g.beginPath();
  g.arc(R * 0.1, -R * 0.08, R * 0.55, 0, TAU);
  g.stroke();
  wear(g, c.width, c.height, 0.025);
  return c;
}

function starGear(R: number, n: number, dpr: number, dark: boolean) {
  const [c, g] = layerFor(R * 1.15, dpr, dark);
  teeth(g, R, n, R * 0.13, 0.95);
  ring(g, R * 0.86, 1.1, 0.7);
  rays(g, R * 0.22, R * 0.8, 36, 0.6, R * 0.18);
  ring(g, R * 0.5, 0.8, 0.5);
  ring(g, R * 0.2, 1.4, 0.85);
  g.globalAlpha = 0.85;
  g.lineWidth = 1.3;
  for (let i = 0; i < 8; i++) {
    const t = (i / 8) * TAU;
    g.beginPath();
    g.moveTo(Math.cos(t) * R * 0.2, Math.sin(t) * R * 0.2);
    g.lineTo(Math.cos(t + 0.2) * R * 0.5, Math.sin(t + 0.2) * R * 0.5);
    g.stroke();
  }
  wear(g, c.width, c.height, 0.03);
  return c;
}

function arcs(R: number, dpr: number, dark: boolean, seed: number) {
  const [c, g] = layerFor(R * 1.02, dpr, dark);
  const segs: Point[] = [[0, 1.1], [1.35, 0.5], [2.1, 1.6], [4.05, 0.35], [4.6, 1.1]];
  segs.forEach(([s, len], i) => {
    const a0 = s + seed, a1 = a0 + len;
    g.globalAlpha = 0.8;
    g.lineWidth = i % 2 ? 1 : 2.2;
    g.beginPath();
    g.arc(0, 0, R, a0, a1);
    g.stroke();
    g.globalAlpha = 0.5;
    g.lineWidth = 0.7;
    g.beginPath();
    g.arc(0, 0, R * 0.965, a0, a1);
    g.stroke();
    const k = Math.round(len * 40);
    for (let j = 0; j <= k; j++) {
      const tt = a0 + (j / k) * len, big = j % 5 === 0;
      g.lineWidth = big ? 1 : 0.6;
      g.beginPath();
      g.moveTo(Math.cos(tt) * R * 0.965, Math.sin(tt) * R * 0.965);
      g.lineTo(Math.cos(tt) * R * (big ? 0.93 : 0.95), Math.sin(tt) * R * (big ? 0.93 : 0.95));
      g.stroke();
    }
    g.globalAlpha = 0.9;
    g.beginPath();
    g.arc(Math.cos(a1) * R, Math.sin(a1) * R, i % 2 ? 2.2 : 3.4, 0, TAU);
    g.fill();
  });
  wear(g, c.width, c.height, 0.015);
  return c;
}

// ---------- the running scene ----------

/** Starts drawing on `canvas`; returns a function that stops it. */
export function mountAmbient(canvas: HTMLCanvasElement) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return () => {};
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let W = 0, H = 0, dpr = 1, raf = 0, last = 0;
  let mx = 0.65, my = 0.3, gx = 0.65, gy = 0.3, glow = 0, flareUntil = 0, spin = 0;
  let orrery: { key: string; layers: Orrery } | null = null;
  let sparks: Spark[] = [];
  const motes: Mote[] = [];
  const isDark = () => document.documentElement.dataset.theme !== "light";

  const mote = (): Mote => ({ x: rand(0, W), y: rand(0, H), vx: rand(-0.08, 0.08), vy: rand(-0.05, 0.07), r: rand(0.5, 1.6), seed: Math.random() * 1000 });

  // Three diagonal light shafts from a high window, slowly breathing.
  const shaftAt = (x: number, y: number, t: number) => {
    const d = x * 0.62 + y * 0.78 - W * 0.18;
    let v = 0;
    [[0, 140], [260, 90], [470, 170]].forEach(([off, w], i) => {
      const c = d - off - Math.sin(t * 0.08 + i) * 30;
      v = Math.max(v, Math.exp(-(c * c) / (2 * w * w)));
    });
    return v;
  };

  function draw(t: number, ts: number, dark: boolean, dt: number) {
    const g = ctx!;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    const S = Math.min(Math.max(H * 1.2, W * 0.72), 1700);
    const px = -(gx - 0.5) * 18, py = -(gy - 0.5) * 12;
    const R1 = S * 0.27, R2 = S * 0.17, R3 = S * 0.105, n1 = 72, n2 = 44, n3 = 28;
    const c1: Point = [W - S * 0.36 + px, H * 0.66 + py];
    const ax = c1[0] + S * 0.05, ay = c1[1] - S * 0.2;
    const ang12 = -0.95, d12 = R1 + R2 + S * 0.012;
    const c2: Point = [c1[0] + Math.cos(ang12) * d12, c1[1] + Math.sin(ang12) * d12];
    const ang23 = -2.25, d23 = R2 + R3 + S * 0.014;
    const c3: Point = [c2[0] + Math.cos(ang23) * d23, c2[1] + Math.sin(ang23) * d23];

    const key = `${dark}|${Math.round(S)}|${dpr}`;
    if (orrery?.key !== key) {
      orrery = {
        key,
        layers: {
          ring1: clockRing(R1, n1, dpr, dark),
          face1: clockFace(R1 * 0.9, dpr, dark),
          g2: astrolabe(R2, n2, dpr, dark),
          g3: starGear(R3, n3, dpr, dark),
          arcA: arcs(R1 * 1.32, dpr, dark, 0.4),
          arcB: arcs(R1 * 1.55, dpr, dark, 2.2),
          dots: Array.from({ length: 26 }, () => ({ x: rand(-0.3, 0.55), y: rand(-0.6, 0.65), r: rand(0.8, 4.2), tw: Math.random() * 6 })),
          hang: Array.from({ length: 9 }, () => ({ dx: rand(-0.22, 0.42), len: rand(0.12, 0.55), r: rand(2, 5), d: Math.random() })),
        },
      };
    }
    const L = orrery.layers;

    const base = dark ? 0.34 : 0.3;
    const speed = 1 + glow * 7;
    spin += dt * 0.00006 * speed;
    const w1 = spin, w2 = (-spin * n1) / n2, w3 = (spin * n1) / n3;
    const gold = dark ? "232,186,110" : "120,82,38";
    const goldHi = dark ? "247,220,164" : "110,74,34";

    // Halo behind the astrolabe.
    const pulse = 0.85 + Math.sin(t * 0.6) * 0.08 + glow * 0.6;
    const hr = R2 * 2.1;
    const hg = g.createRadialGradient(c2[0], c2[1], R2 * 0.2, c2[0], c2[1], hr);
    const halo = dark ? "232,135,58" : "220,130,60";
    hg.addColorStop(0, `rgba(${halo},${(dark ? 0.13 : 0.12) * pulse})`);
    hg.addColorStop(0.55, `rgba(${halo},${(dark ? 0.07 : 0.06) * pulse})`);
    hg.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = hg;
    g.fillRect(c2[0] - hr, c2[1] - hr, hr * 2, hr * 2);

    // Spine, with an ornament diamond and beads.
    const sx = c2[0] + R2 * 0.05;
    g.strokeStyle = `rgba(${gold},${base * 0.9})`;
    g.fillStyle = `rgba(${goldHi},${base})`;
    g.lineWidth = 1.2;
    g.beginPath();
    g.moveTo(sx - 5, 0); g.lineTo(sx - 5, H); g.moveTo(sx + 5, 0); g.lineTo(sx + 5, H);
    g.stroke();
    g.lineWidth = 0.7;
    g.globalAlpha = 0.7;
    g.beginPath();
    g.moveTo(sx - 12, H * 0.02); g.lineTo(sx - 12, H * 0.32); g.moveTo(sx + 12, H * 0.02); g.lineTo(sx + 12, H * 0.32);
    g.stroke();
    g.globalAlpha = 1;
    const dy = H * 0.12;
    g.lineWidth = 1.3;
    g.beginPath();
    g.moveTo(sx, dy - 34); g.lineTo(sx + 14, dy); g.lineTo(sx, dy + 34); g.lineTo(sx - 14, dy);
    g.closePath();
    g.stroke();
    g.beginPath();
    g.moveTo(sx, dy - 18); g.lineTo(sx + 6, dy); g.lineTo(sx, dy + 18); g.lineTo(sx - 6, dy);
    g.closePath();
    g.fill();
    for (let i = 0; i < 5; i++) {
      g.beginPath();
      g.arc(sx, dy + 52 + i * 14, i === 2 ? 3 : 1.6, 0, TAU);
      g.fill();
    }

    // Hanging threads with beads.
    for (const h of L.hang) {
      const x = sx + h.dx * S, len = h.len * H;
      g.globalAlpha = 0.65;
      g.lineWidth = 0.7;
      g.beginPath(); g.moveTo(x, 0); g.lineTo(x, len); g.stroke();
      g.globalAlpha = 1;
      g.lineWidth = 1;
      g.beginPath(); g.arc(x, len + h.r, h.r, 0, TAU); g.stroke();
      if (h.d > 0.4) { g.beginPath(); g.arc(x, len + h.r, h.r * 0.4, 0, TAU); g.fill(); }
      if (h.d > 0.7) { g.beginPath(); g.arc(x, len * 0.6, 1.6, 0, TAU); g.fill(); }
    }

    // Pendulum from the spine.
    const swing = Math.sin((t * TAU) / 4.2) * 0.16;
    const py0 = H * 0.04, plen = H * 0.86;
    const bx = sx + Math.sin(swing) * plen, by = py0 + Math.cos(swing) * plen;
    g.globalAlpha = 0.55;
    g.lineWidth = 0.8;
    g.beginPath(); g.moveTo(sx, py0); g.lineTo(bx, by); g.stroke();
    g.globalAlpha = 0.9;
    g.lineWidth = 1.3;
    g.beginPath(); g.arc(bx, by, 13, 0, TAU); g.stroke();
    g.beginPath(); g.arc(bx, by, 5, 0, TAU); g.fill();
    g.globalAlpha = 1;

    const place = (img: HTMLCanvasElement, c: Point, rot: number, alpha: number) => {
      g.save();
      g.globalAlpha = alpha;
      g.translate(c[0], c[1]);
      g.rotate(rot);
      g.drawImage(img, -img.width / dpr / 2, -img.height / dpr / 2, img.width / dpr, img.height / dpr);
      g.restore();
    };
    place(L.arcB, c1, -spin * 0.35 + 0.3, base * 0.75);
    place(L.arcA, c1, spin * 0.55, base * 0.9);
    place(L.ring1, c1, w1, base);
    place(L.face1, c1, 0, base * 1.05);

    // Real-time clock hands.
    const now = new Date();
    const hrs = (now.getHours() % 12) + now.getMinutes() / 60;
    const mins = now.getMinutes() + now.getSeconds() / 60;
    const secs = now.getSeconds() + now.getMilliseconds() / 1000;
    const hand = (ang: number, len: number, lw: number, tail: number, a: number) => {
      g.save();
      g.translate(c1[0], c1[1]);
      g.rotate(ang);
      g.globalAlpha = a;
      g.lineWidth = lw;
      g.beginPath(); g.moveTo(0, tail); g.lineTo(0, -len); g.stroke();
      g.beginPath();
      g.moveTo(0, -len * 0.62); g.lineTo(lw * 2.4, -len * 0.7); g.lineTo(0, -len * 0.78); g.lineTo(-lw * 2.4, -len * 0.7);
      g.closePath();
      g.fill();
      g.restore();
    };
    g.strokeStyle = g.fillStyle = `rgba(${goldHi},1)`;
    hand((hrs / 12) * TAU, R1 * 0.42, 2.4, R1 * 0.06, base * 1.25);
    hand((mins / 60) * TAU, R1 * 0.62, 1.6, R1 * 0.08, base * 1.2);
    hand((secs / 60) * TAU, R1 * 0.7, 0.8, R1 * 0.14, base * 0.9);
    g.globalAlpha = base * 1.4;
    g.beginPath(); g.arc(c1[0], c1[1], 4, 0, TAU); g.fill();
    g.globalAlpha = 1;

    place(L.g2, c2, w2, base * 1.05);
    place(L.g3, c3, w3, base);

    // Planets orbiting the astrolabe.
    g.fillStyle = `rgba(${goldHi},1)`;
    g.strokeStyle = `rgba(${gold},1)`;
    [[1.45, 0.7, 3.6], [1.8, -0.45, 2.4], [2.25, 0.28, 4.6]].forEach(([k, sp, r], i) => {
      const rr = R2 * k, ang = t * 0.05 * sp * speed + i * 2;
      g.globalAlpha = base * 0.35;
      g.lineWidth = 0.6;
      g.beginPath(); g.arc(c2[0], c2[1], rr, 0, TAU); g.stroke();
      g.globalAlpha = base * 1.3;
      g.beginPath(); g.arc(c2[0] + Math.cos(ang) * rr, c2[1] + Math.sin(ang) * rr, r, 0, TAU); g.fill();
    });

    // Gold-leaf dots.
    for (const d of L.dots) {
      g.globalAlpha = base * 0.9 * (0.6 + Math.sin(t * 0.7 + d.tw) * 0.4);
      g.beginPath(); g.arc(ax + d.x * S, ay + d.y * S, d.r, 0, TAU); g.fill();
    }
    g.globalAlpha = 1;

    // Sparks at the meshing points while flared.
    if (glow > 0.05) {
      const meshes: Point[] = [
        [c1[0] + Math.cos(ang12) * (R1 + S * 0.006), c1[1] + Math.sin(ang12) * (R1 + S * 0.006)],
        [c2[0] + Math.cos(ang23) * (R2 + S * 0.007), c2[1] + Math.sin(ang23) * (R2 + S * 0.007)],
      ];
      for (const [x, y] of meshes) {
        if (Math.random() < glow * 0.5) sparks.push({ x, y, vx: gauss() * 2.2, vy: -rand(0.5, 2.4), r: rand(0.5, 1.2), heat: 1, cool: rand(0.012, 0.025) });
      }
    }
    g.globalCompositeOperation = dark ? "lighter" : "source-over";
    sparks = sparks.filter((e) => {
      e.vy += 0.03; e.x += e.vx; e.y += e.vy; e.heat -= e.cool;
      if (e.heat <= 0) return false;
      g.strokeStyle = sparkColor(e.heat, e.heat * 0.8);
      g.lineWidth = e.r;
      g.beginPath(); g.moveTo(e.x - e.vx * 3, e.y - e.vy * 3); g.lineTo(e.x, e.y); g.stroke();
      return true;
    });

    // Dust motes, lit where they cross a window shaft.
    const target = Math.round((W * H) / 14000);
    while (motes.length < target) motes.push(mote());
    motes.length = target;
    for (const m of motes) {
      m.vx += (noise(m.x * 0.004, m.y * 0.004 + t * 0.05, 5) - 0.5) * 0.004;
      m.vx *= 0.995;
      m.vy += (noise(m.y * 0.004, t * 0.05, 9) - 0.5) * 0.003;
      m.vy *= 0.995;
      m.x += m.vx * (1 + glow * 2);
      m.y += m.vy * (1 + glow * 2);
      if (m.x < -10) m.x = W + 10;
      if (m.x > W + 10) m.x = -10;
      if (m.y < -10) m.y = H + 10;
      if (m.y > H + 10) m.y = -10;
      const lit = shaftAt(m.x, m.y, t), glint = 0.5 + Math.sin(ts * 0.004 + m.seed) * 0.5;
      const a = (0.05 + lit * (0.6 + glint * 0.3)) * (dark ? 0.8 : 0.45);
      if (a < 0.03) continue;
      g.fillStyle = dark ? `rgba(255,226,180,${a})` : `rgba(120,90,50,${a})`;
      g.beginPath(); g.arc(m.x, m.y, m.r * (0.7 + lit * 0.6), 0, TAU); g.fill();
    }
    g.globalCompositeOperation = "source-over";
  }

  function frame(ts: number) {
    gx += (mx - gx) * 0.025;
    gy += (my - gy) * 0.025;
    glow += ((flareUntil > ts ? 1 : 0) - glow) * 0.035;
    ctx!.setTransform(1, 0, 0, 1, 0, 0);
    ctx!.clearRect(0, 0, canvas.width, canvas.height);
    draw(ts / 1000, ts, isDark(), Math.min(64, ts - (last || ts)));
    last = ts;
    if (!reduce) raf = requestAnimationFrame(frame);
  }

  // With reduced motion the scene is a still frame, redrawn only when something changes it.
  const redraw = () => {
    if (reduce) requestAnimationFrame(frame);
  };
  const size = () => {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth;
    H = window.innerHeight;
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    orrery = null;
    redraw();
  };
  const onMove = (e: PointerEvent) => {
    mx = e.clientX / W;
    my = e.clientY / H;
  };
  const onFlare = (e: Event) => {
    flareUntil = performance.now() + ((e as CustomEvent<{ ms?: number }>).detail?.ms ?? 2200);
  };
  const onVisibility = () => {
    cancelAnimationFrame(raf);
    if (!document.hidden && !reduce) raf = requestAnimationFrame(frame);
  };
  const themeObserver = new MutationObserver(redraw);
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  // The numerals are drawn in Newsreader; rebuild the layers once the web font is in.
  void document.fonts?.ready.then(() => {
    orrery = null;
    redraw();
  });

  size();
  window.addEventListener("resize", size);
  window.addEventListener("pointermove", onMove);
  window.addEventListener(FLARE_EVENT, onFlare);
  document.addEventListener("visibilitychange", onVisibility);
  raf = requestAnimationFrame(frame);

  return () => {
    cancelAnimationFrame(raf);
    themeObserver.disconnect();
    window.removeEventListener("resize", size);
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener(FLARE_EVENT, onFlare);
    document.removeEventListener("visibilitychange", onVisibility);
  };
}
