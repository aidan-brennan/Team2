import pygame
import random
import sys
import os
import math
from math import sin
from oxygentank import OxygenSystem

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "Images")
AUDIO_DIR = os.path.join(BASE_DIR, "Audio")

WIDTH = 1000
HEIGHT = 600

Gravity = 0.25
Swim_strength = -7
Max_fall_speed = 6

diver_x = 80
diver_radius = 16
diver_size = (95, 75)

tentacle_width = 110
tentacle_gap = 120
tentacle_speed_base = 4       # starting speed — difficulty scales from here
tentacle_speed = tentacle_speed_base
tentacle_spawn_min = 1000
tentacle_spawn_max = 2000
tentacle_spawn_ms = random.randint(tentacle_spawn_min, tentacle_spawn_max)

Ground_height = 40
FPS = 60

TEXT_COLOR = (255, 255, 255)

# The following are populated by run_level2() once pygame is initialized and
# the screen surface exists. They start out as None/empty so that classes
# and module-level functions referencing them by name still import cleanly;
# they are only ever *used* after run_level2() has populated them.
screen = None
tentacle = None
tentacle_ceiling = None
background = None
mapfrag1_img = None
mapfrag2_img = None
fullmap_img = None
ding_sound = None
diver_frames = []

music_volume = 0.6
sfx_volume = 0.7


def _load_diver_frame(path):
    img = pygame.image.load(path).convert_alpha()
    img = pygame.transform.smoothscale(img, diver_size)
    return img


class diver:
    FRAME_DURATION = 0.25

    def __init__(self):
        self.x = diver_x
        self.y = HEIGHT // 2
        self.velocity_y = 0
        self.radius = diver_radius
        self.angle = 0
        self.frame_index = 0
        self.frame_timer = 0.0

    def swim(self):
        self.velocity_y = Swim_strength

    def update(self, dt=1/60):
        self.velocity_y += Gravity
        self.velocity_y = min(self.velocity_y, Max_fall_speed)
        self.y += self.velocity_y
        self.angle = max(-30, min(25, -self.velocity_y * 4))
        self.frame_timer += dt
        if self.frame_timer >= self.FRAME_DURATION:
            self.frame_timer -= self.FRAME_DURATION
            self.frame_index = (self.frame_index + 1) % len(diver_frames)

    def draw(self, surface):
        frame   = diver_frames[self.frame_index]
        rotated = pygame.transform.rotate(frame, self.angle)
        rect    = rotated.get_rect(center=(self.x, int(self.y)))
        surface.blit(rotated, rect)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)


class Tentacle:
    SWAY_AMPLITUDE = 6
    SWAY_SPEED     = 0.004

    def __init__(self, x):
        self.x = x
        self.gap_y = random.randint(120, HEIGHT - Ground_height - 120)
        self.width = tentacle_width
        self.passed = False
        self.time_offset = random.uniform(0, 2 * math.pi)
        self._last_top_h = -1
        self._last_bot_h = -1
        self._top_img = None
        self._bot_img = None
        self._top_mask = None
        self._bot_mask = None

    def update(self):
        self.x -= tentacle_speed

    def get_rects(self):
        top_rect = pygame.Rect(self.x, 0, self.width, self.gap_y - tentacle_gap // 2)
        bottom_rect = pygame.Rect(
            self.x, self.gap_y + tentacle_gap // 2,
            self.width, HEIGHT - (self.gap_y + tentacle_gap // 2) - Ground_height
        )
        return top_rect, bottom_rect

    def _get_scaled(self):
        top_rect, bottom_rect = self.get_rects()
        if top_rect.height != self._last_top_h:
            self._top_img  = pygame.transform.smoothscale(tentacle_ceiling, (self.width, max(1, top_rect.height)))
            self._top_mask = pygame.mask.from_surface(self._top_img)
            self._last_top_h = top_rect.height
        if bottom_rect.height != self._last_bot_h:
            self._bot_img  = pygame.transform.smoothscale(tentacle, (self.width, max(1, bottom_rect.height)))
            self._bot_mask = pygame.mask.from_surface(self._bot_img)
            self._last_bot_h = bottom_rect.height
        return self._top_img, self._bot_img, self._top_mask, self._bot_mask

    def check_collision(self, player_rect):
        top_rect, bottom_rect = self.get_rects()
        _, _, top_mask, bot_mask = self._get_scaled()
        player_mask = pygame.mask.Mask((player_rect.width, player_rect.height), fill=True)
        for t_rect, t_mask in ((top_rect, top_mask), (bottom_rect, bot_mask)):
            offset = (t_rect.x - player_rect.x, t_rect.y - player_rect.y)
            if player_mask.overlap(t_mask, offset):
                return True
        return False

    def draw(self, surface):
        top_rect, bottom_rect = self.get_rects()
        top_img, bot_img, _, _ = self._get_scaled()
        now  = pygame.time.get_ticks()
        sway = int(math.sin(now * self.SWAY_SPEED + self.time_offset) * self.SWAY_AMPLITUDE)
        surface.blit(bot_img, bottom_rect.move(sway, 0))
        surface.blit(top_img, top_rect.move(-sway, 0))

    def offscreen(self):
        return self.x + self.width < 0


class Bubble:
    def __init__(self, x, y):
        self.radius = random.randint(2, 6)
        self.x = float(x)
        self.y = float(y)
        self.rise_speed  = random.uniform(30, 80)
        self.sway_amount = random.uniform(4, 14)
        self.sway_speed  = random.uniform(1.5, 3.5)
        self.age      = 0.0
        self.lifetime = random.uniform(2.5, 5.5)
        size = self.radius * 2 + 2
        self._surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self._surf, (240, 248, 255, 90),
                           (self.radius + 1, self.radius + 1), self.radius)
        pygame.draw.circle(self._surf, (255, 255, 255, 200),
                           (self.radius + 1, self.radius + 1), self.radius, 1)
        pygame.draw.circle(self._surf, (255, 255, 255, 230),
                           (self.radius - 1, self.radius - 1), max(1, self.radius // 3))

    def update(self, dt):
        self.age += dt
        self.y -= self.rise_speed * dt
        self.x -= tentacle_speed
        self.x += math.sin(self.age * self.sway_speed) * self.sway_amount * dt

    def draw(self, surface):
        surface.blit(self._surf, (int(self.x) - self.radius, int(self.y) - self.radius))

    def dead(self):
        return self.age >= self.lifetime or self.y + self.radius < 0 or self.x + self.radius < 0


class MapFragment:
    SIZE = (80, 80)

    def __init__(self, x, y):
        self.img  = pygame.transform.smoothscale(mapfrag2_img, self.SIZE)
        self.rect = self.img.get_rect(center=(x, y))
        self.collected = False
        self._age = 0.0
        self._bob = 0

    def update(self, dt):
        self._age   += dt
        self.rect.x -= tentacle_speed
        self._bob    = int(math.sin(self._age * 3.0) * 5)

    def draw(self, surface):
        if not self.collected:
            surface.blit(self.img, self.rect.move(0, self._bob))

    def check_collect(self, player_rect):
        if not self.collected and self.rect.colliderect(player_rect):
            self.collected = True
            return True
        return False

    def offscreen(self):
        return self.rect.right < 0


class MenuButton:
    PAD_X, PAD_Y = 48, 14
    NORMAL_COL  = (20,  60, 100, 210)
    HOVER_COL   = (40, 120, 180, 230)
    BORDER_COL  = (100, 200, 255, 255)
    TEXT_COL    = (220, 240, 255)
    TEXT_HOV    = (255, 255, 255)

    def __init__(self, label, center):
        self.label = label
        self._font = pygame.font.SysFont(None, 40)
        self._surf = self._font.render(label, True, self.TEXT_COL)
        tw, th     = self._surf.get_size()
        self.rect  = pygame.Rect(0, 0, tw + self.PAD_X * 2, th + self.PAD_Y * 2)
        self.rect.center = center

    def draw(self, surface, hover=False):
        col = self.HOVER_COL if hover else self.NORMAL_COL
        s   = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        s.fill(col)
        pygame.draw.rect(s, self.BORDER_COL, s.get_rect(), 2, border_radius=8)
        surface.blit(s, self.rect.topleft)
        tcol = self.TEXT_HOV if hover else self.TEXT_COL
        ts   = self._font.render(self.label, True, tcol)
        surface.blit(ts, ts.get_rect(center=self.rect.center))

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


def run_options():
    """Options submenu. Returns 'quit_app' if the window was closed while
    this menu was open (propagated up through run_pause_menu), otherwise
    returns None on Back/ESC."""
    global music_volume, sfx_volume
    options_clock = pygame.time.Clock()
    title_font    = pygame.font.SysFont(None, 72)
    label_font    = pygame.font.SysFont(None, 40)
    hint_font     = pygame.font.SysFont(None, 26)
    back_btn      = MenuButton("Back", (WIDTH // 2, HEIGHT - 70))

    SLIDER_X = WIDTH // 2 - 100
    SLIDER_W = 200
    SLIDER_H = 8
    HANDLE_R = 10
    MUSIC_Y  = 220
    SFX_Y    = 310
    dragging_music = False
    dragging_sfx   = False

    def vol_to_x(v):
        return int(SLIDER_X + v * SLIDER_W)

    def draw_slider(y, volume, label):
        lbl = label_font.render(label, True, (200, 230, 255))
        screen.blit(lbl, lbl.get_rect(right=SLIDER_X - 14, centery=y))
        pygame.draw.rect(screen, (60, 80, 120),
                         (SLIDER_X, y - SLIDER_H // 2, SLIDER_W, SLIDER_H), border_radius=4)
        fill_w = int(volume * SLIDER_W)
        if fill_w > 0:
            pygame.draw.rect(screen, (80, 180, 255),
                             (SLIDER_X, y - SLIDER_H // 2, fill_w, SLIDER_H), border_radius=4)
        hx = vol_to_x(volume)
        pygame.draw.circle(screen, (255, 255, 255), (hx, y), HANDLE_R)
        pygame.draw.circle(screen, (80, 180, 255),  (hx, y), HANDLE_R, 2)
        pct = label_font.render(f"{int(volume * 100)}%", True, (160, 190, 140))
        screen.blit(pct, pct.get_rect(left=SLIDER_X + SLIDER_W + 14, centery=y))

    while True:
        dt    = options_clock.tick(60) / 1000
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit_app'
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn.is_hovered(mouse):
                    return
                if math.hypot(mouse[0] - vol_to_x(music_volume), mouse[1] - MUSIC_Y) <= HANDLE_R + 4:
                    dragging_music = True
                if math.hypot(mouse[0] - vol_to_x(sfx_volume), mouse[1] - SFX_Y) <= HANDLE_R + 4:
                    dragging_sfx = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging_music = False
                dragging_sfx   = False
            if event.type == pygame.MOUSEMOTION:
                if dragging_music:
                    music_volume = max(0.0, min(1.0, (mouse[0] - SLIDER_X) / SLIDER_W))
                    pygame.mixer.music.set_volume(music_volume)
                if dragging_sfx:
                    sfx_volume = max(0.0, min(1.0, (mouse[0] - SLIDER_X) / SLIDER_W))
                    ding_sound.set_volume(sfx_volume)

        draw_background(screen, 0)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 8, 25, 160))
        screen.blit(overlay, (0, 0))

        title_s = title_font.render("OPTIONS", True, (120, 220, 255))
        screen.blit(title_s, title_s.get_rect(midtop=(WIDTH // 2, 30)))

        draw_slider(MUSIC_Y, music_volume, "Music:")
        draw_slider(SFX_Y,   sfx_volume,   "SFX:")

        # stub row
        ks = label_font.render("Window:", True, (200, 230, 255))
        vs = label_font.render("1000 x 600", True, (160, 190, 140))
        screen.blit(ks, ks.get_rect(right=WIDTH // 2 - 20, centery=410))
        screen.blit(vs, vs.get_rect(left=WIDTH  // 2 + 20, centery=410))

        back_btn.draw(screen, back_btn.is_hovered(mouse))
        hint = hint_font.render("ESC to go back", True, (120, 140, 160))
        screen.blit(hint, (14, HEIGHT - 28))
        pygame.display.flip()


def run_pause_menu():
    """Returns one of:
      'resume'      - player chose to resume (ESC/P or Resume button)
      'quit_to_menu'- player clicked the Quit button (return to main menu)
      'quit_app'    - the window was closed while paused (full app exit)
    """
    frozen = screen.copy()
    cx = WIDTH  // 2
    cy = HEIGHT // 2

    btn_resume  = MenuButton("Resume",  (cx, cy - 10))
    btn_options = MenuButton("Options", (cx, cy + 60))
    btn_quit    = MenuButton("Quit",    (cx, cy + 130))
    buttons     = [btn_resume, btn_options, btn_quit]

    pause_clock = pygame.time.Clock()
    pulse       = 0.0
    title_font  = pygame.font.SysFont(None, 72)
    hint_font   = pygame.font.SysFont(None, 26)

    while True:
        dt    = pause_clock.tick(60) / 1000
        pulse += dt * 2.0
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit_app'
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    return 'resume'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_resume.is_hovered(mouse):
                    return 'resume'
                if btn_options.is_hovered(mouse):
                    options_result = run_options()
                    if options_result == 'quit_app':
                        return 'quit_app'
                if btn_quit.is_hovered(mouse):
                    return 'quit_to_menu'

        screen.blit(frozen, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 8, 25, 175))
        screen.blit(overlay, (0, 0))

        panel_w, panel_h = 420, 360
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((10, 30, 65, 210))
        pygame.draw.rect(panel, (80, 180, 255, 180), (0, 0, panel_w, panel_h), 2, border_radius=14)
        screen.blit(panel, panel.get_rect(center=(cx, cy)))

        glow_a = int(80 + 40 * sin(pulse))
        glow   = pygame.Surface((320, 70), pygame.SRCALPHA)
        glow.fill((40, 120, 200, glow_a))
        screen.blit(glow, glow.get_rect(center=(cx, cy - 90)))

        title_s = title_font.render("PAUSED", True, (255, 255, 255))
        screen.blit(title_s, title_s.get_rect(center=(cx, cy - 90)))

        for btn in buttons:
            btn.draw(screen, btn.is_hovered(mouse))

        hint = hint_font.render("ESC / P  to resume", True, (130, 170, 200))
        screen.blit(hint, hint.get_rect(midbottom=(cx, HEIGHT - 14)))
        pygame.display.flip()


def run_level_complete_sequence(frozen_frame):
    """Runs the map-piecing-together cutscene. Returns 'quit' if the window
    was closed during the cutscene, otherwise returns None once the player
    presses a key/click to dismiss the final frame."""
    seq_clock  = pygame.time.Clock()
    cx, cy     = WIDTH // 2, HEIGHT // 2
    title_font = pygame.font.SysFont(None, 68)
    hint_font  = pygame.font.SysFont(None, 28)

    DISPLAY_SIZE = (340, 340)
    FULL_SIZE    = (480, 480)
    FRAG_SIZE    = (220, 220)

    frag1_join  = pygame.transform.smoothscale(mapfrag1_img, FRAG_SIZE)
    frag2_join  = pygame.transform.smoothscale(mapfrag2_img, FRAG_SIZE)
    fullmap_big = pygame.transform.smoothscale(fullmap_img,  FULL_SIZE)

    def draw_frozen():
        screen.blit(frozen_frame, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 8, 25, 200))
        screen.blit(ov, (0, 0))

    # phase 1: frag2 enlarges
    t = 0.0
    PHASE1_DUR = 1.8
    while t < PHASE1_DUR:
        dt = seq_clock.tick(60) / 1000
        t += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
        progress = min(t / PHASE1_DUR, 1.0)
        ease     = 1 - (1 - progress) ** 3
        size     = max(1, int(40 + ease * (DISPLAY_SIZE[0] - 40)))
        scaled   = pygame.transform.smoothscale(mapfrag2_img, (size, size))
        draw_frozen()
        screen.blit(scaled, scaled.get_rect(center=(cx, cy - 30)))
        title_s = title_font.render("Level 2 Complete!", True, (50, 220, 50))
        title_s.set_alpha(int(255 * min(t / 0.6, 1.0)))
        screen.blit(title_s, title_s.get_rect(center=(cx, cy + DISPLAY_SIZE[1] // 2 - 10)))
        pygame.display.flip()

    # phase 2: both frags slide in and join
    t = 0.0
    PHASE2_DUR = 2.0
    gap = 8
    while t < PHASE2_DUR:
        dt = seq_clock.tick(60) / 1000
        t += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
        progress = min(t / PHASE2_DUR, 1.0)
        ease     = 1 - (1 - progress) ** 3
        joined_left_x  = cx - FRAG_SIZE[0] - gap // 2
        joined_right_x = cx + gap // 2
        frag2_x = int(-FRAG_SIZE[0]  + ease * (joined_left_x  - (-FRAG_SIZE[0])))
        frag1_x = int(WIDTH           + ease * (joined_right_x - WIDTH))
        frag_y  = cy - FRAG_SIZE[1] // 2
        draw_frozen()
        screen.blit(frag2_join, (frag2_x, frag_y))
        screen.blit(frag1_join, (frag1_x, frag_y))
        title_s = title_font.render("Level 2 Complete!", True, (50, 220, 50))
        screen.blit(title_s, title_s.get_rect(center=(cx, cy + FRAG_SIZE[1] // 2 + 20)))
        pygame.display.flip()

    # phase 3: fullmap grows in then waits
    t       = 0.0
    GROW    = 1.2
    waiting = False
    while True:
        dt = seq_clock.tick(60) / 1000
        if not waiting:
            t += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                if waiting:
                    return
        draw_frozen()
        if not waiting:
            progress = min(t / GROW, 1.0)
            ease     = 1 - (1 - progress) ** 3
            size     = max(1, int(40 + ease * FULL_SIZE[0]))
            scaled   = pygame.transform.smoothscale(fullmap_img, (size, size))
            screen.blit(scaled, scaled.get_rect(center=(cx, cy)))
            if progress >= 1.0:
                waiting = True
        else:
            screen.blit(fullmap_big, fullmap_big.get_rect(center=(cx, cy)))
            hint = hint_font.render("Press any key to continue", True, (200, 220, 255))
            screen.blit(hint, hint.get_rect(midbottom=(cx, HEIGHT - 14)))
        pygame.display.flip()


def draw_background(surface, bg_x):
    if background is not None:
        surface.blit(background, (bg_x, 0))
        surface.blit(background, (bg_x + WIDTH, 0))


def _draw_panel(surface, x, y, w, h, alpha=200, radius=10):
    """Dark frosted panel with a subtle blue rim — copied from level1."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (8, 18, 45, alpha),  (0, 0, w, h), border_radius=radius)
    pygame.draw.rect(s, (60, 140, 220, 160), (0, 0, w, h), 2, border_radius=radius)
    surface.blit(s, (x, y))


def _draw_bar(surface, x, y, w, h, ratio, fill_col, bg_col=(30, 30, 55),
              border_col=(180, 210, 255), radius=6):
    """Generic rounded progress bar — copied from level1."""
    pygame.draw.rect(surface, bg_col,    (x, y, w, h), border_radius=radius)
    fw = max(0, round(w * ratio))
    if fw:
        pygame.draw.rect(surface, fill_col, (x, y, fw, h), border_radius=radius)
    pygame.draw.rect(surface, border_col, (x, y, w, h), 2, border_radius=radius)


def draw_oxygen_bar(surface, oxygen, max_oxygen):
    """
    Oxygen bar styled exactly like level1's oxygen bar.
    Positioned bottom-left.
    """
    small_font_o2 = pygame.font.SysFont("arial", 22)
    o2_bar_w, o2_bar_h = 200, 16
    o2_bar_x, o2_bar_y = 16, HEIGHT - 70
    o2_ratio = oxygen / max_oxygen if max_oxygen > 0 else 0.0
    o2_col   = (0, 200, 255) if o2_ratio > 0.3 else (255, 80, 80)
    _draw_panel(surface, o2_bar_x - 10, o2_bar_y - 30, o2_bar_w + 20, o2_bar_h + 42, alpha=180, radius=10)
    _draw_bar(surface, o2_bar_x, o2_bar_y, o2_bar_w, o2_bar_h, o2_ratio, o2_col)
    o2_lbl = small_font_o2.render("OXYGEN", True, (180, 230, 255))
    surface.blit(o2_lbl, o2_lbl.get_rect(midbottom=(o2_bar_x + o2_bar_w // 2, o2_bar_y - 4)))
    # flashing low-oxygen warning
    if o2_ratio < 0.25 and int(pygame.time.get_ticks() / 400) % 2 == 0:
        warn = small_font_o2.render("LOW OXYGEN!", True, (255, 80, 80))
        surface.blit(warn, warn.get_rect(midleft=(o2_bar_x + o2_bar_w + 10, o2_bar_y + o2_bar_h // 2)))


def draw_text_center(surface, text, font, color, y):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(WIDTH // 2, y))
    surface.blit(rendered, rect)


def reset_game():
    Diver        = diver()
    Tentacles    = [Tentacle(WIDTH + 100)]
    score        = 0
    bg_x         = 0
    map_fragment = None
    oxygen_system = OxygenSystem(WIDTH, HEIGHT, image_path=os.path.join(IMAGES_DIR, "o2 tank.png"),
                                  tentacle_gap=tentacle_gap, ground_height=Ground_height)
    bubbles = [Bubble(random.randint(0, WIDTH), HEIGHT - Ground_height) for _ in range(6)]
    return Diver, Tentacles, score, oxygen_system, bg_x, bubbles, map_fragment


def run_level2(screen, music_volume=0.6, sfx_volume=0.7):
    """Runs level 2 to completion.

    Returns one of "next" (level complete), "menu" (player quit to the main
    menu from the pause menu), or "quit" (the window was closed). Never
    calls pygame.quit()/sys.exit() itself — the caller (main.py) owns the
    pygame lifecycle.
    """
    global tentacle_spawn_ms, tentacle_speed
    global tentacle, tentacle_ceiling, background
    global mapfrag1_img, mapfrag2_img, fullmap_img
    global ding_sound, diver_frames

    # `screen`, `music_volume` and `sfx_volume` are parameters here, which
    # shadows the module-level globals of the same name for the rest of this
    # function. Other top-level functions in this module (run_options,
    # run_pause_menu, run_level_complete_sequence, draw_background, the
    # diver/Tentacle/MapFragment classes, ...) read those names as module
    # globals, so push the incoming values into the module namespace here.
    globals()['screen'] = screen
    globals()['music_volume'] = music_volume
    globals()['sfx_volume'] = sfx_volume

    # ---- load all level-2 assets now that pygame is guaranteed to be
    # initialized (this used to happen at import time, which is unsafe). ----
    tentacle = pygame.image.load(os.path.join(IMAGES_DIR, "newredtentacle.png"))
    tentacle = pygame.transform.flip(tentacle, True, False)
    tentacle_ceiling = pygame.transform.flip(tentacle, False, True)
    background = pygame.image.load(os.path.join(IMAGES_DIR, "cave.png"))
    background = pygame.transform.smoothscale(background, (WIDTH, HEIGHT))

    mapfrag1_img = pygame.image.load(os.path.join(IMAGES_DIR, "mapfrag1.png")).convert_alpha()
    mapfrag2_img = pygame.image.load(os.path.join(IMAGES_DIR, "mapfrag2.png")).convert_alpha()
    fullmap_img  = pygame.image.load(os.path.join(IMAGES_DIR, "fullmap.png")).convert_alpha()

    # background music
    pygame.mixer.music.load(os.path.join(AUDIO_DIR, "soundlevel2.mp3"))
    pygame.mixer.music.set_volume(music_volume)
    pygame.mixer.music.play(-1)

    # sound effects
    ding_sound = pygame.mixer.Sound(os.path.join(AUDIO_DIR, "dingsound.mp3"))
    ding_sound.set_volume(sfx_volume)

    diver_frames = [
        _load_diver_frame(os.path.join(IMAGES_DIR, "animation1d.png")),
        _load_diver_frame(os.path.join(IMAGES_DIR, "animation2d.png")),
        _load_diver_frame(os.path.join(IMAGES_DIR, "animation3d.png")),
        _load_diver_frame(os.path.join(IMAGES_DIR, "animation4d.png")),
        _load_diver_frame(os.path.join(IMAGES_DIR, "animation5d.png")),
    ]

    clock      = pygame.time.Clock()
    font_big   = pygame.font.SysFont(None, 64)
    font_small = pygame.font.SysFont(None, 32)

    def _show_level_complete_screen():
        """Simple 'press SPACE to continue' screen shown after the level
        complete cutscene finishes. Matches the cutscene's font/colors."""
        hint_col = (200, 220, 255)
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return "quit"
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                    return "next"
            draw_text_center(screen, "LEVEL COMPLETE", font_big, (50, 220, 50), HEIGHT // 2 - 30)
            draw_text_center(screen, "Press SPACE to continue", font_small, hint_col, HEIGHT // 2 + 20)
            pygame.display.flip()

    Diver, Tentacles, score, oxygen_system, bg_x, bubbles, map_fragment = reset_game()
    oxygen_system.set_sfx_volume(sfx_volume)
    game_over      = False
    level_complete = False
    started        = False
    elapsed        = 0.0   # seconds since the game started (pausing doesn't count)

    last_tentacle_time = pygame.time.get_ticks()
    running = True

    while running:
        dt = clock.tick(FPS) / 1000
        swim_pressed = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    swim_pressed = True
                if event.key == pygame.K_ESCAPE and started and not game_over and not level_complete:
                    result = run_pause_menu()
                    if result == 'quit_app':
                        return "quit"
                    if result == 'quit_to_menu':
                        return "menu"
                    # 'resume' — sync any slider changes made in the options
                    # menu back to the sfx-driven systems (read the live
                    # module-global value since it may have changed there).
                    oxygen_system.set_sfx_volume(globals()['sfx_volume'])
                    clock.tick(FPS)
                    last_tentacle_time = pygame.time.get_ticks()
                if event.key == pygame.K_r and game_over:
                    Diver, Tentacles, score, oxygen_system, bg_x, bubbles, map_fragment = reset_game()
                    oxygen_system.set_sfx_volume(globals()['sfx_volume'])
                    last_tentacle_time = pygame.time.get_ticks()
                    game_over      = False
                    level_complete = False
                    started        = False
                    elapsed        = 0.0
                    tentacle_speed = tentacle_speed_base
            if event.type == pygame.MOUSEBUTTONDOWN:
                swim_pressed = True

        if swim_pressed and not game_over and not level_complete:
            if not started:
                last_tentacle_time = pygame.time.get_ticks()
            started = True
            Diver.swim()

        if not game_over and not level_complete and started:
            elapsed += dt

            # ── difficulty ramp ───────────────────────────────────────────
            # difficulty goes from 1.0 at start to 2.0 at 90 seconds, capped there
            difficulty = 1.0 + min(1.0, elapsed / 90.0)

            # scroll speed: 4 → 8 over 90 s
            tentacle_speed = tentacle_speed_base * difficulty

            # spawn interval: 1000-2000 ms → 500-1000 ms over 90 s
            spawn_scale = 1.0 / difficulty   # shrinks interval as difficulty grows
            current_spawn_min = int(tentacle_spawn_min * spawn_scale)
            current_spawn_max = int(tentacle_spawn_max * spawn_scale)

            # oxygen drain: 5 → 10 per second over 90 s
            oxygen_system.drain_per_second = 5.0 * difficulty
            # ─────────────────────────────────────────────────────────────

            Diver.update(dt)

            bg_x -= tentacle_speed
            if bg_x <= -WIDTH:
                bg_x = 0

            for b in bubbles:
                b.update(dt)
            bubbles = [b for b in bubbles if not b.dead()]
            if random.random() < 3 * dt:
                bubbles.append(Bubble(Diver.x + random.randint(-20, 5),
                                      Diver.y + random.randint(-8, 8)))
            if random.random() < 1 * dt:
                bubbles.append(Bubble(random.randint(0, WIDTH), HEIGHT - Ground_height))

            now = pygame.time.get_ticks()
            if now - last_tentacle_time > tentacle_spawn_ms:
                Tentacles.append(Tentacle(WIDTH + 20))
                last_tentacle_time = now
                tentacle_spawn_ms = random.randint(current_spawn_min, current_spawn_max)

            for t in Tentacles:
                t.update()
            Tentacles[:] = [t for t in Tentacles if not t.offscreen()]

            for t in Tentacles:
                if not t.passed and t.x + t.width < Diver.x:
                    t.passed = True
                    score += 1
                    ding_sound.play()   # play ding on every point
                    if score >= 30 and map_fragment is None:
                        map_fragment = MapFragment(Diver.x + 300, Diver.y)

            if map_fragment and not map_fragment.collected:
                map_fragment.update(dt)
                if map_fragment.check_collect(Diver.get_rect()):
                    draw_background(screen, bg_x)
                    for b in bubbles:
                        b.draw(screen)
                    for t in Tentacles:
                        t.draw(screen)
                    Diver.draw(screen)
                    pygame.display.flip()
                    frozen = screen.copy()
                    seq_result = run_level_complete_sequence(frozen)
                    if seq_result == 'quit':
                        return "quit"
                    return _show_level_complete_screen()

            Diver_rect = Diver.get_rect()
            if Diver.y - Diver.radius <= 0 or Diver.y + Diver.radius >= HEIGHT - Ground_height:
                game_over = True
            for t in Tentacles:
                if t.check_collision(Diver_rect):
                    game_over = True

            if oxygen_system.update(dt, Diver.get_rect(), scroll_speed=tentacle_speed,
                                     tentacles=Tentacles):
                game_over = True

        draw_background(screen, bg_x)
        for b in bubbles:
            b.draw(screen)
        for t in Tentacles:
            t.draw(screen)
        if map_fragment and not map_fragment.collected:
            map_fragment.draw(screen)
        Diver.draw(screen)
        oxygen_system.draw(screen)
        draw_oxygen_bar(screen, oxygen_system.oxygen, oxygen_system.max_oxygen)

        draw_text_center(screen, str(score), font_big, (255, 255, 255), 60)

        if not started and not game_over:
            draw_text_center(screen, "Press SPACE to start", font_small, TEXT_COLOR, HEIGHT // 2)

        if game_over:
            draw_text_center(screen, "Game Over",          font_big,   (200, 30, 30), HEIGHT // 2 - 30)
            draw_text_center(screen, f"Score: {score}",    font_small, TEXT_COLOR,    HEIGHT // 2 + 15)
            draw_text_center(screen, "Press R to restart", font_small, TEXT_COLOR,    HEIGHT // 2 + 50)

        pygame.display.flip()

    return "quit"


if __name__ == "__main__":
    pygame.init()
    pygame.mixer.init()
    _screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Level 2")
    run_level2(_screen)
    pygame.quit()
