import pygame
import sys
import os
from random import randint, uniform, choice
from math import sin, cos, pi

# Add the Fionn folder so we can import OxygenTank
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Fionn'))
from oxygentank import OxygenTank

pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Underwater Harpoon")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 28)
small_font = pygame.font.SysFont("arial", 22)
big_font = pygame.font.SysFont("arial", 64, bold=True)
title_font = pygame.font.SysFont("arial", 40, bold=True)

# ---------------------------------------------------------------------------
# Sound effects
# ---------------------------------------------------------------------------
pygame.mixer.init()

def _load_sound(path, volume=100.0):
    """Load a sound file. Returns a silent placeholder if the file is missing."""
    try:
        snd = pygame.mixer.Sound(path)
        snd.set_volume(volume)
        return snd
    except (pygame.error, FileNotFoundError) as e:
        print(f"[sound] couldn't load '{path}' ({e}) - using silent placeholder.")
        # Return a zero-length silent sound so .play() calls never crash
        buf = pygame.mixer.Sound(buffer=bytes(44))
        return buf

# ── placeholder paths — swap these for your own files ──────────────────────
SFX_HARPOON_SHOOT  = _load_sound('sounds/harpoongun.ogg',       volume=0.8)
SFX_HEALTH_PICKUP  = _load_sound('sounds/heart bubble.ogg',     volume=0.8)
SFX_JELLY_ATTACK   = _load_sound('sounds/jellyfish attack.ogg', volume=0.8)
SFX_JELLY_DIE      = _load_sound('sounds/jellyfish die.ogg',    volume=0.8)
SFX_PLAYER_DAMAGE  = _load_sound('sounds/jerry damage.ogg',     volume=1.0)
SFX_PLAYER_DIE     = _load_sound('sounds/jerrydie.ogg',         volume=1.0)
SFX_SHARK_ATTACK   = _load_sound('sounds/sharkbiteAUDIO.ogg',   volume=0.9)
SFX_SHARK_DIE      = _load_sound('sounds/shark die.ogg',        volume=0.8)
SFX_BOSS_DIE       = _load_sound('sounds/boss die.ogg',         volume=1.0)
SFX_OXYGEN_PICKUP  = _load_sound('sounds/oxygen tank.ogg',      volume=0.7)
# ── end of sound placeholders ───────────────────────────────────────────────

# ---------------------------------------------------------------------------
# Art loading helpers
# ---------------------------------------------------------------------------
def load_or_placeholder(path, placeholder_maker, alpha=True):
    try:
        surf = pygame.image.load(path)
        return surf.convert_alpha() if alpha else surf.convert()
    except (pygame.error, FileNotFoundError) as e:
        print(f"[art] couldn't load '{path}' ({e}) - using placeholder art instead.")
        return placeholder_maker()

def make_player_surface():
    """
    Diver with a wetsuit body, swim fins, face mask, and a harpoon gun barrel.
    Faces LEFT by default (the code flips it for right-facing).
    Canvas: 90 x 54
    """
    W, H = 90, 54
    surf = pygame.Surface((W, H), pygame.SRCALPHA)

    # --- body (wetsuit, dark teal-blue) ---
    body_pts = [(10, 27), (20, 12), (55, 10), (65, 18), (65, 36), (55, 44), (20, 42)]
    pygame.draw.polygon(surf, (30, 80, 100),  body_pts)
    pygame.draw.polygon(surf, (20, 55, 75),   body_pts, 2)

    # --- wetsuit stripe (yellow accent down the side) ---
    stripe_pts = [(22, 14), (52, 12), (52, 20), (22, 22)]
    pygame.draw.polygon(surf, (220, 190, 50), stripe_pts)

    # --- head / helmet ---
    pygame.draw.circle(surf, (45, 110, 130),  (18, 27), 12)   # helmet shell
    pygame.draw.circle(surf, (15, 50,  70),   (18, 27), 10)   # dark visor base
    pygame.draw.ellipse(surf, (100, 200, 230, 160), (10, 20, 14, 14))  # visor glass

    # --- oxygen tank on back ---
    pygame.draw.ellipse(surf, (180, 180, 200), (56, 14, 12, 26))
    pygame.draw.ellipse(surf, (140, 140, 160), (56, 14, 12, 26), 1)
    pygame.draw.line(surf, (160, 160, 180), (62, 14), (62,  8), 2)   # regulator pipe

    # --- swim fins (bottom) ---
    fin_pts = [(10, 42), (28, 42), (24, 54), (4, 52)]
    pygame.draw.polygon(surf, (50, 160, 140), fin_pts)
    pygame.draw.polygon(surf, (30, 120, 110), fin_pts, 1)

    # --- harpoon gun barrel ---
    pygame.draw.rect(surf,  (90, 60, 30),  pygame.Rect(32, 22, 34, 7), border_radius=2)
    pygame.draw.rect(surf,  (60, 40, 20),  pygame.Rect(32, 22, 34, 7), 1, border_radius=2)
    # gun grip
    pygame.draw.polygon(surf, (70, 45, 25), [(42, 29), (50, 29), (48, 36), (40, 36)])
    # muzzle tip
    pygame.draw.rect(surf, (200, 200, 215), pygame.Rect(64, 23, 8, 5), border_radius=1)

    # --- bubble from regulator ---
    pygame.draw.circle(surf, (200, 230, 255, 140), (65, 6), 3)
    pygame.draw.circle(surf, (200, 230, 255, 90),  (70, 3), 2)

    return surf


def make_harpoon_surface():
    """Sleek harpoon bolt: wooden shaft + steel tip + flight vanes."""
    W, H = 52, 14
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    # shaft
    pygame.draw.rect(surf, (160, 110, 60), pygame.Rect(0, 5, 40, 4), border_radius=2)
    pygame.draw.rect(surf, (130, 85,  40), pygame.Rect(0, 5, 40, 4), 1, border_radius=2)
    # steel tip
    pygame.draw.polygon(surf, (210, 215, 225), [(38, 2), (52, 7), (38, 12)])
    pygame.draw.polygon(surf, (170, 175, 185), [(38, 2), (52, 7), (38, 12)], 1)
    # vanes at tail
    pygame.draw.polygon(surf, (200, 70, 50), [(0, 5), (8, 1), (8, 5)])
    pygame.draw.polygon(surf, (200, 70, 50), [(0, 9), (8, 9), (8, 13)])
    return surf


def make_shark_surface():
    """
    Detailed shark: tapered body, dorsal + pectoral + caudal fins,
    white belly, gill slits, eye with pupil, teeth hint.
    Faces RIGHT. Canvas: 120 x 60
    """
    W, H = 120, 60
    surf = pygame.Surface((W, H), pygame.SRCALPHA)

    # --- main body ---
    body_pts = [
        (0, 30),          # snout tip
        (15, 18), (50, 10), (85, 12),   # top edge
        (110, 20),        # caudal peduncle top
        (120, 12),        # tail top
        (120, 48),        # tail bottom
        (110, 40),        # caudal peduncle bottom
        (85, 48), (50, 50), (15, 42),   # bottom edge
        (8, 36),          # chin
    ]
    pygame.draw.polygon(surf, (100, 115, 130), body_pts)
    pygame.draw.polygon(surf, (75,  88, 105),  body_pts, 2)

    # --- white belly ---
    belly_pts = [
        (10, 32), (50, 40), (90, 38), (108, 32),
        (90, 34), (50, 36), (10, 34),
    ]
    pygame.draw.polygon(surf, (230, 235, 240), belly_pts)

    # --- dorsal fin ---
    dorsal = [(55, 10), (68, -4), (80, 10)]
    pygame.draw.polygon(surf, (80, 95, 112), dorsal)
    pygame.draw.polygon(surf, (60, 75,  92), dorsal, 1)

    # --- pectoral fin (side fin) ---
    pec = [(35, 32), (25, 52), (55, 40)]
    pygame.draw.polygon(surf, (85, 100, 118), pec)
    pygame.draw.polygon(surf, (65,  80,  98), pec, 1)

    # --- caudal (tail) fin ---
    caudal_top    = [(108, 24), (120, 12), (115, 30)]
    caudal_bottom = [(108, 36), (120, 48), (115, 30)]
    pygame.draw.polygon(surf, (80, 95, 112), caudal_top)
    pygame.draw.polygon(surf, (80, 95, 112), caudal_bottom)
    pygame.draw.polygon(surf, (60, 75, 92),  caudal_top,    1)
    pygame.draw.polygon(surf, (60, 75, 92),  caudal_bottom, 1)

    # --- gill slits ---
    for gx in [28, 33, 38]:
        pygame.draw.arc(surf, (60, 72, 85),
                        pygame.Rect(gx, 20, 4, 16), 0.2, pi - 0.2, 1)

    # --- eye ---
    pygame.draw.circle(surf, (240, 245, 250), (22, 22), 5)
    pygame.draw.circle(surf, (15,  15,  20),  (23, 22), 3)   # pupil
    pygame.draw.circle(surf, (255, 255, 255), (24, 21), 1)   # specular

    # --- teeth hint at snout ---
    for tx in [4, 8]:
        pygame.draw.polygon(surf, (240, 242, 245),
                            [(tx, 28), (tx + 3, 24), (tx + 6, 28)])

    return surf


def make_jellyfish_surface():
    """
    High-quality jellyfish: smooth gradient-like bell with inner organs,
    rim fringe, and thick tentacles. Canvas 72 x 96.
    Animated version is built frame-by-frame in the Jellyfish class;
    this function is only used as the loaded-image fallback placeholder.
    """
    return _build_jelly_frame(0.0)


def _build_jelly_frame(pulse: float):
    """
    Draw one frame of the jellyfish bell.
    pulse = 0.0 → fully relaxed (wide bell)
    pulse = 1.0 → fully contracted (narrow, tall bell)
    Returns a new Surface each call.
    """
    BASE_W, BASE_H = 72, 52   # bell only — tentacles drawn separately
    squeeze = 1.0 - pulse * 0.22          # horizontal squeeze
    stretch = 1.0 + pulse * 0.14          # vertical stretch

    bw = max(10, round(BASE_W * squeeze))
    bh = max(10, round(BASE_H * stretch))

    # --- draw at fixed size then scale (cleaner curves) ---
    bell = pygame.Surface((BASE_W, BASE_H + 4), pygame.SRCALPHA)

    # outer bell — deep violet
    pygame.draw.ellipse(bell, (120, 50, 180, 220),  (2, 2, BASE_W - 4, BASE_H - 2))
    # mid layer — medium purple
    pygame.draw.ellipse(bell, (160, 80, 220, 180),  (8, 4, BASE_W - 16, BASE_H - 10))
    # inner glow — bright pink-purple
    pygame.draw.ellipse(bell, (200, 120, 255, 130), (16, 6, BASE_W - 32, BASE_H - 20))
    # specular highlight (top-left)
    pygame.draw.ellipse(bell, (240, 210, 255, 90),  (14, 5, 20, 12))

    # rim fringe dots
    for i in range(9):
        angle  = pi * i / 8
        rx     = BASE_W // 2 + round((BASE_W // 2 - 4) * cos(angle))
        ry     = BASE_H - 4  - round(4 * abs(sin(angle)))
        radius = 3 if i % 2 == 0 else 2
        pygame.draw.circle(bell, (220, 160, 255, 200), (rx, ry), radius)

    # --- tentacle strip below bell ---
    TENT_H   = 44
    total_h  = BASE_H + TENT_H
    full     = pygame.Surface((BASE_W, total_h), pygame.SRCALPHA)
    full.blit(bell, (0, 0))

    # draw 7 tentacles with sinusoidal sway baked in
    cols = [8, 18, 28, 36, 44, 54, 64]
    for ci, tx in enumerate(cols):
        thickness = 2 if ci % 2 == 0 else 1
        for seg in range(10):
            sy1 = BASE_H + seg * (TENT_H // 10)
            sy2 = BASE_H + (seg + 1) * (TENT_H // 10)
            sway = round(sin(seg * 0.6 + ci * 0.9 + pulse * 3) * 4)
            col  = (200, 100, 240, max(40, 200 - seg * 16))
            pygame.draw.line(full, col, (tx + sway, sy1), (tx + sway, sy2), thickness)

    # scale to pulse dimensions
    return pygame.transform.smoothscale(full, (bw, round(total_h * stretch)))

def make_mapfrag_surface():
    """Fallback if mapfrag1.png is missing."""
    size = 40
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    points = [(size/2, 0),(size, size*0.4),(size*0.75, size),(size*0.25, size),(0, size*0.4)]
    pygame.draw.polygon(surf, (250, 210, 90), points)
    pygame.draw.polygon(surf, (255, 255, 255), points, 2)
    return surf

def make_background_tile():
    """
    Rich underwater background:
    - Deep gradient from sunlit surface teal to abyssal navy
    - Caustic light rays fanning from top
    - Scattered coral silhouettes at the bottom
    - Fine particle dust / plankton dots
    - Subtle dark-rock sea floor strip
    """
    W, H = WINDOW_WIDTH, WINDOW_HEIGHT
    tile = pygame.Surface((W, H))

    # --- base gradient ---
    surf_color  = pygame.Color(20, 120, 160)
    abyss_color = pygame.Color(4,  22,  55)
    for y in range(H):
        t = y / H
        c = surf_color.lerp(abyss_color, t ** 1.6)   # accelerated darkening
        pygame.draw.line(tile, c, (0, y), (W, y))

    # --- caustic light shafts from top ---
    ray_surf = pygame.Surface((W, H), pygame.SRCALPHA)
    num_rays = 9
    for i in range(num_rays):
        cx  = int(W * (i + 0.5) / num_rays) + randint(-30, 30)
        w_r = randint(30, 80)
        pts = [
            (cx - w_r // 2, 0),
            (cx + w_r // 2, 0),
            (cx + w_r * 2,  H // 2),
            (cx - w_r * 2,  H // 2),
        ]
        alpha = randint(12, 26)
        pygame.draw.polygon(ray_surf, (180, 230, 255, alpha), pts)
    tile.blit(ray_surf, (0, 0))

    # --- sea-floor strip ---
    floor_y = int(H * 0.82)
    for y in range(floor_y, H):
        t    = (y - floor_y) / (H - floor_y)
        dark = pygame.Color(12, 28, 18).lerp(pygame.Color(6, 14, 8), t)
        pygame.draw.line(tile, dark, (0, y), (W, y))

    # --- coral / rock silhouettes ---
    coral_surf = pygame.Surface((W, H), pygame.SRCALPHA)
    colors = [(160, 60, 50, 200), (140, 80, 30, 200), (80, 130, 60, 200)]
    for _ in range(18):
        bx    = randint(0, W)
        by    = randint(floor_y - 10, floor_y + 20)
        btype = randint(0, 2)
        col   = colors[btype]
        if btype == 0:   # branching coral
            h_c = randint(30, 70)
            pygame.draw.line(coral_surf, col, (bx, by), (bx, by - h_c), 3)
            pygame.draw.line(coral_surf, col, (bx, by - h_c // 2),
                             (bx - 10, by - h_c // 2 - 15), 2)
            pygame.draw.line(coral_surf, col, (bx, by - h_c // 2),
                             (bx + 10, by - h_c // 2 - 15), 2)
        elif btype == 1: # boulder
            r = randint(12, 28)
            pygame.draw.ellipse(coral_surf, col, (bx - r, by - r // 2, r * 2, r))
        else:            # seaweed stalk
            h_s = randint(25, 55)
            for seg in range(h_s // 5):
                sx  = bx + round(sin(seg * 0.8) * 5)
                sy1 = by - seg * 5
                sy2 = by - (seg + 1) * 5
                pygame.draw.line(coral_surf, col, (sx, sy1), (sx, sy2), 2)
    tile.blit(coral_surf, (0, 0))

    # --- plankton / dust particles ---
    for _ in range(120):
        px = randint(0, W)
        py = randint(0, floor_y)
        r  = randint(1, 3)
        a  = randint(30, 100)
        # draw onto a tiny alpha surface to get transparency
        dot = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(dot, (200, 235, 255, a), (r, r), r)
        tile.blit(dot, (px - r, py - r))

    return tile.convert()

def scale_surface(surf, factor):
    w, h = surf.get_size()
    return pygame.transform.smoothscale(surf, (max(1, round(w * factor)), max(1, round(h * factor))))

PLAYER_SCALE  = 1.5
HARPOON_SCALE = 1.2
SHARK_SCALE   = 1.6
BOSS_EXTRA_SCALE = 2.7

player_surf = scale_surface(load_or_placeholder('images/jerryharpoon.png', make_player_surface), PLAYER_SCALE)

_harpoon_raw = load_or_placeholder('images/harpoon.png', make_harpoon_surface)
harpoon_surf = scale_surface(_harpoon_raw.subsurface(_harpoon_raw.get_bounding_rect()).copy(), HARPOON_SCALE)


# ---------------------------------------------------------------------------
# Shark surfaces — all variants use shark1.png
#   Normal shark : original scale
#   Boss shark   : scaled up + red tint
#   The "frame arrays" are single-element lists so the animation code
#   works without any other changes.
# ---------------------------------------------------------------------------
_shark1    = scale_surface(load_or_placeholder('images/shark1.png',    make_shark_surface), SHARK_SCALE)
_sharkmov1 = scale_surface(load_or_placeholder('images/sharkmov1.png', make_shark_surface), SHARK_SCALE)
_sharkmov2 = scale_surface(load_or_placeholder('images/sharkmov2.png', make_shark_surface), SHARK_SCALE)

# Swim animation: 3-frame cycle.  Attack uses shark1 only.
SHARK_SWIM_FRAMES   = [_shark1, _sharkmov1, _sharkmov2]
SHARK_ATTACK_FRAMES = [_shark1]

# Boss: load sharkboss.png (scaled up, no tint)
def _make_boss_surface():
    """Fallback if sharkboss.png is missing."""
    return scale_surface(make_shark_surface(), BOSS_EXTRA_SCALE)

_boss1 = scale_surface(
    load_or_placeholder('images/sharkboss.png', _make_boss_surface), BOSS_EXTRA_SCALE
)

BOSS_SWIM_FRAMES   = [_boss1]
BOSS_ATTACK_FRAMES = [_boss1]
background_surf = load_or_placeholder('images/background.jpeg', make_background_tile, alpha=False)
# Scale the map to 1.5× the window so it's compact but still scrollable
_MAP_SCALE = 1.5
background_surf = pygame.transform.smoothscale(
    background_surf,
    (round(WINDOW_WIDTH * _MAP_SCALE), round(WINDOW_HEIGHT * _MAP_SCALE))
).convert()
# Dim the background so it reads as distant
_bg_dim = pygame.Surface(background_surf.get_size(), pygame.SRCALPHA)
_bg_dim.fill((0, 10, 30, 110))
background_surf.blit(_bg_dim, (0, 0))

bg_width, bg_height = background_surf.get_size()
WORLD_BOUNDS = pygame.Rect(0, 0, bg_width, bg_height)

# ---------------------------------------------------------------------------
# Sea floor — rendered at the bottom of the world.
# FLOOR_Y is the y-coordinate of the TOP of the floor (collision boundary).
# Players, sharks and jellyfish are clamped so their bottom never crosses it.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Sea floor — rendered at the bottom of the world.
# FLOOR_Y is the y-coordinate of the TOP of the floor (collision boundary).
# Players, sharks and jellyfish are clamped so their bottom never crosses it.
# ---------------------------------------------------------------------------
FLOOR_THICKNESS = 90          # pixel height of the floor strip
FLOOR_Y         = bg_height - FLOOR_THICKNESS   # collision top edge

def _make_floor_surface():
    """
    Rich procedural sea floor:
      - Sand gradient + ripple marks + grain noise (as before)
      - Rock formations: large boulders with highlights/shadows, cracked surfaces
      - Barnacle clusters on rocks
      - Seaweed tufts growing between rocks
      - Shells and small pebbles
      - Shadow at water-edge
    """
    W, H = bg_width, FLOOR_THICKNESS
    surf = pygame.Surface((W, H))

    # ── sand gradient ────────────────────────────────────────────────────────
    sand_top    = pygame.Color(195, 165,  90)
    sand_mid    = pygame.Color(145, 115,  55)
    sand_bottom = pygame.Color( 50,  38,  18)
    for y in range(H):
        t = y / (H - 1)
        c = sand_top.lerp(sand_mid, min(1.0, t / 0.4)) if t < 0.4 \
            else sand_mid.lerp(sand_bottom, (t - 0.4) / 0.6)
        pygame.draw.line(surf, c, (0, y), (W, y))

    # ── water-edge shadow ────────────────────────────────────────────────────
    shadow_layer = pygame.Surface((W, H), pygame.SRCALPHA)
    for y in range(18):
        a = int(200 * (1 - y / 18))
        shadow_layer.fill((0, 12, 35, a), (0, y, W, 1))
    surf.blit(shadow_layer, (0, 0))

    # ── sand ripple marks ────────────────────────────────────────────────────
    ripple_layer = pygame.Surface((W, H), pygame.SRCALPHA)
    for i in range(8):
        yb = 12 + i * (H // 9)
        for x in range(W):
            ry = yb + round(sin(x * 0.022 + i * 1.4) * 5)
            ripple_layer.fill((75, 55, 20, 100), (x, min(H-1, ry),   1, 2))
            ripple_layer.fill((225, 198, 118, 60), (x, max(0, ry-1), 1, 1))
    surf.blit(ripple_layer, (0, 0))

    # ── fine grain noise ─────────────────────────────────────────────────────
    grain_layer = pygame.Surface((W, H), pygame.SRCALPHA)
    for _ in range(W * H // 5):
        gx = randint(0, W - 1)
        gy = randint(0, H - 1)
        v, a = randint(-20, 20), randint(20, 65)
        grain_layer.set_at((gx, gy), (max(0,180+v), max(0,148+v), max(0,66+v), a))
    surf.blit(grain_layer, (0, 0))

    # ── rocks ────────────────────────────────────────────────────────────────
    # Pre-generate rock placements so barnacles/seaweed can reference them
    rock_list = []  # (cx, cy, rx, ry, angle_deg)
    num_rocks = randint(12, 18)
    for _ in range(num_rocks):
        rx_ = randint(18, 55)
        ry_ = randint(12, 32)
        cx  = randint(rx_, W - rx_)
        cy  = randint(4, H - ry_ - 4)
        ang = randint(-25, 25)
        rock_list.append((cx, cy, rx_, ry_, ang))

    rock_layer = pygame.Surface((W, H), pygame.SRCALPHA)
    for (cx, cy, rx_, ry_, ang) in rock_list:
        # Draw on a temp surface so we can rotate
        rw, rh = rx_ * 2 + 6, ry_ * 2 + 6
        tmp = pygame.Surface((rw, rh), pygame.SRCALPHA)
        tc, tr = rw // 2, rh // 2

        # Base rock body — dark grey-green stone
        shade = randint(55, 85)
        rock_col   = (shade,     shade - 8,  shade - 15, 255)
        shadow_col = (shade - 20, shade - 28, shade - 32, 255)
        hi_col     = (shade + 40, shade + 35, shade + 28, 200)

        pygame.draw.ellipse(tmp, rock_col,   (3,     4,     rx_*2,   ry_*2))
        # shadow underside
        pygame.draw.ellipse(tmp, shadow_col, (3,     tr,    rx_*2,   ry_),  0)
        pygame.draw.ellipse(tmp, rock_col,   (3,     4,     rx_*2,   ry_*2), 0)
        # highlight top-left
        hl_rect = (tc - rx_//2, tr - ry_//2, rx_ - 4, ry_ // 2)
        if hl_rect[2] > 0 and hl_rect[3] > 0:
            pygame.draw.ellipse(tmp, hi_col, hl_rect)
        # crack lines
        for _ in range(randint(1, 3)):
            cx0 = randint(tc - rx_//2, tc + rx_//2)
            cy0 = randint(tr - ry_//3, tr + ry_//3)
            pygame.draw.line(tmp, shadow_col,
                             (cx0, cy0),
                             (cx0 + randint(-12, 12), cy0 + randint(-8, 8)), 1)
        # dark outline
        pygame.draw.ellipse(tmp, (30, 25, 18, 200), (3, 4, rx_*2, ry_*2), 2)

        rotated = pygame.transform.rotate(tmp, ang)
        rock_layer.blit(rotated, rotated.get_frect(center=(cx, cy)))

    surf.blit(rock_layer, (0, 0))

    # ── barnacle clusters on rocks ────────────────────────────────────────────
    barnacle_layer = pygame.Surface((W, H), pygame.SRCALPHA)
    for (cx, cy, rx_, ry_, _) in rock_list:
        num_b = randint(3, 9)
        for _ in range(num_b):
            bx = cx + randint(-rx_ + 4, rx_ - 4)
            by = cy + randint(-ry_ // 2, ry_ // 2)
            br = randint(2, 5)
            pygame.draw.circle(barnacle_layer, (140, 130, 100, 220), (bx, by), br)
            pygame.draw.circle(barnacle_layer, (180, 168, 138, 150), (bx, by), br, 1)
            # tiny hole
            pygame.draw.circle(barnacle_layer, (40, 35, 25, 200), (bx, by), max(1, br - 2))
    surf.blit(barnacle_layer, (0, 0))

    # ── seaweed tufts between rocks ───────────────────────────────────────────
    weed_layer = pygame.Surface((W, H), pygame.SRCALPHA)
    for (cx, cy, rx_, ry_, _) in rock_list[::2]:  # every other rock
        wx = cx + randint(-rx_, rx_)
        wy = cy - ry_
        stalks = randint(2, 5)
        for s in range(stalks):
            sx = wx + s * 5 - stalks * 2
            stalk_h = randint(14, 30)
            weed_col = (30 + randint(0,20), 110 + randint(0,30), 40 + randint(0,20), 200)
            for seg in range(stalk_h // 4):
                sway = round(sin(seg * 0.7 + s * 1.2) * 3)
                sy1  = wy - seg * 4
                sy2  = wy - (seg + 1) * 4
                pygame.draw.line(weed_layer, weed_col,
                                 (sx + sway, min(H, sy1)),
                                 (sx + sway, min(H, sy2)), 2)
    surf.blit(weed_layer, (0, 0))

    # ── shells and small pebbles ──────────────────────────────────────────────
    detail_layer = pygame.Surface((W, H), pygame.SRCALPHA)
    for _ in range(80):
        ox = randint(0, W)
        oy = randint(6, H - 6)
        kind = randint(0, 2)
        if kind == 0:
            # small pebble
            rx2, ry2 = randint(3, 8), randint(2, 4)
            sh = randint(110, 170)
            pygame.draw.ellipse(detail_layer, (sh, sh-8, sh-18, 230),
                                (ox-rx2, oy-ry2, rx2*2, ry2*2))
            pygame.draw.ellipse(detail_layer, (sh+40, sh+32, sh+18, 120),
                                (ox-rx2, oy-ry2, rx2*2, ry2*2), 1)
        elif kind == 1:
            # shell arc
            r = randint(4, 9)
            pygame.draw.arc(detail_layer, (215, 195, 145, 210),
                            (ox-r, oy-r, r*2, r*2), 0.1, pi, 2)
            pygame.draw.arc(detail_layer, (175, 150, 105, 160),
                            (ox-r+2, oy-r+2, r, r), pi, 2*pi, 2)
        else:
            # stone chip
            pts = [(ox, oy),
                   (ox + randint(6,14), oy + randint(-3, 3)),
                   (ox + randint(4,10), oy + randint(4, 8))]
            pygame.draw.polygon(detail_layer, (195, 175, 118, 210), pts)
    surf.blit(detail_layer, (0, 0))

    return surf.convert()

floor_surf = _make_floor_surface()

# PLAY_BOUNDS — same as WORLD_BOUNDS but the bottom is the top of the floor
PLAY_BOUNDS = pygame.Rect(0, 0, bg_width, FLOOR_Y)

# jellyfish.png is tried at runtime; _build_jelly_frame is the live fallback
load_or_placeholder('images/jellyfish.png', make_jellyfish_surface)   # preload/log only
mapfrag_surf = scale_surface(load_or_placeholder('images/mapfrag1.png', make_mapfrag_surface), 1.0)

# ---------------------------------------------------------------------------
# Menu-specific art
#   menu_bg_surf  — top portion of web_back.png scaled to fill the window
#   menu_title_img — title.png scaled to a comfortable header size
# ---------------------------------------------------------------------------
def _load_menu_bg():
    try:
        raw = pygame.image.load('images/web_back.png').convert()
        # web_back.png is 862×1825 — crop just the top WINDOW_HEIGHT rows then
        # scale to the full window width so it fills the screen edge-to-edge.
        crop_h = min(raw.get_height(), round(raw.get_width() * WINDOW_HEIGHT / WINDOW_WIDTH))
        cropped = raw.subsurface((0, 0, raw.get_width(), crop_h))
        return pygame.transform.smoothscale(cropped, (WINDOW_WIDTH, WINDOW_HEIGHT))
    except (pygame.error, FileNotFoundError) as e:
        print(f"[art] couldn't load 'images/web_back.png' ({e}) - using game background instead.")
        return background_surf   # fallback to the game background

def _load_menu_title():
    try:
        raw = pygame.image.load('images/title.png').convert_alpha()
        # Scale up proportionally so the title is ~500px wide
        target_w = 500
        scale    = target_w / raw.get_width()
        return pygame.transform.smoothscale(
            raw, (target_w, max(1, round(raw.get_height() * scale))))
    except (pygame.error, FileNotFoundError) as e:
        print(f"[art] couldn't load 'images/title.png' ({e}) - using text fallback.")
        return None   # run_main_menu handles None gracefully

menu_bg_surf    = _load_menu_bg()
menu_title_img  = _load_menu_title()

# ---------------------------------------------------------------------------
# Wave definitions
#   count    = total sharks this wave
#   jellies  = total jellyfish this wave (0 for early waves)
#   interval = ms between shark spawns
# ---------------------------------------------------------------------------
WAVE_DATA = [
    # wave 0 – tutorial
    {"count": 1, "jellies": 0, "interval": 3000, "speed_mult": 0.55, "health_bonus": 0, "boss": False},
    # wave 1
    {"count": 3, "jellies": 0, "interval": 2200, "speed_mult": 0.75, "health_bonus": 0, "boss": False},
    # wave 2
    {"count": 5, "jellies": 0, "interval": 1800, "speed_mult": 1.0,  "health_bonus": 0, "boss": False},
    # wave 3 – first jellyfish appear
    {"count": 5, "jellies": 2, "interval": 1500, "speed_mult": 1.2,  "health_bonus": 1, "boss": False},
    # wave 4
    {"count": 6, "jellies": 4, "interval": 1300, "speed_mult": 1.4,  "health_bonus": 1, "boss": False},
    # wave 5 – boss + jellies
    {"count": 3, "jellies": 4, "interval": 1200, "speed_mult": 1.5,  "health_bonus": 1, "boss": True},
]

BETWEEN_WAVE_DELAY = 3.0

# ---------------------------------------------------------------------------
# Camera group
# ---------------------------------------------------------------------------
class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.offset = pygame.Vector2()

    def draw_background(self, target_pos):
        target_pos = pygame.Vector2(target_pos)
        desired_x = target_pos.x - WINDOW_WIDTH / 2
        desired_y = target_pos.y - WINDOW_HEIGHT / 2
        max_offset_x = max(bg_width - WINDOW_WIDTH, 0)
        max_offset_y = max(bg_height - WINDOW_HEIGHT, 0)
        self.offset.x = min(max(desired_x, 0), max_offset_x)
        self.offset.y = min(max(desired_y, 0), max_offset_y)
        display_surface.fill((0, 0, 0))
        display_surface.blit(background_surf, -self.offset)

    def draw_all(self, target_pos):
        self.draw_background(target_pos)
        # Draw the sea floor at the bottom of the world, scrolled with the camera
        floor_screen_y = FLOOR_Y - self.offset.y
        display_surface.blit(floor_surf, (int(-self.offset.x), int(floor_screen_y)))
        for sprite in self.sprites():
            offset_pos = pygame.Vector2(sprite.rect.topleft) - self.offset
            offset_pos.y += getattr(sprite, "bob_offset", 0)
            display_surface.blit(sprite.image, offset_pos)
            if isinstance(sprite, (Shark, Jellyfish)):
                self.draw_health_bar(sprite, offset_pos)

    def draw_health_bar(self, enemy, screen_pos):
        is_big  = isinstance(enemy, Shark) and enemy.is_boss
        bar_w   = enemy.rect.width * 0.8
        bar_h   = 8 if is_big else 6
        bar_x   = screen_pos.x + (enemy.rect.width - bar_w) / 2
        bar_y   = screen_pos.y - (bar_h + 10)
        ratio   = max(0.0, enemy.health / enemy.max_health)
        pygame.draw.rect(display_surface, (30, 30, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill_color = (90, 220, 120) if ratio > 0.6 else (250, 200, 60) if ratio > 0.3 else (220, 60, 60)
        pygame.draw.rect(display_surface, fill_color, (bar_x, bar_y, bar_w * ratio, bar_h), border_radius=3)
        pygame.draw.rect(display_surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=3)

# ---------------------------------------------------------------------------
# Player  (enhanced: smooth tail-fin swim cycle, recoil on gun)
# ---------------------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.base_surf   = player_surf          # original, un-flipped art
        self.normal_surf = player_surf
        self.image       = self.normal_surf
        self.rect        = self.image.get_frect(center=(WORLD_BOUNDS.centerx, WORLD_BOUNDS.centery))
        self.hitbox      = self.rect.inflate(-self.rect.width * 0.3, -self.rect.height * 0.35)
        self.mask        = pygame.mask.from_surface(self.image)
        self.direction   = pygame.Vector2()
        self.speed       = 500
        self.facing_right = False

        self.max_health = 3
        self.health     = self.max_health
        self.invincible_until    = 0
        self.invincible_duration = 1200
        self.alive = True

        # Oxygen system
        self.max_oxygen    = 100.0
        self.oxygen        = self.max_oxygen
        self.oxygen_drain  = 4.0    # points per second lost passively
        self.oxygen_empty  = False  # True once oxygen first hits 0

        self.can_shoot          = True
        self.harpoon_shoot_time = 0
        self.cooldown_duration  = 650

        # Bob (vertical float)
        self.bob_timer       = uniform(0, 10)
        self.bob_offset      = 0
        self.idle_bob_speed  = 2.5
        self.idle_bob_amount = 5
        self.swim_bob_speed  = 7
        self.swim_bob_amount = 8

        # Swim cycle – horizontal body-lean (tilt) expressed as a rotation angle
        self.swim_cycle      = uniform(0, 2 * pi)   # phase offset so fish don't sync
        self.swim_tilt       = 0.0                   # degrees, applied each frame

        # Recoil state
        self.recoil_offset    = 0.0    # pixels backward from gun direction
        self.recoil_direction = pygame.Vector2()
        self.recoil_timer     = 0.0
        self.recoil_duration  = 0.18   # seconds
        self.recoil_amount    = 14     # max pixel kick-back

        self.bubble_timer    = 0
        self.bubble_interval = 220

    @property
    def cooldown_progress(self):
        if self.can_shoot:
            return 1.0
        elapsed = pygame.time.get_ticks() - self.harpoon_shoot_time
        return max(0.0, min(1.0, elapsed / self.cooldown_duration))

    def harpoon_timer(self):
        if not self.can_shoot and pygame.time.get_ticks() - self.harpoon_shoot_time >= self.cooldown_duration:
            self.can_shoot = True

    # --- bob ---
    def update_bob(self, dt, moving):
        self.bob_timer += dt
        speed  = self.swim_bob_speed  if moving else self.idle_bob_speed
        amount = self.swim_bob_amount if moving else self.idle_bob_amount
        self.bob_offset = sin(self.bob_timer * speed) * amount

    # --- swim body tilt ---
    def update_swim_tilt(self, dt, moving):
        if moving:
            self.swim_cycle += dt * 5.5           # speed of tail stroke
        else:
            self.swim_cycle += dt * 2.0
        tilt_amount = 7 if moving else 3          # degrees of rock
        self.swim_tilt = sin(self.swim_cycle) * tilt_amount

    # --- recoil ---
    def fire_recoil(self, shot_direction):
        """Call this immediately when a harpoon is fired."""
        self.recoil_direction = -shot_direction   # kick opposite to shot
        self.recoil_timer     = self.recoil_duration

    def update_recoil(self, dt):
        if self.recoil_timer > 0:
            self.recoil_timer = max(0.0, self.recoil_timer - dt)
            # smooth spring-back curve: ease-out
            progress = self.recoil_timer / self.recoil_duration
            self.recoil_offset = progress * self.recoil_amount
        else:
            self.recoil_offset = 0.0

    def spawn_trail_bubbles(self, moving):
        if not moving:
            return
        now = pygame.time.get_ticks()
        if now - self.bubble_timer >= self.bubble_interval:
            self.bubble_timer = now
            offset_x = (-self.rect.width if self.facing_right else self.rect.width) * 0.28
            spawn_pos = self.rect.center + pygame.Vector2(offset_x, -self.rect.height * 0.2)
            Bubble(spawn_pos, (all_sprites, bubble_sprites), small=True)

    def take_damage(self):
        now = pygame.time.get_ticks()
        if now < self.invincible_until:
            return
        self.health -= 1
        self.invincible_until = now + self.invincible_duration
        if self.health <= 0:
            self.alive = False
            SFX_PLAYER_DIE.play()
        else:
            SFX_PLAYER_DAMAGE.play()

    def is_invincible(self):
        return pygame.time.get_ticks() < self.invincible_until

    def update(self, dt):
        if not self.alive:
            return

        # Oxygen drain
        self.oxygen = max(0.0, self.oxygen - self.oxygen_drain * dt)
        if self.oxygen <= 0 and not self.oxygen_empty:
            self.oxygen_empty = True
            self.take_damage()   # lose a life when oxygen runs out
        elif self.oxygen > 0:
            self.oxygen_empty = False   # allow damage again next time it hits 0

        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_DOWN]  or keys[pygame.K_s]) - int(keys[pygame.K_UP]   or keys[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction
        moving = self.direction.length() > 0

        self.update_recoil(dt)

        # apply recoil offset as a positional nudge (cosmetic only)
        recoil_vec = self.recoil_direction * self.recoil_offset if self.recoil_timer > 0 else pygame.Vector2()
        self.rect.center += self.direction * self.speed * dt + recoil_vec
        self.rect.clamp_ip(PLAY_BOUNDS)
        old_center = self.rect.center

        # pick base surface (flip for facing direction)
        if self.direction.x > 0:
            self.facing_right = True
            base = pygame.transform.flip(self.base_surf, True, False)
        elif self.direction.x < 0:
            self.facing_right = False
            base = self.base_surf
        else:
            base = pygame.transform.flip(self.base_surf, True, False) if self.facing_right else self.base_surf

        # apply swim tilt rotation on top
        self.update_swim_tilt(dt, moving)
        self.image = pygame.transform.rotate(base, self.swim_tilt)

        self.rect = self.image.get_frect(center=old_center)
        self.hitbox.center = self.rect.center

        self.harpoon_timer()
        self.update_bob(dt, moving)
        self.spawn_trail_bubbles(moving)

        if self.is_invincible():
            self.image.set_alpha(120 if (pygame.time.get_ticks() // 100) % 2 == 0 else 255)
        else:
            self.image.set_alpha(255)

        recent_mouse = pygame.mouse.get_just_pressed()
        if recent_mouse[0] and self.can_shoot:
            # Gun tip is at raw pixel (22,34) in the 100x100 source art,
            # which is dx=-28, dy=-16 from centre. After PLAYER_SCALE 1.5x: dx=-42, dy=-24.
            # When facing_right the image is flipped so dx becomes +42.
            gun_x = 42 * (1 if self.facing_right else -1)
            gun_y = -24
            start_pos = self.rect.center + pygame.Vector2(gun_x, gun_y)
            mouse_world_pos = pygame.Vector2(pygame.mouse.get_pos()) + all_sprites.offset
            direction = mouse_world_pos - start_pos
            if direction:
                direction = direction.normalize()
                Harpoon(harpoon_surf, start_pos, direction, (all_sprites, harpoon_sprites))
                SFX_HARPOON_SHOOT.play()
                self.can_shoot = False
                self.harpoon_shoot_time = pygame.time.get_ticks()
                self.fire_recoil(direction)
                # Muzzle burst — spray of bubbles at the gun tip
                for _ in range(randint(6, 10)):
                    perp = pygame.Vector2(-direction.y, direction.x)
                    spread = perp * uniform(-12, 12) + direction * uniform(0, 18)
                    TrailBubble(pygame.Vector2(start_pos) + spread,
                                (all_sprites, bubble_sprites), burst=True)


# ---------------------------------------------------------------------------
# Harpoon projectile
# ---------------------------------------------------------------------------
class Harpoon(pygame.sprite.Sprite):
    TRAIL_INTERVAL = 0.04   # seconds between each trail bubble

    def __init__(self, surf, pos, direction, groups):
        super().__init__(groups)
        self.direction = direction
        angle = self.direction.angle_to(pygame.Vector2(-1, 0))
        self.image = pygame.transform.rotate(surf, angle)
        self.rect  = self.image.get_frect(center=pos)
        self._trail_timer = 0.0

    def update(self, dt):
        self.rect.center += self.direction * 500 * dt

        # Spawn a small trail bubble periodically behind the harpoon tip
        self._trail_timer += dt
        if self._trail_timer >= self.TRAIL_INTERVAL:
            self._trail_timer = 0.0
            # Slight perpendicular jitter so the trail isn't a perfectly straight line
            perp = pygame.Vector2(-self.direction.y, self.direction.x)
            jitter = perp * uniform(-4, 4)
            spawn = pygame.Vector2(self.rect.center) - self.direction * 8 + jitter
            TrailBubble(spawn, (all_sprites, bubble_sprites))

        if pygame.Vector2(self.rect.center).distance_to(player.rect.center) > \
                pygame.Vector2(WINDOW_WIDTH, WINDOW_HEIGHT).length():
            self.kill()


# ---------------------------------------------------------------------------
# TrailBubble — tiny, fast, short-lived; used for harpoon trail & muzzle burst
# ---------------------------------------------------------------------------
class TrailBubble(pygame.sprite.Sprite):
    def __init__(self, pos, groups, burst=False):
        super().__init__(groups)
        # Burst bubbles are a bit bigger and spread wider
        self.radius = randint(3, 6) if burst else randint(2, 4)
        size = self.radius * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (180, 220, 255, 160), (self.radius, self.radius), self.radius)
        pygame.draw.circle(self.image, (255, 255, 255, 200), (self.radius, self.radius), self.radius, 1)
        self.pos  = pygame.Vector2(pos)
        self.rect = self.image.get_frect(center=self.pos)
        # Rise faster and live shorter than ambient bubbles
        self.rise_speed  = uniform(80, 180) if burst else uniform(60, 130)
        self.sway_amount = uniform(8, 20)  if burst else uniform(4, 10)
        self.sway_speed  = uniform(3, 6)
        self.age      = 0.0
        self.lifetime = uniform(0.4, 0.9) if burst else uniform(0.3, 0.65)

    def update(self, dt):
        self.age   += dt
        self.pos.y -= self.rise_speed * dt
        self.pos.x += sin(self.age * self.sway_speed) * self.sway_amount * dt
        self.rect.center = self.pos
        if self.age >= self.lifetime:
            self.kill()


# ---------------------------------------------------------------------------
# Shark — sprite-sheet state machine  (normal + boss)
#
# Normal shark states:  SWIM → ATTACK → SWIM …
# Boss states:          SWIM → ATTACK → SWIM  (+ periodic CHARGE and SUMMON)
#
# Boss extra mechanics
#   CHARGE  – winds up then rockets across the screen; deals damage on contact
#   SUMMON  – pauses and spawns 2-3 mini-sharks around itself
# ---------------------------------------------------------------------------
class Shark(pygame.sprite.Sprite):
    # ── normal attack tuning ──
    SWIM_FPS        = 8
    ATTACK_FPS      = 10
    ATTACK_RANGE    = 160
    ATTACK_COOLDOWN = 1.8
    LUNGE_SPEED     = 420
    BITE_FRAME      = 2        # frame index where bite damage is dealt

    # ── boss-only tuning ──
    CHARGE_COOLDOWN  = 4.0     # seconds between charge sequences
    CHARGE_WINDUP    = 0.45    # seconds of wind-up telegraph
    CHARGE_SPEED     = 1000     # px/s during each dash
    CHARGE_DASH_DUR  = 0.6    # seconds each individual dash lasts
    CHARGE_PAUSE_DUR = 0.18    # brief pause between back-and-forth dashes
    CHARGE_PASSES    = 2       # how many back-and-forth passes per sequence
    SUMMON_COOLDOWN  = 5.0
    SUMMON_COUNT     = 3

    STATE_SWIM   = "swim"
    STATE_ATTACK = "attack"
    STATE_CHARGE = "charge"    # boss only
    STATE_SUMMON = "summon"    # boss only

    def __init__(self, pos, groups, is_boss=False, speed_mult=1.0,
                 health_bonus=0, is_minion=False):
        super().__init__(groups)
        self.is_boss   = is_boss
        self.is_minion = is_minion

        self.swim_frames   = BOSS_SWIM_FRAMES   if is_boss else SHARK_SWIM_FRAMES
        self.attack_frames = BOSS_ATTACK_FRAMES if is_boss else SHARK_ATTACK_FRAMES

        self.pos = pygame.Vector2(pos)

        if is_boss:
            self.speed      = uniform(70, 100) * speed_mult
            self.max_health = 10 + health_bonus * 3
        elif is_minion:
            self.speed      = uniform(130, 190) * speed_mult
            self.max_health = 1
        else:
            self.speed      = uniform(90, 160) * speed_mult
            self.max_health = 2 + health_bonus
        self.health = self.max_health

        # ── animation ──
        self.state       = self.STATE_SWIM
        self.frame_idx   = 0
        self.frame_timer = 0.0

        # ── normal attack ──
        self.attack_cooldown  = 0.0
        self._bit_this_attack = False

        # ── boss: charge ──
        self._charge_cd      = uniform(2.0, self.CHARGE_COOLDOWN)
        self._charge_phase   = "idle"   # idle → windup → dash → pause → dash → … → done
        self._charge_timer   = 0.0
        self._charge_dir     = pygame.Vector2(1, 0)   # locked-in direction per dash
        self._charge_hit     = False
        self._charge_passes  = 0        # dashes completed so far
        self._charge_forward = True     # True = toward player, False = back

        # ── boss: summon ──
        self._summon_cd      = uniform(6.0, self.SUMMON_COOLDOWN)

        # ── movement ──
        self.wobble_timer  = uniform(0, 10)
        self.wobble_amount = uniform(20, 45)
        self.facing_right  = True

        # ── visual ──
        self.bob_offset = 0.0
        self.bob_timer  = uniform(0, 10)

        self.image = self.swim_frames[0]
        self.rect  = self.image.get_frect(center=self.pos)

    # ── helpers ──────────────────────────────────────────────────────────────
    def _fps(self):
        return self.ATTACK_FPS if self.state == self.STATE_ATTACK else self.SWIM_FPS

    def _frames(self):
        return self.attack_frames if self.state == self.STATE_ATTACK else self.swim_frames

    def _get_frame(self):
        raw = self._frames()[self.frame_idx % len(self._frames())]
        return raw if self.facing_right else pygame.transform.flip(raw, True, False)

    def _advance_frame(self, dt):
        """Returns True when an ATTACK sequence finishes its last frame."""
        self.frame_timer += dt
        if self.frame_timer >= 1.0 / self._fps():
            self.frame_timer -= 1.0 / self._fps()
            self.frame_idx   += 1
            total = len(self._frames())
            if self.frame_idx >= total:
                if self.state == self.STATE_ATTACK:
                    self.frame_idx = 0
                    return True
                self.frame_idx = self.frame_idx % total
        return False

    def _facing_toward(self, vec):
        if vec.x > 0:   self.facing_right = True
        elif vec.x < 0: self.facing_right = False

    # ── update ───────────────────────────────────────────────────────────────
    def update(self, dt):
        self.wobble_timer += dt
        self.bob_timer    += dt

        to_player = pygame.Vector2(player.rect.center) - self.pos
        dist      = to_player.length()
        forward   = to_player.normalize() if dist > 0 else pygame.Vector2(1, 0)
        self._facing_toward(forward)

        # ── tick cooldowns ────────────────────────────────────────────────────
        if self.attack_cooldown > 0:
            self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        # ── boss ability cooldowns ────────────────────────────────────────────
        if self.is_boss and self.state == self.STATE_SWIM:
            self._charge_cd -= dt
            self._summon_cd -= dt

            if self._summon_cd <= 0:
                self._summon_cd = self.SUMMON_COOLDOWN
                self._begin_summon()

            elif self._charge_cd <= 0:
                self._charge_cd      = self.CHARGE_COOLDOWN
                self._charge_phase   = "windup"
                self._charge_timer   = 0.0
                self._charge_dir     = forward.copy()   # locked toward player at trigger
                self._charge_hit     = False
                self._charge_passes  = 0
                self._charge_forward = True
                self.state = self.STATE_CHARGE

        # ── state machine ─────────────────────────────────────────────────────
        if self.state == self.STATE_SWIM:
            # trigger normal attack when close
            if dist < self.ATTACK_RANGE and self.attack_cooldown <= 0:
                self.state            = self.STATE_ATTACK
                self.frame_idx        = 0
                self.frame_timer      = 0.0
                self._bit_this_attack = False
            else:
                # swim toward player with wobble
                perp   = pygame.Vector2(-forward.y, forward.x)
                wobble = sin(self.wobble_timer * 2.2) * self.wobble_amount
                self.pos += forward * self.speed * dt + perp * wobble * dt

        elif self.state == self.STATE_ATTACK:
            # lunge frame moves fast, other frames drift
            move_speed = self.LUNGE_SPEED if self.frame_idx == 1 else self.speed * 0.25
            self.pos += forward * move_speed * dt

            # bite damage on bite frame (once per attack)
            if (self.frame_idx == self.BITE_FRAME and not self._bit_this_attack
                    and player.alive and not player.is_invincible()
                    and self.rect.colliderect(player.hitbox)):
                player.take_damage()
                self._bit_this_attack = True
                SFX_SHARK_ATTACK.play()

            if self._advance_frame(dt):
                self.state           = self.STATE_SWIM
                self.attack_cooldown = self.ATTACK_COOLDOWN
                self.frame_idx       = 0

        elif self.state == self.STATE_CHARGE:
            self._charge_timer += dt

            if self._charge_phase == "windup":
                # telegraph: slow drift, tilt back slightly
                self.pos += forward * (self.speed * 0.1) * dt
                if self._charge_timer >= self.CHARGE_WINDUP:
                    self._charge_phase  = "dash"
                    self._charge_timer  = 0.0
                    self._charge_hit    = False
                    # first dash is toward the player
                    self._charge_dir    = forward.copy()
                    self._charge_forward = True

            elif self._charge_phase == "dash":
                # rocket in the locked direction
                self.pos += self._charge_dir * self.CHARGE_SPEED * dt

                # deal damage once per dash
                if not self._charge_hit and player.alive and not player.is_invincible():
                    self.rect = self.image.get_frect(center=self.pos)
                    if self.rect.colliderect(player.hitbox):
                        player.take_damage()
                        self._charge_hit = True
                        SFX_SHARK_ATTACK.play()

                if self._charge_timer >= self.CHARGE_DASH_DUR:
                    self._charge_timer   = 0.0
                    self._charge_passes += 1
                    if self._charge_passes >= self.CHARGE_PASSES * 2:
                        # all dashes done
                        self._charge_phase = "idle"
                        self.state         = self.STATE_SWIM
                    else:
                        # pause before reversing
                        self._charge_phase = "pause"

            elif self._charge_phase == "pause":
                # brief stop between dashes
                if self._charge_timer >= self.CHARGE_PAUSE_DUR:
                    self._charge_timer   = 0.0
                    self._charge_hit     = False
                    # flip direction: odd passes go back, even go forward again
                    self._charge_forward = not self._charge_forward
                    if self._charge_forward:
                        # re-aim at current player position for the next forward dash
                        tp = pygame.Vector2(player.rect.center) - self.pos
                        self._charge_dir = tp.normalize() if tp.length() > 0 else self._charge_dir
                    else:
                        self._charge_dir = -self._charge_dir   # reverse
                    self._charge_phase = "dash"

        elif self.state == self.STATE_SUMMON:
            # pause in place; summoning is instant, state returns to swim
            self.state = self.STATE_SWIM

        # ── clamp + apply frame ───────────────────────────────────────────────
        self.pos.x = min(max(self.pos.x, PLAY_BOUNDS.left),  PLAY_BOUNDS.right)
        self.pos.y = min(max(self.pos.y, PLAY_BOUNDS.top),   PLAY_BOUNDS.bottom)

        self.bob_offset = sin(self.bob_timer * 2.8) * 4

        # Advance swim-state animation continuously
        if self.state not in (self.STATE_ATTACK,):
            self._advance_frame(dt)

        self.image = self._get_frame()
        self.rect  = self.image.get_frect(center=self.pos)

    def _begin_summon(self):
        """Spawn minion sharks around the boss."""
        self.state = self.STATE_SUMMON
        cfg = wave_config()
        for i in range(self.SUMMON_COUNT):
            angle  = (2 * pi / self.SUMMON_COUNT) * i
            offset = pygame.Vector2(cos(angle), sin(angle)) * 120
            spawn  = self.pos + offset
            spawn.x = min(max(spawn.x, PLAY_BOUNDS.left + 30),  PLAY_BOUNDS.right  - 30)
            spawn.y = min(max(spawn.y, PLAY_BOUNDS.top  + 30),  PLAY_BOUNDS.bottom - 30)
            Shark(spawn, (all_sprites, shark_sprites),
                  is_boss=False, is_minion=True,
                  speed_mult=cfg["speed_mult"],
                  health_bonus=0)
        # Flash the boss tint yellow briefly to signal summon
        self._summon_flash = 0.3

    def hit(self):
        self.health -= 1
        if self.is_boss and self.health <= 0:
            SFX_BOSS_DIE.play()
            self.kill()
            return True
        if self.health <= 0 and self.is_boss == False:
            for _ in range(6):
                Bubble(self.rect.center, (all_sprites, bubble_sprites), small=True)
            SFX_SHARK_DIE.play()
            self.kill()
            return True
        return False


# ---------------------------------------------------------------------------
# Map fragment (dropped by boss) — uses mapfrag1.png if available
# ---------------------------------------------------------------------------
class MapFragment(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.image       = mapfrag_surf.copy()
        self.pos         = pygame.Vector2(pos)
        self.rect        = self.image.get_frect(center=self.pos)
        self.spawn_timer = uniform(0, 10)

    def update(self, dt):
        self.spawn_timer += dt
        self.bob_offset   = sin(self.spawn_timer * 3) * 6


# ---------------------------------------------------------------------------
# Bubble
# ---------------------------------------------------------------------------
class Bubble(pygame.sprite.Sprite):
    def __init__(self, pos, groups, small=False):
        super().__init__(groups)
        self.radius = randint(2, 4) if small else randint(4, 10)
        size = self.radius * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (200, 230, 255, 130), (self.radius, self.radius), self.radius)
        pygame.draw.circle(self.image, (255, 255, 255, 180), (self.radius, self.radius), self.radius, 1)
        self.pos  = pygame.Vector2(pos)
        self.rect = self.image.get_frect(center=self.pos)
        self.rise_speed  = uniform(40, 110)
        self.sway_amount = uniform(4, 14)
        self.sway_speed  = uniform(1.5, 3.5)
        self.age      = 0
        self.lifetime = uniform(2.5, 5)

    def update(self, dt):
        self.age   += dt
        self.pos.y -= self.rise_speed * dt
        self.pos.x += sin(self.age * self.sway_speed) * self.sway_amount * dt
        self.rect.center = self.pos
        if self.age >= self.lifetime:
            self.kill()


# ---------------------------------------------------------------------------
# HealthBubble — collectible that restores 1 HP (capped at max_health)
# ---------------------------------------------------------------------------
class HealthBubble(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self._build_image()
        self.pos      = pygame.Vector2(pos)
        self.rect     = self.image.get_frect(center=self.pos)
        self._timer   = 0.0
        self._pulse   = uniform(0, 2 * pi)   # phase offset for glow pulse
        self.bob_offset = 0.0

    def _build_image(self, pulse=0.0):
        R = 18
        size = R * 2 + 6
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2

        # outer glow ring (pulses)
        glow_a = int(60 + 40 * sin(pulse))
        pygame.draw.circle(surf, (80, 220, 120, glow_a), (cx, cy), R + 3)

        # main bubble body — green tinted
        pygame.draw.circle(surf, (60, 200, 100, 210), (cx, cy), R)
        # inner bright highlight
        pygame.draw.circle(surf, (160, 255, 180, 130), (cx - R//3, cy - R//3), R // 3)
        # white rim
        pygame.draw.circle(surf, (200, 255, 215, 160), (cx, cy), R, 2)

        # red cross / plus symbol in the centre
        cw = 3   # cross arm width
        cl = 8   # cross arm half-length
        pygame.draw.rect(surf, (220, 40, 40, 230), (cx - cw, cy - cl, cw*2, cl*2))
        pygame.draw.rect(surf, (220, 40, 40, 230), (cx - cl, cy - cw, cl*2, cw*2))

        self.image = surf

    def update(self, dt):
        self._timer += dt
        self._pulse += dt * 3.0
        self._build_image(self._pulse)
        self.bob_offset = sin(self._timer * 2.5) * 6
        self.rect.center = self.pos

        # Despawn after 15 seconds if not collected
        if self._timer > 15.0:
            self.kill()


# ---------------------------------------------------------------------------
# OxygenTankPickup — uses OxygenTank from oxygentank.py for bob/visual logic,
# wrapped in a Sprite so it works with CameraGroup and the free-roam world.
# ---------------------------------------------------------------------------
def _make_o2_surface():
    """Fallback surface if o2 tank.png is missing."""
    s = pygame.Surface((48, 48), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (60, 180, 220), (8, 4, 32, 42))
    pygame.draw.ellipse(s, (100, 220, 255), (8, 4, 32, 42), 2)
    pygame.draw.rect(s, (180, 180, 200), (18, 0, 12, 6), border_radius=3)
    ts = pygame.font.SysFont("arial", 14, bold=True).render("O2", True, (255,255,255))
    s.blit(ts, ts.get_rect(center=(24, 24)))
    return s

try:
    _o2_raw = pygame.image.load('images/o2 tank.png').convert_alpha()
    _o2_img = pygame.transform.smoothscale(_o2_raw, (52, 52))
except (pygame.error, FileNotFoundError):
    _o2_img = _make_o2_surface()


class OxygenTankPickup(pygame.sprite.Sprite):
    """
    Collectible oxygen tank.  Reuses OxygenTank for the bob animation;
    lives in world-space as a normal Sprite so CameraGroup can draw it.
    """
    REFILL = 60          # oxygen points restored on pickup
    LIFETIME = 18.0      # seconds before it despawns

    def __init__(self, pos, groups):
        super().__init__(groups)
        # OxygenTank handles bob + collision, we feed it screen coords;
        # CameraGroup translates world→screen, so we pass world pos here.
        self._tank    = OxygenTank(pos[0], pos[1], _o2_img.copy(), self.REFILL)
        self.image    = _o2_img
        self.pos      = pygame.Vector2(pos)
        self.rect     = self.image.get_frect(center=self.pos)
        self._age     = 0.0
        self.bob_offset = 0.0

    def update(self, dt):
        self._age += dt
        if self._age >= self.LIFETIME:
            self.kill()
            return
        # Bob using OxygenTank constants
        import math
        now = pygame.time.get_ticks()
        self.bob_offset = (math.sin(now * OxygenTank.BOB_SPEED +
                                    self._tank.time_offset) * OxygenTank.BOB_AMPLITUDE)
        self.rect.center = self.pos
        


# ---------------------------------------------------------------------------
# ElectricBolt — jellyfish projectile
# ---------------------------------------------------------------------------
class ElectricBolt(pygame.sprite.Sprite):
    SPEED = 280

    def __init__(self, pos, direction, groups):
        super().__init__(groups)
        self.direction  = direction
        self._age       = 0.0
        self._lifetime  = 3.5   # seconds before despawning
        self._zap_timer = 0.0   # for animated zigzag redraw

        # Build bolt surface (zigzag lightning bolt shape)
        self._base_color = (180, 100, 255)
        self._glow_color = (220, 180, 255)
        self.image = self._make_bolt_surf(0)
        self.rect  = self.image.get_frect(center=pos)
        self.pos   = pygame.Vector2(pos)

        # Rotate to face direction
        angle = self.direction.angle_to(pygame.Vector2(1, 0))
        self.image = pygame.transform.rotate(self.image, angle)
        self.rect  = self.image.get_frect(center=pos)

    def _make_bolt_surf(self, phase):
        """Draw a small zigzag lightning bolt; phase shifts the zags for animation."""
        w, h = 28, 10
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        # Glow halo
        pygame.draw.line(surf, (*self._glow_color, 60), (0, h//2), (w, h//2), 5)
        # Zigzag core
        pts = []
        segs = 5
        for i in range(segs + 1):
            x = round(i * w / segs)
            y = h // 2 + (4 if (i + phase) % 2 == 0 else -4)
            pts.append((x, y))
        if len(pts) >= 2:
            pygame.draw.lines(surf, self._base_color, False, pts, 2)
            pygame.draw.lines(surf, (255, 230, 255), False, pts, 1)
        return surf

    def update(self, dt):
        self._age       += dt
        self._zap_timer += dt

        self.pos += self.direction * self.SPEED * dt
        self.rect.center = self.pos

        # Flicker the bolt every 0.06 s for an electric look
        if self._zap_timer >= 0.06:
            self._zap_timer = 0.0
            phase = randint(0, 1)
            base  = self._make_bolt_surf(phase)
            angle = self.direction.angle_to(pygame.Vector2(1, 0))
            self.image = pygame.transform.rotate(base, angle)
            self.rect  = self.image.get_frect(center=self.pos)

        if self._age >= self._lifetime:
            self.kill()
            return
        if pygame.Vector2(self.rect.center).distance_to(player.rect.center) > \
                pygame.Vector2(WINDOW_WIDTH, WINDOW_HEIGHT).length():
            self.kill()


# ---------------------------------------------------------------------------
# Jellyfish enemy — floats, pulses its bell, and periodically fires bolts
# ---------------------------------------------------------------------------
class Jellyfish(pygame.sprite.Sprite):
    SHOOT_INTERVAL_MIN = 2.2
    SHOOT_INTERVAL_MAX = 4.0
    # How often we rebuild the frame surface (seconds) — keeps CPU reasonable
    FRAME_INTERVAL    = 0.05

    def __init__(self, pos, groups, speed_mult=1.0):
        super().__init__(groups)
        self.pos        = pygame.Vector2(pos)
        self.max_health = 1
        self.health     = self.max_health
        self.speed      = uniform(45, 75) * speed_mult

        # Bell pulse — drives both the squish animation AND tentacle sway
        self._pulse_timer  = uniform(0, 2 * pi)
        self._pulse_speed  = uniform(1.8, 3.0)      # slower = more majestic

        # Gentle drift
        self._drift_timer  = uniform(0, 10)
        self._drift_amount = uniform(15, 35)

        # Shooting
        self._shoot_timer = uniform(0, self.SHOOT_INTERVAL_MAX)
        self._next_shot   = uniform(self.SHOOT_INTERVAL_MIN, self.SHOOT_INTERVAL_MAX)

        # Frame rebuild throttle
        self._frame_timer = 0.0

        self.bob_offset = 0.0
        self._bob_timer = uniform(0, 10)

        # Build first frame
        self._rebuild_frame()

    def _rebuild_frame(self):
        """Regenerate the bell+tentacle surface from the current pulse phase."""
        # pulse goes 0→1→0 smoothly using sin
        raw_pulse  = (sin(self._pulse_timer) + 1) / 2   # 0..1
        self.image = _build_jelly_frame(raw_pulse)
        self.rect  = self.image.get_frect(center=self.pos)

    def update(self, dt):
        self._pulse_timer += dt * self._pulse_speed
        self._drift_timer += dt
        self._bob_timer   += dt

        # Drift toward player
        to_player = pygame.Vector2(player.rect.center) - self.pos
        forward   = to_player.normalize() if to_player.length() > 0 else pygame.Vector2(0, 1)
        perp      = pygame.Vector2(-forward.y, forward.x)
        drift     = sin(self._drift_timer * 1.4) * self._drift_amount
        self.pos += (forward * self.speed + perp * drift) * dt
        self.pos  = pygame.Vector2(
            min(max(self.pos.x, WORLD_BOUNDS.left), WORLD_BOUNDS.right),
            min(max(self.pos.y, WORLD_BOUNDS.top), FLOOR_Y),
        )

        # Rebuild animated frame at throttled rate
        self._frame_timer += dt
        if self._frame_timer >= self.FRAME_INTERVAL:
            self._frame_timer = 0.0
            self._rebuild_frame()
        else:
            self.rect.center = self.pos

        self.bob_offset = sin(self._bob_timer * 2.2) * 5

        # Shoot
        self._shoot_timer += dt
        if self._shoot_timer >= self._next_shot:
            self._shoot_timer = 0.0
            self._next_shot   = uniform(self.SHOOT_INTERVAL_MIN, self.SHOOT_INTERVAL_MAX)
            direction = to_player.normalize() if to_player.length() > 0 else pygame.Vector2(0, 1)
            ElectricBolt(pygame.Vector2(self.rect.center), direction,
                         (all_sprites, bolt_sprites))
            SFX_JELLY_ATTACK.play()

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            # Discharge sparks on death
            for _ in range(4):
                Bubble(self.rect.center, (all_sprites, bubble_sprites), small=True)
            SFX_JELLY_DIE.play()
            self.kill()
            return True
        return False
class TutorialOverlay:
    """Draws a semi-transparent HUD explaining the controls during wave 0."""
    HINTS = [
        ("Move",  "Arrow Keys  /  WASD"),
        ("Shoot", "Left Click  (aim with mouse)"),
    ]
    DISMISS_TEXT = "Press  SPACE  or  kill the shark  to continue"

    def __init__(self):
        self.visible      = True
        self._pulse_timer = 0.0

    def update(self, dt):
        self._pulse_timer += dt

    def draw(self):
        if not self.visible:
            return

        panel_w, panel_h = 500, 190
        panel_x = (WINDOW_WIDTH - panel_w) // 2
        panel_y = WINDOW_HEIGHT - panel_h - 30

        # semi-transparent panel
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((10, 20, 50, 195))
        pygame.draw.rect(panel, (80, 180, 255, 200), (0, 0, panel_w, panel_h), 2, border_radius=10)
        display_surface.blit(panel, (panel_x, panel_y))

        # title
        title_surf = title_font.render("TUTORIAL", True, (120, 210, 255))
        display_surface.blit(title_surf, title_surf.get_frect(midtop=(WINDOW_WIDTH // 2, panel_y + 10)))

        # hints
        for i, (action, keys) in enumerate(self.HINTS):
            y = panel_y + 65 + i * 38
            action_surf = font.render(action + ":", True, (200, 230, 255))
            keys_surf   = font.render(keys,       True, (255, 255, 200))
            display_surface.blit(action_surf, (panel_x + 30,  y))
            display_surface.blit(keys_surf,   (panel_x + 165, y))

        # pulsing dismiss prompt
        alpha = int(180 + 75 * sin(self._pulse_timer * 3))
        dismiss_surf = small_font.render(self.DISMISS_TEXT, True, (180, 220, 180))
        dismiss_surf.set_alpha(alpha)
        display_surface.blit(dismiss_surf, dismiss_surf.get_frect(midbottom=(WINDOW_WIDTH // 2, panel_y + panel_h - 8)))


# ---------------------------------------------------------------------------
# Sprite groups
# ---------------------------------------------------------------------------
all_sprites       = CameraGroup()
harpoon_sprites   = pygame.sprite.Group()
shark_sprites     = pygame.sprite.Group()
jellyfish_sprites = pygame.sprite.Group()
bolt_sprites      = pygame.sprite.Group()
bubble_sprites    = pygame.sprite.Group()
fragment_sprites  = pygame.sprite.Group()
healthbubble_sprites = pygame.sprite.Group()
oxygentank_sprites   = pygame.sprite.Group()

player = Player(all_sprites)

# ---------------------------------------------------------------------------
# Wave state
# ---------------------------------------------------------------------------
current_wave             = 0
sharks_spawned_this_wave = 0
jellies_spawned_this_wave = 0
wave_kills               = 0      # total enemies killed this wave
wave_ending              = False
boss_spawned             = False
boss_announce_timer      = 0.0    # counts down after boss spawns for the name flash
level_complete           = False
between_wave_timer       = 0.0
wave_announce_timer      = 0.0

tutorial_overlay = TutorialOverlay()

AMBIENT_BUBBLE_EVENT   = pygame.USEREVENT + 1
SHARK_SPAWN_EVENT      = pygame.USEREVENT + 2
HEALTH_BUBBLE_EVENT    = pygame.USEREVENT + 3
OXYGEN_TANK_EVENT      = pygame.USEREVENT + 4
pygame.time.set_timer(AMBIENT_BUBBLE_EVENT, 250)
pygame.time.set_timer(HEALTH_BUBBLE_EVENT, 20_000)
pygame.time.set_timer(OXYGEN_TANK_EVENT,   15_000)  # one oxygen tank every 15 s


def wave_config():
    return WAVE_DATA[min(current_wave, len(WAVE_DATA) - 1)]


def start_wave(wave_idx):
    global current_wave, sharks_spawned_this_wave, jellies_spawned_this_wave
    global wave_kills, wave_ending, boss_spawned, wave_announce_timer, boss_announce_timer
    current_wave              = wave_idx
    sharks_spawned_this_wave  = 0
    jellies_spawned_this_wave = 0
    wave_kills                = 0
    wave_ending               = False
    boss_spawned              = False
    boss_announce_timer       = 0.0
    wave_announce_timer       = 2.5
    cfg = wave_config()
    pygame.time.set_timer(SHARK_SPAWN_EVENT, cfg["interval"])


def spawn_shark(is_boss=False):
    global sharks_spawned_this_wave
    cfg    = wave_config()
    margin = 60
    for _ in range(10):
        x = randint(WORLD_BOUNDS.left + margin, WORLD_BOUNDS.right - margin)
        y = randint(WORLD_BOUNDS.top  + margin, FLOOR_Y - margin)
        if pygame.Vector2(x, y).distance_to(player.rect.center) > 300:
            Shark((x, y), (all_sprites, shark_sprites),
                  is_boss=is_boss,
                  speed_mult=cfg["speed_mult"],
                  health_bonus=cfg["health_bonus"])
            sharks_spawned_this_wave += 1
            return
    x = randint(WORLD_BOUNDS.left + margin, WORLD_BOUNDS.right - margin)
    y = randint(WORLD_BOUNDS.top  + margin, FLOOR_Y - margin)
    Shark((x, y), (all_sprites, shark_sprites),
          is_boss=is_boss,
          speed_mult=cfg["speed_mult"],
          health_bonus=cfg["health_bonus"])
    sharks_spawned_this_wave += 1


def spawn_jellyfish():
    global jellies_spawned_this_wave
    cfg    = wave_config()
    margin = 60
    for _ in range(10):
        x = randint(WORLD_BOUNDS.left + margin, WORLD_BOUNDS.right - margin)
        y = randint(WORLD_BOUNDS.top  + margin, FLOOR_Y - margin)
        if pygame.Vector2(x, y).distance_to(player.rect.center) > 300:
            Jellyfish((x, y), (all_sprites, jellyfish_sprites),
                      speed_mult=cfg["speed_mult"])
            jellies_spawned_this_wave += 1
            return
    x = randint(WORLD_BOUNDS.left + margin, WORLD_BOUNDS.right - margin)
    y = randint(WORLD_BOUNDS.top  + margin, FLOOR_Y - margin)
    Jellyfish((x, y), (all_sprites, jellyfish_sprites), speed_mult=cfg["speed_mult"])
    jellies_spawned_this_wave += 1


start_wave(0)  # kick off tutorial wave

# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
def _draw_panel(x, y, w, h, alpha=200, radius=10):
    """Dark frosted panel with a subtle blue rim."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (8, 18, 45, alpha),        (0, 0, w, h), border_radius=radius)
    pygame.draw.rect(s, (60, 140, 220, 160),       (0, 0, w, h), 2, border_radius=radius)
    display_surface.blit(s, (x, y))

def _draw_bar(x, y, w, h, ratio, fill_col, bg_col=(30, 30, 55),
              border_col=(180, 210, 255), radius=6):
    """Generic rounded progress bar."""
    pygame.draw.rect(display_surface, bg_col,     (x, y, w, h), border_radius=radius)
    fw = max(0, round(w * ratio))
    if fw:
        pygame.draw.rect(display_surface, fill_col, (x, y, fw, h), border_radius=radius)
    pygame.draw.rect(display_surface, border_col,  (x, y, w, h), 2, border_radius=radius)

# ---------------------------------------------------------------------------
# UI drawing
# ---------------------------------------------------------------------------
def draw_ui():
    # ── Health pips (top-left) ────────────────────────────────────────────
    pip_r   = 14
    pip_gap = 36
    pip_y   = 28
    _draw_panel(8, 8, player.max_health * pip_gap + 16, pip_r * 2 + 16, alpha=170)
    for i in range(player.max_health):
        cx_ = 16 + pip_r + i * pip_gap
        if i < player.health:
            # filled heart — glowing red
            pygame.draw.circle(display_surface, (200, 40, 40), (cx_, pip_y), pip_r)
            pygame.draw.circle(display_surface, (255, 120, 120), (cx_ - 4, pip_y - 4), 5)  # highlight
            pygame.draw.circle(display_surface, (255, 80, 80), (cx_, pip_y), pip_r, 2)
        else:
            # empty
            pygame.draw.circle(display_surface, (50, 30, 30), (cx_, pip_y), pip_r)
            pygame.draw.circle(display_surface, (120, 60, 60), (cx_, pip_y), pip_r, 2)

    # health-bubble indicator
    if healthbubble_sprites:
        pulse_a = int(180 + 75 * sin(pygame.time.get_ticks() / 300))
        hs = small_font.render("+1 health available", True, (80, 235, 120))
        hs.set_alpha(pulse_a)
        display_surface.blit(hs, (16, pip_y + pip_r + 8))

    # oxygen-tank indicator
    if oxygentank_sprites:
        pulse_a = int(180 + 75 * sin(pygame.time.get_ticks() / 280))
        os_ = small_font.render("O2 tank nearby!", True, (0, 210, 255))
        os_.set_alpha(pulse_a)
        display_surface.blit(os_, (16, pip_y + pip_r + 28))

    # ── Wave progress bar (top-centre) ───────────────────────────────────
    if not level_complete and player.alive:
        cfg          = wave_config()
        total        = cfg["count"] + cfg["jellies"]
        wave_label   = "TUTORIAL" if current_wave == 0 else f"Wave {current_wave}"

        bar_w, bar_h = 340, 18
        bar_x        = (WINDOW_WIDTH - bar_w) // 2
        bar_y        = 38

        # panel behind bar
        _draw_panel(bar_x - 14, bar_y - 28, bar_w + 28, bar_h + 46, alpha=180, radius=10)

        # label row
        if between_wave_timer > 0:
            ratio      = 1.0 - (between_wave_timer / BETWEEN_WAVE_DELAY)
            bar_col    = (60, 220, 160)
            next_idx   = current_wave + 1
            if next_idx < len(WAVE_DATA):
                nxt   = "BOSS" if WAVE_DATA[next_idx]["boss"] else f"Wave {next_idx}"
                ltext = f"Next: {nxt}"
                lcol  = (255, 160, 60) if WAVE_DATA[next_idx]["boss"] else (140, 255, 180)
            else:
                ltext, lcol = "All waves done!", (140, 255, 180)
        else:
            remaining  = max(0, total - wave_kills)
            ratio      = remaining / total if total > 0 else 0.0
            bar_col    = (80, 210, 255) if ratio > 0.6 else (255, 200, 60) if ratio > 0.3 else (255, 80, 80)
            ltext      = f"{wave_label}   {wave_kills} / {total}"
            lcol       = (210, 235, 255)

        ls = small_font.render(ltext, True, lcol)
        display_surface.blit(ls, ls.get_rect(midbottom=(WINDOW_WIDTH // 2, bar_y - 4)))
        _draw_bar(bar_x, bar_y, bar_w, bar_h, ratio, bar_col)

    # ── Oxygen bar (bottom-left, below harpoon) ──────────────────────────
    o2_bar_w, o2_bar_h = 200, 16
    o2_bar_x, o2_bar_y = 16, WINDOW_HEIGHT - 90
    o2_ratio   = player.oxygen / player.max_oxygen
    o2_col     = (0, 200, 255) if o2_ratio > 0.3 else (255, 80, 80)
    _draw_panel(o2_bar_x - 10, o2_bar_y - 30, o2_bar_w + 20, o2_bar_h + 42, alpha=180, radius=10)
    _draw_bar(o2_bar_x, o2_bar_y, o2_bar_w, o2_bar_h, o2_ratio, o2_col)
    o2_lbl = small_font.render("OXYGEN", True, (180, 230, 255))
    display_surface.blit(o2_lbl, o2_lbl.get_rect(midbottom=(o2_bar_x + o2_bar_w // 2, o2_bar_y - 4)))
    # flashing warning when low
    if o2_ratio < 0.25 and int(pygame.time.get_ticks() / 400) % 2 == 0:
        warn = small_font.render("LOW OXYGEN!", True, (255, 80, 80))
        display_surface.blit(warn, warn.get_rect(midleft=(o2_bar_x + o2_bar_w + 10, o2_bar_y + o2_bar_h // 2)))

    # ── Harpoon cooldown (bottom-left) ───────────────────────────────────
    bar_w, bar_h = 200, 16
    bar_x, bar_y = 16, WINDOW_HEIGHT - 44
    progress     = player.cooldown_progress
    _draw_panel(bar_x - 10, bar_y - 30, bar_w + 20, bar_h + 42, alpha=180, radius=10)
    ready        = progress >= 1.0
    bar_col      = (60, 210, 255) if ready else (255, 160, 50)
    _draw_bar(bar_x, bar_y, bar_w, bar_h, progress, bar_col)
    lbl          = small_font.render("HARPOON" if not ready else "READY", True,
                                     (200, 240, 255) if not ready else (120, 255, 180))
    display_surface.blit(lbl, lbl.get_rect(midbottom=(bar_x + bar_w // 2, bar_y - 4)))
    # tiny cannon icon to the left of the bar
    pygame.draw.rect(display_surface, (160, 130, 80),  (bar_x - 8, bar_y + 4, 8, 8), border_radius=2)
    pygame.draw.rect(display_surface, (200, 170, 110), (bar_x - 8, bar_y + 4, 8, 8), 1, border_radius=2)

    # ── Wave start flash ─────────────────────────────────────────────────
    if wave_announce_timer > 0 and between_wave_timer == 0 and player.alive and not level_complete:
        t     = wave_announce_timer / 2.5
        alpha = min(255, int(t * 255))
        wlbl  = "TUTORIAL" if current_wave == 0 else f"WAVE  {current_wave}"
        # black letterbox bars
        bar_s = pygame.Surface((WINDOW_WIDTH, 70), pygame.SRCALPHA)
        bar_s.fill((0, 0, 0, int(t * 200)))
        display_surface.blit(bar_s, (0, WINDOW_HEIGHT // 2 - 60))
        display_surface.blit(bar_s, (0, WINDOW_HEIGHT // 2 + 10))
        ws = menu_title_font.render(wlbl, True, (100, 210, 255))
        ws.set_alpha(alpha)
        display_surface.blit(ws, ws.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 12)))

    # ── Boss announce ─────────────────────────────────────────────────────
    if boss_announce_timer > 0 and player.alive and not level_complete:
        t     = boss_announce_timer / 3.5
        alpha = min(255, int(t * 255))
        bar_s = pygame.Surface((WINDOW_WIDTH, 180), pygame.SRCALPHA)
        bar_s.fill((0, 0, 0, int(t * 210)))
        display_surface.blit(bar_s, (0, WINDOW_HEIGHT // 2 - 90))
        ns = menu_title_font.render("THE SHARKFATHER", True, (255, 205, 50))
        ns.set_alpha(alpha)
        display_surface.blit(ns, ns.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 22)))
        ss = title_font.render("has arrived...", True, (220, 160, 40))
        ss.set_alpha(alpha)
        display_surface.blit(ss, ss.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 36)))

    # ── Boss warning ticker ───────────────────────────────────────────────
    if boss_spawned and not level_complete and boss_announce_timer <= 0:
        pulse_a = int(190 + 65 * sin(pygame.time.get_ticks() / 250))
        ws = small_font.render("!  THE SHARKFATHER is guarding a map fragment!", True, (255, 200, 60))
        ws.set_alpha(pulse_a)
        display_surface.blit(ws, ws.get_rect(midtop=(WINDOW_WIDTH // 2, 8)))

    # ── End screens ───────────────────────────────────────────────────────
    if not player.alive:
        _draw_end_screen("YOU DIED", (220, 50, 50), "Press  R  to try again")
    elif level_complete:
        _draw_end_screen("LEVEL COMPLETE", (60, 220, 130), "Press  R  to play again")


def _draw_end_screen(title_text, title_col, sub_text):
    """Full-screen cinematic end overlay."""
    # dim the game world
    dim = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 160))
    display_surface.blit(dim, (0, 0))

    # centre panel
    pw, ph = 600, 220
    _draw_panel((WINDOW_WIDTH - pw) // 2, (WINDOW_HEIGHT - ph) // 2, pw, ph,
                alpha=220, radius=16)

    # coloured glow behind title
    gw = pygame.Surface((pw - 40, 80), pygame.SRCALPHA)
    gw.fill((*title_col, 55))
    display_surface.blit(gw, gw.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30)))

    ts = big_font.render(title_text, True, title_col)
    display_surface.blit(ts, ts.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 28)))

    ss = font.render(sub_text, True, (200, 220, 240))
    display_surface.blit(ss, ss.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 46)))

# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------
def reset_game():
    global wave_kills, sharks_spawned_this_wave, jellies_spawned_this_wave, wave_ending
    global boss_spawned, boss_announce_timer, level_complete, between_wave_timer, wave_announce_timer
    for sprite in list(shark_sprites):        sprite.kill()
    for sprite in list(jellyfish_sprites):    sprite.kill()
    for sprite in list(bolt_sprites):         sprite.kill()
    for sprite in list(harpoon_sprites):      sprite.kill()
    for sprite in list(bubble_sprites):       sprite.kill()
    for sprite in list(fragment_sprites):     sprite.kill()
    for sprite in list(healthbubble_sprites): sprite.kill()
    for sprite in list(oxygentank_sprites):   sprite.kill()
    player.health = player.max_health
    player.oxygen        = player.max_oxygen
    player.oxygen_empty  = False
    player.alive  = True
    player.rect.center = (WORLD_BOUNDS.centerx, WORLD_BOUNDS.centery)
    player.invincible_until = 0
    between_wave_timer  = 0.0
    boss_announce_timer = 0.0
    wave_announce_timer = 0.0
    tutorial_overlay.visible = True
    start_wave(0)


# ---------------------------------------------------------------------------
# Menu fonts (larger than game fonts)
# ---------------------------------------------------------------------------
menu_title_font  = pygame.font.SysFont("arial", 80, bold=True)
menu_button_font = pygame.font.SysFont("arial", 38, bold=True)
menu_small_font  = pygame.font.SysFont("arial", 26)
credits_font     = pygame.font.SysFont("arial", 30)
credits_role_font= pygame.font.SysFont("arial", 22)

# ---------------------------------------------------------------------------
# Menu background — animated underwater scene reusing background_surf
# ---------------------------------------------------------------------------
def _draw_menu_bg(tick):
    """Draw the animated menu background using web_back.png (top crop)."""
    display_surface.blit(menu_bg_surf, (0, 0))
    # Subtle dark overlay to keep text readable without killing the image
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 8, 22, 110))
    display_surface.blit(overlay, (0, 0))


# ---------------------------------------------------------------------------
# Animated menu shark (swims across the screen)
# ---------------------------------------------------------------------------
class MenuShark:
    SPEED = 180

    def __init__(self):
        self._reset(start_offscreen=False)

    def _reset(self, start_offscreen=True):
        self.y    = uniform(WINDOW_HEIGHT * 0.25, WINDOW_HEIGHT * 0.75)
        self.x    = -200 if start_offscreen else uniform(0, WINDOW_WIDTH)
        self.flip = False   # facing right (moves left→right)
        self._frame_idx   = 0
        self._frame_timer = 0.0

    def update(self, dt):
        self.x += self.SPEED * dt
        self._frame_timer += dt
        if self._frame_timer >= 1.0 / 8:   # 8 fps
            self._frame_timer = 0.0
            self._frame_idx = (self._frame_idx + 1) % len(SHARK_SWIM_FRAMES)
        if self.x > WINDOW_WIDTH + 200:
            self._reset(start_offscreen=True)

    def draw(self):
        frame = SHARK_SWIM_FRAMES[self._frame_idx]
        # menu shark faces RIGHT — our source art faces right, no flip needed
        display_surface.blit(frame, (int(self.x - frame.get_width() // 2),
                                     int(self.y - frame.get_height() // 2)))


# ---------------------------------------------------------------------------
# Button helper
# ---------------------------------------------------------------------------
class MenuButton:
    PAD_X, PAD_Y   = 56, 16

    def __init__(self, label, center):
        self.label  = label
        tw, th      = menu_button_font.size(label)
        self.rect   = pygame.Rect(0, 0, tw + self.PAD_X * 2, th + self.PAD_Y * 2)
        self.rect.center = center

    def draw(self, hover=False):
        r = self.rect
        # drop shadow
        shadow = pygame.Surface((r.w + 4, r.h + 4), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 80), (4, 4, r.w, r.h), border_radius=10)
        display_surface.blit(shadow, (r.x - 2, r.y - 2))

        # main body — two-tone gradient via two rects
        body = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        if hover:
            top_col  = (50, 130, 200, 235)
            bot_col  = (25,  80, 145, 235)
            rim_col  = (120, 210, 255, 255)
        else:
            top_col  = (18,  55, 110, 210)
            bot_col  = (10,  30,  70, 210)
            rim_col  = (70, 150, 220, 200)

        pygame.draw.rect(body, top_col, (0,        0, r.w, r.h // 2), border_radius=10)
        pygame.draw.rect(body, bot_col, (0, r.h // 2, r.w, r.h // 2), border_radius=10)
        # unify border radius on bottom half
        pygame.draw.rect(body, bot_col, (0, r.h // 2 - 10, r.w, 10))

        # inner glow line at top
        if hover:
            pygame.draw.line(body, (180, 230, 255, 120), (12, 3), (r.w - 12, 3), 1)

        pygame.draw.rect(body, rim_col, (0, 0, r.w, r.h), 2, border_radius=10)
        display_surface.blit(body, r.topleft)

        # label with subtle shadow
        tcol = (255, 255, 255) if hover else (200, 230, 255)
        sh_s = menu_button_font.render(self.label, True, (0, 0, 0))
        sh_s.set_alpha(80)
        display_surface.blit(sh_s, sh_s.get_rect(center=(r.centerx + 1, r.centery + 1)))
        ts = menu_button_font.render(self.label, True, tcol)
        display_surface.blit(ts, ts.get_rect(center=r.center))

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


# ---------------------------------------------------------------------------
# Credits data
# ---------------------------------------------------------------------------
_NAMES = ["Fionn Murphy", "Matthew Shine", "Max Nolan", "Aidan Brennan"]

CREDITS_ENTRIES = [
    #("", ""),                           # top padding
    ("A game by", ""),
    ("", ""),
    (_NAMES[0],           "Developer"),
    ("", ""),
    (_NAMES[1],           "Developer"),
    ("", ""),
    (_NAMES[3],           "Developer"),
    ("", ""),
    (_NAMES[2],           "Developer"),
    ("", ""),
    (_NAMES[0],           "Story & Writing"),
    ("", ""),
    (_NAMES[1],           "Sound Design"),
    ("", ""),
    (_NAMES[3],           "UI / UX"),
    ("", ""),
    (_NAMES[0],           "Producer"),
    ("", ""),
    ("Special Thanks", ""),
    (choice(_NAMES),      "for making it this far"),
    ("", ""),
    ("", ""),
    ("", ""),
]


def run_credits():
    """Scrolling film-style credits.  Returns when ESC or click."""
    scroll_y = float(WINDOW_HEIGHT)
    scroll_speed = 55   # pixels per second
    shark = MenuShark()
    clock2 = pygame.time.Clock()

    while True:
        dt = clock2.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                return

        scroll_y -= scroll_speed * dt
        shark.update(dt)

        _draw_menu_bg(pygame.time.get_ticks())
        shark.draw()

        # title
        tc = menu_title_font.render("CREDITS", True, (120, 220, 255))
        display_surface.blit(tc, tc.get_rect(midtop=(WINDOW_WIDTH // 2, 20)))

        # scroll the entries
        y = scroll_y
        LINE_H = 42
        for (name, role) in CREDITS_ENTRIES:
            if name:
                col = (255, 255, 255) if role else (160, 220, 255)
                ns  = credits_font.render(name, True, col)
                display_surface.blit(ns, ns.get_rect(centerx=WINDOW_WIDTH // 2, top=y))
                if role:
                    rs = credits_role_font.render(role, True, (150, 190, 140))
                    display_surface.blit(rs, rs.get_rect(centerx=WINDOW_WIDTH // 2, top=y + 30))
                    y += LINE_H + 16
                else:
                    y += LINE_H
            else:
                y += LINE_H // 2

        # auto-return when all text scrolled off top
        if y < 0:
            return

        # dim bars at top and bottom so text fades in/out
        for bar_y, bar_h, direction in [(0, 80, 1), (WINDOW_HEIGHT - 80, 80, -1)]:
            for i in range(bar_h):
                a = int(255 * (1 - i / bar_h)) if direction == 1 else int(255 * (i / bar_h))
                pygame.draw.line(display_surface, (0, 10, 30),
                                 (0, bar_y + i), (WINDOW_WIDTH, bar_y + i))
                # re-blit with alpha would be complex; simple black bar is clean enough

        back = menu_small_font.render("ESC / click to return", True, (120, 140, 160))
        display_surface.blit(back, (14, WINDOW_HEIGHT - 28))
        pygame.display.update()


def run_options():
    """Simple options screen — placeholder with volume/fullscreen stubs."""
    clock2 = pygame.time.Clock()
    shark  = MenuShark()
    back_btn = MenuButton("Back", (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 80))

    while True:
        dt = clock2.tick(60) / 1000
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.is_hovered(mouse):
                    return

        shark.update(dt)
        _draw_menu_bg(pygame.time.get_ticks())
        shark.draw()

        title_s = menu_title_font.render("OPTIONS", True, (120, 220, 255))
        display_surface.blit(title_s, title_s.get_rect(midtop=(WINDOW_WIDTH // 2, 30)))

        # stub options
        opts = [
            ("Music",  "Coming soon"),
            ("SFX",    "Coming soon"),
            ("Window", "1280 x 720"),
        ]
        for i, (k, v) in enumerate(opts):
            ks = menu_button_font.render(f"{k}:", True, (200, 230, 255))
            vs = menu_button_font.render(v,       True, (160, 190, 140))
            cy = 200 + i * 80
            display_surface.blit(ks, ks.get_rect(right=WINDOW_WIDTH // 2 - 20, centery=cy))
            display_surface.blit(vs, vs.get_rect(left=WINDOW_WIDTH  // 2 + 20, centery=cy))

        back_btn.draw(back_btn.is_hovered(mouse))
        pygame.display.update()


def run_pause_menu():
    """
    Pause screen — blurs/dims the frozen game frame and shows a
    polished cinematic overlay.  Returns when the player resumes.
    """
    frozen  = display_surface.copy()

    cx      = WINDOW_WIDTH  // 2
    cy      = WINDOW_HEIGHT // 2
    btn_resume  = MenuButton("Resume",  (cx, cy - 20))
    btn_options = MenuButton("Options", (cx, cy + 70))
    btn_quit    = MenuButton("Quit",    (cx, cy + 160))
    buttons     = [btn_resume, btn_options, btn_quit]

    shark   = MenuShark()
    clock2  = pygame.time.Clock()
    pulse   = 0.0
    enter_t = 0.0          # tracks a short fade-in on open

    while True:
        dt      = clock2.tick(60) / 1000
        pulse  += dt * 1.8
        enter_t = min(1.0, enter_t + dt * 4)   # 0→1 in 0.25 s
        mouse   = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_r):
                    return 'resume'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_resume.is_hovered(mouse):
                    return 'resume'
                if btn_options.is_hovered(mouse):
                    run_options()
                if btn_quit.is_hovered(mouse):
                    pygame.quit(); raise SystemExit

        #shark.update(dt)

        # ── frozen game frame ────────────────────────────────────────────
        display_surface.blit(frozen, (0, 0))

        # ── vignette / depth-of-field sim: darken edges, blur centre ────
        vign = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        # uniform dark wash
        vign.fill((0, 5, 20, int(155 * enter_t)))
        # darker edges
        edge = 200
        for i in range(edge):
            a = int(80 * (1 - i / edge) * enter_t)
            pygame.draw.rect(vign, (0, 0, 0, a), (i, i, WINDOW_WIDTH - i*2, WINDOW_HEIGHT - i*2), 1)
        display_surface.blit(vign, (0, 0))

        # ── animated shark behind the panel ──────────────────────────────
        #shark.draw()

        # ── decorative horizontal lines ───────────────────────────────────
        line_alpha = int(60 * enter_t)
        for ly in range(0, WINDOW_HEIGHT, 6):
            pygame.draw.line(display_surface, (20, 60, 120, line_alpha),
                             (0, ly), (WINDOW_WIDTH, ly))

        # ── centre panel ─────────────────────────────────────────────────
        pw, ph  = 460, 380
        px, py  = cx - pw // 2, cy - ph // 2
        panel   = pygame.Surface((pw, ph), pygame.SRCALPHA)

        # outer shadow
        sh = pygame.Surface((pw + 16, ph + 16), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 90), (8, 8, pw, ph), border_radius=18)
        display_surface.blit(sh, (px - 8, py - 8))

        # panel body (dark navy)
        pygame.draw.rect(panel, (8, 18, 50, int(230 * enter_t)),
                         (0, 0, pw, ph), border_radius=16)
        # inner top highlight strip
        pygame.draw.rect(panel, (60, 140, 220, 40), (2, 2, pw - 4, 4), border_radius=14)
        # border glow (double ring)
        glow_a = int((150 + 60 * sin(pulse)) * enter_t)
        pygame.draw.rect(panel, (50, 140, 220, glow_a), (0, 0, pw, ph), 2, border_radius=16)
        pygame.draw.rect(panel, (100, 190, 255, glow_a // 2), (3, 3, pw - 6, ph - 6), 1, border_radius=14)
        display_surface.blit(panel, (px, py))

        # ── divider line under title ──────────────────────────────────────
        div_y = py + 105
        div_alpha = int(180 * enter_t)
        div_surf = pygame.Surface((pw - 40, 2), pygame.SRCALPHA)
        div_surf.fill((80, 170, 255, div_alpha))
        display_surface.blit(div_surf, (px + 20, div_y))

        # ── title ─────────────────────────────────────────────────────────
        # glow halo
        gh = pygame.Surface((380, 72), pygame.SRCALPHA)
        gh_a = int((60 + 30 * sin(pulse)) * enter_t)
        gh.fill((40, 120, 210, gh_a))
        display_surface.blit(gh, gh.get_rect(center=(cx, py + 62)))

        ts = menu_title_font.render("PAUSED", True, (220, 240, 255))
        ts.set_alpha(int(255 * enter_t))
        display_surface.blit(ts, ts.get_rect(center=(cx, py + 62)))

        # ── buttons ───────────────────────────────────────────────────────
        for btn in buttons:
            # fade in with enter_t
            btn.rect.x = cx - btn.rect.w // 2
            btn.draw(btn.is_hovered(mouse))

        # ── bottom hint ───────────────────────────────────────────────────
        hint_a = int((140 + 60 * sin(pulse * 1.5)) * enter_t)
        hint   = menu_small_font.render("ESC  or  R  to resume", True, (120, 170, 210))
        hint.set_alpha(hint_a)
        display_surface.blit(hint, hint.get_rect(midbottom=(cx, py + ph - 12)))

        pygame.display.update()


def run_main_menu():
    """
    Animated start screen.
    Returns 'start' or raises SystemExit.
    """
    cx = WINDOW_WIDTH  // 2
    btn_start   = MenuButton("Start Game", (cx, 360))
    btn_options = MenuButton("Options",    (cx, 450))
    btn_credits = MenuButton("Credits",    (cx, 540))
    btn_quit    = MenuButton("Quit",       (cx, 630))
    buttons     = [btn_start, btn_options, btn_credits, btn_quit]

    #shark       = MenuShark()
    # second shark slightly behind, different y
    #shark2      = MenuShark()
    #shark2.x    = uniform(-400, -100)
    #shark2.y    = uniform(WINDOW_HEIGHT * 0.5, WINDOW_HEIGHT * 0.8)

    clock2      = pygame.time.Clock()
    bg_x        = 0.0   # slow pan
    pulse       = 0.0

    while True:
        dt    = clock2.tick(60) / 1000
        pulse += dt * 2.0
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_start.is_hovered(mouse):
                    return 'start'
                if btn_options.is_hovered(mouse):
                    run_options()
                if btn_credits.is_hovered(mouse):
                    run_credits()
                if btn_quit.is_hovered(mouse):
                    pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return 'start'
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); raise SystemExit

        #shark.update(dt)
        #shark2.update(dt)

        # ── background ──────────────────────────────────────────────────────
        _draw_menu_bg(pygame.time.get_ticks())
        #shark2.draw()
        #shark.draw()

        # ── title ────────────────────────────────────────────────────────────
        # ── title image (title.png) or text fallback ─────────────────────
        if menu_title_img:
            # Gentle bob up/down
            bob_y = round(sin(pulse) * 5)
            t_rect = menu_title_img.get_rect(center=(cx, 155 + bob_y))

            # Drop shadow
            sh = pygame.Surface(menu_title_img.get_size(), pygame.SRCALPHA)
            sh.blit(menu_title_img, (0, 0))
            sh.fill((0, 0, 0, 100), special_flags=pygame.BLEND_RGBA_MULT)
            display_surface.blit(sh, (t_rect.x + 3, t_rect.y + 4))

            # Glow halo behind the image
            glow_a = int(50 + 30 * sin(pulse))
            glow_s = pygame.Surface((menu_title_img.get_width() + 40,
                                     menu_title_img.get_height() + 20), pygame.SRCALPHA)
            glow_s.fill((40, 140, 220, glow_a))
            display_surface.blit(glow_s, glow_s.get_rect(center=(cx, 155 + bob_y)))

            display_surface.blit(menu_title_img, t_rect)
        else:
            # Text fallback if title.png is missing
            glow_a = int(80 + 40 * sin(pulse))
            glow_s = pygame.Surface((640, 120), pygame.SRCALPHA)
            glow_s.fill((40, 120, 200, glow_a))
            display_surface.blit(glow_s, glow_s.get_rect(center=(cx, 165)))
            t1 = menu_title_font.render("SEA",   True, (255, 255, 255))
            t2 = menu_title_font.render("BOUND", True, (80, 210, 255))
            display_surface.blit(t1, t1.get_rect(center=(cx, 130)))
            display_surface.blit(t2, t2.get_rect(center=(cx, 210)))

        # subtitle flicker
        if int(pulse * 2) % 4 != 0:
            press_s = menu_small_font.render("Press ENTER or click Start Game", True, (200, 230, 255))
            display_surface.blit(press_s, press_s.get_rect(center=(cx, 225)))

        # ── buttons ──────────────────────────────────────────────────────────
        for btn in buttons:
            btn.draw(btn.is_hovered(mouse))

        pygame.display.update()


# ---------------------------------------------------------------------------
# Run the main menu first — only proceed to the game if 'start' is returned
# ---------------------------------------------------------------------------
run_main_menu()

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
running = True
while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- ambient bubbles ---
        if event.type == AMBIENT_BUBBLE_EVENT and player.alive:
            spawn_x = min(max(player.rect.centerx + randint(-WINDOW_WIDTH // 2, WINDOW_WIDTH // 2),
                              WORLD_BOUNDS.left), WORLD_BOUNDS.right)
            spawn_y = min(max(player.rect.centery + WINDOW_HEIGHT // 2 + randint(0, 100),
                              WORLD_BOUNDS.top), WORLD_BOUNDS.bottom)
            Bubble((spawn_x, spawn_y), (all_sprites, bubble_sprites))

        # --- health bubble spawn ---
        if event.type == HEALTH_BUBBLE_EVENT and player.alive and not level_complete:
            margin = 80
            hx = randint(WORLD_BOUNDS.left + margin, WORLD_BOUNDS.right  - margin)
            hy = randint(WORLD_BOUNDS.top  + margin, FLOOR_Y - margin)
            HealthBubble((hx, hy), (all_sprites, healthbubble_sprites))

        # --- oxygen tank spawn ---
        if event.type == OXYGEN_TANK_EVENT and player.alive and not level_complete:
            margin = 80
            ox = randint(WORLD_BOUNDS.left + margin, WORLD_BOUNDS.right  - margin)
            oy = randint(WORLD_BOUNDS.top  + margin, FLOOR_Y - margin)
            OxygenTankPickup((ox, oy), (all_sprites, oxygentank_sprites))

        # --- wave shark spawning ---
        if event.type == SHARK_SPAWN_EVENT and player.alive and not level_complete and not wave_ending:
            cfg     = wave_config()
            is_boss = cfg["boss"]

            if is_boss and not boss_spawned:
                spawn_shark(is_boss=True)
                boss_spawned        = True
                boss_announce_timer = 3.5   # seconds to show "THE SHARKFATHER" flash
                pygame.time.set_timer(SHARK_SPAWN_EVENT, 0)
            elif not is_boss and sharks_spawned_this_wave < cfg["count"]:
                spawn_shark(is_boss=False)

            # Spawn jellyfish alongside sharks (spread across first half of wave)
            if not is_boss and jellies_spawned_this_wave < cfg["jellies"]:
                spawn_jellyfish()

        # --- pause on ESC ---
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            run_pause_menu()
            # Discard the time that accumulated while paused so sprites
            # don't get a huge dt on the first frame back.
            clock.tick(60)

        # --- tutorial dismiss on SPACE ---
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if current_wave == 0 and tutorial_overlay.visible:
                tutorial_overlay.visible = False

        # --- restart ---
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and not player.alive:
            reset_game()

    # -------------------------------------------------------------------
    # Update sprites
    # -------------------------------------------------------------------
    all_sprites.update(dt)

    if wave_announce_timer > 0:
        wave_announce_timer = max(0.0, wave_announce_timer - dt)

    if boss_announce_timer > 0:
        boss_announce_timer = max(0.0, boss_announce_timer - dt)

    if current_wave == 0 and tutorial_overlay.visible:
        tutorial_overlay.update(dt)

    # -------------------------------------------------------------------
    # Harpoon <-> shark collisions
    # -------------------------------------------------------------------
    for harpoon in list(harpoon_sprites):
        hit_sharks = pygame.sprite.spritecollide(harpoon, shark_sprites, False)
        if hit_sharks:
            harpoon.kill()
            for shark in hit_sharks:
                if shark.hit():
                    if shark.is_boss:
                        MapFragment(shark.rect.center, (all_sprites, fragment_sprites))
                    else:
                        wave_kills += 1
            continue   # harpoon already dead

        hit_jellies = pygame.sprite.spritecollide(harpoon, jellyfish_sprites, False)
        if hit_jellies:
            harpoon.kill()
            for jelly in hit_jellies:
                if jelly.hit():
                    wave_kills += 1

    # -------------------------------------------------------------------
    # Electric bolt <-> player collisions
    # -------------------------------------------------------------------
    if player.alive and not player.is_invincible():
        for bolt in list(bolt_sprites):
            if player.hitbox.colliderect(bolt.rect):
                bolt.kill()
                player.take_damage()
                break

    # -------------------------------------------------------------------
    # Collect map fragment -> transition to level 2
    # -------------------------------------------------------------------
    if player.alive and not level_complete and fragment_sprites:
        collected = pygame.sprite.spritecollide(player, fragment_sprites, True)
        if collected:
            level_complete = True
            pygame.time.set_timer(SHARK_SPAWN_EVENT, 0)
            pygame.time.set_timer(HEALTH_BUBBLE_EVENT, 0)

            # ── fade-out + "LEVEL COMPLETE" splash ──────────────────────────
            fade = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            fade.fill((0, 0, 0))
            for alpha in range(0, 256, 4):
                all_sprites.draw_all(player.rect.center)
                draw_ui()
                fade.set_alpha(alpha)
                display_surface.blit(fade, (0, 0))
                pygame.display.update()
                clock.tick(60)

            # Show "LEVEL COMPLETE" for 2 seconds
            display_surface.fill((0, 5, 20))
            line1 = big_font.render("LEVEL COMPLETE", True, (90, 220, 140))
            line2 = title_font.render("Proceeding to Level 2...", True, (160, 210, 255))
            display_surface.blit(line1, line1.get_frect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30)))
            display_surface.blit(line2, line2.get_frect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40)))
            pygame.display.update()
            pygame.time.wait(2000)

            # ── hand off to level2.py ────────────────────────────────────────
            pygame.quit()
            import subprocess, sys, os
            level2_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "Fionn", "level2.py"
            )
            subprocess.run([sys.executable, level2_path])
            raise SystemExit

    # -------------------------------------------------------------------
    # Collect health bubbles -> +1 HP (capped at max)
    # -------------------------------------------------------------------
    if player.alive:
        picked = pygame.sprite.spritecollide(player, healthbubble_sprites, True)
        if picked and player.health < player.max_health:
            player.health += 1
            SFX_HEALTH_PICKUP.play()

    # -------------------------------------------------------------------
    # Collect oxygen tanks -> refill oxygen + reset empty flag
    # -------------------------------------------------------------------
    if player.alive:
        o2_picked = pygame.sprite.spritecollide(player, oxygentank_sprites, True)
        if o2_picked:
            player.oxygen       = min(player.max_oxygen,
                                      player.oxygen + OxygenTankPickup.REFILL)
            player.oxygen_empty = False
            SFX_PLAYER_DIE.play()   # reuse the oxygen-tank sound

    # -------------------------------------------------------------------
    # Player <-> shark damage
    # -------------------------------------------------------------------
    if player.alive and not player.is_invincible():
        for shark in shark_sprites:
            if player.hitbox.colliderect(shark.rect):
                player.take_damage()
                break

    # -------------------------------------------------------------------
    # Wave progression logic
    # -------------------------------------------------------------------
    if player.alive and not level_complete:
        cfg          = wave_config()
        total_sharks = cfg["count"]
        total_jelly  = cfg["jellies"]
        total        = total_sharks + total_jelly

        wave_done = (sharks_spawned_this_wave  >= total_sharks and
                     jellies_spawned_this_wave >= total_jelly  and
                     wave_kills >= total and
                     not wave_ending)

        if wave_done:
            wave_ending = True
            pygame.time.set_timer(SHARK_SPAWN_EVENT, 0)   # stop any remaining spawns
            # Tutorial wave: dismiss overlay
            if current_wave == 0:
                tutorial_overlay.visible = False
            between_wave_timer = BETWEEN_WAVE_DELAY

        # Tick down the between-wave countdown
        if between_wave_timer > 0:
            between_wave_timer = max(0.0, between_wave_timer - dt)
            if between_wave_timer == 0.0:
                next_wave = current_wave + 1
                if next_wave < len(WAVE_DATA):
                    start_wave(next_wave)
                # Final wave (boss) handled via fragment collect above

    # -------------------------------------------------------------------
    # Draw
    # -------------------------------------------------------------------
    all_sprites.draw_all(player.rect.center)
    draw_ui()

    if current_wave == 0 and tutorial_overlay.visible:
        tutorial_overlay.draw()

    pygame.display.update()

pygame.quit()
