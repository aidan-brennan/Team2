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

  const name    = document.getElementById("fname").value.trim();
  const email   = document.getElementById("femail").value.trim();
  const subject = document.getElementById("fsubject").value.trim();
  const message = document.getElementById("fmessage").value.trim();

  const mailtoLink = "mailto:maxnolan187@gmail.com"
    + "?subject=" + encodeURIComponent(subject + " (from " + name + ")")
    + "&body="    + encodeURIComponent("Name: " + name + "\nEmail: " + email + "\n\n" + message);

  window.location.href = mailtoLink;

  const form    = document.getElementById("contactForm");
  const success = document.getElementById("formSuccess");
  form.querySelectorAll("input, textarea").forEach(el => el.value = "");
  success.classList.add("show");
  setTimeout(() => success.classList.remove("show"), 4000);
}

// ── Levels data ───────────────────────────────────────────────────────────────
const LEVELS = [
  { num: 1, name: "The Shallows",  diff: 3, thumb: "sea_floor.png"  },
  { num: 2, name: "Kraken Waters", diff: 4, thumb: "cave.png"       },
  { num: 3, name: "The Wreck",     diff: 5, thumb: "shipwreck.png"  },
];

function buildLevels() {
  const grid = document.getElementById("levelsGrid");
  if (!grid) return;

  LEVELS.forEach(lv => {
    const card = document.createElement("div");
    card.className = "level-card";

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

// ── Artwork data ──────────────────────────────────────────────────────────────
const ARTWORKS = [
  { label: "THE KRAKEN",  img: "Tentacle.png"        },
  { label: "SHARK",       img: "shark3.png"           },
  { label: "JERRY",       img: "jerryharpoon-r.png"  },
  { label: "SEA FLOOR",   img: "sea_floor.png"        },
  { label: "THE WRECK",   img: "shipwreck.png"        },
];

function buildArtwork() {
  const grid = document.getElementById("artGrid");
  if (!grid) return;
  ARTWORKS.forEach(art => {
    const card = document.createElement("div");
    card.className = "art-card";

    const imgEl = document.createElement("img");
    imgEl.src = art.img;
    imgEl.alt = art.label;
    imgEl.className = "art-img";
    imgEl.loading = "lazy";
    card.appendChild(imgEl);

    const label = document.createElement("div");
    label.className = "art-label";
    label.textContent = art.label;
    card.appendChild(label);
    grid.appendChild(card);
  });
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

// ── Enemies data ──────────────────────────────────────────────────────────────
const ENEMIES = [
  { label: "Shark",              img: "shark1.png"           },
  { label: "Jellyfish",          img: "pixil-frame-0.png"    },
  { label: "Shark Father",       img: "sharkboss.png"        },
  { label: "Kraken Tentacle",    img: "Tentacle.png"         },
  { label: "Skeleton (Melee)",   img: "pirate.png"           },
  { label: "Skeleton Captain",   img: "skeleton_captain.png" },
];

function buildEnemies() {
  const grid = document.getElementById("enemiesGrid");
  if (!grid) return;
  ENEMIES.forEach(en => {
    const card = document.createElement("div");
    card.className = "enemy-card";

    const img = document.createElement("img");
    img.src = en.img;
    img.alt = en.label;
    img.className = "enemy-img";
    img.loading = "lazy";
    card.appendChild(img);

    const label = document.createElement("div");
    label.className = "enemy-label";
    label.textContent = en.label;
    card.appendChild(label);

    grid.appendChild(card);
  });
}

// ── Collectables data ─────────────────────────────────────────────────────────
const COLLECTABLES = [
  { label: "Heart",   img: "heart.png"    },
  { label: "O2 Tank", img: "o2 tank.png"  },
];

function buildCollectables() {
  const grid = document.getElementById("collectablesGrid");
  if (!grid) return;
  COLLECTABLES.forEach(item => {
    const card = document.createElement("div");
    card.className = "enemy-card";

    const img = document.createElement("img");
    img.src = item.img;
    img.alt = item.label;
    img.className = "enemy-img";
    img.loading = "lazy";
    card.appendChild(img);

    const label = document.createElement("div");
    label.className = "enemy-label";
    label.textContent = item.label;
    card.appendChild(label);

    grid.appendChild(card);
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
buildLevels();
buildArtwork();
buildEnemies();
buildCollectables();
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
