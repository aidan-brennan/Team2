import pygame
from random import randint, uniform, choice
from math import sin, cos, pi

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
BOSS_EXTRA_SCALE = 1.9

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
_shark1 = scale_surface(load_or_placeholder('images/shark1.png', make_shark_surface), SHARK_SCALE)

# One swim frame + one attack frame — both the same image
SHARK_SWIM_FRAMES   = [_shark1]
SHARK_ATTACK_FRAMES = [_shark1]

# Boss: scale up further and apply red tint
_boss1 = scale_surface(_shark1, BOSS_EXTRA_SCALE).copy()
_boss_tint = pygame.Surface(_boss1.get_size(), pygame.SRCALPHA)
_boss_tint.fill((255, 110, 110, 255))
_boss1.blit(_boss_tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

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

jellyfish_surf = scale_surface(load_or_placeholder('images/jellyfish.png', make_jellyfish_surface), 1.4)
mapfrag_surf   = scale_surface(load_or_placeholder('images/mapfrag1.png',  make_mapfrag_surface),   1.0)

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

    def is_invincible(self):
        return pygame.time.get_ticks() < self.invincible_until

    def update(self, dt):
        if not self.alive:
            return

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
            offset_x = (self.rect.width if self.facing_right else -self.rect.width) * 0.3
            start_pos = self.rect.center + pygame.Vector2(offset_x, -self.rect.height * 0.35)
            mouse_world_pos = pygame.Vector2(pygame.mouse.get_pos()) + all_sprites.offset
            direction = mouse_world_pos - start_pos
            if direction:
                direction = direction.normalize()
                Harpoon(harpoon_surf, start_pos, direction, (all_sprites, harpoon_sprites))
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
    CHARGE_COOLDOWN  = 5.0     # seconds between charge sequences
    CHARGE_WINDUP    = 0.45    # seconds of wind-up telegraph
    CHARGE_SPEED     = 1000     # px/s during each dash
    CHARGE_DASH_DUR  = 0.38    # seconds each individual dash lasts
    CHARGE_PAUSE_DUR = 0.18    # brief pause between back-and-forth dashes
    CHARGE_PASSES    = 2       # how many back-and-forth passes per sequence
    SUMMON_COOLDOWN  = 7.0
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
        if self.health <= 0:
            for _ in range(6):
                Bubble(self.rect.center, (all_sprites, bubble_sprites), small=True)
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

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            # Discharge sparks on death
            for _ in range(4):
                Bubble(self.rect.center, (all_sprites, bubble_sprites), small=True)
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
level_complete           = False
between_wave_timer       = 0.0
wave_announce_timer      = 0.0

tutorial_overlay = TutorialOverlay()

AMBIENT_BUBBLE_EVENT   = pygame.USEREVENT + 1
SHARK_SPAWN_EVENT      = pygame.USEREVENT + 2
HEALTH_BUBBLE_EVENT    = pygame.USEREVENT + 3
pygame.time.set_timer(AMBIENT_BUBBLE_EVENT, 250)
pygame.time.set_timer(HEALTH_BUBBLE_EVENT, 20_000)   # one health bubble every 20 s


def wave_config():
    return WAVE_DATA[min(current_wave, len(WAVE_DATA) - 1)]


def start_wave(wave_idx):
    global current_wave, sharks_spawned_this_wave, jellies_spawned_this_wave
    global wave_kills, wave_ending, boss_spawned, wave_announce_timer
    current_wave              = wave_idx
    sharks_spawned_this_wave  = 0
    jellies_spawned_this_wave = 0
    wave_kills                = 0
    wave_ending               = False
    boss_spawned              = False
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
# UI drawing
# ---------------------------------------------------------------------------
def draw_ui():
    # --- Health pips ---
    for i in range(player.max_health):
        color = (220, 60, 60) if i < player.health else (70, 70, 70)
        pygame.draw.circle(display_surface, color, (30 + i * 34, 30), 12)
        pygame.draw.circle(display_surface, (255, 255, 255), (30 + i * 34, 30), 12, 2)

    # Show a small green "+" next to any active health bubbles on screen
    if healthbubble_sprites:
        hint = small_font.render("+  health", True, (80, 220, 110))
        display_surface.blit(hint, (30 + player.max_health * 34 + 8, 20))

    # --- Wave progress bar (top-centre) ---
    if not level_complete and player.alive:
        cfg         = wave_config()
        total_sharks = cfg["count"]
        total_jelly  = cfg["jellies"]
        total        = total_sharks + total_jelly

        if between_wave_timer > 0:
            ratio = 1.0 - (between_wave_timer / BETWEEN_WAVE_DELAY)
        else:
            remaining = max(0, total - wave_kills)
            ratio = remaining / total if total > 0 else 0.0

        bar_w, bar_h = 320, 16
        bar_x = (WINDOW_WIDTH - bar_w) // 2
        bar_y = 36

        # Background track
        pygame.draw.rect(display_surface, (20, 20, 50, 200), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), border_radius=7)
        pygame.draw.rect(display_surface, (40, 40, 70), (bar_x, bar_y, bar_w, bar_h), border_radius=6)

        # Colour: teal while refilling, blue→yellow→red while draining
        if between_wave_timer > 0:
            bar_color = (60, 220, 160)
        elif ratio > 0.6:
            bar_color = (80, 210, 255)
        elif ratio > 0.3:
            bar_color = (255, 200, 60)
        else:
            bar_color = (255, 80, 80)

        fill_w = round(bar_w * ratio)
        if fill_w > 0:
            pygame.draw.rect(display_surface, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=6)

        # Border
        pygame.draw.rect(display_surface, (200, 220, 255), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)

        # Label above bar
        wave_label = "TUTORIAL" if current_wave == 0 else f"Wave {current_wave}"
        if between_wave_timer > 0:
            next_idx  = current_wave + 1
            if next_idx < len(WAVE_DATA):
                next_label = "BOSS" if WAVE_DATA[next_idx]["boss"] else f"Wave {next_idx}"
                sub_label  = f"Next: {next_label}"
            else:
                sub_label = "Final wave cleared!"
            label_surf = small_font.render(sub_label, True, (160, 255, 200))
        else:
            kill_label = f"{wave_kills} / {total}"
            label_surf = small_font.render(f"{wave_label}   {kill_label}", True, (220, 240, 255))
        display_surface.blit(label_surf, label_surf.get_frect(midtop=(WINDOW_WIDTH // 2, bar_y + bar_h + 4)))

    # --- Harpoon cooldown bar (bottom-left) ---
    bar_w, bar_h = 160, 14
    bar_x, bar_y = 20, WINDOW_HEIGHT - 34
    progress = player.cooldown_progress
    pygame.draw.rect(display_surface, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
    fill_color = (90, 200, 255) if progress >= 1 else (255, 170, 60)
    pygame.draw.rect(display_surface, fill_color, (bar_x, bar_y, round(bar_w * progress), bar_h), border_radius=4)
    pygame.draw.rect(display_surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=4)
    label = font.render("HARPOON", True, (255, 255, 255))
    display_surface.blit(label, (bar_x, bar_y - 24))

    # --- Wave announce flash at start of each wave ---
    if wave_announce_timer > 0 and between_wave_timer == 0 and player.alive and not level_complete:
        alpha = min(255, int(wave_announce_timer / 2.5 * 255))
        wave_label = "TUTORIAL" if current_wave == 0 else f"Wave {current_wave}"
        ann_surf = big_font.render(wave_label, True, (120, 220, 255))
        ann_surf.set_alpha(alpha)
        display_surface.blit(ann_surf, ann_surf.get_frect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))

    # --- End states ---
    if not player.alive:
        over_surf = big_font.render("YOU DIED", True, (255, 60, 60))
        display_surface.blit(over_surf, over_surf.get_frect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20)))
        restart_surf = font.render("Press R to restart", True, (255, 255, 255))
        display_surface.blit(restart_surf, restart_surf.get_frect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40)))
    elif level_complete:
        over_surf = big_font.render("LEVEL COMPLETE", True, (90, 220, 140))
        display_surface.blit(over_surf, over_surf.get_frect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20)))
        restart_surf = font.render("Press R to play again", True, (255, 255, 255))
        display_surface.blit(restart_surf, restart_surf.get_frect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40)))
    elif boss_spawned and not level_complete:
        warning_surf = font.render("A massive shark is guarding a map fragment!", True, (255, 170, 170))
        display_surface.blit(warning_surf, warning_surf.get_frect(midtop=(WINDOW_WIDTH // 2, 34)))

# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------
def reset_game():
    global wave_kills, sharks_spawned_this_wave, jellies_spawned_this_wave, wave_ending
    global boss_spawned, level_complete, between_wave_timer, wave_announce_timer
    for sprite in list(shark_sprites):        sprite.kill()
    for sprite in list(jellyfish_sprites):    sprite.kill()
    for sprite in list(bolt_sprites):         sprite.kill()
    for sprite in list(harpoon_sprites):      sprite.kill()
    for sprite in list(bubble_sprites):       sprite.kill()
    for sprite in list(fragment_sprites):     sprite.kill()
    for sprite in list(healthbubble_sprites): sprite.kill()
    player.health = player.max_health
    player.alive  = True
    player.rect.center = (WORLD_BOUNDS.centerx, WORLD_BOUNDS.centery)
    player.invincible_until = 0
    between_wave_timer  = 0.0
    wave_announce_timer = 0.0
    tutorial_overlay.visible = True
    start_wave(0)


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

        # --- wave shark spawning ---
        if event.type == SHARK_SPAWN_EVENT and player.alive and not level_complete and not wave_ending:
            cfg     = wave_config()
            is_boss = cfg["boss"]

            if is_boss and not boss_spawned:
                spawn_shark(is_boss=True)
                boss_spawned = True
                pygame.time.set_timer(SHARK_SPAWN_EVENT, 0)
            elif not is_boss and sharks_spawned_this_wave < cfg["count"]:
                spawn_shark(is_boss=False)

            # Spawn jellyfish alongside sharks (spread across first half of wave)
            if not is_boss and jellies_spawned_this_wave < cfg["jellies"]:
                spawn_jellyfish()

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
    # Collect map fragment -> level complete
    # -------------------------------------------------------------------
    if player.alive and not level_complete and fragment_sprites:
        collected = pygame.sprite.spritecollide(player, fragment_sprites, True)
        if collected:
            level_complete = True
            pygame.time.set_timer(SHARK_SPAWN_EVENT, 0)

    # -------------------------------------------------------------------
    # Collect health bubbles -> +1 HP (capped at max)
    # -------------------------------------------------------------------
    if player.alive:
        picked = pygame.sprite.spritecollide(player, healthbubble_sprites, True)
        if picked and player.health < player.max_health:
            player.health += 1

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
