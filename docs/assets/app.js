/* BioQubit Atlas — site script. No external libraries, no inline handlers (CSP-safe). */
(() => {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let SITE = null, DATA = null, RES = null;
  const state = { q: "", cat: null, type: "all", sort: "section" };

  /* ================================================================ art
     Original line illustrations, one per theme (viewBox 0 0 80 80). */
  const V = "#a38bff", C = "#67e0ef", M = "#59dfb0", A = "#ffc578", W = "#e9e5ff";
  const ART = {
    "biological-qubits": `<svg viewBox="0 0 80 80" aria-hidden="true"><ellipse cx="40" cy="56" rx="17" ry="6" fill="none" stroke="${V}" stroke-width="1.6"/><path d="M23 56V34M57 56V34" stroke="${V}" stroke-width="1.6"/><ellipse cx="40" cy="34" rx="17" ry="6" fill="rgba(163,139,255,.12)" stroke="${V}" stroke-width="1.6"/><path d="M29 38.6v20M35 39.8v21M41 40v21M47 39.6v20.6M52.5 38.5v19" stroke="${V}" stroke-width="1" opacity=".55"/><circle cx="40" cy="47" r="3.2" fill="${M}"/><path d="M40 30V10" stroke="${C}" stroke-width="2.4" stroke-linecap="round"/><path d="M34.5 15.5L40 9.5l5.5 6" fill="none" stroke="${C}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><ellipse cx="40" cy="18" rx="10" ry="3.2" fill="none" stroke="${C}" stroke-width="1" stroke-dasharray="2 2.5" opacity=".7"/></svg>`,
    "radical-pair": `<svg viewBox="0 0 80 80" aria-hidden="true"><circle cx="40" cy="40" r="31" fill="none" stroke="${V}" stroke-width="1" opacity=".35"/><path d="M40 9v5M40 66v5M9 40h5M66 40h5" stroke="${V}" stroke-width="1.4" opacity=".6"/><circle cx="25" cy="44" r="9" fill="rgba(103,224,239,.10)" stroke="${C}" stroke-width="1.6"/><circle cx="55" cy="44" r="9" fill="rgba(163,139,255,.12)" stroke="${V}" stroke-width="1.6"/><path d="M25 50V37M21.5 40.5L25 36.5l3.5 4" fill="none" stroke="${C}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M55 37v13M51.5 46.5L55 50.5l3.5-4" fill="none" stroke="${V}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M34 44h12" stroke="${W}" stroke-width="1.2" stroke-dasharray="2 2.4"/><path d="M40 18l4 9h-8z" fill="${A}"/></svg>`,
    "methods": `<svg viewBox="0 0 80 80" aria-hidden="true"><path d="M31 8h18v9H31zM33 17h14l-3 17h-8z" fill="rgba(163,139,255,.12)" stroke="${V}" stroke-width="1.6" stroke-linejoin="round"/><path d="M38 34h4v5h-4z" fill="${V}"/><path d="M40 39L28 58M40 39l12 19" stroke="${C}" stroke-width="1.2" opacity=".7"/><path d="M14 64c4 0 4-7 8-7s4 7 8 7 4-11 10-11 6 11 10 11 4-7 8-7 4 7 8 7" fill="none" stroke="${M}" stroke-width="1.8" stroke-linecap="round"/><path d="M12 70h56" stroke="${V}" stroke-width="1" opacity=".4"/></svg>`,
    "flavin-spin": `<svg viewBox="0 0 80 80" aria-hidden="true"><g fill="rgba(163,139,255,.08)" stroke="${V}" stroke-width="1.6" stroke-linejoin="round"><path d="M10 40l7-12h14l7 12-7 12H17z"/><path d="M31 28h14l7 12-7 12H31l-7-12z"/><path d="M45 28h14l7 12-7 12H45l-7-12z"/></g><circle cx="31" cy="28" r="2.6" fill="${C}"/><circle cx="45" cy="52" r="2.6" fill="${C}"/><text x="27" y="23" fill="${C}" font-size="7" font-family="DM Mono, monospace">N5</text><path d="M66 18v-9M63 12l3-3.5 3 3.5" fill="none" stroke="${M}" stroke-width="1.8" stroke-linecap="round"/><circle cx="66" cy="22" r="2.2" fill="${M}"/><path d="M14 64h52" stroke="${A}" stroke-width="1.6" stroke-dasharray="1 4" stroke-linecap="round"/></svg>`,
    "lov": `<svg viewBox="0 0 80 80" aria-hidden="true"><path d="M20 62C18 38 36 20 64 16c2 26-14 46-44 46z" fill="rgba(89,223,176,.10)" stroke="${M}" stroke-width="1.6" stroke-linejoin="round"/><path d="M20 62C32 48 44 36 58 22" stroke="${M}" stroke-width="1.2" opacity=".75"/><path d="M33 49l-2-9M41 41l-2-9M49 33l-2-8" stroke="${M}" stroke-width="1" opacity=".55"/><g stroke="${C}" stroke-width="1.8" stroke-linecap="round"><path d="M10 12l9 7"/><path d="M8 24l10 3"/><path d="M20 6l4 10"/></g><circle cx="47" cy="40" r="3" fill="${A}"/></svg>`,
    "posner": `<svg viewBox="0 0 80 80" aria-hidden="true"><g stroke="${V}" stroke-width="1" opacity=".55"><path d="M40 16L60 28v24L40 64 20 52V28z" fill="none"/><path d="M40 16v48M20 28l40 24M60 28L20 52"/></g><g fill="rgba(163,139,255,.18)" stroke="${V}" stroke-width="1.4"><circle cx="40" cy="16" r="5"/><circle cx="60" cy="28" r="5"/><circle cx="60" cy="52" r="5"/><circle cx="40" cy="64" r="5"/><circle cx="20" cy="52" r="5"/><circle cx="20" cy="28" r="5"/></g><circle cx="40" cy="40" r="6" fill="rgba(103,224,239,.18)" stroke="${C}" stroke-width="1.6"/><text x="36.4" y="42.6" fill="${C}" font-size="7" font-family="DM Mono, monospace">³¹P</text></svg>`,
    "theory": `<svg viewBox="0 0 80 80" aria-hidden="true"><circle cx="40" cy="42" r="26" fill="none" stroke="${V}" stroke-width="1.6"/><ellipse cx="40" cy="42" rx="26" ry="8" fill="none" stroke="${V}" stroke-width="1" opacity=".6"/><path d="M40 12v60" stroke="${V}" stroke-width="1" opacity=".4" stroke-dasharray="2 3"/><path d="M40 42l15-17" stroke="${C}" stroke-width="2.2" stroke-linecap="round"/><circle cx="55" cy="25" r="3" fill="${C}"/><text x="36" y="10" fill="${W}" font-size="7" font-family="DM Mono, monospace">|0⟩</text><text x="36" y="79" fill="${W}" font-size="7" font-family="DM Mono, monospace">|1⟩</text></svg>`,
    "reviews": `<svg viewBox="0 0 80 80" aria-hidden="true"><path d="M40 22C32 16 20 15 10 17v42c10-2 22-1 30 5 8-6 20-7 30-5V17c-10-2-22-1-30 5z" fill="rgba(163,139,255,.08)" stroke="${V}" stroke-width="1.6" stroke-linejoin="round"/><path d="M40 22v42" stroke="${V}" stroke-width="1.2"/><path d="M17 28c6-1 12 0 17 2M17 36c6-1 12 0 17 2M17 44c6-1 12 0 17 2M46 30c5-2 11-3 17-2M46 38c5-2 11-3 17-2" stroke="${C}" stroke-width="1" opacity=".6"/></svg>`
  };
  const art = k => ART[k] || ART.theory;

  /* ================================================================ simulator
     Semiclassical radical pair: electron 1 precesses about B + a·n (one nucleus),
     electron 2 about B only. Born antiparallel (singlet-like). Singlet character
     P = (1 − S1·S2)/2; yield Φ = ∫ k e^{−kt} P(t) dt, done in closed form. */
  const GAMMA = 2 * Math.PI * 28.025;   // rad µs⁻¹ mT⁻¹ (free electron)
  const A_HF = 1.0, K = 10.0;           // hyperfine (mT), recombination rate (µs⁻¹, i.e. 100 ns lifetime)
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const scale = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
  const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const norm = a => { const n = Math.hypot(...a) || 1; return scale(a, 1 / n); };
  function fib(n) { const pts = [], g = Math.PI * (3 - Math.sqrt(5)); for (let i = 0; i < n; i++) { const y = 1 - 2 * (i + .5) / n, r = Math.sqrt(1 - y * y); pts.push([Math.cos(g * i) * r, Math.sin(g * i) * r, y]); } return pts; }
  function decompose(S0, axis) { const P = scale(axis, dot(S0, axis)); return [P, sub(S0, P), cross(axis, S0)]; }
  const Lc = w => K * K / (K * K + w * w), Ls = w => K * w / (K * K + w * w);
  function pairYield(B, n, S0) {
    const O1 = add([0, 0, B], scale(n, A_HF)), w1 = GAMMA * Math.hypot(...O1), u1 = norm(O1);
    const w2 = GAMMA * B, u2 = [0, 0, 1];
    const [P1, Q1, R1] = decompose(S0, u1), [P2, Q2, R2] = decompose(scale(S0, -1), u2);
    const d = w1 - w2, s = w1 + w2;
    const cc = (Lc(d) + Lc(s)) / 2, cs = (Ls(s) - Ls(d)) / 2, sc = (Ls(s) + Ls(d)) / 2, ss = (Lc(d) - Lc(s)) / 2;
    const meanDot = dot(P1, P2) + dot(P1, Q2) * Lc(w2) + dot(P1, R2) * Ls(w2) + dot(Q1, P2) * Lc(w1) + dot(R1, P2) * Ls(w1)
      + dot(Q1, Q2) * cc + dot(Q1, R2) * cs + dot(R1, Q2) * sc + dot(R1, R2) * ss;
    return (1 - meanDot) / 2;
  }
  const NUC = fib(26), SPIN = fib(26);
  const yieldAt = B => { let t = 0; for (const n of NUC) for (const S0 of SPIN) t += pairYield(B, n, S0); return t / (NUC.length * SPIN.length); };
  const MARY = []; for (let i = 0; i <= 125; i++) { const B = i * 0.04; MARY.push([B, yieldAt(B)]); }
  const Y0 = MARY[0][1];

  function rotate(v, axis, ang) { const [P, Q, R] = decompose(v, axis); return add(P, add(scale(Q, Math.cos(ang)), scale(R, Math.sin(ang)))); }

  function setupCanvas(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2), w = cv.width, h = cv.height;
    cv.width = w * dpr; cv.height = h * dpr;
    const ctx = cv.getContext("2d"); ctx.scale(dpr, dpr); return { ctx, w, h };
  }

  function initSim() {
    const cv = $("#simCanvas"), mc = $("#maryCanvas");
    if (!cv || !cv.getContext) return;
    const { ctx, w, h } = setupCanvas(cv), mary = setupCanvas(mc);
    const slider = $("#bField"), out = $("#bOut"), yNum = $("#yieldNum"), yDel = $("#yieldDelta"), pauseBtn = $("#simPause");
    const NHAT = norm([0.55, 0.35, 0.76]);
    let B = +slider.value, t = 0, S1, S2, trail1 = [], trail2 = [], paused = REDUCED, born = 0, last = performance.now();
    const TILT = 0.36, CT = Math.cos(TILT), ST = Math.sin(TILT);
    const proj = (v, cx, cy, r) => [cx + v[0] * r, cy - (v[2] * CT - v[1] * ST) * r, v[1] * CT + v[2] * ST];
    function rebirth() { const s0 = norm([0.82, -0.25, 0.5]); S1 = s0; S2 = scale(s0, -1); trail1 = []; trail2 = []; born = t; }
    rebirth();

    function drawSphere(cx, cy, r, label, sub, col) {
      const g = ctx.createRadialGradient(cx - r * .3, cy - r * .35, r * .1, cx, cy, r);
      g.addColorStop(0, "rgba(163,139,255,.16)"); g.addColorStop(1, "rgba(14,20,38,.0)");
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.fill();
      ctx.strokeStyle = "rgba(164,181,224,.28)"; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.stroke();
      ctx.strokeStyle = "rgba(164,181,224,.16)"; ctx.beginPath(); ctx.ellipse(cx, cy, r, r * ST, 0, 0, 7); ctx.stroke();
      ctx.fillStyle = col; ctx.font = "600 13px 'DM Sans', sans-serif"; ctx.textAlign = "center";
      ctx.fillText(label, cx, cy + r + 22);
      ctx.fillStyle = "rgba(148,162,191,.9)"; ctx.font = "12px 'DM Sans', sans-serif"; ctx.fillText(sub, cx, cy + r + 38);
    }
    function arrow(x0, y0, x1, y1, col, wid) {
      const a = Math.atan2(y1 - y0, x1 - x0), hl = 9 + wid;
      ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = wid; ctx.lineCap = "round";
      ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1 - Math.cos(a) * hl * .6, y1 - Math.sin(a) * hl * .6); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x1 - hl * Math.cos(a - .42), y1 - hl * Math.sin(a - .42)); ctx.lineTo(x1 - hl * Math.cos(a + .42), y1 - hl * Math.sin(a + .42)); ctx.closePath(); ctx.fill();
    }
    function drawSpin(cx, cy, r, v, trail, col) {
      for (let i = 1; i < trail.length; i++) {
        const a = trail[i - 1], b = trail[i];
        ctx.strokeStyle = col.replace("1)", (i / trail.length * .55).toFixed(2) + ")"); ctx.lineWidth = 1.6;
        ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
      }
      const p = proj(v, cx, cy, r * .92);
      arrow(cx, cy, p[0], p[1], col, p[2] < 0 ? 2.4 : 3.2);
      ctx.fillStyle = "#e9e5ff"; ctx.beginPath(); ctx.arc(cx, cy, 3, 0, 7); ctx.fill();
      return p;
    }
    function frame(now) {
      const dt = Math.min((now - last) / 1000, .05); last = now;
      if (!paused) {
        const step = dt * 0.045;                              // simulated µs per real second
        const O1 = add([0, 0, B], scale(NHAT, A_HF));
        S1 = rotate(S1, norm(O1), GAMMA * Math.hypot(...O1) * step);
        S2 = rotate(S2, [0, 0, 1], GAMMA * B * step);
        t += step; if (t - born > 0.3) rebirth();
      }
      const r = Math.min(88, h * .32), c1 = [w * .27, h * .4], c2 = [w * .73, h * .4];
      ctx.clearRect(0, 0, w, h);
      // field arrows
      const bl = 26 + Math.min(B, 5) * 14;
      for (const cx of [c1[0] - r - 22, c2[0] + r + 22]) {
        ctx.globalAlpha = .35 + Math.min(B, 5) * .12;
        arrow(cx, c1[1] + bl / 2, cx, c1[1] - bl / 2, "#ffc578", 1.8);
        ctx.globalAlpha = 1; ctx.fillStyle = "#ffc578"; ctx.font = "italic 600 14px 'Playfair Display', serif"; ctx.textAlign = "center";
        ctx.fillText("B", cx, c1[1] + bl / 2 + 16);
      }
      drawSphere(c1[0], c1[1], r, "Electron 1", "feels a nucleus", "#67e0ef");
      drawSphere(c2[0], c2[1], r, "Electron 2", "feels the field only", "#c1b4ff");
      // hyperfine axis
      const hp = proj(NHAT, c1[0], c1[1], r);
      ctx.setLineDash([3, 4]); ctx.strokeStyle = "rgba(89,223,176,.7)"; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(c1[0], c1[1]); ctx.lineTo(hp[0], hp[1]); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = "#59dfb0"; ctx.beginPath(); ctx.arc(hp[0], hp[1], 3.2, 0, 7); ctx.fill();
      const p1 = drawSpin(c1[0], c1[1], r, S1, trail1, "rgba(103,224,239,1)");
      const p2 = drawSpin(c2[0], c2[1], r, S2, trail2, "rgba(193,180,255,1)");
      if (!paused) { trail1.push(p1); trail2.push(p2); if (trail1.length > 46) { trail1.shift(); trail2.shift(); } }
      // singlet meter between spheres
      const P = (1 - dot(S1, S2)) / 2, mx = w / 2, mh = r * 1.5, my = c1[1] - mh / 2;
      ctx.fillStyle = "rgba(164,181,224,.12)"; roundRect(mx - 6, my, 12, mh, 6); ctx.fill();
      const gr = ctx.createLinearGradient(0, my + mh, 0, my); gr.addColorStop(0, "#7456e5"); gr.addColorStop(1, "#67e0ef");
      ctx.fillStyle = gr; roundRect(mx - 6, my + mh * (1 - P), 12, mh * P, 6); ctx.fill();
      ctx.fillStyle = "rgba(233,229,255,.85)"; ctx.font = "12px 'DM Sans', sans-serif"; ctx.textAlign = "center";
      ctx.fillText("singlet", mx, my - 8); ctx.fillStyle = "rgba(148,162,191,.85)"; ctx.fillText("triplet", mx, my + mh + 16);
      if (!REDUCED) requestAnimationFrame(frame);
    }
    function roundRect(x, y, ww, hh, rr) { ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(x, y, ww, Math.max(hh, .01), Math.min(rr, hh / 2)); else ctx.rect(x, y, ww, hh); }

    function drawMary() {
      const c = mary.ctx, W2 = mary.w, H2 = mary.h, pad = { l: 4, r: 4, t: 10, b: 20 };
      const ys = MARY.map(p => p[1]), lo = Math.min(...ys), hi = Math.max(...ys), span = (hi - lo) || 1;
      const X = b => pad.l + b / 5 * (W2 - pad.l - pad.r), Y = y => pad.t + (1 - (y - lo) / span) * (H2 - pad.t - pad.b);
      c.clearRect(0, 0, W2, H2);
      c.strokeStyle = "rgba(164,181,224,.18)"; c.lineWidth = 1; c.beginPath(); c.moveTo(pad.l, H2 - pad.b); c.lineTo(W2 - pad.r, H2 - pad.b); c.stroke();
      const g = c.createLinearGradient(0, 0, W2, 0); g.addColorStop(0, "#67e0ef"); g.addColorStop(1, "#a38bff");
      c.strokeStyle = g; c.lineWidth = 2.2; c.beginPath(); MARY.forEach(([b, y], i) => i ? c.lineTo(X(b), Y(y)) : c.moveTo(X(b), Y(y))); c.stroke();
      c.fillStyle = "rgba(89,223,176,.9)"; c.fillRect(X(.05) - .5, pad.t, 1, H2 - pad.t - pad.b);
      const yb = yieldAt(B);  // exact, ~700 closed-form terms
      c.fillStyle = "#fff"; c.beginPath(); c.arc(X(B), Y(yb), 4.5, 0, 7); c.fill();
      c.strokeStyle = "#7456e5"; c.lineWidth = 2; c.stroke();
      c.fillStyle = "rgba(148,162,191,.9)"; c.font = "11px 'DM Mono', monospace"; c.textAlign = "left"; c.fillText("singlet yield vs field", pad.l, H2 - 5);
      c.textAlign = "right"; c.fillText("5 mT", W2 - pad.r, H2 - 5);
      yNum.textContent = (yb * 100).toFixed(1) + "%";
      const d = (yb - Y0) / Y0 * 100;
      yDel.textContent = B < 0.005 ? "zero-field reference" : `${d >= 0 ? "+" : "−"}${Math.abs(d).toFixed(1)}% vs zero field`;
    }
    slider.addEventListener("input", () => { B = +slider.value; out.textContent = B.toFixed(2) + " mT"; drawMary(); if (REDUCED) frame(performance.now()); });
    pauseBtn.addEventListener("click", () => {
      paused = !paused; pauseBtn.setAttribute("aria-pressed", String(paused));
      pauseBtn.setAttribute("aria-label", paused ? "Play animation" : "Pause animation");
      pauseBtn.innerHTML = paused
        ? '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M6 4l10 6-10 6z" fill="currentColor"/></svg>'
        : '<svg viewBox="0 0 20 20" aria-hidden="true"><rect x="5" y="4" width="3.4" height="12" rx="1" fill="currentColor"/><rect x="11.6" y="4" width="3.4" height="12" rx="1" fill="currentColor"/></svg>';
      if (REDUCED && !paused) { paused = true; toast("Animation is off because your system asks for reduced motion."); }
    });
    if (REDUCED) { pauseBtn.hidden = true; }
    drawMary();
    document.fonts?.ready.then(() => { drawMary(); if (REDUCED) frame(performance.now()); });
    requestAnimationFrame(frame);
  }

  /* ================================================================ helpers */
  function toast(msg) { const t = $("#toast"); t.textContent = msg; t.classList.add("show"); clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("show"), 2200); }
  const authorsShort = a => { a = (a || []).filter(x => x !== "et al."); return a.length <= 3 ? a.join(", ") : `${a[0]}, ${a[1]} … ${a[a.length - 1]}`; };
  const isNew = p => p.added && (Date.now() - Date.parse(p.added)) / 864e5 < 30 && p.added > "2026-11-23";
  const safeUrl = u => /^https:\/\//i.test(u || "") ? u : "#";
  function bibtex(p) {
    const name = n => { if (n === "et al.") return "others"; const t = n.split(" "); return t.length < 2 ? n : `${t.slice(-1)}, ${t.slice(0, -1).join(" ")}`; };
    const kind = p.type === "preprint" ? "misc" : "article";
    const f = [["title", `{${p.title}}`], ["author", (p.authors || []).map(name).join(" and ")], ["year", p.year], [kind === "article" ? "journal" : "howpublished", p.journal]];
    if (p.volume) f.push(["volume", p.volume]); if (p.pages) f.push(["pages", String(p.pages).replace("–", "--")]);
    if (p.doi) f.push(["doi", p.doi]); if (p.arxiv) f.push(["eprint", p.arxiv]);
    return `@${kind}{${p.id},\n` + f.map(([k, v]) => `  ${k} = {${v}}`).join(",\n") + "\n}";
  }
  function copy(text, ok) { (navigator.clipboard?.writeText(text) || Promise.reject()).then(() => toast(ok), () => toast("Copy failed; your browser blocked clipboard access.")); }
  const catOf = k => DATA.categories.find(c => c.key === k) || { title: k, emoji: "" };
  const shortTitle = t => t.split(/ (?:—|&) /)[0];

  /* ================================================================ header + themes */
  function renderStats() {
    const P = DATA.papers, ys = P.map(p => +p.year).filter(Boolean);
    const items = [[P.length, "papers"], [DATA.categories.filter(c => P.some(p => p.category === c.key)).length, "themes"],
      [P.filter(p => p.oa).length, "free to read"], [`${Math.min(...ys)}–${Math.max(...ys)}`, "years covered"]];
    $("#stats").innerHTML = items.map(([v, l]) => `<div><dt>${esc(l)}</dt><dd>${esc(v)}</dd></div>`).join("");
  }
  function renderThemes() {
    const used = DATA.categories.filter(c => DATA.papers.some(p => p.category === c.key));
    $("#themeGrid").innerHTML = used.map(c => {
      const n = DATA.papers.filter(p => p.category === c.key).length;
      return `<button class="theme" type="button" data-theme="${esc(c.key)}"><span class="theme-art">${art(c.key)}</span>
        <span><h3>${esc(shortTitle(c.title))}</h3><p>${esc(c.blurb)}</p><span class="n">${n} paper${n === 1 ? "" : "s"}</span></span></button>`;
    }).join("");
  }

  /* ================================================================ papers */
  const TYPES = [["all", "All"], ["article", "Articles"], ["preprint", "Preprints"], ["review", "Reviews"], ["oa", "Free to read"]];
  function matches(p) {
    if (state.cat && p.category !== state.cat) return false;
    if (state.type === "oa" && !p.oa) return false;
    if (["article", "preprint", "review"].includes(state.type) && (p.type === "letter" ? "article" : p.type) !== state.type) return false;
    if (!state.q) return true;
    const hay = [p.title, (p.authors || []).join(" "), p.journal, (p.tags || []).join(" "), p.year, p.note, p.doi].join(" ").toLowerCase();
    return state.q.toLowerCase().split(/\s+/).every(w => hay.includes(w));
  }
  function card(p) {
    const badges = (isNew(p) ? '<span class="badge b-new">new</span>' : "") +
      (p.type === "preprint" ? '<span class="badge b-pre">preprint</span>' : "") +
      (p.type === "review" ? '<span class="badge b-rev">review</span>' : "") +
      (p.oa ? '<span class="badge b-oa">free</span>' : "");
    const vol = p.volume ? `, ${esc(p.volume)}` : "", pg = p.pages ? `, ${esc(p.pages)}` : "";
    return `<article class="paper"><div class="paper-art" title="${esc(catOf(p.category).title)}">${art(p.category)}</div><div>
      <h3><a href="${esc(safeUrl(p.link))}" target="_blank" rel="noopener noreferrer">${esc(p.title)}</a>${badges}</h3>
      <div class="meta">${esc(authorsShort(p.authors))} · <em>${esc(p.journal)}</em>${vol}${pg} · <b>${esc(p.year)}</b></div>
      ${(p.tags || []).length ? `<div class="tags">${p.tags.map(t => `<button class="tag" type="button" data-tag="${esc(t)}">${esc(t)}</button>`).join("")}</div>` : ""}
      ${p.note ? `<p class="note">${esc(p.note)}</p>` : ""}
      <div class="actions">${p.doi ? `<a href="https://doi.org/${encodeURI(p.doi)}" target="_blank" rel="noopener noreferrer">doi:${esc(p.doi)}</a>` : ""}
        <button type="button" data-bib="${esc(p.id)}">Copy BibTeX</button><button type="button" data-cite="${esc(p.id)}">Copy citation</button></div>
    </div></article>`;
  }
  function renderChips() {
    const used = DATA.categories.filter(c => DATA.papers.some(p => p.category === c.key));
    $("#cats").innerHTML = [`<button class="chip" type="button" data-cat="" aria-pressed="${!state.cat}">All themes</button>`]
      .concat(used.map(c => `<button class="chip" type="button" data-cat="${esc(c.key)}" aria-pressed="${state.cat === c.key}">${esc(c.emoji)} ${esc(shortTitle(c.title))}</button>`)).join("");
    $("#types").innerHTML = TYPES.map(([k, l]) => `<button class="chip" type="button" data-type="${k}" aria-pressed="${state.type === k}">${l}</button>`).join("");
  }
  function renderList() {
    const items = DATA.papers.filter(matches);
    $("#count").textContent = `${items.length} of ${DATA.papers.length}`;
    if (!items.length) { $("#list").innerHTML = '<p class="empty">No papers match. Try fewer words or another theme.</p>'; return; }
    let html = "";
    if (state.sort === "section") {
      for (const c of DATA.categories) {
        const sub = items.filter(p => p.category === c.key); if (!sub.length) continue;
        html += `<h3 class="group-h">${art(c.key)}<span>${esc(c.title)} <small>${sub.length}</small></span></h3>` + sub.map(card).join("");
      }
    } else if (state.sort === "timeline") {
      const s = [...items].sort((a, b) => b.year - a.year); let y = null;
      for (const p of s) { if (p.year !== y) { y = p.year; html += `<h3 class="year-h">${esc(y)}</h3>`; } html += card(p); }
    } else {
      const s = [...items];
      if (state.sort === "new") s.sort((a, b) => b.year - a.year);
      if (state.sort === "old") s.sort((a, b) => a.year - b.year);
      if (state.sort === "added") s.sort((a, b) => (b.added || "").localeCompare(a.added || "") || b.year - a.year);
      html = s.map(card).join("");
    }
    $("#list").innerHTML = html;
  }
  const rerender = () => { renderChips(); renderList(); };
  function citation(p) {
    const a = (p.authors || []).filter(x => x !== "et al.");
    const au = a.length > 3 ? `${a[0]} et al.` : a.join(", ");
    return `${au} (${p.year}). ${p.title}. ${p.journal}${p.volume ? `, ${p.volume}` : ""}${p.pages ? `, ${p.pages}` : ""}.${p.doi ? ` https://doi.org/${p.doi}` : ""}`;
  }

  /* ================================================================ library */
  function renderLibrary() {
    if (!RES) return;
    const path = `<ol class="path">${(RES.path || []).map(s => `<li>${esc(s.replace(/\*/g, ""))}</li>`).join("")}</ol>`;
    const books = (RES.books || []).map(g => `<div class="book-group"><h4>${esc(g.group)}</h4>${g.items.map(b =>
      `<div class="book"><b>${esc(b.title)}</b><span>${esc(b.authors)}${b.publisher ? ", " + esc(b.publisher) : ""}, ${esc(b.year)}</span><p>${esc(b.why)}</p></div>`).join("")}</div>`).join("");
    const reviews = `<ul class="reviews">${(RES.reviews || []).map(r => `<li>${r.doi ? `<a href="https://doi.org/${encodeURI(r.doi)}" target="_blank" rel="noopener noreferrer">${esc(r.title)}</a>` : `<b>${esc(r.title)}</b>`}<span>${esc(r.cite)}: ${esc(r.why)}</span></li>`).join("")}</ul>`;
    const tools = `<div class="tools">${(RES.software || []).concat(RES.community || []).map(t =>
      t.url ? `<a class="tool" href="${esc(safeUrl(t.url))}" target="_blank" rel="noopener noreferrer"><b>${esc(t.name)}</b>${esc(t.what)}</a>`
            : `<div class="tool"><b>${esc(t.name)}</b>${esc(t.what)}</div>`).join("")}</div>`;
    $("#libraryBody").innerHTML = `<div class="lib"><div class="lib-col"><h3>Where to start</h3>${path}<h3>Books</h3>${books}</div>
      <div class="lib-col"><h3>Landmark reviews</h3>${reviews}<h3 class="lib-sub">Software &amp; community</h3>${tools}</div></div>`;
  }

  /* ================================================================ suggest */
  const ID_RX = /(10\.\d{4,9}\/\S+)|(\b\d{4}\.\d{4,5}(v\d+)?\b)|(^https?:\/\/\S+$)/i;
  function readForm() {
    const v = id => $(id).value.trim();
    return { doi: v("#sDoi"), title: v("#sTitle"), name: v("#sName"), email: v("#sMail"), why: v("#sWhy") };
  }
  function validId() {
    const f = readForm(), ok = ID_RX.test(f.doi), inp = $("#sDoi"), hint = $("#sDoiHint");
    inp.setAttribute("aria-invalid", String(!ok));
    hint.classList.toggle("err", !ok);
    hint.textContent = ok ? "Paste a DOI, an arXiv id like 2501.01234, or the paper's web address."
      : f.doi ? "That doesn't look like a DOI, arXiv id or web address." : "Add the paper's DOI, arXiv id or web address first.";
    if (!ok) inp.focus();
    return ok ? f : null;
  }
  function mailAddress() { const [d, u] = SITE.curator.c; return `${[...u].reverse().join("")}@${[...d].reverse().join("")}`; }
  function sendMail() {
    const f = validId(); if (!f) return;
    const subject = `Paper suggestion for the BioQubit Atlas: ${f.title || f.doi}`.slice(0, 180);
    const body = [`Paper: ${f.doi}`, f.title && `Title: ${f.title}`, f.why && `\nWhy it belongs:\n${f.why}`,
      `\n— ${f.name || "Suggested via the BioQubit Atlas website"}${f.email ? ` <${f.email}>` : ""}`].filter(Boolean).join("\n");
    window.location.href = `mailto:${mailAddress()}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    $("#formMsg").textContent = "Your email app should open with the message ready. Press send there to deliver it.";
  }
  function issueUrl(id, title, why) {
    const u = new URL(`${SITE.repo_url}/issues/new`);
    u.searchParams.set("template", "suggest-paper.yml"); u.searchParams.set("title", title);
    u.searchParams.set("identifier", id); if (why) u.searchParams.set("why", why);
    return u.toString();
  }
  function sendGh() {
    const f = validId(); if (!f) return;
    window.open(issueUrl(f.doi, `Suggestion: ${f.title || f.doi}`.slice(0, 200), f.why), "_blank", "noopener");
    $("#formMsg").textContent = "GitHub opened in a new tab. Your name and email are not included there, because issues are public.";
  }

  /* ================================================================ curator desk */
  async function loadPending() {
    const box = $("#pending");
    box.innerHTML = '<p class="muted">Checking GitHub…</p>';
    try {
      const r = await fetch(`https://api.github.com/repos/${encodeURIComponent(SITE.owner)}/${encodeURIComponent(SITE.repo)}/issues?labels=candidate&state=open&per_page=30`,
        { headers: { Accept: "application/vnd.github+json" } });
      if (r.status === 403) throw new Error("GitHub's hourly limit for anonymous visitors is used up. Try again later.");
      if (!r.ok) throw new Error(`GitHub answered ${r.status}.`);
      const items = (await r.json()).filter(i => !i.pull_request);
      box.innerHTML = items.length ? items.map(i => {
        const tier = (i.labels || []).map(l => l.name).find(n => ["high-impact", "specialist", "preprint"].includes(n)) || "";
        return `<div class="pend"><div><b>${esc(i.title.replace(/^📄\s*/, ""))}</b><span>#${i.number}${tier ? " · " + esc(tier) : ""} · ${esc(new Date(i.created_at).toLocaleDateString())}</span></div>
          <a class="btn btn-sm btn-ghost" href="${esc(safeUrl(i.html_url))}" target="_blank" rel="noopener noreferrer">Review</a></div>`;
      }).join("") : '<p class="muted">Nothing waiting. The watcher will add candidates here when it finds them.</p>';
    } catch (e) { box.innerHTML = `<p class="muted">Couldn't load candidates: ${esc(e.message)}</p>`; }
  }
  function openDesk() {
    const d = $("#desk");
    $("#deskLinks").innerHTML = [
      ["All candidates", `${SITE.repo_url}/issues?q=is%3Aissue+is%3Aopen+label%3Acandidate`],
      ["Run the watcher", `${SITE.repo_url}/actions/workflows/watch.yml`],
      ["Edit papers.yaml", `${SITE.repo_url}/edit/main/data/papers.yaml`],
      ["Tune the watcher", `${SITE.repo_url}/edit/main/config/watch.yaml`]
    ].map(([l, u]) => `<a class="btn btn-sm btn-ghost" href="${esc(u)}" target="_blank" rel="noopener noreferrer">${esc(l)}</a>`).join("");
    if (typeof d.showModal === "function") d.showModal(); else d.setAttribute("open", "");
    loadPending();
  }

  /* ================================================================ events */
  document.addEventListener("click", e => {
    const t = e.target.closest("button, a"); if (!t) return;
    if (t.dataset.cat !== undefined) { state.cat = t.dataset.cat || null; rerender(); }
    else if (t.dataset.type) { state.type = t.dataset.type; rerender(); }
    else if (t.dataset.tag) { state.q = t.dataset.tag; $("#q").value = t.dataset.tag; renderList(); }
    else if (t.dataset.theme) { state.cat = t.dataset.theme; state.sort = "section"; $("#sort").value = "section"; rerender(); $("#papers").scrollIntoView({ behavior: REDUCED ? "auto" : "smooth" }); }
    else if (t.dataset.bib) copy(bibtex(DATA.papers.find(x => x.id === t.dataset.bib)), "BibTeX copied");
    else if (t.dataset.cite) copy(citation(DATA.papers.find(x => x.id === t.dataset.cite)), "Citation copied");
  });
  document.addEventListener("keydown", e => {
    if (e.key === "/" && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) { e.preventDefault(); $("#q").focus(); }
  });

  function wire() {
    $("#q").addEventListener("input", e => { state.q = e.target.value.trim(); renderList(); });
    $("#sort").addEventListener("change", e => { state.sort = e.target.value; renderList(); });
    $("#sendMail").addEventListener("click", sendMail);
    $("#sendGh").addEventListener("click", sendGh);
    $("#suggestForm").addEventListener("submit", e => { e.preventDefault(); sendMail(); });
    $("#openDesk").addEventListener("click", openDesk);
    $("#closeDesk").addEventListener("click", () => $("#desk").close());
    $("#deskAdd").addEventListener("submit", e => {
      e.preventDefault(); const v = $("#dDoi").value.trim();
      if (!ID_RX.test(v)) { toast("Enter a DOI or arXiv id first."); $("#dDoi").focus(); return; }
      window.open(issueUrl(v, `Add: ${v}`), "_blank", "noopener");
    });
    if (location.hash === "#curator") openDesk();
    window.addEventListener("hashchange", () => { if (location.hash === "#curator") openDesk(); });
  }

  function fillLinks() {
    $("#ghLink").href = SITE.repo_url;
    $("#fBib").href = `${SITE.repo_url}/blob/main/bibliography/bioqubits.bib`;
    $("#fRes").href = `${SITE.repo_url}/blob/main/RESOURCES.md`;
    $("#fCite").href = `${SITE.repo_url}/blob/main/CITATION.cff`;
    $("#footCurator").innerHTML = `Curated by <a href="${esc(safeUrl(SITE.curator.website))}" target="_blank" rel="noopener noreferrer">${esc(SITE.curator.name)}</a>, ${esc(SITE.curator.affiliation)}.`;
    $("#gen").textContent = `Collection rebuilt ${DATA.generated}.`;
  }

  /* ================================================================ boot */
  initSim();
  const get = u => fetch(u, { cache: "no-cache" }).then(r => { if (!r.ok) throw new Error(u); return r.json(); });
  Promise.all([get("data/site.json"), get("data/papers.json"), get("data/resources.json").catch(() => null)])
    .then(([s, d, r]) => {
      SITE = s; DATA = d; RES = r;
      renderStats(); renderThemes(); rerender(); renderLibrary(); fillLinks(); wire();
    })
    .catch(() => { $("#list").innerHTML = '<p class="empty">The collection could not be loaded. Reload the page; if it persists, the site is being rebuilt.</p>'; });
})();
