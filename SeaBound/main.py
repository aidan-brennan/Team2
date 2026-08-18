import pygame
import sys
import os
from random import uniform
from math import sin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# pygame must be initialised — with a display Surface already created —
# *before* the level modules are imported: lvl3.py loads some of its art
# (via .convert()/.convert_alpha(), which need a display mode set) and sound
# effects at module import time (see its own comments). main.py is the
# single owner of pygame's lifecycle for the whole app, so this initial
# setup happens here rather than only inside main(). main() below sets the
# display mode again for each screen/level, so this is just a bootstrap size.
pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()
pygame.display.set_mode((1280, 720))

from lvl1 import run_level1
from lvl2 import run_level2
from lvl3 import run_level3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "Images")
AUDIO_DIR = os.path.join(BASE_DIR, "Audio")

LEVELS = [
    (run_level1, (1280, 720)),
    (run_level2, (1000, 600)),
    (run_level3, (1000, 600)),
]

# The main menu / options / credits screens always run at the level-1 window
# size — main() switches back to this size before showing them.
MENU_WIDTH, MENU_HEIGHT = LEVELS[0][1]

music_volume = 0.6
sfx_volume = 0.7

# ---------------------------------------------------------------------------
# Fonts — created inside main() once pygame.font has been initialised.
# ---------------------------------------------------------------------------
menu_title_font   = None
menu_button_font  = None
menu_small_font   = None
credits_font      = None
credits_role_font = None


def _init_fonts():
    global menu_title_font, menu_button_font, menu_small_font
    global credits_font, credits_role_font
    menu_title_font   = pygame.font.SysFont("arial", 80, bold=True)
    menu_button_font  = pygame.font.SysFont("arial", 38, bold=True)
    menu_small_font   = pygame.font.SysFont("arial", 26)
    credits_font      = pygame.font.SysFont("arial", 30)
    credits_role_font = pygame.font.SysFont("arial", 22)


# ---------------------------------------------------------------------------
# Menu art — top crop of web_back.png, title.png, and the shark swim frames
# used to animate MenuShark. Loaded once inside main().
# ---------------------------------------------------------------------------
def _load_or_placeholder(path, placeholder_maker, alpha=True):
    try:
        surf = pygame.image.load(path)
        return surf.convert_alpha() if alpha else surf.convert()
    except (pygame.error, FileNotFoundError) as e:
        print(f"[art] couldn't load '{path}' ({e}) - using placeholder art instead.")
        return placeholder_maker()


def _make_shark_placeholder():
    surf = pygame.Surface((120, 60), pygame.SRCALPHA)
    pygame.draw.polygon(surf, (100, 115, 130),
                         [(0, 30), (30, 10), (100, 15), (120, 30), (100, 45), (30, 50)])
    pygame.draw.circle(surf, (240, 245, 250), (26, 24), 4)
    return surf


def _make_background_placeholder():
    surf = pygame.Surface((MENU_WIDTH, MENU_HEIGHT))
    surf.fill((6, 30, 60))
    return surf


menu_bg_surf   = None
menu_title_img = None
_shark_frames  = None


def _load_menu_art():
    global menu_bg_surf, menu_title_img, _shark_frames

    # background — top crop of web_back.png scaled to fill the menu window
    try:
        raw = pygame.image.load(os.path.join(IMAGES_DIR, "web_back.png")).convert()
        crop_h = min(raw.get_height(), round(raw.get_width() * MENU_HEIGHT / MENU_WIDTH))
        cropped = raw.subsurface((0, 0, raw.get_width(), crop_h))
        menu_bg_surf = pygame.transform.smoothscale(cropped, (MENU_WIDTH, MENU_HEIGHT))
    except (pygame.error, FileNotFoundError) as e:
        print(f"[art] couldn't load 'web_back.png' ({e}) - using plain background instead.")
        menu_bg_surf = _make_background_placeholder()

    # title image
    try:
        raw = pygame.image.load(os.path.join(IMAGES_DIR, "title.png")).convert_alpha()
        target_w = 500
        scale = target_w / raw.get_width()
        menu_title_img = pygame.transform.smoothscale(
            raw, (target_w, max(1, round(raw.get_height() * scale))))
    except (pygame.error, FileNotFoundError) as e:
        print(f"[art] couldn't load 'title.png' ({e}) - using text fallback.")
        menu_title_img = None

    # shark swim frames (reuses the same source art as lvl1's Shark class)
    frames = []
    for name in ("shark1.png", "sharkmov1.png", "sharkmov2.png"):
        raw = _load_or_placeholder(os.path.join(IMAGES_DIR, name), _make_shark_placeholder)
        w, h = raw.get_size()
        frames.append(pygame.transform.smoothscale(raw, (round(w * 1.6), round(h * 1.6))))
    _shark_frames = frames


def _draw_menu_bg(screen):
    """Draw the animated menu background using web_back.png (top crop)."""
    screen.blit(menu_bg_surf, (0, 0))
    overlay = pygame.Surface((MENU_WIDTH, MENU_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 8, 22, 110))
    screen.blit(overlay, (0, 0))


# ---------------------------------------------------------------------------
# Animated menu shark (swims across the screen)
# ---------------------------------------------------------------------------
class MenuShark:
    SPEED = 180

    def __init__(self):
        self._reset(start_offscreen=False)

    def _reset(self, start_offscreen=True):
        self.y = uniform(MENU_HEIGHT * 0.25, MENU_HEIGHT * 0.75)
        self.x = -200 if start_offscreen else uniform(0, MENU_WIDTH)
        self._frame_idx = 0
        self._frame_timer = 0.0

    def update(self, dt):
        self.x += self.SPEED * dt
        self._frame_timer += dt
        if self._frame_timer >= 1.0 / 8:   # 8 fps
            self._frame_timer = 0.0
            self._frame_idx = (self._frame_idx + 1) % len(_shark_frames)
        if self.x > MENU_WIDTH + 200:
            self._reset(start_offscreen=True)

    def draw(self, screen):
        frame = _shark_frames[self._frame_idx]
        screen.blit(frame, (int(self.x - frame.get_width() // 2),
                             int(self.y - frame.get_height() // 2)))


# ---------------------------------------------------------------------------
# Button helper — same look as the original lvl1.py MenuButton, adapted to
# take the target surface explicitly instead of relying on a module global.
# ---------------------------------------------------------------------------
class MenuButton:
    PAD_X, PAD_Y = 56, 16

    def __init__(self, label, center):
        self.label = label
        tw, th = menu_button_font.size(label)
        self.rect = pygame.Rect(0, 0, tw + self.PAD_X * 2, th + self.PAD_Y * 2)
        self.rect.center = center

    def draw(self, screen, hover=False):
        r = self.rect
        # drop shadow
        shadow = pygame.Surface((r.w + 4, r.h + 4), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 80), (4, 4, r.w, r.h), border_radius=10)
        screen.blit(shadow, (r.x - 2, r.y - 2))

        # main body — two-tone gradient via two rects
        body = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        if hover:
            top_col = (50, 130, 200, 235)
            bot_col = (25, 80, 145, 235)
            rim_col = (120, 210, 255, 255)
        else:
            top_col = (18, 55, 110, 210)
            bot_col = (10, 30, 70, 210)
            rim_col = (70, 150, 220, 200)

        pygame.draw.rect(body, top_col, (0, 0, r.w, r.h // 2), border_radius=10)
        pygame.draw.rect(body, bot_col, (0, r.h // 2, r.w, r.h // 2), border_radius=10)
        pygame.draw.rect(body, bot_col, (0, r.h // 2 - 10, r.w, 10))

        if hover:
            pygame.draw.line(body, (180, 230, 255, 120), (12, 3), (r.w - 12, 3), 1)

        pygame.draw.rect(body, rim_col, (0, 0, r.w, r.h), 2, border_radius=10)
        screen.blit(body, r.topleft)

        tcol = (255, 255, 255) if hover else (200, 230, 255)
        sh_s = menu_button_font.render(self.label, True, (0, 0, 0))
        sh_s.set_alpha(80)
        screen.blit(sh_s, sh_s.get_rect(center=(r.centerx + 1, r.centery + 1)))
        ts = menu_button_font.render(self.label, True, tcol)
        screen.blit(ts, ts.get_rect(center=r.center))

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


# ---------------------------------------------------------------------------
# Credits data
# ---------------------------------------------------------------------------
_NAMES = ["Fionn Murphy", "Matthew Shine", "Max Nolan", "Aidan Brennan"]

CREDITS_ENTRIES = [
    ("A game by", ""),
    ("", ""),
    (_NAMES[0],  "Developer"),
    ("", ""),
    (_NAMES[1],  "Developer"),
    ("", ""),
    (_NAMES[3],  "Developer"),
    ("", ""),
    (_NAMES[2],  "Developer"),
    ("", ""),
    (_NAMES[0],  "Story & Writing"),
    ("", ""),
    (_NAMES[1],  "Sound Design"),
    ("", ""),
    (_NAMES[3],  "UI / UX"),
    ("", ""),
    (_NAMES[0],  "Producer"),
    ("", ""),
    ("Special Thanks", ""),
    ("Everyone who played this far", ""),
    ("", ""),
    ("", ""),
    ("", ""),
]


def run_credits(screen):
    """Scrolling film-style credits. Returns 'quit' if the window was closed
    (so the caller can propagate it up to main()), otherwise returns None
    when the player presses ESC or clicks."""
    scroll_y = float(MENU_HEIGHT)
    scroll_speed = 55
    shark = MenuShark()
    clock2 = pygame.time.Clock()

    while True:
        dt = clock2.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                return None

        scroll_y -= scroll_speed * dt
        shark.update(dt)

        _draw_menu_bg(screen)
        shark.draw(screen)

        tc = menu_title_font.render("CREDITS", True, (120, 220, 255))
        screen.blit(tc, tc.get_rect(midtop=(MENU_WIDTH // 2, 20)))

        y = scroll_y
        LINE_H = 42
        for (name, role) in CREDITS_ENTRIES:
            if name:
                col = (255, 255, 255) if role else (160, 220, 255)
                ns = credits_font.render(name, True, col)
                screen.blit(ns, ns.get_rect(centerx=MENU_WIDTH // 2, top=y))
                if role:
                    rs = credits_role_font.render(role, True, (150, 190, 140))
                    screen.blit(rs, rs.get_rect(centerx=MENU_WIDTH // 2, top=y + 30))
                    y += LINE_H + 16
                else:
                    y += LINE_H
            else:
                y += LINE_H // 2

        if y < 0:
            return None

        for bar_y, bar_h in [(0, 80), (MENU_HEIGHT - 80, 80)]:
            for i in range(bar_h):
                pygame.draw.line(screen, (0, 10, 30),
                                  (0, bar_y + i), (MENU_WIDTH, bar_y + i))

        back = menu_small_font.render("ESC / click to return", True, (120, 140, 160))
        screen.blit(back, (14, MENU_HEIGHT - 28))
        pygame.display.update()


# ---------------------------------------------------------------------------
# Options — volume sliders adapted from lvl2.py's run_options() pattern.
# ---------------------------------------------------------------------------
def run_options(screen):
    """Options screen with Music/SFX volume sliders. Returns 'quit' if the
    window was closed, otherwise None when the player backs out."""
    global music_volume, sfx_volume

    clock2 = pygame.time.Clock()
    shark = MenuShark()
    back_btn = MenuButton("Back", (MENU_WIDTH // 2, MENU_HEIGHT - 80))

    SLIDER_X = MENU_WIDTH // 2 - 100
    SLIDER_W = 200
    SLIDER_H = 8
    HANDLE_R = 10
    MUSIC_Y = 300
    SFX_Y = 390
    dragging_music = False
    dragging_sfx = False

    def vol_to_x(v):
        return int(SLIDER_X + v * SLIDER_W)

    def draw_slider(y, volume, label):
        lbl = menu_button_font.render(label, True, (200, 230, 255))
        screen.blit(lbl, lbl.get_rect(right=SLIDER_X - 14, centery=y))
        pygame.draw.rect(screen, (60, 80, 120),
                          (SLIDER_X, y - SLIDER_H // 2, SLIDER_W, SLIDER_H), border_radius=4)
        fill_w = int(max(0.0, min(1.0, volume)) * SLIDER_W)
        if fill_w > 0:
            pygame.draw.rect(screen, (80, 180, 255),
                              (SLIDER_X, y - SLIDER_H // 2, fill_w, SLIDER_H), border_radius=4)
        hx = vol_to_x(volume)
        pygame.draw.circle(screen, (255, 255, 255), (hx, y), HANDLE_R)
        pygame.draw.circle(screen, (80, 180, 255), (hx, y), HANDLE_R, 2)
        pct = menu_small_font.render(f"{int(volume * 100)}%", True, (160, 220, 180))
        screen.blit(pct, pct.get_rect(left=SLIDER_X + SLIDER_W + 14, centery=y))

    while True:
        dt = clock2.tick(60) / 1000
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn.is_hovered(mouse):
                    return None
                if (mouse[0] - vol_to_x(music_volume)) ** 2 + (mouse[1] - MUSIC_Y) ** 2 <= (HANDLE_R + 4) ** 2:
                    dragging_music = True
                if (mouse[0] - vol_to_x(sfx_volume)) ** 2 + (mouse[1] - SFX_Y) ** 2 <= (HANDLE_R + 4) ** 2:
                    dragging_sfx = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging_music = False
                dragging_sfx = False
            if event.type == pygame.MOUSEMOTION:
                if dragging_music:
                    music_volume = max(0.0, min(1.0, (mouse[0] - SLIDER_X) / SLIDER_W))
                    pygame.mixer.music.set_volume(music_volume)
                if dragging_sfx:
                    sfx_volume = max(0.0, min(1.0, (mouse[0] - SLIDER_X) / SLIDER_W))

        shark.update(dt)
        _draw_menu_bg(screen)
        shark.draw(screen)

        title_s = menu_title_font.render("OPTIONS", True, (120, 220, 255))
        screen.blit(title_s, title_s.get_rect(midtop=(MENU_WIDTH // 2, 30)))

        draw_slider(MUSIC_Y, music_volume, "Music:")
        draw_slider(SFX_Y, sfx_volume, "SFX:")

        back_btn.draw(screen, back_btn.is_hovered(mouse))
        hint = menu_small_font.render("ESC to go back", True, (120, 140, 160))
        screen.blit(hint, (14, MENU_HEIGHT - 28))
        pygame.display.update()


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------
def run_main_menu(screen):
    """Animated start screen. Returns 'start' or 'quit'."""
    cx = MENU_WIDTH // 2
    btn_start = MenuButton("Start Game", (cx, 360))
    btn_options = MenuButton("Options", (cx, 450))
    btn_credits = MenuButton("Credits", (cx, 540))
    btn_quit = MenuButton("Quit", (cx, 630))
    buttons = [btn_start, btn_options, btn_credits, btn_quit]

    shark = MenuShark()
    shark2 = MenuShark()
    shark2.x = uniform(-400, -100)
    shark2.y = uniform(MENU_HEIGHT * 0.5, MENU_HEIGHT * 0.8)

    clock2 = pygame.time.Clock()
    pulse = 0.0

    while True:
        dt = clock2.tick(60) / 1000
        pulse += dt * 2.0
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_start.is_hovered(mouse):
                    return 'start'
                if btn_options.is_hovered(mouse):
                    if run_options(screen) == 'quit':
                        return 'quit'
                if btn_credits.is_hovered(mouse):
                    if run_credits(screen) == 'quit':
                        return 'quit'
                if btn_quit.is_hovered(mouse):
                    return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return 'start'
                if event.key == pygame.K_ESCAPE:
                    return 'quit'

        shark.update(dt)
        shark2.update(dt)

        _draw_menu_bg(screen)
        shark2.draw(screen)
        shark.draw(screen)

        if menu_title_img:
            bob_y = round(sin(pulse) * 5)
            t_rect = menu_title_img.get_rect(center=(cx, 155 + bob_y))

            sh = pygame.Surface(menu_title_img.get_size(), pygame.SRCALPHA)
            sh.blit(menu_title_img, (0, 0))
            sh.fill((0, 0, 0, 100), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(sh, (t_rect.x + 3, t_rect.y + 4))

            glow_a = int(50 + 30 * sin(pulse))
            glow_s = pygame.Surface((menu_title_img.get_width() + 40,
                                      menu_title_img.get_height() + 20), pygame.SRCALPHA)
            glow_s.fill((40, 140, 220, glow_a))
            screen.blit(glow_s, glow_s.get_rect(center=(cx, 155 + bob_y)))

            screen.blit(menu_title_img, t_rect)
        else:
            glow_a = int(80 + 40 * sin(pulse))
            glow_s = pygame.Surface((640, 120), pygame.SRCALPHA)
            glow_s.fill((40, 120, 200, glow_a))
            screen.blit(glow_s, glow_s.get_rect(center=(cx, 165)))
            t1 = menu_title_font.render("SEA", True, (255, 255, 255))
            t2 = menu_title_font.render("BOUND", True, (80, 210, 255))
            screen.blit(t1, t1.get_rect(center=(cx, 130)))
            screen.blit(t2, t2.get_rect(center=(cx, 210)))

        if int(pulse * 2) % 4 != 0:
            press_s = menu_small_font.render("Press ENTER or click Start Game", True, (200, 230, 255))
            screen.blit(press_s, press_s.get_rect(center=(cx, 225)))

        for btn in buttons:
            btn.draw(screen, btn.is_hovered(mouse))

        pygame.display.update()


# ---------------------------------------------------------------------------
# Win screen — shown once all levels have been completed.
# ---------------------------------------------------------------------------
def run_win_and_credits(screen):
    """Brief 'YOU WIN' splash (press any key/click to continue), followed by
    the credits. Returns 'quit' if the window was closed at any point,
    otherwise None."""
    clock2 = pygame.time.Clock()
    pulse = 0.0

    while True:
        dt = clock2.tick(60) / 1000
        pulse += dt * 2.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return run_credits(screen)

        _draw_menu_bg(screen)

        glow_a = int(90 + 40 * sin(pulse))
        glow_s = pygame.Surface((700, 140), pygame.SRCALPHA)
        glow_s.fill((40, 160, 120, glow_a))
        screen.blit(glow_s, glow_s.get_rect(center=(MENU_WIDTH // 2, MENU_HEIGHT // 2 - 40)))

        win_s = menu_title_font.render("YOU WIN!", True, (120, 240, 170))
        screen.blit(win_s, win_s.get_rect(center=(MENU_WIDTH // 2, MENU_HEIGHT // 2 - 40)))

        sub_s = menu_button_font.render("Thanks for playing SeaBound", True, (220, 235, 255))
        screen.blit(sub_s, sub_s.get_rect(center=(MENU_WIDTH // 2, MENU_HEIGHT // 2 + 30)))

        if int(pulse * 2) % 4 != 0:
            hint_s = menu_small_font.render("Press any key to continue", True, (200, 230, 255))
            screen.blit(hint_s, hint_s.get_rect(center=(MENU_WIDTH // 2, MENU_HEIGHT // 2 + 90)))

        pygame.display.update()


def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode(LEVELS[0][1])
    pygame.display.set_caption("SeaBound")

    _init_fonts()
    _load_menu_art()

    while True:
        screen = pygame.display.set_mode(LEVELS[0][1])
        choice = run_main_menu(screen)
        if choice == 'quit':
            break

        idx = 0
        while idx < len(LEVELS):
            func, size = LEVELS[idx]
            screen = pygame.display.set_mode(size)
            result = func(screen, music_volume, sfx_volume)
            if result == 'next':
                idx += 1
            elif result == 'menu':
                break
            else:  # 'quit'
                pygame.quit()
                sys.exit()

        if idx == len(LEVELS):
            screen = pygame.display.set_mode(LEVELS[0][1])
            if run_win_and_credits(screen) == 'quit':
                break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
