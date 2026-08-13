// ── Sea Bound – Site Logic ────────────────────────────────────────────────────

// ── Navigation ────────────────────────────────────────────────────────────────
(function () {
  const navbar   = document.getElementById("navbar");
  const links    = document.querySelectorAll("[data-page]");
  const pages    = document.querySelectorAll(".page");
  const hamburger = document.getElementById("hamburger");
  const navLinks  = document.getElementById("navLinks");

  function showPage(id) {
    const leaving = document.querySelector(".page.active")?.id;

    // Stop the game when navigating away from the play page
    if (leaving === "play" && id !== "play" && window.SeaBoundGame) {
      window.SeaBoundGame.stop();
    }

    pages.forEach(p => p.classList.toggle("active", p.id === id));
    document.querySelectorAll(".nav-link").forEach(l =>
      l.classList.toggle("active", l.dataset.page === id)
    );
    window.scrollTo({ top: 0, behavior: "smooth" });

    // Start the game when navigating to the play page
    if (id === "play" && window.SeaBoundGame) {
      // Small delay so the canvas is visible before we touch its dimensions
      setTimeout(() => {
        const cvs = document.getElementById("gameCanvas");
        if (cvs) window.SeaBoundGame.start(cvs);
      }, 60);
    }

    // Close mobile menu
    hamburger.classList.remove("open");
    navLinks.classList.remove("open");
  }

  links.forEach(link => {
    link.addEventListener("click", e => {
      const page = link.dataset.page;
      if (page) { e.preventDefault(); showPage(page); }
    });
  });

  hamburger.addEventListener("click", () => {
    hamburger.classList.toggle("open");
    navLinks.classList.toggle("open");
  });

  window.addEventListener("scroll", () => {
    navbar.classList.toggle("scrolled", window.scrollY > 10);
  });

  // Handle hash on load
  const hash = location.hash.replace("#", "");
  if (hash && document.getElementById(hash)) showPage(hash);
})();

// ── Contact form ──────────────────────────────────────────────────────────────
function handleSubmit(e) {
  e.preventDefault();
  const form    = document.getElementById("contactForm");
  const success = document.getElementById("formSuccess");
  form.querySelectorAll("input, textarea").forEach(el => el.value = "");
  success.classList.add("show");
  setTimeout(() => success.classList.remove("show"), 4000);
}

// ── Levels data ───────────────────────────────────────────────────────────────
const LEVELS = [
  { num: 1, name: "The Shallows",   diff: 3, colA: "#0099cc", colB: "#004d66" },
  { num: 2, name: "Kraken Waters",  diff: 4, colA: "#4a148c", colB: "#1a0038" },
  { num: 3, name: "The Wreck",      diff: 5, colA: "#7f8c8d", colB: "#2c3e50" },
];

function buildLevels() {
  const grid = document.getElementById("levelsGrid");
  if (!grid) return;

  LEVELS.forEach(lv => {
    const card = document.createElement("div");
    card.className = "level-card";

    // Canvas thumbnail
    const cvs = document.createElement("canvas");
    cvs.className  = "level-thumb";
    cvs.width  = 200;
    cvs.height = 120;
    drawLevelThumb(cvs, lv);
    card.appendChild(cvs);

    // Info
    const info = document.createElement("div");
    info.className = "level-info";
    info.innerHTML = `
      <div class="level-num">LEVEL ${String(lv.num).padStart(2, "0")}</div>
      <div class="level-name">${lv.name}</div>
      <div class="level-diff">${Array.from({ length: 5 }, (_, i) =>
        `<div class="diff-pip ${i < lv.diff ? "on" : "off"}"></div>`
      ).join("")}</div>`;
    card.appendChild(info);
    grid.appendChild(card);
  });
}

function drawLevelThumb(cvs, lv) {
  const c   = cvs.getContext("2d");
  const w   = cvs.width, h = cvs.height;
  const sy  = Math.floor(h * 0.45);

  // Sky gradient
  const sg = c.createLinearGradient(0, 0, 0, sy);
  sg.addColorStop(0, "#0a1220");
  sg.addColorStop(1, lv.colB);
  c.fillStyle = sg;
  c.fillRect(0, 0, w, sy);

  // Water gradient
  const wg = c.createLinearGradient(0, sy, 0, h);
  wg.addColorStop(0, lv.colA);
  wg.addColorStop(1, lv.colB);
  c.fillStyle = wg;
  c.fillRect(0, sy, w, h - sy);

  // Horizon line
  c.fillStyle = "rgba(255,255,255,0.15)";
  c.fillRect(0, sy - 1, w, 2);

  // Simple pixel star dots in sky
  for (let s = 0; s < 12; s++) {
    const sx2 = (lv.num * 31 + s * 17) % w;
    const sy2 = (lv.num * 13 + s * 7)  % sy;
    c.fillStyle = "rgba(255,255,255,0.7)";
    c.fillRect(sx2, sy2, 1, 1);
  }

  // Level number watermark
  c.fillStyle = "rgba(255,255,255,0.07)";
  c.font = "bold 52px 'Press Start 2P', monospace";
  c.textAlign = "center";
  c.fillText(lv.num, w / 2, h * 0.75);

  // Lock icon for locked levels
  if (lv.num > 3) {
    c.fillStyle = "rgba(0,0,0,0.5)";
    c.fillRect(0, 0, w, h);
    c.fillStyle = "rgba(255,255,255,0.25)";
    c.font = "18px sans-serif";
    c.textAlign = "center";
    c.fillText("🔒", w / 2, h / 2 + 6);
  }
}

// ── Artwork data ──────────────────────────────────────────────────────────────
const ARTWORKS = [
  { label: "THE KRAKEN",  img: "Tentacle.png"},
  { label: "SHARK", img: "shark3.png"},
  { label: "JERRY", img: "jerryharpoon-r.png"},
  { label: "SEA FLOOR", img: "../../Images/sea_floor.png"},
  { label: "THE WRECK", img: "../../Images/shipwreck.png"},
];

function buildArtwork() {
  const grid = document.getElementById("artGrid");
  if (!grid) return;
  ARTWORKS.forEach(art => {
    const card = document.createElement("div");
    card.className = "art-card";

    if (art.img) {
      // Real image — use an <img> tag so the full image is shown
      const imgEl = document.createElement("img");
      imgEl.src = art.img;
      imgEl.alt = art.label;
      imgEl.className = "art-img";
      imgEl.loading = "lazy";
      card.appendChild(imgEl);
    } else {
      // Canvas-drawn artwork
      const cvs = document.createElement("canvas");
      cvs.width = 240; cvs.height = 200;
      art.draw(cvs);
      card.appendChild(cvs);
    }

    const label = document.createElement("div");
    label.className = "art-label";
    label.textContent = art.label;
    card.appendChild(label);
    grid.appendChild(card);
  });
}

function drawArtKraken(cvs) {
  const c = cvs.getContext("2d"), w = cvs.width, h = cvs.height;
  const g = c.createRadialGradient(w/2, h/2, 10, w/2, h/2, 130);
  g.addColorStop(0, "#2d0060"); g.addColorStop(1, "#030010");
  c.fillStyle = g; c.fillRect(0, 0, w, h);
  // Tentacles
  for (let t = 0; t < 8; t++) {
    const ang = (t / 8) * Math.PI * 2;
    c.strokeStyle = t % 2 === 0 ? "#4a1a7a" : "#6b2a9e";
    c.lineWidth = 6 - t % 3;
    c.beginPath(); c.moveTo(w/2, h*0.55);
    c.quadraticCurveTo(
      w/2 + Math.cos(ang) * 60, h/2 + Math.sin(ang) * 60,
      w/2 + Math.cos(ang) * 110, h/2 + Math.sin(ang) * 100
    );
    c.stroke();
  }
  // Body
  const bg = c.createRadialGradient(w/2, h*0.4, 5, w/2, h*0.4, 55);
  bg.addColorStop(0, "#7b2fff"); bg.addColorStop(1, "#1a0040");
  c.fillStyle = bg;
  c.beginPath(); c.ellipse(w/2, h*0.38, 50, 42, 0, 0, Math.PI*2); c.fill();
  // Eyes
  c.fillStyle = "#ff2222";
  c.beginPath(); c.arc(w/2 - 16, h*0.35, 7, 0, Math.PI*2); c.fill();
  c.beginPath(); c.arc(w/2 + 16, h*0.35, 7, 0, Math.PI*2); c.fill();
  c.fillStyle = "#000";
  c.beginPath(); c.arc(w/2 - 15, h*0.35, 3, 0, Math.PI*2); c.fill();
  c.beginPath(); c.arc(w/2 + 17, h*0.35, 3, 0, Math.PI*2); c.fill();
}

function drawArtShark(cvs) {
  const c = cvs.getContext("2d"), w = cvs.width, h = cvs.height;
  const g = c.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, "#0a2235"); g.addColorStop(1, "#061520");
  c.fillStyle = g; c.fillRect(0, 0, w, h);
  // Light rays
  for (let r = 0; r < 4; r++) {
    c.fillStyle = "rgba(100,200,255,0.04)";
    c.beginPath(); c.moveTo(w*0.4 + r*20, 0);
    c.lineTo(w*0.1 + r*30, h); c.lineTo(w*0.25 + r*30, h);
    c.lineTo(w*0.55 + r*20, 0); c.fill();
  }
  // Body
  c.fillStyle = "#4a6070";
  c.beginPath(); c.ellipse(w/2, h/2, 95, 26, 0, 0, Math.PI*2); c.fill();
  c.fillStyle = "#c0cfd8";
  c.beginPath(); c.ellipse(w/2+10, h/2+8, 60, 14, 0, 0, Math.PI*2); c.fill();
  // Dorsal fin
  c.fillStyle = "#3a5060";
  c.beginPath(); c.moveTo(w/2-10, h/2-26); c.lineTo(w/2+5, h/2-52);
  c.lineTo(w/2+22, h/2-26); c.closePath(); c.fill();
  // Tail
  c.beginPath(); c.moveTo(w/2-90, h/2);
  c.lineTo(w/2-110, h/2-20); c.lineTo(w/2-85, h/2);
  c.lineTo(w/2-110, h/2+20); c.closePath();
  c.fillStyle = "#3a5060"; c.fill();
  // Eye
  c.fillStyle = "#ff2020";
  c.beginPath(); c.arc(w/2+55, h/2-6, 5, 0, Math.PI*2); c.fill();
  c.fillStyle="#000"; c.beginPath(); c.arc(w/2+56, h/2-6, 2, 0, Math.PI*2); c.fill();
}

function drawArtDiver(cvs) {
  const c = cvs.getContext("2d"), w = cvs.width, h = cvs.height;
  const g = c.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, "#00334e"); g.addColorStop(1, "#001020");
  c.fillStyle = g; c.fillRect(0, 0, w, h);
  // Bubbles
  for (let b = 0; b < 12; b++) {
    c.strokeStyle = "rgba(160,220,255,0.4)"; c.lineWidth = 1;
    c.beginPath(); c.arc(w/2 - 20 + b*5, h*0.2 + b*8, 3+b%4, 0, Math.PI*2); c.stroke();
  }
  // Tank
  c.fillStyle = "#aaa";
  c.beginPath(); c.roundRect(w/2+18, h*0.3, 14, 60, 4); c.fill();
  // Body
  c.fillStyle = "#1a6fa8";
  c.beginPath(); c.roundRect(w/2-22, h*0.32, 44, 62, 10); c.fill();
  c.fillStyle = "#0d4f7a";
  c.fillRect(w/2-2, h*0.35, 4, 56);
  // Head
  c.fillStyle = "#1a6fa8";
  c.beginPath(); c.arc(w/2, h*0.26, 22, 0, Math.PI*2); c.fill();
  // Mask
  c.fillStyle = "#88ddff";
  c.beginPath(); c.ellipse(w/2-2, h*0.25, 16, 12, 0, 0, Math.PI*2); c.fill();
  c.strokeStyle = "#0055aa"; c.lineWidth = 2;
  c.beginPath(); c.ellipse(w/2-2, h*0.25, 16, 12, 0, 0, Math.PI*2); c.stroke();
  // Eye reflection
  c.fillStyle = "#fff";
  c.beginPath(); c.arc(w/2-4, h*0.24, 4, 0, Math.PI*2); c.fill();
  c.fillStyle = "#222"; c.beginPath(); c.arc(w/2-3, h*0.24, 2, 0, Math.PI*2); c.fill();
  // Fins
  c.fillStyle = "#e8a020";
  c.beginPath(); c.ellipse(w/2-16, h*0.78, 20, 8, 0.4, 0, Math.PI*2); c.fill();
  c.beginPath(); c.ellipse(w/2+14, h*0.78, 20, 8, -0.4, 0, Math.PI*2); c.fill();
  // Harpoon gun
  c.fillStyle = "#334"; c.beginPath(); c.roundRect(w/2+22, h*0.44, 34, 8, 3); c.fill();
  c.fillStyle = "#ff6600";
  c.beginPath(); c.moveTo(w/2+56, h*0.48); c.lineTo(w/2+50, h*0.44);
  c.lineTo(w/2+50, h*0.52); c.closePath(); c.fill();
}

function drawArtCoral(cvs) {
  const c = cvs.getContext("2d"), w = cvs.width, h = cvs.height;
  c.fillStyle = "#061828"; c.fillRect(0, 0, w, h);
  // Sand
  c.fillStyle = "#8a6a3a"; c.fillRect(0, h-22, w, 22);
  c.fillStyle = "#a07a48"; c.fillRect(0, h-24, w, 4);
  // Corals
  const corals = [
    {x:30, col:"#e74c3c"},{x:75,col:"#ff7043"},{x:130,col:"#9b59b6"},
    {x:175,col:"#e74c3c"},{x:210,col:"#ff9800"},{x:w-40,col:"#e91e63"},
  ];
  corals.forEach(cr => {
    c.strokeStyle = cr.col; c.lineWidth = 5; c.lineCap = "round";
    c.beginPath(); c.moveTo(cr.x, h-22); c.lineTo(cr.x, h-80); c.stroke();
    c.lineWidth = 3;
    for (let b = 0; b < 4; b++) {
      const bDir = b%2===0?1:-1, by = h-40-b*12;
      c.beginPath(); c.moveTo(cr.x, by); c.lineTo(cr.x+bDir*22, by-14); c.stroke();
    }
  });
  // Fish silhouettes
  for (let f = 0; f < 5; f++) {
    c.fillStyle = `rgba(${100+f*20},${180+f*10},${220},0.6)`;
    const fx = 20+f*42, fy = h*0.3+f*15;
    c.beginPath(); c.ellipse(fx,fy,10,5,0,0,Math.PI*2); c.fill();
    c.beginPath(); c.moveTo(fx-10,fy); c.lineTo(fx-17,fy-5); c.lineTo(fx-17,fy+5); c.fill();
  }
}

function drawArtWreck(cvs) {
  const c = cvs.getContext("2d"), w = cvs.width, h = cvs.height;
  const g = c.createLinearGradient(0,0,0,h);
  g.addColorStop(0,"#0a1828"); g.addColorStop(1,"#050c14");
  c.fillStyle=g; c.fillRect(0,0,w,h);
  // Hull of wreck
  c.fillStyle = "#3a3a3a";
  c.beginPath(); c.moveTo(20,h*0.75); c.lineTo(w-20,h*0.75);
  c.lineTo(w-40,h*0.95); c.lineTo(40,h*0.95); c.closePath(); c.fill();
  c.fillStyle="#2a2a2a"; c.fillRect(20,h*0.75,w-40,4);
  // Porthole windows
  for (let pw=0;pw<4;pw++) {
    c.strokeStyle="#555"; c.lineWidth=3;
    c.beginPath(); c.arc(55+pw*50, h*0.83, 9, 0, Math.PI*2); c.stroke();
    c.fillStyle="rgba(0,150,200,0.15)";
    c.beginPath(); c.arc(55+pw*50, h*0.83, 7, 0, Math.PI*2); c.fill();
  }
  // Mast
  c.fillStyle="#2a2a2a"; c.fillRect(w*0.6-2,h*0.3,4,h*0.45);
  c.fillRect(w*0.6-28,h*0.45,56,3);
  // Kelp growing on wreck
  for (let k=0;k<5;k++) {
    c.strokeStyle=k%2===0?"#1a5c2a":"#2e7d45"; c.lineWidth=3;
    c.beginPath(); c.moveTo(30+k*40,h*0.75);
    c.quadraticCurveTo(25+k*40,h*0.55,35+k*38,h*0.4); c.stroke();
  }
  // Particles / particles
  for (let p=0;p<20;p++) {
    c.fillStyle=`rgba(150,210,255,${0.1+Math.random()*0.2})`;
    c.fillRect(Math.random()*w, Math.random()*h, 1, 1);
  }
}

function drawArtJelly(cvs) {
  const c = cvs.getContext("2d"), w = cvs.width, h = cvs.height;
  const g = c.createRadialGradient(w/2,h/2,20,w/2,h/2,130);
  g.addColorStop(0,"#1a0040"); g.addColorStop(1,"#000818");
  c.fillStyle=g; c.fillRect(0,0,w,h);
  // Glow
  const glow = c.createRadialGradient(w/2,h*0.38,5,w/2,h*0.38,70);
  glow.addColorStop(0,"rgba(180,0,255,0.3)"); glow.addColorStop(1,"rgba(0,0,0,0)");
  c.fillStyle=glow; c.fillRect(0,0,w,h);
  // Bell
  const jg = c.createRadialGradient(w/2,h*0.3,5,w/2,h*0.38,55);
  jg.addColorStop(0,"rgba(220,100,255,0.9)"); jg.addColorStop(1,"rgba(100,0,180,0.6)");
  c.fillStyle=jg;
  c.beginPath(); c.ellipse(w/2,h*0.38,48,38,0,Math.PI,Math.PI*2); c.fill();
  // Inner pattern
  c.strokeStyle="rgba(255,150,255,0.3)"; c.lineWidth=1;
  for(let r=10;r<45;r+=10){
    c.beginPath(); c.arc(w/2,h*0.38,r,Math.PI,Math.PI*2); c.stroke();
  }
  // Tentacles
  for(let t=0;t<10;t++){
    const tx = w/2 - 36 + t*8;
    c.strokeStyle = t%2===0 ? "rgba(200,80,255,0.7)" : "rgba(255,150,255,0.5)";
    c.lineWidth = 1.5;
    c.beginPath(); c.moveTo(tx, h*0.56);
    c.bezierCurveTo(tx-10+t*2, h*0.65, tx+5, h*0.78, tx-8+t*3, h*0.95);
    c.stroke();
  }
}

// ── About diver image ─────────────────────────────────────────────────────────
function drawAboutCanvas() {
  const cvs = document.getElementById("aboutCanvas");
  if (!cvs) return;
  // Replace the canvas with an img tag showing jerryharpoon-r.png
  const img = document.createElement("img");
  img.src = "jerryharpoon-r.png";
  img.alt = "Diver with harpoon";
  img.style.cssText = "width:100%;height:100%;object-fit:contain;image-rendering:pixelated;";
  cvs.replaceWith(img);
}

// ── Init ──────────────────────────────────────────────────────────────────────
buildLevels();
buildArtwork();
drawAboutCanvas();

// ── Hero hotspot tooltips ─────────────────────────────────────────────────────
(function () {
  const tooltip   = document.getElementById("heroTooltip");
  const tipTitle  = document.getElementById("heroTooltipTitle");
  const tipText   = document.getElementById("heroTooltipText");
  const heroWrap  = document.querySelector(".hero-wrap");
  const hotspots  = document.querySelectorAll(".hotspot");

  if (!tooltip || !heroWrap) return;

  hotspots.forEach(hs => {
    hs.addEventListener("mouseenter", () => {
      tipTitle.textContent = hs.dataset.title;
      tipText.textContent  = hs.dataset.tip;
      tooltip.classList.add("visible");
    });
    hs.addEventListener("mouseleave", () => {
      tooltip.classList.remove("visible");
    });
  });

  heroWrap.addEventListener("mousemove", e => {
    if (!tooltip.classList.contains("visible")) return;
    const rect   = heroWrap.getBoundingClientRect();
    const margin = 12;
    const tw     = tooltip.offsetWidth  || 220;
    const th     = tooltip.offsetHeight || 80;

    let x = e.clientX - rect.left + margin;
    let y = e.clientY - rect.top  + margin;

    // Flip left if too close to right edge
    if (x + tw > rect.width  - margin) x = e.clientX - rect.left - tw - margin;
    // Flip up if too close to bottom edge
    if (y + th > rect.height - margin) y = e.clientY - rect.top  - th - margin;

    tooltip.style.left = x + "px";
    tooltip.style.top  = y + "px";
  });
})();
