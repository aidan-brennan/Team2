# =============================================================
# IMPORTS
# =============================================================

import pygame
import random
import math
from os.path import join, dirname, abspath

# =============================================================
# SCREEN
# =============================================================
# NOTE: pygame.init() and the display surface are now owned by
# main.py.  This module receives its screen Surface as a parameter
# to run_level3() (see ENTRY POINT / run_level3 near the bottom of
# this file).  "screen" is kept as a module-level global so every
# function below (drawing, HUD, etc.) can keep using it unchanged.

WIDTH  = 1000
HEIGHT = 600

screen = None   # assigned inside run_level3()

# Safety net for standalone testing ONLY (`python lvl3.py`).
# Python executes this file top-to-bottom, so the `if __name__ ==
# "__main__":` block way down at the bottom of the file would run too
# late to help the module-level asset loading below (pygame.image.load
# .convert()/.convert_alpha(), pygame.mixer.Sound(), pygame.font.SysFont,
# pygame.time.Clock() all need pygame.init()/display/mixer already done).
# When this module is imported normally by main.py, main.py has already
# called pygame.init() (and mixer.init()) before the import happens, so
# pygame.get_init() is already True here and this block is skipped —
# main.py still fully owns pygame's lifecycle in the normal flow.
if __name__ == "__main__" and not pygame.get_init():
    pygame.init()
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

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

# How many frames between each pirate walk animation frame swap.
# 12 frames at 60fps = roughly 5 steps per second.
# Lower this number to make the animation faster, raise it to slow it down.
PIRATE_ANIM_SPEED = 12

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
# The Images folder lives inside this same directory (SeaBound/Images/)
# =============================================================

BASE_DIR   = dirname(abspath(__file__))
IMAGES_DIR = join(BASE_DIR, "Images")

# =============================================================
# LOAD IMAGES
# =============================================================

# Background
background_img = pygame.image.load(join(IMAGES_DIR, "shipwreck.png")).convert()
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

# =============================================================
# JERRY NORMAL WALKING FRAMES
# =============================================================
# Two frames that alternate while Jerry is moving.
# Frame 1 = walking_jerry1.png  (leg position A)
# Frame 2 = jerry_walk1.jpg     (leg position B — different pose)
#
# The jpg has a white background. We convert it to RGBA and then
# replace every near-white pixel with transparent so it looks clean.

def remove_white_background(surface):
    # Convert to a format that supports per-pixel alpha
    surface = surface.convert_alpha()
    w, h = surface.get_size()
    for x in range(w):
        for y in range(h):
            r, g, b, a = surface.get_at((x, y))
            # If the pixel is close to white, make it transparent
            if r > 220 and g > 220 and b > 220:
                surface.set_at((x, y), (r, g, b, 0))
    return surface

jerry_frame1 = pygame.image.load(join(IMAGES_DIR, "walking_jerry1.png")).convert_alpha()
jerry_frame1 = pygame.transform.scale(jerry_frame1, (85, 110))
jerry_frame1.set_colorkey(WHITE)

# Load the jpg, scale it, then strip the white background pixel by pixel
jerry_frame2_raw = pygame.image.load(join(IMAGES_DIR, "jerry_walk1.jpg")).convert()
jerry_frame2_raw = pygame.transform.scale(jerry_frame2_raw, (85, 110))
jerry_frame2     = remove_white_background(jerry_frame2_raw)

jerry_frame1_left = pygame.transform.flip(jerry_frame1, True, False)
jerry_frame2_left = pygame.transform.flip(jerry_frame2, True, False)

# =============================================================
# JERRY SWORD-IDLE AND SWORD-WALKING FRAMES
# =============================================================
# When Jerry has his sword out (after pressing SPACE) but is NOT
# swinging, we show a "sword held" idle pose.
# When he IS moving with the sword held, we animate between two
# sword-walk frames, exactly like the normal walking animation.
#
# jerryharpoon-r.png  = Jerry facing right holding sword (idle/walk frame A)
# jerryharpoon-l.png  = Jerry facing left  holding sword (idle/walk frame A)
# We use these as both the idle pose AND both walk frames so the
# sword stays visible.  If you create a second sword-walk frame later,
# add it to sword_walk_frames_right just like the normal walk frames.

sword_idle_right = pygame.image.load(join(IMAGES_DIR, "jerryharpoon-r.png")).convert_alpha()
sword_idle_right = pygame.transform.scale(sword_idle_right, (85, 110))
sword_idle_right.set_colorkey(WHITE)

sword_idle_left = pygame.image.load(join(IMAGES_DIR, "jerryharpoon-l.png")).convert_alpha()
sword_idle_left = pygame.transform.scale(sword_idle_left, (85, 110))
sword_idle_left.set_colorkey(WHITE)

# Sword-walking frame list (right-facing).
# Using the same image twice gives a subtle "bob" while walking.
# Replace sword_idle_right with a second distinct frame if you make one.
sword_walk_frames_right = [sword_idle_right, sword_idle_right]
sword_walk_frames_left  = [sword_idle_left,  sword_idle_left]

# =============================================================
# SWORD SWING ANIMATION FRAMES
# =============================================================
# The animation plays LOW → MEDIUM → HIGH → MEDIUM → LOW,
# which gives a clear wind-up → strike → follow-through feel.
#
# All frames are scaled to exactly (85, 110) — the same size as
# Jerry's normal walking sprites — so his body stays the same
# size during the attack.
#
# set_colorkey removes the white background just like the walk frames.
# Left-facing versions are pre-flipped so we don't flip every frame.

def load_sword_frame(filename):
    img = pygame.image.load(join(IMAGES_DIR, filename)).convert_alpha()
    img = pygame.transform.scale(img, (85, 110))   # SAME size as normal Jerry sprite
    img.set_colorkey(WHITE)
    return img

# 5 frames using the 3 reference images: LOW → MED → HIGH → MED → LOW
sword_swing_right = [
    load_sword_frame("jerry_sword_low.png"),    # frame 0: wind-up (sword low/back)
    load_sword_frame("jerry_sword.png"),         # frame 1: mid approach
    load_sword_frame("jerry_sword_high.png"),    # frame 2: full swing (sword high)
    load_sword_frame("jerry_sword.png"),         # frame 3: coming back through
    load_sword_frame("jerry_sword_low.png"),     # frame 4: follow-through / finish
]

# Pre-flip all 5 frames for when Jerry faces left
sword_swing_left = []
for frame in sword_swing_right:
    sword_swing_left.append(pygame.transform.flip(frame, True, False))

# Pirate — two walking frames for the animation
# Frame 0 = skeleton.png     (default / standing pose)
# Frame 1 = skeletonwalking 1.png  (mid-stride pose)
# Both are scaled to the same size as the original pirate sprite (150x120)
# so nothing else in the game changes.
pirate_walk_frame0 = pygame.image.load(join(IMAGES_DIR, "skeleton.png")).convert_alpha()
pirate_walk_frame0 = pygame.transform.scale(pirate_walk_frame0, (150, 120))

pirate_walk_frame1 = pygame.image.load(join(IMAGES_DIR, "skeletonwalking 1.png")).convert_alpha()
pirate_walk_frame1 = pygame.transform.scale(pirate_walk_frame1, (150, 120))

# Pre-flip both frames for left-side pirates (they face the other way)
pirate_walk_frame0_left = pygame.transform.flip(pirate_walk_frame0, True, False)
pirate_walk_frame1_left = pygame.transform.flip(pirate_walk_frame1, True, False)

# Keep pirate_img and pirate_img_left pointing at frame 0 so any other
# code that still references them continues to work unchanged.
pirate_img      = pirate_walk_frame0
pirate_img_left = pirate_walk_frame0_left

# Heart collectable
heart_img = pygame.image.load(join(IMAGES_DIR, "heart bubble.png")).convert_alpha()
heart_img = pygame.transform.scale(heart_img, (45, 45))
heart_img.set_colorkey(WHITE)

# =============================================================
# KEY IMAGE  (drawn in code — no external file needed)
# =============================================================
# We build a pixel-art golden key Surface at startup using
# pygame.draw calls.  This means you don't need an image file.
# The key is 40 x 20 pixels, gold coloured with a dark outline.

def make_key_image():
    surf = pygame.Surface((40, 20), pygame.SRCALPHA)

    GOLD      = (255, 200,  30)
    GOLD_DARK = (180, 130,   0)
    OUTLINE   = ( 40,  30,   0)

    # --- Key ring (circle on the left) ---
    pygame.draw.circle(surf, OUTLINE,  ( 9, 10), 9)       # outline
    pygame.draw.circle(surf, GOLD,     ( 9, 10), 7)       # fill
    pygame.draw.circle(surf, GOLD_DARK,( 9, 10), 4)       # inner shadow
    pygame.draw.circle(surf, GOLD,     ( 9, 10), 2)       # centre highlight

    # --- Key shaft ---
    pygame.draw.rect(surf, OUTLINE, (16,  7, 22,  6))     # outline rect
    pygame.draw.rect(surf, GOLD,    (17,  8, 20,  4))     # shaft fill

    # --- Key teeth (two notches on the bottom of the shaft) ---
    pygame.draw.rect(surf, OUTLINE, (28, 12,  4,  5))
    pygame.draw.rect(surf, GOLD,    (29, 13,  2,  4))

    pygame.draw.rect(surf, OUTLINE, (22, 12,  4,  4))
    pygame.draw.rect(surf, GOLD,    (23, 13,  2,  3))

    return surf

key_img = make_key_image()
# Scale up 3× so it's clearly visible on screen (120 x 60)
key_img = pygame.transform.scale(key_img, (120, 60))

# Bullet - fired from Jerry's gun toward the mouse cursor.
# We keep the original harpoon image at a readable size so it
# can be rotated cleanly to point in any direction.
# The base image faces RIGHT (0 degrees).  We rotate it each frame
# depending on the angle the bullet is travelling.
bullet_img_base = pygame.image.load(join(IMAGES_DIR, "harpoon.png")).convert_alpha()
bullet_img_base = pygame.transform.scale(bullet_img_base, (40, 14))
bullet_img_base.set_colorkey(WHITE)

# Boss - the Skeleton Captain (separate image, no tint needed)
# Scaled to 170x200: bigger than normal pirates (150x120) but not massive.
boss_base_img = pygame.image.load(join(IMAGES_DIR, "skeleton_captain.png")).convert_alpha()
boss_base_img = pygame.transform.scale(boss_base_img, (170, 200))
boss_base_img.set_colorkey(WHITE)

# =============================================================
# FONTS
# =============================================================

font_big    = pygame.font.SysFont("impact",  90)
font_large  = pygame.font.SysFont("impact",  52)
font_medium = pygame.font.SysFont("impact",  32)
font_small  = pygame.font.SysFont("verdana", 20, bold=True)
font_tiny   = pygame.font.SysFont("verdana", 16)


# =============================================================
# SOUNDS
# =============================================================
#
# Sound files live in the "Audio" folder inside SeaBound/.
# Path:  SeaBound/Audio/footstep.wav  etc.
#
# HOW TO ADD YOUR OWN SOUNDS:
#   1. Create the folder:  SeaBound/Audio/
#   2. Put .wav (or .ogg) files in it with the names listed below.
#   3. Run the game — the sounds will play automatically.
#
# If a sound file is missing, the game will NOT crash.
# It just prints a message and continues without that sound.
#
# VOLUMES:
#   Music volume is set lower than sound effects on purpose.
#   Change the numbers (0.0 = silent, 1.0 = full volume):
MUSIC_VOLUME  = 0.35   # background music volume
SFX_VOLUME    = 0.7    # sound effects volume

AUDIO_DIR = join(BASE_DIR, "Audio")

def load_sound(filename):
    """
    Try to load a sound file.
    If the file is missing, return None instead of crashing.
    The game checks for None before playing, so nothing breaks.
    """
    path = join(AUDIO_DIR, filename)
    try:
        sound = pygame.mixer.Sound(path)
        sound.set_volume(SFX_VOLUME)
        return sound
    except Exception:
        print(f"[Sound] Could not load: {filename}  (add it to SeaBound/Audio/ to hear it)")
        return None

# NOTE: pygame.mixer initialisation (pre_init/init) is now owned by
# main.py (or by the __main__ guard at the bottom of this file when
# run standalone) — it must happen before this module is imported so
# that the pygame.mixer.Sound(...) calls below succeed.

# ------------------------------------------------------------------
# LOAD ALL SOUND EFFECTS
# Each variable is either a pygame.mixer.Sound object or None.
# ------------------------------------------------------------------

sound_footstep    = load_sound("footstep.wav")      # plays while Jerry walks
sound_sword_hit   = load_sound("sword_hit.wav")     # sword hits a pirate/boss
sound_bullet_hit  = load_sound("bullet_hit.wav")    # bullet hits an enemy

# ------------------------------------------------------------------
# SWORD SWING SOUND
# Put your sword swing sound filename below (file goes in SeaBound/Audio/)
# ------------------------------------------------------------------
SWORD_SWING_SOUND_PATH = "sword attack.ogg"   # <-- SeaBound/Audio/sword attack.ogg
sound_sword_swing = load_sound(SWORD_SWING_SOUND_PATH)

# ------------------------------------------------------------------
# JERRY HURT SOUND
# Change the filename below to use your own sound file.
# The file must be placed in SeaBound/Audio/
# ------------------------------------------------------------------
JERRY_HURT_SOUND_PATH = "jerry damage.ogg"
sound_player_hit = load_sound(JERRY_HURT_SOUND_PATH)

# Harpoon / gun fired
sound_shoot = load_sound("gun_shot.mp3")

# ------------------------------------------------------------------
# PIRATE DEATH SOUNDS  (3 variants — one is chosen at random each kill)
# Put the filenames below.  All files go in SeaBound/Audio/
# ------------------------------------------------------------------
PIRATE_DEATH_SOUND_1 = "pirate_death 1.ogg"   # <-- SeaBound/Audio/pirate_death 1.ogg
PIRATE_DEATH_SOUND_2 = "pirate_death 2.ogg"   # <-- SeaBound/Audio/pirate_death 2.ogg
PIRATE_DEATH_SOUND_3 = "pirate_death 3.ogg"   # <-- SeaBound/Audio/pirate_death 3.ogg

sound_enemy_death_1 = load_sound(PIRATE_DEATH_SOUND_1)
sound_enemy_death_2 = load_sound(PIRATE_DEATH_SOUND_2)
sound_enemy_death_3 = load_sound(PIRATE_DEATH_SOUND_3)

# List of the 3 death sounds — random.choice() picks one when a pirate dies
pirate_death_sounds = [sound_enemy_death_1, sound_enemy_death_2, sound_enemy_death_3]

# Keep sound_enemy_death pointing at sound 1 so boss-death and any
# other existing play_sound(sound_enemy_death) calls still work
sound_enemy_death = sound_enemy_death_1

sound_boss_hit    = load_sound("boss_hit.wav")      # boss takes a hit
sound_game_over   = load_sound("game_over.wav")     # player runs out of lives
sound_wave_start  = load_sound("wave_start.wav")    # new wave begins

def play_sound(sound):
    """Play a sound if it loaded successfully.  Safe to call with None."""
    if sound is not None:
        sound.play()

# ------------------------------------------------------------------
# BACKGROUND MUSIC
# ------------------------------------------------------------------
# Music files also go in SeaBound/Audio/.
# The game switches tracks at certain points.
#
# MUSIC_GAMEPLAY  plays during normal waves
# MUSIC_BOSS      plays during the boss fight
# MUSIC_GAMEOVER  plays on the game over screen

MUSIC_GAMEPLAY = join(AUDIO_DIR, "music_gameplay.ogg")
MUSIC_BOSS     = join(AUDIO_DIR, "music_boss.ogg")
MUSIC_GAMEOVER = join(AUDIO_DIR, "music_gameover.ogg")

def play_music(filepath):
    """
    Start a music track looping.
    If the file is missing, stop any current music and continue silently.
    """
    try:
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.set_volume(MUSIC_VOLUME)
        pygame.mixer.music.play(-1)   # -1 = loop forever
    except Exception:
        pygame.mixer.music.stop()
        print(f"[Music] Could not load: {filepath}  (add it to SeaBound/Audio/)")

def stop_music():
    pygame.mixer.music.stop()

# ------------------------------------------------------------------
# FOOTSTEP TIMER
# ------------------------------------------------------------------
# We don't play the footstep sound every single frame —
# that would be an annoying rapid-fire noise.
# Instead we count frames and play it every FOOTSTEP_INTERVAL frames.
FOOTSTEP_INTERVAL = 22   # frames between each footstep sound (~2.7 steps/sec at 60fps)
footstep_timer    = 0    # counts up; reset when it reaches FOOTSTEP_INTERVAL


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
        # True while the sword swing animation is playing
        self.attacking = False

        # attack_timer counts down from 25 to 0 during the swing.
        # 5 animation frames × 5 ticks each = 25 ticks total.
        self.attack_timer = 0

        # Which of the 5 sword swing images to show (0 to 4)
        self.sword_frame = 0

        # Counts down between attacks (prevents spamming)
        self.attack_cooldown = 0

    def move(self):
        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        # Arrow keys OR WASD — both work, existing mechanics unchanged
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
            self.facing_right = False

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
            self.facing_right = True

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
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
            self.attack_timer    = 25   # 5 frames × 5 ticks each
            self.sword_frame     = 0
            self.attack_cooldown = 35

    def update_attack(self):
        if self.attack_timer > 0:
            self.attack_timer -= 1
            bucket = int((self.attack_timer - 1) / 5)
            self.sword_frame = 4 - bucket
        else:
            self.attacking   = False
            self.sword_frame = 0

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def get_sword_rect(self):
        # Returns the collision box for the sword while attacking.
        # Returns an empty rectangle (size 0) when not attacking.
        #
        # The hitbox moves with the animation:
        #   Early frames (wind-up)  → hitbox is close to Jerry
        #   Middle frames (swing)   → hitbox extends further out
        #   Late frames (finish)    → hitbox is below/forward
        if not self.attacking:
            return pygame.Rect(0, 0, 0, 0)

        # Hitbox offsets per frame — all coordinates are relative to self.x / self.y.
        # The sword stays within the 85x110 sprite so reach is more compact.
        # frame 0 (LOW  - wind-up):  sword is low/back
        # frame 1 (MED  - approach): sword coming forward
        # frame 2 (HIGH - strike):   sword at full height/reach
        # frame 3 (MED  - return):   sword coming back
        # frame 4 (LOW  - finish):   sword low again
        offsets_right = [
            (40,  60, 40, 35),   # frame 0  low/wind-up
            (50,  30, 45, 35),   # frame 1  approaching
            (55,   5, 50, 40),   # frame 2  high strike — full reach
            (50,  30, 45, 35),   # frame 3  returning
            (40,  60, 40, 35),   # frame 4  low/finish
        ]

        # For left-facing, mirror the x offset
        offsets_left = [
            ( 5,  60, 40, 35),   # frame 0
            ( 0,  30, 45, 35),   # frame 1
            (-20,  5, 50, 40),   # frame 2  full reach to the left
            ( 0,  30, 45, 35),   # frame 3
            ( 5,  60, 40, 35),   # frame 4
        ]

        f = self.sword_frame   # which frame (0–4)

        if self.facing_right:
            ox, oy, ow, oh = offsets_right[f]
            return pygame.Rect(self.x + ox, self.y + oy, ow, oh)
        else:
            ox, oy, ow, oh = offsets_left[f]
            return pygame.Rect(self.x + ox, self.y + oy, ow, oh)

    def draw(self):
        if self.attacking:
            # --- SWORD SWING ---
            # Show the sword swing animation frame while attacking
            if self.facing_right:
                image = sword_swing_right[self.sword_frame]
            else:
                image = sword_swing_left[self.sword_frame]
            screen.blit(image, (self.x, self.y))

            if SHOW_HITBOXES:
                pygame.draw.rect(screen, YELLOW, self.get_sword_rect(), 2)

        else:
            # --- NORMAL WALK / IDLE ---
            # anim_frame is 0 or 1, toggled by update_animation()
            # Both use walking_jerry1.png (you can add a second image later)
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

    def __init__(self, x, y, from_left=False, wave=1):
        self.x = x
        self.y = y

        self.width  = 150
        self.height = 120

        # from_left = True  means this pirate came from the LEFT edge
        # from_left = False means it came from the RIGHT edge (original behaviour)
        self.from_left = from_left

        # Use the pre-flipped image — no transform work at runtime
        if from_left:
            self.image = pirate_img_left   # faces RIGHT (toward screen centre)
        else:
            self.image = pirate_img        # faces LEFT  (toward screen centre)

        # ---------------------------------------------------------
        # HP SYSTEM
        # ---------------------------------------------------------
        # Wave 1: all pirates have 1 HP (one hit = dead).
        # Wave 2+: some pirates are "tough" with 2 HP.
        #   The chance of being tough increases each wave:
        #     Wave 2: 30% tough
        #     Wave 3: 50% tough
        #     Wave 4+: 70% tough
        # A tough pirate takes TWO hits to kill.
        # ---------------------------------------------------------
        if wave >= 2:
            # Calculate chance of being tough based on wave number
            tough_chance = min(0.30 + (wave - 2) * 0.20, 0.70)
            self.is_tough = random.random() < tough_chance
        else:
            self.is_tough = False

        self.hp = 2 if self.is_tough else 1

        # ---------------------------------------------------------
        # SPEED
        # ---------------------------------------------------------
        # Base speed is PIRATE_SPEED.
        # Tough pirates are always slightly faster.
        # Additionally, ~30% of wave 2+ pirates get a random speed
        # boost regardless of toughness.
        # ---------------------------------------------------------
        base_speed = PIRATE_SPEED

        if self.is_tough:
            base_speed += 0.6    # tough pirates are noticeably faster

        if wave >= 2 and random.random() < 0.30:
            base_speed += random.uniform(0.3, 0.8)   # random bonus for some pirates

        self.speed = base_speed

        # Natural movement — each pirate steers toward a point that
        # drifts around Jerry rather than heading straight at him.
        self.offset_x      = random.randint(-120, 120)
        self.offset_y      = random.randint(-80,   80)
        self.wander_timer  = 0
        self.wander_change = random.randint(50, 130)

        # Sword damage guard — prevents a single sword swing hitting
        # the same pirate twice on consecutive frames.
        self.sword_hit_this_swing = False

        # ---------------------------------------------------------
        # WALKING ANIMATION
        # ---------------------------------------------------------
        # anim_frame is 0 or 1 — which of the two walk images to show.
        # anim_timer counts up every frame the pirate is moving.
        # When anim_timer reaches PIRATE_ANIM_SPEED it flips the frame
        # and resets.  Change PIRATE_ANIM_SPEED to adjust the speed:
        #   lower number  = faster animation
        #   higher number = slower animation
        self.anim_frame = 0   # start on frame 0 (default pose)
        self.anim_timer = 0   # counts frames since the last frame swap

    def move_towards_player(self, player):
        # =======================================================
        # HOW THE NATURAL MOVEMENT WORKS
        # =======================================================
        # Instead of always heading straight at Jerry's exact
        # position, each pirate chases a "wobble target" — a point
        # that drifts around Jerry in a slow random circle.
        #
        # Every wander_change frames we pick new random offsets
        # (offset_x, offset_y) from Jerry's position.  The pirate
        # steers toward (Jerry + offset) rather than Jerry directly.
        # This makes them approach from angles, circle around, and
        # change pace in a way that looks far more natural.
        # =======================================================

        # The point we are actually steering toward this moment
        target_x = player.x + self.offset_x
        target_y = player.y + self.offset_y

        dx = target_x - self.x
        dy = target_y - self.y

        # Work out how far we are from that target
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > 0:
            # Normalise and apply speed so movement is smooth
            # at any distance rather than snapping to the target
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        # Every wander_change frames, pick a fresh offset around Jerry.
        # Large offsets = wide circling; small offsets = close approach.
        # We also vary the speed slightly each time for extra personality.
        self.wander_timer += 1
        if self.wander_timer >= self.wander_change:
            self.wander_timer  = 0
            self.wander_change = random.randint(50, 130)
            # Offset range: ±120px horizontally, ±80px vertically
            self.offset_x = random.randint(-120, 120)
            self.offset_y = random.randint(-80, 80)
            # Occasionally speed up or slow down
            self.speed = PIRATE_SPEED + random.uniform(-0.5, 0.8)

        # ---------------------------------------------------------
        # WALK ANIMATION TIMER
        # ---------------------------------------------------------
        # Count up every frame the pirate is moving.
        # When the timer hits PIRATE_ANIM_SPEED, swap the frame.
        self.anim_timer += 1
        if self.anim_timer >= PIRATE_ANIM_SPEED:
            self.anim_timer = 0
            # Toggle between frame 0 and frame 1
            if self.anim_frame == 0:
                self.anim_frame = 1
            else:
                self.anim_frame = 0

        if self.y < TOP_BARRIER:
            self.y = TOP_BARRIER
        if self.y > HEIGHT - self.height:
            self.y = HEIGHT - self.height

    def take_damage(self, particles_list):
        """
        Reduce HP by 1.  Spawns a small hit flash.
        Returns True if the pirate is now dead (HP reached 0).
        """
        self.hp -= 1

        # Small orange flash where the pirate was hit
        cx = self.x + self.width  // 2
        cy = self.y + self.height // 2
        for i in range(8):
            particles_list.append(Particle(cx, cy))

        return self.hp <= 0

    def draw(self):
        # Pick the correct walk frame based on anim_frame (0 or 1)
        # and which side the pirate came from (left or right).
        if self.from_left:
            # Left-side pirates face right — use the left-flipped versions
            if self.anim_frame == 0:
                image = pirate_walk_frame0_left
            else:
                image = pirate_walk_frame1_left
        else:
            # Right-side pirates face left — use the normal versions
            if self.anim_frame == 0:
                image = pirate_walk_frame0
            else:
                image = pirate_walk_frame1

        screen.blit(image, (self.x, self.y))

        # ---------------------------------------------------------
        # SMALL HP BAR — only drawn for tough (2 HP) pirates
        # ---------------------------------------------------------
        # We only show the bar when the pirate started with 2 HP.
        # Bar is small (50px wide, 5px tall) and sits just above
        # the pirate sprite so it doesn't clutter normal fights.
        # ---------------------------------------------------------
        if self.is_tough:
            bar_w = 50
            bar_h = 5
            bar_x = int(self.x + self.width // 2 - bar_w // 2)
            bar_y = int(self.y - 10)

            # Dark background track
            pygame.draw.rect(screen, (60, 0, 0), (bar_x, bar_y, bar_w, bar_h))

            # Fill — shrinks from full to half as HP drops from 2 to 1
            fill_w = int(bar_w * (self.hp / 2))
            bar_colour = (220, 60, 0) if self.hp == 1 else (220, 160, 0)
            pygame.draw.rect(screen, bar_colour, (bar_x, bar_y, fill_w, bar_h))

        if SHOW_HITBOXES:
            pygame.draw.rect(screen, RED, self.get_rect(), 2)

    def get_rect(self):
        return pygame.Rect(self.x + 30, self.y + 10, 90, 100)


# =============================================================
# HARPOON CLASS  (mouse-aimed, travels in any direction)
# =============================================================
#
# HOW MOUSE AIMING WORKS:
#   When Jerry shoots (left click or X), we:
#     1. Get the mouse position: mouse_x, mouse_y
#     2. Work out the direction from Jerry to the mouse:
#          dx = mouse_x - jerry_x
#          dy = mouse_y - jerry_y
#     3. Normalise this so the bullet always travels at the same
#        speed regardless of how far away the cursor is:
#          length = sqrt(dx*dx + dy*dy)
#          vx = dx / length * HARPOON_SPEED
#          vy = dy / length * HARPOON_SPEED
#     4. Every frame: bullet.x += vx,  bullet.y += vy
#
#   The image is rotated to point in the direction of travel so
#   it always looks like it's flying toward the cursor.

class Harpoon:

    def __init__(self, x, y, vx, vy):
        # Starting position (centre of the bullet)
        self.x = float(x)
        self.y = float(y)

        # Velocity components — how many pixels to move each frame
        # in the x and y directions.  These are set when the bullet
        # is fired and never change (it travels in a straight line).
        self.vx = vx
        self.vy = vy

        # Size of the drawn image (used for off-screen check)
        self.width  = 40
        self.height = 14

        # Work out the rotation angle from the velocity.
        # math.atan2 gives the angle in radians; we convert to degrees.
        # The base image faces RIGHT (0 degrees in our coordinate system).
        # Pygame rotates ANTI-clockwise, and screen y is flipped, so we
        # negate vy to get the correct visual rotation.
        angle_radians = math.atan2(-vy, vx)
        self.angle_degrees = math.degrees(angle_radians)

        # Pre-rotate the image once at creation time.
        # We don't need to rotate it every frame because the direction
        # never changes after firing.
        self.image = pygame.transform.rotate(bullet_img_base, self.angle_degrees)

    def move(self):
        self.x += self.vx
        self.y += self.vy

    def is_off_screen(self):
        # Remove when the centre of the bullet leaves the screen
        if self.x < -50 or self.x > WIDTH + 50:
            return True
        if self.y < -50 or self.y > HEIGHT + 50:
            return True
        return False

    def draw(self):
        # Draw the pre-rotated image centred on the bullet position
        img_rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(self.image, img_rect)

        if SHOW_HITBOXES:
            pygame.draw.rect(screen, CYAN, self.get_rect(), 2)

    def get_rect(self):
        # Small collision box centred on the bullet
        return pygame.Rect(int(self.x) - 10, int(self.y) - 6, 20, 12)


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
        # The Skeleton Captain is 170x200 — bigger than pirates (150x120)
        # but not so large it fills the screen
        self.width  = 170
        self.height = 200

        # Start off the right edge and move in
        self.x = WIDTH
        self.y = HEIGHT // 2 - 100   # roughly vertically centred in the play area

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
        # Position the bar above the boss sprite, centred on the captain
        bar_x = self.x + self.width // 2 - 110
        bar_y = self.y - 30
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
        # Smaller hitbox so transparent edges don't count.
        # The captain sprite is 170x200.
        # self.x + 30  = 30px in from the left
        # self.y + 20  = 20px down from the top
        # 110          = hitbox width
        # 160          = hitbox height
        return pygame.Rect(self.x + 30, self.y + 20, 110, 160)


# =============================================================
# HEART COLLECTABLE CLASS
# =============================================================
# One heart bubble spawns each wave at a random accessible spot.
# Jerry collects it by walking over it, gaining +1 life (max 5).
# It stays on screen until collected or the wave ends.

class Heart:

    SIZE = 45   # matches the scaled image size above

    def __init__(self):
        # Pick a random position that is:
        #   - below the HUD bar (TOP_BARRIER + a small gap)
        #   - away from all four edges so it is fully visible
        margin = 60
        self.x = random.randint(margin, WIDTH  - margin - self.SIZE)
        self.y = random.randint(TOP_BARRIER + 30, HEIGHT - margin - self.SIZE)

        self.width  = self.SIZE
        self.height = self.SIZE
        self.collected = False

        # Gentle bob animation so the heart looks alive
        self.bob_timer = 0     # counts up every frame
        self.bob_y     = 0.0   # vertical offset applied during draw

    def update(self):
        # bob_y oscillates between -4 and +4 pixels using a sine wave
        self.bob_timer += 0.08
        self.bob_y = math.sin(self.bob_timer) * 4

    def draw(self):
        if not self.collected:
            screen.blit(heart_img, (self.x, int(self.y + self.bob_y)))

            if SHOW_HITBOXES:
                pygame.draw.rect(screen, RED, self.get_rect(), 2)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


# =============================================================
# KEY CLASS
# =============================================================
# Drops from the Skeleton Captain when he dies.
# Has a pulsing gold aura drawn around it.
# Jerry walks over it to collect it, ending the game in victory.

class Key:

    WIDTH  = 120
    HEIGHT = 60

    def __init__(self, x, y):
        # Centre the key on where the boss died
        self.x = x - self.WIDTH  // 2
        self.y = y - self.HEIGHT // 2

        self.collected = False

        # Aura pulse — this number grows every frame and feeds into
        # math.sin() to make the glow expand and shrink smoothly.
        self.aura_pulse = 0.0

    def update(self):
        # Advance the pulse timer each frame (~1 full cycle per second)
        self.aura_pulse += 0.06

    def draw(self):
        if self.collected:
            return

        cx = self.x + self.WIDTH  // 2
        cy = self.y + self.HEIGHT // 2

        # --- Shining aura ---
        # We draw several concentric circles with low alpha.
        # Their radius pulses using sin() so they breathe in and out.
        # sin() goes between -1 and +1; we map that to a radius range.
        pulse_val   = math.sin(self.aura_pulse)           # -1 to +1
        aura_radius = int(55 + pulse_val * 15)            # 40 to 70 px

        # Draw 4 rings from largest (most transparent) to smallest
        for i in range(4):
            radius = aura_radius - i * 8
            if radius <= 0:
                continue
            alpha  = 30 + i * 20                          # 30, 50, 70, 90
            aura_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            # Gold colour: (255, 215, 0) with varying alpha
            pygame.draw.circle(aura_surf, (255, 215, 0, alpha),
                               (radius, radius), radius)
            screen.blit(aura_surf, (cx - radius, cy - radius))

        # --- Spinning sparkle crosses ---
        # Four small bright crosses orbit the key at the aura edge.
        for i in range(4):
            angle = self.aura_pulse * 1.5 + i * (math.pi / 2)
            sx = int(cx + math.cos(angle) * (aura_radius - 5))
            sy = int(cy + math.sin(angle) * (aura_radius - 5))
            pygame.draw.line(screen, (255, 255, 180), (sx - 4, sy), (sx + 4, sy), 2)
            pygame.draw.line(screen, (255, 255, 180), (sx, sy - 4), (sx, sy + 4), 2)

        # --- Key image ---
        screen.blit(key_img, (self.x, self.y))

        # Small "COLLECT KEY" prompt that pulses in brightness
        alpha_prompt = int(160 + 80 * math.sin(self.aura_pulse * 2))
        prompt = font_small.render("COLLECT THE KEY!", True, YELLOW)
        prompt.set_alpha(alpha_prompt)
        screen.blit(prompt, prompt.get_rect(center=(cx, self.y - 25)))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
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
    # NOTE: no longer called from run_level3() (main.py's own menu covers
    # "start game"), but kept functional/consistent in case it is ever
    # invoked directly.  Returns "quit" on window-close, None otherwise.
    waiting = True
    pulse   = 0   # used to make the "Press Enter" text pulse in brightness

    while waiting:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
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
    # Returns "quit" if the window is closed during the announcement,
    # otherwise returns None once the announcement has finished playing.
    for frame in range(90):   # show for 90 frames (1.5 seconds at 60fps)
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

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
    # Returns "quit" if the window is closed during the announcement,
    # otherwise returns None once the announcement has finished playing.
    for frame in range(120):   # 2 seconds
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

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
                return "quit"
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
# WIN SCREEN
# Shown when the player defeats the Pirate Captain (the boss).
# This is the last level, so there is no "restart in place" here —
# pressing SPACE just tells run_level3() (and, above that, main.py)
# to move on.
# =============================================================

def show_win_screen(score, wave):
    waiting = True
    pulse   = 0

    while waiting:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return "win"

        pulse += 0.07
        pulse_alpha = int(160 + 80 * math.sin(pulse))

        screen.blit(background_img, (0, 0))

        # Dark gold/teal panel
        panel = pygame.Surface((700, 360), pygame.SRCALPHA)
        panel.fill((0, 30, 25, 210))
        screen.blit(panel, (150, 120))

        draw_text_centered_shadow("VICTORY!", font_big, YELLOW,
                                   WIDTH // 2, HEIGHT // 2 - 120,
                                   shadow_colour=(80, 60, 0))
        draw_text_centered("YOU DEFEATED THE PIRATE CAPTAIN", font_medium, CYAN,
                            WIDTH // 2, HEIGHT // 2 - 30)
        draw_text_centered(f"SCORE  {score}", font_large, YELLOW,
                            WIDTH // 2, HEIGHT // 2 + 40)

        pygame.draw.line(screen, CYAN, (220, HEIGHT // 2 + 90), (780, HEIGHT // 2 + 90), 2)

        prompt = font_small.render("PRESS  SPACE  TO  CONTINUE", True, WHITE)
        prompt.set_alpha(pulse_alpha)
        screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 125)))

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

    # Heart collectable - one per wave, None when not on screen
    heart = None

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

    # --- RANDOM SPAWNING ---
    # Instead of a fixed delay (always 120 frames), we pick a new
    # random delay after each spawn.  This makes enemy timing feel
    # unpredictable rather than perfectly metronomic.
    spawn_timer = 0
    spawn_delay = random.randint(60, 180)   # first delay is random too

    # Maximum pirates allowed on screen at once.
    # Prevents the game from becoming unfair or laggy.
    MAX_PIRATES = 6

    # Wave 4 is the boss wave.  These two flags track whether it has
    # been triggered and whether the boss fight is still ongoing.
    boss_wave_active = False
    boss_wave_done   = False

    # Set to True once the boss is defeated — ends the game loop in victory
    # instead of resuming pirate waves.
    level_won = False

    # Show the wave 1 announcement
    if show_wave_screen(wave) == "quit":
        return "quit"

    # Spawn the first heart collectable for wave 1
    heart = Heart()

    # Start gameplay music when the game begins
    play_music(MUSIC_GAMEPLAY)

    # Footstep sound timer — tracks frames since the last footstep sound
    footstep_timer = 0

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
                    play_sound(sound_sword_swing)

            # =====================================================
            # SHOOT — left mouse click OR X key
            # =====================================================
            # We fire on MOUSEBUTTONDOWN (button 1 = left click) or K_x.
            # Both use the same firing function defined below.

            shoot_pressed = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                shoot_pressed = True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_x:
                shoot_pressed = True

            if shoot_pressed and harpoon_cooldown == 0:
                # Get the current mouse position
                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Bullet spawns at the tip of Jerry's gun (front-centre of body)
                bullet_x = player.x + 55
                bullet_y = player.y + 50

                # Work out the direction from the gun to the mouse
                dx = mouse_x - bullet_x
                dy = mouse_y - bullet_y

                # Normalise: make the vector length = 1, then multiply by speed
                # This ensures the bullet always travels at HARPOON_SPEED
                # regardless of how far the cursor is from Jerry.
                length = math.sqrt(dx * dx + dy * dy)
                if length == 0:
                    length = 1   # prevent division by zero if cursor is on Jerry

                vx = (dx / length) * HARPOON_SPEED
                vy = (dy / length) * HARPOON_SPEED

                new_harpoon = Harpoon(bullet_x, bullet_y, vx, vy)
                harpoons.append(new_harpoon)
                play_sound(sound_shoot)

                harpoon_cooldown = HARPOON_COOLDOWN

                # Update facing direction based on where the cursor is
                player.facing_right = (mouse_x >= player.x)

        # =====================================================
        # UPDATE PLAYER
        # =====================================================

        player.move()
        player.update_animation()
        player.update_attack()

        # --- FOOTSTEP SOUND ---
        # Only play a footstep while Jerry is actually moving.
        # footstep_timer counts up each frame; when it hits FOOTSTEP_INTERVAL
        # we play the sound and reset the timer.
        if player.moving:
            footstep_timer += 1
            if footstep_timer >= FOOTSTEP_INTERVAL:
                footstep_timer = 0
                play_sound(sound_footstep)
        else:
            footstep_timer = 0   # reset when Jerry stops

        # Count down the harpoon cooldown each frame
        if harpoon_cooldown > 0:
            harpoon_cooldown -= 1

        # Count down invincibility after being hit
        if invincibility_timer > 0:
            invincibility_timer -= 1

        # =====================================================
        # HEART COLLECTABLE
        # =====================================================
        # Update the heart's bob animation each frame.
        # Check if Jerry has walked onto it.

        if heart is not None and not heart.collected:
            heart.update()

            if player.get_rect().colliderect(heart.get_rect()):
                heart.collected = True
                # Give Jerry +1 life, but never more than 3
                if lives < 3:
                    lives += 1
                # No damage sound on pickup — removed as requested

        # =====================================================
        # PIRATE SPAWNING
        # =====================================================
        # Pirates only spawn during normal waves (not the boss wave)

        if not boss_wave_active:
            spawn_timer += 1

            # Only spawn if:
            #   - enough time has passed (random delay)
            #   - we haven't spawned all pirates for this wave yet
            #   - there aren't too many pirates on screen already
            if (spawn_timer >= spawn_delay
                    and pirates_spawned < pirates_per_wave
                    and len(pirates) < MAX_PIRATES):

                spawn_timer = 0
                # Pick a NEW random delay for the NEXT spawn
                spawn_delay = random.randint(60, 180)

                spawn_y = random.randint(TOP_BARRIER + 20, HEIGHT - 150)

                # Randomly choose left or right side to spawn from
                side = random.choice(["left", "right"])

                if side == "left":
                    # Spawn just off the left edge, moving right
                    spawn_x    = -160          # starts off-screen left
                    from_left  = True
                else:
                    # Spawn just off the right edge, moving left
                    spawn_x    = WIDTH + 10    # starts off-screen right
                    from_left  = False

                # Don't spawn directly on top of Jerry
                # If the spawn y is very close to Jerry's y, nudge it
                if abs(spawn_y - player.y) < 60:
                    spawn_y += 80

                new_pirate = Pirate(spawn_x, spawn_y, from_left=from_left, wave=wave)
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

                    play_sound(sound_bullet_hit)    # bullet connects

                    # take_damage() returns True when the pirate is dead
                    is_dead = pirate.take_damage(particles)

                    if is_dead:
                        pirates.remove(pirate)
                        # Play a random death sound from the 3 options
                        play_sound(random.choice(pirate_death_sounds))
                        score += 10

                    if harpoon in harpoons:
                        harpoons.remove(harpoon)

                    break   # one harpoon can only hit one pirate

        # =====================================================
        # COLLISIONS - HARPOON vs BOSS
        # =====================================================

        if boss is not None:
            for harpoon in harpoons[:]:
                if harpoon.get_rect().colliderect(boss.get_rect()):
                    boss.take_damage(2)   # harpoon does 2 damage to boss
                    play_sound(sound_boss_hit)

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

        # Reset the sword-hit guard at the START of each new swing
        # (attack_timer == 24 is the very first tick of a swing)
        if player.attack_timer == 24:
            for pirate in pirates:
                pirate.sword_hit_this_swing = False

        for pirate in pirates[:]:
            if sword_rect.colliderect(pirate.get_rect()):
                # Only deal damage once per swing per pirate
                if not pirate.sword_hit_this_swing:
                    pirate.sword_hit_this_swing = True

                    play_sound(sound_sword_hit)

                    is_dead = pirate.take_damage(particles)

                    if is_dead:
                        pirates.remove(pirate)
                        # Play a random death sound from the 3 options
                        play_sound(random.choice(pirate_death_sounds))
                        score += 10

        # =====================================================
        # COLLISIONS - SWORD vs BOSS
        # =====================================================
        # attack_timer == 24 is the very first tick of the swing
        # (timer starts at 25 and counts down).
        # We only deal damage on that one tick so a single swing
        # can't hit the boss multiple times.

        if boss is not None:
            if sword_rect.colliderect(boss.get_rect()):
                if player.attack_timer == 24:
                    boss.take_damage(1)
                    play_sound(sound_boss_hit)

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
                    play_sound(sound_player_hit)   # Jerry gets hit

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
                    play_sound(sound_player_hit)   # Jerry gets hit by boss

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

            play_sound(sound_enemy_death)   # boss dies
            score            += 200
            boss              = None
            boss_wave_active  = False
            boss_wave_done    = True

            # Switch back to normal gameplay music for the victory moment
            play_music(MUSIC_GAMEPLAY)

            # The Pirate Captain was the final challenge of this level.
            # Defeating him wins the level — do NOT advance to another
            # wave or resume pirate spawning.  End the game loop so
            # run_game() can show the win screen.
            level_won = True
            running   = False

        # =====================================================
        # REMOVE OBJECTS THAT ARE NO LONGER NEEDED
        # =====================================================

        # Remove harpoons that have gone off screen
        harpoons_to_keep = []
        for harpoon in harpoons:
            if not harpoon.is_off_screen():
                harpoons_to_keep.append(harpoon)
        harpoons = harpoons_to_keep

        # Remove pirates that have gone far off either edge
        pirates_to_keep = []
        for pirate in pirates:
            if pirate.x > -200 and pirate.x < WIDTH + 200:
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

        if not boss_wave_active and not level_won:
            if pirates_spawned == pirates_per_wave and len(pirates) == 0:

                # Wave clear bonus
                score += wave * 25

                next_wave = wave + 1

                # Wave 4 is the boss wave (triggers only once)
                if next_wave == 4 and not boss_wave_done:
                    wave             = 4
                    boss_wave_active = True
                    pirates_spawned  = pirates_per_wave  # stop normal spawning

                    if show_boss_screen() == "quit":
                        return "quit"

                    # Switch to boss music for the big fight
                    play_music(MUSIC_BOSS)

                    # Create the boss and two minion pirates
                    boss = Boss()
                    pirates.append(Pirate(WIDTH,      random.randint(TOP_BARRIER, HEIGHT - 150)))
                    pirates.append(Pirate(WIDTH + 80, random.randint(TOP_BARRIER, HEIGHT - 150)))

                else:
                    # Normal wave transition
                    wave            = next_wave
                    pirates_per_wave += 2
                    pirates_spawned  = 0
                    spawn_timer      = 0
                    spawn_delay      = random.randint(60, 150)
                    play_sound(sound_wave_start)
                    if show_wave_screen(wave) == "quit":
                        return "quit"
                    # Spawn a fresh heart for the new wave
                    heart = Heart()

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

        # 2. Heart collectable (drawn before enemies so it sits on the floor)
        if heart is not None and not heart.collected:
            heart.draw()

        # 3. Boss (drawn behind pirates so minions appear in front)
        if boss is not None:
            boss.draw()

        # 4. Pirates
        for pirate in pirates:
            pirate.draw()

        # 5. Harpoons
        for harpoon in harpoons:
            harpoon.draw()

        # 6. Player
        if invincibility_timer == 0 or (invincibility_timer // 6) % 2 == 0:
            player.draw()

        # 7. Particles
        for particle in particles:
            particle.draw()

        # 8. HUD
        draw_hud(score // 10, lives, wave, harpoon_cooldown)

        # Show "BOSS WAVE" in red over the wave counter during wave 4
        if boss_wave_active:
            draw_text_centered_shadow("BOSS  WAVE", font_medium, RED,
                                       WIDTH // 2, 25, shadow_colour=(60, 0, 0))

        # 8. Show the finished frame
        pygame.display.flip()

    # The while loop ended either because the boss was defeated
    # (level_won) or because lives reached 0.
    if level_won:
        # Show the victory screen and return what the player chose.
        result = show_win_screen(score // 10, wave)
        stop_music()
        return result

    # Otherwise the loop ended because lives reached 0.
    # Stop gameplay/boss music and play the game over track.
    stop_music()
    play_music(MUSIC_GAMEOVER)
    play_sound(sound_game_over)

    # Show the game over screen and return what the player chose.
    result = show_game_over_screen(score // 10, wave)

    # Stop the game-over music before returning so it doesn't
    # keep playing if the player restarts.
    stop_music()
    return result


# =============================================================
# run_level3 - the entry point main.py calls to play this level
# =============================================================
#
# main.py owns pygame's lifecycle (pygame.init(), the display Surface,
# pygame.mixer.init(), and the final pygame.quit()).  It calls this
# function, handing it the Surface to draw onto plus the volumes the
# player has configured.  run_level3() never calls pygame.quit() itself.
#
# Returns one of:
#   "next" - the boss was defeated (level won) - main.py should advance
#            (this is the last level, so main.py shows its own
#            "you beat the game" / credits screen after this)
#   "menu" - reserved for a future "return to menu" flow (not currently
#            reachable from this level, kept for interface symmetry
#            with the other levels)
#   "quit" - the player closed the window - main.py should shut down

def run_level3(target_screen, music_volume=0.6, sfx_volume=0.7):
    global screen
    screen = target_screen

    # Apply the requested volumes to music and to every sound effect
    # that was loaded at import time (see the SOUNDS section above).
    pygame.mixer.music.set_volume(music_volume)

    for sound in (sound_footstep, sound_sword_swing, sound_sword_hit,
                  sound_shoot, sound_bullet_hit, sound_player_hit,
                  sound_enemy_death, sound_boss_hit, sound_game_over,
                  sound_wave_start):
        if sound is not None:
            sound.set_volume(sfx_volume)

    # NOTE: show_start_screen() is intentionally NOT called here.
    # main.py's own main menu already covers "start game" for the
    # whole game, so this level's duplicate title card is skipped
    # to avoid a redundant/confusing extra screen.

    # Keep running games until the player quits or wins
    while True:
        result = run_game()

        if result == "quit":
            return "quit"

        if result == "win":
            return "next"

        # If result == "restart", loop and call run_game() again


# =============================================================
# ENTRY POINT (standalone testing only)
# Lets this file be run directly with `python lvl3.py` for quick
# testing.  Normal play goes through main.py -> run_level3().
# =============================================================

if __name__ == "__main__":
    pygame.init()
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    _screen = pygame.display.set_mode((WIDTH, HEIGHT))
    run_level3(_screen)
    pygame.quit()
