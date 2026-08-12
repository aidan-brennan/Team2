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
    surf = pygame.Surface((70, 40), pygame.SRCALPHA)
    pygame.draw.polygon(surf, (250, 200, 60), [(0, 20), (45, 4), (45, 36)])
    pygame.draw.polygon(surf, (240, 140, 40), [(45, 12), (70, 20), (45, 28)])
    pygame.draw.circle(surf, (20, 20, 20), (18, 18), 3)
    return surf

def make_harpoon_surface():
    surf = pygame.Surface((40, 10), pygame.SRCALPHA)
    pygame.draw.line(surf, (170, 130, 90), (0, 5), (32, 5), 3)
    pygame.draw.polygon(surf, (200, 200, 210), [(32, 0), (40, 5), (32, 10)])
    return surf

def make_shark_surface():
    surf = pygame.Surface((100, 50), pygame.SRCALPHA)
    pygame.draw.polygon(surf, (110, 120, 130), [(0, 25), (75, 5), (100, 25), (75, 45)])
    pygame.draw.polygon(surf, (90, 100, 110), [(30, 5), (45, -12), (55, 5)])
    pygame.draw.polygon(surf, (70, 80, 90), [(0, 25), (20, 15), (20, 35)])
    pygame.draw.circle(surf, (250, 250, 250), (78, 18), 3)
    return surf

def make_jellyfish_surface():
    """Procedural jellyfish: dome bell + dangling tentacles."""
    w, h = 60, 80
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    # Bell (semi-circle dome)
    bell_color  = (180, 100, 220, 200)
    bell_rim    = (220, 160, 255, 220)
    pygame.draw.ellipse(surf, bell_color, (4, 0, w - 8, 44))
    pygame.draw.ellipse(surf, bell_rim,   (4, 0, w - 8, 44), 2)
    # Highlight shimmer
    pygame.draw.ellipse(surf, (240, 200, 255, 80), (12, 4, 18, 14))
    # Tentacles
    tentacle_color = (200, 120, 240, 160)
    for i, tx in enumerate([10, 20, 30, 40, 50]):
        wave_off = (i % 2) * 6
        for seg in range(5):
            sy = 38 + seg * 8 + wave_off
            pygame.draw.circle(surf, tentacle_color, (tx, sy), 2)
    return surf

def make_mapfrag_surface():
    """Fallback if mapfrag1.png is missing."""
    size = 40
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    points = [(size/2, 0),(size, size*0.4),(size*0.75, size),(size*0.25, size),(0, size*0.4)]
    pygame.draw.polygon(surf, (250, 210, 90), points)
    pygame.draw.polygon(surf, (255, 255, 255), points, 2)
    return surf

def make_background_tile():
    tile = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    top_color = pygame.Color(30, 110, 160)
    bottom_color = pygame.Color(5, 40, 80)
    for y in range(WINDOW_HEIGHT):
        t = y / WINDOW_HEIGHT
        color = top_color.lerp(bottom_color, t)
        pygame.draw.line(tile, color, (0, y), (WINDOW_WIDTH, y))
    for _ in range(25):
        pos = (randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT))
        radius = randint(1, 3)
        pygame.draw.circle(tile, (255, 255, 255, 40), pos, radius)
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

shark_surf = scale_surface(load_or_placeholder('images/shark1.png', make_shark_surface), SHARK_SCALE)

boss_shark_surf = scale_surface(shark_surf, BOSS_EXTRA_SCALE).copy()
_tint = pygame.Surface(boss_shark_surf.get_size(), pygame.SRCALPHA)
_tint.fill((255, 110, 110, 255))
boss_shark_surf.blit(_tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

background_surf = load_or_placeholder('images/background.jpeg', make_background_tile, alpha=False)
bg_width, bg_height = background_surf.get_size()
WORLD_BOUNDS = pygame.Rect(0, 0, bg_width, bg_height)

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
        self.rect.clamp_ip(WORLD_BOUNDS)
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
# Shark enemy  (enhanced: full tail-fin swim animation via body tilt + scale pulse)
# ---------------------------------------------------------------------------
class Shark(pygame.sprite.Sprite):
    def __init__(self, pos, groups, is_boss=False, speed_mult=1.0, health_bonus=0):
        super().__init__(groups)
        self.is_boss  = is_boss
        self.base_surf = boss_shark_surf if is_boss else shark_surf
        self.image     = self.base_surf
        self.rect      = self.image.get_frect(center=pos)
        self.pos       = pygame.Vector2(pos)

        if is_boss:
            self.speed     = uniform(70, 100) * speed_mult
            self.max_health = 10 + health_bonus * 3
        else:
            self.speed     = uniform(90, 160) * speed_mult
            self.max_health = 2 + health_bonus

        self.health = self.max_health

        # Swim animation state
        self.swim_cycle   = uniform(0, 2 * pi)    # random phase so sharks don't sync
        self.swim_speed   = uniform(4.0, 6.5)     # tail-stroke frequency
        self.tilt_amount  = uniform(9, 15)         # degrees of body rock
        self.scale_pulse  = uniform(0.025, 0.045)  # subtle size breath

        # Wobble (lateral drift while chasing)
        self.wobble_timer  = uniform(0, 10)
        self.wobble_amount = uniform(20, 45)
        self.facing_right  = True

        self.bob_offset = 0.0
        self.bob_timer  = uniform(0, 10)

    def update(self, dt):
        self.swim_cycle  += dt * self.swim_speed
        self.wobble_timer += dt
        self.bob_timer   += dt

        # Chase player
        to_player = pygame.Vector2(player.rect.center) - self.pos
        if to_player.length() > 0:
            forward = to_player.normalize()
        else:
            forward = pygame.Vector2(1, 0)

        perpendicular = pygame.Vector2(-forward.y, forward.x)
        wobble = sin(self.wobble_timer * 2.2) * self.wobble_amount

        self.pos += forward * self.speed * dt
        self.pos += perpendicular * wobble * dt

        # Flip for direction
        should_face_right = forward.x > 0
        if should_face_right != self.facing_right:
            self.facing_right = should_face_right

        base = self.base_surf if self.facing_right else pygame.transform.flip(self.base_surf, True, False)

        # Body tilt swim animation
        tilt = sin(self.swim_cycle) * self.tilt_amount
        # Subtle scale pulse (breathe effect)
        pulse = 1.0 + sin(self.swim_cycle * 0.5) * self.scale_pulse
        w, h  = base.get_size()
        scaled = pygame.transform.smoothscale(base, (max(1, round(w * pulse)), max(1, round(h * pulse))))
        self.image = pygame.transform.rotate(scaled, tilt if self.facing_right else -tilt)

        # Bob offset for CameraGroup
        self.bob_offset = sin(self.bob_timer * 2.8) * 4

        old_center = self.pos
        self.rect = self.image.get_frect(center=old_center)
        self.rect.clamp_ip(WORLD_BOUNDS)
        self.pos = pygame.Vector2(self.rect.center)

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
    SHOOT_INTERVAL_MIN = 2.2   # seconds between shots (min)
    SHOOT_INTERVAL_MAX = 4.0   # seconds between shots (max)

    def __init__(self, pos, groups, speed_mult=1.0):
        super().__init__(groups)
        self.base_surf   = jellyfish_surf
        self.image       = self.base_surf
        self.rect        = self.image.get_frect(center=pos)
        self.pos         = pygame.Vector2(pos)

        self.max_health  = 1          # dies in one harpoon hit
        self.health      = self.max_health
        self.speed       = uniform(45, 75) * speed_mult

        # Bell pulse animation
        self._pulse_timer  = uniform(0, 2 * pi)
        self._pulse_speed  = uniform(2.5, 4.0)

        # Gentle drift — jellyfish don't charge, they meander toward the player
        self._drift_timer  = uniform(0, 10)
        self._drift_amount = uniform(15, 35)

        # Shooting
        self._shoot_timer = uniform(0, self.SHOOT_INTERVAL_MAX)
        self._next_shot   = uniform(self.SHOOT_INTERVAL_MIN, self.SHOOT_INTERVAL_MAX)

        self.bob_offset  = 0.0
        self._bob_timer  = uniform(0, 10)

    def update(self, dt):
        self._pulse_timer += dt * self._pulse_speed
        self._drift_timer += dt
        self._bob_timer   += dt

        # Drift gently toward player
        to_player = pygame.Vector2(player.rect.center) - self.pos
        if to_player.length() > 0:
            forward = to_player.normalize()
        else:
            forward = pygame.Vector2(0, 1)

        perp   = pygame.Vector2(-forward.y, forward.x)
        drift  = sin(self._drift_timer * 1.4) * self._drift_amount
        self.pos += (forward * self.speed + perp * drift) * dt
        self.pos  = pygame.Vector2(
            min(max(self.pos.x, WORLD_BOUNDS.left),  WORLD_BOUNDS.right),
            min(max(self.pos.y, WORLD_BOUNDS.top),   WORLD_BOUNDS.bottom),
        )

        # Bell scale pulse (inhale/exhale)
        pulse = 1.0 + sin(self._pulse_timer) * 0.12
        w, h  = self.base_surf.get_size()
        self.image = pygame.transform.smoothscale(
            self.base_surf, (max(1, round(w * pulse)), max(1, round(h * (0.92 + 0.08 * pulse))))
        )
        self.rect = self.image.get_frect(center=self.pos)

        self.bob_offset = sin(self._bob_timer * 2.2) * 5

        # Shooting — fire at player
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
all_sprites      = CameraGroup()
harpoon_sprites  = pygame.sprite.Group()
shark_sprites    = pygame.sprite.Group()
jellyfish_sprites = pygame.sprite.Group()
bolt_sprites     = pygame.sprite.Group()
bubble_sprites   = pygame.sprite.Group()
fragment_sprites = pygame.sprite.Group()

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

AMBIENT_BUBBLE_EVENT = pygame.USEREVENT + 1
SHARK_SPAWN_EVENT    = pygame.USEREVENT + 2
pygame.time.set_timer(AMBIENT_BUBBLE_EVENT, 250)


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
        y = randint(WORLD_BOUNDS.top  + margin, WORLD_BOUNDS.bottom - margin)
        if pygame.Vector2(x, y).distance_to(player.rect.center) > 300:
            Shark((x, y), (all_sprites, shark_sprites),
                  is_boss=is_boss,
                  speed_mult=cfg["speed_mult"],
                  health_bonus=cfg["health_bonus"])
            sharks_spawned_this_wave += 1
            return
    x = randint(WORLD_BOUNDS.left + margin, WORLD_BOUNDS.right - margin)
    y = randint(WORLD_BOUNDS.top  + margin, WORLD_BOUNDS.bottom - margin)
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
        y = randint(WORLD_BOUNDS.top  + margin, WORLD_BOUNDS.bottom - margin)
        if pygame.Vector2(x, y).distance_to(player.rect.center) > 300:
            Jellyfish((x, y), (all_sprites, jellyfish_sprites),
                      speed_mult=cfg["speed_mult"])
            jellies_spawned_this_wave += 1
            return
    x = randint(WORLD_BOUNDS.left + margin, WORLD_BOUNDS.right - margin)
    y = randint(WORLD_BOUNDS.top  + margin, WORLD_BOUNDS.bottom - margin)
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
        bar_y = 10

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
        display_surface.blit(label_surf, label_surf.get_frect(midbottom=(WINDOW_WIDTH // 2, bar_y - 2)))

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
    for sprite in list(shark_sprites):     sprite.kill()
    for sprite in list(jellyfish_sprites): sprite.kill()
    for sprite in list(bolt_sprites):      sprite.kill()
    for sprite in list(harpoon_sprites):   sprite.kill()
    for sprite in list(bubble_sprites):    sprite.kill()
    for sprite in list(fragment_sprites):  sprite.kill()
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
