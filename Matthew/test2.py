import pygame
import random
import math
from os.path import join, dirname, abspath

pygame.init()

WIDTH  = 1000
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Deep Sea Diver – Fight the Pirate Crew")

clock = pygame.time.Clock()

# ------------------------------------------------------------------ #
#  PATHS                                                               #
# ------------------------------------------------------------------ #

BASE_DIR   = dirname(abspath(__file__))
IMAGES_DIR = join(BASE_DIR, "..", "Images")

def img(name):
    return join(IMAGES_DIR, name)

# ------------------------------------------------------------------ #
#  FONTS                                                               #
# ------------------------------------------------------------------ #

FONT_HUGE   = pygame.font.SysFont("impact",  90)
FONT_LARGE  = pygame.font.SysFont("impact",  52)
FONT_MEDIUM = pygame.font.SysFont("impact",  32)
FONT_SMALL  = pygame.font.SysFont("verdana", 20, bold=True)
FONT_TINY   = pygame.font.SysFont("verdana", 16)

# ------------------------------------------------------------------ #
#  COLOURS                                                             #
# ------------------------------------------------------------------ #

WHITE      = (255, 255, 255)
BLACK      = (  0,   0,   0)
YELLOW     = (255, 215,   0)
CYAN       = ( 80, 230, 255)
RED        = (220,  50,  50)
DARK_PANEL = (  0,  15,  35, 180)
GREEN      = ( 60, 200,  80)
ORANGE     = (255, 140,   0)

# ================================================================== #
#  GAME SETTINGS  – change these values to tweak the game             #
# ================================================================== #

# How far from the top of the screen Jerry can walk
TOP_BARRIER = 150

# Harpoon cooldown in frames (60 frames = 1 second at 60 fps)
# CHANGE THIS to make the harpoon fire faster or slower
SHOOT_COOLDOWN = 120

# ---------- HITBOX OFFSETS ----------
# These values trim the collision box so it matches the visible body
# rather than the full transparent image rectangle.
# Increase offset_x / offset_y to push the hitbox inward.
# Decrease hitbox_w / hitbox_h to make the hitbox smaller.

# Jerry (sprite is 85 x 110)
JERRY_HB_OFFSET_X = 15   # pixels from left edge of sprite
JERRY_HB_OFFSET_Y = 10   # pixels from top edge of sprite
JERRY_HB_W        = 55   # width  of the collision box  (was 85)
JERRY_HB_H        = 90   # height of the collision box  (was 110)

# Pirate (sprite is 150 x 120)
PIRATE_HB_OFFSET_X = 30   # pixels from left edge
PIRATE_HB_OFFSET_Y = 10   # pixels from top edge
PIRATE_HB_W        = 90   # width  of collision box  (was 150)
PIRATE_HB_H        = 100  # height of collision box  (was 120)

# Boss (sprite is 220 x 180)
BOSS_HB_OFFSET_X = 40    # pixels from left edge
BOSS_HB_OFFSET_Y = 15    # pixels from top edge
BOSS_HB_W        = 140   # width  of collision box  (was 220)
BOSS_HB_H        = 150   # height of collision box  (was 180)

# Harpoon collision box (the harpoon PNG is drawn at 150 x 50,
# but the actual spike is much narrower – use a slim rectangle)
HARPOON_HB_OFFSET_X = 0    # from left of drawn image
HARPOON_HB_OFFSET_Y = 15   # from top  of drawn image
HARPOON_HB_W        = 60   # width  of collision box
HARPOON_HB_H        = 20   # height of collision box

# Sword hitbox (extends in front of Jerry while attacking)
SWORD_OFFSET_X = 5    # how far ahead of Jerry's front edge
SWORD_W        = 55   # width  of the swing arc
SWORD_H        = 45   # height of the swing arc
SWORD_OFFSET_Y = 35   # vertical offset from top of Jerry sprite

# ---------- DEBUG FLAG ----------
# Set to True to see all collision boxes drawn on screen.
# Very useful for tweaking the values above.
# Set to False for normal play.
SHOW_HITBOXES = False


# ================================================================== #
#  IMAGES                                                              #
# ================================================================== #

background_img = pygame.transform.scale(
    pygame.image.load(img("shipwreck.png")).convert(),
    (WIDTH, HEIGHT)
)

# ------------------------------------------------------------------
#  WHY convert_alpha()?
#  pygame.image.load() gives you a Surface with whatever pixel format
#  is in the file.  Calling .convert_alpha() converts it to the same
#  format as the display surface AND keeps the alpha (transparency)
#  channel.  This makes blitting much faster because Pygame doesn't
#  need to convert pixel formats every frame.
#
#  WHY set_colorkey(WHITE)?
#  Some pixel-art PNGs were saved without proper transparency – the
#  background is painted solid white instead.  set_colorkey() tells
#  Pygame "treat every pixel that is exactly this colour as fully
#  transparent when drawing."  We use (255, 255, 255) = white.
#  IMPORTANT: this only removes EXACT white pixels.  Off-white pixels
#  that are part of Jerry's design are kept.
# ------------------------------------------------------------------

def load_sprite(filename, size):
    """Load a PNG, scale it, and make pure-white pixels transparent."""
    raw  = pygame.image.load(img(filename)).convert_alpha()
    raw  = pygame.transform.scale(raw, size)
    # Remove solid white backgrounds that some pixel-art exports produce.
    # This does NOT remove off-white pixels that are part of the sprite.
    raw.set_colorkey(WHITE)
    return raw

# Pre-load the two raw Jerry frames (facing RIGHT)
_jerry_r0 = load_sprite("walking_jerry.png",  (85, 110))
_jerry_r1 = load_sprite("walking_jerry1.png", (85, 110))

# ------------------------------------------------------------------
#  WHY pre-cache the flipped versions?
#  pygame.transform.flip() creates a brand-new Surface every time
#  it is called.  If we called it inside player.draw() every frame,
#  we'd create and throw away a Surface 60 times per second.
#  By creating the flipped copies ONCE here at startup and storing
#  them in a list, player.draw() just picks the right Surface from
#  the list – no transformation work at all during gameplay.
# ------------------------------------------------------------------

# Cache all 4 variants: [right-frame0, right-frame1, left-frame0, left-frame1]
#   Index 0 = right, frame 0
#   Index 1 = right, frame 1
#   Index 2 = left,  frame 0  (pre-flipped)
#   Index 3 = left,  frame 1  (pre-flipped)
JERRY_FRAMES = [
    _jerry_r0,
    _jerry_r1,
    pygame.transform.flip(_jerry_r0, True, False),
    pygame.transform.flip(_jerry_r1, True, False),
]

pirate_img = pygame.transform.scale(
    pygame.image.load(img("pirate.png")).convert_alpha(),
    (150, 120)
)

# Harpoon PNG – full drawn size is 150x50.
# The collision box is defined separately in GAME SETTINGS above.
harpoon_img_right = pygame.transform.scale(
    pygame.image.load(img("harpoon.png")).convert_alpha(),
    (150, 50)
)
# Pre-flip the harpoon for left-facing shots (same reason as Jerry)
harpoon_img_left = pygame.transform.flip(harpoon_img_right, True, False)

# Boss uses pirate art scaled up; swap the file path later for custom art
boss_img_raw = pygame.transform.scale(
    pygame.image.load(img("pirate.png")).convert_alpha(),
    (220, 180)
)


# ================================================================== #
#  HELPER FUNCTIONS                                                    #
# ================================================================== #

def draw_text(surface, text, font, colour, cx, cy,
              shadow=True, shadow_colour=(0, 0, 0), shadow_offset=3):
    rendered = font.render(text, True, colour)
    rect     = rendered.get_rect(center=(cx, cy))
    if shadow:
        shadow_surf = font.render(text, True, shadow_colour)
        surface.blit(shadow_surf, rect.move(shadow_offset, shadow_offset))
    surface.blit(rendered, rect)


def draw_panel(surface, x, y, w, h, colour=DARK_PANEL, radius=12):
    """Semi-transparent rounded rectangle panel."""
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 0))
    pygame.draw.rect(panel, colour, (0, 0, w, h), border_radius=radius)
    surface.blit(panel, (x, y))


def debug_rect(rect, colour=(0, 255, 0)):
    """Draw a collision box outline – only when SHOW_HITBOXES is True."""
    if SHOW_HITBOXES:
        pygame.draw.rect(screen, colour, rect, 2)


# ================================================================== #
#  PLAYER CLASS                                                        #
# ================================================================== #
#
#  HOW THE PLAYER CLASS WORKS
#  --------------------------
#  The Player stores its position as (self.x, self.y) – the TOP-LEFT
#  corner of the sprite rectangle.  Every frame:
#    1. move()         reads the keyboard and updates x/y
#    2. update_animation() swaps the sprite frame
#    3. update_attack()    counts down the sword timer
#    4. draw()         blits the correct sprite to the screen
#
#  The HITBOX (get_rect) is SMALLER than the sprite.  We add offsets
#  so the invisible transparent edges of the PNG don't count as solid.

class Player:

    def __init__(self, x, y):
        self.x      = x
        self.y      = y
        self.width  = 85    # full sprite width  (DO NOT change for hitbox)
        self.height = 110   # full sprite height (DO NOT change for hitbox)
        self.speed  = 5     # pixels per frame – CHANGE THIS to make Jerry faster/slower

        # Animation state
        self.frame_index  = 0      # 0 or 1 (which frame we're on)
        self.anim_timer   = 0      # counts up each frame
        self.anim_speed   = 8      # frames before swapping sprite (lower = faster walk cycle)
        self.facing_right = True   # True = facing right, False = facing left
        self.moving       = False  # True while any arrow key is held

        # Sword attack state
        self.attacking       = False
        self.attack_timer    = 0
        self.attack_cooldown = 0

    # ------------------------------------------------------------------
    #  CHOOSING THE CORRECT SPRITE FRAME
    #  We pick from the JERRY_FRAMES list we pre-cached above.
    #  facing_right=True  → indices 0 and 1
    #  facing_right=False → indices 2 and 3  (pre-flipped)
    #  This costs nothing at runtime – just an array lookup.
    # ------------------------------------------------------------------
    @property
    def image(self):
        if self.facing_right:
            return JERRY_FRAMES[self.frame_index]       # 0 or 1
        else:
            return JERRY_FRAMES[self.frame_index + 2]   # 2 or 3

    # ------------------------------------------------------------------
    #  MOVEMENT WITH NORMALISED DIAGONAL SPEED
    #  Without normalisation, holding RIGHT + DOWN gives you speed in
    #  both axes, so you travel diagonally at √2 ≈ 1.41× normal speed.
    #  To fix this we check if the player is moving in both axes at once
    #  and scale the step down by 1/√2 ≈ 0.707 so the total distance
    #  per frame is always equal to self.speed regardless of direction.
    # ------------------------------------------------------------------
    def move(self):
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0

        if keys[pygame.K_LEFT]:
            dx = -self.speed
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            dx = self.speed
            self.facing_right = True
        if keys[pygame.K_UP]:
            dy = -self.speed
        if keys[pygame.K_DOWN]:
            dy = self.speed

        # Normalise diagonal movement
        if dx != 0 and dy != 0:
            dx = int(dx * 0.707)
            dy = int(dy * 0.707)

        self.moving = (dx != 0 or dy != 0)
        self.x += dx
        self.y += dy

        # Screen boundary clamping
        self.x = max(0,           min(self.x, WIDTH  - self.width))
        self.y = max(TOP_BARRIER, min(self.y, HEIGHT - self.height))

    def update_animation(self):
        if self.moving:
            self.anim_timer += 1
            if self.anim_timer >= self.anim_speed:
                self.anim_timer  = 0
                self.frame_index = 1 - self.frame_index   # toggle 0 ↔ 1
        else:
            self.frame_index = 0   # snap back to idle frame when still

    def attack(self):
        if self.attack_cooldown == 0:
            self.attacking       = True
            self.attack_timer    = 10
            self.attack_cooldown = 25

    def update_attack(self):
        if self.attack_timer > 0:
            self.attack_timer -= 1
        else:
            self.attacking = False
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    # ------------------------------------------------------------------
    #  SWORD HITBOX
    #  The sword appears only while self.attacking is True.
    #  It sits just in front of Jerry's body, either to the right or
    #  left depending on which way he is facing.
    #  SWORD_W, SWORD_H, SWORD_OFFSET_X, SWORD_OFFSET_Y are all in
    #  the GAME SETTINGS block above – easy to tweak.
    # ------------------------------------------------------------------
    def get_sword_rect(self):
        if not self.attacking:
            return pygame.Rect(0, 0, 0, 0)

        if self.facing_right:
            # Place sword just beyond the right edge of Jerry's body hitbox
            sx = self.x + JERRY_HB_OFFSET_X + JERRY_HB_W + SWORD_OFFSET_X
        else:
            # Place sword just beyond the LEFT edge of Jerry's body hitbox
            sx = self.x + JERRY_HB_OFFSET_X - SWORD_W - SWORD_OFFSET_X

        sy = self.y + SWORD_OFFSET_Y
        return pygame.Rect(sx, sy, SWORD_W, SWORD_H)

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

        if self.attacking:
            sword_rect = self.get_sword_rect()
            if SHOW_HITBOXES:
                pygame.draw.rect(screen, YELLOW, sword_rect, 2)
            else:
                # Soft glow effect instead of a solid box during normal play
                glow = pygame.Surface((sword_rect.w, sword_rect.h), pygame.SRCALPHA)
                glow.fill((255, 255, 0, 80))
                screen.blit(glow, sword_rect.topleft)

        # Show Jerry's body hitbox when debugging
        debug_rect(self.get_rect(), (0, 255, 0))

    # ------------------------------------------------------------------
    #  BODY HITBOX
    #  Uses offsets so we only cover the visible body pixels.
    #  WHY SMALLER HITBOXES?
    #  In pixel-art games the sprite image always has transparent padding
    #  around the character.  Using the full image size means a pirate
    #  "hits" Jerry even when they are visually centimetres apart.
    #  Smaller hitboxes make the game feel fair and precise.
    # ------------------------------------------------------------------
    def get_rect(self):
        return pygame.Rect(
            self.x + JERRY_HB_OFFSET_X,
            self.y + JERRY_HB_OFFSET_Y,
            JERRY_HB_W,
            JERRY_HB_H
        )


# ================================================================== #
#  PIRATE CLASS                                                        #
# ================================================================== #
#
#  HOW THE PIRATE CLASS WORKS
#  --------------------------
#  Each Pirate has its own (x, y) position and chases the player by
#  comparing its x,y to the player's x,y and moving toward them one
#  step at a time.  The hitbox is smaller than the full 150x120 image
#  so collisions only trigger when the visible bodies actually overlap.

class Pirate:

    def __init__(self, x, y):
        self.x      = x
        self.y      = y
        self.width  = 150   # full sprite width
        self.height = 120   # full sprite height
        self.speed  = 2     # pixels per frame – CHANGE THIS to make pirates faster
        self.image  = pirate_img
        self.health = 1

    def move_towards_player(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        if dx > 0: self.x += self.speed
        elif dx < 0: self.x -= self.speed
        if dy > 0: self.y += self.speed
        elif dy < 0: self.y -= self.speed
        self.y = max(TOP_BARRIER, min(self.y, HEIGHT - self.height))

    def draw(self):
        screen.blit(self.image, (self.x, self.y))
        debug_rect(self.get_rect(), (255, 0, 0))   # red box when SHOW_HITBOXES=True

    def get_rect(self):
        # Smaller hitbox centred on the visible pirate body
        return pygame.Rect(
            self.x + PIRATE_HB_OFFSET_X,
            self.y + PIRATE_HB_OFFSET_Y,
            PIRATE_HB_W,
            PIRATE_HB_H
        )


# ================================================================== #
#  BOSS CLASS                                                          #
# ================================================================== #

BOSS_MAX_HP = 8

class Boss:
    """Bigger, tougher pirate.  Swap the image file later for custom art."""

    BAR_W = 220
    BAR_H = 18

    def __init__(self):
        self.width  = 220
        self.height = 180
        self.x      = WIDTH
        self.y      = HEIGHT // 2 - self.height // 2
        self.speed  = 1.5   # CHANGE THIS to make the boss faster
        self.hp     = BOSS_MAX_HP

        # Build the red-tinted surface ONCE in __init__, not every frame
        surf = boss_img_raw.copy()
        tint = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        tint.fill((180, 0, 0, 60))
        surf.blit(tint, (0, 0))
        self._image = surf   # stored, never recreated

    def move_towards_player(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        if dx > 0: self.x += self.speed
        elif dx < 0: self.x -= self.speed
        if dy > 0: self.y += self.speed
        elif dy < 0: self.y -= self.speed
        self.y = max(TOP_BARRIER, min(self.y, HEIGHT - self.height))

    def take_damage(self, amount):
        self.hp -= amount

    def is_dead(self):
        return self.hp <= 0

    def draw(self):
        screen.blit(self._image, (self.x, self.y))
        self._draw_hp_bar()
        debug_rect(self.get_rect(), (255, 100, 0))   # orange box when debugging

    def _draw_hp_bar(self):
        bx = self.x + self.width // 2 - self.BAR_W // 2
        by = self.y - 28
        pygame.draw.rect(screen, (60, 0, 0), (bx, by, self.BAR_W, self.BAR_H), border_radius=5)
        fill_w = int(self.BAR_W * self.hp / BOSS_MAX_HP)
        ratio  = self.hp / BOSS_MAX_HP
        g      = int(40 + 160 * ratio)
        pygame.draw.rect(screen, (220, g, 0), (bx, by, fill_w, self.BAR_H), border_radius=5)
        pygame.draw.rect(screen, RED, (bx, by, self.BAR_W, self.BAR_H), 2, border_radius=5)
        draw_text(screen, f"BOSS  {self.hp}/{BOSS_MAX_HP}", FONT_TINY, WHITE,
                  bx + self.BAR_W // 2, by + self.BAR_H // 2 + 1, shadow=False)

    def get_rect(self):
        # Smaller hitbox so the large sprite padding doesn't count as collision
        return pygame.Rect(
            self.x + BOSS_HB_OFFSET_X,
            self.y + BOSS_HB_OFFSET_Y,
            BOSS_HB_W,
            BOSS_HB_H
        )


# ================================================================== #
#  BULLET (HARPOON) CLASS                                              #
# ================================================================== #
#
#  HOW THE HARPOON WORKS
#  ---------------------
#  When the player presses X, a Bullet is created at the FRONT of
#  Jerry's body (not the centre of the sprite).  It stores the
#  direction Jerry was facing at the moment of firing, then moves
#  in that direction every frame.
#
#  x/y POSITION
#    self.x and self.y are the TOP-LEFT corner of the drawn harpoon image.
#    We spawn it so that the tip of the harpoon lines up with the front
#    of Jerry's body hitbox.
#
#  SPEED
#    self.speed is always positive.  direction is +1 (right) or -1 (left).
#    Each frame:  self.x += self.speed * self.direction
#    CHANGE self.speed (currently 10) to make the harpoon faster or slower.
#
#  COLLISION RECTANGLE
#    The drawn image is 150x50 but most of that is empty space around
#    the actual spike.  The collision rectangle uses HARPOON_HB_* offsets
#    from the settings block to cover only the spike tip area.
#    This means the harpoon has to visually overlap a pirate to count as a hit.
#
#  IMAGE DIRECTION
#    We pre-cached harpoon_img_right and harpoon_img_left at startup.
#    Here we just pick the right one – no transform work per frame.

class Bullet:

    def __init__(self, x, y, facing_right):
        # facing_right: True = travels right, False = travels left
        self.direction = 1 if facing_right else -1
        self.speed     = 10   # pixels per frame – CHANGE THIS to adjust harpoon speed

        # Pick the correct pre-cached image
        self.image  = harpoon_img_right if facing_right else harpoon_img_left

        # Drawn image size (used to position the image on screen)
        self.img_w  = 150   # CHANGE THIS if you rescale the harpoon PNG
        self.img_h  = 50

        # The collision box width/height come from GAME SETTINGS
        self.hb_w   = HARPOON_HB_W
        self.hb_h   = HARPOON_HB_H

        # x, y = top-left of the drawn harpoon image
        self.x = x
        self.y = y

    def move(self):
        # direction is +1 or -1, so this handles both left and right travel
        self.x += self.speed * self.direction

    def draw(self):
        screen.blit(self.image, (self.x, self.y))
        debug_rect(self.get_rect(), CYAN)   # cyan box when SHOW_HITBOXES=True

    # ------------------------------------------------------------------
    #  COLLISION RECTANGLE
    #  The harpoon image is wider than the actual spike, so we shrink
    #  the hitbox using HARPOON_HB_OFFSET_X and HARPOON_HB_OFFSET_Y.
    #  For a right-facing harpoon, the spike is at the right end of
    #  the image, so we push the hitbox toward the right.
    #  For left-facing, the spike is at the left end (image is flipped),
    #  so the offset starts from the left.
    # ------------------------------------------------------------------
    def get_rect(self):
        if self.direction == 1:   # travelling right: spike at right side
            hx = self.x + self.img_w - self.hb_w - HARPOON_HB_OFFSET_X
        else:                      # travelling left:  spike at left side
            hx = self.x + HARPOON_HB_OFFSET_X
        hy = self.y + HARPOON_HB_OFFSET_Y
        return pygame.Rect(hx, hy, self.hb_w, self.hb_h)

    def is_off_screen(self):
        """True when the harpoon has left the screen on either side."""
        return self.x > WIDTH or (self.x + self.img_w) < 0


# ================================================================== #
#  PARTICLE CLASS                                                      #
# ================================================================== #
#
#  PERFORMANCE NOTE
#  The original code created a brand-new pygame.Surface inside draw()
#  every single frame for every particle.  That's up to 18 new surfaces
#  per dead pirate, 60 times a second.  Allocating memory that quickly
#  makes the game stutter.
#
#  FIX: we create the surface ONCE in __init__ at full opacity, then
#  use Surface.set_alpha() to change how transparent it is each frame.
#  set_alpha() is fast because it just updates a number stored on the
#  surface – it doesn't copy or recreate any pixel data.

class Particle:

    def __init__(self, x, y):
        self.x      = x
        self.y      = y
        self.vx     = random.uniform(-4, 4)
        self.vy     = random.uniform(-4, 4)
        self.life   = random.randint(15, 30)
        self.r      = random.randint(3, 7)
        colour      = random.choice([YELLOW, ORANGE, WHITE])

        # Create the surface ONCE here, reuse it in draw()
        diameter    = self.r * 2
        self._surf  = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(self._surf, colour, (self.r, self.r), self.r)

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.life -= 1

    def draw(self):
        # Fade out as life drops toward 0
        alpha = max(0, int(255 * self.life / 30))
        self._surf.set_alpha(alpha)   # fast – just updates a stored value
        screen.blit(self._surf, (int(self.x - self.r), int(self.y - self.r)))


# ================================================================== #
#  HUD                                                                 #
# ================================================================== #

HEART = "♥"

def draw_hud(score, lives, wave, shoot_cooldown):
    draw_panel(screen, 0, 0, WIDTH, 50, colour=(0, 10, 30, 200), radius=0)

    draw_text(screen, f"SCORE  {score}", FONT_SMALL, YELLOW, 110, 25,
              shadow_colour=(80, 60, 0))
    draw_text(screen, f"WAVE  {wave}", FONT_SMALL, CYAN, WIDTH // 2, 25,
              shadow_colour=(0, 60, 80))

    heart_col = RED if lives == 1 else (255, 100, 100)
    draw_text(screen, HEART * max(lives, 0), FONT_SMALL, heart_col,
              WIDTH - 120, 25, shadow_colour=(80, 0, 0))

    bar_x, bar_y, bar_w, bar_h = 20, 60, 200, 14
    draw_panel(screen, bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 8,
               colour=(0, 10, 30, 160), radius=6)
    pygame.draw.rect(screen, (40, 40, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=4)

    if shoot_cooldown == 0:
        fill_w  = bar_w
        fill_c  = GREEN
        label   = "HARPOON  READY"
        label_c = GREEN
    else:
        fill_w  = int(bar_w * (1 - shoot_cooldown / SHOOT_COOLDOWN))
        fill_c  = ORANGE
        label   = f"HARPOON  {shoot_cooldown / 60:.1f}s"
        label_c = ORANGE

    pygame.draw.rect(screen, fill_c, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
    draw_text(screen, label, FONT_TINY, label_c,
              bar_x + bar_w // 2, bar_y + bar_h + 12, shadow=False)

    if SHOW_HITBOXES:
        draw_text(screen, "HITBOXES ON", FONT_TINY, (255, 80, 80),
                  WIDTH - 70, HEIGHT - 15, shadow=False)


# ================================================================== #
#  START SCREEN                                                        #
# ================================================================== #

def start_screen():
    title_y = HEIGHT // 2 - 140
    pulse   = 0
    waiting = True

    while waiting:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    waiting = False

        pulse     += 0.07
        glow_alpha = int(160 + 80 * math.sin(pulse))

        screen.blit(background_img, (0, 0))
        draw_panel(screen, 100, 60, WIDTH - 200, HEIGHT - 120, colour=(0, 10, 35, 200))

        draw_text(screen, "DEEP SEA DIVER", FONT_HUGE, CYAN,
                  WIDTH // 2, title_y, shadow_colour=(0, 40, 80), shadow_offset=5)
        draw_text(screen, "FIGHT THE PIRATE CREW", FONT_MEDIUM, YELLOW,
                  WIDTH // 2, title_y + 100)

        pygame.draw.line(screen, CYAN,
                         (180, title_y + 135), (WIDTH - 180, title_y + 135), 2)

        controls = [
            ("ARROW KEYS", "Move"),
            ("SPACE",      "Sword Attack"),
            ("X",          "Fire Harpoon"),
        ]
        for i, (key, action) in enumerate(controls):
            cy = title_y + 175 + i * 38
            draw_text(screen, key,    FONT_SMALL, YELLOW, WIDTH // 2 - 80, cy, shadow=False)
            draw_text(screen, "—",    FONT_SMALL, WHITE,  WIDTH // 2,      cy, shadow=False)
            draw_text(screen, action, FONT_SMALL, WHITE,  WIDTH // 2 + 80, cy, shadow=False)

        prompt = FONT_MEDIUM.render("PRESS  ENTER  TO  START", True, WHITE)
        prompt.set_alpha(glow_alpha)
        screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, title_y + 330)))

        pygame.display.flip()


# ================================================================== #
#  WAVE ANNOUNCEMENT                                                   #
# ================================================================== #

def wave_announcement(wave_number):
    for frame in range(90):
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        if frame < 20:
            alpha = int(255 * frame / 20)
        elif frame < 70:
            alpha = 255
        else:
            alpha = int(255 * (90 - frame) / 20)

        screen.blit(background_img, (0, 0))

        panel = pygame.Surface((500, 140), pygame.SRCALPHA)
        panel.fill((0, 10, 35, min(200, alpha)))
        screen.blit(panel, (WIDTH // 2 - 250, HEIGHT // 2 - 70))

        s1 = FONT_LARGE.render(f"WAVE  {wave_number}", True, CYAN)
        s1.set_alpha(alpha)
        screen.blit(s1, s1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))

        s2 = FONT_MEDIUM.render("SURVIVE!", True, YELLOW)
        s2.set_alpha(alpha)
        screen.blit(s2, s2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 45)))

        pygame.display.flip()


# ================================================================== #
#  BOSS ANNOUNCEMENT                                                   #
# ================================================================== #

def boss_announcement():
    for frame in range(120):
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        if frame < 20:
            alpha = int(255 * frame / 20)
        elif frame < 90:
            alpha = 255
        else:
            alpha = int(255 * (120 - frame) / 30)

        screen.blit(background_img, (0, 0))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((80, 0, 0, min(160, alpha)))
        screen.blit(overlay, (0, 0))

        panel = pygame.Surface((620, 200), pygame.SRCALPHA)
        panel.fill((40, 0, 0, min(220, alpha)))
        screen.blit(panel, (WIDTH // 2 - 310, HEIGHT // 2 - 100))

        s1 = FONT_LARGE.render("⚠  BOSS  INCOMING  ⚠", True, RED)
        s1.set_alpha(alpha)
        screen.blit(s1, s1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 35)))

        s2 = FONT_MEDIUM.render("THE PIRATE CAPTAIN APPROACHES!", True, ORANGE)
        s2.set_alpha(alpha)
        screen.blit(s2, s2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 35)))

        s3 = FONT_SMALL.render("Harpoon deals DOUBLE damage to the boss", True, YELLOW)
        s3.set_alpha(min(255, alpha))
        screen.blit(s3, s3.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80)))

        pygame.display.flip()


# ================================================================== #
#  GAME OVER SCREEN                                                    #
# ================================================================== #

def game_over_screen(score, wave):
    pulse   = 0
    waiting = True

    while waiting:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "restart"
                if event.key == pygame.K_ESCAPE:
                    return "quit"

        pulse     += 0.07
        glow_alpha = int(160 + 80 * math.sin(pulse))

        screen.blit(background_img, (0, 0))
        draw_panel(screen, 150, 100, WIDTH - 300, HEIGHT - 200,
                   colour=(30, 0, 0, 210), radius=18)

        draw_text(screen, "GAME  OVER", FONT_HUGE, RED,
                  WIDTH // 2, HEIGHT // 2 - 140,
                  shadow_colour=(80, 0, 0), shadow_offset=5)
        draw_text(screen, f"SCORE  {score}", FONT_LARGE, YELLOW,
                  WIDTH // 2, HEIGHT // 2 - 30)
        draw_text(screen, f"REACHED  WAVE  {wave}", FONT_MEDIUM, CYAN,
                  WIDTH // 2, HEIGHT // 2 + 50)

        pygame.draw.line(screen, RED,
                         (220, HEIGHT // 2 + 90), (WIDTH - 220, HEIGHT // 2 + 90), 2)

        r_surf = FONT_SMALL.render("R — RESTART", True, WHITE)
        r_surf.set_alpha(glow_alpha)
        e_surf = FONT_SMALL.render("ESC — QUIT", True, (180, 180, 180))
        e_surf.set_alpha(glow_alpha)
        screen.blit(r_surf, r_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 125)))
        screen.blit(e_surf, e_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 160)))

        pygame.display.flip()


# ================================================================== #
#  MAIN GAME LOOP                                                      #
# ================================================================== #
#
#  HOW THE GAME LOOP WORKS
#  -----------------------
#  Every frame the loop does the same four things in order:
#    1. EVENTS   – check for key presses, window close, etc.
#    2. UPDATE   – move everything, run collision checks, update timers
#    3. DRAW     – clear the screen, draw everything, show the frame
#    4. TICK     – wait so we run at exactly 60 frames per second
#
#  This order matters.  We always update positions BEFORE drawing so
#  the screen shows where things actually are this frame.

def run_game():

    player              = Player(250, 250)
    lives               = 3
    invincibility_timer = 0

    pirates   = []
    bullets   = []
    particles = []
    boss      = None

    shoot_cooldown = 0
    score          = 0

    wave             = 1
    pirates_in_wave  = 3
    pirates_spawned  = 0
    spawn_timer      = 0
    spawn_delay      = 120

    BOSS_WAVE        = 4
    boss_wave_done   = False
    boss_wave_active = False

    wave_announcement(wave)

    running = True

    while running:

        clock.tick(60)

        # ── EVENTS ─────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_SPACE:
                    player.attack()

                # ── FIRE HARPOON ──────────────────────────────────
                # We pass player.facing_right into the Bullet so it
                # knows which direction to travel and which image to use.
                # The spawn position is calculated so the harpoon tip
                # starts at the front edge of Jerry's body, not his centre.
                if event.key == pygame.K_x and shoot_cooldown == 0:
                    if player.facing_right:
                        # Front edge of Jerry's hitbox, centred vertically
                        bx = player.x + JERRY_HB_OFFSET_X + JERRY_HB_W
                        by = player.y + JERRY_HB_OFFSET_Y + JERRY_HB_H // 2 - 25
                    else:
                        # Left edge of Jerry's hitbox, minus the harpoon width
                        bx = player.x + JERRY_HB_OFFSET_X - 150
                        by = player.y + JERRY_HB_OFFSET_Y + JERRY_HB_H // 2 - 25

                    bullets.append(Bullet(bx, by, player.facing_right))
                    shoot_cooldown = SHOOT_COOLDOWN

        # ── UPDATE PLAYER ──────────────────────────────────────────
        player.move()
        player.update_animation()
        player.update_attack()

        if shoot_cooldown > 0:
            shoot_cooldown -= 1

        # ── PIRATE SPAWNING ────────────────────────────────────────
        if not boss_wave_active:
            spawn_timer += 1
            if spawn_timer >= spawn_delay and pirates_spawned < pirates_in_wave:
                spawn_timer = 0
                new_pirate  = Pirate(WIDTH, random.randint(TOP_BARRIER, HEIGHT - 150))
                pirates.append(new_pirate)
                pirates_spawned += 1

        # ── MOVEMENT ───────────────────────────────────────────────
        for p in pirates:
            p.move_towards_player(player)
        if boss:
            boss.move_towards_player(player)
        for b in bullets:
            b.move()

        # ── HARPOON ↔ PIRATE COLLISION ─────────────────────────────
        for bullet in bullets[:]:
            hit = False
            for pirate in pirates[:]:
                if bullet.get_rect().colliderect(pirate.get_rect()):
                    cx = pirate.x + pirate.width  // 2
                    cy = pirate.y + pirate.height // 2
                    for _ in range(18):
                        particles.append(Particle(cx, cy))
                    pirates.remove(pirate)
                    if bullet in bullets:
                        bullets.remove(bullet)
                    score += 10
                    hit = True
                    break

            # Harpoon ↔ Boss (2 damage)
            if not hit and boss and bullet in bullets:
                if bullet.get_rect().colliderect(boss.get_rect()):
                    boss.take_damage(2)
                    bullets.remove(bullet)
                    for _ in range(12):
                        particles.append(Particle(
                            bullet.x + bullet.img_w // 2,
                            bullet.y + bullet.img_h // 2
                        ))

        # ── SWORD ↔ PIRATE COLLISION ───────────────────────────────
        sword_rect = player.get_sword_rect()
        for pirate in pirates[:]:
            if sword_rect.colliderect(pirate.get_rect()):
                cx = pirate.x + pirate.width  // 2
                cy = pirate.y + pirate.height // 2
                for _ in range(18):
                    particles.append(Particle(cx, cy))
                pirates.remove(pirate)
                score += 10

        # Sword ↔ Boss (1 damage, only on first frame of swing)
        if boss and sword_rect.colliderect(boss.get_rect()):
            if player.attack_timer == 9:
                boss.take_damage(1)
                for _ in range(10):
                    particles.append(Particle(
                        boss.x + boss.width  // 2,
                        boss.y + boss.height // 2
                    ))

        # ── BOSS DEATH ─────────────────────────────────────────────
        if boss and boss.is_dead():
            for _ in range(40):
                particles.append(Particle(
                    boss.x + boss.width  // 2,
                    boss.y + boss.height // 2
                ))
            score           += 200
            boss             = None
            boss_wave_active = False
            boss_wave_done   = True
            wave            += 1
            pirates_in_wave  = wave + 1
            pirates_spawned  = 0
            spawn_timer      = 0
            wave_announcement(wave)

        # ── PLAYER ↔ PIRATE COLLISION ──────────────────────────────
        if invincibility_timer > 0:
            invincibility_timer -= 1

        for pirate in pirates[:]:
            if player.get_rect().colliderect(pirate.get_rect()):
                if invincibility_timer == 0:
                    lives -= 1
                    invincibility_timer = 120
                    pirates.remove(pirate)
                    if lives <= 0:
                        running = False

        # Player ↔ Boss (2 lives damage)
        if boss and player.get_rect().colliderect(boss.get_rect()):
            if invincibility_timer == 0:
                lives -= 2
                invincibility_timer = 150
                if lives <= 0:
                    running = False

        # ── CLEANUP ────────────────────────────────────────────────
        # is_off_screen() now checks both edges, so left-fired harpoons
        # are removed when they disappear off the left side too.
        bullets   = [b for b in bullets   if not b.is_off_screen()]
        pirates   = [p for p in pirates   if p.x > -200]
        particles = [p for p in particles if p.life > 0]

        for p in particles:
            p.update()

        # ── NEXT WAVE ──────────────────────────────────────────────
        if (
            not boss_wave_active
            and pirates_spawned == pirates_in_wave
            and len(pirates) == 0
        ):
            score     += wave * 25
            next_wave  = wave + 1

            if next_wave == BOSS_WAVE and not boss_wave_done:
                wave             = BOSS_WAVE
                boss_wave_active = True
                pirates_spawned  = pirates_in_wave
                boss_announcement()
                boss = Boss()
                pirates.append(Pirate(WIDTH,      random.randint(TOP_BARRIER, HEIGHT - 150)))
                pirates.append(Pirate(WIDTH + 80, random.randint(TOP_BARRIER, HEIGHT - 150)))
            else:
                wave            = next_wave
                pirates_in_wave += 2
                pirates_spawned  = 0
                spawn_timer      = 0
                wave_announcement(wave)

        # ── SCORE TRICKLE ──────────────────────────────────────────
        score += 1

        # ── DRAW ───────────────────────────────────────────────────
        screen.blit(background_img, (0, 0))

        if boss:
            boss.draw()

        for pirate in pirates:
            pirate.draw()

        for bullet in bullets:
            bullet.draw()

        if invincibility_timer == 0 or (invincibility_timer // 6) % 2 == 0:
            player.draw()

        for p in particles:
            p.draw()

        draw_hud(score // 10, lives, wave, shoot_cooldown)

        if boss_wave_active:
            draw_text(screen, "BOSS  WAVE", FONT_MEDIUM, RED,
                      WIDTH // 2, 25, shadow_colour=(60, 0, 0))

        pygame.display.flip()

    return game_over_screen(score // 10, wave)


# ================================================================== #
#  ENTRY POINT                                                         #
# ================================================================== #

start_screen()

while True:
    result = run_game()
    if result == "quit":
        break

pygame.quit()
