# =============================================================
# IMPORTS
# =============================================================

import pygame
import random
import math
from os.path import join, dirname, abspath

pygame.init()

# =============================================================
# SCREEN
# =============================================================

WIDTH  = 1000
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Deep Sea Diver - Fight the Pirate Crew")

clock = pygame.time.Clock()

# =============================================================
# SETTINGS  - change these to tweak the game
# =============================================================

# Jerry cannot move above this y position
TOP_BARRIER = 150

# How fast Jerry moves (pixels per frame)
JERRY_SPEED = 5

# Pirate speed (pixels per frame)
PIRATE_SPEED = 2

# Boss speed (pixels per frame)
BOSS_SPEED = 1.5

# How many frames between harpoon shots (60 frames = 1 second)
HARPOON_COOLDOWN = 120

# How fast the harpoon travels (pixels per frame)
HARPOON_SPEED = 10

# How many HP the boss has
BOSS_MAX_HP = 8

# Set to True to see collision boxes drawn on screen (useful for testing)
# Set to False for normal play
SHOW_HITBOXES = False

# =============================================================
# COLOURS
# =============================================================

WHITE  = (255, 255, 255)
BLACK  = (  0,   0,   0)
RED    = (220,  50,  50)
GREEN  = ( 60, 200,  80)
YELLOW = (255, 215,   0)
ORANGE = (255, 140,   0)
CYAN   = ( 80, 230, 255)

# =============================================================
# IMAGE FOLDER PATH
# The Images folder is one level up from this file (../Images/)
# =============================================================

BASE_DIR   = dirname(abspath(__file__))
IMAGES_DIR = join(BASE_DIR, "..", "Images")

# =============================================================
# LOAD IMAGES
# =============================================================

# Background
background_img = pygame.image.load(join(IMAGES_DIR, "shipwreck.png")).convert()
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

# Jerry - two frames for walking animation
# convert_alpha() keeps the transparent parts of the image
jerry_frame1 = pygame.image.load(join(IMAGES_DIR, "walking_jerry.png")).convert_alpha()
jerry_frame1 = pygame.transform.scale(jerry_frame1, (85, 110))
jerry_frame1.set_colorkey(WHITE)   # make pure white pixels transparent

jerry_frame2 = pygame.image.load(join(IMAGES_DIR, "walking_jerry1.png")).convert_alpha()
jerry_frame2 = pygame.transform.scale(jerry_frame2, (85, 110))
jerry_frame2.set_colorkey(WHITE)

# Pre-create the left-facing versions so we don't flip every frame
jerry_frame1_left = pygame.transform.flip(jerry_frame1, True, False)
jerry_frame2_left = pygame.transform.flip(jerry_frame2, True, False)

# Pirate
pirate_img = pygame.image.load(join(IMAGES_DIR, "pirate.png")).convert_alpha()
pirate_img = pygame.transform.scale(pirate_img, (150, 120))

# Harpoon - one facing right, one pre-flipped for left
harpoon_img_right = pygame.image.load(join(IMAGES_DIR, "harpoon.png")).convert_alpha()
harpoon_img_right = pygame.transform.scale(harpoon_img_right, (150, 50))
harpoon_img_left  = pygame.transform.flip(harpoon_img_right, True, False)

# Boss - uses the pirate image scaled up with a red tint
# You can swap "pirate.png" for a different image later
boss_base_img = pygame.image.load(join(IMAGES_DIR, "pirate.png")).convert_alpha()
boss_base_img = pygame.transform.scale(boss_base_img, (220, 180))
# Add a red tint to make the boss look different
tint_surface  = pygame.Surface((220, 180), pygame.SRCALPHA)
tint_surface.fill((180, 0, 0, 60))
boss_base_img.blit(tint_surface, (0, 0))

# =============================================================
# FONTS
# =============================================================

font_big    = pygame.font.SysFont("impact",  90)
font_large  = pygame.font.SysFont("impact",  52)
font_medium = pygame.font.SysFont("impact",  32)
font_small  = pygame.font.SysFont("verdana", 20, bold=True)
font_tiny   = pygame.font.SysFont("verdana", 16)


# =============================================================
# PLAYER CLASS
# =============================================================
#
# The Player class holds everything about Jerry:
#   - his position (x, y)
#   - his speed
#   - his animation (which frame to show)
#   - his sword attack
#
# Every frame the game loop calls:
#   player.move()       - reads keys, moves Jerry
#   player.draw()       - draws Jerry on screen
#   player.get_rect()   - returns the collision box

class Player:

    def __init__(self, x, y):
        self.x = x
        self.y = y

        # Full sprite size (do not change these for the hitbox)
        self.width  = 85
        self.height = 110

        self.speed = JERRY_SPEED

        # --- Animation ---
        # frame is 0 or 1 - switches between the two walking images
        self.anim_frame = 0
        # anim_timer counts up each frame; when it reaches 10 we swap frames
        self.anim_timer = 0
        # True if Jerry is moving this frame (used to decide whether to animate)
        self.moving = False
        # True = facing right, False = facing left
        self.facing_right = True

        # --- Sword attack ---
        # True while the sword swing is active
        self.attacking = False
        # Counts down while attacking (attack lasts 10 frames)
        self.attack_timer = 0
        # Counts down between attacks (prevents spamming)
        self.attack_cooldown = 0

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

        # Diagonal movement fix:
        # Moving diagonally would normally be faster (going right AND down at once).
        # Multiplying by 0.707 (roughly 1/sqrt(2)) brings it back to normal speed.
        if dx != 0 and dy != 0:
            dx = int(dx * 0.707)
            dy = int(dy * 0.707)

        self.moving = (dx != 0 or dy != 0)

        self.x += dx
        self.y += dy

        # Keep Jerry inside the screen
        if self.x < 0:
            self.x = 0
        if self.x > WIDTH - self.width:
            self.x = WIDTH - self.width
        if self.y < TOP_BARRIER:
            self.y = TOP_BARRIER
        if self.y > HEIGHT - self.height:
            self.y = HEIGHT - self.height

    def update_animation(self):
        # Only animate when Jerry is moving
        if self.moving:
            self.anim_timer += 1
            if self.anim_timer >= 10:
                self.anim_timer = 0
                # Toggle between frame 0 and frame 1
                if self.anim_frame == 0:
                    self.anim_frame = 1
                else:
                    self.anim_frame = 0
        else:
            # Stand still on frame 0 when not moving
            self.anim_frame = 0
            self.anim_timer = 0

    def start_attack(self):
        # Only start a new attack if cooldown has finished
        if self.attack_cooldown == 0:
            self.attacking       = True
            self.attack_timer    = 10
            self.attack_cooldown = 25

    def update_attack(self):
        # Count down the attack timer
        if self.attack_timer > 0:
            self.attack_timer -= 1
        else:
            self.attacking = False

        # Count down the cooldown between attacks
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def get_sword_rect(self):
        # Returns the collision box for the sword while attacking.
        # Returns an empty rectangle when not attacking.
        if not self.attacking:
            return pygame.Rect(0, 0, 0, 0)

        if self.facing_right:
            # Sword appears to the RIGHT of Jerry
            sx = self.x + 60
        else:
            # Sword appears to the LEFT of Jerry
            sx = self.x - 55

        sy = self.y + 35
        return pygame.Rect(sx, sy, 55, 45)

    def draw(self):
        # Pick the correct image based on direction and animation frame
        if self.facing_right:
            if self.anim_frame == 0:
                image = jerry_frame1
            else:
                image = jerry_frame2
        else:
            if self.anim_frame == 0:
                image = jerry_frame1_left
            else:
                image = jerry_frame2_left

        screen.blit(image, (self.x, self.y))

        # Draw a faint yellow glow where the sword is during an attack
        if self.attacking:
            sword_rect = self.get_sword_rect()
            if SHOW_HITBOXES:
                pygame.draw.rect(screen, YELLOW, sword_rect, 2)
            else:
                glow = pygame.Surface((sword_rect.width, sword_rect.height), pygame.SRCALPHA)
                glow.fill((255, 255, 0, 80))
                screen.blit(glow, (sword_rect.x, sword_rect.y))

        # Draw the body hitbox when testing
        if SHOW_HITBOXES:
            pygame.draw.rect(screen, GREEN, self.get_rect(), 2)

    def get_rect(self):
        # This is the collision box for Jerry's body.
        # It is smaller than the full sprite so that transparent edges don't count.
        # self.x + 15  = start 15 pixels from the left edge of the sprite
        # self.y + 10  = start 10 pixels from the top edge of the sprite
        # 55           = width of the hitbox
        # 90           = height of the hitbox
        return pygame.Rect(self.x + 15, self.y + 10, 55, 90)


# =============================================================
# PIRATE CLASS
# =============================================================
#
# Each Pirate spawns off the right edge and chases Jerry.
# The Pirate class holds:
#   - its position (x, y)
#   - how fast it moves
#   - how to draw itself
#   - its collision box

class Pirate:

    def __init__(self, x, y):
        self.x = x
        self.y = y

        # Full sprite size
        self.width  = 150
        self.height = 120

        self.speed = PIRATE_SPEED

    def move_towards_player(self, player):
        # Work out which direction Jerry is relative to this pirate
        dx = player.x - self.x
        dy = player.y - self.y

        # Move one step towards Jerry
        if dx > 0:
            self.x += self.speed
        elif dx < 0:
            self.x -= self.speed

        if dy > 0:
            self.y += self.speed
        elif dy < 0:
            self.y -= self.speed

        # Stop pirate going above the top barrier or below the screen bottom
        if self.y < TOP_BARRIER:
            self.y = TOP_BARRIER
        if self.y > HEIGHT - self.height:
            self.y = HEIGHT - self.height

    def draw(self):
        screen.blit(pirate_img, (self.x, self.y))

        if SHOW_HITBOXES:
            pygame.draw.rect(screen, RED, self.get_rect(), 2)

    def get_rect(self):
        # Smaller hitbox so the transparent edges of the sprite don't count.
        # self.x + 30  = start 30 pixels in from the left of the sprite
        # self.y + 10  = start 10 pixels down from the top
        # 90           = width of the hitbox
        # 100          = height of the hitbox
        return pygame.Rect(self.x + 30, self.y + 10, 90, 100)


# =============================================================
# HARPOON CLASS
# =============================================================
#
# How the harpoon works:
#   1. Player presses X
#   2. A Harpoon object is created in front of Jerry
#   3. It is added to the harpoons list
#   4. Every frame, harpoon.move() is called to slide it across
#   5. We check if it hits a pirate or the boss
#   6. If it hits something or goes off screen, we remove it

class Harpoon:

    def __init__(self, x, y, facing_right):
        self.x = x
        self.y = y

        # Store which direction this harpoon travels
        self.facing_right = facing_right

        # Speed is always positive; direction decides left or right
        self.speed = HARPOON_SPEED

        # Full drawn image size
        self.width  = 150
        self.height = 50

    def move(self):
        if self.facing_right:
            self.x += self.speed
        else:
            self.x -= self.speed

    def is_off_screen(self):
        # Returns True when the harpoon has gone past either edge of the screen
        if self.x > WIDTH:
            return True
        if self.x + self.width < 0:
            return True
        return False

    def draw(self):
        if self.facing_right:
            screen.blit(harpoon_img_right, (self.x, self.y))
        else:
            screen.blit(harpoon_img_left, (self.x, self.y))

        if SHOW_HITBOXES:
            pygame.draw.rect(screen, CYAN, self.get_rect(), 2)

    def get_rect(self):
        # The actual spike is only a small part of the 150x50 image.
        # We use a slim rectangle to cover just the tip of the spike.
        if self.facing_right:
            # Spike is on the right side of the image
            return pygame.Rect(self.x + 90, self.y + 15, 60, 20)
        else:
            # Spike is on the left side of the flipped image
            return pygame.Rect(self.x, self.y + 15, 60, 20)


# =============================================================
# BOSS CLASS
# =============================================================
#
# The boss is a bigger, tougher version of the pirate.
# It has a health bar drawn above it.
# Harpoon hits do 2 damage; sword hits do 1 damage.
# The boss deals 2 lives of damage when it touches Jerry.

class Boss:

    def __init__(self):
        self.width  = 220
        self.height = 180

        # Start off the right edge and move in
        self.x = WIDTH
        self.y = HEIGHT // 2 - 90

        self.speed = BOSS_SPEED
        self.hp    = BOSS_MAX_HP

    def move_towards_player(self, player):
        dx = player.x - self.x
        dy = player.y - self.y

        if dx > 0:
            self.x += self.speed
        elif dx < 0:
            self.x -= self.speed

        if dy > 0:
            self.y += self.speed
        elif dy < 0:
            self.y -= self.speed

        if self.y < TOP_BARRIER:
            self.y = TOP_BARRIER
        if self.y > HEIGHT - self.height:
            self.y = HEIGHT - self.height

    def take_damage(self, amount):
        self.hp -= amount

    def is_dead(self):
        return self.hp <= 0

    def draw(self):
        screen.blit(boss_base_img, (self.x, self.y))
        self.draw_hp_bar()

        if SHOW_HITBOXES:
            pygame.draw.rect(screen, ORANGE, self.get_rect(), 2)

    def draw_hp_bar(self):
        # Position the bar above the boss sprite
        bar_x = self.x + self.width // 2 - 110
        bar_y = self.y - 28
        bar_w = 220
        bar_h = 18

        # Dark red background track
        pygame.draw.rect(screen, (60, 0, 0), (bar_x, bar_y, bar_w, bar_h), border_radius=5)

        # Coloured fill that shrinks as HP drops
        fill_w = int(bar_w * self.hp / BOSS_MAX_HP)
        # The bar goes from orange-red when low HP to yellow-green when full HP
        green_amount = int(40 + 160 * (self.hp / BOSS_MAX_HP))
        pygame.draw.rect(screen, (220, green_amount, 0), (bar_x, bar_y, fill_w, bar_h), border_radius=5)

        # Border around the bar
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=5)

        # HP text in the centre of the bar
        hp_text = font_tiny.render(f"BOSS  {self.hp}/{BOSS_MAX_HP}", True, WHITE)
        text_rect = hp_text.get_rect(center=(bar_x + bar_w // 2, bar_y + bar_h // 2))
        screen.blit(hp_text, text_rect)

    def get_rect(self):
        # Smaller hitbox so the edges of the large sprite don't count.
        # self.x + 40  = start 40 pixels in from the left
        # self.y + 15  = start 15 pixels down from the top
        # 140          = width of the hitbox
        # 150          = height of the hitbox
        return pygame.Rect(self.x + 40, self.y + 15, 140, 150)


# =============================================================
# PARTICLE CLASS
# =============================================================
#
# Particles are the little sparks that appear when a pirate dies.
# Each particle moves outward and fades away over time.

class Particle:

    def __init__(self, x, y):
        self.x = x
        self.y = y

        # Random velocity in any direction
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-4, 4)

        # Life counts down to 0, then the particle is removed
        self.life = random.randint(15, 30)

        self.radius = random.randint(3, 7)
        self.colour = random.choice([YELLOW, ORANGE, WHITE])

        # Create the circle image once here so we don't recreate it every frame
        size = self.radius * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.colour, (self.radius, self.radius), self.radius)

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.life -= 1

    def draw(self):
        # Fade out as life drops
        alpha = int(255 * self.life / 30)
        if alpha < 0:
            alpha = 0
        self.image.set_alpha(alpha)
        screen.blit(self.image, (int(self.x - self.radius), int(self.y - self.radius)))


# =============================================================
# SCREEN DRAWING HELPERS
# =============================================================
# These small functions are called from the game loop to draw
# the HUD and the various screens (start, wave, boss, game over).

def draw_text_centered(text, font, colour, center_x, center_y):
    # Render a text surface and draw it centred on the given point
    surface  = font.render(text, True, colour)
    text_rect = surface.get_rect(center=(center_x, center_y))
    screen.blit(surface, text_rect)


def draw_text_centered_shadow(text, font, colour, center_x, center_y,
                               shadow_colour=(0, 0, 0)):
    # Same as above but with a drop shadow for readability
    shadow  = font.render(text, True, shadow_colour)
    surface = font.render(text, True, colour)
    text_rect = surface.get_rect(center=(center_x, center_y))
    screen.blit(shadow,  (text_rect.x + 3, text_rect.y + 3))
    screen.blit(surface, text_rect)


def draw_hud(score, lives, wave, harpoon_cooldown):
    # Dark strip across the top of the screen
    pygame.draw.rect(screen, (0, 10, 30), (0, 0, WIDTH, 50))

    # Score
    draw_text_centered_shadow(f"SCORE  {score}",
                               font_small, YELLOW, 110, 25)

    # Wave
    draw_text_centered_shadow(f"WAVE  {wave}",
                               font_small, CYAN, WIDTH // 2, 25)

    # Lives as heart symbols
    hearts = ""
    for i in range(lives):
        hearts += "♥ "
    if lives <= 1:
        heart_colour = RED
    else:
        heart_colour = (255, 100, 100)
    draw_text_centered_shadow(hearts, font_small, heart_colour, WIDTH - 120, 25)

    # Harpoon cooldown bar
    bar_x = 20
    bar_y = 60
    bar_w = 200
    bar_h = 14

    # Background of the bar (dark)
    pygame.draw.rect(screen, (40, 40, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=4)

    # Filled portion grows as the cooldown counts down to 0
    if harpoon_cooldown == 0:
        fill_w = bar_w
        fill_colour = GREEN
        label = "HARPOON  READY"
        label_colour = GREEN
    else:
        fill_w = int(bar_w * (1 - harpoon_cooldown / HARPOON_COOLDOWN))
        fill_colour = ORANGE
        seconds = harpoon_cooldown / 60
        label = f"HARPOON  {seconds:.1f}s"
        label_colour = ORANGE

    pygame.draw.rect(screen, fill_colour, (bar_x, bar_y, fill_w, bar_h), border_radius=4)

    # Label below the bar
    label_surface = font_tiny.render(label, True, label_colour)
    screen.blit(label_surface, (bar_x, bar_y + bar_h + 4))

    # Reminder in the corner when hitboxes are on
    if SHOW_HITBOXES:
        hint = font_tiny.render("HITBOXES ON", True, RED)
        screen.blit(hint, (WIDTH - 130, HEIGHT - 25))


# =============================================================
# START SCREEN
# =============================================================

def show_start_screen():
    waiting = True
    pulse   = 0   # used to make the "Press Enter" text pulse in brightness

    while waiting:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    waiting = False

        pulse += 0.07
        # sin() goes between -1 and +1, so this gives an alpha between 80 and 240
        pulse_alpha = int(160 + 80 * math.sin(pulse))

        # Draw background
        screen.blit(background_img, (0, 0))

        # Dark panel behind the text
        panel = pygame.Surface((800, 480), pygame.SRCALPHA)
        panel.fill((0, 10, 35, 200))
        screen.blit(panel, (100, 60))

        # Title
        draw_text_centered_shadow("DEEP SEA DIVER", font_big, CYAN,
                                   WIDTH // 2, 160, shadow_colour=(0, 40, 80))
        draw_text_centered("FIGHT THE PIRATE CREW", font_medium, YELLOW,
                            WIDTH // 2, 260)

        # Divider line
        pygame.draw.line(screen, CYAN, (180, 295), (820, 295), 2)

        # Controls list
        draw_text_centered("ARROW KEYS  -  Move",       font_small, WHITE, WIDTH // 2, 330)
        draw_text_centered("SPACE       -  Sword Attack", font_small, WHITE, WIDTH // 2, 368)
        draw_text_centered("X           -  Fire Harpoon", font_small, WHITE, WIDTH // 2, 406)

        # Pulsing prompt
        prompt = font_medium.render("PRESS  ENTER  TO  START", True, WHITE)
        prompt.set_alpha(pulse_alpha)
        prompt_rect = prompt.get_rect(center=(WIDTH // 2, 460))
        screen.blit(prompt, prompt_rect)

        pygame.display.flip()


# =============================================================
# WAVE ANNOUNCEMENT SCREEN
# Shows "WAVE 2 - SURVIVE!" briefly between waves
# =============================================================

def show_wave_screen(wave_number):
    for frame in range(90):   # show for 90 frames (1.5 seconds at 60fps)
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        # Fade in (frames 0-19), hold (20-69), fade out (70-89)
        if frame < 20:
            alpha = int(255 * frame / 20)
        elif frame < 70:
            alpha = 255
        else:
            alpha = int(255 * (90 - frame) / 20)

        screen.blit(background_img, (0, 0))

        # Dark blue panel
        panel = pygame.Surface((500, 140), pygame.SRCALPHA)
        panel.fill((0, 10, 35, min(200, alpha)))
        screen.blit(panel, (WIDTH // 2 - 250, HEIGHT // 2 - 70))

        wave_surf = font_large.render(f"WAVE  {wave_number}", True, CYAN)
        wave_surf.set_alpha(alpha)
        screen.blit(wave_surf, wave_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))

        survive_surf = font_medium.render("SURVIVE!", True, YELLOW)
        survive_surf.set_alpha(alpha)
        screen.blit(survive_surf, survive_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 45)))

        pygame.display.flip()


# =============================================================
# BOSS ANNOUNCEMENT SCREEN
# Shows a dramatic warning before wave 4
# =============================================================

def show_boss_screen():
    for frame in range(120):   # 2 seconds
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

        # Red overlay across the whole screen
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((80, 0, 0, min(160, alpha)))
        screen.blit(overlay, (0, 0))

        # Dark red panel
        panel = pygame.Surface((620, 200), pygame.SRCALPHA)
        panel.fill((40, 0, 0, min(220, alpha)))
        screen.blit(panel, (WIDTH // 2 - 310, HEIGHT // 2 - 100))

        s1 = font_large.render("!  BOSS  INCOMING  !", True, RED)
        s1.set_alpha(alpha)
        screen.blit(s1, s1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 35)))

        s2 = font_medium.render("THE PIRATE CAPTAIN APPROACHES!", True, ORANGE)
        s2.set_alpha(alpha)
        screen.blit(s2, s2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 35)))

        s3 = font_small.render("Harpoon deals DOUBLE damage to the boss", True, YELLOW)
        s3.set_alpha(alpha)
        screen.blit(s3, s3.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80)))

        pygame.display.flip()


# =============================================================
# GAME OVER SCREEN
# Shows the final score and lets the player restart
# =============================================================

def show_game_over_screen(score, wave):
    waiting = True
    pulse   = 0

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

        pulse += 0.07
        pulse_alpha = int(160 + 80 * math.sin(pulse))

        screen.blit(background_img, (0, 0))

        # Dark red panel
        panel = pygame.Surface((700, 400), pygame.SRCALPHA)
        panel.fill((30, 0, 0, 210))
        screen.blit(panel, (150, 100))

        draw_text_centered_shadow("GAME  OVER", font_big, RED,
                                   WIDTH // 2, HEIGHT // 2 - 140,
                                   shadow_colour=(80, 0, 0))
        draw_text_centered(f"SCORE  {score}", font_large, YELLOW,
                            WIDTH // 2, HEIGHT // 2 - 30)
        draw_text_centered(f"REACHED  WAVE  {wave}", font_medium, CYAN,
                            WIDTH // 2, HEIGHT // 2 + 50)

        pygame.draw.line(screen, RED, (220, HEIGHT // 2 + 90), (780, HEIGHT // 2 + 90), 2)

        r_text = font_small.render("R - RESTART", True, WHITE)
        r_text.set_alpha(pulse_alpha)
        screen.blit(r_text, r_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 125)))

        e_text = font_small.render("ESC - QUIT", True, (180, 180, 180))
        e_text.set_alpha(pulse_alpha)
        screen.blit(e_text, e_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 160)))

        pygame.display.flip()


# =============================================================
# MAIN GAME FUNCTION
# =============================================================
#
# This function runs one full game from start to game over.
# When the player dies it returns "restart" or "quit" depending
# on what they press on the game over screen.
#
# HOW THE GAME LOOP WORKS:
#   Every frame we do these things in order:
#     1. Check for events (key presses, closing the window)
#     2. Update everything (move Jerry, move pirates, check collisions)
#     3. Draw everything to the screen
#     4. Wait for the next frame (clock.tick(60) keeps it at 60fps)

def run_game():

    # ---------------------------------------------------------
    # CREATE GAME OBJECTS
    # ---------------------------------------------------------

    player = Player(250, 250)

    # Lists of active game objects
    pirates   = []
    harpoons  = []
    particles = []

    # Boss starts as None - it is created when wave 4 begins
    boss = None

    # ---------------------------------------------------------
    # GAME VARIABLES
    # ---------------------------------------------------------

    lives               = 3
    score               = 0
    harpoon_cooldown    = 0
    invincibility_timer = 0   # Jerry can't be hurt while this is > 0

    # ---------------------------------------------------------
    # WAVE VARIABLES
    # ---------------------------------------------------------

    wave              = 1    # current wave number
    pirates_per_wave  = 3    # how many pirates spawn this wave
    pirates_spawned   = 0    # how many have spawned so far this wave
    spawn_timer       = 0    # counts up; pirate spawns when it reaches spawn_delay
    spawn_delay       = 120  # frames between each pirate spawn

    # Wave 4 is the boss wave.  These two flags track whether it has
    # been triggered and whether the boss fight is still ongoing.
    boss_wave_active = False
    boss_wave_done   = False

    # Show the wave 1 announcement
    show_wave_screen(wave)

    # ---------------------------------------------------------
    # GAME LOOP
    # ---------------------------------------------------------

    running = True

    while running:

        clock.tick(60)   # run at 60 frames per second

        # =====================================================
        # EVENTS
        # =====================================================

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:

                # SPACE = sword attack
                if event.key == pygame.K_SPACE:
                    player.start_attack()

                # X = fire harpoon (only if cooldown has finished)
                if event.key == pygame.K_x:
                    if harpoon_cooldown == 0:

                        # Spawn the harpoon at the front of Jerry's body
                        if player.facing_right:
                            harpoon_x = player.x + 70
                        else:
                            harpoon_x = player.x - 80

                        harpoon_y = player.y + 45

                        new_harpoon = Harpoon(harpoon_x, harpoon_y, player.facing_right)
                        harpoons.append(new_harpoon)

                        harpoon_cooldown = HARPOON_COOLDOWN

        # =====================================================
        # UPDATE PLAYER
        # =====================================================

        player.move()
        player.update_animation()
        player.update_attack()

        # Count down the harpoon cooldown each frame
        if harpoon_cooldown > 0:
            harpoon_cooldown -= 1

        # Count down invincibility after being hit
        if invincibility_timer > 0:
            invincibility_timer -= 1

        # =====================================================
        # PIRATE SPAWNING
        # =====================================================
        # Pirates only spawn during normal waves (not the boss wave)

        if not boss_wave_active:
            spawn_timer += 1

            if spawn_timer >= spawn_delay and pirates_spawned < pirates_per_wave:
                spawn_timer = 0
                spawn_y     = random.randint(TOP_BARRIER, HEIGHT - 150)
                new_pirate  = Pirate(WIDTH, spawn_y)
                pirates.append(new_pirate)
                pirates_spawned += 1

        # =====================================================
        # MOVEMENT
        # =====================================================

        # Move each pirate towards Jerry
        for pirate in pirates:
            pirate.move_towards_player(player)

        # Move the boss towards Jerry (if the boss exists)
        if boss is not None:
            boss.move_towards_player(player)

        # Move each harpoon across the screen
        for harpoon in harpoons:
            harpoon.move()

        # =====================================================
        # COLLISIONS - HARPOON vs PIRATE
        # =====================================================
        # We loop over copies of the lists (using [:]) so we can
        # safely remove items while looping

        for harpoon in harpoons[:]:
            for pirate in pirates[:]:
                if harpoon.get_rect().colliderect(pirate.get_rect()):

                    # Spawn sparks where the pirate was
                    cx = pirate.x + pirate.width  // 2
                    cy = pirate.y + pirate.height // 2
                    for i in range(18):
                        particles.append(Particle(cx, cy))

                    pirates.remove(pirate)

                    if harpoon in harpoons:
                        harpoons.remove(harpoon)

                    score += 10
                    break   # one harpoon can only hit one pirate

        # =====================================================
        # COLLISIONS - HARPOON vs BOSS
        # =====================================================

        if boss is not None:
            for harpoon in harpoons[:]:
                if harpoon.get_rect().colliderect(boss.get_rect()):
                    boss.take_damage(2)   # harpoon does 2 damage to boss

                    if harpoon in harpoons:
                        harpoons.remove(harpoon)

                    # Sparks on the boss
                    for i in range(12):
                        particles.append(Particle(
                            boss.x + boss.width  // 2,
                            boss.y + boss.height // 2
                        ))

        # =====================================================
        # COLLISIONS - SWORD vs PIRATE
        # =====================================================

        sword_rect = player.get_sword_rect()

        for pirate in pirates[:]:
            if sword_rect.colliderect(pirate.get_rect()):

                cx = pirate.x + pirate.width  // 2
                cy = pirate.y + pirate.height // 2
                for i in range(18):
                    particles.append(Particle(cx, cy))

                pirates.remove(pirate)
                score += 10

        # =====================================================
        # COLLISIONS - SWORD vs BOSS
        # =====================================================
        # attack_timer == 9 is the first frame of the swing,
        # so we only deal damage once per swing, not every frame

        if boss is not None:
            if sword_rect.colliderect(boss.get_rect()):
                if player.attack_timer == 9:
                    boss.take_damage(1)

                    for i in range(10):
                        particles.append(Particle(
                            boss.x + boss.width  // 2,
                            boss.y + boss.height // 2
                        ))

        # =====================================================
        # COLLISIONS - PIRATE vs PLAYER
        # =====================================================

        for pirate in pirates[:]:
            if player.get_rect().colliderect(pirate.get_rect()):
                if invincibility_timer == 0:
                    lives -= 1
                    invincibility_timer = 120   # 2 seconds of protection
                    pirates.remove(pirate)

                    if lives <= 0:
                        running = False

        # =====================================================
        # COLLISIONS - BOSS vs PLAYER
        # =====================================================
        # The boss deals 2 lives of damage and gives slightly
        # more invincibility time

        if boss is not None:
            if player.get_rect().colliderect(boss.get_rect()):
                if invincibility_timer == 0:
                    lives -= 2
                    invincibility_timer = 150

                    if lives <= 0:
                        running = False

        # =====================================================
        # BOSS DEATH CHECK
        # =====================================================

        if boss is not None and boss.is_dead():
            # Big explosion of sparks
            for i in range(40):
                particles.append(Particle(
                    boss.x + boss.width  // 2,
                    boss.y + boss.height // 2
                ))

            score            += 200
            boss              = None
            boss_wave_active  = False
            boss_wave_done    = True

            # Move on to the next wave after the boss dies
            wave            += 1
            pirates_per_wave = wave + 1
            pirates_spawned  = 0
            spawn_timer      = 0
            show_wave_screen(wave)

        # =====================================================
        # REMOVE OBJECTS THAT ARE NO LONGER NEEDED
        # =====================================================

        # Remove harpoons that have gone off screen
        harpoons_to_keep = []
        for harpoon in harpoons:
            if not harpoon.is_off_screen():
                harpoons_to_keep.append(harpoon)
        harpoons = harpoons_to_keep

        # Remove pirates that have gone far off the left edge
        pirates_to_keep = []
        for pirate in pirates:
            if pirate.x > -200:
                pirates_to_keep.append(pirate)
        pirates = pirates_to_keep

        # Remove particles whose life has run out
        particles_to_keep = []
        for particle in particles:
            if particle.life > 0:
                particles_to_keep.append(particle)
        particles = particles_to_keep

        # Update all living particles
        for particle in particles:
            particle.update()

        # =====================================================
        # WAVE PROGRESSION
        # =====================================================
        # When all pirates in a wave have spawned AND been defeated,
        # move on to the next wave.

        if not boss_wave_active:
            if pirates_spawned == pirates_per_wave and len(pirates) == 0:

                # Wave clear bonus
                score += wave * 25

                next_wave = wave + 1

                # Wave 4 is the boss wave (triggers only once)
                if next_wave == 4 and not boss_wave_done:
                    wave             = 4
                    boss_wave_active = True
                    pirates_spawned  = pirates_per_wave  # stop normal spawning

                    show_boss_screen()

                    # Create the boss and two minion pirates
                    boss = Boss()
                    pirates.append(Pirate(WIDTH,      random.randint(TOP_BARRIER, HEIGHT - 150)))
                    pirates.append(Pirate(WIDTH + 80, random.randint(TOP_BARRIER, HEIGHT - 150)))

                else:
                    # Normal wave transition
                    wave            = next_wave
                    pirates_per_wave += 2   # each wave has 2 more pirates
                    pirates_spawned  = 0
                    spawn_timer      = 0
                    show_wave_screen(wave)

        # =====================================================
        # SCORE TRICKLE
        # =====================================================
        # Score slowly increases just for surviving (distance score)

        score += 1

        # =====================================================
        # DRAW EVERYTHING
        # =====================================================

        # 1. Background
        screen.blit(background_img, (0, 0))

        # 2. Boss (drawn behind pirates so minions appear in front)
        if boss is not None:
            boss.draw()

        # 3. Pirates
        for pirate in pirates:
            pirate.draw()

        # 4. Harpoons
        for harpoon in harpoons:
            harpoon.draw()

        # 5. Player
        # When invincible, Jerry flickers by skipping alternate draw calls
        if invincibility_timer == 0 or (invincibility_timer // 6) % 2 == 0:
            player.draw()

        # 6. Particles
        for particle in particles:
            particle.draw()

        # 7. HUD (drawn last so it appears on top of everything)
        draw_hud(score // 10, lives, wave, harpoon_cooldown)

        # Show "BOSS WAVE" in red over the wave counter during wave 4
        if boss_wave_active:
            draw_text_centered_shadow("BOSS  WAVE", font_medium, RED,
                                       WIDTH // 2, 25, shadow_colour=(60, 0, 0))

        # 8. Show the finished frame
        pygame.display.flip()

    # The while loop ended because lives reached 0.
    # Show the game over screen and return what the player chose.
    return show_game_over_screen(score // 10, wave)


# =============================================================
# ENTRY POINT
# This is where the program starts running.
# =============================================================

# Show the start screen once
show_start_screen()

# Keep running games until the player quits
while True:
    result = run_game()

    if result == "quit":
        break
    # If result == "restart", the while loop runs run_game() again

pygame.quit()
