import pygame
from random import randint, uniform, choice
from math import sin

# ---------------------------------------------------------------------------
# Self-contained prototype: every sprite is drawn procedurally, so it runs
# immediately with no external image files. To use your own art, swap the
# surfaces built in `make_*_surface()` for `pygame.image.load(path)` calls.
# ---------------------------------------------------------------------------

pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Underwater Harpoon")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 28)
big_font = pygame.font.SysFont("arial", 64, bold=True)


# ---------------------------------------------------------------------------
# Art loading — uses your real image files when present, and only falls
# back to a drawn placeholder if a specific file can't be found/loaded,
# so a missing asset (e.g. no shark image yet) won't crash the game.
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


# how much bigger sprites are drawn than their source art/placeholder size
PLAYER_SCALE = 1.5
HARPOON_SCALE = 1.2
SHARK_SCALE = 1.6
BOSS_EXTRA_SCALE = 1.9  # applied on top of SHARK_SCALE for the boss shark

player_surf = scale_surface(load_or_placeholder('images/jerryharpoon.png', make_player_surface), PLAYER_SCALE)

# crop the harpoon image down to its actual content, same as the original code
_harpoon_raw = load_or_placeholder('images/harpoon.png', make_harpoon_surface)
harpoon_surf = scale_surface(_harpoon_raw.subsurface(_harpoon_raw.get_bounding_rect()).copy(), HARPOON_SCALE)

# no shark asset yet -> falls back to the drawn placeholder automatically;
# drop a real file at images/shark.png (or change the path) whenever you have one
shark_surf = scale_surface(load_or_placeholder('images/shark1.png', make_shark_surface), SHARK_SCALE)

# boss shark: bigger still, with a reddish tint so it reads as distinct/dangerous
boss_shark_surf = scale_surface(shark_surf, BOSS_EXTRA_SCALE).copy()
_tint = pygame.Surface(boss_shark_surf.get_size(), pygame.SRCALPHA)
_tint.fill((255, 110, 110, 255))
boss_shark_surf.blit(_tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

background_surf = load_or_placeholder('images/background.jpeg', make_background_tile, alpha=False)
bg_width, bg_height = background_surf.get_size()

# the playable world is exactly the size of the background image -
# nothing scrolls or spawns past its edges
WORLD_BOUNDS = pygame.Rect(0, 0, bg_width, bg_height)


# ---------------------------------------------------------------------------
# Camera group
# ---------------------------------------------------------------------------
class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.offset = pygame.Vector2()

    def draw_background(self, target_pos):
        target_pos = pygame.Vector2(target_pos)

        # where the camera would like to be, centered on the player
        desired_x = target_pos.x - WINDOW_WIDTH / 2
        desired_y = target_pos.y - WINDOW_HEIGHT / 2

        # clamp so the camera never shows past the edge of the picture
        max_offset_x = max(bg_width - WINDOW_WIDTH, 0)
        max_offset_y = max(bg_height - WINDOW_HEIGHT, 0)
        self.offset.x = min(max(desired_x, 0), max_offset_x)
        self.offset.y = min(max(desired_y, 0), max_offset_y)

        display_surface.fill((0, 0, 0))  # letterbox bars if the image is smaller than the window
        display_surface.blit(background_surf, -self.offset)

    def draw_all(self, target_pos):
        self.draw_background(target_pos)
        for sprite in self.sprites():
            offset_pos = pygame.Vector2(sprite.rect.topleft) - self.offset
            offset_pos.y += getattr(sprite, "bob_offset", 0)
            display_surface.blit(sprite.image, offset_pos)

            if isinstance(sprite, Shark):
                self.draw_health_bar(sprite, offset_pos)

    def draw_health_bar(self, shark, screen_pos):
        bar_w = shark.rect.width * 0.8
        bar_h = 8 if shark.is_boss else 6
        bar_x = screen_pos.x + (shark.rect.width - bar_w) / 2
        bar_y = screen_pos.y - (bar_h + 10)

        ratio = max(0.0, shark.health / shark.max_health)
        pygame.draw.rect(display_surface, (30, 30, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        if ratio > 0.6:
            fill_color = (90, 220, 120)
        elif ratio > 0.3:
            fill_color = (250, 200, 60)
        else:
            fill_color = (220, 60, 60)
        pygame.draw.rect(display_surface, fill_color, (bar_x, bar_y, bar_w * ratio, bar_h), border_radius=3)
        pygame.draw.rect(display_surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=3)


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.normal_surf = player_surf
        self.image = self.normal_surf
        self.rect = self.image.get_frect(center=(WORLD_BOUNDS.centerx, WORLD_BOUNDS.centery))
        self.hitbox = self.rect.inflate(-self.rect.width * 0.3, -self.rect.height * 0.35)
        self.mask = pygame.mask.from_surface(self.image)
        self.direction = pygame.Vector2()
        self.speed = 500
        self.facing_right = False

        self.max_health = 3
        self.health = self.max_health
        self.invincible_until = 0
        self.invincible_duration = 1200
        self.alive = True

        self.can_shoot = True
        self.harpoon_shoot_time = 0
        self.cooldown_duration = 650

        self.bob_timer = uniform(0, 10)
        self.bob_offset = 0
        self.idle_bob_speed, self.idle_bob_amount = 3, 4
        self.swim_bob_speed, self.swim_bob_amount = 8, 7

        self.bubble_timer = 0
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

    def update_bob(self, dt, moving):
        self.bob_timer += dt
        speed = self.swim_bob_speed if moving else self.idle_bob_speed
        amount = self.swim_bob_amount if moving else self.idle_bob_amount
        self.bob_offset = sin(self.bob_timer * speed) * amount

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
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        self.direction = self.direction.normalize() if self.direction else self.direction
        moving = self.direction.length() > 0

        self.rect.center += self.direction * self.speed * dt
        self.rect.clamp_ip(WORLD_BOUNDS)
        old_center = self.rect.center

        if self.direction.x > 0:
            self.facing_right = True
            self.image = pygame.transform.flip(self.normal_surf, True, False)
        elif self.direction.x < 0:
            self.facing_right = False
            self.image = self.normal_surf

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


class Harpoon(pygame.sprite.Sprite):
    def __init__(self, surf, pos, direction, groups):
        super().__init__(groups)
        self.direction = direction
        angle = self.direction.angle_to(pygame.Vector2(-1, 0))
        self.image = pygame.transform.rotate(surf, angle)
        self.rect = self.image.get_frect(center=pos)

    def update(self, dt):
        self.rect.center += self.direction * 500 * dt
        if pygame.Vector2(self.rect.center).distance_to(player.rect.center) > \
                pygame.Vector2(WINDOW_WIDTH, WINDOW_HEIGHT).length():
            self.kill()


# ---------------------------------------------------------------------------
# Shark enemy
# ---------------------------------------------------------------------------
class Shark(pygame.sprite.Sprite):
    def __init__(self, pos, groups, is_boss=False):
        super().__init__(groups)
        self.is_boss = is_boss
        self.base_surf = boss_shark_surf if is_boss else shark_surf
        self.image = self.base_surf
        self.rect = self.image.get_frect(center=pos)
        self.pos = pygame.Vector2(pos)

        if is_boss:
            self.speed = uniform(70, 100)
            self.health = self.max_health = 10
        else:
            self.speed = uniform(90, 160)
            self.health = self.max_health = 2

        self.wobble_timer = uniform(0, 10)
        self.wobble_amount = uniform(20, 45)
        self.facing_right = True

    def update(self, dt):
        self.wobble_timer += dt

        to_player = pygame.Vector2(player.rect.center) - self.pos
        if to_player.length() > 0:
            forward = to_player.normalize()
        else:
            forward = pygame.Vector2(1, 0)

        perpendicular = pygame.Vector2(-forward.y, forward.x)
        wobble = sin(self.wobble_timer * 2) * self.wobble_amount

        self.pos += forward * self.speed * dt
        self.pos += perpendicular * wobble * dt

        should_face_right = forward.x > 0
        if should_face_right != self.facing_right:
            self.facing_right = should_face_right
            # base art faces right by default -> flip horizontally when facing left
            self.image = self.base_surf if self.facing_right else pygame.transform.flip(self.base_surf, True, False)

        self.rect.center = self.pos
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


class MapFragment(pygame.sprite.Sprite):
    """Dropped by the boss shark. Walking into it ends the level."""

    def __init__(self, pos, groups):
        super().__init__(groups)
        size = 34
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        points = [(size / 2, 0), (size, size * 0.4), (size * 0.75, size), (size * 0.25, size), (0, size * 0.4)]
        pygame.draw.polygon(self.image, (250, 210, 90), points)
        pygame.draw.polygon(self.image, (255, 255, 255), points, 2)

        self.pos = pygame.Vector2(pos)
        self.rect = self.image.get_frect(center=self.pos)
        self.spawn_timer = uniform(0, 10)

    def update(self, dt):
        self.spawn_timer += dt
        self.bob_offset = sin(self.spawn_timer * 3) * 6


class Bubble(pygame.sprite.Sprite):
    def __init__(self, pos, groups, small=False):
        super().__init__(groups)
        self.radius = randint(2, 4) if small else randint(4, 10)
        size = self.radius * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (200, 230, 255, 130), (self.radius, self.radius), self.radius)
        pygame.draw.circle(self.image, (255, 255, 255, 180), (self.radius, self.radius), self.radius, 1)

        self.pos = pygame.Vector2(pos)
        self.rect = self.image.get_frect(center=self.pos)

        self.rise_speed = uniform(40, 110)
        self.sway_amount = uniform(4, 14)
        self.sway_speed = uniform(1.5, 3.5)
        self.age = 0
        self.lifetime = uniform(2.5, 5)

    def update(self, dt):
        self.age += dt
        self.pos.y -= self.rise_speed * dt
        self.pos.x += sin(self.age * self.sway_speed) * self.sway_amount * dt
        self.rect.center = self.pos
        if self.age >= self.lifetime:
            self.kill()


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
all_sprites = CameraGroup()
harpoon_sprites = pygame.sprite.Group()
shark_sprites = pygame.sprite.Group()
bubble_sprites = pygame.sprite.Group()
fragment_sprites = pygame.sprite.Group()

player = Player(all_sprites)
score = 0

SHARK_KILLS_TO_BOSS = 5  # how many regular sharks to kill before the boss appears
shark_kills = 0
boss_spawned = False
level_complete = False

AMBIENT_BUBBLE_EVENT = pygame.USEREVENT + 1
SHARK_SPAWN_EVENT = pygame.USEREVENT + 2
pygame.time.set_timer(AMBIENT_BUBBLE_EVENT, 250)
pygame.time.set_timer(SHARK_SPAWN_EVENT, 1800)


def spawn_shark(is_boss=False):
    margin = 60
    for _ in range(10):
        x = randint(WORLD_BOUNDS.left + margin, WORLD_BOUNDS.right - margin)
        y = randint(WORLD_BOUNDS.top + margin, WORLD_BOUNDS.bottom - margin)
        if pygame.Vector2(x, y).distance_to(player.rect.center) > 300:
            Shark((x, y), (all_sprites, shark_sprites), is_boss=is_boss)
            return
    # fallback if we couldn't find a spot far from the player in 10 tries
    x = randint(WORLD_BOUNDS.left + margin, WORLD_BOUNDS.right - margin)
    y = randint(WORLD_BOUNDS.top + margin, WORLD_BOUNDS.bottom - margin)
    Shark((x, y), (all_sprites, shark_sprites), is_boss=is_boss)


def draw_ui():
    for i in range(player.max_health):
        color = (220, 60, 60) if i < player.health else (70, 70, 70)
        pygame.draw.circle(display_surface, color, (30 + i * 34, 30), 12)
        pygame.draw.circle(display_surface, (255, 255, 255), (30 + i * 34, 30), 12, 2)

    score_surf = font.render(f"Score: {score}", True, (255, 255, 255))
    display_surface.blit(score_surf, (20, 55))

    bar_w, bar_h = 160, 14
    bar_x, bar_y = 20, WINDOW_HEIGHT - 34
    progress = player.cooldown_progress
    pygame.draw.rect(display_surface, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
    fill_color = (90, 200, 255) if progress >= 1 else (255, 170, 60)
    pygame.draw.rect(display_surface, fill_color, (bar_x, bar_y, bar_w * progress, bar_h), border_radius=4)
    pygame.draw.rect(display_surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=4)
    label = font.render("HARPOON", True, (255, 255, 255))
    display_surface.blit(label, (bar_x, bar_y - 24))

    if not player.alive:
        over_surf = big_font.render("YOU DIED", True, (255, 60, 60))
        display_surface.blit(over_surf, over_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 20)))
        restart_surf = font.render("Press R to restart", True, (255, 255, 255))
        display_surface.blit(restart_surf, restart_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 40)))
    elif level_complete:
        over_surf = big_font.render("LEVEL COMPLETE", True, (90, 220, 140))
        display_surface.blit(over_surf, over_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 20)))
        restart_surf = font.render("Press R to play again", True, (255, 255, 255))
        display_surface.blit(restart_surf, restart_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 40)))
    elif boss_spawned:
        warning_surf = font.render("A massive shark is guarding a map fragment!", True, (255, 170, 170))
        display_surface.blit(warning_surf, warning_surf.get_frect(midtop=(WINDOW_WIDTH / 2, 20)))


def reset_game():
    global score, shark_kills, boss_spawned, level_complete
    for sprite in list(shark_sprites):
        sprite.kill()
    for sprite in list(harpoon_sprites):
        sprite.kill()
    for sprite in list(bubble_sprites):
        sprite.kill()
    for sprite in list(fragment_sprites):
        sprite.kill()
    player.health = player.max_health
    player.alive = True
    player.rect.center = (WORLD_BOUNDS.centerx, WORLD_BOUNDS.centery)
    player.invincible_until = 0
    score = 0
    shark_kills = 0
    boss_spawned = False
    level_complete = False
    pygame.time.set_timer(SHARK_SPAWN_EVENT, 1800)


running = True
while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == AMBIENT_BUBBLE_EVENT and player.alive:
            spawn_x = min(max(player.rect.centerx + randint(-WINDOW_WIDTH // 2, WINDOW_WIDTH // 2),
                               WORLD_BOUNDS.left), WORLD_BOUNDS.right)
            spawn_y = min(max(player.rect.centery + WINDOW_HEIGHT // 2 + randint(0, 100),
                               WORLD_BOUNDS.top), WORLD_BOUNDS.bottom)
            Bubble((spawn_x, spawn_y), (all_sprites, bubble_sprites))

        if event.type == SHARK_SPAWN_EVENT and player.alive and not level_complete and not boss_spawned:
            if shark_kills >= SHARK_KILLS_TO_BOSS:
                spawn_shark(is_boss=True)
                boss_spawned = True
                pygame.time.set_timer(SHARK_SPAWN_EVENT, 0)  # stop future regular spawns
            else:
                spawn_shark()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and not player.alive:
            reset_game()

    all_sprites.update(dt)

    for harpoon in list(harpoon_sprites):
        hit_sharks = pygame.sprite.spritecollide(harpoon, shark_sprites, False)
        if hit_sharks:
            harpoon.kill()
            for shark in hit_sharks:
                if shark.hit():
                    if shark.is_boss:
                        MapFragment(shark.rect.center, (all_sprites, fragment_sprites))
                        score += 100
                    else:
                        shark_kills += 1
                        score += 10

    if player.alive and not level_complete and fragment_sprites:
        collected = pygame.sprite.spritecollide(player, fragment_sprites, True)
        if collected:
            level_complete = True

    if player.alive and not player.is_invincible():
        for shark in shark_sprites:
            if player.hitbox.colliderect(shark.rect):
                player.take_damage()
                break

    all_sprites.draw_all(player.rect.center)
    draw_ui()

    pygame.display.update()

pygame.quit()