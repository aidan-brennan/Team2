// ── Hero Canvas – Sea Bound ───────────────────────────────────────────────────
// Draws a split scene: sunset ocean above, underwater below.
// Top half: sky gradient, sun, clouds, wooden boat with diving cage.
// Bottom half: deep ocean, coral, kelp, pixel kraken, circling sharks.
// Everything is drawn with ctx pixel rectangles for a chunky pixel-art look.

(function () {
  const canvas = document.getElementById("heroCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  // Internal resolution (low-res for pixel art effect, CSS scales it up)
  const W = 480, H = 320;
  canvas.width  = W;
  canvas.height = H;

  const SEA_Y = Math.floor(H * 0.46); // horizon line

  // ── Palette ────────────────────────────────────────────────────────────────
  const P = {
    // Sky / sunset
    sky0:   "#1a0a2e", sky1: "#3d1c5a", sky2: "#7b2d6b",
    sky3:   "#c0514a", sky4: "#e8834e", sky5: "#f7b267",
    sun:    "#ffe566", sunGlow: "#ffaa00",
    cloud:  "#f7d9b0", cloudDark: "#d4a97a",
    // Sea surface
    surf0:  "#1a4a6e", surf1:  "#1e5a82", surf2: "#236b99",
    foam:   "#a0d4e8",
    // Deep water
    deep0:  "#0a1e2e", deep1: "#0d2a40", deep2: "#102f48",
    deep3:  "#0e2638",
    // Boat
    hull:   "#5c3a1e", hullDk: "#3b2510", hullLt: "#7a4e28",
    deck:   "#8b6040", plank:  "#6b4a2e", cabin:  "#4a2e14",
    mast:   "#3b2510", rope:   "#c8a060",
    // Cage
    cageBar:"#8a8a8a", cageDk: "#555", cageLt: "#bbb",
    // Underwater
    uw0:    "#061520", uw1: "#081c2a", uw2: "#0a2235",
    coral0: "#c0392b", coral1: "#e74c3c", coral2: "#ff7043",
    kelp:   "#1a5c2a", kelp2:  "#2e7d45",
    sand:   "#8a6a3a", sandLt: "#a07a48",
    // Creatures
    sharkB: "#4a6070", sharkBl:"#c0cfd8", sharkF: "#3a5060",
    krk0:   "#1a0a3e", krk1:   "#2d1460", krk2:   "#4a1a7a",
    krkEye: "#ff2222", krkPup: "#220000",
    krkTen: "#3d1470", krkSck: "#6b2a9e",
    // Bubbles / light
    bub:    "rgba(160,212,232,0.5)",
    ray:    "rgba(255,200,80,0.06)",
    rayW:   "rgba(120,200,255,0.05)",
  };

  // ── Pixel helper ───────────────────────────────────────────────────────────
  // Draw a single "pixel" (scaled 1×1 block at our internal res)
  function px(x, y, col) {
    ctx.fillStyle = col;
    ctx.fillRect(Math.floor(x), Math.floor(y), 1, 1);
  }
  // Draw a filled rectangle in pixel coords
  function rect(x, y, w, h, col) {
    ctx.fillStyle = col;
    ctx.fillRect(Math.floor(x), Math.floor(y), Math.floor(w), Math.floor(h));
  }

  // ── Animation state ────────────────────────────────────────────────────────
  let frame = 0;

  // Sharks  [x, y, dir, speed, phase]
  const sharks = [
    { x: 60,  y: SEA_Y + 80, dir: 1, spd: 0.35, phase: 0.0 },
    { x: 360, y: SEA_Y + 55, dir:-1, spd: 0.28, phase: 1.2 },
    { x: 200, y: SEA_Y + 110,dir: 1, spd: 0.22, phase: 2.5 },
  ];

  // Bubbles
  const bubbles = Array.from({ length: 22 }, () => ({
    x: Math.random() * W,
    y: SEA_Y + 20 + Math.random() * (H - SEA_Y - 20),
    vy: 0.25 + Math.random() * 0.45,
    r:  1 + Math.floor(Math.random() * 2),
    phase: Math.random() * Math.PI * 2,
  }));

  // Kelp sway phases
  const kelpData = [
    { x: 28,  h: 38, phase: 0.0, col: P.kelp  },
    { x: 55,  h: 28, phase: 1.1, col: P.kelp2 },
    { x: 390, h: 42, phase: 0.7, col: P.kelp  },
    { x: 418, h: 30, phase: 1.9, col: P.kelp2 },
    { x: 450, h: 36, phase: 0.3, col: P.kelp  },
    { x: 140, h: 22, phase: 2.1, col: P.kelp2 },
    { x: 320, h: 32, phase: 1.5, col: P.kelp  },
  ];

  // ── Draw: Sky ──────────────────────────────────────────────────────────────
  function drawSky() {
    // Gradient bands (chunky pixel rows)
    const bands = [
      [0,    12, P.sky0], [12,  24, P.sky1], [24,  38, P.sky2],
      [38,   54, P.sky3], [54,  70, P.sky4], [70,  SEA_Y, P.sky5],
    ];
    bands.forEach(([y1, y2, col]) => rect(0, y1, W, y2 - y1, col));

    // Sun glow halo (concentric rects)
    const sx = 340, sy = 62;
    [[30, P.ray],["rgba(255,180,60,0.09)",28],].forEach(() => {});
    for (let r = 28; r >= 0; r -= 4) {
      const alpha = 0.04 + (28 - r) * 0.012;
      ctx.fillStyle = `rgba(255,200,60,${alpha})`;
      ctx.fillRect(sx - r * 2, sy - r, r * 4, r * 2);
    }

    // Sun body (pixel circle approx)
    const sunR = 14;
    for (let dy = -sunR; dy <= sunR; dy++) {
      for (let dx = -sunR * 2; dx <= sunR * 2; dx++) {
        if ((dx / 2) * (dx / 2) + dy * dy <= sunR * sunR) {
          const bright = 1 - Math.sqrt((dx/2)**2 + dy**2) / sunR * 0.25;
          ctx.fillStyle = dy < -sunR * 0.5 ? P.sun : P.sunGlow;
          ctx.fillRect(sx + dx, sy + dy, 1, 1);
        }
      }
    }

    // Sun reflection on sea surface
    for (let rx = -40; rx <= 40; rx += 3) {
      const len = Math.max(1, 6 - Math.abs(rx) * 0.1);
      const alpha = 0.5 - Math.abs(rx) * 0.01;
      ctx.fillStyle = `rgba(255,220,80,${alpha})`;
      ctx.fillRect(sx + rx, SEA_Y - 4 + (frame + rx) % 3, Math.max(1, 3 - Math.abs(rx/20)), len);
    }

    // Pixel clouds
    drawCloud(60,  22, 55, 12, P.cloud, P.cloudDark);
    drawCloud(200, 16, 40,  9, P.cloudDark, P.cloud);
    drawCloud(130, 32, 30,  7, P.cloud, P.cloudDark);
  }

  function drawCloud(cx, cy, cw, ch, col, shadow) {
    // Chunky blocky pixel cloud
    const blocks = [
      [0, ch * 0.4, cw, ch * 0.6],
      [cw * 0.1, 0, cw * 0.5, ch],
      [cw * 0.45, ch * 0.2, cw * 0.4, ch * 0.7],
    ];
    blocks.forEach(([bx, by, bw, bh]) => {
      rect(cx + bx, cy + by, bw, bh, col);
    });
    // Shadow underside
    rect(cx, cy + ch * 0.65, cw, ch * 0.2, shadow);
  }

  // ── Draw: Sea surface ──────────────────────────────────────────────────────
  function drawSeaSurface() {
    // Horizon band
    rect(0, SEA_Y - 2, W, 6, P.surf2);
    rect(0, SEA_Y + 4, W, 4, P.surf1);
    rect(0, SEA_Y + 8, W, 3, P.surf0);

    // Animated wave pixels
    for (let x = 0; x < W; x += 4) {
      const waveOff = Math.sin((x * 0.08) + frame * 0.04) * 2;
      rect(x, SEA_Y - 2 + waveOff, 3, 1, P.foam);
    }
    for (let x = 8; x < W; x += 10) {
      const waveOff = Math.sin((x * 0.1) + frame * 0.03 + 1) * 1.5;
      rect(x, SEA_Y + 2 + waveOff, 2, 1, P.foam);
    }
  }

  // ── Draw: Underwater background ────────────────────────────────────────────
  function drawUnderwater() {
    // Gradient bands
    const bands = [
      [SEA_Y + 12, SEA_Y + 40,  P.uw0],
      [SEA_Y + 40, SEA_Y + 90,  P.uw1],
      [SEA_Y + 90, SEA_Y + 150, P.uw2],
      [SEA_Y + 150, H,          P.uw0],
    ];
    bands.forEach(([y1, y2, col]) => rect(0, y1, W, y2 - y1, col));

    // Animated light rays from surface
    for (let r = 0; r < 5; r++) {
      const rx = 80 + r * 80 + Math.sin(frame * 0.012 + r * 1.2) * 18;
      const spread = 20 + r * 5;
      ctx.save();
      ctx.globalAlpha = 0.07 + Math.sin(frame * 0.02 + r) * 0.02;
      ctx.fillStyle = P.rayW;
      ctx.beginPath();
      ctx.moveTo(rx - 4, SEA_Y + 12);
      ctx.lineTo(rx - spread, H);
      ctx.lineTo(rx + spread, H);
      ctx.lineTo(rx + 4, SEA_Y + 12);
      ctx.fill();
      ctx.restore();
    }

    // Sandy floor
    rect(0, H - 18, W, 4, P.sandLt);
    rect(0, H - 14, W, 14, P.sand);
    // Sand ripple pixels
    for (let x = 0; x < W; x += 8) {
      rect(x, H - 16, 5, 1, P.sandLt);
    }
  }

  // ── Draw: Coral & Kelp ─────────────────────────────────────────────────────
  function drawFlora() {
    // Coral clusters (left)
    drawCoral(18,  H - 18, 14, P.coral0);
    drawCoral(34,  H - 18, 10, P.coral1);
    drawCoral(380, H - 18, 12, P.coral2);
    drawCoral(400, H - 18, 16, P.coral0);
    drawCoral(230, H - 18,  8, P.coral1);

    // Kelp with sway
    kelpData.forEach(k => {
      const sway = Math.sin(frame * 0.04 + k.phase) * 3;
      for (let seg = 0; seg < k.h; seg += 2) {
        const sx = k.x + Math.sin(frame * 0.04 + k.phase + seg * 0.15) * (seg / k.h) * 5;
        rect(sx, H - 18 - seg - 2, 2, 2, seg % 6 < 3 ? k.col : P.kelp2);
        // Leaf nubs
        if (seg % 8 === 0) {
          rect(sx - 3, H - 18 - seg - 1, 3, 1, P.kelp2);
          rect(sx + 2,  H - 18 - seg - 3, 3, 1, P.kelp);
        }
      }
    });
  }

  function drawCoral(x, floorY, size, col) {
    // Simple branching coral in pixel blocks
    const branches = [
      [0, 0, size, size * 2.5],
      [-size, -size * 1.2, size * 0.7, size * 1.5],
      [size * 0.5, -size * 1.5, size * 0.6, size * 1.2],
      [-size * 0.3, -size * 2.2, size * 0.5, size * 0.8],
    ];
    branches.forEach(([bx, by, bw, bh]) => {
      rect(x + bx, floorY + by, bw, bh, col);
    });
    // Tips (lighter)
    rect(x - size, floorY - size * 2.5, size * 0.6, size * 0.5, "#ff9999");
    rect(x + size * 0.5, floorY - size * 2.8, size * 0.5, size * 0.5, "#ffaaaa");
  }

  // ── Draw: Boat ─────────────────────────────────────────────────────────────
  function drawBoat() {
    const bx = 170, by = SEA_Y - 32;
    const bw = 130, bh = 30;

    // Hull shadow
    rect(bx + 3, by + bh - 2, bw - 6, 4, "rgba(0,0,0,0.35)");

    // Hull body
    rect(bx, by + 6, bw, bh - 6, P.hull);

    // Hull planks (horizontal lines)
    for (let py = by + 9; py < by + bh - 2; py += 5) {
      rect(bx + 2, py, bw - 4, 1, P.hullDk);
    }

    // Hull highlight top edge
    rect(bx, by + 6, bw, 2, P.hullLt);

    // Hull bow taper (right side)
    rect(bx + bw - 14, by + 8, 14, bh - 12, P.hull);
    rect(bx + bw - 8,  by + 12, 8,  bh - 16, P.hull);
    rect(bx + bw - 4,  by + 16, 4,  bh - 20, P.hull);

    // Hull stern taper (left)
    rect(bx, by + 10, 10, bh - 14, P.hull);

    // Deck
    rect(bx + 4, by,      bw - 18, 8, P.deck);
    rect(bx + 4, by,      bw - 18, 2, P.hullLt);

    // Deck planks
    for (let px2 = bx + 10; px2 < bx + bw - 20; px2 += 8) {
      rect(px2, by + 2, 1, 6, P.plank);
    }

    // Cabin / wheelhouse
    const cx2 = bx + 38, cy2 = by - 20;
    rect(cx2, cy2, 36, 20, P.cabin);
    rect(cx2, cy2, 36, 3, P.hullLt);
    // Cabin window
    rect(cx2 + 8,  cy2 + 6, 8, 6, "#4fc3f7");
    rect(cx2 + 20, cy2 + 6, 8, 6, "#4fc3f7");
    rect(cx2 + 8,  cy2 + 6, 8, 1, "#2980b9");
    rect(cx2 + 20, cy2 + 6, 8, 1, "#2980b9");

    // Mast
    rect(bx + 60, by - 50, 3, 52, P.mast);
    // Boom
    rect(bx + 40, by - 38, 40, 2, P.mast);
    // Sail (furled)
    rect(bx + 44, by - 36, 32, 8, "#e8d8b0");
    rect(bx + 44, by - 36, 32, 2, "#d4c09a");

    // Rope from mast to bow
    for (let ri = 0; ri < 16; ri++) {
      const rx = bx + 62 + ri * 3;
      const ry = by - 48 + ri * 3;
      rect(rx, ry, 1, 1, P.rope);
    }

    // Railing posts
    for (let post = bx + 10; post < bx + bw - 20; post += 12) {
      rect(post, by - 6, 2, 8, P.mast);
    }
    rect(bx + 10, by - 6, bw - 32, 1, P.rope);
  }

  // ── Draw: Diving cage ──────────────────────────────────────────────────────
  function drawDiveCage() {
    const cgx = 90;  // cage center x
    const cgy = SEA_Y - 10; // top of cage rope (at water level)
    const cw = 22, ch = 36;
    const cx = cgx - cw / 2;

    // Rope from boat to cage
    for (let ry = cgy - 28; ry < cgy; ry += 2) {
      rect(cgx - 1, ry, 2, 1, P.rope);
    }
    // Second rope
    for (let ry = cgy - 28; ry < cgy; ry += 2) {
      rect(cgx + 8, ry, 2, 1, P.rope);
    }

    // Cage frame – outer bars
    rect(cx,          cgy, 2, ch, P.cageBar);           // left
    rect(cx + cw - 2, cgy, 2, ch, P.cageBar);           // right
    rect(cx,          cgy, cw, 2, P.cageLt);            // top
    rect(cx,          cgy + ch - 2, cw, 2, P.cageDk);  // bottom

    // Horizontal cross bars
    for (let bar = cgy + 8; bar < cgy + ch - 2; bar += 8) {
      rect(cx, bar, cw, 1, P.cageDk);
    }
    // Vertical bars
    for (let vb = cx + 6; vb < cx + cw - 2; vb += 6) {
      rect(vb, cgy, 1, ch, P.cageDk);
    }
    // Highlight edge
    rect(cx + 1, cgy + 1, 1, ch - 2, P.cageLt);

    // Diver silhouette inside cage
    const dvx = cgx - 4, dvy = cgy + 8;
    rect(dvx,     dvy,      8, 5, "#1a6fa8");   // body
    rect(dvx + 1, dvy - 5,  6, 5, "#1a6fa8");   // head/helmet
    rect(dvx + 2, dvy - 4,  4, 3, "#88ddff");   // mask
    rect(dvx - 2, dvy + 4,  4, 2, "#e8a020");   // left fin
    rect(dvx + 6, dvy + 4,  4, 2, "#e8a020");   // right fin
  }

  // ── Draw: Sharks ───────────────────────────────────────────────────────────
  function drawShark(s) {
    const { x, y, dir } = s;
    const w = 28, h = 10;
    const wiggle = Math.sin(frame * 0.18 + s.phase) * 1.5;

    ctx.save();
    ctx.translate(Math.floor(x), Math.floor(y + wiggle));
    if (dir < 0) ctx.scale(-1, 1);

    // Tail
    rect(-w * 0.5 - 6, -h * 0.5, 6, h * 0.45, P.sharkF);
    rect(-w * 0.5 - 4, h * 0.1,  4, h * 0.45, P.sharkF);

    // Body
    rect(-w * 0.5, -h * 0.45, w, h, P.sharkB);

    // Belly
    rect(-w * 0.3, h * 0.15, w * 0.55, h * 0.3, P.sharkBl);

    // Dorsal fin
    rect(0, -h * 0.45 - 5, 5, 5, P.sharkF);
    rect(2, -h * 0.45 - 7, 3, 2, P.sharkF);

    // Pectoral fin
    rect(2, h * 0.2, 7, 4, P.sharkF);

    // Snout
    rect(w * 0.5 - 4, -h * 0.3, 6, h * 0.6, P.sharkB);

    // Eye
    rect(w * 0.25, -h * 0.25, 2, 2, "#cc2222");

    // Mouth slit
    rect(w * 0.35, h * 0.1, 5, 1, "#1a2a30");

    ctx.restore();
  }

  // ── Draw: Kraken ───────────────────────────────────────────────────────────
  function drawKraken() {
    const kx = 260, ky = H - 80;
    const pulse = Math.sin(frame * 0.03) * 3;

    // ── Tentacles (drawn behind body) ────────────────────────────────────────
    const tentacles = [
      { ox: -30, oy: 10, curve: -1.0 },
      { ox: -18, oy: 14, curve: -0.5 },
      { ox:  -5, oy: 16, curve:  0.2 },
      { ox:  10, oy: 16, curve:  0.6 },
      { ox:  24, oy: 14, curve:  1.0 },
      { ox:  36, oy: 10, curve:  1.4 },
    ];

    tentacles.forEach((t, i) => {
      const sway = Math.sin(frame * 0.05 + i * 0.8) * 6;
      const tx = kx + t.ox;
      const ty = ky + t.oy;
      const length = 45 + i % 3 * 8;
      for (let seg = 0; seg < length; seg += 3) {
        const progress = seg / length;
        const sx = tx + Math.sin(frame * 0.05 + i * 0.9 + progress * 2) * (sway * progress);
        const sy = ty + seg * 0.85;
        const sw = Math.max(1, 4 - progress * 3);
        rect(sx, sy, sw, 3, seg % 9 < 6 ? P.krkTen : P.krkSck);
      }
    });

    // ── Mantle (head/body) ───────────────────────────────────────────────────
    const mw = 52, mh = 38;
    const mx = kx - mw / 2, my = ky - mh + pulse;

    // Mantle glow
    ctx.save();
    ctx.globalAlpha = 0.18;
    ctx.fillStyle = "#7b2fff";
    ctx.beginPath();
    ctx.ellipse(kx, ky - mh / 2 + pulse, mw * 0.8, mh * 0.7, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Main body blocks
    for (let row = 0; row < mh; row++) {
      const rowW = Math.floor(mw * Math.sin((row / mh) * Math.PI));
      const rowX = kx - rowW / 2;
      const col = row < mh * 0.3 ? P.krk2 : row < mh * 0.7 ? P.krk1 : P.krk0;
      rect(rowX, my + row, rowW, 1, col);
    }

    // Skin texture spots
    for (let sp = 0; sp < 8; sp++) {
      const sx = kx - 16 + sp * 5;
      const sy = my + 8 + (sp % 3) * 6;
      rect(sx, sy, 2, 2, P.krkSck);
    }

    // Eyes (pair)
    const eyeY = my + mh * 0.35 + pulse;
    // Left eye
    rect(kx - 16, eyeY, 8, 6, P.krkEye);
    rect(kx - 15, eyeY + 1, 6, 4, "#ff4444");
    rect(kx - 14, eyeY + 2, 4, 2, P.krkPup);
    rect(kx - 13, eyeY + 2, 2, 2, "#110000");
    // Right eye
    rect(kx + 8,  eyeY, 8, 6, P.krkEye);
    rect(kx + 9,  eyeY + 1, 6, 4, "#ff4444");
    rect(kx + 10, eyeY + 2, 4, 2, P.krkPup);
    rect(kx + 11, eyeY + 2, 2, 2, "#110000");

    // Beak
    rect(kx - 4, my + mh * 0.6 + pulse, 8, 4, "#1a0030");
    rect(kx - 3, my + mh * 0.6 + 2 + pulse, 6, 2, "#000");

    // Two long grabbing tentacles reaching upward
    for (let arm = 0; arm < 2; arm++) {
      const armDir = arm === 0 ? -1 : 1;
      const armSway = Math.sin(frame * 0.04 + arm * 1.5) * 10;
      for (let seg = 0; seg < 60; seg += 3) {
        const progress = seg / 60;
        const ax = kx + armDir * (12 + seg * 0.5 + armSway * progress);
        const ay = ky - seg * 0.9;
        const aw = Math.max(1, 5 - progress * 4);
        rect(ax, ay, aw, 3, progress < 0.5 ? P.krkTen : P.krkSck);
        // Sucker marks
        if (seg % 9 === 0) rect(ax + 1, ay + 1, 2, 1, P.krkSck);
      }
    }
  }

  // ── Draw: Bubbles ──────────────────────────────────────────────────────────
  function drawBubbles() {
    bubbles.forEach(b => {
      b.y -= b.vy;
      b.x += Math.sin(frame * 0.04 + b.phase) * 0.3;
      if (b.y < SEA_Y + 4) {
        b.y = H - 20 + Math.random() * 10;
        b.x = Math.random() * W;
      }
      ctx.fillStyle = P.bub;
      ctx.fillRect(Math.floor(b.x), Math.floor(b.y), b.r, b.r);
    });
  }

  // ── Main render loop ───────────────────────────────────────────────────────
  function render() {
    ctx.clearRect(0, 0, W, H);

    // ── Above water ──────────────────────────────────────────────────────────
    drawSky();
    drawBoat();
    drawSeaSurface();

    // ── Below water ──────────────────────────────────────────────────────────
    drawUnderwater();
    drawFlora();
    drawKraken();

    // Update & draw sharks
    sharks.forEach(s => {
      s.x += s.dir * s.spd;
      if (s.x > W + 40)  s.x = -40;
      if (s.x < -40)     s.x = W + 40;
      drawShark(s);
    });

    drawBubbles();

    // Draw cage last so it sits on top of water
    drawDiveCage();

    // Waterline overlay to blend above/below
    const waterGrad = ctx.createLinearGradient(0, SEA_Y - 4, 0, SEA_Y + 16);
    waterGrad.addColorStop(0, "rgba(10,22,40,0)");
    waterGrad.addColorStop(1, "rgba(10,30,48,0.5)");
    ctx.fillStyle = waterGrad;
    ctx.fillRect(0, SEA_Y - 4, W, 20);

    frame++;
    requestAnimationFrame(render);
  }

  render();
})();
