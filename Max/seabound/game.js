// ── Sea Bound – Embedded Game (namespaced IIFE) ───────────────────────────────
// Wrapped so all variables are isolated from the website's own globals.
// Exposed on window.SeaBoundGame so site.js can start / stop it.

window.SeaBoundGame = (function () {

  // ── Canvas ──────────────────────────────────────────────────────────────────
  let canvas, ctx;
  const W = 800, H = 560;

  // ── Palette ─────────────────────────────────────────────────────────────────
  const C = {
    water0:"#00334e", water1:"#00446a", water2:"#005580", water3:"#006694",
    surface:"#0099cc", bubble:"rgba(180,230,255,0.55)",
    sand:"#c8a96e", sandDark:"#b5944e",
    coral0:"#e05050", coral1:"#ff7043",
    seaweed:"#2e8b57", seaweed2:"#3cb371",
    suit:"#1a6fa8", suitDark:"#0d4f7a", tank:"#aaaaaa",
    mask:"#88ddff", fin:"#e8a020",
    harpoon:"#e0e0e0", harpoonTip:"#ff6600",
    rope:"rgba(200,180,100,0.7)",
    sharkBody:"#607080", sharkBelly:"#c8d8e0", sharkFin:"#506070", sharkEye:"#ff2020",
    blood:"rgba(180,0,0,0.6)",
    heartFull:"#ff3355", heartEmpty:"#333355",
    uiBg:"rgba(0,20,40,0.75)",
    white:"#ffffff", yellow:"#ffd700", orange:"#ff8c00",
    overlay:"rgba(0,10,25,0.78)",
  };

  // ── Constants ────────────────────────────────────────────────────────────────
  let SAND_Y;
  const DIVER_SPEED     = 3.2;
  const HARPOON_SPD     = 9;
  const MAX_HARPOON_DIST= 340;
  const MAX_LIVES       = 3;
  const INVULN_TIME     = 120;

  // ── State ────────────────────────────────────────────────────────────────────
  const STATE = { START:"start", PLAYING:"playing", DEAD:"dead" };
  let state;
  let diver, harpoon, sharks, bubbles, particles, corals, seaweeds;
  let score, lives, wave, frameCount, sharkSpawnTimer, invulnTimer;
  let animId = null;
  let keys   = {};
  let mousePos = { x: 0, y: 0 };

  // ── Utility ──────────────────────────────────────────────────────────────────
  function rand(a, b)   { return Math.random() * (b - a) + a; }
  function randInt(a,b) { return Math.floor(rand(a, b + 1)); }
  function dist(a, b)   { return Math.hypot(a.x - b.x, a.y - b.y); }
  function clamp(v,lo,hi){ return Math.max(lo, Math.min(hi, v)); }

  // ── Spawn helpers ────────────────────────────────────────────────────────────
  function spawnBubbles(n = 18) {
    for (let i = 0; i < n; i++)
      bubbles.push({ x:rand(20,W-20), y:rand(80,SAND_Y-20),
        r:rand(2,6), vy:rand(-0.4,-1.0), alpha:rand(0.3,0.7) });
  }
  function spawnCoral() {
    corals = [];
    for (let i = 0; i < 9; i++)
      corals.push({ x:rand(30,W-30), y:SAND_Y+rand(4,22),
        height:randInt(18,44), branches:randInt(3,6),
        color:[C.coral0,C.coral1,"#ff9966","#cc4444"][randInt(0,3)] });
  }
  function spawnSeaweed() {
    seaweeds = [];
    for (let i = 0; i < 12; i++)
      seaweeds.push({ x:rand(0,W), segments:randInt(4,8),
        phase:rand(0,Math.PI*2),
        color:Math.random()>0.5 ? C.seaweed : C.seaweed2 });
  }
  function spawnShark() {
    const left = Math.random() > 0.5;
    const spd  = rand(1.2, 1.8 + wave * 0.18);
    sharks.push({ x:left?-80:W+80, y:rand(100,SAND_Y-40),
      vx:left?spd:-spd, vy:0, w:90, h:36, hp:1,
      phase:rand(0,Math.PI*2), hit:0, dead:false, deathTimer:0 });
  }
  function spawnParticle(x, y, color, n = 10) {
    for (let i = 0; i < n; i++) {
      const a = rand(0, Math.PI*2), s = rand(1.5, 5);
      particles.push({ x, y, vx:Math.cos(a)*s, vy:Math.sin(a)*s,
        r:rand(2,6), life:rand(20,45), maxLife:45, color });
    }
  }

  function initGame() {
    SAND_Y = H - 60;
    diver  = { x:120, y:260, w:48, h:32, vx:0, vy:0, facingRight:true };
    harpoon = null; sharks = []; bubbles = []; particles = [];
    score = 0; lives = MAX_LIVES; wave = 1;
    frameCount = 0; invulnTimer = 0; sharkSpawnTimer = 60;
    spawnBubbles(18); spawnCoral(); spawnSeaweed();
    state = STATE.START;
  }

  // ── Draw: background ─────────────────────────────────────────────────────────
  function drawBackground() {
    const grad = ctx.createLinearGradient(0,0,0,SAND_Y);
    grad.addColorStop(0, C.water0); grad.addColorStop(0.35, C.water1);
    grad.addColorStop(0.7, C.water2); grad.addColorStop(1, C.water3);
    ctx.fillStyle = grad; ctx.fillRect(0,0,W,SAND_Y);
    ctx.save();
    for (let i = 0; i < 5; i++) {
      const rx = (W/5)*i + W/10 + Math.sin(frameCount*0.008+i)*30;
      ctx.beginPath(); ctx.moveTo(rx,0);
      ctx.lineTo(rx-40,SAND_Y); ctx.lineTo(rx+40,SAND_Y); ctx.closePath();
      ctx.fillStyle = "rgba(0,180,255,0.04)"; ctx.fill();
    }
    ctx.restore();
    ctx.fillStyle = C.surface; ctx.fillRect(0,0,W,8);
    ctx.fillStyle = "rgba(255,255,255,0.18)";
    for (let i = 0; i < W; i += 30) {
      ctx.fillRect(i, 2, 14 + Math.sin(frameCount*0.04+i)*6, 3);
    }
    const sg = ctx.createLinearGradient(0,SAND_Y,0,H);
    sg.addColorStop(0,C.sand); sg.addColorStop(1,C.sandDark);
    ctx.fillStyle=sg; ctx.fillRect(0,SAND_Y,W,H-SAND_Y);
    ctx.strokeStyle="rgba(100,70,20,0.25)"; ctx.lineWidth=1;
    for (let i = 0; i < 8; i++) {
      const sy = SAND_Y+10+i*7; ctx.beginPath(); ctx.moveTo(0,sy);
      for (let x=0;x<W;x+=4) ctx.lineTo(x,sy+Math.sin((x+frameCount*0.3)*0.08)*2);
      ctx.stroke();
    }
  }

  function drawSeaweed() {
    seaweeds.forEach(sw => {
      ctx.lineWidth=4; ctx.strokeStyle=sw.color; ctx.lineCap="round";
      ctx.beginPath(); ctx.moveTo(sw.x,SAND_Y);
      for (let s=0;s<sw.segments;s++) {
        ctx.lineTo(sw.x+Math.sin(frameCount*0.05+sw.phase+s*0.8)*8, SAND_Y-(s+1)*18);
      }
      ctx.stroke();
    });
  }

  function drawCoral() {
    corals.forEach(c => {
      ctx.strokeStyle=c.color; ctx.lineWidth=5; ctx.lineCap="round";
      ctx.beginPath(); ctx.moveTo(c.x,c.y); ctx.lineTo(c.x,c.y-c.height); ctx.stroke();
      for (let b=0;b<c.branches;b++) {
        const t=(b+1)/(c.branches+1), by=c.y-c.height*t;
        const bLen=c.height*0.35, dir=b%2===0?1:-1;
        ctx.lineWidth=3; ctx.beginPath(); ctx.moveTo(c.x,by);
        ctx.lineTo(c.x+dir*bLen, by-bLen*0.6); ctx.stroke();
      }
    });
  }

  function drawBubbles() {
    bubbles.forEach(b => {
      ctx.save(); ctx.globalAlpha=b.alpha;
      ctx.strokeStyle=C.bubble; ctx.lineWidth=1;
      ctx.beginPath(); ctx.arc(b.x,b.y,b.r,0,Math.PI*2); ctx.stroke();
      ctx.restore();
    });
  }

  // ── Draw: diver ───────────────────────────────────────────────────────────────
  function drawDiver() {
    const {x,y,facingRight,w,h} = diver;
    if (invulnTimer>0 && Math.floor(invulnTimer/6)%2===0) return;
    ctx.save(); ctx.translate(x,y);
    if (!facingRight) ctx.scale(-1,1);
    ctx.fillStyle=C.tank; ctx.beginPath();
    ctx.roundRect(-w*0.08,-h*0.3,10,h*0.6,3); ctx.fill();
    ctx.fillStyle=C.suit; ctx.beginPath();
    ctx.roundRect(-w*0.38,-h*0.38,w*0.55,h*0.75,8); ctx.fill();
    ctx.fillStyle=C.suitDark; ctx.fillRect(-w*0.25,-h*0.3,4,h*0.55);
    ctx.fillStyle=C.suit; ctx.beginPath();
    ctx.arc(-w*0.15,-h*0.42,13,0,Math.PI*2); ctx.fill();
    ctx.fillStyle=C.mask; ctx.beginPath();
    ctx.ellipse(-w*0.18,-h*0.44,9,7,-0.2,0,Math.PI*2); ctx.fill();
    ctx.strokeStyle="#0055aa"; ctx.lineWidth=2; ctx.stroke();
    ctx.fillStyle="#333"; ctx.beginPath();
    ctx.arc(-w*0.2,-h*0.46,2,0,Math.PI*2); ctx.fill();
    ctx.fillStyle=C.fin;
    ctx.beginPath(); ctx.ellipse(-w*0.28,h*0.38,18,7,0.3,0,Math.PI*2); ctx.fill();
    ctx.beginPath(); ctx.ellipse(-w*0.12,h*0.38,18,7,-0.3,0,Math.PI*2); ctx.fill();
    ctx.fillStyle=C.suit; ctx.beginPath();
    ctx.roundRect(w*0.14,-h*0.18,14,8,3); ctx.fill();
    ctx.fillStyle="#334"; ctx.beginPath();
    ctx.roundRect(w*0.22,-h*0.22,28,9,3); ctx.fill();
    ctx.fillStyle="#556"; ctx.fillRect(w*0.28,-h*0.24,14,4);
    ctx.restore();
    if (frameCount%18===0)
      bubbles.push({ x:x+(facingRight?-w*0.08:w*0.08), y:y-h*0.48,
        r:rand(2,4), vy:rand(-0.5,-0.9), alpha:0.55 });
  }

  // ── Draw: harpoon ─────────────────────────────────────────────────────────────
  function drawHarpoon() {
    if (!harpoon) return;
    const {x,y,ox,oy} = harpoon;
    ctx.save(); ctx.strokeStyle=C.rope; ctx.lineWidth=1.5;
    ctx.setLineDash([4,4]); ctx.beginPath();
    ctx.moveTo(ox,oy); ctx.lineTo(x,y); ctx.stroke();
    ctx.setLineDash([]); ctx.restore();
    const angle = Math.atan2(harpoon.dy,harpoon.dx);
    ctx.save(); ctx.translate(x,y); ctx.rotate(angle);
    ctx.fillStyle=C.harpoon; ctx.fillRect(-18,-2,36,4);
    ctx.fillStyle=C.harpoonTip; ctx.beginPath();
    ctx.moveTo(18,0); ctx.lineTo(10,-5); ctx.lineTo(10,5); ctx.closePath(); ctx.fill();
    ctx.fillStyle="#aaa";
    ctx.beginPath(); ctx.moveTo(-18,0); ctx.lineTo(-24,-5); ctx.lineTo(-18,-2); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.moveTo(-18,0); ctx.lineTo(-24,5);  ctx.lineTo(-18,2);  ctx.closePath(); ctx.fill();
    ctx.restore();
  }

  // ── Draw: shark ───────────────────────────────────────────────────────────────
  function drawShark(s) {
    const {x,y,w,h,vx,hit,dead,deathTimer} = s;
    if (dead && deathTimer<=0) return;
    ctx.save(); ctx.translate(x,y);
    ctx.globalAlpha = dead ? deathTimer/30 : 1;
    if (vx>0) ctx.scale(-1,1);
    ctx.rotate(Math.sin(frameCount*0.18+s.phase)*3*0.04);
    if (hit>0) ctx.filter="brightness(3) sepia(1) saturate(5) hue-rotate(-20deg)";
    ctx.fillStyle=C.sharkFin;
    ctx.beginPath(); ctx.moveTo(-w*0.5,0); ctx.lineTo(-w*0.7,-h*0.55);
    ctx.lineTo(-w*0.55,0); ctx.lineTo(-w*0.7,h*0.55); ctx.closePath(); ctx.fill();
    ctx.fillStyle=C.sharkBody; ctx.beginPath();
    ctx.ellipse(0,0,w*0.5,h*0.42,0,0,Math.PI*2); ctx.fill();
    ctx.fillStyle=C.sharkBelly; ctx.beginPath();
    ctx.ellipse(w*0.05,h*0.1,w*0.32,h*0.22,0,0,Math.PI*2); ctx.fill();
    ctx.fillStyle=C.sharkFin;
    ctx.beginPath(); ctx.moveTo(-w*0.05,-h*0.42); ctx.lineTo(w*0.18,-h*0.85);
    ctx.lineTo(w*0.3,-h*0.42); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.moveTo(w*0.1,h*0.12); ctx.lineTo(w*0.25,h*0.62);
    ctx.lineTo(w*0.38,h*0.15); ctx.closePath(); ctx.fill();
    ctx.fillStyle=C.sharkBody; ctx.beginPath();
    ctx.ellipse(w*0.5,0,w*0.18,h*0.28,0,0,Math.PI*2); ctx.fill();
    ctx.strokeStyle="#223"; ctx.lineWidth=2; ctx.beginPath();
    ctx.moveTo(w*0.42,h*0.08); ctx.quadraticCurveTo(w*0.62,h*0.2,w*0.42,h*0.02); ctx.stroke();
    ctx.fillStyle=C.white;
    for (let t=0;t<4;t++) {
      ctx.beginPath(); ctx.moveTo(w*(0.44+t*0.035),h*0.08);
      ctx.lineTo(w*(0.455+t*0.035),h*0.18); ctx.lineTo(w*(0.47+t*0.035),h*0.08);
      ctx.closePath(); ctx.fill();
    }
    ctx.fillStyle=C.sharkEye; ctx.beginPath();
    ctx.arc(w*0.36,-h*0.1,4,0,Math.PI*2); ctx.fill();
    ctx.fillStyle="#111"; ctx.beginPath();
    ctx.arc(w*0.36,-h*0.1,2,0,Math.PI*2); ctx.fill();
    ctx.restore();
  }

  function drawParticles() {
    particles.forEach(p => {
      ctx.save(); ctx.globalAlpha=p.life/p.maxLife;
      ctx.fillStyle=p.color; ctx.beginPath();
      ctx.arc(p.x,p.y,p.r,0,Math.PI*2); ctx.fill(); ctx.restore();
    });
  }

  // ── Draw: HUD ─────────────────────────────────────────────────────────────────
  function drawHUD() {
    ctx.fillStyle=C.uiBg; ctx.beginPath();
    ctx.roundRect(8,8,200,52,8); ctx.fill();
    ctx.fillStyle=C.yellow; ctx.font="bold 14px Arial"; ctx.textAlign="left";
    ctx.fillText("SCORE",20,26);
    ctx.fillStyle=C.white; ctx.font="bold 22px Arial"; ctx.fillText(String(score),20,50);
    ctx.fillStyle=C.uiBg; ctx.beginPath();
    ctx.roundRect(W/2-60,8,120,36,8); ctx.fill();
    ctx.fillStyle=C.orange; ctx.font="bold 14px Arial"; ctx.textAlign="center";
    ctx.fillText(`WAVE  ${wave}`,W/2,30);
    ctx.fillStyle=C.uiBg; ctx.beginPath();
    ctx.roundRect(W-130,8,122,52,8); ctx.fill();
    ctx.fillStyle=C.white; ctx.font="bold 13px Arial"; ctx.textAlign="right";
    ctx.fillText("LIVES",W-16,24);
    for (let i=0;i<MAX_LIVES;i++) drawHeart(W-28-i*34,42,i<lives?C.heartFull:C.heartEmpty);
    if (!harpoon) {
      ctx.save(); ctx.translate(mousePos.x,mousePos.y);
      ctx.strokeStyle="rgba(255,220,80,0.6)"; ctx.lineWidth=1.5;
      ctx.beginPath(); ctx.arc(0,0,10,0,Math.PI*2); ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(-14,0); ctx.lineTo(-6,0); ctx.moveTo(6,0); ctx.lineTo(14,0);
      ctx.moveTo(0,-14); ctx.lineTo(0,-6); ctx.moveTo(0,6); ctx.lineTo(0,14);
      ctx.stroke(); ctx.restore();
    }
    ctx.textAlign="left";
  }

  function drawHeart(cx,cy,color) {
    ctx.fillStyle=color; ctx.beginPath();
    ctx.moveTo(cx,cy-3);
    ctx.bezierCurveTo(cx,cy-9,cx-12,cy-9,cx-12,cy-2);
    ctx.bezierCurveTo(cx-12,cy+4,cx,cy+10,cx,cy+10);
    ctx.bezierCurveTo(cx,cy+10,cx+12,cy+4,cx+12,cy-2);
    ctx.bezierCurveTo(cx+12,cy-9,cx,cy-9,cx,cy-3); ctx.fill();
  }

  function drawOverlay(title, sub1, sub2) {
    ctx.fillStyle=C.overlay; ctx.fillRect(0,0,W,H);
    ctx.textAlign="center";
    ctx.fillStyle=C.yellow; ctx.font="bold 52px Arial"; ctx.fillText(title,W/2,H/2-40);
    ctx.fillStyle=C.white;  ctx.font="bold 22px Arial"; ctx.fillText(sub1,W/2,H/2+10);
    if (sub2) { ctx.fillStyle="rgba(255,255,255,0.65)"; ctx.font="16px Arial"; ctx.fillText(sub2,W/2,H/2+42); }
    ctx.textAlign="left";
  }

  function drawStartScreen() {
    drawBackground();
    ctx.textAlign="center";
    ctx.fillStyle=C.uiBg; ctx.beginPath();
    ctx.roundRect(W/2-240,H/2-130,480,260,16); ctx.fill();
    ctx.fillStyle=C.yellow; ctx.font="bold 42px Arial"; ctx.fillText("SEA \u2693 BOUND",W/2,H/2-65);
    ctx.fillStyle=C.white;  ctx.font="20px Arial";      ctx.fillText("Scuba Fighter",W/2,H/2-28);
    ctx.fillStyle=C.orange; ctx.font="bold 15px Arial";
    ctx.fillText("WASD / Arrows \u2014 Move",W/2,H/2+18);
    ctx.fillText("Click / Space \u2014 Fire Harpoon",W/2,H/2+44);
    ctx.fillStyle=C.yellow; ctx.font="bold 18px Arial";
    ctx.fillText("Click or press Space to start",W/2,H/2+90);
    ctx.textAlign="left";
  }

  // ── Update ────────────────────────────────────────────────────────────────────
  function updateDiver() {
    let ax=0, ay=0;
    if (keys["ArrowLeft"] ||keys["a"]||keys["A"]) ax-=1;
    if (keys["ArrowRight"]||keys["d"]||keys["D"]) ax+=1;
    if (keys["ArrowUp"]   ||keys["w"]||keys["W"]) ay-=1;
    if (keys["ArrowDown"] ||keys["s"]||keys["S"]) ay+=1;
    diver.vx=ax*DIVER_SPEED; diver.vy=ay*DIVER_SPEED;
    diver.x=clamp(diver.x+diver.vx,diver.w/2,W-diver.w/2);
    diver.y=clamp(diver.y+diver.vy,40,SAND_Y-diver.h/2-4);
    if (ax!==0) diver.facingRight=ax>0;
    if (invulnTimer>0) invulnTimer--;
  }

  function updateHarpoon() {
    if (!harpoon) return;
    harpoon.x+=harpoon.dx*HARPOON_SPD; harpoon.y+=harpoon.dy*HARPOON_SPD;
    harpoon.traveled+=HARPOON_SPD;
    for (let i=sharks.length-1;i>=0;i--) {
      const s=sharks[i]; if (s.dead) continue;
      if (harpoon.x>s.x-s.w*0.55 && harpoon.x<s.x+s.w*0.55 &&
          harpoon.y>s.y-s.h*0.55 && harpoon.y<s.y+s.h*0.55) {
        s.dead=true; s.deathTimer=30; score+=100;
        spawnParticle(s.x,s.y,C.blood,14); spawnParticle(s.x,s.y,C.sharkBody,8);
        harpoon=null; return;
      }
    }
    if (harpoon.traveled>MAX_HARPOON_DIST||harpoon.x<0||harpoon.x>W||
        harpoon.y<0||harpoon.y>SAND_Y) harpoon=null;
  }

  function updateSharks() {
    sharkSpawnTimer--;
    if (sharkSpawnTimer<=0) {
      if (sharks.filter(s=>!s.dead).length < 2+wave) spawnShark();
      sharkSpawnTimer=Math.max(80-wave*8,30);
    }
    for (let i=sharks.length-1;i>=0;i--) {
      const s=sharks[i];
      if (s.dead) { s.deathTimer--; if (s.deathTimer<=0) sharks.splice(i,1); continue; }
      s.vy=clamp(s.vy+(diver.y-s.y)*0.003,-1.5,1.5); s.y+=s.vy;
      s.x+=s.vx*(dist(s,diver)<160?1.5:1);
      if (s.x<-150||s.x>W+150) { sharks.splice(i,1); continue; }
      if (s.hit>0) s.hit--;
      if (invulnTimer===0 && dist(s,diver)<36) {
        lives--; invulnTimer=INVULN_TIME;
        spawnParticle(diver.x,diver.y,C.blood,10);
        if (lives<=0) state=STATE.DEAD;
      }
    }
  }

  function updateAmbient() {
    bubbles.forEach(b => {
      b.y+=b.vy; b.x+=Math.sin(frameCount*0.05+b.y)*0.3;
      if (b.y<0) { b.y=SAND_Y-10; b.x=rand(20,W-20); }
    });
    for (let i=particles.length-1;i>=0;i--) {
      const p=particles[i]; p.x+=p.vx; p.y+=p.vy; p.vy+=0.08; p.life--;
      if (p.life<=0) particles.splice(i,1);
    }
  }

  // ── Fire harpoon ──────────────────────────────────────────────────────────────
  function fireHarpoon() {
    if (harpoon) return;
    const angle=Math.atan2(mousePos.y-diver.y,mousePos.x-diver.x);
    const gx=diver.x+(diver.facingRight?38:-38), gy=diver.y-5;
    harpoon={x:gx,y:gy,ox:gx,oy:gy,dx:Math.cos(angle),dy:Math.sin(angle),traveled:0};
    diver.facingRight=mousePos.x>=diver.x;
  }

  // ── Game loop ─────────────────────────────────────────────────────────────────
  function gameLoop() {
    animId = requestAnimationFrame(gameLoop);
    frameCount++;
    if (state===STATE.START) { drawStartScreen(); return; }
    if (state===STATE.PLAYING) {
      updateDiver(); updateHarpoon(); updateSharks();
      wave=Math.floor(score/500)+1; updateAmbient();
    }
    drawBackground(); drawSeaweed(); drawCoral();
    drawBubbles(); drawParticles(); sharks.forEach(drawShark);
    drawHarpoon(); drawDiver(); drawHUD();
    if (state===STATE.DEAD)
      drawOverlay("GAME OVER",`Score: ${score}`,"Click or press Space to retry");
  }

  // ── Input handlers (stored so we can remove them on stop) ─────────────────────
  function onKeyDown(e) {
    // Only intercept keys when the play page is active
    if (!document.getElementById("play")?.classList.contains("active")) return;
    keys[e.key]=true;
    if (["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"," "].includes(e.key)) e.preventDefault();
    if (e.key===" ") {
      if (state===STATE.START||state===STATE.DEAD) { initGame(); state=STATE.PLAYING; }
      else fireHarpoon();
    }
  }
  function onKeyUp(e)   { keys[e.key]=false; }
  function onMouseMove(e) {
    const r=canvas.getBoundingClientRect();
    mousePos.x=(e.clientX-r.left)*(W/r.width);
    mousePos.y=(e.clientY-r.top)*(H/r.height);
  }
  function onClick(e) {
    const r=canvas.getBoundingClientRect();
    mousePos.x=(e.clientX-r.left)*(W/r.width);
    mousePos.y=(e.clientY-r.top)*(H/r.height);
    if (state===STATE.START||state===STATE.DEAD) { initGame(); state=STATE.PLAYING; }
    else fireHarpoon();
  }
  let touchAim=null;
  function onTouchStart(e) {
    e.preventDefault();
    const t=e.touches[0], r=canvas.getBoundingClientRect();
    touchAim={x:(t.clientX-r.left)*(W/r.width),y:(t.clientY-r.top)*(H/r.height)};
  }
  function onTouchEnd(e) {
    e.preventDefault(); if(!touchAim) return;
    mousePos={...touchAim};
    if (state===STATE.START||state===STATE.DEAD){initGame();state=STATE.PLAYING;}
    else fireHarpoon();
    touchAim=null;
  }

  // ── Public API ────────────────────────────────────────────────────────────────
  function start(canvasEl) {
    canvas = canvasEl;
    ctx    = canvas.getContext("2d");
    canvas.width=W; canvas.height=H;
    initGame();
    document.addEventListener("keydown",  onKeyDown);
    document.addEventListener("keyup",    onKeyUp);
    canvas.addEventListener("mousemove",  onMouseMove);
    canvas.addEventListener("click",      onClick);
    canvas.addEventListener("touchstart", onTouchStart, {passive:false});
    canvas.addEventListener("touchend",   onTouchEnd,   {passive:false});
    if (animId) cancelAnimationFrame(animId);
    gameLoop();
  }

  function stop() {
    if (animId) { cancelAnimationFrame(animId); animId=null; }
    document.removeEventListener("keydown",  onKeyDown);
    document.removeEventListener("keyup",    onKeyUp);
    if (canvas) {
      canvas.removeEventListener("mousemove",  onMouseMove);
      canvas.removeEventListener("click",      onClick);
      canvas.removeEventListener("touchstart", onTouchStart);
      canvas.removeEventListener("touchend",   onTouchEnd);
    }
    keys={};
  }

  return { start, stop };
})();
